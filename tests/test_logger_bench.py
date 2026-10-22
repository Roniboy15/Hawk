"""Hosttests fuer Logger-Vorbereitung: keine realen Pins oder MCU-Dateien."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
import weakref
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'firmware'))
import config
import logger_bench
from recording import RecordingSwitch

MOD = 1 << 30


def diff(a, b):
    return (a-b+MOD//2) % MOD-MOD//2


class Clock:
    def __init__(self, us=0):
        self.us = us

    def ticks_us(self):
        return self.us % MOD

    def ticks_ms(self):
        return (self.us//1000) % MOD

    ticks_diff = staticmethod(diff)

    def sleep_us(self, value):
        self.us += value


class SwitchTests(unittest.TestCase):
    def make(self, sign=1):
        return RecordingSwitch(1200, 1800, 200, diff, sign)

    def test_high_at_boot_cannot_start_then_low_high_can(self):
        s = self.make()
        self.assertEqual(s.update(1900, True, 0), (False, None))
        self.assertEqual(s.update(1900, True, 1000), (False, None))
        s.update(1100, True, 1100)
        s.update(1100, True, 1300)
        s.update(1900, True, 1400)
        self.assertEqual(s.update(1900, True, 1599), (False, None))
        self.assertEqual(s.update(1900, True, 1600), (True, 'start'))
        self.assertEqual(s.update(1900, True, 1800), (True, None))

    def test_middle_and_brief_low_do_not_stop(self):
        s = self.make()
        for pulse,stamp in ((1100,0),(1100,200),(1900,300),(1900,500)):
            s.update(pulse, True, stamp)
        self.assertEqual(s.update(1500, True, 600), (True, None))
        s.update(1100, True, 700)
        s.update(1500, True, 899)
        self.assertEqual(s.update(1100, True, 900), (True, None))
        self.assertEqual(s.update(1100, True, 1100), (False, 'stop'))

    def test_channel_loss_stops_capture_and_requires_low_again(self):
        s = self.make()
        for pulse,stamp in ((1100,0),(1100,200),(1900,300),(1900,500)):
            s.update(pulse, True, stamp)
        self.assertEqual(s.update(1900, False, 600), (False, 'channel_invalid'))
        s.update(1900, True, 700)
        self.assertEqual(s.update(1900, True, 1000), (False, None))
        s.update(1100, True, 1100)
        s.update(1100, True, 1300)
        s.update(1900, True, 1400)
        self.assertEqual(s.update(1900, True, 1600), (True, 'start'))

    def test_physical_stick_high_can_mean_small_pulse(self):
        s = self.make(sign=-1)
        for pulse,stamp in ((1900,0),(1900,200),(1100,300)):
            s.update(pulse, True, stamp)
        self.assertEqual(s.update(1100, True, 500), (True, 'start'))
        s.update(1900, True, 600)
        self.assertEqual(s.update(1900, True, 800), (False, 'stop'))

    def test_debounce_across_tick_wrap_and_invalid_values(self):
        s = self.make()
        s.update(1100, True, MOD-100)
        s.update(1100, True, 100)
        s.update(1900, True, 200)
        self.assertEqual(s.update(1900, True, 400), (True, 'start'))
        self.assertEqual(s.update(2200, True, 500), (False, 'channel_invalid'))
        for pulse in (None, float('nan'), True):
            self.assertEqual(s.update(pulse, True, 600), (False, None))

    def test_reject_bad_thresholds(self):
        for low,high,hold,sign in ((1800,1200,200,1),(800,1800,200,1),
                                   (1200,1800,0,1),(1200,1800,200,0)):
            with self.assertRaises(ValueError):
                RecordingSwitch(low,high,hold,diff,sign)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous = os.getcwd()
        os.chdir(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(os.chdir, self.previous)
        self.clock = Clock()
        self.settings = dict(config.LOGGER_BENCH, case_bytes=4096, block_sizes=(512,1024,4096))
        self.fs = types.SimpleNamespace(stat=os.stat,
                     statvfs=lambda path:(4096,4096,512,256,256,0,0,0,0,255),
                     sync=lambda:self.clock.sleep_us(17000))

    def opener(self, failure=None):
        clock = self.clock
        class File:
            def __init__(self, file): self.file = file
            def write(self, data):
                clock.sleep_us(60000)
                if failure == 'interrupt': raise KeyboardInterrupt()
                if failure == 'write': raise OSError('injected write error')
                if failure == 'short': return self.file.write(data[:-1])
                if failure == 'corrupt':
                    self.file.write(b'X'*len(data))
                    return len(data)
                return self.file.write(data)
            def flush(self):
                clock.sleep_us(13000)
                self.file.flush()
            def close(self):
                clock.sleep_us(70000)
                self.file.close()
                if failure == 'close': raise OSError('injected close error')
        def open_file(path, mode):
            file = open(path,mode)
            if mode == 'wb':
                clock.sleep_us(1000)
                return File(file)
            return file
        return open_file

    def run_storage(self, failure=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return logger_bench._storage_run(self.settings,self.clock,self.fs,self.opener(failure))

    def test_full_write_readback_and_all_blocking_phases_measured(self):
        self.clock.us = MOD-10000
        report = self.run_storage()
        self.assertEqual(report['stop_reason'],'complete')
        self.assertFalse(report['flight_timing_qualified'])
        for case in report['cases']:
            self.assertTrue(case['verified'])
            self.assertEqual(case['written_bytes'],4096)
            self.assertEqual(case['timing']['write']['max_us'],60000)
            self.assertEqual(case['timing']['flush']['max_us'],13000)
            self.assertEqual(case['timing']['sync']['max_us'],17000)
            self.assertEqual(case['timing']['cycle']['max_us'],90000)
            self.assertEqual(case['timing']['close']['max_us'],70000)
            self.assertEqual(case['timing']['sync_after_close']['max_us'],17000)
        saved = json.loads(Path(report['report_file']).read_text())
        self.assertEqual(saved['cases'],report['cases'])

    def test_no_overwrite_or_calibration_changes(self):
        Path('logger_storage_0_0_512.bin').write_bytes(b'old evidence')
        Path('calibration.json').write_text('{"rc":"keep"}')
        report = self.run_storage()
        self.assertEqual(report['report_file'],'logger_storage_0_1.json')
        self.assertEqual(Path('logger_storage_0_0_512.bin').read_bytes(),b'old evidence')
        self.assertEqual(Path('calibration.json').read_text(),'{"rc":"keep"}')

    def test_low_space_fails_before_creating_any_file(self):
        self.fs.statvfs=lambda path:(4096,4096,100,1,1,0,0,0,0,255)
        opener=Mock()
        with self.assertRaises(ValueError):
            logger_bench._storage_run(self.settings,self.clock,self.fs,opener)
        opener.assert_not_called()
        self.assertEqual(list(Path('.').iterdir()),[])

    def test_write_short_write_corruption_and_close_failure_are_reported(self):
        for failure in ('write','short','corrupt','close'):
            with self.subTest(failure=failure):
                report=self.run_storage(failure)
                self.assertEqual(report['stop_reason'],'error')
                self.assertFalse(report['cases'][0]['verified'])
                self.assertTrue(report['cases'][0]['errors'])
                self.assertEqual(len(report['cases']),1)
                self.assertEqual(report['cases'][0]['timing']['close']['count'],1)

    def test_interrupt_closes_file_and_saves_partial_report(self):
        report=self.run_storage('interrupt')
        self.assertEqual(report['stop_reason'],'keyboard_interrupt')
        self.assertEqual(report['cases'][0]['timing']['close']['count'],1)
        self.assertTrue(Path(report['report_file']).exists())
        self.assertFalse(report['cases'][0]['verified'])

    def test_missing_sync_is_visible(self):
        del self.fs.sync
        report=self.run_storage()
        self.assertFalse(report['sync_supported'])
        self.assertIsNone(report['cases'][0]['timing']['sync']['max_us'])

    def test_test_pin_collision_rejected_and_defaults_preserved(self):
        before=dict(config.SENSOR)
        with patch.dict(config.LOGGER_BENCH,{'channel_pin':config.GPS['rx']}):
            with self.assertRaises(ValueError): logger_bench._settings()
        with patch.object(config,'AUTO_START',True):
            with self.assertRaises(ValueError): logger_bench._settings()
        with patch.dict(config.LOGGER_BENCH,{'ram_records_per_block':64}):
            with self.assertRaises(ValueError): logger_bench._settings()
        self.assertEqual(config.SENSOR,before)

    def run_ram(self, free_values, allocate=bytearray, opener=open, heap_info=None,
                prepare=None):
        memory=types.SimpleNamespace(collect=Mock(), mem_free=Mock(side_effect=free_values))
        with contextlib.redirect_stdout(io.StringIO()):
            report=logger_bench._ram_run(self.settings,self.clock,self.fs,opener,memory,
                                         allocate,heap_info,prepare)
        self.assertEqual(json.loads(Path(report['report_file']).read_text()),json.loads(json.dumps(report)))
        return report

    def test_ram_probe_reserves_target_and_releases_before_report(self):
        allocations=[]
        def allocate(size):
            # Modelliert einen Heap mit genug Gesamtplatz, aber keinem
            # grossen freien Bereich. Der bisherige 91-kB-Puffer passt nicht.
            if size > 4096:
                raise MemoryError()
            allocations.append(size)
            return bytearray(size)
        report=self.run_ram([200000,108992,198000],allocate)
        self.assertEqual(allocations,[2304]*39+[1152])
        self.assertEqual(sum(allocations),91008)
        self.assertEqual(report['status'],'fits_preliminary')
        self.assertEqual(report['target_samples'],632)
        self.assertEqual(report['block_count'],40)
        self.assertEqual(report['max_block_bytes'],2304)
        self.assertEqual(report['storage_strategy'],'record_aligned_blocks')
        self.assertTrue(report['allocation_ok'])
        self.assertTrue(report['content_verified'])
        self.assertEqual(report['allocated_blocks'],40)
        self.assertEqual(report['allocated_payload_bytes'],91008)
        self.assertFalse(report['allocator_failed'])
        self.assertIsNone(report['free_at_allocator_failure_bytes'])
        self.assertFalse(report['flight_timing_qualified'])
        self.assertFalse(report['record_format_implemented'])
        self.assertFalse(report['final_control_objects_allocated'])
        self.assertEqual(report['timing_thresholds']['deadline_us'],config.MAX_LOOP_US)
        self.assertEqual(report['free_after_release_bytes'],198000)

    def test_ram_probe_refuses_low_free_space_without_allocating(self):
        allocate=Mock()
        report=self.run_ram([100000,100000],allocate)
        allocate.assert_not_called()
        self.assertFalse(report['allocation_ok'])
        self.assertEqual(report['status'],'insufficient_ram')
        self.assertEqual(report['allocated_blocks'],0)

    def test_ram_probe_handles_fragmentation_without_silent_smaller_buffer(self):
        allocate=Mock(side_effect=MemoryError())
        report=self.run_ram([200000,190000,198000],allocate)
        allocate.assert_called_once_with(2304)
        self.assertEqual(report['status'],'allocation_failed')
        self.assertEqual(report['requested_bytes'],91008)
        self.assertFalse(report['allocation_ok'])
        self.assertEqual(report['allocated_blocks'],0)
        self.assertEqual(report['free_at_allocator_failure_bytes'],190000)
        self.assertEqual(report['failure_location'],'block_allocator')

    def test_ram_probe_checks_actual_reserve_after_allocation(self):
        report=self.run_ram([200000,50000,198000])
        self.assertTrue(report['allocation_ok'])
        self.assertEqual(report['status'],'insufficient_reserve')

    def test_ram_partial_allocation_and_interrupt_release_before_json(self):
        class Block(bytearray):
            pass
        for error, status in ((MemoryError,'allocation_failed'),
                              (KeyboardInterrupt,'keyboard_interrupt')):
            with self.subTest(error=error):
                refs=[]
                def allocate(size):
                    if len(refs)==5:
                        raise error()
                    block=Block(size)
                    refs.append(weakref.ref(block))
                    return block
                def checked_open(path,mode):
                    self.assertEqual(len(refs),5)
                    self.assertTrue(all(ref() is None for ref in refs))
                    return open(path,mode)
                free=[200000,180000,198000] if error is MemoryError else [200000,198000]
                report=self.run_ram(free,allocate,checked_open)
                self.assertEqual(report['status'],status)
                self.assertEqual(report['failure_phase'],'allocate')
                self.assertFalse(report['allocation_ok'])
                self.assertEqual(report['allocated_blocks'],5)
                self.assertEqual(report['allocated_payload_bytes'],11520)
                self.assertEqual(report['last_block_request_bytes'],2304)

    def test_ram_diagnosis_captures_failure_before_partial_buffer_release(self):
        allocated=[]
        snapshots=[]
        def allocate(size):
            if len(allocated)==3:
                raise MemoryError('memory allocation failed, allocating 2304 bytes')
            allocated.append(size)
            return bytearray(size)
        def heap_info():
            snapshots.append(len(allocated))
        report=self.run_ram([162608,154000,162400],allocate,heap_info=heap_info)
        self.assertEqual(snapshots,[0,3])
        self.assertTrue(report['heap_info_available'])
        self.assertEqual(report['allocated_blocks'],3)
        self.assertEqual(report['allocated_payload_bytes'],6912)
        self.assertEqual(report['free_at_allocator_failure_bytes'],154000)
        self.assertIn('2304 bytes',report['error'])
        self.assertEqual(report['status'],'allocation_failed')

    def test_ram_metadata_failure_is_distinct_from_payload_allocation_failure(self):
        allocate=Mock()
        with patch.object(logger_bench,'RecordBuffer',side_effect=MemoryError('metadata')):
            report=self.run_ram([162608,162400],allocate)
        allocate.assert_not_called()
        self.assertEqual(report['allocated_blocks'],0)
        self.assertEqual(report['last_block_request_bytes'],0)
        self.assertFalse(report['allocator_failed'])
        self.assertIsNone(report['free_at_allocator_failure_bytes'])
        self.assertEqual(report['failure_location'],'buffer_setup_or_probe_runtime')

    def test_ram_failed_verification_is_reported(self):
        with patch.object(logger_bench,'_probe_records',side_effect=RuntimeError('corrupt')):
            report=self.run_ram([200000,198000])
        self.assertEqual(report['status'],'probe_failed')
        self.assertEqual(report['failure_phase'],'verify')
        self.assertFalse(report['content_verified'])
        self.assertFalse(report['allocation_ok'])

    def test_ram_reserves_before_imports_and_checks_final_reserve(self):
        # Modelliert die beobachtete Grenze: nach Imports passen nur 35 Bloecke.
        # Fruehe Reservierung muss alle 40 halten; danach kann die echte Reserve
        # immer noch zu knapp sein. Der grosse Ausgangswert darf das nicht kaschieren.
        state={'imports':False,'blocks':0}
        def allocate(size):
            if state['imports'] and state['blocks']>=35:
                raise MemoryError('fragmented after imports')
            state['blocks']+=1
            return bytearray(size)
        def prepare():
            self.assertEqual(state['blocks'],40)
            state['imports']=True
        report=self.run_ram([240000,64000,238000],allocate,prepare=prepare)
        self.assertTrue(report['runtime_modules_imported'])
        self.assertEqual(report['allocation_order'],'buffer_before_runtime_imports')
        self.assertEqual(report['capacity_estimate_stage'],'before_runtime_imports')
        self.assertEqual(report['allocated_payload_bytes'],91008)
        self.assertTrue(report['content_verified'])
        self.assertEqual(report['free_after_allocation_bytes'],64000)
        self.assertEqual(report['status'],'insufficient_reserve')

    def test_ram_import_failure_releases_whole_buffer_before_report(self):
        class Block(bytearray):
            pass
        for error in (MemoryError('compiler needs RAM'), ImportError('module missing'),
                      KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                refs=[]
                def allocate(size):
                    block=Block(size)
                    refs.append(weakref.ref(block))
                    return block
                def prepare():
                    self.assertEqual(len(refs),40)
                    self.assertTrue(all(ref() is not None for ref in refs))
                    raise error
                def checked_open(path,mode):
                    self.assertTrue(all(ref() is None for ref in refs))
                    return open(path,mode)
                report=self.run_ram([240000,238000],allocate,checked_open,prepare=prepare)
                self.assertEqual(report['failure_phase'],'runtime_imports')
                self.assertEqual(report['status'],'keyboard_interrupt' if
                                 isinstance(error,KeyboardInterrupt) else 'runtime_import_failed')
                self.assertFalse(report['runtime_modules_imported'])
                self.assertFalse(report['content_verified'])
                self.assertFalse(report['allocator_failed'])

    def test_run_ram_entry_passes_imports_to_after_buffer_phase(self):
        order=[]
        real_buffer=logger_bench.RecordBuffer
        def buffer_factory(*args):
            self.assertEqual(order,[])
            buffer=real_buffer(*args)
            order.append('buffer')
            return buffer
        def prepare():
            self.assertEqual(order,['buffer'])
            order.append('imports')
        memory=types.SimpleNamespace(collect=Mock(),
                                     mem_free=Mock(side_effect=[240000,145000,238000]))
        with patch.object(logger_bench,'RecordBuffer',side_effect=buffer_factory), \
             patch.object(logger_bench,'_import_logger_modules',side_effect=prepare), \
             patch.object(logger_bench,'gc',memory), \
             patch.object(logger_bench,'time',self.clock), \
             patch.object(logger_bench,'os',self.fs), \
             patch.dict(sys.modules,{'micropython':types.SimpleNamespace(mem_info=Mock())}), \
             contextlib.redirect_stdout(io.StringIO()):
            report=logger_bench.run_ram()
        self.assertEqual(order,['buffer','imports'])
        self.assertEqual(report['status'],'fits_preliminary')
        self.assertTrue(report['runtime_modules_imported'])
        self.assertFalse(logger_bench._running)

    def channel_receiver(self, close_error=False):
        class RX:
            def __init__(self):
                self.count=0
                self.closed=False
                self.channels={'record':{'pulse':None,'sequence':0}}
            def poll(self,now):
                self.count+=1
                if self.count>2: raise KeyboardInterrupt()
                self.channels['record'].update(pulse=1100 if self.count==1 else 1900,
                                               sequence=self.count)
            def fresh(self,axis,now): return True
            def close(self):
                self.closed=True
                if close_error: raise OSError('PIO close failed')
        return RX()

    def test_channel_report_only_after_pio_stop(self):
        rx=self.channel_receiver()
        def checked_open(path,mode):
            self.assertTrue(rx.closed)
            return open(path,mode)
        with contextlib.redirect_stdout(io.StringIO()):
            report=logger_bench._channel_run(self.settings,self.clock,self.fs,checked_open,
                                              lambda settings:rx)
        self.assertTrue(report['shutdown_ok'])
        self.assertEqual(report['pulse_min_us'],1100)
        self.assertEqual(report['pulse_max_us'],1900)
        self.assertEqual(report['fresh_frames'],2)

    def test_no_channel_export_when_pio_stop_fails(self):
        rx=self.channel_receiver(close_error=True)
        opener=Mock()
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(OSError):
            logger_bench._channel_run(self.settings,self.clock,self.fs,opener,lambda s:rx)
        opener.assert_not_called()


if __name__ == '__main__':
    unittest.main()
