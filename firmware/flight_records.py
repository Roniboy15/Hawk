"""144-Byte-Flugrecords: reine Kodierung, keine Hardware und keine Dateizugriffe.

Koerperzeichen wie config: Roll rechts, Nick Nase runter, Gier Nase links.
Accel in g, Gyro in Grad/s; GPS-Kurs ab Nord ist kein IMU-Gierwinkel.
Fehlende Gleitkommawerte sind NaN, fehlende Pulse 0, unbekannte Alter -1.
Alter 32767 bedeutet >=32767 ms. Flags entscheiden ueber Datenverwendung.
"""
import math
import struct
from io import IOBase

FORMAT = '<IIHBBBBH9f4H3h3H3iIIdd4f2hI2fHBB'
RECORD_BYTES = struct.calcsize(FORMAT)
CSV_MAX_ROW_BYTES = 512  # Auch Extremwerte; Grenzwert wird je Exportzeile geprueft.


class ByteCounter(IOBase):
    """Dateigroesse ohne Datei und ohne grossen JSON-/CSV-Gesamtstring zaehlen."""
    def __init__(self):
        self.size = 0

    def write(self, data):
        self.size += len(data.encode('utf-8')) if isinstance(data, str) else len(data)
        return len(data)

    def ioctl(self, op, arg):
        return 0 if op in (1, 4) else -1


MODES = ('SENSOR', 'WAIT_NEUTRAL', 'MANUAL', 'RX_TIMEOUT', 'MANUAL_FALLBACK', 'STABILIZE')
FAULTS = ('', 'IMU_START', 'IMU_RUNTIME', 'PITCH_RANGE', 'TIMING')
KINDS = ('', 'sample', 'start', 'stop', 'channel_invalid', 'full', 'state')
COLUMNS = ('ms,sequence,segment,kind,mode,fault,valid_bits,status_bits,'
           'roll_deg,pitch_down_deg,yaw_relative_deg,acc_x_g,acc_y_g,acc_z_g,'
           'gyro_roll_dps,gyro_pitch_down_dps,gyro_yaw_left_dps,'
           'rx_roll_us,rx_pitch_us,rx_yaw_us,ch3_us,rx_roll_age_ms,rx_pitch_age_ms,'
           'rx_yaw_age_ms,servo_roll_us,servo_pitch_us,servo_yaw_us,period_us,'
           'work_to_log_us,imu_age_ms,utc_ms,date_ddmmyy,lat_deg,lon_deg,'
           'gps_alt_msl_m,ground_speed_ms,course_true_deg,hdop,gga_age_ms,rmc_age_ms,'
           'pressure_pa,temperature_c,relative_height_m,baro_age_ms,satellites,fix_quality')


def number(value):
    return float('nan') if value is None else value


def age(value):
    return max(-1, min(32767, value))


def encode(buffer, index, ms, segment, kind, control, gps, baro, ch3,
           recording, ready, full):
    """Ein kompletter Record direkt in seinen Block; kein Vollpuffer-Kopieren."""
    block, offset = buffer.slot(index)
    gyro_ok = control.get('gyro_fresh', control['imu_fresh'])
    tilt_ok = control.get('tilt_valid', control['imu_fresh'])
    valid = (int(control['imu_fresh']) | int(bool(gps.get('valid'))) << 1 |
             int(baro['valid']) << 2 | int(bool(gps.get('course_usable'))) << 3 |
             int(bool(gps.get('gga_valid'))) << 4 | int(bool(gps.get('rmc_valid'))) << 5 |
             int(gyro_ok) << 6 | int(tilt_ok) << 7)
    status = (int(recording) | int(control['armed']) << 1 |
              int(control['fresh']) << 2 | int(bool(control['pulses'])) << 3 |
              int(ready) << 4 | int(full) << 5)
    struct.pack_into('<IIHBBBBH', block, offset, ms, index, segment, kind,
                     MODES.index(control['mode']), FAULTS.index(control['fault']), valid, status)
    # Ungueltige IMU niemals als frische alte Lage ausgeben. Alter bleibt sichtbar.
    missing = (float('nan'),)*3
    values = ((tuple(control['angles']) if tilt_ok else missing) +
              (tuple(control['sample'][:3]) if control['imu_fresh'] else missing) +
              (tuple(control['sample'][3:]) if gyro_ok else missing))
    struct.pack_into('<9f', block, offset+16, *values)
    values = (tuple(control['rx'][0]) + (ch3 or 0,) +
              tuple(age(v) for v in control['rx'][1]) +
              tuple(control['pulses'].get(a, 0) for a in ('roll', 'pitch', 'yaw')) +
              (control['period_us'] if control['period_us'] is not None else -1,
               control['work_to_log_us'], control['imu_age_ms']))
    struct.pack_into('<4H3h3H3i', block, offset+52, *values)
    struct.pack_into('<IIdd4f2h', block, offset+84,
                     gps.get('utc_ms', 0xffffffff), int(gps.get('date') or 0),
                     number(gps.get('lat')), number(gps.get('lon')),
                     number(gps.get('altitude_msl_m')), number(gps.get('speed_ms')),
                     number(gps.get('course_deg')), number(gps.get('hdop')),
                     age(gps.get('gga_age_ms', -1)), age(gps.get('rmc_age_ms', -1)))
    struct.pack_into('<I2fHBB', block, offset+128,
                     baro['pressure_pa'] or 0, number(baro['temperature_c']),
                     number(baro['relative_height_m']),
                     65535 if baro['age_ms'] < 0 else min(65534, baro['age_ms']),
                     min(255, gps.get('satellites', 0)), min(255, gps.get('quality', 0)))


def decode(buffer, index):
    block, offset = buffer.slot(index)
    return struct.unpack_from(FORMAT, block, offset)


def csv_row(buffer, index):
    values = list(decode(buffer, index))
    values[3], values[4], values[5] = KINDS[values[3]], MODES[values[4]], FAULTS[values[5]]
    if values[30] == 0xffffffff:
        values[30] = ''
    values[31] = '%06d' % values[31] if values[31] else ''
    if not values[6] & 4:
        values[40] = ''
    if values[43] == 65535:
        values[43] = -1
    def text(index, value):
        if type(value) is float:
            # GPS-Koordinaten behalten8 Nachkommastellen; andere float32-Werte
            # brauchen keine8 Dezimalstellen.6 signifikante Stellen sparen Flash.
            return '' if not math.isfinite(value) else (('%.8f' if index in (32, 33)
                                                        else '%.6g') % value)
        return str(value)
    row = ','.join(text(index, value) for index, value in enumerate(values)) + '\n'
    if len(row) > CSV_MAX_ROW_BYTES:
        raise ValueError('Flug-CSV-Zeile ueberschreitet Platzbudget')
    return row


class GroundStop:
    """Nach Loslassen erst 2-s-Druck akzeptieren; nur bei pausierter Aufnahme."""
    def __init__(self, diff, hold_ms=2000):
        self.diff, self.hold = diff, hold_ms
        self.released = False
        self.since = None

    def update(self, pressed, allowed, now):
        if not pressed:
            self.released, self.since = True, None
        elif not allowed or not self.released:
            self.since = None
        elif self.since is None:
            self.since = now
        elif self.diff(now, self.since) < 0:
            self.since = now
        elif self.diff(now, self.since) >= self.hold:
            return True
        return False
