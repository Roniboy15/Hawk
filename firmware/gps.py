"""Begrenzter NMEA-Empfang fuer BN-180: GGA/RMC, Pruefsumme und Datenalter.

Koordinaten in Dezimalgrad (+Nord/+Ost), Geschwindigkeit ueber Grund in m/s,
Kurs ueber Grund im Uhrzeigersinn ab Nord, GGA-Hoehe in m ueber MSL.
Kurs ueber Grund ist weder unsere IMU-Gier noch eine Airspeedmessung.
Kein Hardwareimport und keine GPS-Konfigurationsbefehle; UART wird uebergeben.
Grundlage fuer Satzfelder: u-blox 8/M8 Receiver Description, Kapitel 31.
"""
import math


def _number(text, minimum=None, maximum=None):
    if text == '':
        return None
    value = float(text)
    if (not math.isfinite(value) or
            (minimum is not None and value < minimum) or
            (maximum is not None and value > maximum)):
        raise ValueError('NMEA-Wert ausserhalb Bereich')
    return value


def _utc(text):
    if (len(text) < 6 or not text[:6].isdigit() or
            (len(text) > 6 and (text[6] != '.' or not text[7:].isdigit()))):
        raise ValueError('Ungueltige NMEA-UTC-Zeit')
    hour, minute, second = int(text[:2]), int(text[2:4]), int(text[4:6])
    if hour > 23 or minute > 59 or second > 60:
        raise ValueError('Ungueltige NMEA-UTC-Zeit')
    if second == 60 and (hour != 23 or minute != 59):
        raise ValueError('Ungueltige Schaltsekunde')
    fraction = int((text[7:] + '000')[:3]) if len(text) > 6 else 0
    return ((hour * 60 + minute) * 60 + second) * 1000 + fraction


def _coordinate(text, hemisphere, latitude):
    if text == '' and hemisphere == '':
        return None
    digits = 2 if latitude else 3
    if (len(text) < digits + 2 or not text[:digits+2].isdigit() or
            (len(text) > digits+2 and
             (text[digits+2] != '.' or not text[digits+3:].isdigit()))):
        raise ValueError('Ungueltiges NMEA-Koordinatenformat')
    degrees = int(text[:digits])
    minutes = _number(text[digits:], 0)
    limit, positive, negative = (90, 'N', 'S') if latitude else (180, 'E', 'W')
    if (minutes >= 60 or degrees > limit or (degrees == limit and minutes != 0) or
            hemisphere not in (positive, negative)):
        raise ValueError('Ungueltige NMEA-Koordinate')
    result = degrees + minutes / 60
    return -result if hemisphere == negative else result


def checked_fields(line):
    """Prueft genau einen vollstaendigen ASCII-Satz inklusive XOR-Pruefsumme."""
    if isinstance(line, (bytes, bytearray)):
        line = line.decode()  # MicroPython unterstuetzt UTF-8; ASCII wird unten geprueft.
    line = line.rstrip('\r\n')
    if len(line) > 128 or not line.startswith('$') or line.count('*') != 1:
        raise ValueError('Ungueltiger NMEA-Rahmen')
    payload, checksum = line[1:].split('*')
    if len(checksum) != 2 or any(c not in '0123456789abcdefABCDEF' for c in checksum):
        raise ValueError('Ungueltige NMEA-Pruefsumme')
    actual = 0
    for char in payload:
        if not 32 <= ord(char) <= 126:
            raise ValueError('Nicht-ASCII-NMEA-Daten')
        actual ^= ord(char)
    if actual != int(checksum, 16):
        raise ValueError('NMEA-Pruefsumme stimmt nicht')
    fields = payload.split(',')
    if len(fields[0]) != 5 or not fields[0].isalpha():
        raise ValueError('Ungueltige NMEA-Satzkennung')
    return fields


def parse_fields(fields):
    """None fuer andere Satztypen; leere No-Fix-Felder bleiben unbekannt."""
    kind = fields[0][-3:]
    if kind not in ('GGA', 'RMC'):
        return None
    if len(fields) < (15 if kind == 'GGA' else 10):
        raise ValueError('NMEA-Satz unvollstaendig')
    # Manche Receiver liefern vor erster Zeitbestimmung auch leere UTC-Felder.
    utc_ms = _utc(fields[1]) if fields[1] else None
    if kind == 'GGA':
        if not fields[6].isdigit() or not fields[7].isdigit():
            raise ValueError('Ungueltiger GGA-Status')
        quality, satellites = int(fields[6]), int(fields[7])
        if not 0 <= quality <= 8 or not 0 <= satellites <= 99:
            raise ValueError('Ungueltiger GGA-Status')
        lat = _coordinate(fields[2], fields[3], True)
        lon = _coordinate(fields[4], fields[5], False)
        altitude = _number(fields[9])
        if altitude is not None and fields[10] != 'M':
            raise ValueError('GGA-Hoehe braucht Einheit Meter')
        valid = quality in (1, 2, 4, 5)
        record = {'kind': kind, 'utc': fields[1], 'utc_ms': utc_ms,
                  'valid': valid, 'lat': lat, 'lon': lon, 'quality': quality,
                  'satellites': satellites, 'hdop': _number(fields[8], 0),
                  'altitude_msl_m': altitude if valid else None}
    else:
        if fields[2] not in ('A', 'V'):
            raise ValueError('Ungueltiger RMC-Status')
        lat = _coordinate(fields[3], fields[4], True)
        lon = _coordinate(fields[5], fields[6], False)
        speed = _number(fields[7], 0)
        course = _number(fields[8], 0, 360)
        mode = fields[12] if len(fields) > 12 else ''
        # Keine simulierten/manuellen/geschaetzten Positionen als GNSS-Fix ausgeben.
        valid = fields[2] == 'A' and mode in ('', 'A', 'D', 'F', 'R', 'P')
        date = fields[9]
        if date and (len(date) != 6 or not date.isdigit() or
                     not 1 <= int(date[:2]) <= 31 or not 1 <= int(date[2:4]) <= 12):
            raise ValueError('Ungueltiges RMC-Datum')
        record = {'kind': kind, 'utc': fields[1], 'utc_ms': utc_ms,
                  'valid': valid, 'lat': lat, 'lon': lon, 'date': date,
                  'speed_ms': speed * 0.514444444444 if valid and speed is not None else None,
                  'course_deg': course % 360 if valid and course is not None else None}
    if record['valid'] and (lat is None or lon is None or utc_ms is None):
        raise ValueError('Gueltiger Fix ohne Zeit/Position')
    if not record['valid']:
        record['lat'] = record['lon'] = None
    return record


class GPS:
    def __init__(self, uart, ticks_diff, stale_ms=2500, max_read=256, rxbuf=1024,
                 course_min_speed_ms=2.0, max_poll_ms=100):
        if (type(stale_ms) is not int or stale_ms < 1 or
                type(max_read) is not int or not 1 <= max_read <= 1024 or
                type(rxbuf) is not int or not max_read <= rxbuf <= 8192 or
                type(max_poll_ms) is not int or not 1 <= max_poll_ms < stale_ms or
                not math.isfinite(course_min_speed_ms) or course_min_speed_ms < 0):
            raise ValueError('Ungueltige GPS-Empfangseinstellung')
        self.uart, self.diff = uart, ticks_diff
        self.stale_ms, self.max_read, self.rxbuf = stale_ms, max_read, rxbuf
        self.max_poll_ms = max_poll_ms
        self.course_min_speed = course_min_speed_ms
        self.buffer = bytearray(128)
        self.length, self.receiving = 0, False
        self.gga, self.rmc = None, None
        self.gga_ms, self.rmc_ms, self.last_poll = None, None, None
        self.counters = dict((key, 0) for key in
                             ('bytes', 'sentences', 'checksum_errors', 'parse_errors',
                              'ignored', 'overlong', 'resyncs', 'poll_gaps', 'updates',
                              'gga_fix_sentences', 'rmc_fix_sentences', 'max_satellites_used'))
        self.first_sentences = []  # Hoechstens vier Rohsaetze fuer Baud-/No-Fix-Diagnose.

    def _count(self, key, amount=1):
        self.counters[key] = min(1000000000, self.counters[key] + amount)

    def feed(self, data, now_ms):
        """Begrenzter Rahmenpuffer; neue $-Marke synchronisiert nach Stoerung."""
        for byte in data:
            self._count('bytes')
            if byte == 36:
                if self.receiving and self.length:
                    self._count('resyncs')
                self.length, self.receiving = 0, True
            if not self.receiving:
                continue
            if byte == 10:
                self.receiving = False
                try:
                    line = bytes(self.buffer[:self.length]).decode()
                    fields = checked_fields(line)
                except (ValueError, UnicodeError):
                    self._count('checksum_errors')
                    continue
                self._count('sentences')
                if len(self.first_sentences) < 4:
                    self.first_sentences.append(line.rstrip('\r'))
                try:
                    record = parse_fields(fields)
                except (ValueError, IndexError, OverflowError):
                    self._count('parse_errors')
                    continue
                if record is None:
                    self._count('ignored')
                elif record['kind'] == 'GGA':
                    self.gga, self.gga_ms = record, now_ms
                    self._count('updates')
                    # Empfangenen Receiverstatus auch nach Frischeverlust nachweisen.
                    self.counters['max_satellites_used'] = max(
                        self.counters['max_satellites_used'], record['satellites'])
                    if record['valid']:
                        self._count('gga_fix_sentences')
                else:
                    self.rmc, self.rmc_ms = record, now_ms
                    self._count('updates')
                    if record['valid']:
                        self._count('rmc_fix_sentences')
                continue
            if self.length == len(self.buffer):
                self.receiving = False
                self._count('overlong')
                continue
            self.buffer[self.length] = byte
            self.length += 1

    def poll(self, now_ms):
        # UART-Altdaten nach langer Anwendungspause nicht als frischen Fix umdeuten.
        if self.last_poll is not None:
            gap = self.diff(now_ms, self.last_poll)
            if gap < 0 or gap > self.max_poll_ms:
                self.gga = self.rmc = self.gga_ms = self.rmc_ms = None
                self.receiving, self.length = False, 0
                available = self.uart.any()
                if available:
                    # Auch beim Verwerfen nur schon vorhandene Bytes anfordern.
                    self.uart.read(min(available, self.rxbuf))
                self._count('poll_gaps')
                self.last_poll = now_ms
                return
        self.last_poll = now_ms
        available = self.uart.any()
        if available:
            # RP2 erzwingt einen Zeichen-Timeout, selbst bei timeout_char=0.
            # read(256) kann deshalb einen laufenden 9600-Baud-Burst abwarten.
            # any() liefert vorhandene Bytes: nicht auf kuenftige Zeichen warten.
            data = self.uart.read(min(available, self.max_read))
            if data:
                self.feed(data, now_ms)

    def snapshot(self, now_ms):
        def age(stamp):
            value = self.diff(now_ms, stamp) if stamp is not None else -1
            return value if value >= 0 else -1
        gga_age, rmc_age = age(self.gga_ms), age(self.rmc_ms)
        gga_ok = bool(self.gga and self.gga['valid'] and 0 <= gga_age < self.stale_ms)
        rmc_ok = bool(self.rmc and self.rmc['valid'] and 0 <= rmc_age < self.stale_ms)
        # Position erst aus zwei frischen, gueltigen Saetzen derselben UTC-Epoche.
        paired = bool(gga_ok and rmc_ok and self.gga['utc_ms'] == self.rmc['utc_ms'])
        result = {'valid': paired, 'gga_valid': gga_ok, 'rmc_valid': rmc_ok,
                  'gga_age_ms': gga_age, 'rmc_age_ms': rmc_age,
                  'utc': self.rmc['utc'] if self.rmc else '',
                  'date': self.rmc['date'] if self.rmc else '',
                  'lat': self.rmc['lat'] if paired else None,
                  'lon': self.rmc['lon'] if paired else None,
                  'quality': self.gga['quality'] if self.gga else 0,
                  'satellites': self.gga['satellites'] if self.gga else 0,
                  'hdop': self.gga['hdop'] if gga_ok else None,
                  'altitude_msl_m': self.gga['altitude_msl_m'] if gga_ok else None,
                  'speed_ms': self.rmc['speed_ms'] if rmc_ok else None,
                  'course_deg': self.rmc['course_deg'] if rmc_ok else None}
        result['course_usable'] = bool(paired and result['speed_ms'] is not None and
                                        result['speed_ms'] >= self.course_min_speed and
                                        result['course_deg'] is not None)
        return result
