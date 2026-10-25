"""Kompakte MANUAL-Reaktion: 20 Hz im RAM, CSV erst nach Hardwarestop.

Winkel als 0.01 Grad, Gyro weiter als float in Grad/s. Zeitstempel ist der
Logger-Eintritt nach PWM, kein gemessener Servo-/Sensor-Capture-Zeitpunkt.
Segmente stehen mit denselben ms-Zeitmarken im vollstaendigen 1-Hz-Log.
"""
import math
import struct
import config as cfg
from flight_records import MODES, FAULTS

FORMAT = '<I2h3f6HHBB'
RECORD_BYTES = struct.calcsize(FORMAT)  # 36 statt 144 Byte je schneller Zeile.
COLUMNS = ('ms,sequence,roll_deg,pitch_down_deg,gyro_roll_dps,'
           'gyro_pitch_down_dps,gyro_yaw_left_dps,rx_roll_us,rx_pitch_us,'
           'rx_yaw_us,servo_roll_us,servo_pitch_us,servo_yaw_us,period_us,'
           'mode,fault,status_bits')
NAN = float('nan')


class ResponseLog:
    def __init__(self, buffer):
        s = cfg.RESPONSE_LOGGER
        if (buffer.record_bytes != RECORD_BYTES or s['record_bytes'] != RECORD_BYTES or
                buffer.capacity != s['capacity'] or s['sample_ms'] != 50):
            raise ValueError('Ungeprueftes 20-Hz-Format/Puffer/Intervall')
        self.buffer = buffer
        self.count = self.missed = self.intervals = self.interval_sum = 0
        self.interval_min = self.interval_max = None
        self.segment = self.next_ms = self.last_ms = None

    def sample(self, ms, segment, control):
        if segment != self.segment:
            self.segment, self.next_ms, self.last_ms = segment, ms, None
        late = ms-self.next_ms
        if late < 0 or self.count == self.buffer.capacity:
            return
        # Auf dem 50-ms-Raster bleiben; verpasste Termine zaehlen, niemals
        # mehrere identische Messwerte zum scheinbaren Nachholen speichern.
        self.missed += late//50
        self.next_ms += (late//50+1)*50
        angles, sample, rx = control['angles'], control['sample'], control['rx'][0]
        pulses, valid = control['pulses'], control['imu_fresh']
        period = control['period_us']
        status = (int(valid) | int(control['armed']) << 1 |
                  int(control['fresh']) << 2 | int(bool(pulses)) << 3)
        block, offset = self.buffer.slot(self.count)
        struct.pack_into(FORMAT, block, offset, ms,
                         round(angles[0]*100) if valid else 32767,
                         round(angles[1]*100) if valid else 32767,
                         sample[3] if valid else NAN, sample[4] if valid else NAN,
                         sample[5] if valid else NAN, rx[0], rx[1], rx[2],
                         pulses.get('roll', 0), pulses.get('pitch', 0), pulses.get('yaw', 0),
                         period if period is not None and 0 <= period < 65535 else 65535,
                         MODES.index(control['mode']) | FAULTS.index(control['fault']) << 4,
                         status)
        self.count += 1
        if self.last_ms is not None:
            gap = ms-self.last_ms
            self.intervals += 1
            self.interval_sum += gap
            self.interval_min = gap if self.interval_min is None else min(self.interval_min, gap)
            self.interval_max = gap if self.interval_max is None else max(self.interval_max, gap)
        self.last_ms = ms

    def report(self, filename):
        return {'csv_file': filename, 'samples': self.count, 'target_hz': 20,
                'capacity': self.buffer.capacity, 'record_bytes': RECORD_BYTES,
                'allocated_bytes': self.buffer.payload_bytes, 'record_format': FORMAT,
                'missed_samples': self.missed, 'interval_min_ms': self.interval_min,
                'interval_max_ms': self.interval_max,
                'interval_mean_ms': self.interval_sum/self.intervals if self.intervals else None,
                'status_bit_names': ['imu', 'rc_armed', 'control_rx_fresh', 'pwm_present']}

    def export(self, filename):
        # Nur FlightSession.export() nach bestaetigtem Hardwarestop ruft dies auf.
        with open(filename, 'w') as file:
            file.write(COLUMNS+'\n')
            for index in range(self.count):
                block, offset = self.buffer.slot(index)
                row = list(struct.unpack_from(FORMAT, block, offset))
                for axis in (1, 2):
                    row[axis] = row[axis]/100 if row[axis] != 32767 else NAN
                if row[12] == 65535:
                    row[12] = -1
                packed = row[13]
                row[13:14] = [MODES[packed & 15], FAULTS[packed >> 4]]
                row.insert(1, index)
                file.write(','.join('' if type(v) is float and not math.isfinite(v)
                                    else str(v) for v in row)+'\n')
