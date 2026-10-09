"""Bodenversuch orchestrieren: Sensor -> Lage -> RC -> Modus -> Regler -> Servo.

Hauptfunktion run(): Initialisierung, 100-Hz-Schleife, Fehlerbehandlung, Aufraeumen.
validate_config() prueft aktive Achsen/Pins. PWM startet erst nach RC-Kalibrierung
und einmaliger Neutralfreigabe. Standard START_MODE='sensor' erzeugt keine PWM.
Groesserer Rollwinkel ist kein Fehler. Nick >75 Grad, Saettigung, Sensorfehler
oder zu lange Schleife verriegeln die Automatik in MANUAL_FALLBACK, solange RX
gueltig ist. RX-Ausfall neutralisiert und verlangt neue Neutralfreigabe.
Diese Software ist kein unabh. Bypass: haengende CPU/I2C wird nicht geloest.
Logs bleiben im RAM; erst nach dem Abschalten der PWM wird CSV geschrieben.
"""
import time
import config as cfg
from calibration import load, check_orientation
from imu import IMU
from attitude import Attitude, wrap_degrees, quaternion, body_error, clamp
from receiver import Receiver, normalize
from control import AxisController, Gate, select_mode
from outputs import Outputs
from logger import RingLog


def validate_config():
    if cfg.START_MODE not in ('sensor', 'manual', 'stabilize'):
        raise ValueError('START_MODE ungueltig')
    if not cfg.ACTIVE_AXES or len(set(cfg.ACTIVE_AXES)) != len(cfg.ACTIVE_AXES):
        raise ValueError('ACTIVE_AXES leer/doppelt')
    pins = [cfg.SENSOR['sda'], cfg.SENSOR['scl']]
    for axis in cfg.ACTIVE_AXES:
        if axis not in ('roll', 'pitch', 'yaw'):
            raise ValueError('Unbekannte Achse')
        pins.extend((cfg.RECEIVER[axis]['pin'], cfg.SERVOS[axis]['pin']))
        if cfg.RECEIVER[axis]['sign'] not in (-1, 1) or cfg.SERVOS[axis]['sign'] not in (-1, 1):
            raise ValueError('Vorzeichen muss +/-1 sein')
        s = cfg.SERVOS[axis]
        if not (100 <= s['limit'] <= 400 and
                900 <= s['center']-s['limit'] < s['center']+s['limit'] <= 2100):
            raise ValueError('Servogrenzen unplausibel')
        if abs(s['trim']) > s['limit']:
            raise ValueError('Servotrim ausserhalb Grenzen')
    if len(set(pins)) != len(pins):
        raise ValueError('GPIO mehrfach verwendet')


def run():
    validate_config()
    data = load(cfg.CALIBRATION_FILE)
    level = data.get('level')
    if level:
        check_orientation(level, cfg.SENSOR)
    reference_ok = level is not None
    if cfg.START_MODE != 'sensor':
        for axis in cfg.ACTIVE_AXES:
            if axis not in data['rc']:
                raise RuntimeError('Zuerst calibrate_rc.py fuer '+axis+' ausfuehren')
        if cfg.START_MODE == 'stabilize' and not reference_ok:
            raise RuntimeError('Zuerst calibrate_level.py ausfuehren')
    receiver, outputs, imu = None, None, None
    log = RingLog(cfg.LOG_CAPACITY)
    fault = ''
    pose = Attitude(cfg.ATTITUDE_ACCEL_GAIN)
    controllers = {axis: AxisController(cfg.CONTROLLERS[axis], cfg.SERVOS[axis]['limit'])
                   for axis in cfg.ACTIVE_AXES}
    gate = Gate(cfg.NEUTRAL_FRAMES, cfg.NEUTRAL_WINDOW)
    last_sequence = {}
    sample = (0, 0, 1, 0, 0, 0)
    angles = (0, 0, 0)
    try:
        try:
            imu = IMU(cfg.SENSOR, cfg.ALLOW_ID72_BENCH)
            acc = imu.calibrate_gyro(cfg.GYRO_STD_MAX)
            pose.seed(acc)
            angles = pose.angles()
        except Exception as error:
            if cfg.START_MODE == 'sensor':
                raise
            fault = 'IMU_START'
            imu = None
            print('Keine Automatik wegen Sensorstart:', error)
        receiver = Receiver(cfg.RECEIVER, cfg.ACTIVE_AXES, cfg.RX_TIMEOUT_MS)
        print('Version:', cfg.VERSION, '| Modus:', cfg.START_MODE,
              '| Achsen:', cfg.ACTIVE_AXES)
        print('Neutral wird nur vor Aktivierung/nach RX-Ausfall verlangt.')
        print('Ohne Lagekalibrierung: Winkel relativ zum Sensorkoordinatensystem.')
        previous = time.ticks_us()
        started = time.ticks_ms()
        print_time, log_time = started, started
        last_mode = None
        while True:
            start = time.ticks_us()
            elapsed_us = time.ticks_diff(start, previous)
            previous = start
            dt = max(elapsed_us, 1)/1000000
            if elapsed_us > cfg.MAX_LOOP_US and not fault:
                fault = 'TIMING'
            if imu is not None and not fault:
                try:
                    sample = imu.read()
                    if imu.saturated:
                        raise ValueError('Messbereich ueberschritten')
                    pose.update(sample, dt)
                    angles = pose.angles()
                    if abs(angles[1]) > cfg.PITCH_CONTROL_LIMIT_DEG:
                        fault = 'PITCH_RANGE'
                except Exception as error:
                    fault = 'IMU_RUNTIME'
                    print('Automatik aus:', error)
            now = time.ticks_ms()
            receiver.poll(now)
            fresh = receiver.all_fresh(now)
            sticks = {}
            for axis in cfg.ACTIVE_AXES:
                pulse = receiver.channels[axis]['pulse']
                cal = data['rc'].get(axis)
                sticks[axis] = (normalize(pulse, cal, cfg.RECEIVER[axis]['sign'])
                                if pulse is not None and cal is not None else 0.0)
            # Freigabe nur bei neuen Frames aller aktiven Kanale.
            new_frame = all(receiver.channels[a]['sequence'] != last_sequence.get(a, 0)
                            for a in cfg.ACTIVE_AXES)
            if new_frame:
                last_sequence = {a: receiver.channels[a]['sequence'] for a in cfg.ACTIVE_AXES}
            armed = gate.update(fresh, list(sticks.values()), new_frame)
            mode = select_mode(cfg.START_MODE, armed, fresh, fault, reference_ok)
            if mode != last_mode:
                print('Zustand:', mode, 'Fehler:', fault or '-')
                for controller in controllers.values():
                    controller.reset()
                last_mode = mode
            roll = wrap_degrees(angles[0]-(level['roll'] if level else 0))
            pitch = angles[1]-(level['pitch'] if level else 0)
            target_roll = (sticks.get('roll', 0)*cfg.CONTROLLERS['roll']['max_angle']+
                           cfg.FLIGHT_ATTITUDE_TRIM['roll'])
            target_pitch = (sticks.get('pitch', 0)*cfg.CONTROLLERS['pitch']['max_angle']+
                            cfg.FLIGHT_ATTITUDE_TRIM['pitch'])
            offsets = {}
            if mode in ('MANUAL', 'MANUAL_FALLBACK'):
                offsets = {a: sticks[a]*cfg.SERVOS[a]['limit'] for a in cfg.ACTIVE_AXES}
            elif mode == 'STABILIZE':
                # Winkelfehler im Koerperrahmen vermeidet Verwechslung von
                # Euler-Winkelraten und Gyroachsen bei kombinierter Neigung.
                absolute_roll = (target_roll+level['roll'] if 'roll' in cfg.ACTIVE_AXES
                                 else angles[0])
                absolute_pitch = (target_pitch+level['pitch'] if 'pitch' in cfg.ACTIVE_AXES
                                  else angles[1])
                error_body = body_error(pose.q, quaternion(absolute_roll, absolute_pitch, angles[2]))
                for axis in cfg.ACTIVE_AXES:
                    if axis in ('roll', 'pitch'):
                        index = 0 if axis == 'roll' else 1
                        settings = cfg.CONTROLLERS[axis]
                        target_rate = clamp(settings['angle_gain']*error_body[index],
                                            -settings['max_rate'], settings['max_rate'])
                        offsets[axis] = controllers[axis].update(target_rate, 0, sample[3+index], dt, True)
                    else:
                        target_rate = sticks[axis]*cfg.CONTROLLERS[axis]['max_rate']
                        offsets[axis] = controllers[axis].update(target_rate, 0, sample[5], dt, True)
            # Vor Neutralfreigabe keinerlei Servopulse. Danach neutral bei RX-Ausfall.
            if outputs is None and mode in ('MANUAL', 'MANUAL_FALLBACK', 'STABILIZE'):
                outputs = Outputs(cfg.SERVOS, cfg.ACTIVE_AXES)
            pulses = outputs.write(offsets) if outputs is not None else {}
            if time.ticks_diff(now, print_time) >= int(1000/cfg.CONSOLE_HZ):
                rx = {a: receiver.channels[a]['pulse'] for a in cfg.ACTIVE_AXES}
                print('roll=%.1f pitch=%.1f soll=(%.1f,%.1f) rx=%s servo=%s %s %s' %
                      (roll, pitch, target_roll, target_pitch, rx, pulses, mode, fault))
                print_time = now
            if time.ticks_diff(now, log_time) >= int(1000/cfg.LOG_HZ):
                row = '%d,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%d,%d,%d,%.2f,%s\n' % (
                    time.ticks_diff(now, started), mode, roll, pitch, angles[2],
                    target_roll, target_pitch, pulses.get('roll', 0), pulses.get('pitch', 0),
                    pulses.get('yaw', 0), dt*1000, fault)
                log.append(row)
                log_time = now
            remaining = cfg.LOOP_US-time.ticks_diff(time.ticks_us(), start)
            if remaining > 0:
                time.sleep_us(remaining)
    except KeyboardInterrupt:
        print('Test gestoppt')
    finally:
        if outputs is not None:
            outputs.close()
        if receiver is not None:
            receiver.close()
        print('PWM/PIO ausgeschaltet')
        if cfg.SAVE_LOG_ON_STOP and log.count:
            # Keine Flashzugriffe, solange Servos/Regelung laufen.
            stamp = time.ticks_ms()
            path = 'bench_%d.csv' % stamp
            try:
                log.save(path)
                print('RAM-Log gespeichert:', path)
            except OSError as error:
                print('Log konnte nicht gespeichert werden:', error)
