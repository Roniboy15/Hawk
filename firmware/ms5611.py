"""MS5611: PROM/CRC, Temperaturkompensation und zeitgesteuerte I2C-Wandlungen.

MS5611 und compensate() liefern Druck in Pa und Temperatur in Grad C.
poll() wartet nicht auf ADC-Wandlungen: D2/D1 laufen zwischen Aufrufen.
Nur beim expliziten Konstruktoraufruf wird nach Reset einmal 3 ms gewartet.
Grundlage: TE MS5611-01BA03 Datenblatt, AN520 nur fuer CRC, NICHT MS5607-Formeln.
Keine Hardwareimporte, keine Servos, kein automatischer Start.
"""
import math


def crc4(prom):
    """CRC-4 ueber acht PROM-Worte, ohne die Eingabeliste zu veraendern."""
    if len(prom) != 8 or any(type(v) is not int or not 0 <= v <= 65535 for v in prom):
        raise ValueError('PROM braucht acht 16-Bit-Worte')
    remainder = 0
    for index, word in enumerate(prom):
        # AN520: ganzes unteres Byte von Wort 7 fuer die Rechnung auf 0 setzen.
        if index == 7:
            word &= 0xff00
        for byte in (word >> 8, word & 255):
            remainder ^= byte
            for _ in range(8):
                remainder = ((remainder << 1) ^ (0x3000 if remainder & 0x8000 else 0)) & 0xffff
    return (remainder >> 12) & 15


def validate_prom(prom):
    expected = crc4(prom)
    if all(v == 0 for v in prom[1:7]) or all(v == 65535 for v in prom[1:7]):
        raise ValueError('PROM leer/ungueltig')
    if expected != prom[7] & 15:
        raise ValueError('MS5611 PROM-CRC stimmt nicht')


def compensate(prom, d1, d2):
    """MS5611-Formeln mit Integer-Zwischenwerten; zweite Ordnung unter 20 C."""
    if any(type(v) is not int or not 0 < v < 0xffffff for v in (d1, d2)):
        raise ValueError('Ungueltiger ADC-Wert')
    if len(prom) != 8:
        raise ValueError('Ungueltige Kalibrierkoeffizienten')
    dt = d2 - (prom[5] << 8)
    temperature = 2000 + ((dt * prom[6]) >> 23)
    offset = (prom[2] << 16) + ((prom[4] * dt) >> 7)
    sensitivity = (prom[1] << 15) + ((prom[3] * dt) >> 8)
    if temperature < 2000:
        squared = (temperature - 2000) ** 2
        offset2 = (5 * squared) >> 1
        sensitivity2 = (5 * squared) >> 2
        if temperature < -1500:
            cold = (temperature + 1500) ** 2
            offset2 += 7 * cold
            sensitivity2 += (11 * cold) >> 1
        temperature -= (dt * dt) >> 31
        offset -= offset2
        sensitivity -= sensitivity2
    pressure_pa = (((d1 * sensitivity) >> 21) - offset) >> 15
    if not 1000 <= pressure_pa <= 120000 or not -4000 <= temperature <= 8500:
        raise ValueError('MS5611 ausserhalb spezifiziertem Messbereich')
    return pressure_pa, temperature / 100


def relative_altitude(pressure_pa, reference_pa):
    """ISA-Naeherung relativ zum Startdruck, keine absolute Hoehe/AGL."""
    for value in (pressure_pa, reference_pa):
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError('Druck muss positiv und endlich sein')
    return 44330.0 * (1.0 - (pressure_pa / reference_pa) ** (1.0 / 5.255))


class MS5611:
    def __init__(self, bus, address=None, sample_ms=100, sleep_ms=None, ticks_diff=None,
                 ticks_ms=None):
        if type(sample_ms) is not int or sample_ms < 20:
            raise ValueError('MS5611 braucht mindestens 20 ms pro D2/D1-Paar')
        if address is not None and address not in (0x76, 0x77):
            raise ValueError('MS5611-Adresse muss 0x76/0x77 sein')
        if sleep_ms is None or ticks_diff is None or ticks_ms is None:
            import time
            sleep_ms = sleep_ms or time.sleep_ms
            ticks_diff = ticks_diff or time.ticks_diff
            ticks_ms = ticks_ms or time.ticks_ms
        if address is None:
            found = [a for a in bus.scan() if a in (0x76, 0x77)]
            if len(found) != 1:
                raise ValueError('Genau einen Sensor bei 0x76/0x77 erwartet; Adresse sonst explizit setzen')
            address = found[0]
        self.bus, self.address = bus, address
        self.diff, self.sample_ms = ticks_diff, sample_ms
        self.now = ticks_ms
        self._command(0x1e)
        sleep_ms(3)  # Datenblatt: PROM-Neuladen dauert 2.8 ms.
        self.prom = [self._read(0xa0 + i * 2, 2) for i in range(8)]
        validate_prom(self.prom)
        self.phase = 'idle'
        self.cycle_ms = None
        self.conversion_ms = None
        self.d2 = None
        self.samples = 0

    def _command(self, command):
        if self.bus.writeto(self.address, bytes([command])) != 1:
            raise OSError('MS5611: Befehl nicht bestaetigt')

    def _read(self, command, length):
        self._command(command)
        data = self.bus.readfrom(self.address, length)
        if data is None or len(data) != length:
            raise OSError('MS5611: unvollstaendige Antwort')
        value = 0
        for byte in data:
            value = (value << 8) | byte
        return value

    def poll(self, now_ms):
        """None bis ein neues D2/D1-Paar vorliegt; sonst (Pa, Grad C, D1, D2)."""
        if self.phase == 'idle':
            if self.cycle_ms is not None:
                elapsed = self.diff(now_ms, self.cycle_ms)
                if elapsed < 0:
                    raise ValueError('MS5611: ungueltige Tick-Differenz')
                if elapsed < self.sample_ms:
                    return None
            self._command(0x58)
            self.cycle_ms = now_ms
            # Erst NACH Rueckkehr des Busbefehls die volle Wandlungszeit abwarten.
            self.conversion_ms = self.now()
            self.phase = 'temperature'
            return None
        elapsed = self.diff(now_ms, self.conversion_ms)
        if elapsed < 0:
            raise ValueError('MS5611: ungueltige Tick-Differenz')
        if elapsed < 10:
            return None  # OSR4096: bis 9.04 ms, nicht nur typische 8.22 ms.
        value = self._read(0x00, 3)
        if not 0 < value < 0xffffff:
            raise ValueError('MS5611: ADC leer/ungueltig')
        if self.phase == 'temperature':
            self.d2 = value
            self._command(0x48)
            self.conversion_ms, self.phase = self.now(), 'pressure'
            return None
        pressure, temperature = compensate(self.prom, value, self.d2)
        self.phase = 'idle'
        self.samples += 1
        return pressure, temperature, value, self.d2
