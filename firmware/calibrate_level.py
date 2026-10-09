"""Waagerechte Montage-Referenz explizit erfassen, NICHT Flugtrimmung lernen.

Hauptfunktion run(): Gyro-Ruhepruefung -> Roll/Nick aus Gravitation -> JSON.
Sensor muss fest montiert, Flugzeug geometrisch waagerecht und unbewegt sein.
Kein Servo/Receiver wird gestartet. Referenz ist persistent; Gyrooffset wird
bei jedem spaeteren Start neu gemessen. Vorhandene RC-Kalibrierung bleibt erhalten.
"""
import config as cfg
from imu import IMU
from attitude import Attitude
from calibration import load, save


def run():
    input('Flugzeug waagerecht/ruhig ablegen, dann Enter: ')
    imu = IMU(cfg.SENSOR, cfg.ALLOW_ID72_BENCH)
    acc = imu.calibrate_gyro(cfg.GYRO_STD_MAX)
    pose = Attitude()
    pose.seed(acc)
    roll, pitch, _ = pose.angles()
    if abs(roll) > 30 or abs(pitch) > 30:
        raise RuntimeError('Lage nicht hinreichend waagerecht')
    data = load(cfg.CALIBRATION_FILE)
    data['level'] = {'roll': roll, 'pitch': pitch,
                     'axes': list(cfg.SENSOR['body_axes']),
                     'signs': list(cfg.SENSOR['body_signs']),
                     'offset': list(cfg.SENSOR['acc_offset']),
                     'scale': list(cfg.SENSOR['acc_scale'])}
    save(cfg.CALIBRATION_FILE, data)
    print('Referenz gespeichert:', data['level'])


if __name__ == '__main__':
    run()
