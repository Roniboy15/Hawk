"""Zentrale Einstellungen; hier werden Pins und Parameter angepasst.

Hauptteile: START_MODE/ACTIVE_AXES, SENSOR, RECEIVER, SERVOS, CONTROLLERS.
Logik: Hardwaremodule lesen diese Werte beim Start. Nach einer Aenderung
alle Dateien speichern und den MCU soft-resetten; Imports sind gecacht.
Nur Bodenversuch. Kein autonomer Flug, keine Thermiknavigation.
Koordinaten wie im bisherigen Rolltest: X vorwaerts, Y links, Z oben.
Roll = atan2(ay, az), Nick = atan2(-ax, sqrt(ay^2+az^2)).
Die Vorzeichen von Sender und Rudern werden getrennt konfiguriert.
"""

VERSION = '0.2.1-bench'
AUTO_START = False
START_MODE = 'sensor'             # sensor / manual / stabilize
ACTIVE_AXES = ('roll',)            # danach ('roll', 'pitch'), spaeter 'yaw'
ALLOW_ID72_BENCH = True            # fuer diesen getesteten Sensor, kein Typnachweis
LOOP_US = 10000
MAX_LOOP_US = 50000                # auch RX-Pollbudget; <= attitude.MAX_DT_S
CALIBRATION_FILE = 'calibration.json'

SENSOR = {'sda': 4, 'scl': 5, 'freq': 100000,
          'acc_offset': (0.0142, 0.02775, 0.19325),
          'acc_scale': (0.9924, 1.00085, 1.02405),
          'body_axes': (0, 1, 2), 'body_signs': (1, 1, 1)}
GYRO_STD_MAX = 1.0
ATTITUDE_ACCEL_GAIN = 1.0          # Gravitation nur schwach zur Driftkorrektur
PITCH_CONTROL_LIMIT_DEG = 75.0    # Euler-Reglerbereich, keine Sensorgrenze

# RX-Signale nur 3,3-V-kompatibel an GPIO! Dieser Segler hat kein Gas/Triebwerk.
# GP-Nummern, NICHT physische Pinpositionen. GP3 bleibt Y-Querruder-Ausgang.
RECEIVER = {'roll': {'pin': 2, 'sign': 1},
            'pitch': {'pin': 8, 'sign': 1},
            'yaw': {'pin': 9, 'sign': 1}}
RX_TIMEOUT_MS = 100
NEUTRAL_WINDOW = 0.08
NEUTRAL_FRAMES = 25

SERVOS = {'roll': {'pin': 3, 'center': 1500, 'trim': 0, 'sign': 1, 'limit': 200},
          'pitch': {'pin': 6, 'center': 1500, 'trim': 0, 'sign': 1, 'limit': 150},
          'yaw': {'pin': 7, 'center': 1500, 'trim': 0, 'sign': 1, 'limit': 150}}

# Zweistufig: Winkelfehler -> Sollrate -> Servo. I-Anteil vorerst 0.
# Diese Werte sind konservative Bodenversuchsparameter, keine Flugabstimmung.
CONTROLLERS = {
    'roll': {'angle_gain': 2.0, 'rate_p': 1.5, 'rate_i': 0.0,
             'integral_limit': 30.0, 'max_rate': 60.0, 'max_angle': 20.0},
    'pitch': {'angle_gain': 2.0, 'rate_p': 1.0, 'rate_i': 0.0,
              'integral_limit': 20.0, 'max_rate': 40.0, 'max_angle': 10.0},
    'yaw': {'rate_p': 1.0, 'rate_i': 0.0, 'integral_limit': 20.0,
            'max_rate': 40.0}}
FLIGHT_ATTITUDE_TRIM = {'roll': 0.0, 'pitch': 0.0}  # Solllage, NICHT Sensoroffset

LOG_HZ = 10
LOG_CAPACITY = 200                 # letzte 20 Sekunden, fester RAM-Ring
CONSOLE_HZ = 4
SAVE_LOG_ON_STOP = True            # erst NACH Abschalten der PWM auf Flash
