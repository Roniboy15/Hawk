"""MPU-kompatibles Modul konfigurieren, messen und Gyro-Nullpunkt erfassen.

Hauptklasse IMU: read() liefert (ax,ay,az,gx,gy,gz), accel in g, gyro in Grad/s;
calibrate_gyro() prueft Ruhe und bestimmt Offsets fuer diesen Start.
Logik: Sensoroffset/Skalierung -> rechtshaendige Koordinatentransformation ->
Gyrooffset abziehen. Kennung 0x72 bleibt ausdruecklich nur im Tischtest erlaubt.
Kein Servo wird hier angesteuert. Bereiche/Umrechnung kommen aus config.SENSOR.
"""
import math
import time
from struct import unpack_from
from machine import Pin, I2C


def ranges(settings):
    """MPU-60x0-Registerwerte UND zugehoerige LSB pro physikalischer Einheit."""
    accel = (2, 4, 8, 16).index(settings.get('accel_range_g', 2))
    gyro = (250, 500, 1000, 2000).index(settings.get('gyro_range_dps', 250))
    return accel << 3, gyro << 3, (16384, 8192, 4096, 2048)[accel], (131, 65.5, 32.8, 16.4)[gyro]


def validate_transform(axes, signs):
    if (not isinstance(axes, (list, tuple)) or not isinstance(signs, (list, tuple)) or
            len(axes) != 3 or len(signs) != 3 or
            any(type(axis) is not int for axis in axes) or
            any(type(sign) is not int for sign in signs) or
            sorted(axes) != [0, 1, 2] or any(s not in (-1, 1) for s in signs)):
        raise ValueError('Ungueltige Sensorachsenzuordnung')
    inversions = sum(axes[i] > axes[j] for i in range(3) for j in range(i+1, 3))
    if ((-1) ** inversions) * signs[0] * signs[1] * signs[2] != 1:
        raise ValueError('Sensortransformation muss rechtshaendig sein')


class IMU:
    def __init__(self, settings, allow_id72):
        self.settings = settings
        accel_reg, gyro_reg, self.accel_lsb, self.gyro_lsb = ranges(settings)
        validate_transform(settings['body_axes'], settings['body_signs'])
        if any(s <= 0 for s in settings['acc_scale']):
            raise ValueError('Ungueltige Beschleunigungsskalierung')
        self.bus = I2C(0, sda=Pin(settings['sda']), scl=Pin(settings['scl']),
                       freq=settings['freq'])
        found = self.bus.scan()
        self.addr = 0x68 if 0x68 in found else 0x69 if 0x69 in found else None
        if self.addr is None:
            raise RuntimeError('Kein Sensor bei 0x68/0x69')
        self.identity = self.bus.readfrom_mem(self.addr, 0x75, 1)[0]
        if self.identity != 0x68 and not (allow_id72 and self.identity == 0x72):
            raise RuntimeError('Unbekannte Sensor-ID: ' + hex(self.identity))
        print('Sensor-ID:', hex(self.identity), 'nur Bodenversuch')
        self.write(0x6B, 0x80)
        time.sleep_ms(100)
        for register, value in ((0x6B, 1), (0x1A, 3), (0x19, 9),
                                (0x1B, gyro_reg), (0x1C, accel_reg)):
            self.write(register, value)
            if self.bus.readfrom_mem(self.addr, register, 1)[0] != value:
                raise RuntimeError('Sensoreinstellung nicht uebernommen')
        print('IMU-Bereiche: +/-', settings.get('accel_range_g', 2), 'g; +/-',
              settings.get('gyro_range_dps', 250), 'Grad/s; Register bestaetigt')
        time.sleep_ms(100)
        self.buffer = bytearray(14)
        self.bias = (0.0, 0.0, 0.0)
        self.saturated = False
        self.accel_saturated = self.gyro_saturated = False
        self.saturation_counts = [0, 0]
        self.first_saturation = None  # Ein Rohsatz fuer die Diagnose, kein wachsender Log.

    def write(self, register, value):
        self.bus.writeto_mem(self.addr, register, bytes([value]))

    def read(self):
        self.bus.readfrom_mem_into(self.addr, 0x3B, self.buffer)
        # Ein entpackter Rohsatz statt Python-Schleife und Generatoren je Messung:
        # weniger kurzlebige Objekte im langsamen IMU-/Lageabschnitt von F2.
        values = unpack_from('>7h', self.buffer)
        self.accel_saturated = max(abs(values[0]), abs(values[1]), abs(values[2])) >= 32700
        self.gyro_saturated = max(abs(values[4]), abs(values[5]), abs(values[6])) >= 32095
        self.saturated = self.accel_saturated or self.gyro_saturated
        self.saturation_counts[0] += self.accel_saturated
        self.saturation_counts[1] += self.gyro_saturated
        if self.saturated and self.first_saturation is None:
            self.first_saturation = values  # ax,ay,az,Temperatur,gx,gy,gz, alle roh.
        offset, scale = self.settings['acc_offset'], self.settings['acc_scale']
        acc = ((values[0]/self.accel_lsb-offset[0])/scale[0],
               (values[1]/self.accel_lsb-offset[1])/scale[1],
               (values[2]/self.accel_lsb-offset[2])/scale[2])
        gyro = (values[4]/self.gyro_lsb, values[5]/self.gyro_lsb, values[6]/self.gyro_lsb)
        x, y, z = self.settings['body_axes']
        sx, sy, sz = self.settings['body_signs']
        return (sx*acc[x], sy*acc[y], sz*acc[z],
                sx*gyro[x]-self.bias[0], sy*gyro[y]-self.bias[1], sz*gyro[z]-self.bias[2])

    def calibrate_gyro(self, std_limit=1.0):
        self.bias = (0.0, 0.0, 0.0)
        print('Sensor 6 Sekunden unbewegt halten')
        time.sleep_ms(2000)
        sums, squares = [0.0]*6, [0.0]*6
        count = 400
        for _ in range(count):
            sample = self.read()
            if self.saturated:
                raise RuntimeError('Sensor waehrend Kalibrierung saturiert')
            for i, value in enumerate(sample):
                sums[i] += value
                squares[i] += value*value
            time.sleep_ms(10)
        mean = [value/count for value in sums]
        std = [math.sqrt(max(0, squares[i]/count-mean[i]**2)) for i in range(6)]
        magnitude = math.sqrt(sum(value*value for value in mean[:3]))
        print('Mittel:', mean, 'Streuung:', std)
        if (not 0.85 < magnitude < 1.15 or max(std[:3]) > 0.03 or
                max(std[3:]) > std_limit or max(abs(v) for v in mean[3:]) > 10):
            raise RuntimeError('Gyro-Kalibrierung nicht ruhig/plausibel')
        self.bias = tuple(mean[3:])
        return mean[:3]
