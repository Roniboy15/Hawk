"""Zentrale Einstellungen; hier werden Pins und Parameter angepasst.

Hauptteile: START_MODE/ACTIVE_AXES, SENSOR, RECEIVER, SERVOS, CONTROLLERS.
Logik: Hardwaremodule lesen diese Werte beim Start. Nach einer Aenderung
alle Dateien speichern und den MCU soft-resetten; Imports sind gecacht.
Nur Bodenversuch. Kein autonomer Flug, keine Thermiknavigation.
Koordinaten wie im bisherigen Rolltest: X vorwaerts, Y links, Z oben.
Roll = atan2(ay, az), Nick = atan2(-ax, sqrt(ay^2+az^2)).
In diesem Koerperrahmen: +Roll=rechts, +Nick=Nase runter, +Gier=Nase links.
Nase hoch muss einen negativen Nick-Sollwert erhalten; nicht den Gyro einzeln drehen.
Die Vorzeichen von Sender und Rudern werden getrennt konfiguriert.
"""

VERSION = '0.2.3-bench'
AUTO_START = False
# Besitzer meldet am 2026-10-13 alle Achsentests bestanden. Gespeicherter Stand
# startet zur erneuten Sichtpruefung ohne PWM; STABILIZE bewusst am Tisch waehlen.
START_MODE = 'sensor'              # sensor / manual / stabilize
ACTIVE_AXES = ('roll', 'pitch', 'yaw')
# SENSOR/MANUAL/STABILIZE laut Besitzer bestanden; kein elektrischer/Flugnachweis.
# Nach anderer Verdrahtung, Polung oder Montage betroffene Bestaetigung entfernen.
DIRECTION_CHECKED_AXES = ('roll', 'pitch', 'yaw')
ALLOW_ID72_BENCH = True            # fuer diesen getesteten Sensor, kein Typnachweis
LOOP_US = 10000
MAX_LOOP_US = 50000                # auch RX-Pollbudget; <= attitude.MAX_DT_S
CALIBRATION_FILE = 'calibration.json'

SENSOR = {'sda': 4, 'scl': 5, 'freq': 100000,
          'acc_offset': (0.0142, 0.02775, 0.19325),
          'acc_scale': (0.9924, 1.00085, 1.02405),
          'body_axes': (0, 1, 2), 'body_signs': (1, 1, 1)}
# Geplanter Einbau: Oberseite weiter oben, Sensor-X nach hinten/Y nach rechts.
# Erst BEIM mechanischen Umbau body_signs=(-1,-1,1) setzen (180 Grad um Z).
# Das dreht Accel UND Gyro. Danach Lage neu speichern/Richtungen neu pruefen;
# calibrate_level allein erkennt die umgekehrte Laengsrichtung nicht.
# Aktive Werte oben gehoeren noch zum bisherigen getesteten Aufbau.
GYRO_STD_MAX = 1.0
ATTITUDE_ACCEL_GAIN = 1.0          # Gravitation nur schwach zur Driftkorrektur
PITCH_CONTROL_LIMIT_DEG = 75.0    # Euler-Reglerbereich, keine Sensorgrenze

# RX-Signale nur 3,3-V-kompatibel an GPIO! Dieser Segler hat kein Gas/Triebwerk.
# GP-Nummern, NICHT physische Pinpositionen. GP3 bleibt Y-Querruder-Ausgang.
# Rechtsknueppel liefert kleinere Pulse, Rechtsbank ist positiver Rollwinkel.
# Beide Rollzeichen gemeinsam -1: MANUAL bleibt gleich, Feedback wird korrekt.
# Nick/Gier ebenfalls -1/-1 nach Besitzerpruefung: groesserer RX-Puls fordert
# Nase-hoch/Rechtsgier (negative Koerperwerte); groesserer Servopuls wirkt so.
RECEIVER = {'roll': {'pin': 2, 'sign': -1},
            'pitch': {'pin': 8, 'sign': -1},
            'yaw': {'pin': 9, 'sign': -1}}
RX_TIMEOUT_MS = 100
NEUTRAL_WINDOW = 0.08
NEUTRAL_FRAMES = 25

SERVOS = {'roll': {'pin': 3, 'center': 1500, 'trim': 0, 'sign': -1, 'limit': 200},
          'pitch': {'pin': 6, 'center': 1500, 'trim': 0, 'sign': -1, 'limit': 150},
          'yaw': {'pin': 7, 'center': 1500, 'trim': 0, 'sign': -1, 'limit': 150}}
# Mit dieser Servopolung erzeugt ein positives internes Nick-/Gierkommando
# kleinere Pulse: Nase-runter-/Nase-links-Wirkung. Logauswertung: VALIDIERUNG.md.

# Zweistufig: Winkelfehler -> Sollrate -> Servo. I-Anteil vorerst 0.
# Diese Werte sind konservative Bodenversuchsparameter, keine Flugabstimmung.
# Roll rate_p=2: nach Vorzeichenkorrektur am Tisch verwendet, keine Flugabstimmung.
CONTROLLERS = {
    'roll': {'angle_gain': 2.0, 'rate_p': 2, 'rate_i': 0.0,
             'integral_limit': 30.0, 'max_rate': 60.0, 'max_angle': 20.0},
    'pitch': {'angle_gain': 2.0, 'rate_p': 1.0, 'rate_i': 0.0,
              'integral_limit': 20.0, 'max_rate': 40.0, 'max_angle': 10.0},
    'yaw': {'rate_p': 1.0, 'rate_i': 0.0, 'integral_limit': 20.0,
            'max_rate': 40.0}}
FLIGHT_ATTITUDE_TRIM = {'roll': 0.0, 'pitch': 0.0}  # Solllage, NICHT Sensoroffset

LOG_HZ = 10
LOG_CAPACITY = 200                 # ca. 20 s bei 10 Hz; extra Zustandszeilen verkuerzen den Rest
EVENT_CAPACITY = 64                # letzte Zustands-/Fault-Wechsel; ganze Laufstatistik separat
CONSOLE_HZ = 4
SAVE_LOG_ON_STOP = True            # erst NACH Abschalten der PWM auf Flash

# Separater GPS-/Barometer-Funktionstest; app.run() nutzt diese Module noch nicht.
# Keine GPS-Konfiguration senden: GPS-RX bleibt frei, GP12 ist nur reservierter TX.
# Neuer I2C1-Bus schuetzt den bestehenden IMU-Bus auf GP4/GP5 vor Umbauten.
GPS = {'uart': 0, 'tx': 12, 'rx': 13, 'baudrate': 9600,
       'rxbuf': 1024, 'max_read': 256, 'stale_ms': 2500, 'max_poll_ms': 100,
       'course_min_speed_ms': 2.0}
BAROMETER = {'i2c': 1, 'sda': 10, 'scl': 11, 'freq': 100000,
             'address': None, 'sample_ms': 100}
# 0.2.0: Ganzer kurzer Sensorlauf kompakt im RAM, CSV erst nach Testende.
# 2 Hz deckt das 1-Hz-GPS doppelt ab; Barometerpolling und Loop bleiben unveraendert.
SENSOR_TEST = {'version': '0.2.0', 'loop_us': 10000, 'log_hz': 2,
               'console_hz': 1, 'max_log_bytes': 65536, 'reserve_bytes': 32768,
               'reference_warmup_ms': 2000, 'reference_samples': 20}
