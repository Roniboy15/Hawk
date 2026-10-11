"""Bodenversuch orchestrieren: Sensor -> Lage -> RC -> Modus -> Regler -> Servo.

Hauptfunktion run(): Initialisierung, 100-Hz-Schleife, Fehlerbehandlung, Aufraeumen.
validate_config() prueft Parameter vor Hardwarestart. PWM startet erst nach RC-Kalibrierung
und einmaliger Neutralfreigabe. Standard START_MODE='sensor' erzeugt keine PWM.
Groesserer Rollwinkel ist kein Fehler. Nick >75 Grad, Saettigung, Sensorfehler
oder zu lange Schleife verriegeln die Automatik in MANUAL_FALLBACK, solange RX
gueltig ist. RX-Ausfall neutralisiert und verlangt neue Neutralfreigabe.
Erkannter Zeitverlust verwirft RC-Puffer, neutralisiert noch in dieser Iteration
und verlangt neue Neutralframes vor dem manuellen Ersatz. Deadline nach Read
und vor Ausgabe pruefen; ein dauerhaft blockierter Bus bleibt ungelöst.
Diese Software ist kein unabh. Bypass: haengende CPU/I2C wird nicht geloest.
Logs bleiben im RAM; erst nach dem Abschalten der PWM wird CSV geschrieben.
"""
import math
import time
import config as cfg
from calibration import load, check_orientation
from imu import IMU, validate_transform
from attitude import Attitude, wrap_degrees, quaternion, body_error, clamp, MAX_DT_S
from receiver import Receiver, normalize
from control import AxisController, Gate, select_mode
from outputs import Outputs
from logger import RingLog


def _number(name, value, low=None, high=None, integer=False):
    """Parameter vor Hardwarestart pruefen; NaN darf Grenztests nicht umgehen."""
    if (type(value) not in (int, float) or not math.isfinite(value) or
            (integer and type(value) is not int) or
            (low is not None and value < low) or
            (high is not None and value > high)):
        raise ValueError(name+' ungueltig')


def validate_config():
    # Erst alle benoetigten Werte pruefen: kein Sensor/PIO/PWM bei Fehlkonfiguration.
    if cfg.START_MODE not in ('sensor', 'manual', 'stabilize'):
        raise ValueError('START_MODE ungueltig')
    if (not isinstance(cfg.ACTIVE_AXES, (tuple, list)) or not cfg.ACTIVE_AXES or
            any(axis not in ('roll', 'pitch', 'yaw') for axis in cfg.ACTIVE_AXES) or
            len(set(cfg.ACTIVE_AXES)) != len(cfg.ACTIVE_AXES)):
        raise ValueError('ACTIVE_AXES leer/doppelt')
    for name in ('AUTO_START', 'ALLOW_ID72_BENCH', 'SAVE_LOG_ON_STOP'):
        if type(getattr(cfg, name)) is not bool:
            raise ValueError(name+' muss bool sein')
    _number('LOOP_US', cfg.LOOP_US, 1, integer=True)
    _number('MAX_LOOP_US', cfg.MAX_LOOP_US, cfg.LOOP_US,
            int(MAX_DT_S*1000000), integer=True)
    # Der konservative RX-Zeitstempel kann um ein Pollintervall aelter sein.
    max_poll_ms = (cfg.MAX_LOOP_US+999)//1000
    _number('RX_TIMEOUT_MS', cfg.RX_TIMEOUT_MS, max_poll_ms+1, integer=True)
    _number('NEUTRAL_FRAMES', cfg.NEUTRAL_FRAMES, 1, integer=True)
    _number('NEUTRAL_WINDOW', cfg.NEUTRAL_WINDOW, 0)
    if cfg.NEUTRAL_WINDOW >= 1:
        raise ValueError('NEUTRAL_WINDOW muss kleiner 1 sein')
    _number('LOG_CAPACITY', cfg.LOG_CAPACITY, 1, integer=True)
    for name in ('LOG_HZ', 'CONSOLE_HZ'):
        value = getattr(cfg, name)
        _number(name, value, 0, min(1000, 1000000/cfg.LOOP_US))
        if value == 0:
            raise ValueError(name+' muss positiv sein')
    _number('GYRO_STD_MAX', cfg.GYRO_STD_MAX, 0)
    _number('ATTITUDE_ACCEL_GAIN', cfg.ATTITUDE_ACCEL_GAIN, 0)
    _number('PITCH_CONTROL_LIMIT_DEG', cfg.PITCH_CONTROL_LIMIT_DEG, 0, 90)
    if cfg.GYRO_STD_MAX == 0 or not 0 < cfg.PITCH_CONTROL_LIMIT_DEG < 90:
        raise ValueError('Sensor-/Nickgrenze ungueltig')
    validate_transform(cfg.SENSOR['body_axes'], cfg.SENSOR['body_signs'])
    for name in ('acc_offset', 'acc_scale'):
        vector = cfg.SENSOR[name]
        if not isinstance(vector, (list, tuple)) or len(vector) != 3:
            raise ValueError(name+' braucht 3 Werte')
        for value in vector:
            _number(name, value)
            if name == 'acc_scale' and value <= 0:
                raise ValueError('acc_scale muss positiv sein')
    _number('I2C-Frequenz', cfg.SENSOR['freq'], 1, integer=True)
    pins = [cfg.SENSOR['sda'], cfg.SENSOR['scl']]
    for axis in cfg.ACTIVE_AXES:
        pins.extend((cfg.RECEIVER[axis]['pin'], cfg.SERVOS[axis]['pin']))
        if cfg.RECEIVER[axis]['sign'] not in (-1, 1) or cfg.SERVOS[axis]['sign'] not in (-1, 1):
            raise ValueError('Vorzeichen muss +/-1 sein')
        s = cfg.SERVOS[axis]
        for name in ('center', 'limit', 'trim'):
            _number('Servo '+name, s[name])
        if not (100 <= s['limit'] <= 400 and
                900 <= s['center']-s['limit'] < s['center']+s['limit'] <= 2100):
            raise ValueError('Servogrenzen unplausibel')
        if abs(s['trim']) > s['limit']:
            raise ValueError('Servotrim ausserhalb Grenzen')
        controller = cfg.CONTROLLERS[axis]
        for name in ('rate_p', 'rate_i', 'integral_limit', 'max_rate'):
            _number(axis+' '+name, controller[name], 0)
        if controller['max_rate'] == 0:
            raise ValueError('max_rate muss positiv sein')
    # Auch inaktive Roll-/Nick-Sollwerte werden fuer die Anzeige berechnet.
    for axis in ('roll', 'pitch'):
        _number(axis+' angle_gain', cfg.CONTROLLERS[axis]['angle_gain'], 0)
        _number(axis+' max_angle', cfg.CONTROLLERS[axis]['max_angle'], 0, 90)
        _number(axis+' Fluglagentrim', cfg.FLIGHT_ATTITUDE_TRIM[axis], -90, 90)
    for pin in pins:
        _number('GPIO', pin, 0, 29, integer=True)
    if len(set(pins)) != len(pins):
        raise ValueError('GPIO mehrfach verwendet')


def deadline_missed(start):
    elapsed = time.ticks_diff(time.ticks_us(), start)
    return elapsed < 0 or elapsed > cfg.MAX_LOOP_US


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
    construction_complete = True
    stopped = False
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
        # Bei abgebrochenem Konstruktor gibt es evtl. Teilressourcen, obwohl
        # die Zuweisung noch fehlt. Dann niemals erfolgreiche Abschaltung melden.
        construction_complete = False
        receiver = Receiver(cfg.RECEIVER, cfg.ACTIVE_AXES, cfg.RX_TIMEOUT_MS,
                            max_poll_ms=(cfg.MAX_LOOP_US+999)//1000)
        construction_complete = True
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
            timing_failed = elapsed_us < 0 or elapsed_us > cfg.MAX_LOOP_US
            sensor_error = None
            if imu is not None and not fault and not timing_failed:
                try:
                    sample = imu.read()
                    # Erst NACH dem Read pruefen. Ein spaet zurueckkehrender Bus
                    # darf nicht noch einen STABILIZE-Ausgang mit altem dt liefern.
                    timing_failed = deadline_missed(start)
                    if not timing_failed:
                        if imu.saturated:
                            raise ValueError('Messbereich ueberschritten')
                        pose.update(sample, dt)
                        angles = pose.angles()
                        if abs(angles[1]) > cfg.PITCH_CONTROL_LIMIT_DEG:
                            fault = 'PITCH_RANGE'
                except Exception as error:
                    fault = 'IMU_RUNTIME'
                    sensor_error = error
            now = time.ticks_ms()
            timing_failed = timing_failed or deadline_missed(start)
            if not timing_failed:
                receiver.poll(now)
                timing_failed = deadline_missed(start)
            if timing_failed:
                if not fault:
                    fault = 'TIMING'
                # Nach Zeitverlust ist auch das Alter gepufferter RC-Worte
                # unbekannt. Neutral und neue Freigabe vor manuellem Ersatz.
                receiver.invalidate(time.ticks_ms())
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
                for controller in controllers.values():
                    controller.reset()
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
            if (outputs is None and mode in ('MANUAL', 'MANUAL_FALLBACK', 'STABILIZE')
                    and not deadline_missed(start)):
                # Schon vor dem allerersten PWM-Start muss die Deadline gelten.
                construction_complete = False
                outputs = Outputs(cfg.SERVOS, cfg.ACTIVE_AXES)
                construction_complete = True
            # Zweite Schranke direkt vor der Ausgabe: auch Reglerrechnung oder
            # PWM-Initialisierung koennen Zeit verbrauchen. Frische Freigabe
            # verwerfen, wenn eine Zeitueberschreitung erkannt wurde.
            if not timing_failed and deadline_missed(start):
                if not fault:
                    fault = 'TIMING'
                receiver.invalidate(time.ticks_ms())
                gate.update(False, [], False)
                for controller in controllers.values():
                    controller.reset()
                offsets = {}
                mode = select_mode(cfg.START_MODE, False, False, fault, reference_ok)
            pulses = outputs.write(offsets) if outputs is not None else {}
            # Konsolenausgabe erst nach dem begrenzten Aktuatorkommando.
            if sensor_error is not None:
                print('Automatik aus:', sensor_error)
            if mode != last_mode:
                print('Zustand:', mode, 'Fehler:', fault or '-')
                last_mode = mode
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
        stopped = True  # Stopmeldung erst NACH den Abschaltversuchen ausgeben.
    finally:
        shutdown_ok = construction_complete
        output_error, receiver_error = None, None
        if outputs is not None:
            try:
                outputs.close()
            except BaseException as error:
                shutdown_ok = False
                output_error = error
        if receiver is not None:
            try:
                receiver.close()
            except BaseException as error:
                shutdown_ok = False
                receiver_error = error
        # Auch eine blockierende/fehlerhafte Konsole darf nicht zwischen den
        # Abschaltversuchen stehen: Diagnose erst nach ALLEN Ressourcen.
        if stopped:
            print('Test gestoppt')
        if output_error is not None:
            print('PWM-Abschalten fehlgeschlagen:', output_error)
        if receiver_error is not None:
            print('PIO-Abschalten fehlgeschlagen:', receiver_error)
        if shutdown_ok:
            print('PWM/PIO ausgeschaltet')
        else:
            # Kein Flashzugriff, wenn die Aktuatorabschaltung unbestaetigt ist.
            print('Abschalten unvollstaendig; kein Logexport. Versorgung trennen.')
        if shutdown_ok and cfg.SAVE_LOG_ON_STOP and log.count:
            # Keine Flashzugriffe, solange Servos/Regelung laufen.
            stamp = time.ticks_ms()
            path = 'bench_%d.csv' % stamp
            try:
                log.save(path)
                print('RAM-Log gespeichert:', path)
            except OSError as error:
                print('Log konnte nicht gespeichert werden:', error)
