"""Hosttests ohne MCU: Geometrie, RC-Freigabe, Grenzen, Speicher und Ablauf.

Hauptteile: PureTests, FlowTests. machine/rp2 werden nur zum Import ersetzt;
die PIO-Assemblerfunktion selbst wird nicht am Host ausgefuehrt/verifiziert.
FlowTests pruefen die echte app.run()-Logik mit simuliertem Sensor/RC/Zeit.
Keine Aussage ueber Servoelektrik, echte PIO-Pulse oder Ausfuehrungszeiten.
Aufruf aus Projektordner: python3 -m unittest discover -s tests -v
"""
import contextlib
import io
import math
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'firmware'))
machine = types.ModuleType('machine')
machine.Pin = machine.I2C = machine.PWM = object
rp2 = types.ModuleType('rp2')
rp2.asm_pio = lambda **kwargs: lambda function: function
sys.modules['machine'], sys.modules['rp2'] = machine, rp2

import config
import app
import calibration
import receiver
import outputs
import calibrate_rc
import bench_test
from attitude import Attitude, quaternion, body_error
from receiver import normalize
from outputs import command
from control import AxisController, Gate, select_mode
from logger import RingLog
from diagnostics import BenchDiagnostics, TimingStats, rx_snapshot
from imu import validate_transform
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from analyze_bench import inspect_run, read_csv, main as analyze_main


class DiagnosticsTests(unittest.TestCase):
    def test_timing_extrema_and_counts_include_every_observation(self):
        stats = TimingStats(10000, 50000)
        for value in (None, 8000, 11000, 60000, -1):
            stats.add(value)
        report = stats.report()
        self.assertEqual(report['count'], 3)
        self.assertEqual(report['min_us'], 8000)
        self.assertEqual(report['max_us'], 60000)
        self.assertEqual(report['over_period'], 2)
        self.assertEqual(report['over_deadline'], 1)
        self.assertEqual(report['invalid'], 1)

    def test_transition_ring_is_bounded_and_retains_fault_only_changes(self):
        diag = BenchDiagnostics(10000, 50000, 2)
        rx = ([1500, 0, 0], [10, -1, -1], [1, 0, 0])
        for mode, fault in (('WAIT_NEUTRAL', ''), ('STABILIZE', ''), ('STABILIZE', 'IMU_RUNTIME')):
            self.assertTrue(diag.transition(0, mode, fault, True, True, 25, True, rx, {'roll': 1500}))
            diag.finish(None, 100, 10, 200, False)
        self.assertFalse(diag.transition(0, 'STABILIZE', 'IMU_RUNTIME', True, True, 25, True, rx, {'roll': 1500}))
        report = diag.report()
        self.assertEqual(len(report['events']), 2)
        self.assertEqual(report['events_dropped'], 1)
        self.assertEqual(report['events'][-1]['fault'], 'IMU_RUNTIME')
        self.assertEqual(report['fault_iterations'], {'IMU_RUNTIME': 1})
        self.assertEqual(report['iterations'], 3)

    def test_rx_snapshot_handles_tick_wrap_absent_channels_and_negative_age(self):
        channels = {'roll': {'pulse': 1500, 'time': 1010, 'sequence': 5}}
        diff = lambda a, b: (a-b+512) % 1024-512
        self.assertEqual(rx_snapshot(channels, ('roll',), 6, diff),
                         ([1500, 0, 0], [20, -1, -1], [5, 0, 0]))
        self.assertEqual(rx_snapshot(channels, ('roll',), 1000, diff)[1], [-1, -1, -1])

    def test_json_export_roundtrip(self):
        import json
        diag = BenchDiagnostics(10000, 50000, 2)
        diag.finish(10000, None, None, 200, False)
        with tempfile.TemporaryDirectory() as directory:
            path = str(pathlib.Path(directory)/'report.json')
            diag.save(path, {'version': 'test'})
            report = json.loads(pathlib.Path(path).read_text())
        self.assertEqual(report['version'], 'test')
        self.assertIsNone(report['timing']['pre_output']['max_us'])
        self.assertEqual(report['timing']['period']['max_us'], 10000)


class BenchProfileTests(unittest.TestCase):
    def test_import_and_invalid_profile_do_not_start_app(self):
        with patch.object(app, 'run') as run:
            with self.assertRaises(ValueError):
                bench_test.run('unknown')
            run.assert_not_called()

    def test_autostart_configuration_blocks_bench_entry(self):
        with patch.object(config, 'AUTO_START', True), patch.object(app, 'run') as run:
            with self.assertRaises(ValueError):
                bench_test.run('manual')
            run.assert_not_called()

    def test_test_overrides_are_restored_after_start_error_or_interrupt(self):
        for error in (OSError('Sensorstart'), KeyboardInterrupt()):
            def failed_run():
                self.assertEqual(config.START_MODE, 'stabilize')
                self.assertEqual(config.PITCH_CONTROL_LIMIT_DEG, 20.0)
                raise error
            with self.subTest(error=type(error).__name__), \
                 patch.object(config, 'START_MODE', 'sensor'), \
                 patch.object(config, 'PITCH_CONTROL_LIMIT_DEG', 75.0), \
                 patch.object(app, 'run', side_effect=failed_run), \
                 contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(type(error)):
                    bench_test.run('pitch-range')
                self.assertEqual(config.START_MODE, 'sensor')
                self.assertEqual(config.PITCH_CONTROL_LIMIT_DEG, 75.0)


class ReceiverTests(unittest.TestCase):
    """Echte Poll-/Cleanup-Logik, aber ausschliesslich simulierte PIO-Hardware."""
    def setUp(self):
        self.devices = []
        owner = self

        class Pin:
            IN, PULL_DOWN = 0, 1
            def __init__(self, *args): pass

        class StateMachine:
            def __init__(self, *args, **kwargs):
                self.queue, self.actions = [], []
                self.fail_stop = False
                owner.devices.append(self)
            def rx_fifo(self): return len(self.queue)
            def get(self): return self.queue.pop(0)
            def active(self, value):
                self.actions.append(('active', value))
                if value == 0 and self.fail_stop:
                    raise OSError('PIO stop failed')
            def restart(self): self.actions.append(('restart',))

        # Small modulus deliberately crosses wrap boundaries in the age tests.
        clock = types.SimpleNamespace(ticks_diff=lambda a, b: (a-b+512) % 1024-512)
        self.patches = [patch.object(receiver, 'Pin', Pin),
                        patch.object(receiver.rp2, 'StateMachine', StateMachine, create=True),
                        patch.object(receiver, 'time', clock)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.rx = receiver.Receiver(config.RECEIVER, ('roll', 'pitch'), 100)

    def test_first_poll_discards_unknown_age(self):
        self.devices[0].queue = [1800]
        self.rx.poll(100)
        self.assertFalse(self.rx.all_fresh(100))
        self.assertEqual(self.rx.channels['roll']['sequence'], 0)
        self.assertEqual(self.devices[0].queue, [])
        self.assertIn(('restart',), self.devices[0].actions)

    def test_pulse_age_uses_previous_poll_not_dequeue_time(self):
        self.rx.poll(100)
        for device in self.devices:
            device.queue = [1500]
        self.rx.poll(110)
        self.assertEqual(self.rx.channels['roll']['time'], 100)
        self.assertTrue(self.rx.all_fresh(199))
        self.assertFalse(self.rx.all_fresh(200))

    def test_stall_discards_fifo_and_requires_new_frames(self):
        self.rx.poll(100)
        for device in self.devices:
            device.queue = [1500]
        self.rx.poll(110)
        for device in self.devices:
            device.queue = [1800, 1800]
        self.rx.poll(170)  # longer than the 50 ms polling budget
        self.assertFalse(self.rx.all_fresh(170))
        self.assertEqual(self.rx.channels['roll']['sequence'], 1)
        for device in self.devices:
            self.assertEqual(device.queue, [])
            device.queue = [1500]
        self.rx.poll(180)
        self.assertTrue(self.rx.all_fresh(180))
        self.assertEqual(self.rx.channels['roll']['pulse'], 1500)

    def test_full_fifo_is_rejected_even_without_long_gap(self):
        self.rx.poll(100)
        self.devices[0].queue = [1500]*4
        self.devices[1].queue = [1500]
        self.rx.poll(110)
        self.assertFalse(self.rx.all_fresh(110))
        self.assertIsNone(self.rx.channels['roll']['pulse'])

    def test_invalid_pulse_clears_freshness(self):
        self.rx.poll(100)
        self.devices[0].queue = [1500, 2200]
        self.devices[1].queue = [1500]
        self.rx.poll(110)
        self.assertFalse(self.rx.all_fresh(110))
        self.assertIsNone(self.rx.channels['roll']['pulse'])

    def test_poll_and_timeout_across_tick_wrap(self):
        self.rx.poll(1010)
        for device in self.devices:
            device.queue = [1500]
        self.rx.poll(6)  # 20 ms later
        self.assertTrue(self.rx.all_fresh(6))
        self.assertFalse(self.rx.all_fresh(86))  # exactly 100 ms old

    def test_negative_age_is_not_fresh(self):
        self.rx.poll(100)
        self.devices[0].queue = [1500]
        self.rx.poll(110)
        self.assertFalse(self.rx.fresh('roll', 99))

    def test_close_attempts_all_channels_after_failure(self):
        self.devices[0].fail_stop = True
        with self.assertRaises(OSError):
            self.rx.close()
        self.assertEqual(self.devices[1].actions[-1], ('active', 0))

    def test_poll_consumes_only_snapshot_and_keeps_new_arrivals_for_next_poll(self):
        self.rx.poll(100)
        device = self.devices[0]
        device.queue = [1500]
        original_get = device.get
        def get_with_new_arrival():
            value = original_get()
            device.queue.append(1600)
            return value
        device.get = get_with_new_arrival
        self.rx.poll(110)
        self.assertEqual(self.rx.channels['roll']['sequence'], 1)
        self.assertEqual(device.queue, [1600])
        device.get = original_get
        self.rx.poll(120)
        self.assertEqual(self.rx.channels['roll']['pulse'], 1600)
        self.assertEqual(self.rx.channels['roll']['time'], 110)

    def test_interrupted_pio_start_closes_already_created_channels(self):
        original = receiver.rp2.StateMachine
        created = []
        def interrupted_start(index, *args, **kwargs):
            if index == 1:
                raise KeyboardInterrupt
            device = original(index, *args, **kwargs)
            created.append(device)
            return device
        with patch.object(receiver.rp2, 'StateMachine', interrupted_start):
            with self.assertRaises(KeyboardInterrupt):
                receiver.Receiver(config.RECEIVER, ('roll', 'pitch'), 100)
        self.assertEqual(created[0].actions[-1], ('active', 0))


class ConfigurationTests(unittest.TestCase):
    def test_defaults_are_valid(self):
        app.validate_config()

    def test_invalid_scheduling_values(self):
        cases = [('LOOP_US', 0), ('LOOP_US', 50001), ('MAX_LOOP_US', 50001),
                 ('MAX_LOOP_US', 9999), ('RX_TIMEOUT_MS', 0), ('RX_TIMEOUT_MS', 50),
                 ('NEUTRAL_FRAMES', 0), ('NEUTRAL_WINDOW', 1),
                 ('LOG_HZ', 0), ('LOG_HZ', float('nan')), ('CONSOLE_HZ', 0),
                 ('LOG_CAPACITY', 0), ('PITCH_CONTROL_LIMIT_DEG', 90)]
        cases.extend([('EVENT_CAPACITY', 0), ('EVENT_CAPACITY', 257)])
        for name, value in cases:
            with self.subTest(name=name, value=value), patch.object(config, name, value):
                with self.assertRaises(ValueError):
                    app.validate_config()

    def test_nonfinite_servo_trim_rejected(self):
        settings = dict(config.SERVOS, roll=dict(config.SERVOS['roll'], trim=float('nan')))
        with patch.object(config, 'SERVOS', settings), self.assertRaises(ValueError):
            app.validate_config()

    def test_invalid_controller_values_rejected(self):
        for name, value in [('rate_p', float('inf')), ('rate_i', -1), ('max_rate', 0)]:
            settings = dict(config.CONTROLLERS,
                            roll=dict(config.CONTROLLERS['roll'], **{name: value}))
            with self.subTest(name=name), patch.object(config, 'CONTROLLERS', settings):
                with self.assertRaises(ValueError):
                    app.validate_config()

    def test_incomplete_sensor_vectors_rejected(self):
        for name in ('body_axes', 'body_signs', 'acc_offset', 'acc_scale'):
            settings = dict(config.SENSOR, **{name: (1, 1)})
            with self.subTest(name=name), patch.object(config, 'SENSOR', settings):
                with self.assertRaises(ValueError):
                    app.validate_config()

    def test_invalid_config_rejected_before_any_hardware_construction(self):
        with patch.object(config, 'LOG_HZ', 0), patch.object(app, 'IMU') as imu, \
             patch.object(app, 'Receiver') as rx, patch.object(app, 'Outputs') as pwm:
            with self.assertRaises(ValueError):
                app.run()
        imu.assert_not_called()
        rx.assert_not_called()
        pwm.assert_not_called()

    def test_unchecked_axis_cannot_start_stabilization(self):
        with patch.object(config, 'START_MODE', 'stabilize'), \
             patch.object(config, 'ACTIVE_AXES', ('roll', 'pitch')), \
             patch.object(config, 'DIRECTION_CHECKED_AXES', ('roll',)), \
             patch.object(app, 'IMU') as imu, patch.object(app, 'Outputs') as pwm:
            with self.assertRaisesRegex(ValueError, 'pitch'):
                app.run()
        imu.assert_not_called()
        pwm.assert_not_called()

    def test_manual_allows_direction_check_of_new_axis(self):
        with patch.object(config, 'START_MODE', 'manual'), \
             patch.object(config, 'ACTIVE_AXES', ('roll', 'pitch')), \
             patch.object(config, 'DIRECTION_CHECKED_AXES', ('roll',)):
            app.validate_config()


class CalibrationSelectionTests(unittest.TestCase):
    def test_pitch_only_calibration_preserves_roll_and_level(self):
        roll = {'min': 1053, 'center': 1554, 'max': 1998}
        level = {'roll': -3, 'pitch': 7}
        data = {'schema': 1, 'rc': {'roll': dict(roll)}, 'level': dict(level)}
        with patch.object(config, 'ACTIVE_AXES', ('roll', 'pitch')), \
             patch.object(calibrate_rc, 'load', return_value=data), \
             patch.object(calibrate_rc, 'Receiver') as rx, \
             patch.object(calibrate_rc, 'collect', side_effect=[[1500]*30, [1000]*30+[2000]*30]), \
             patch.object(calibrate_rc, 'save') as save, patch('builtins.input', return_value=''), \
             contextlib.redirect_stdout(io.StringIO()):
            calibrate_rc.run(('pitch',))
        self.assertEqual(rx.call_args[0][1], ('pitch',))
        self.assertEqual(data['rc']['roll'], roll)
        self.assertEqual(data['level'], level)
        self.assertEqual(data['rc']['pitch'], {'min': 1000, 'center': 1500, 'max': 2000})
        save.assert_called_once_with(config.CALIBRATION_FILE, data)
        rx.return_value.close.assert_called_once()

    def test_inactive_axis_is_rejected_before_receiver_start(self):
        with patch.object(config, 'ACTIVE_AXES', ('roll', 'pitch')), \
             patch.object(calibrate_rc, 'Receiver') as rx:
            with self.assertRaises(ValueError):
                calibrate_rc.run(('yaw',))
        rx.assert_not_called()


class CleanupTests(unittest.TestCase):
    def test_pwm_failure_still_attempts_zero_deinit_and_low_on_all_outputs(self):
        actions = []

        class Pin:
            OUT = 1
            def __init__(self, pin, *args, **kwargs): actions.append(('low', pin))

        class PWM:
            def __init__(self, name, fail=False): self.name, self.fail = name, fail
            def duty_ns(self, value): actions.append(('zero', self.name, value))
            def deinit(self):
                actions.append(('deinit', self.name))
                if self.fail: raise OSError('PWM deinit failed')

        out = outputs.Outputs.__new__(outputs.Outputs)
        out.settings = config.SERVOS
        out.devices = {'roll': PWM('roll', True), 'pitch': PWM('pitch')}
        with patch.object(outputs, 'Pin', Pin), self.assertRaises(OSError):
            out.close()
        self.assertEqual(actions, [('zero', 'roll', 0), ('deinit', 'roll'), ('low', 3),
                                   ('zero', 'pitch', 0), ('deinit', 'pitch'), ('low', 6)])

    def test_interrupted_pwm_start_closes_first_device(self):
        actions = []
        class Pin:
            OUT = 1
            def __init__(self, pin, *args, **kwargs):
                self.pin = pin
                if kwargs.get('value') == 0: actions.append(('low', pin))
        class PWM:
            def __init__(self, pin, **kwargs):
                if pin.pin == 6: raise KeyboardInterrupt
            def duty_ns(self, value): actions.append(('zero', value))
            def deinit(self): actions.append(('deinit',))
        with patch.object(outputs, 'Pin', Pin), patch.object(outputs, 'PWM', PWM):
            with self.assertRaises(KeyboardInterrupt):
                outputs.Outputs(config.SERVOS, ('roll', 'pitch'))
        self.assertEqual(actions, [('zero', 0), ('deinit',), ('low', 3)])


class PureTests(unittest.TestCase):
    def test_asymmetric_rc_endpoints(self):
        cal = {'min': 1000, 'center': 1375, 'max': 2000}
        self.assertEqual(normalize(1000, cal), -1)
        self.assertEqual(normalize(1375, cal), 0)
        self.assertEqual(normalize(2000, cal), 1)
        self.assertEqual(normalize(2000, cal, -1), -1)
        self.assertEqual(normalize(3000, cal), 1)

    def test_deadband_continuous(self):
        cal = {'min': 1000, 'center': 1500, 'max': 2000}
        self.assertEqual(normalize(1510, cal), 0)
        self.assertAlmostEqual(normalize(1520, cal), 0)
        self.assertGreater(normalize(1521, cal), 0)
        self.assertLess(normalize(1521, cal), 0.003)

    def test_gate_new_frames_only(self):
        gate = Gate(3)
        for _ in range(100):
            self.assertFalse(gate.update(True, [0], False))
        for _ in range(2):
            self.assertFalse(gate.update(True, [0], True))
        self.assertTrue(gate.update(True, [0], True))

    def test_trim_does_not_disarm(self):
        gate = Gate(1)
        gate.update(True, [0], True)
        self.assertTrue(gate.update(True, [0.6], True))
        self.assertFalse(gate.update(False, [0.6], False))
        self.assertFalse(gate.update(True, [0.6], True))
        self.assertTrue(gate.update(True, [0], True))

    def test_modes(self):
        self.assertEqual(select_mode('stabilize', True, True, 'IMU', True), 'MANUAL_FALLBACK')
        self.assertEqual(select_mode('stabilize', True, False, 'IMU', True), 'RX_TIMEOUT')
        self.assertEqual(select_mode('stabilize', True, True, '', True), 'STABILIZE')
        self.assertEqual(select_mode('manual', True, True, 'IMU', False), 'MANUAL')

    def test_gravity_initialization(self):
        pose = Attitude()
        roll, pitch = math.radians(35), math.radians(-20)
        pose.seed((-math.sin(pitch), math.sin(roll)*math.cos(pitch),
                   math.cos(roll)*math.cos(pitch)))
        r, p, _ = pose.angles()
        self.assertAlmostEqual(r, 35)
        self.assertAlmostEqual(p, -20)

    def test_nose_up_is_negative_body_pitch(self):
        pose = Attitude()
        angle = math.radians(10)
        pose.seed((math.sin(angle), 0, math.cos(angle)))
        self.assertAlmostEqual(pose.angles()[1], -10)

    def test_roll_crosses_70_without_fault(self):
        pose = Attitude(gain=0)
        for _ in range(100):
            pose.update((0, 0, 1, 90, 0, 0), 0.01)
        self.assertAlmostEqual(pose.angles()[0], 90, places=2)
        self.assertAlmostEqual(sum(v*v for v in pose.q), 1)

    def test_pitch_and_yaw_integration(self):
        for index, expected in ((4, 30), (5, 30)):
            pose = Attitude(gain=0)
            values = [0, 0, 1, 0, 0, 0]
            values[index] = 30
            for _ in range(100):
                pose.update(values, 0.01)
            self.assertAlmostEqual(pose.angles()[index-3], expected, places=2)

    def test_gravity_feedback_sign(self):
        pose = Attitude(gain=2)
        roll = math.radians(10)
        for _ in range(400):
            pose.update((0, math.sin(roll), math.cos(roll), 0, 0, 0), 0.01)
        self.assertAlmostEqual(pose.angles()[0], 10, places=1)

    def test_body_error_direction_and_short_path(self):
        self.assertAlmostEqual(body_error(quaternion(10, 0, 0), quaternion(0, 0, 0))[0], -10)
        self.assertAlmostEqual(body_error(quaternion(179, 0, 0), quaternion(-179, 0, 0))[0], 2)
        q = quaternion(45, 20, 12)
        self.assertEqual(body_error(q, q), (0, 0, 0))

    def test_pitch_error_at_bank_is_body_coupled(self):
        e = body_error(quaternion(60, 0, 0), quaternion(60, 10, 0))
        self.assertAlmostEqual(e[1], 5, places=5)
        self.assertAlmostEqual(e[2], -10*math.sin(math.radians(60)), places=5)

    def test_filter_rejects_bad_dt(self):
        with self.assertRaises(ValueError):
            Attitude().update((0, 0, 1, 0, 0, 0), 0.1)

    def test_controller_limits_antiwindup(self):
        settings = dict(config.CONTROLLERS['roll'], rate_i=1)
        controller = AxisController(settings, 20)
        for _ in range(500):
            self.assertEqual(controller.update(90, 0, 0, 0.01, True), 20)
        self.assertEqual(controller.integral, 0)
        self.assertLess(controller.update(0, 0, 10, 0.01, True), 0)

    def test_servo_trim_clamped(self):
        settings = dict(config.SERVOS['roll'], trim=100, sign=-1)
        self.assertEqual(command(0, settings), 1600)
        self.assertEqual(command(-500, settings), 1700)
        self.assertEqual(command(500, settings), 1300)

    def test_roll_sign_pair_preserves_manual_and_corrects_bank_targets(self):
        # Besitzerpruefung: kleinere RX-Pulse = Rechtsknueppel; Rechtsbank = +Roll.
        # Beispielkalibrierung; keine Kopie der unbekannten MCU-Kalibrierdatei.
        cal = {'min': 1000, 'center': 1500, 'max': 2000}
        legacy_servo = dict(config.SERVOS['roll'], sign=1)
        for pulse, target_sign in ((1000, 1), (2000, -1)):
            stick = normalize(pulse, cal, config.RECEIVER['roll']['sign'])
            self.assertGreater(stick*target_sign, 0)
            actual = command(stick*config.SERVOS['roll']['limit'], config.SERVOS['roll'])
            legacy = command(normalize(pulse, cal)*legacy_servo['limit'], legacy_servo)
            self.assertEqual(actual, legacy)
        self.assertEqual(command(0, config.SERVOS['roll']), 1500)

    def test_pitch_yaw_sign_pairs_preserve_manual_and_match_body_targets(self):
        # Besitzerprofil: hoher RX-Puls = Nase hoch / Gier rechts, beides negativ.
        # Beispiel-Endpunkte, keine Behauptung ueber die Kalibrierdatei am MCU.
        cal = {'min': 1000, 'center': 1500, 'max': 2000}
        for axis in ('pitch', 'yaw'):
            legacy_servo = dict(config.SERVOS[axis], sign=1)
            for pulse, body_sign in ((1000, 1), (2000, -1)):
                with self.subTest(axis=axis, pulse=pulse):
                    stick = normalize(pulse, cal, config.RECEIVER[axis]['sign'])
                    self.assertGreater(stick*body_sign, 0)
                    actual = command(stick*config.SERVOS[axis]['limit'], config.SERVOS[axis])
                    legacy = command(normalize(pulse, cal)*legacy_servo['limit'], legacy_servo)
                    self.assertEqual(actual, legacy)

    def test_calibration_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(pathlib.Path(directory)/'calibration.json')
            data = calibration.load(path)
            data['rc']['roll'] = {'min': 1000, 'center': 1375, 'max': 2000}
            calibration.save(path, data)
            self.assertEqual(calibration.load(path), data)

    def test_bad_calibration_and_handedness(self):
        with self.assertRaises(ValueError):
            calibration.check_channel({'min': 1000, 'center': 1001, 'max': 2000})
        with self.assertRaises(ValueError):
            validate_transform((0, 1, 2), (1, -1, 1))
        validate_transform((0, 1, 2), (1, -1, -1))

    def test_log_bounded_order(self):
        log = RingLog(3)
        for n in range(5):
            log.append(str(n))
        self.assertEqual(list(log.ordered()), ['2', '3', '4'])


class FlowTests(unittest.TestCase):
    def simulate(self, scenario, axes=('roll',), mode='stabilize', save_log=False,
                 expected_error=None, failed_axis='pitch', log_hz=100):
        recorded = []
        state = {'iteration': 0, 'closed': False, 'write_times': [], 'saved_logs': [],
                 'pulse_records': [], 'log_rows': [], 'reports': []}

        class Clock:
            value = (1 << 30)-15000 if scenario == 'wrap' else 1000000
            @classmethod
            def ticks_us(cls): return cls.value % (1 << 30)
            @classmethod
            def ticks_ms(cls): return (cls.value//1000) % (1 << 30)
            @staticmethod
            def ticks_diff(a, b): return (a-b+(1 << 29)) % (1 << 30)-(1 << 29)
            @classmethod
            def sleep_us(cls, us): cls.value += us

        class FakeIMU:
            saturated = False
            def __init__(self, *args): pass
            def calibrate_gyro(self, *args):
                if scenario in ('nose_up', 'nose_down'):
                    pitch = math.radians(-10 if scenario == 'nose_up' else 10)
                    return (-math.sin(pitch), 0, math.cos(pitch))
                angle = 10 if scenario == 'bank_right' else -10 if scenario == 'bank_left' else 0
                return (0, math.sin(math.radians(angle)), math.cos(math.radians(angle)))
            def read(self):
                if scenario == 'sensor_error' and state['iteration'] >= 4:
                    raise OSError('Sensor abgezogen')
                if scenario in ('timing', 'timing_rearm') and state['iteration'] == 4:
                    Clock.value += 60000
                    state['stall_return_us'] = Clock.value
                gz = 10 if scenario == 'yaw_left' else -10 if scenario == 'yaw_right' else 0
                gy = 100 if scenario == 'pitch_range' and state['iteration'] >= 4 else 0
                if scenario == 'yaw_stopped':
                    gz = 50 if state['iteration'] < 5 else 0
                return tuple(self.calibrate_gyro())+(0, gy, gz)

        class Controller(AxisController):
            def update(self, *args):
                result = super().update(*args)
                if scenario == 'controller_delay' and not state.get('controller_delayed'):
                    state['controller_delayed'] = True
                    Clock.value += 60000
                return result

        class FakeRX:
            def __init__(self, settings, axes, timeout, **kwargs):
                self.channels = {a: {'pulse': 1500, 'sequence': 0, 'time': None} for a in axes}
            def poll(self, now):
                state['iteration'] += 1
                if state['iteration'] > 10:
                    raise KeyboardInterrupt
                for axis, c in self.channels.items():
                    missing = (scenario == 'missing_channel' or
                               (scenario in ('channel_loss', 'channel_recovery') and
                                state['iteration'] >= 4))
                    if scenario == 'channel_recovery' and state['iteration'] >= 6:
                        missing = False
                    if missing and axis == failed_axis:
                        c['pulse'], c['time'] = None, None
                        continue
                    c['sequence'] += 1
                    c['time'] = (now-10) % (1 << 30)
                    c['pulse'] = 1500 if state['iteration'] < 4 else 1800
                    if scenario in ('bank_right', 'bank_left', 'nose_up', 'nose_down', 'yaw_left', 'yaw_right', 'yaw_stopped'):
                        c['pulse'] = 1500
                    if scenario == 'stick_right' and state['iteration'] >= 4:
                        c['pulse'] = 1000
                    if scenario in ('stick_low', 'stick_high') and state['iteration'] >= 4:
                        c['pulse'] = 1000 if scenario == 'stick_low' else 2000
                    if scenario == 'channel_recovery' and 8 <= state['iteration'] <= 9:
                        c['pulse'] = 1500
                    if scenario == 'initial_non_neutral':
                        c['pulse'] = 1800 if state['iteration'] <= 4 else 1500
                    if scenario == 'timing_rearm' and 5 <= state['iteration'] <= 7:
                        c['pulse'] = 1500
                        state['invalid'] = False
                if scenario == 'missing_pitch' or (scenario == 'pitch_loss' and state['iteration'] >= 6):
                    self.channels['pitch']['pulse'] = None
                if scenario == 'receiver_delay' and state['iteration'] == 2:
                    Clock.value += 60000
            def all_fresh(self, now):
                return all(c['pulse'] is not None for c in self.channels.values()) and not state.get('invalid', False) and not (
                    scenario == 'rx_loss' and state['iteration'] >= 6) and not (
                    scenario == 'missing_pitch' or (scenario == 'pitch_loss' and state['iteration'] >= 6))
            def invalidate(self, now):
                state['invalid'] = True
                state['invalidated_at'] = state['iteration']
                for c in self.channels.values(): c['pulse'], c['time'] = None, None
            def close(self): state['rx_closed'] = True

        class FakeOut:
            def __init__(self, *args):
                self.settings, self.axes = args
                state['out_created'] = True
                if scenario == 'startup_error': raise OSError('PWM start failed')
                if scenario == 'output_delay': Clock.value += 60000
            def write(self, offsets):
                recorded.append((state['iteration'], dict(offsets)))
                state['write_times'].append(Clock.value)
                # Reine Pulsrechnung einbeziehen, damit Tests auch die zweite
                # Vorzeichenstufe pruefen. Keine echten PWM-Objekte erzeugen.
                pulses = {a: command(offsets.get(a, 0), self.settings[a]) for a in self.axes}
                state['pulse_records'].append(pulses)
                return pulses
            def close(self):
                state['closed'] = True
                if scenario == 'cleanup_error': raise OSError('PWM close failed')

        level = {'roll': 0, 'pitch': 0, 'axes': [0, 1, 2], 'signs': [1, 1, 1],
                 'offset': list(config.SENSOR['acc_offset']), 'scale': list(config.SENSOR['acc_scale'])}
        data = {'schema': 1, 'level': level,
                'rc': {axis: {'min': 1000, 'center': 1500, 'max': 2000} for axis in axes}}
        transcript = io.StringIO()
        original_print = print
        def diagnostic_print(*args, **kwargs):
            if (scenario == 'startup_console_delay' and args and
                    str(args[0]).startswith('Phase PWM_START_REQUEST')):
                Clock.value += 60000
            if (scenario == 'console_delay' and args and str(args[0]).startswith('roll=')
                    and not state.get('console_delayed')):
                state['console_delayed'] = True
                Clock.value += 60000
            original_print(*args, **kwargs)
        def save_report(report, path, metadata):
            self.assertTrue(state['rx_closed'])
            if state.get('out_created'):
                self.assertTrue(state['closed'])
            state['reports'].append(dict(metadata, **report.report()))
        with patch.object(app, 'IMU', FakeIMU), patch.object(app, 'Receiver', FakeRX), \
             patch.object(app, 'Outputs', FakeOut), patch.object(app, 'time', Clock), \
             patch.object(app, 'AxisController', Controller), \
             patch.object(app, 'print', diagnostic_print, create=True), \
             patch.object(app, 'load', lambda path: data), \
             patch.object(config, 'START_MODE', mode), \
             patch.object(config, 'ACTIVE_AXES', axes), \
             patch.object(config, 'DIRECTION_CHECKED_AXES', axes), \
             patch.object(config, 'NEUTRAL_FRAMES', 2), \
             patch.object(config, 'LOG_HZ', log_hz), \
             patch.object(config, 'CONSOLE_HZ', 100 if scenario == 'console_delay' else 4), \
             patch.object(config, 'PITCH_CONTROL_LIMIT_DEG', 2 if scenario == 'pitch_range' else 75), \
             patch.object(config, 'SAVE_LOG_ON_STOP', save_log), \
             patch.object(RingLog, 'save', lambda log, path: (
                 state['saved_logs'].append(path), state['log_rows'].extend(log.ordered()))), \
             patch.object(BenchDiagnostics, 'save', save_report), \
             contextlib.redirect_stdout(transcript):
            if expected_error is None:
                app.run()
            else:
                with self.assertRaises(expected_error):
                    app.run()
        return recorded, state, transcript.getvalue()

    def test_start_then_trim_keeps_control(self):
        records, state, text = self.simulate('normal')
        self.assertEqual(records[0][0], 2)
        # 1800 us wird je nach RX-Polung zum positiven/negativen Banksollwert.
        self.assertGreater(records[-1][1]['roll']*config.RECEIVER['roll']['sign'], 0)
        self.assertIn('STABILIZE', text)
        self.assertNotIn('MANUAL_FALLBACK', text)
        self.assertTrue(state['closed'])

    def test_imu_failure_falls_back_to_manual(self):
        records, _, text = self.simulate('sensor_error')
        expected = normalize(1800, {'min': 1000, 'center': 1500, 'max': 2000},
                             config.RECEIVER['roll']['sign'])*config.SERVOS['roll']['limit']
        self.assertAlmostEqual(records[-1][1]['roll'], expected)
        self.assertIn('MANUAL_FALLBACK', text)

    def test_rx_loss_neutralizes(self):
        records, _, text = self.simulate('rx_loss')
        self.assertEqual(records[-1][1], {})
        self.assertIn('RX_TIMEOUT', text)

    def test_timing_failure_falls_back(self):
        records, state, text = self.simulate('timing')
        # Check the FIRST write after the delayed read, not eventual fallback.
        late = [offsets for (_, offsets), stamp in zip(records, state['write_times'])
                if stamp >= state['stall_return_us']]
        self.assertTrue(late)
        self.assertTrue(all(offsets == {} for offsets in late))
        self.assertEqual(state['invalidated_at'], 4)
        self.assertIn('RX_TIMEOUT', text)
        self.assertIn('TIMING', text)

    def test_cleanup_error_still_closes_receiver_and_reports_incomplete_shutdown(self):
        _, state, text = self.simulate('cleanup_error', save_log=True)
        self.assertTrue(state['rx_closed'])
        self.assertIn('Abschalten unvollstaendig', text)
        self.assertNotIn('PWM/PIO ausgeschaltet', text)
        self.assertEqual(state['saved_logs'], [])

    def test_timing_fault_latches_after_neutral_reacquisition(self):
        records, _, text = self.simulate('timing_rearm')
        self.assertEqual(next(offsets for i, offsets in records if i == 5), {})
        expected = normalize(1800, {'min': 1000, 'center': 1500, 'max': 2000},
                             config.RECEIVER['roll']['sign'])*config.SERVOS['roll']['limit']
        self.assertAlmostEqual(records[-1][1]['roll'], expected)
        self.assertIn('WAIT_NEUTRAL', text)
        self.assertIn('MANUAL_FALLBACK', text)
        self.assertNotIn('STABILIZE', text.split('Fehler: TIMING', 1)[1])

    def test_late_receiver_poll_cannot_start_pwm(self):
        records, state, text = self.simulate('receiver_delay')
        self.assertEqual(records, [])
        self.assertFalse(state.get('out_created', False))
        self.assertIn('TIMING', text)

    def test_late_controller_calculation_cannot_start_pwm(self):
        records, state, text = self.simulate('controller_delay')
        self.assertEqual(records, [])
        self.assertFalse(state.get('out_created', False))
        self.assertIn('TIMING', text)

    def test_late_pwm_initialization_is_followed_by_neutral(self):
        records, _, text = self.simulate('output_delay')
        self.assertEqual(records[0][1], {})
        self.assertIn('TIMING', text)

    def test_partial_startup_does_not_claim_shutdown_or_export_log(self):
        _, state, text = self.simulate('startup_error', save_log=True, expected_error=OSError)
        self.assertTrue(state['rx_closed'])
        self.assertIn('Abschalten unvollstaendig', text)
        self.assertNotIn('PWM/PIO ausgeschaltet', text)
        self.assertEqual(state['saved_logs'], [])

    def test_tick_wrap_does_not_create_timing_fault(self):
        records, _, text = self.simulate('wrap')
        self.assertGreater(records[-1][1]['roll']*config.RECEIVER['roll']['sign'], 0)
        self.assertNotIn('Fehler: TIMING', text)

    def test_manual_mode_also_neutralizes_after_late_read(self):
        records, state, _ = self.simulate('timing', mode='manual')
        late = [offsets for (_, offsets), stamp in zip(records, state['write_times'])
                if stamp >= state['stall_return_us']]
        self.assertTrue(all(offsets == {} for offsets in late))

    def test_sensor_mode_has_no_pwm_even_after_timing_fault(self):
        records, state, _ = self.simulate('timing', mode='sensor')
        self.assertEqual(records, [])
        self.assertTrue(state['rx_closed'])

    def test_sensor_mode_has_no_pwm(self):
        records, state, _ = self.simulate('normal', mode='sensor')
        self.assertEqual(records, [])
        self.assertTrue(state['rx_closed'])

    def test_roll_pitch_outputs_together(self):
        records, _, text = self.simulate('normal', axes=('roll', 'pitch'))
        self.assertIn('STABILIZE', text)
        self.assertGreater(records[-1][1]['roll']*config.RECEIVER['roll']['sign'], 0)
        self.assertGreater(records[-1][1]['pitch']*config.RECEIVER['pitch']['sign'], 0)

    def test_right_stick_has_same_physical_direction_in_manual_and_stabilize(self):
        for mode in ('manual', 'stabilize'):
            with self.subTest(mode=mode):
                _, state, _ = self.simulate('stick_right', mode=mode)
                # In diesem verifizierten Aufbau bedeutet kleinerer Servopuls Rechtsrollen.
                self.assertLess(state['pulse_records'][-1]['roll'], config.SERVOS['roll']['center'])

    def test_all_axes_keep_stick_pulse_direction_in_manual_and_stabilize(self):
        # Zweite Vorzeichenstufe mitpruefen: gleiche physische Knueppelrichtung
        # braucht gleiche Pulsrichtung in beiden Modi, nicht gleichen Ausschlag.
        for scenario, pulse_sign in (('stick_low', -1), ('stick_high', 1)):
            for mode in ('manual', 'stabilize'):
                with self.subTest(scenario=scenario, mode=mode):
                    _, state, _ = self.simulate(scenario, mode=mode,
                                               axes=('roll', 'pitch', 'yaw'))
                    for axis in ('roll', 'pitch', 'yaw'):
                        deviation = state['pulse_records'][-1][axis]-command(0, config.SERVOS[axis])
                        self.assertGreater(deviation*pulse_sign, 0)

    def test_centered_stick_opposes_both_bank_directions(self):
        for scenario, correction_sign in (('bank_right', 1), ('bank_left', -1)):
            with self.subTest(scenario=scenario):
                _, state, text = self.simulate(scenario)
                deviation = state['pulse_records'][-1]['roll']-config.SERVOS['roll']['center']
                # Rechtsbank braucht Linksrollwirkung (groesserer Puls), und umgekehrt.
                self.assertGreater(deviation*correction_sign, 0)
                self.assertIn('STABILIZE', text)

    def test_pitch_feedback_opposes_nose_up_and_down(self):
        # +Pitchkommando = Nase runter. Im bestaetigten -1-Servoprofil braucht
        # dies einen kleineren Puls; nur ein Kommando-Test wuerde falsche PWM uebersehen.
        for scenario, offset_sign in (('nose_up', 1), ('nose_down', -1)):
            with self.subTest(scenario=scenario):
                records, state, _ = self.simulate(scenario, axes=('roll', 'pitch'))
                self.assertGreater(records[-1][1]['pitch']*offset_sign, 0)
                self.assertAlmostEqual(records[-1][1]['roll'], 0, places=6)
                deviation = state['pulse_records'][-1]['pitch']-command(0, config.SERVOS['pitch'])
                self.assertGreater(deviation*(-offset_sign), 0)

    def test_yaw_feedback_opposes_left_and_right_turn_rate(self):
        # +Koerper-Gier ist links. Bei Drehung nach links muss Kommando negativ sein.
        for scenario, offset_sign in (('yaw_left', -1), ('yaw_right', 1)):
            with self.subTest(scenario=scenario):
                records, state, _ = self.simulate(scenario, axes=('roll', 'pitch', 'yaw'))
                self.assertGreater(records[-1][1]['yaw']*offset_sign, 0)
                deviation = state['pulse_records'][-1]['yaw']-command(0, config.SERVOS['yaw'])
                self.assertGreater(deviation*(-offset_sign), 0)

    def test_yaw_returns_to_trim_after_rotation_stops_at_new_heading(self):
        _, state, _ = self.simulate('yaw_stopped', axes=('roll', 'pitch', 'yaw'), save_log=True)
        row = dict(zip(RingLog.HEADER.strip().split(','), state['log_rows'][-1].strip().split(',')))
        self.assertGreater(abs(float(row['yaw'])), 1)
        self.assertEqual(float(row['gyro_yaw']), 0)
        self.assertEqual(state['pulse_records'][-1]['yaw'], command(0, config.SERVOS['yaw']))

    def test_startup_phases_and_extended_csv_are_consistent(self):
        _, state, text = self.simulate('normal', save_log=True)
        self.assertLess(text.index('GYRO_CAL'), text.index('GYRO_DONE'))
        self.assertLess(text.index('GYRO_DONE'), text.index('PWM_START_REQUEST'))
        self.assertTrue(state['log_rows'])
        count = len(RingLog.HEADER.strip().split(','))
        self.assertEqual(count, 30)
        self.assertTrue(all(len(row.strip().split(',')) == count for row in state['log_rows']))

    def test_slow_startup_diagnostic_cannot_start_pwm(self):
        records, state, text = self.simulate('startup_console_delay')
        self.assertEqual(records, [])
        self.assertFalse(state.get('out_created', False))
        self.assertIn('TIMING', text)

    def test_missing_pitch_input_prevents_all_outputs(self):
        records, state, text = self.simulate('missing_pitch', axes=('roll', 'pitch'))
        self.assertEqual(records, [])
        self.assertFalse(state.get('out_created', False))
        self.assertIn('RX_TIMEOUT', text)

    def test_pitch_input_loss_neutralizes_both_axes(self):
        records, state, text = self.simulate('pitch_loss', axes=('roll', 'pitch'))
        self.assertEqual(records[-1][1], {})
        self.assertEqual(state['pulse_records'][-1], {'roll': 1500, 'pitch': 1500})
        self.assertIn('RX_TIMEOUT', text)

    def test_yaw_uses_rate_command(self):
        records, _, _ = self.simulate('normal', axes=('roll', 'pitch', 'yaw'))
        self.assertGreater(records[-1][1]['yaw']*config.RECEIVER['yaw']['sign'], 0)

    def test_each_missing_channel_prevents_all_three_outputs(self):
        for axis in ('roll', 'pitch', 'yaw'):
            with self.subTest(axis=axis):
                records, state, _ = self.simulate('missing_channel', axes=('roll', 'pitch', 'yaw'),
                                                 save_log=True, failed_axis=axis)
                self.assertEqual(records, [])
                self.assertFalse(state.get('out_created', False))
                self.assertTrue(all(not event['pwm'] for event in state['reports'][0]['events']))

    def test_each_channel_loss_neutralizes_all_three_outputs(self):
        for axis in ('roll', 'pitch', 'yaw'):
            with self.subTest(axis=axis):
                records, state, _ = self.simulate('channel_loss', axes=('roll', 'pitch', 'yaw'),
                                                 save_log=True, failed_axis=axis)
                self.assertTrue(all(offsets == {} for iteration, offsets in records if iteration >= 4))
                self.assertEqual(state['pulse_records'][-1], {'roll': 1500, 'pitch': 1500, 'yaw': 1500})

    def test_each_channel_recovery_waits_for_new_neutral_frames(self):
        for axis in ('roll', 'pitch', 'yaw'):
            with self.subTest(axis=axis):
                records, state, _ = self.simulate('channel_recovery', axes=('roll', 'pitch', 'yaw'),
                                                 mode='manual', save_log=True, failed_axis=axis)
                self.assertTrue(all(offsets == {} for iteration, offsets in records if 4 <= iteration <= 8))
                self.assertTrue(next(offsets for iteration, offsets in records if iteration == 10))
                modes = [event['mode'] for event in state['reports'][0]['events']]
                self.assertEqual(modes, ['WAIT_NEUTRAL', 'MANUAL', 'RX_TIMEOUT', 'WAIT_NEUTRAL', 'MANUAL'])

    def test_offcenter_start_does_not_construct_pwm(self):
        _, state, _ = self.simulate('initial_non_neutral', axes=('roll', 'pitch', 'yaw'),
                                    mode='manual', save_log=True)
        self.assertEqual(state['pulse_records'][0], {'roll': 1500, 'pitch': 1500, 'yaw': 1500})
        self.assertGreaterEqual(state['write_times'][0], 1050000)
        self.assertFalse(state['reports'][0]['events'][0]['pwm'])

    def test_timing_after_controller_delay_is_counted(self):
        _, state, _ = self.simulate('controller_delay', save_log=True)
        self.assertGreater(state['reports'][0]['timing_trips'], 0)

    def test_console_cost_is_measured_and_next_iteration_faults(self):
        _, state, _ = self.simulate('console_delay', axes=('roll', 'pitch', 'yaw'), save_log=True)
        report = state['reports'][0]
        self.assertGreaterEqual(report['timing']['work']['max_us'], 60000)
        self.assertGreaterEqual(report['timing']['period']['max_us'], 60000)
        self.assertGreater(report['timing_trips'], 0)
        self.assertTrue(report['fault_iterations'].get('TIMING', 0))

    def test_summary_is_saved_only_after_confirmed_shutdown(self):
        _, state, _ = self.simulate('normal', axes=('roll', 'pitch', 'yaw'), save_log=True)
        report = state['reports'][0]
        self.assertTrue(report['shutdown_ok'])
        self.assertEqual(report['iterations'], 10)
        self.assertEqual(report['timing']['period']['count'], 9)
        self.assertEqual(report['configuration']['active_axes'], ['roll', 'pitch', 'yaw'])
        self.assertEqual(report['calibration']['rc']['yaw']['center'], 1500)
        for scenario in ('cleanup_error', 'startup_error'):
            _, failed, _ = self.simulate(scenario, save_log=True,
                                        expected_error=OSError if scenario == 'startup_error' else None)
            self.assertEqual(failed['reports'], [])

    def test_fault_and_mode_changes_logged_even_between_periodic_samples(self):
        _, state, _ = self.simulate('sensor_error', axes=('roll', 'pitch', 'yaw'),
                                    save_log=True, log_hz=1)
        events = state['reports'][0]['events']
        self.assertTrue(any(e['mode'] == 'MANUAL_FALLBACK' and e['fault'] == 'IMU_RUNTIME' for e in events))
        rows = [dict(zip(RingLog.HEADER.strip().split(','), row.strip().split(',')))
                for row in state['log_rows']]
        self.assertTrue(any(row['mode'] == 'MANUAL_FALLBACK' and row['fault'] == 'IMU_RUNTIME' for row in rows))
        self.assertTrue(all(int(row['ms']) < 1000 for row in rows))

    def test_fresh_held_pulses_remain_indistinguishable_from_radio_link(self):
        _, state, _ = self.simulate('normal', axes=('roll', 'pitch', 'yaw'), save_log=True)
        rows = [dict(zip(RingLog.HEADER.strip().split(','), row.strip().split(',')))
                for row in state['log_rows']]
        tail = rows[-3:]
        self.assertTrue(all(row['rx_roll'] == '1800' and row['fresh'] == '1' for row in tail))
        self.assertLess(int(tail[0]['rx_seq_roll']), int(tail[-1]['rx_seq_roll']))
        self.assertTrue(all(row['mode'] == 'STABILIZE' for row in tail))

    def test_automation_fault_is_latched_for_all_axes(self):
        for scenario in ('sensor_error', 'pitch_range', 'timing_rearm'):
            with self.subTest(scenario=scenario):
                records, state, _ = self.simulate(scenario, axes=('roll', 'pitch', 'yaw'), save_log=True)
                self.assertTrue(any(e['mode'] == 'MANUAL_FALLBACK' for e in state['reports'][0]['events']))
                for axis in ('roll', 'pitch', 'yaw'):
                    expected = normalize(1800, {'min': 1000, 'center': 1500, 'max': 2000},
                                         config.RECEIVER[axis]['sign'])*config.SERVOS[axis]['limit']
                    self.assertAlmostEqual(records[-1][1][axis], expected)


class AnalysisTests(unittest.TestCase):
    def recorded_run(self, scenario='normal', mode='stabilize', failed_axis='pitch'):
        _, state, _ = FlowTests().simulate(scenario, axes=('roll', 'pitch', 'yaw'), mode=mode,
                                          save_log=True, failed_axis=failed_axis)
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)/'sample.csv'
            path.write_text(RingLog.HEADER+''.join(state['log_rows']))
            rows = read_csv(path)
        return rows, state['reports'][0]

    def test_sensor_and_normal_stabilize_profiles_pass(self):
        for mode, profile in (('sensor', 'sensor'), ('stabilize', 'stabilize')):
            with self.subTest(mode=mode):
                rows, report = self.recorded_run(mode=mode)
                result = inspect_run(rows, report, profile)
                self.assertEqual(result['issues'], [])
                self.assertTrue(result['verdict'].startswith('PASS'))

    def test_missing_and_recovery_profiles_for_each_axis(self):
        for axis in ('roll', 'pitch', 'yaw'):
            for scenario, profile in (('missing_channel', 'missing-rx'), ('channel_recovery', 'rx-recovery')):
                with self.subTest(axis=axis, scenario=scenario):
                    rows, report = self.recorded_run(scenario, mode='manual', failed_axis=axis)
                    self.assertTrue(inspect_run(rows, report, profile)['verdict'].startswith('PASS'))

    def test_initial_non_neutral_profile_requires_blocked_start(self):
        rows, report = self.recorded_run('initial_non_neutral', mode='manual')
        self.assertTrue(inspect_run(rows, report, 'neutral-gate')['verdict'].startswith('PASS'))
        rows, report = self.recorded_run(mode='manual')
        self.assertEqual(inspect_run(rows, report, 'neutral-gate')['verdict'], 'FAIL')

    def test_automation_fault_and_timing_profiles_pass_without_unlatching(self):
        for scenario, profile in (('sensor_error', 'imu-fault'),
                                  ('pitch_range', 'pitch-range'), ('timing_rearm', 'timing-fault')):
            with self.subTest(scenario=scenario):
                rows, report = self.recorded_run(scenario)
                result = inspect_run(rows, report, profile)
                self.assertEqual(result['issues'], [])
                self.assertTrue(result['verdict'].startswith('PASS'))

    def test_corrupt_pulse_and_early_fault_cannot_pass_normal_profile(self):
        rows, report = self.recorded_run()
        rows[-1]['servo_pitch'] = 2500
        self.assertEqual(inspect_run(rows, report, 'stabilize')['verdict'], 'FAIL')
        rows, report = self.recorded_run()
        # Ein alter Fehler darf nicht durch den 20-s-CSV-Ring verschwinden.
        report['fault_iterations']['IMU_RUNTIME'] = 1
        self.assertEqual(inspect_run(rows, report, 'stabilize')['verdict'], 'FAIL')

    def test_event_overflow_is_incomplete_and_nonfinite_summary_is_rejected(self):
        rows, report = self.recorded_run()
        report['events_dropped'] = 1
        self.assertEqual(inspect_run(rows, report, 'stabilize')['verdict'], 'BEFUND / UNVOLLSTAENDIG')
        report['timing']['work']['max_us'] = float('nan')
        with self.assertRaises(ValueError):
            inspect_run(rows, report, 'stabilize')

    def test_missing_whole_run_statistics_cannot_pass(self):
        rows, report = self.recorded_run()
        report['timing']['work']['count'] = 0
        with self.assertRaises(ValueError):
            inspect_run(rows, report, 'stabilize')

    def test_csv_rejects_missing_columns_and_nonfinite_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)/'bad.csv'
            path.write_text('ms,mode\n0,SENSOR\n')
            with self.assertRaises(ValueError):
                read_csv(path)
            _, state, _ = FlowTests().simulate('normal', save_log=True)
            line = state['log_rows'][-1].strip().split(',')
            line[RingLog.HEADER.strip().split(',').index('dt_ms')] = 'nan'
            path.write_text(RingLog.HEADER+','.join(line)+'\n')
            with self.assertRaises(ValueError):
                read_csv(path)

    def test_cli_reads_real_file_pair_and_rejects_missing_summary(self):
        import json
        _, state, _ = FlowTests().simulate('normal', axes=('roll', 'pitch', 'yaw'), save_log=True)
        report = state['reports'][0]
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)/report['csv_file']
            path.write_text(RingLog.HEADER+''.join(state['log_rows']))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(analyze_main([str(path), '--expect', 'stabilize']), 2)
            path.with_suffix('.json').write_text(json.dumps(report))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(analyze_main([str(path), '--expect', 'stabilize']), 0)


if __name__ == '__main__':
    unittest.main()
