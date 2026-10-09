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
from attitude import Attitude, quaternion, body_error
from receiver import normalize
from outputs import command
from control import AxisController, Gate, select_mode
from logger import RingLog
from imu import validate_transform


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
    def simulate(self, scenario, axes=('roll',), mode='stabilize'):
        recorded = []
        state = {'iteration': 0, 'closed': False}

        class Clock:
            value = 1000000
            @classmethod
            def ticks_us(cls): return cls.value
            @classmethod
            def ticks_ms(cls): return cls.value//1000
            @staticmethod
            def ticks_diff(a, b): return a-b
            @classmethod
            def sleep_us(cls, us): cls.value += us

        class FakeIMU:
            saturated = False
            def __init__(self, *args): pass
            def calibrate_gyro(self, *args): return (0, 0, 1)
            def read(self):
                if scenario == 'sensor_error' and state['iteration'] >= 4:
                    raise OSError('Sensor abgezogen')
                if scenario == 'timing' and state['iteration'] == 4:
                    Clock.value += 60000
                return (0, 0, 1, 0, 0, 0)

        class FakeRX:
            def __init__(self, settings, axes, timeout):
                self.channels = {a: {'pulse': 1500, 'sequence': 0} for a in axes}
            def poll(self, now):
                state['iteration'] += 1
                if state['iteration'] > 10:
                    raise KeyboardInterrupt
                for c in self.channels.values():
                    c['sequence'] += 1
                    c['pulse'] = 1500 if state['iteration'] < 4 else 1800
            def all_fresh(self, now):
                return not (scenario == 'rx_loss' and state['iteration'] >= 6)
            def close(self): state['rx_closed'] = True

        class FakeOut:
            def __init__(self, *args): pass
            def write(self, offsets):
                recorded.append((state['iteration'], dict(offsets)))
                return {}
            def close(self): state['closed'] = True

        level = {'roll': 0, 'pitch': 0, 'axes': [0, 1, 2], 'signs': [1, 1, 1],
                 'offset': list(config.SENSOR['acc_offset']), 'scale': list(config.SENSOR['acc_scale'])}
        data = {'schema': 1, 'level': level,
                'rc': {axis: {'min': 1000, 'center': 1500, 'max': 2000} for axis in axes}}
        transcript = io.StringIO()
        with patch.object(app, 'IMU', FakeIMU), patch.object(app, 'Receiver', FakeRX), \
             patch.object(app, 'Outputs', FakeOut), patch.object(app, 'time', Clock), \
             patch.object(app, 'load', lambda path: data), \
             patch.object(config, 'START_MODE', mode), \
             patch.object(config, 'ACTIVE_AXES', axes), \
             patch.object(config, 'NEUTRAL_FRAMES', 2), \
             patch.object(config, 'SAVE_LOG_ON_STOP', False), \
             contextlib.redirect_stdout(transcript):
            app.run()
        return recorded, state, transcript.getvalue()

    def test_start_then_trim_keeps_control(self):
        records, state, text = self.simulate('normal')
        self.assertEqual(records[0][0], 2)
        self.assertGreater(records[-1][1]['roll'], 0)
        self.assertIn('STABILIZE', text)
        self.assertNotIn('MANUAL_FALLBACK', text)
        self.assertTrue(state['closed'])

    def test_imu_failure_falls_back_to_manual(self):
        records, _, text = self.simulate('sensor_error')
        expected = normalize(1800, {'min': 1000, 'center': 1500, 'max': 2000})*200
        self.assertAlmostEqual(records[-1][1]['roll'], expected)
        self.assertIn('MANUAL_FALLBACK', text)

    def test_rx_loss_neutralizes(self):
        records, _, text = self.simulate('rx_loss')
        self.assertEqual(records[-1][1], {})
        self.assertIn('RX_TIMEOUT', text)

    def test_timing_failure_falls_back(self):
        _, _, text = self.simulate('timing')
        self.assertIn('MANUAL_FALLBACK', text)
        self.assertIn('TIMING', text)

    def test_sensor_mode_has_no_pwm(self):
        records, state, _ = self.simulate('normal', mode='sensor')
        self.assertEqual(records, [])
        self.assertTrue(state['rx_closed'])

    def test_roll_pitch_outputs_together(self):
        records, _, text = self.simulate('normal', axes=('roll', 'pitch'))
        self.assertIn('STABILIZE', text)
        self.assertGreater(records[-1][1]['roll'], 0)
        self.assertGreater(records[-1][1]['pitch'], 0)

    def test_yaw_uses_rate_command(self):
        records, _, _ = self.simulate('normal', axes=('roll', 'pitch', 'yaw'))
        self.assertGreater(records[-1][1]['yaw'], 0)


if __name__ == '__main__':
    unittest.main()
