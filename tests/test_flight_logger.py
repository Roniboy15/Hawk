"""Fluglogger am Host: virtuelle Zeit/RC/Sensoren, nie echte Pins/PWM."""
import contextlib
import csv
import io
import json
import math
import os
import struct
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'firmware'))
import config
import flight_records as records
import flight_logger
import flight_start
from diagnostics import BenchDiagnostics, StageTiming
from ram_buffer import RecordBuffer
from response_log import ResponseLog

MOD = 1 << 30


class Clock:
    us = 0
    def ticks_ms(self): return self.us//1000 % MOD
    def ticks_us(self): return self.us % MOD
    @staticmethod
    def ticks_diff(a,b): return (a-b+MOD//2) % MOD-MOD//2
    def sleep_ms(self,n): self.us += n*1000


def control():
    return {'mode':'MANUAL', 'fault':'', 'angles':(3,-4,5),
            'sample':(0.1,0.2,1,11,12,13), 'imu_fresh':True,
            'rx':([1053,1554,1998],[10,11,12],[1,2,3]),
            'pulses':{'roll':1300,'pitch':1500,'yaw':1650},
            'armed':True,'fresh':True,'period_us':10000,
            'work_to_log_us':2100,'imu_age_ms':0,'iteration_start_us':0}


def fix(epoch='120000.000'):
    return {'valid':True,'gga_valid':True,'rmc_valid':True,'utc':epoch,
            'date':'211026','lat':47.355676,'lon':8.508009,'altitude_msl_m':455.2,
            'speed_ms':4.2,'course_deg':270.1,'course_usable':True,'quality':1,
            'satellites':11,'hdop':0.8,'gga_age_ms':100,'rmc_age_ms':20}


def raw_record(buffer,index):
    block,offset=buffer.slot(index)
    return bytes(block[offset:offset+144])


class RecordsTests(unittest.TestCase):
    def test_csv_budget_covers_extreme_record_fields_and_fast_row(self):
        b=RecordBuffer(1,144)
        # Alle Integergrenzen und laengste float32-Notation; Koordinaten WGS84.
        values=([4294967295,4294967295,65535,4,4,2,255,65535]+[-1.23456e-30]*9+
                [65535]*4+[-32768]*3+[65535]*3+[-2147483648]*3+
                [4294967294,311299,-89.99999999,-179.99999999]+[-1.23456e-30]*4+
                [-32768]*2+[4294967295,-1.23456e-30,-1.23456e-30,65534,255,255])
        block,offset=b.slot(0)
        struct.pack_into(records.FORMAT,block,offset,*values)
        self.assertLessEqual(len(records.csv_row(b,0)),records.CSV_MAX_ROW_BYTES)
        from response_log import FORMAT,CSV_MAX_ROW_BYTES
        fast=ResponseLog(RecordBuffer(1800,30,48))
        block,offset=fast.buffer.slot(0)
        struct.pack_into(FORMAT,block,offset,4294967295,*([-32768]*5),
                         *([65535]*6),65534,36,255)
        fast.count=1
        file=io.StringIO(); fast.write_csv(file)
        self.assertLessEqual(len(file.getvalue().splitlines()[1])+1,CSV_MAX_ROW_BYTES)

    def test_byte_counter_handles_json_utf8_and_native_binary_writes(self):
        data={'message':'Groesse: \u00b5 / \u00e4', 'values':[1, -2.5, None]}
        counter=records.ByteCounter()
        json.dump(data,counter,ensure_ascii=False)
        self.assertEqual(counter.size,len(json.dumps(data,ensure_ascii=False).encode('utf-8')))
        self.assertEqual(counter.write(b'123'),3)
        self.assertEqual(counter.ioctl(4,None),0)

    def test_accel_invalid_keeps_gyro_and_untrusted_tilt_stays_missing(self):
        buffer=RecordBuffer(1,144)
        c=dict(control(),imu_fresh=False,gyro_fresh=True,tilt_valid=False)
        records.encode(buffer,0,2000,1,1,c,{},
                       {'valid':False,'pressure_pa':None,'temperature_c':None,
                        'relative_height_m':None,'age_ms':-1},1998,True,False,False)
        row=next(csv.DictReader(io.StringIO(records.COLUMNS+'\n'+records.csv_row(buffer,0))))
        self.assertEqual(row['roll_deg'],'')
        self.assertEqual(row['acc_z_g'],'')
        self.assertEqual(float(row['gyro_roll_dps']),11)
        self.assertEqual(int(row['valid_bits']) & 193,64)

    def test_stage_timing_preserves_previous_slow_iteration_across_tick_wrap(self):
        clock=Clock()
        clock.us=MOD-2000
        stages=StageTiming(clock)
        arrays=(stages.current,stages.maximum,stages.worst)
        stages.begin(clock.ticks_us(),None)
        clock.us+=1000
        stages.mark(0)
        clock.us+=60000
        stages.mark(4)
        clock.us+=500
        stages.mark(8)
        stages.begin(clock.ticks_us(),61500)
        clock.us+=100
        stages.mark(0)
        stages.begin(clock.ticks_us(),10000)
        report=stages.report()
        self.assertEqual(report['preceding_iteration'],1)
        self.assertEqual(report['worst_period_us'],61500)
        self.assertEqual(report['preceding_stages_us'],[1000,0,0,0,60000,0,0,0,500])
        self.assertEqual(report['max_us'][4],60000)
        self.assertEqual(report['outside_stages_us'],0)
        for before,after in zip(arrays,(stages.current,stages.maximum,stages.worst)):
            self.assertIs(before,after)
        clock.us-=1
        stages.mark(0)
        self.assertEqual(stages.report()['invalid'],1)

    def test_144_byte_roundtrip_and_missing_values_preserve_coordinates(self):
        buffer=RecordBuffer(2,144)
        g=dict(fix(),utc_ms=43200000)
        b={'valid':True,'pressure_pa':96001,'temperature_c':21.5,
           'relative_height_m':2.25,'age_ms':5}
        records.encode(buffer,0,2000,1,1,control(),g,b,1998,True,True,False)
        row=next(csv.DictReader(io.StringIO(records.COLUMNS+'\n'+records.csv_row(buffer,0))))
        self.assertEqual(records.RECORD_BYTES,144)
        self.assertEqual(len(row),46)
        self.assertEqual(row['mode'],'MANUAL')
        self.assertEqual(row['date_ddmmyy'],'211026')
        self.assertAlmostEqual(float(row['lat_deg']),g['lat'],places=8)
        self.assertAlmostEqual(float(row['lon_deg']),g['lon'],places=8)
        self.assertEqual(row['servo_roll_us'],'1300')
        c=control()
        c['imu_fresh']=False
        b.update(valid=False,pressure_pa=None,temperature_c=None,relative_height_m=None,age_ms=-1)
        records.encode(buffer,1,3000,1,3,c,{},b,None,False,False,False)
        row=next(csv.DictReader(io.StringIO(records.COLUMNS+'\n'+records.csv_row(buffer,1))))
        for key in ('roll_deg','gyro_roll_dps','lat_deg','lon_deg','utc_ms','pressure_pa'):
            self.assertEqual(row[key],'')
        self.assertEqual(row['baro_age_ms'],'-1')
        self.assertEqual(row['ch3_us'],'0')

    def test_ground_button_requires_release_hold_pause_and_handles_wrap(self):
        stop=records.GroundStop(Clock.ticks_diff,2000)
        self.assertFalse(stop.update(True,True,0))
        self.assertFalse(stop.update(True,True,3000))
        stop.update(False,True,MOD-3000)
        stop.update(True,False,MOD-2500)
        self.assertFalse(stop.update(True,False,MOD-100))
        stop.update(True,True,MOD-1000)
        self.assertFalse(stop.update(True,True,999))
        self.assertTrue(stop.update(True,True,1000))


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock()
        self.session=flight_logger.FlightSession(RecordBuffer(632,144),self.clock)
        self.session.started=0
        self.channel=types.SimpleNamespace(channels={'record':{'pulse':998}},
                            poll=Mock(),fresh=lambda a,t:True,close=Mock())
        self.session.aux=self.channel
        self.session.button=lambda:False

    def step(self,ms,pulse=None):
        self.clock.us=ms*1000
        if pulse is not None:
            self.channel.channels['record']['pulse']=pulse
        c=control()
        c['iteration_start_us']=self.clock.ticks_us()
        return self.session.step(self.clock.ticks_ms(),c)

    def start_capture(self):
        self.step(0,998)
        self.step(200,998)
        self.step(300,1998)
        self.step(500,1998)

    def test_ch3_pause_resume_and_loss_do_not_stop_or_write_files(self):
        with patch('builtins.open',side_effect=AssertionError('Flash waehrend Loop')):
            self.start_capture()
            self.assertTrue(self.session.recording)
            self.step(1500)
            self.step(1600,998)
            self.step(1800)
            count=self.session.count
            self.assertFalse(self.step(10000))
            self.assertEqual(self.session.count,count)
            self.step(11000,1998)
            self.step(11200)
            self.assertEqual(self.session.segment,2)
            self.channel.fresh=lambda a,t:False
            self.assertFalse(self.step(11300))
            self.assertFalse(self.session.recording)
            self.channel.fresh=lambda a,t:True
            self.step(12000,1998)
            self.step(12500)
            self.assertFalse(self.session.recording)

    def test_paused_loop_polls_sensors_but_does_not_build_record_snapshots(self):
        with patch.object(self.session,'_poll_sensors') as poll, \
             patch.object(self.session,'_snapshots',wraps=self.session._snapshots) as snapshots:
            self.step(0,998)
            self.step(100)
            self.step(200)
            self.assertEqual(poll.call_count,3)
            snapshots.assert_not_called()
            self.assertEqual(self.session.count,0)

    def test_sensor_profiling_separates_slow_gps_and_baro_even_when_paused(self):
        stages=StageTiming(self.clock)
        self.session.stage_timing=stages
        self.session.gps=types.SimpleNamespace(
            poll=lambda now:self.clock.sleep_ms(60),snapshot=lambda now,result=None:fix())
        self.session.baro=types.SimpleNamespace(poll=lambda now:self.clock.sleep_ms(8))
        stages.begin(0,None)
        with patch('builtins.open',side_effect=AssertionError('Flash waehrend Messung')):
            self.assertFalse(self.step(0,998))
        stages.mark(8)
        stages.begin(self.clock.ticks_us(),68000)
        report=stages.report()
        self.assertEqual(report['preceding_stages_us'][4:6],[60000,8000])
        self.assertEqual(self.session.count,0)
        self.assertFalse(self.session.recording)

    def test_planned_gc_runs_in_light_loop_and_its_cost_is_not_hidden(self):
        self.session.gc_work_limit_us=15000
        with patch.object(flight_logger.gc,'mem_free',return_value=32000,create=True), \
             patch.object(flight_logger.gc,'collect',side_effect=lambda:self.clock.sleep_ms(24)), \
             patch('builtins.open',side_effect=AssertionError('Flash im Loop')):
            self.assertFalse(self.step(0,998))
        self.assertEqual(self.clock.us,24000)
        self.assertEqual(self.session.gc_count,1)
        self.assertEqual(self.session.gc_max_us,24000)
        self.assertFalse(self.session.recording)

    def test_planned_gc_defers_busy_loop_and_skips_sufficient_free_heap(self):
        self.session.gc_work_limit_us=15000
        with patch.object(flight_logger.gc,'mem_free',return_value=32000,create=True), \
             patch.object(flight_logger.gc,'collect') as collect:
            self.clock.us=16000
            self.session._collect_if_due(0)
            collect.assert_not_called()
            self.assertEqual(self.session.gc_deferred,1)
        with patch.object(flight_logger.gc,'mem_free',return_value=40000,create=True), \
             patch.object(flight_logger.gc,'collect') as collect:
            self.session._collect_if_due(16000)
            collect.assert_not_called()
        self.assertEqual(self.session.gc_count,0)

    def test_slow_heap_query_does_not_starve_gc_in_an_eligible_loop(self):
        self.session.gc_work_limit_us=15000
        self.session.startup_gc_us=24000
        self.clock.us=10000
        def query():
            self.clock.sleep_ms(7)
            return 32000
        with patch.object(flight_logger.gc,'mem_free',side_effect=query,create=True), \
             patch.object(flight_logger.gc,'collect',side_effect=lambda:self.clock.sleep_ms(24)):
            self.session._collect_if_due(0)
        self.assertEqual(self.session.gc_count,1)
        self.assertEqual(self.clock.us,41000)

    def test_heap_queries_are_spaced_instead_of_scanning_every_iteration(self):
        self.session.gc_work_limit_us=15000
        interval=self.session.settings['gc_poll_ms']*1000
        with patch.object(flight_logger.gc,'mem_free',return_value=40000,create=True) as query:
            for us in (0,interval//2,interval-1,interval):
                self.clock.us=us
                self.session._collect_if_due(us)
        self.assertEqual(query.call_count,2)

    def test_heap_pressure_between_checks_does_not_force_unplanned_collection(self):
        # MicroPython/Unix-Probe: ~5 KiB temporaere IMU-/Lageobjekte je Schritt.
        # Mit 200-ms-Abfrage kann der Heap vor der naechsten Pruefung leer sein.
        # 7-ms-Heapscan/24-ms-GC sind simulierte Kosten aus den Bodenbefunden.
        free, unplanned = 66000, 0
        self.session.gc_work_limit_us=15000
        self.session.startup_gc_us=24000
        def query():
            self.clock.sleep_ms(7)
            return free
        def collect():
            nonlocal free
            self.clock.sleep_ms(24)
            free=66000
        with patch.object(flight_logger.gc,'mem_free',side_effect=query,create=True), \
             patch.object(flight_logger.gc,'collect',side_effect=collect):
            for i in range(1000):
                start=self.clock.ticks_us()
                free-=5120
                if free < 0:
                    unplanned+=1
                    collect()
                self.clock.sleep_ms(12)
                self.session._collect_if_due(start)
                self.clock.sleep_ms(3)
        self.assertEqual(unplanned,0)
        self.assertGreater(self.session.gc_count,0)

    def test_pending_gc_retries_without_repeating_an_expensive_heap_scan(self):
        self.session.gc_work_limit_us=15000
        self.session.startup_gc_us=24000
        self.clock.us=10000
        def query():
            self.clock.sleep_ms(20)
            return 32000
        with patch.object(flight_logger.gc,'mem_free',side_effect=query,create=True) as scanned, \
             patch.object(flight_logger.gc,'collect',side_effect=lambda:self.clock.sleep_ms(24)):
            self.session._collect_if_due(0)
            self.assertEqual(self.session.gc_count,0)
            self.clock.us=35000
            self.session._collect_if_due(35000)
        self.assertEqual(scanned.call_count,1)
        self.assertEqual(self.session.gc_count,1)

    def test_capacity_stops_only_recording_keeps_all_earlier_rows(self):
        self.start_capture()
        first=raw_record(self.session.buffer,0)
        for second in range(1,700):
            self.assertFalse(self.step(500+second*1000))
        self.assertEqual(self.session.count,632)
        self.assertTrue(self.session.full)
        self.assertFalse(self.session.recording)
        self.assertEqual(raw_record(self.session.buffer,0),first)
        self.assertEqual(records.decode(self.session.buffer,631)[3],5)
        self.assertFalse(self.step(900000))  # Kein zehnminuetiger Programmstop.

    def test_latest_coherent_gps_pair_ages_during_mixed_epoch_then_expires(self):
        gps=types.SimpleNamespace(poll=Mock(),snapshot=Mock())
        def snapshot(now,result=None):
            if result is None:
                result={}
            result.clear()
            result.update(current)
            return result
        gps.snapshot.side_effect=snapshot
        self.session.gps=gps
        for index in range(5):
            current=fix('12000%d.000'%index)
            self.step(index*1000)
        self.assertEqual(self.session.good_epochs,5)
        mixed=fix('120005.000')
        mixed['valid']=False
        current=mixed
        self.step(4500)
        g,b=self.session._snapshots(4500)
        self.assertTrue(g['valid'])
        self.assertEqual(g['utc'],'120004.000')
        self.assertEqual(g['gga_age_ms'],600)
        self.assertEqual(self.session._snapshots(7000)[0],{})
        current=dict(mixed,rmc_valid=False)
        self.step(7100)
        self.assertIsNone(self.session.fix)
        self.assertEqual(self.session.good_epochs,0)

    def test_repeated_same_epoch_does_not_make_gps_ready(self):
        self.session.gps=types.SimpleNamespace(poll=Mock(),snapshot=lambda now,result=None:fix())
        for ms in range(0,1000,10):
            self.step(ms)
        self.assertEqual(self.session.good_epochs,1)

    def test_baro_fault_and_logger_fault_remain_local(self):
        self.session.baro=types.SimpleNamespace(poll=Mock(side_effect=OSError('I2C')))
        self.start_capture()
        self.assertIn('barometer',self.session.errors)
        self.assertTrue(self.session.recording)
        self.session.fail('logger',ValueError('encode'))
        self.assertFalse(self.step(1500))
        self.assertFalse(self.session.recording)
        self.assertTrue(self.session.disabled)

    def test_boot_cannot_stop_capture_but_can_stop_after_ch3_pause(self):
        self.start_capture()
        self.session.button=lambda:True
        for ms in (1000,2000,3000,4000):
            self.assertFalse(self.step(ms))
        self.step(4100,998)
        self.step(4300)
        self.assertFalse(self.step(4400))
        self.assertFalse(self.step(6399))
        self.assertTrue(self.step(6450))  # Naechste 50-ms-Buttonabfrage.

    def test_close_attempts_uart_after_aux_close_failure(self):
        self.channel.close.side_effect=OSError('PIO close')
        self.session.uart=types.SimpleNamespace(deinit=Mock())
        with self.assertRaises(OSError): self.session.close()
        self.session.uart.deinit.assert_called_once_with()

    def test_export_requires_shutdown_and_never_overwrites_existing_run(self):
        self.start_capture()
        self.step(1500)
        self.session.stage_timing=StageTiming(self.clock)
        diag=BenchDiagnostics(10000,50000,4)
        with self.assertRaises(RuntimeError): self.session.export({},diag,'ground_button')
        with tempfile.TemporaryDirectory() as folder:
            previous=os.getcwd()
            try:
                os.chdir(folder)
                self.session.can_export=True
                Path('flight_1500_0.csv').write_text('old evidence')
                with contextlib.redirect_stdout(io.StringIO()), \
                     patch.object(flight_logger.os,'statvfs',return_value=(4096,4096,1024,512,512)):
                    report=self.session.export({},diag,'ground_button')
                self.assertEqual(report['csv_file'],'flight_1500_1.csv')
                self.assertEqual(Path('flight_1500_0.csv').read_text(),'old evidence')
                rows=list(csv.DictReader(io.StringIO(Path(report['csv_file']).read_text())))
                self.assertEqual(len(rows),self.session.count)
                self.assertEqual(rows[0]['kind'],'start')
                self.assertEqual(json.loads(Path('flight_1500_1.json').read_text())['stop_reason'],
                                 'ground_button')
                self.assertEqual(report['stage_timing']['max_us'],[0]*9)
                self.assertEqual(report['runtime_gc']['count'],0)
                self.assertEqual(report['start_method'],'explicit')
                self.assertEqual(json.loads(Path('flight_1500_1.json').read_text())['stage_timing']['names'],
                                 list(StageTiming.NAMES))
            finally:
                os.chdir(previous)

    def test_low_flash_does_not_discard_ram(self):
        self.start_capture()
        before=raw_record(self.session.buffer,0)
        self.session.can_export=True
        with patch.object(flight_logger.os,'statvfs',return_value=(4096,4096,1,1,1)), \
             patch('builtins.open') as opened:
            with self.assertRaises(OSError):
                self.session.export({},BenchDiagnostics(10000,50000,4),'ground_button')
            opened.assert_not_called()
        self.assertFalse(self.session.exported)
        self.assertEqual(raw_record(self.session.buffer,0),before)

    def test_preflight_reports_three_or_two_runs_with_reserve_unchanged(self):
        def fs(free): return (4096,4096,1000,free//4096,free//4096)
        with patch.object(flight_logger.os,'statvfs',return_value=fs(2000000)):
            budget=self.session.storage_budget()['full_run_bytes']
        reserve=self.session.settings['flash_reserve_bytes']
        for slots,free in ((3,reserve+3*budget),(2,reserve+3*budget-4096)):
            with patch.object(flight_logger.os,'statvfs',return_value=fs(free)), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.session.preflight_storage()
            self.assertEqual(self.session.storage_plan['full_runs_available'],slots)
            self.assertEqual(self.session.storage_plan['reserve_bytes'],131072)

    def test_large_json_is_rejected_before_creating_files_and_keeps_ram(self):
        self.start_capture()
        first=raw_record(self.session.buffer,0)
        self.session.can_export=True
        with patch('builtins.open') as opened:
            with self.assertRaises(ValueError):
                self.session.export({'too_large':'x'*self.session.json_budget},
                                    BenchDiagnostics(10000,50000,4),'ground_button')
            opened.assert_not_called()
        self.assertFalse(self.session.exported)
        self.assertEqual(raw_record(self.session.buffer,0),first)

    def test_real_start_refuses_low_reserve_and_resources_can_close(self):
        pin=Mock()
        pin.OUT=1
        uart=types.SimpleNamespace(deinit=Mock())
        led=Mock()
        with patch.dict(sys.modules,{
                'machine':types.SimpleNamespace(Pin=pin,UART=Mock(return_value=uart),I2C=Mock()),
                'neopixel':types.SimpleNamespace(NeoPixel=Mock(return_value=led)),
                'rp2':types.SimpleNamespace(bootsel_button=lambda:False)}), \
             patch('receiver.Receiver',return_value=self.channel), \
             patch.object(flight_logger,'MS5611',return_value=Mock()), \
             patch.object(flight_logger.gc,'collect',side_effect=lambda:self.clock.sleep_ms(25)), \
             patch.object(flight_logger.gc,'mem_free',return_value=64000,create=True):
            with self.assertRaises(MemoryError): self.session.start({})
        self.assertEqual(self.session.startup_gc_us,25000)
        self.session.close()
        self.channel.close.assert_called_once_with()
        uart.deinit.assert_called_once_with()


class LauncherTests(unittest.TestCase):
    def setUp(self):
        # Die bisherigen Launcher-Vertraege weiterhin im 1-Hz-Profil pruefen.
        setting=patch.object(config,'LOGGER_PROFILE','snapshot1')
        setting.start()
        self.addCleanup(setting.stop)

    def tearDown(self):
        flight_start._pending=None
        flight_start._running=False

    def test_bad_profile_rejected_without_allocating(self):
        with patch.object(flight_start.cfg,'AUTO_START',False), \
             patch('ram_buffer.RecordBuffer') as allocate:
            with self.assertRaises(ValueError): flight_start.run('stabilize')
            allocate.assert_not_called()

    def test_low_flash_refuses_before_boot_or_controller_and_releases_ram(self):
        import app
        buffer=RecordBuffer(632,144)
        pin=Mock(OUT=1); led=MagicMock()
        session_type=flight_logger.FlightSession
        with patch('ram_buffer.RecordBuffer',return_value=buffer), \
             patch.object(flight_logger,'FlightSession',side_effect=lambda b:session_type(b,Clock())), \
             patch.object(flight_logger.os,'statvfs',return_value=(4096,4096,1,1,1)), \
             patch.dict(sys.modules,{'machine':types.SimpleNamespace(Pin=pin),
                                     'neopixel':types.SimpleNamespace(NeoPixel=Mock(return_value=led))}), \
             patch.object(flight_start,'_wait_for_start') as button, \
             patch.object(app,'run') as run, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(OSError): flight_start.run('manual',wait_for_button=True)
        button.assert_not_called(); run.assert_not_called()
        self.assertIsNone(flight_start._pending)
        with self.assertRaises(RuntimeError): buffer.slot(0)
        led.__setitem__.assert_called_once_with(0,(12,0,0))

    def test_main_default_boot_modes_and_legacy_start_are_separate(self):
        source=(Path(__file__).resolve().parents[1]/'firmware/main.py').read_text()
        launch, legacy = Mock(), Mock()
        with patch.dict(sys.modules,{'flight_start':types.SimpleNamespace(run=launch),
                                     'app':types.SimpleNamespace(run=legacy)}), \
             contextlib.redirect_stdout(io.StringIO()):
            for mode,auto in ((None,False),('sensor',False),('manual',False),(None,True)):
                with self.subTest(mode=mode,auto=auto), \
                     patch.object(config,'LOGGER_BOOT_MODE',mode), \
                     patch.object(config,'AUTO_START',auto):
                    launch.reset_mock(); legacy.reset_mock()
                    exec(compile(source,'main.py','exec'),{})
                    if mode is not None:
                        launch.assert_called_once_with(mode,wait_for_button=True)
                    else:
                        launch.assert_not_called()
                    self.assertEqual(legacy.call_count,int(auto))
            with patch.object(config,'LOGGER_BOOT_MODE','manual'), \
                 patch.object(config,'AUTO_START',True):
                launch.reset_mock(); legacy.reset_mock()
                with self.assertRaises(ValueError): exec(compile(source,'main.py','exec'),{})
                launch.assert_not_called(); legacy.assert_not_called()

    def test_boot_wait_ignores_initial_hold_and_short_press_until_released(self):
        clock=Clock()
        clock.us=(MOD-1000)*1000
        started=clock.us
        events=[]
        led=MagicMock()
        led.write.side_effect=lambda:events.append(clock.us-started)
        def pressed():
            ms=(clock.us-started)//1000
            return ms<500 or 1000<=ms<1200 or 1300<=ms<3600
        with patch.dict(sys.modules,{
                'time':clock,
                'machine':types.SimpleNamespace(Pin=Mock(OUT=1)),
                'rp2':types.SimpleNamespace(bootsel_button=pressed),
                'neopixel':types.SimpleNamespace(NeoPixel=Mock(return_value=led))}), \
             contextlib.redirect_stdout(io.StringIO()):
            flight_start._wait_for_start()
        self.assertEqual(events,[0,3300000,3600000])
        self.assertFalse(pressed())
        self.assertEqual(led.__setitem__.call_args_list[-1].args,(0,(0,0,0)))

    def test_boot_cancel_releases_buffer_and_never_starts_controller(self):
        import app
        buffer=RecordBuffer(632,144)
        real_session=flight_logger.FlightSession
        with patch('ram_buffer.RecordBuffer',return_value=buffer), \
             patch.object(flight_logger,'FlightSession',side_effect=lambda b:real_session(b,Clock())), \
             patch.object(flight_start,'_wait_for_start',side_effect=KeyboardInterrupt), \
             patch.object(app,'run') as run:
            with self.assertRaises(KeyboardInterrupt):
                flight_start.run('manual',wait_for_button=True)
        run.assert_not_called()
        self.assertFalse(flight_start._running)
        self.assertIsNone(flight_start._pending)
        with self.assertRaises(RuntimeError): buffer.slot(0)

    def test_boot_confirmation_follows_reservation_and_precedes_app_run(self):
        import app
        events=[]
        real_buffer=RecordBuffer
        real_session=flight_logger.FlightSession
        def allocate(*args):
            events.append('buffer')
            return real_buffer(*args)
        def wait():
            self.assertEqual(events,['buffer'])
            events.append('button')
        def run(session):
            self.assertEqual(events,['buffer','button'])
            self.assertEqual(session.start_method,'boot_button')
            self.assertEqual(config.START_MODE,'manual')
        with patch('ram_buffer.RecordBuffer',side_effect=allocate), \
             patch.object(flight_logger,'FlightSession',side_effect=lambda b:real_session(b,Clock())), \
             patch.object(flight_start,'_wait_for_start',side_effect=wait), \
             patch.object(app,'run',side_effect=run) as app_run:
            flight_start.run('manual',wait_for_button=True)
        app_run.assert_called_once()

    def test_pending_export_requires_verified_shutdown_and_keeps_failed_data(self):
        buffer=RecordBuffer(632,144)
        session=flight_logger.FlightSession(buffer,Clock())
        session.count=1
        flight_start._pending=session
        with self.assertRaises(RuntimeError): flight_start.save_pending()
        session.can_export=True
        session.export_context=({},None,'ground_button')
        with patch.object(session,'export',side_effect=OSError('storage')):
            with self.assertRaises(OSError): flight_start.save_pending()
        self.assertIs(flight_start._pending,session)
        buffer.slot(0)
        with patch.object(session,'export',return_value={'saved':True}):
            self.assertEqual(flight_start.save_pending(),{'saved':True})
        self.assertIsNone(flight_start._pending)
        with self.assertRaises(RuntimeError): buffer.slot(0)

    def test_launcher_restores_configuration_and_retains_failed_export(self):
        import app
        saved=(config.START_MODE,config.SAVE_LOG_ON_STOP,config.CONSOLE_HZ)
        def run(session):
            self.assertEqual(config.START_MODE,'manual')
            self.assertFalse(config.SAVE_LOG_ON_STOP)
            self.assertEqual(session.buffer.payload_bytes,91008)
            session.count=rows
            session.export_context=({},None,'ground_button')
            raise OSError('failed export')
        real_session=flight_logger.FlightSession
        for rows in (0,1):
            with self.subTest(rows=rows), patch.object(app,'run',side_effect=run), \
                 patch.object(flight_logger,'FlightSession',side_effect=lambda b:real_session(b,Clock())):
                with self.assertRaises(OSError): flight_start.run('manual')
            self.assertEqual((config.START_MODE,config.SAVE_LOG_ON_STOP,config.CONSOLE_HZ),saved)
            self.assertFalse(flight_start._running)
            self.assertIsNotNone(flight_start._pending)
            flight_start._pending.buffer.slot(0)
            flight_start._pending=None


class ResponseTests(SessionTests):
    # Gemeinsame CH3-/GC-/Fehlervertraege auch mit schnellem Puffer ausfuehren.
    def setUp(self):
        super().setUp()
        self.session=flight_logger.FlightSession(RecordBuffer(132,144),self.clock,
                response=ResponseLog(RecordBuffer(1800,30,48)))
        self.session.started=0
        self.session.aux=self.channel
        self.session.button=lambda:False

    def test_capacity_stops_only_recording_keeps_all_earlier_rows(self):
        self.start_capture()
        first=raw_record(self.session.buffer,0)
        with patch('builtins.open',side_effect=AssertionError('Flash im Loop')):
            for ms in range(550,100000,50):
                self.assertFalse(self.step(ms))
        fast=self.session.response
        self.assertEqual(fast.count,1800)
        self.assertTrue(self.session.full)
        self.assertFalse(self.session.recording)
        self.assertEqual(raw_record(self.session.buffer,0),first)
        self.assertEqual(records.decode(self.session.buffer,self.session.count-1)[3],5)
        self.assertEqual(fast.report('test.csv')['interval_mean_ms'],50)
        self.assertEqual(fast.missed,0)
        self.assertEqual(fast.buffer.payload_bytes+self.session.buffer.payload_bytes,73008)

    def test_20hz_deadlines_do_not_drift_or_fabricate_catchup_samples(self):
        self.start_capture()  # erster schneller Wert bei 500 ms
        for ms in (521,563,584,605,750,771,813):
            self.step(ms)
        fast=self.session.response
        self.assertEqual(fast.count,5)  # 500,563,605,750,813; kein Nachholen bei750
        self.assertEqual(fast.missed,2)
        self.assertEqual(fast.interval_min,42)
        self.assertEqual(fast.interval_max,145)
        # Pausen duerfen weder den Puffer fuellen noch als Auslassungen zaehlen.
        self.step(820,998)
        self.step(1020)
        count,missed=fast.count,fast.missed
        self.step(10000)
        self.assertEqual(fast.count,count)
        self.step(11000,1998)
        self.step(11200)
        self.assertEqual(fast.count,count+1)
        self.assertEqual(fast.missed,missed)

    def test_three_full_exports_fit_original_free_flash_without_overwriting(self):
        self.start_capture()
        with patch('builtins.open',side_effect=AssertionError('Flash im Loop')):
            for ms in range(550,90500,50): self.step(ms)
        self.assertEqual(self.session.response.count,1800)
        self.session.can_export=True
        with tempfile.TemporaryDirectory() as folder:
            previous=os.getcwd()
            try:
                os.chdir(folder)
                def fs(_):
                    used=sum((f.stat().st_size+4095)//4096*4096 for f in Path('.').iterdir())
                    free=(1265664-used)//4096
                    return (4096,4096,512,free,free)
                with patch.object(flight_logger.os,'statvfs',side_effect=fs), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.session.preflight_storage()
                    self.assertEqual(self.session.storage_plan['full_runs_available'],3)
                    for _ in range(3):
                        self.session.export({},BenchDiagnostics(10000,50000,4),'ground_button')
                self.assertEqual(len(list(Path('.').glob('*.csv'))),6)
                self.assertEqual(len(list(Path('.').glob('*.json'))),3)
                self.assertGreaterEqual(fs('.')[3]*4096,131072)
            finally: os.chdir(previous)

    def test_maximum_transition_ring_fits_reserved_json_budget(self):
        self.start_capture()
        diag=BenchDiagnostics(10000,50000,config.EVENT_CAPACITY)
        for index in range(config.EVENT_CAPACITY):
            mode='MANUAL_FALLBACK' if index%2 else 'RX_TIMEOUT'
            diag.transition(1000000000+index,mode,'IMU_RUNTIME',False,False,30000,False,
                            ([2000]*3,[32767]*3,[1000000000]*3),
                            {'roll':1730,'pitch':1900,'yaw':1850})
        self.session.can_export=True
        with tempfile.TemporaryDirectory() as folder:
            previous=os.getcwd()
            try:
                os.chdir(folder)
                import app
                with contextlib.redirect_stdout(io.StringIO()):
                    report=self.session.export(app.run_metadata({}),diag,'ground_button')
                self.assertEqual(len(report['diagnostics']['events']),config.EVENT_CAPACITY)
                self.assertLessEqual(Path(report['csv_file']).with_suffix('.json').stat().st_size,
                                     self.session.json_budget)
            finally: os.chdir(previous)

    def test_quantized_gyro_covers_disc_start_rates_and_preserves_validity(self):
        fast=self.session.response
        c=dict(control(),sample=(16,0,0,1999.96,-1999.96,0.04),imu_fresh=False,
               gyro_fresh=True,tilt_valid=False)
        fast.sample(1,1,c)
        file=io.StringIO(); fast.write_csv(file)
        row=next(csv.DictReader(io.StringIO(file.getvalue())))
        self.assertEqual(row['roll_deg'],'')
        self.assertEqual(float(row['gyro_roll_dps']),2000)
        self.assertEqual(float(row['gyro_pitch_down_dps']),-2000)
        self.assertEqual(float(row['gyro_yaw_left_dps']),0)
        self.assertEqual(int(row['status_bits']) & 49,16)
        self.assertEqual(fast.buffer.payload_bytes,54000)

    def test_export_both_streams_roundtrip_flags_and_preserve_existing_files(self):
        self.start_capture()
        c=control()
        c.update(mode='MANUAL_FALLBACK',fault='IMU_RUNTIME',imu_fresh=False,period_us=80000)
        self.session.response.sample(550,1,c)
        self.session.can_export=True
        with tempfile.TemporaryDirectory() as folder:
            previous=os.getcwd()
            try:
                os.chdir(folder)
                Path('flight_500_0_response.csv').write_text('old evidence')
                with contextlib.redirect_stdout(io.StringIO()), \
                     patch.object(flight_logger.os,'statvfs',return_value=(4096,4096,1024,512,512)):
                    report=self.session.export({},BenchDiagnostics(10000,50000,4),'ground_button')
                self.assertEqual(Path('flight_500_0_response.csv').read_text(),'old evidence')
                self.assertEqual(report['schema'],3)
                self.assertEqual(report['logger_configuration']['profile'],'response20')
                self.assertEqual(report['response_log']['samples'],2)
                rows=list(csv.DictReader(io.StringIO(Path(report['response_log']['csv_file']).read_text())))
                self.assertEqual(len(rows[0]),17)
                self.assertEqual(rows[0]['pitch_down_deg'],'-4.0')
                self.assertEqual(rows[0]['gyro_yaw_left_dps'],'13.0')
                self.assertEqual(rows[0]['rx_roll_us'],'1053')
                self.assertEqual(rows[0]['servo_roll_us'],'1300')
                self.assertEqual(rows[0]['status_bits'],'63')
                self.assertEqual(rows[1]['mode'],'MANUAL_FALLBACK')
                self.assertEqual(rows[1]['fault'],'IMU_RUNTIME')
                self.assertEqual(rows[1]['period_us'],'-1')
                for key in ('roll_deg','pitch_down_deg','gyro_roll_dps'):
                    self.assertEqual(rows[1][key],'')
                self.assertEqual(rows[1]['status_bits'],'14')
            finally:
                os.chdir(previous)

    def test_sampling_elapsed_ms_across_clock_wrap(self):
        self.session.started=MOD-500
        self.start_capture()
        self.step(550)
        self.assertEqual(self.session.response.last_ms,1050)
        self.assertEqual(self.session.response.missed,0)

    def test_snapshot_capacity_or_aux_loss_also_halts_fast_capture(self):
        self.start_capture()
        fast=self.session.response
        self.channel.fresh=lambda a,t:False
        self.assertFalse(self.step(550))
        self.assertEqual(fast.count,1)
        self.assertFalse(self.session.recording)
        self.channel.fresh=lambda a,t:True
        self.step(600,998)
        self.step(800)
        self.session.count=self.session.buffer.capacity-1
        self.step(900,1998)
        self.assertFalse(self.step(1100))
        self.assertTrue(self.session.full)
        self.assertEqual(fast.count,1)

    def test_launcher_allocates_both_buffers_before_start_and_releases_after_cancel(self):
        import app
        buffers=[]
        session_type=flight_logger.FlightSession
        def allocate(*args):
            buffer=RecordBuffer(*args)
            buffers.append(buffer)
            return buffer
        def wait():
            self.assertEqual([b.payload_bytes for b in buffers],[19008,54000])
            raise KeyboardInterrupt
        with patch.object(config,'LOGGER_PROFILE','response20'), \
             patch('ram_buffer.RecordBuffer',side_effect=allocate), \
             patch.object(flight_logger,'FlightSession',side_effect=lambda b,response:session_type(b,self.clock,response)), \
             patch.object(flight_start,'_wait_for_start',side_effect=wait), \
             patch.object(app,'run') as run:
            with self.assertRaises(KeyboardInterrupt): flight_start.run('sensor',wait_for_button=True)
        run.assert_not_called()
        for buffer in buffers:
            with self.assertRaises(RuntimeError): buffer.slot(0)

    def test_failed_response_export_keeps_both_buffers_for_retry(self):
        import app
        captured=[]
        session_type=flight_logger.FlightSession
        def run(session):
            captured.append(session)
            session.started=0
            session.count=1
            session.can_export=True
            session.export_context=({},BenchDiagnostics(10000,50000,4),'ground_button')
            raise OSError('failed export')
        try:
            with patch.object(config,'LOGGER_PROFILE','response20'), \
                 patch.object(flight_logger,'FlightSession',side_effect=lambda b,response:session_type(b,self.clock,response)), \
                 patch.object(app,'run',side_effect=run):
                with self.assertRaises(OSError): flight_start.run('manual')
            pending=flight_start._pending
            self.assertIs(pending,captured[0])
            pending.buffer.slot(0)
            pending.response.buffer.slot(0)
            with patch.object(pending,'export',return_value={'saved':True}):
                self.assertEqual(flight_start.save_pending(),{'saved':True})
            for buffer in (pending.buffer,pending.response.buffer):
                with self.assertRaises(RuntimeError): buffer.slot(0)
        finally:
            flight_start._pending=None


if __name__ == '__main__':
    unittest.main()
