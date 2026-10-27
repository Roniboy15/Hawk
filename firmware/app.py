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
v0.2.3 sammelt Laufzeitmaxima jeder Iteration und begrenzte Zustandswechsel;
CSV/JSON werden gemeinsam nach Stop exportiert. Keine Fehler-Injektion im App-Start.
"""
import math
import sys
import time
import config as cfg
from calibration import load, check_orientation
from imu import IMU, validate_transform, ranges
from attitude import Attitude, wrap_degrees, quaternion, body_error, clamp, MAX_DT_S
from receiver import Receiver, normalize
from control import AxisController, Gate, select_mode
from outputs import Outputs
from logger import RingLog
from diagnostics import BenchDiagnostics, StageTiming, rx_snapshot


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
    checked = cfg.DIRECTION_CHECKED_AXES
    if (not isinstance(checked, (tuple, list)) or
            any(axis not in ('roll', 'pitch', 'yaw') for axis in checked) or
            len(set(checked)) != len(checked)):
        raise ValueError('DIRECTION_CHECKED_AXES ungueltig')
    # SENSOR/MANUAL bleiben fuer die Pruefung erreichbar. STABILIZE darf aber
    # keine neue Achse mit ungeprueftem Sensor-/Sender-/Servozeichen regeln.
    if cfg.START_MODE == 'stabilize':
        for axis in cfg.ACTIVE_AXES:
            if axis not in checked:
                raise ValueError(axis+': zuerst SENSOR/MANUAL pruefen, dann DIRECTION_CHECKED_AXES')
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
    _number('EVENT_CAPACITY', cfg.EVENT_CAPACITY, 1, 256, integer=True)
    for name in ('LOG_HZ', 'CONSOLE_HZ'):
        value = getattr(cfg, name)
        _number(name, value, 0, min(1000, 1000000/cfg.LOOP_US))
        if value == 0:
            raise ValueError(name+' muss positiv sein')
    _number('GYRO_STD_MAX', cfg.GYRO_STD_MAX, 0)
    _number('ATTITUDE_ACCEL_GAIN', cfg.ATTITUDE_ACCEL_GAIN, 0)
    ranges(cfg.SENSOR)
    for name, low, high in (('quiet_s', 1, 10), ('gyro_max_dps', 0.1, 10),
                             ('accel_band_g', 0.01, 0.1), ('max_correction_dps', 0.1, 10)):
        _number('Lage-Wiederfang '+name, cfg.ATTITUDE_RECOVERY[name], low, high)
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


def run_metadata(data):
    """Verwendete Einstellungen/Runtime sichern, ohne Geraetekalibrierung zu aendern."""
    return {
        'summary_schema': 1, 'csv_schema': 2, 'version': cfg.VERSION,
        'runtime': {'implementation': sys.implementation.name, 'version': sys.version,
                    'machine': getattr(sys.implementation, '_machine', '')},
        'configuration': {
            'requested_mode': cfg.START_MODE, 'auto_start': cfg.AUTO_START,
            'active_axes': list(cfg.ACTIVE_AXES),
            'direction_checked_axes': list(cfg.DIRECTION_CHECKED_AXES),
            'loop_us': cfg.LOOP_US, 'max_loop_us': cfg.MAX_LOOP_US,
            'rx_timeout_ms': cfg.RX_TIMEOUT_MS, 'neutral_frames': cfg.NEUTRAL_FRAMES,
            'neutral_window': cfg.NEUTRAL_WINDOW,
            'rx_recovery_requires_neutral': cfg.START_MODE != 'manual',
            'log_hz': cfg.LOG_HZ, 'console_hz': cfg.CONSOLE_HZ,
            'log_capacity': cfg.LOG_CAPACITY, 'event_capacity': cfg.EVENT_CAPACITY,
            'gyro_std_max': cfg.GYRO_STD_MAX, 'attitude_accel_gain': cfg.ATTITUDE_ACCEL_GAIN,
            'attitude_recovery': cfg.ATTITUDE_RECOVERY,
            'pitch_control_limit_deg': cfg.PITCH_CONTROL_LIMIT_DEG,
            'sensor': cfg.SENSOR, 'flight_attitude_trim': cfg.FLIGHT_ATTITUDE_TRIM,
            'receiver': {a: cfg.RECEIVER[a] for a in cfg.ACTIVE_AXES},
            'servos': {a: cfg.SERVOS[a] for a in cfg.ACTIVE_AXES},
            'controllers': {a: cfg.CONTROLLERS[a] for a in cfg.ACTIVE_AXES}},
        'calibration': data}


def run(session=None):
    validate_config()
    if session is not None and cfg.START_MODE not in ('sensor', 'manual'):
        raise ValueError('Erster Fluglogger unterstuetzt nur SENSOR/MANUAL')
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
    # Flugsession besitzt einen ganzen Aufnahme-Puffer; keinen zweiten
    # Text-Ring parallel fuellen. Der bisherige Benchpfad bleibt unveraendert.
    log = RingLog(cfg.LOG_CAPACITY) if session is None else None
    diagnostics = BenchDiagnostics(cfg.LOOP_US, cfg.MAX_LOOP_US, cfg.EVENT_CAPACITY)
    # Vorhandene Phasenmessung auch in MANUAL: F2 hatte einen Steueraussetzer,
    # dessen langsamer Abschnitt ohne diese Diagnose unbekannt bleibt.
    # Feste Messfelder vor der RAM-Reservepruefung erzeugen.
    # Alle Messkosten bleiben in Work/Period; keine Aenderung der Deadline.
    stages = StageTiming(time) if session is not None else None
    if session is not None:
        session.stage_timing = stages
    metadata = run_metadata(data)
    fault = ''
    pose = Attitude(cfg.ATTITUDE_ACCEL_GAIN, cfg.ATTITUDE_RECOVERY)
    controllers = {axis: AxisController(cfg.CONTROLLERS[axis], cfg.SERVOS[axis]['limit'])
                   for axis in cfg.ACTIVE_AXES}
    gate = Gate(cfg.NEUTRAL_FRAMES, cfg.NEUTRAL_WINDOW,
                resume_after_loss=cfg.START_MODE == 'manual')
    last_sequence = {}
    sample = (0, 0, 1, 0, 0, 0)
    angles = (0, 0, 0)
    construction_complete = True
    stopped = False
    stop_reason = 'exception'
    flight_report = None
    in_iteration = False
    try:
        try:
            imu = IMU(cfg.SENSOR, cfg.ALLOW_ID72_BENCH)
            print('Phase GYRO_CAL t=%d ms: noch kein PWM-Start' % time.ticks_ms())
            acc = imu.calibrate_gyro(cfg.GYRO_STD_MAX)
            print('Phase GYRO_DONE t=%d ms' % time.ticks_ms())
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
        if session is not None:
            construction_complete = False
            session.start(metadata)  # Alle Objekte/RAM-Reserve vor erster PWM pruefen.
            construction_complete = True
        print('Version:', cfg.VERSION, '| Modus:', cfg.START_MODE,
              '| Achsen:', cfg.ACTIVE_AXES)
        print('Koerperkonvention: +roll=rechts, +pitch=Nase runter, +yaw=Nase links')
        print('Richtungen bestaetigt:', cfg.DIRECTION_CHECKED_AXES)
        print('Neutral nur beim ersten Start.' if cfg.START_MODE == 'manual' else
              'Neutral vor Aktivierung und nach RX-Ausfall.')
        print('Ohne Lagekalibrierung: Winkel relativ zum Sensorkoordinatensystem.')
        previous = time.ticks_us()
        started = time.ticks_ms()
        print_time, log_time = started, started
        last_mode = None
        first_iteration = True
        while True:
            start = time.ticks_us()
            in_iteration = True
            elapsed_us = time.ticks_diff(start, previous)
            previous = start
            # Erste Differenz ist nur Startvorbereitung, kein ganzer Loopabstand.
            measured_period = None if first_iteration else elapsed_us
            first_iteration = False
            if stages is not None:
                stages.begin(start, measured_period)
            dt = max(elapsed_us, 1)/1000000
            timing_failed = elapsed_us < 0 or elapsed_us > cfg.MAX_LOOP_US
            sensor_error = None
            imu_fresh = False
            gyro_fresh = False
            # Beim Datenlogger IMU nach einem verriegelten Automatikfehler weiter
            # erfassen. Fault bleibt gesetzt; das schaltet keine Stabilisierung frei.
            if imu is not None and (not fault or session is not None) and not timing_failed:
                try:
                    sample = imu.read()
                    # Erst NACH dem Read pruefen. Ein spaet zurueckkehrender Bus
                    # darf nicht noch einen STABILIZE-Ausgang mit altem dt liefern.
                    timing_failed = deadline_missed(start)
                    if not timing_failed:
                        if getattr(imu, 'gyro_saturated', imu.saturated):
                            raise ValueError('Messbereich ueberschritten')
                        # Accel-Clipping darf gueltige Gyrodrehung nicht verlieren.
                        # Automatikfehler bleibt trotzdem verriegelt.
                        pose.update(sample, dt, use_accel=not getattr(imu, 'accel_saturated', False))
                        angles = pose.angles()
                        gyro_fresh = True
                        imu_fresh = not imu.saturated
                        if (imu.saturated or not pose.tilt_valid) and not fault:
                            # Ungueltige Lage nach TIMING ersetzt dessen Ursache nicht.
                            sensor_error = ValueError('Accel gesaettigt oder Lage noch ungueltig')
                            fault = 'IMU_RUNTIME'
                        if not fault and abs(angles[1]) > cfg.PITCH_CONTROL_LIMIT_DEG:
                            fault = 'PITCH_RANGE'
                except Exception as error:
                    pose.invalidate()
                    fault = 'IMU_RUNTIME'
                    sensor_error = error
            if stages is not None:
                stages.mark(0)  # IMU inkl. Lageberechnung und Deadlinepruefungen.
            now = time.ticks_ms()
            timing_failed = timing_failed or deadline_missed(start)
            if not timing_failed:
                receiver.poll(now)
                timing_failed = deadline_missed(start)
            if timing_failed:
                imu_fresh = gyro_fresh = False
                pose.invalidate()
                if not fault:
                    fault = 'TIMING'
                # Nach Zeitverlust ist auch das Alter gepufferter RC-Worte
                # unbekannt. Verwerfen; erst neue Frames duerfen steuern.
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
            target_yaw_rate = (sticks.get('yaw', 0)*cfg.CONTROLLERS['yaw']['max_rate']
                               if 'yaw' in cfg.ACTIVE_AXES else 0.0)
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
                        offsets[axis] = controllers[axis].update(target_yaw_rate, 0, sample[5], dt, True)
            # Vor Neutralfreigabe keinerlei Servopulse. Danach neutral bei RX-Ausfall.
            if (outputs is None and mode in ('MANUAL', 'MANUAL_FALLBACK', 'STABILIZE')
                    and not deadline_missed(start)):
                # Zeitmarke erlaubt spaeter Korrelation mit einer Stoerung.
                # "REQUEST" beweist noch keinen Start und Diagnose kann blockieren.
                print('Phase PWM_START_REQUEST t=%d ms axes=%s' %
                      (time.ticks_ms(), str(cfg.ACTIVE_AXES)))
                # Nach Konsolenausgabe erneut pruefen: keine PWM nach erkannter Deadline.
                if not deadline_missed(start):
                    construction_complete = False
                    outputs = Outputs(cfg.SERVOS, cfg.ACTIVE_AXES)
                    construction_complete = True
            # Zweite Schranke direkt vor der Ausgabe: auch Reglerrechnung oder
            # PWM-Initialisierung koennen Zeit verbrauchen. Frische Freigabe
            # verwerfen, wenn eine Zeitueberschreitung erkannt wurde.
            if not timing_failed and deadline_missed(start):
                timing_failed = True
                if not fault:
                    fault = 'TIMING'
                receiver.invalidate(time.ticks_ms())
                gate.update(False, [], False)
                fresh = False
                for controller in controllers.values():
                    controller.reset()
                offsets = {}
                mode = select_mode(cfg.START_MODE, False, False, fault, reference_ok)
            # Diagnose erst nach der letzten Sicherheitsschranke bzw. Ausgabe
            # sammeln. Keine Strings/Dateizugriffe zwischen Freigabe und PWM.
            output_start = time.ticks_us()
            pre_output_us = time.ticks_diff(output_start, start) if outputs is not None else None
            pulses = outputs.write(offsets) if outputs is not None else {}
            write_us = time.ticks_diff(time.ticks_us(), output_start) if outputs is not None else None
            if stages is not None:
                stages.mark(1)  # RC/Freigabe/Regler/Ausgabe zusammen.
            # RX-Alter bezieht sich auf den Entscheidungszeitpunkt `now`, nicht
            # auf eine vermeintlich neue Hardware-Capture-Zeit bei der Ausgabe.
            rx_state = rx_snapshot(receiver.channels, cfg.ACTIVE_AXES, now, time.ticks_diff)
            transition = diagnostics.transition(time.ticks_diff(now, started), mode, fault,
                                                 outputs is not None, gate.armed, gate.count,
                                                 fresh, rx_state, pulses)
            # Konsolenausgabe erst nach dem begrenzten Aktuatorkommando.
            if sensor_error is not None and transition:
                print('Automatik aus:', sensor_error)
            if mode != last_mode:
                print('Zustand:', mode, 'Fehler:', fault or '-',
                      't=%d ms' % time.ticks_diff(now, started))
                last_mode = mode
            elif transition:
                print('Fehlerwechsel:', fault or '-', 't=%d ms' % time.ticks_diff(now, started))
            if session is None and time.ticks_diff(now, print_time) >= int(1000/cfg.CONSOLE_HZ):
                rx = {a: receiver.channels[a]['pulse'] for a in cfg.ACTIVE_AXES}
                print('roll=%.1f pitch_down=%.1f soll=(%.1f,%.1f) gyro=(%.1f,%.1f,%.1f) yaw_rate_left=%.1f rx=%s servo=%s %s %s' %
                      (roll, pitch, target_roll, target_pitch, sample[3], sample[4], sample[5],
                       target_yaw_rate, rx, pulses, mode, fault))
                print_time = now
            # Auch kurze Zustands-/Fault-Wechsel loggen, die zwischen 10-Hz-
            # Samples liegen. Ringgroesse bleibt fest; JSON bewahrt Laufmaxima.
            if log is not None and (transition or time.ticks_diff(now, log_time) >= int(1000/cfg.LOG_HZ)):
                row = '%d,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%d,%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f,%s' % (
                    time.ticks_diff(now, started), mode, roll, pitch, angles[2],
                    target_roll, target_pitch, pulses.get('roll', 0), pulses.get('pitch', 0),
                    pulses.get('yaw', 0), dt*1000, sample[3], sample[4], sample[5],
                    target_yaw_rate, fault)
                row += ',%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n' % (
                    pre_output_us if pre_output_us is not None else -1,
                    write_us if write_us is not None else -1,
                    rx_state[0][0], rx_state[0][1], rx_state[0][2],
                    rx_state[1][0], rx_state[1][1], rx_state[1][2],
                    rx_state[2][0], rx_state[2][1], rx_state[2][2],
                    gate.count, int(gate.armed), int(fresh))
                log.append(row)
                log_time = now
            if stages is not None:
                stages.mark(2)  # Ereignisdiagnose und eventuelle Konsole.
            stop_requested = False
            if session is not None:
                # Zusatzarbeit NACH der Servoausgabe, vor Work-Zeitmessung.
                # Ihr Zeitbedarf bleibt in Work/naechster Periode sichtbar.
                try:
                    stop_requested = session.step(time.ticks_ms(), {
                        'mode': mode, 'fault': fault, 'angles': (roll, pitch, angles[2]),
                        'sample': sample, 'imu_fresh': imu_fresh, 'rx': rx_state,
                        'gyro_fresh': gyro_fresh, 'tilt_valid': gyro_fresh and pose.tilt_valid,
                        'pulses': pulses, 'armed': gate.armed, 'fresh': fresh,
                        'period_us': measured_period, 'iteration_start_us': start})
                except Exception as error:
                    session.fail('logger', error)  # Keine neue MANUAL-Ausfallursache.
            # Work umfasst Sensor/Regler/PWM/Konsole/CSV-Formatierung bis hier.
            # Dieser Counter-Update und sleep sind nicht enthalten; der naechste
            # gemessene Startabstand umfasst dagegen die ganze vorige Iteration.
            work_us = time.ticks_diff(time.ticks_us(), start)
            diagnostics.finish(measured_period, pre_output_us, write_us, work_us, timing_failed)
            if stages is not None:
                stages.mark(8)  # Rest bis Diagnoseabschluss; sleep folgt danach.
            in_iteration = False
            if stop_requested:
                stopped, stop_reason = True, 'ground_button'
                break
            remaining = cfg.LOOP_US-time.ticks_diff(time.ticks_us(), start)
            if remaining > 0:
                time.sleep_us(remaining)
    except KeyboardInterrupt:
        stopped = True  # Stopmeldung erst NACH den Abschaltversuchen ausgeben.
        stop_reason = 'keyboard_interrupt'
    except Exception as error:
        if session is not None:
            metadata['stop_exception'] = type(error).__name__+': '+str(error)[:160]
        raise
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
        session_error = None
        if session is not None:
            try:
                session.close()
            except BaseException as error:
                shutdown_ok = False
                session_error = error
        # Auch eine blockierende/fehlerhafte Konsole darf nicht zwischen den
        # Abschaltversuchen stehen: Diagnose erst nach ALLEN Ressourcen.
        if stopped:
            print('Test gestoppt')
        if output_error is not None:
            print('PWM-Abschalten fehlgeschlagen:', output_error)
        if receiver_error is not None:
            print('PIO-Abschalten fehlgeschlagen:', receiver_error)
        if session_error is not None:
            print('Logger-Ressourcen-Abschalten fehlgeschlagen:', session_error)
        if shutdown_ok:
            print('PWM/PIO ausgeschaltet')
            stats = diagnostics.report()
            print('Timing: Iterationen=%d TIMING-Erkennungen=%d' %
                  (stats['iterations'], stats['timing_trips']))
            for name in ('period', 'pre_output', 'write', 'work'):
                value = stats['timing'][name]
                print('  %s: max_us=%s ueber_Sollperiode=%d ueber_Deadline=%d ungueltig=%d' %
                      (name, str(value['max_us']), value['over_period'],
                       value['over_deadline'], value['invalid']))
        else:
            # Kein Flashzugriff, wenn die Aktuatorabschaltung unbestaetigt ist.
            print('Abschalten unvollstaendig; kein Logexport. Versorgung trennen.')
        if session is not None and shutdown_ok:
            metadata['imu_first_saturation_raw'] = getattr(imu, 'first_saturation', None)
            metadata['imu_saturation_samples'] = getattr(imu, 'saturation_counts', None)
            metadata['tilt_recoveries'] = pose.recoveries
            metadata['tilt_valid_at_stop'] = pose.tilt_valid
            metadata['partial_iteration_on_stop'] = in_iteration
            session.export_context = (metadata, diagnostics, stop_reason)
            session.can_export = True  # Erst jetzt PWM/Steuer-PIO/Aux-PIO/UART bestaetigt aus.
            try:
                flight_report = session.export(*session.export_context)
            except Exception as error:
                session.fail('export', error)
                session.color((session.settings['led_brightness'], 0, 0))
                print('Export fehlgeschlagen; Versorgung behalten. flight_start.save_pending():', error)
        if shutdown_ok and cfg.SAVE_LOG_ON_STOP and log is not None and log.count:
            # Keine Flashzugriffe, solange Servos/Regelung laufen.
            stamp = time.ticks_ms()
            path = 'bench_%d.csv' % stamp
            try:
                log.save(path)
                metadata.update(csv_file=path, shutdown_ok=True,
                                stop_reason='keyboard_interrupt' if stopped else 'exception',
                                csv_rows_total=log.total, csv_rows_retained=log.count,
                                partial_iteration_on_stop=in_iteration)
                diagnostics.save('bench_%d.json' % stamp, metadata)
                print('RAM-Log gespeichert:', path)
                print('Laufbericht gespeichert: bench_%d.json' % stamp)
            except OSError as error:
                print('Log konnte nicht gespeichert werden:', error)
    return flight_report
