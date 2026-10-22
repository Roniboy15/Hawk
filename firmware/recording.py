"""Reine CH3-Schaltlogik: MANUAL bleibt gleich, nur Aufnahme an/aus.

RecordingSwitch benoetigt spaeter gemessene Low-/High-Schwellen. Kein Hardware-
oder Dateizugriff; flight_logger nutzt sie optional in app.run(). Erst stabil unten,
dann stabil oben startet. Zwischenstellung behaelt den Aufnahmezustand.
Kanalverlust beendet nur Aufnahme und verlangt erneut unten->oben.
"""


class RecordingSwitch:
    def __init__(self, low_us, high_us, hold_ms, ticks_diff, sign=1):
        if (type(low_us) is not int or type(high_us) is not int or
                not 900 <= low_us < high_us <= 2100 or
                type(hold_ms) is not int or not 1 <= hold_ms <= 2000 or
                type(sign) is not int or sign not in (-1, 1)):
            raise ValueError('Ungueltige Aufnahmeschwellen/Haltezeit')
        self.low, self.high, self.hold = low_us, high_us, hold_ms
        self.diff = ticks_diff
        self.sign = sign  # Physischer oberer Anschlag kann auch kleinere Pulse liefern.
        self.recording = self.low_seen = False
        self.candidate = self.since = None

    def update(self, pulse_us, fresh, now_ms):
        """Liefert (Aufnahmezustand, Ereignis oder None), nie einen Servobefehl."""
        if (not fresh or type(pulse_us) is not int or not 900 <= pulse_us <= 2100):
            event = 'channel_invalid' if self.recording else None
            self.recording = self.low_seen = False
            self.candidate = self.since = None
            return False, event
        wanted = False if pulse_us <= self.low else True if pulse_us >= self.high else None
        if wanted is None:
            self.candidate = self.since = None
            return self.recording, None
        if self.sign == -1:
            wanted = not wanted
        if self.candidate is None or wanted != self.candidate:
            self.candidate, self.since = wanted, now_ms
            return self.recording, None
        age = self.diff(now_ms, self.since)
        if age < 0:
            self.since = now_ms
            return self.recording, None
        if age < self.hold:
            return self.recording, None
        if not wanted:
            self.low_seen = True
            if self.recording:
                self.recording = False
                return False, 'stop'
        elif self.low_seen and not self.recording:
            self.recording = True
            return True, 'start'
        return self.recording, None
