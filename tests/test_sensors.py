"""Hosttests fuer GPS/MS5611 und den separaten Sensorstarter; keine Hardware.

Referenzen: MS5611-Datenblatt Testvektor (20.07 C / 100009 Pa), AN520 CRC-Vektor.
UART/I2C werden durch endliche Datenquellen ersetzt; keine realen Ports/Uploads.
"""
import contextlib
import csv
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'firmware'))
import config
from gps import GPS, checked_fields, parse_fields
from ms5611 import MS5611, compensate, crc4, relative_altitude, validate_prom
import sensor_test

COEFFICIENTS = [0, 40127, 36924, 23317, 23282, 33464, 28312, 0]
PROM = COEFFICIENTS[:]
PROM[7] = crc4(PROM)
MOD = 1 << 30


def diff(a, b):
    return (a - b + MOD // 2) % MOD - MOD // 2


def sentence(payload):
    checksum = 0
    for byte in payload.encode():
        checksum ^= byte
    return ('$%s*%02X\r\n' % (payload, checksum)).encode()


GGA = sentence('GNGGA,123519.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,')
RMC = sentence('GNRMC,123519.00,A,4807.038,N,01131.000,E,22.4,84.4,181026,,,A')


class FakeUART:
    def __init__(self, data=b''):
        self.data = data
        self.closed = False
        self.read_sizes = []

    def any(self):
        return len(self.data)

    def read(self, length):
        self.read_sizes.append(length)
        result, self.data = self.data[:length], self.data[length:]
        return result or None

    def deinit(self):
        self.closed = True


class FakeBus:
    def __init__(self, prom=None, addresses=None):
        self.prom = PROM[:] if prom is None else prom
        self.addresses = [0x77] if addresses is None else addresses
        self.command = None
        self.conversion = None
        self.commands = []

    def scan(self):
        return self.addresses

    def writeto(self, address, data):
        self.command = data[0]
        self.commands.append(self.command)
        if self.command in (0x48, 0x58):
            self.conversion = self.command
        return 1

    def readfrom(self, address, length):
        if 0xa0 <= self.command <= 0xae:
            return self.prom[(self.command - 0xa0) // 2].to_bytes(2, 'big')
        value = 8569150 if self.conversion == 0x58 else 9085466
        return value.to_bytes(3, 'big')


class FakeClock:
    def __init__(self):
        self.us = 0

    def ticks_ms(self):
        return (self.us // 1000) % MOD

    def ticks_us(self):
        return self.us % MOD

    ticks_diff = staticmethod(diff)

    def sleep_ms(self, value):
        self.us += value * 1000

    def sleep_us(self, value):
        self.us += value


class ArrivingUART:
    """9600-Baud-Stream: ein zu grosser read wartet auf kuenftige Zeichen.

    Modelliert den RP2-Zeichenabstand auch bei timeout=0. Keine echte Wartezeit
    und keine Hardware: nur die Testuhr rueckt waehrend eines solchen reads vor.
    """
    def __init__(self, clock, stream):
        self.clock, self.stream = clock, stream
        self.offset = 0
        self.read_sizes = []

    def any(self):
        received = min(len(self.stream), self.clock.us // 1042 + 1)
        return max(0, received - self.offset)

    def read(self, length):
        self.read_sizes.append(length)
        end = min(len(self.stream), self.offset + length)
        if length > self.any():
            self.clock.us = max(self.clock.us, (end - 1) * 1042)
            if end - self.offset < length:
                self.clock.us += 3000  # RP2: mindestens 2 ms Zeichen-Timeout.
        result = self.stream[self.offset:end]
        self.offset = end
        return result or None


class GPSParsingTests(unittest.TestCase):
    def receiver(self):
        return GPS(FakeUART(), diff)

    def test_primary_nmea_example_checksum_coordinates_and_units(self):
        # u-blox-Koordinatenbeispiel: *57 passt zur Form ohne optionales navStatus.
        # Die R28-PDF zeigt auch ',V*57'; dessen Pruefsumme ist tatsaechlich falsch.
        raw = b'$GPRMC,083559.00,A,4717.11437,N,00833.91522,E,0.004,77.52,091202,,,A*57\r\n'
        data = parse_fields(checked_fields(raw))
        self.assertTrue(data['valid'])
        self.assertAlmostEqual(data['lat'], 47.2852395)
        self.assertAlmostEqual(data['lon'], 8.5652536666667)
        self.assertAlmostEqual(data['speed_ms'], 0.0020577777778)
        self.assertEqual(data['course_deg'], 77.52)
        with self.assertRaises(ValueError):
            checked_fields(raw.replace(b'A*57', b'A,V*57'))

    def test_chunked_multi_gnss_pair_has_explicit_units_and_course(self):
        gps = self.receiver()
        stream = GGA + RMC
        for index in range(0, len(stream), 7):
            gps.feed(stream[index:index+7], 100)
        data = gps.snapshot(110)
        self.assertTrue(data['valid'])
        self.assertAlmostEqual(data['lat'], 48.1173)
        self.assertAlmostEqual(data['lon'], 11.516666666667)
        self.assertAlmostEqual(data['speed_ms'], 11.5235555555)
        self.assertEqual(data['altitude_msl_m'], 545.4)
        self.assertTrue(data['course_usable'])
        self.assertEqual(gps.counters['bytes'],len(stream))

    def test_reusable_snapshot_clears_stale_and_no_fix_values(self):
        gps=self.receiver()
        scratch={}
        gps.feed(GGA+RMC,0)
        self.assertIs(gps.snapshot(100,scratch),scratch)
        coherent=dict(scratch)
        self.assertTrue(coherent['valid'])
        self.assertIs(gps.snapshot(2600,scratch),scratch)
        self.assertFalse(scratch['valid'])
        for key in ('lat','lon','hdop','altitude_msl_m','speed_ms','course_deg'):
            self.assertIsNone(scratch[key])
        gps.feed(sentence('GNGGA,123520.00,,,,,0,00,99.99,,,,,,'),2700)
        self.assertIs(gps.snapshot(2700,scratch),scratch)
        self.assertFalse(scratch['valid'])
        self.assertIsNone(scratch['lat'])
        gps.feed(GGA+RMC,3000)
        gps.snapshot(3010,scratch)
        self.assertTrue(scratch['valid'])
        self.assertEqual(scratch['gga_age_ms'],10)
        self.assertEqual(coherent['gga_age_ms'],100)

    def test_no_fix_clears_previous_position_without_inventing_zero(self):
        gps = self.receiver()
        gps.feed(GGA + RMC, 0)
        gps.feed(sentence('GNGGA,123520.00,,,,,0,00,99.99,,,,,,'), 1000)
        data = gps.snapshot(1000)
        self.assertFalse(data['valid'])
        self.assertIsNone(data['lat'])
        self.assertIsNone(data['altitude_msl_m'])

    def test_mixed_utc_epochs_cannot_be_a_paired_fix(self):
        gps = self.receiver()
        gps.feed(GGA, 0)
        gps.feed(sentence('GNRMC,123520.00,A,4807.038,N,01131.000,E,22.4,84.4,181026,,,A'), 1000)
        self.assertFalse(gps.snapshot(1000)['valid'])

    def test_stale_data_and_tick_wrap(self):
        gps = self.receiver()
        gps.feed(GGA + RMC, MOD - 100)
        self.assertTrue(gps.snapshot(100)['valid'])
        self.assertFalse(gps.snapshot(2400)['valid'])
        self.assertEqual(gps.snapshot(100)['gga_age_ms'], 200)

    def test_bad_checksum_overlong_and_noise_resynchronise(self):
        gps = self.receiver()
        gps.feed(b'garbage\xff$' + b'x'*400 + b'\n$broken\xff\n' + GGA + RMC, 0)
        self.assertEqual(len(gps.buffer), 128)
        self.assertEqual(gps.counters['overlong'], 1)
        self.assertEqual(gps.counters['checksum_errors'], 1)
        self.assertTrue(gps.snapshot(0)['valid'])
        with self.assertRaises(ValueError):
            checked_fields(RMC.replace(b'*', b'*00'))

    def test_checksum_bytes_preserve_ascii_and_strict_hex_validation(self):
        payload = 'GNTXT,' + ''.join(chr(n) for n in range(32, 127) if n != 42)
        raw = sentence(payload)
        self.assertEqual(','.join(checked_fields(raw)), payload)
        for checksum in (b'G0', b'+1', b' 1', b'0', b'000', b'\xc3\xa9'):
            with self.subTest(checksum=checksum), self.assertRaises(ValueError):
                checked_fields(raw.split(b'*')[0] + b'*' + checksum)
        for payload in ('GNTXT,\x1f', 'GNTXT,\x7f', 'GNTXT,\u00e9'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                checked_fields(sentence(payload))

    def test_bad_coordinates_nan_and_non_metre_altitude_rejected(self):
        for payload in (
                'GNGGA,123519.00,4860.000,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,',
                'GNGGA,123519.00,4807.038,N,01131.000,E,1,08,nan,545.4,M,46.9,M,,',
                'GNGGA,123519.00,4807.038,N,01131.000,E,1,08,0.9,545.4,F,46.9,M,,'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                parse_fields(checked_fields(sentence(payload)))

    def test_southern_western_coordinates_and_stationary_course(self):
        gps = self.receiver()
        gps.feed(sentence('GNGGA,123519.00,4807.038,S,01131.000,W,1,08,0.9,545.4,M,46.9,M,,'), 0)
        gps.feed(sentence('GNRMC,123519.00,A,4807.038,S,01131.000,W,0.1,84.4,181026,,,A'), 0)
        data = gps.snapshot(0)
        self.assertTrue(data['valid'])
        self.assertLess(data['lat'], 0)
        self.assertLess(data['lon'], 0)
        self.assertFalse(data['course_usable'])

    def test_estimated_simulated_and_void_rmc_cannot_be_valid(self):
        for status, mode in (('V', 'A'), ('A', 'E'), ('A', 'S'), ('A', 'M')):
            gps = self.receiver()
            gps.feed(GGA + sentence('GNRMC,123519.00,%s,4807.038,N,01131.000,E,22.4,84.4,181026,,,%s' %
                                    (status, mode)), 0)
            self.assertFalse(gps.snapshot(0)['valid'])

    def test_long_poll_gap_discards_backlog_and_demands_new_data(self):
        uart = FakeUART(GGA + RMC)
        gps = GPS(uart, diff)
        gps.poll(0)
        self.assertTrue(gps.snapshot(0)['valid'])
        uart.data = GGA + RMC
        gps.poll(101)
        self.assertFalse(gps.snapshot(101)['valid'])
        self.assertEqual(gps.counters['poll_gaps'], 1)
        self.assertEqual(uart.read_sizes[-1], len(GGA + RMC))
        uart.data = GGA + RMC
        gps.poll(111)
        self.assertTrue(gps.snapshot(111)['valid'])

    def test_uart_reads_are_bounded(self):
        uart = FakeUART(b'x' * 1000)
        gps = GPS(uart, diff, max_read=64)
        gps.poll(0)
        self.assertEqual(uart.read_sizes, [64])
        self.assertEqual(len(uart.data), 936)

    def test_serial_burst_does_not_make_poll_wait_or_erase_a_valid_pair(self):
        clock = FakeClock()
        uart = ArrivingUART(clock, GGA + RMC + b'x' * 1024)
        gps = GPS(uart, diff)
        for _ in range(30):
            before = clock.us
            gps.poll(clock.ticks_ms())
            self.assertEqual(clock.us, before, 'poll waited for future UART bytes')
            clock.sleep_ms(10)
        self.assertTrue(gps.snapshot(clock.ticks_ms())['valid'])
        self.assertEqual(gps.counters['poll_gaps'], 0)

    def test_poll_gap_discard_does_not_wait_for_future_serial_bytes(self):
        clock = FakeClock()
        uart = ArrivingUART(clock, (GGA + RMC) * 20)
        gps = GPS(uart, diff)
        gps.feed(GGA + RMC, 0)
        gps.last_poll = 0
        clock.sleep_ms(110)
        before = clock.us
        gps.poll(clock.ticks_ms())
        self.assertEqual(clock.us, before, 'backlog discard waited for future bytes')
        self.assertFalse(gps.snapshot(clock.ticks_ms())['valid'])
        self.assertEqual(gps.counters['poll_gaps'], 1)

    def test_receiver_fix_evidence_survives_freshness_reset(self):
        gps = self.receiver()
        gps.feed(sentence('GNGGA,123519.00,,,,,0,00,99.99,,,,,,'), 0)
        gps.feed(sentence('GNRMC,123519.00,V,,,,,,,191026,,,N'), 0)
        self.assertEqual(gps.counters['gga_fix_sentences'], 0)
        self.assertEqual(gps.counters['rmc_fix_sentences'], 0)
        self.assertEqual(gps.counters['max_satellites_used'], 0)
        gps.feed(GGA + RMC, 10)
        gps.poll(10)
        gps.poll(111)
        self.assertFalse(gps.snapshot(111)['valid'])
        self.assertEqual(gps.counters['gga_fix_sentences'], 1)
        self.assertEqual(gps.counters['rmc_fix_sentences'], 1)
        self.assertEqual(gps.counters['max_satellites_used'], 8)


class BarometerTests(unittest.TestCase):
    def test_crc_primary_an520_vector_and_input_unchanged(self):
        vector = [0x3132, 0x3334, 0x3536, 0x3738, 0x3940, 0x4142, 0x4344, 0x4500]
        original = vector[:]
        self.assertEqual(crc4(vector), 0xb)
        self.assertEqual(vector, original)

    def test_datasheet_pressure_temperature_vector(self):
        pressure, temperature = compensate(PROM, 9085466, 8569150)
        self.assertEqual(pressure, 100009)
        self.assertEqual(temperature, 20.07)

    def test_second_order_very_cold_and_out_of_range(self):
        # Unabhaengig mit Dezimalrechnung der Datenblattformeln ausgewertet.
        pressure, temperature = compensate(PROM, 9085466, 7500000)
        self.assertAlmostEqual(pressure, 91910.50667046, delta=3)
        self.assertAlmostEqual(temperature, -21.303886, delta=0.03)
        with self.assertRaises(ValueError):
            compensate(PROM, 9085466, 7000000)  # ca. -44.31 C, ausserhalb Spezifikation.

    def test_corrupt_and_empty_prom_rejected(self):
        broken = PROM[:]
        broken[2] ^= 1
        for prom in (broken, [0] * 8, [65535] * 8):
            with self.subTest(prom=prom), self.assertRaises(ValueError):
                validate_prom(prom)

    def test_nonblocking_conversion_waits_maximum_time_and_handles_wrap(self):
        bus, waits, clock = FakeBus(), [], FakeClock()
        baro = MS5611(bus, sleep_ms=waits.append, ticks_diff=diff, ticks_ms=clock.ticks_ms)
        self.assertEqual(waits, [3])
        clock.us = (MOD - 5) * 1000
        self.assertIsNone(baro.poll(clock.ticks_ms()))
        before = len(bus.commands)
        clock.sleep_ms(9)
        self.assertIsNone(baro.poll(clock.ticks_ms()))  # Neun ms reichen nicht.
        self.assertEqual(len(bus.commands), before)
        clock.sleep_ms(1)
        self.assertIsNone(baro.poll(clock.ticks_ms()))
        self.assertEqual(bus.commands[-1], 0x48)
        clock.sleep_ms(9)
        self.assertIsNone(baro.poll(clock.ticks_ms()))
        clock.sleep_ms(1)
        self.assertEqual(baro.poll(clock.ticks_ms())[:2], (100009, 20.07))

    def test_delayed_bus_command_cannot_shorten_adc_wait(self):
        bus, clock = FakeBus(), FakeClock()
        original = bus.writeto
        def delayed(address, data):
            if data[0] in (0x48, 0x58):
                clock.sleep_ms(5)
            return original(address, data)
        bus.writeto = delayed
        baro = MS5611(bus, sleep_ms=clock.sleep_ms, ticks_diff=diff, ticks_ms=clock.ticks_ms)
        baro.poll(clock.ticks_ms())
        before = len(bus.commands)
        clock.sleep_ms(9)
        self.assertIsNone(baro.poll(clock.ticks_ms()))
        self.assertEqual(len(bus.commands), before)
        clock.sleep_ms(1)
        baro.poll(clock.ticks_ms())
        self.assertEqual(bus.commands[-1], 0x48)

    def test_ambiguous_or_absent_address_and_short_read_rejected(self):
        for addresses in ([], [0x76, 0x77]):
            with self.assertRaises(ValueError):
                MS5611(FakeBus(addresses=addresses), sleep_ms=lambda n: None,
                        ticks_diff=diff, ticks_ms=lambda: 0)
        bus = FakeBus()
        bus.readfrom = lambda *args: b'\x00'
        with self.assertRaises(OSError):
            MS5611(bus, sleep_ms=lambda n: None, ticks_diff=diff, ticks_ms=lambda: 0)

    def test_relative_height_direction_and_invalid_pressure(self):
        self.assertEqual(relative_altitude(100000, 100000), 0)
        self.assertGreater(relative_altitude(99988, 100000), 0)
        self.assertAlmostEqual(relative_altitude(99988, 100000), 1.0123, delta=0.01)
        for value in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                relative_altitude(value, 100000)


class SensorLogTests(unittest.TestCase):
    @staticmethod
    def empty_baro():
        return {'valid': False, 'age_ms': -1, 'pressure_pa': None,
                'temperature_c': None, 'relative_height_m': None, 'd1': None, 'd2': None}

    def test_packed_roundtrip_preserves_coordinates_flags_and_missing_values(self):
        log = sensor_test.SensorLog(2)
        log.append_sample(0, {}, self.empty_baro(), 0)
        gps = GPS(FakeUART(), diff)
        gps.feed(GGA + RMC, 0)
        baro = {'valid': True, 'age_ms': 5, 'pressure_pa': 100009,
                'temperature_c': 20.07, 'relative_height_m': None,
                'd1': 9085466, 'd2': 8569150}
        log.append_sample(501, gps.snapshot(10), baro, 10010)
        rows = list(csv.DictReader(io.StringIO(log.HEADER + ''.join(log.ordered()))))
        self.assertEqual(rows[0]['lat_deg'], '')
        self.assertEqual(rows[0]['pressure_pa'], '')
        self.assertEqual(rows[0]['gga_age_ms'], '-1')
        self.assertEqual(rows[1]['lat_deg'], '48.1173000')
        self.assertEqual(rows[1]['lon_deg'], '11.5166667')
        self.assertEqual(rows[1]['utc'], '123519.000')
        self.assertEqual(rows[1]['date'], '181026')
        self.assertEqual(rows[1]['course_usable'], '1')
        self.assertEqual(rows[1]['baro_valid'], '1')
        self.assertEqual(rows[1]['pressure_pa'], '100009')
        self.assertEqual(rows[1]['temperature_c'], '20.07')
        self.assertEqual(rows[1]['relative_height_m'], '')
        self.assertEqual(rows[1]['d1'], '9085466')
        self.assertEqual(rows[1]['period_us'], '10010')

    def test_midnight_date_and_leap_second_survive_packing(self):
        log = sensor_test.SensorLog(2)
        for index, utc in enumerate(('000000.00', '235960.25')):
            log.append_sample(index, {'utc': utc, 'date': '010100'}, self.empty_baro(), 0)
        rows = list(csv.DictReader(io.StringIO(log.HEADER + ''.join(log.ordered()))))
        self.assertEqual([r['utc'] for r in rows], ['000000.000', '235960.250'])
        self.assertEqual([r['date'] for r in rows], ['010100', '010100'])

    def test_full_buffer_raises_without_overwriting_earlier_samples(self):
        log = sensor_test.SensorLog(2)
        for ms in (0, 500):
            log.append_sample(ms, {}, self.empty_baro(), 0)
        with self.assertRaises(RuntimeError):
            log.append_sample(1000, {}, self.empty_baro(), 0)
        rows = list(csv.DictReader(io.StringIO(log.HEADER + ''.join(log.ordered()))))
        self.assertEqual([r['ms'] for r in rows], ['0', '500'])
        self.assertEqual((log.total, log.count), (3, 2))


class SensorRunnerTests(unittest.TestCase):
    def devices(self, profile, clock, resources):
        self.uart = FakeUART(GGA + RMC)
        resources['uart'] = self.uart
        return (GPS(self.uart, clock.ticks_diff),
                MS5611(FakeBus(), sleep_ms=clock.sleep_ms, ticks_diff=clock.ticks_diff,
                        ticks_ms=clock.ticks_ms), self.uart)

    def test_import_and_bad_parameters_do_not_construct_hardware(self):
        class ForbiddenHardware:
            def __getattr__(self, name):
                raise AssertionError('Hardwarezugriff beim Import: ' + name)
        with patch.dict(sys.modules, {'machine': ForbiddenHardware()}):
            importlib.reload(sensor_test)
        with patch.object(sensor_test, '_devices') as factory:
            for profile, duration in (('unknown', 1), ('both', float('nan')), ('gps', 0)):
                with self.assertRaises(ValueError):
                    sensor_test.run(profile, duration_s=duration)
            factory.assert_not_called()

    def test_control_pin_conflict_and_autostart_rejected(self):
        with patch.dict(config.BAROMETER, {'sda': 6, 'scl': 7}):
            with self.assertRaises(ValueError):
                sensor_test.validate_settings('baro', 1, False)
        with patch.object(config, 'AUTO_START', True), self.assertRaises(ValueError):
            sensor_test.validate_settings('gps', 1, False)

    def test_full_run_export_is_after_uart_stop_and_contains_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            stem = str(Path(directory) / 'sensor_run')
            original_save = sensor_test.SensorLog.save
            def checked_save(log, path):
                self.assertTrue(self.uart.closed)
                original_save(log, path)
            with patch.object(sensor_test, '_devices', side_effect=self.devices), \
                    patch.object(sensor_test, '_free_stem', return_value=stem), \
                    patch.object(sensor_test.SensorLog, 'save', checked_save), \
                    patch.dict(config.SENSOR_TEST, {'reference_warmup_ms': 0, 'reference_samples': 2}), \
                    contextlib.redirect_stdout(io.StringIO()):
                report = sensor_test._run('both', 1, True, FakeClock())
            self.assertTrue(report['shutdown_ok'])
            self.assertEqual(report['errors'], {})
            self.assertTrue(report['checks']['paired_gps_fix_seen'])
            self.assertTrue(report['checks']['barometer_reference_ready'])
            self.assertFalse(report['control_loop_timing'])
            rows = list(csv.DictReader(io.StringIO(Path(stem + '.csv').read_text())))
            self.assertTrue(rows)
            self.assertNotIn(None, rows[0])
            self.assertEqual(rows[-1]['relative_height_m'], '0.00')
            self.assertEqual(json.loads(Path(stem + '.json').read_text())['schema'], 2)

    def test_three_minute_run_retains_beginning_and_end(self):
        with tempfile.TemporaryDirectory() as directory:
            stem = str(Path(directory) / 'whole_run')
            with patch.object(sensor_test, '_devices', side_effect=self.devices), \
                    patch.object(sensor_test, '_free_stem', return_value=stem), \
                    contextlib.redirect_stdout(io.StringIO()):
                report = sensor_test._run('both', 180, True, FakeClock())
            rows = list(csv.DictReader(io.StringIO(Path(stem + '.csv').read_text())))
            self.assertGreater(len(rows), 200)
            self.assertLess(int(rows[0]['ms']), 1000)
            self.assertGreater(int(rows[-1]['ms']), 179000)
            self.assertEqual(report['csv_rows_total'], len(rows))
            self.assertEqual(report['csv_rows_retained'], len(rows))
            self.assertTrue(report['log']['all_samples_retained'])
            self.assertLess(report['log']['allocated_bytes'], 65536)
            self.assertTrue(self.uart.closed)

    def test_log_size_limit_rejects_before_hardware_start(self):
        with patch.dict(config.SENSOR_TEST, {'max_log_bytes': 1}), \
                patch.object(sensor_test, '_devices') as factory:
            with self.assertRaises(ValueError):
                sensor_test.run('gps', duration_s=180)
            factory.assert_not_called()
            self.assertFalse(sensor_test._running)

    def test_low_mcu_memory_rejects_before_hardware_start(self):
        with patch.object(sensor_test.gc, 'mem_free', return_value=0, create=True), \
                patch.object(sensor_test, '_devices') as factory:
            with self.assertRaises(MemoryError):
                sensor_test.run('gps', duration_s=180)
            factory.assert_not_called()
            self.assertFalse(sensor_test._running)

    def test_partial_start_closes_uart_and_keeps_original_error(self):
        uart = FakeUART()
        def failed(profile, clock, resources):
            resources['uart'] = uart
            raise ValueError('PROM-CRC falsch')
        with patch.object(sensor_test, '_devices', side_effect=failed), \
                contextlib.redirect_stdout(io.StringIO()):
            report = sensor_test._run('both', 1, False, FakeClock())
        self.assertTrue(uart.closed)
        self.assertEqual(report['stop_reason'], 'error')
        self.assertIn('PROM-CRC', report['errors']['test']['message'])

    def test_runtime_barometer_failure_is_latched_and_not_reported_fresh(self):
        def devices(profile, clock, resources):
            gps, baro, uart = self.devices(profile, clock, resources)
            baro.poll = lambda now: (_ for _ in ()).throw(OSError('I2C read'))
            return gps, baro, uart
        saved = []
        def save(log, path):
            saved.extend(log.ordered())
        with patch.object(sensor_test, '_devices', side_effect=devices), \
                patch.object(sensor_test, '_free_stem', return_value='/unused'), \
                patch.object(sensor_test.SensorLog, 'save', save), \
                patch.object(sensor_test.json, 'dump'), \
                patch('builtins.open', unittest.mock.mock_open()), \
                contextlib.redirect_stdout(io.StringIO()):
            report = sensor_test._run('both', 1, True, FakeClock())
        self.assertIn('barometer', report['errors'])
        self.assertTrue(all(row.split(',')[17] == '0' for row in saved))

    def test_free_stem_does_not_overwrite_existing_csv_or_json(self):
        with tempfile.TemporaryDirectory() as directory:
            real_stat = sensor_test.os.stat
            def temporary_stat(path):
                return real_stat(str(Path(directory) / path))
            (Path(directory) / 'sensors_5_0.csv').write_text('original')
            (Path(directory) / 'sensors_5_1.json').write_text('original')
            with patch.object(sensor_test.os, 'stat', side_effect=temporary_stat):
                self.assertEqual(sensor_test._free_stem(5), 'sensors_5_2')

    def test_ctrl_c_closes_uart_and_preserves_log(self):
        clock = FakeClock()
        count = [0]
        original_sleep = clock.sleep_us
        def interrupt(delay):
            count[0] += 1
            if count[0] == 10:
                raise KeyboardInterrupt()
            original_sleep(delay)
        clock.sleep_us = interrupt
        with patch.object(sensor_test, '_devices', side_effect=self.devices), \
                contextlib.redirect_stdout(io.StringIO()):
            report = sensor_test._run('both', 1, False, clock)
        self.assertTrue(self.uart.closed)
        self.assertEqual(report['stop_reason'], 'keyboard_interrupt')
        self.assertGreater(report['csv_rows_retained'], 0)


if __name__ == '__main__':
    unittest.main()
