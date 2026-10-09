"""MPU-kompatibles Modul konfigurieren, messen und Gyro-Nullpunkt erfassen.

Hauptklasse IMU: read() liefert (ax,ay,az,gx,gy,gz), accel in g, gyro in Grad/s;
calibrate_gyro() prueft Ruhe und bestimmt Offsets fuer diesen Start.
Logik: Sensoroffset/Skalierung -> rechtshaendige Koordinatentransformation ->
Gyrooffset abziehen. Kennung 0x72 bleibt ausdruecklich nur im Tischtest erlaubt.
Kein Servo wird hier angesteuert. Messbereich +/-2 g, +/-250 Grad/s.
"""
import math
import time
from machine import Pin, I2C


def validate_transform(axes, signs):
    if sorted(axes) != [0, 1, 2] or any(s not in (-1, 1) for s in signs):
        raise ValueError('Ungueltige Sensorachsenzuordnung')
    inversions = sum(axes[i] > axes[j] for i in range(3) for j in range(i+1, 3))
    if ((-1) ** inversions) * signs[0] * signs[1] * signs[2] != 1:
        raise ValueError('Sensortransformation muss rechtshaendig sein')


class IMU:
    def __init__(self, settings, allow_id72):
        self.settings = settings
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
        for register, value in ((0x6B, 1), (0x1A, 3), (0x19, 9), (0x1B, 0), (0x1C, 0)):
            self.write(register, value)
            if self.bus.readfrom_mem(self.addr, register, 1)[0] != value:
                raise RuntimeError('Sensoreinstellung nicht uebernommen')
        time.sleep_ms(100)
        self.buffer = bytearray(14)
        self.bias = (0.0, 0.0, 0.0)
        self.saturated = False

    def write(self, register, value):
        self.bus.writeto_mem(self.addr, register, bytes([value]))

    def read(self):
        self.bus.readfrom_mem_into(self.addr, 0x3B, self.buffer)
        values = []
        for i in range(0, 14, 2):
            raw = (self.buffer[i] << 8) | self.buffer[i+1]
            values.append(raw-65536 if raw & 0x8000 else raw)
        self.saturated = (any(abs(values[i]) >= 32700 for i in (0, 1, 2)) or
                          any(abs(values[i]) >= 32095 for i in (4, 5, 6)))
        acc = [(values[i]/16384 - self.settings['acc_offset'][i]) /
               self.settings['acc_scale'][i] for i in range(3)]
        gyro = [values[i]/131 for i in (4, 5, 6)]
        axes, signs = self.settings['body_axes'], self.settings['body_signs']
        return tuple(signs[i]*acc[axes[i]] for i in range(3)) + tuple(
            signs[i]*gyro[axes[i]]-self.bias[i] for i in range(3))

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
