"""RC-PWM mit RP2040-PIO messen und auf -1..+1 normieren.

Hauptteile: pulse_capture (Hardwaremessung), Receiver.poll(), normalize().
Logik: eigener PIO-Zustandsautomat pro aktivem Kanal; weder I2C noch Python-
Interruptlatenz bestimmt die Pulsmessung. Min/Mitte/Max stammen aus expliziter
RC-Kalibrierung. Asymmetrische Wege werden getrennt normiert. Trimmung wird
als Eingabe sichtbar und nicht heimlich als neue Mitte gelernt.
Timeout erkennt nur fehlende Pulse, NICHT den Funkverlust, wenn der Receiver
alte/FailSafe-Pulse weiterliefert. Dies muss separat am Receiver getestet werden.
FIFO-Worte enthalten keine Zeitstempel: Alter wird konservativ ab dem vorigen
Poll gerechnet. Nach Pollpause/vollem FIFO erst neue Pulse akzeptieren.
"""
import time
from machine import Pin
import rp2


def normalize(pulse, calibration, sign=1, deadband=0.04):
    center = calibration['center']
    span = (calibration['max']-center if pulse >= center
            else center-calibration['min'])
    if span <= 0:
        raise ValueError('RC-Kalibrierung ungueltig')
    value = max(-1.0, min(1.0, (pulse-center)/span))
    if abs(value) <= deadband:
        return 0.0
    # Stetige Kennlinie am Rand der Totzone.
    value = (value-deadband)/(1-deadband) if value > 0 else (value+deadband)/(1-deadband)
    return sign*value


@rp2.asm_pio()
def pulse_capture():
    wrap_target()
    wait(0, pin, 0)
    wait(1, pin, 0)
    mov(x, invert(null))
    label('count')
    jmp(pin, 'high')
    jmp('done')
    label('high')
    jmp(x_dec, 'count')
    label('done')
    mov(isr, invert(x))
    push(noblock)
    wrap()


class Receiver:
    def __init__(self, settings, axes, timeout_ms, max_poll_ms=50):
        self.channels = {}
        self.timeout = timeout_ms
        self.max_poll_ms = max_poll_ms
        self.last_poll = None
        try:
            for index, axis in enumerate(axes):
                pin = Pin(settings[axis]['pin'], Pin.IN, Pin.PULL_DOWN)
                sm = rp2.StateMachine(index, pulse_capture, freq=2000000,
                                      in_base=pin, jmp_pin=pin)
                self.channels[axis] = {'sm': sm, 'pulse': None, 'time': None,
                                       'sequence': 0}
                sm.active(1)
        except BaseException:
            # Aufraeumfehler duerfen die eigentliche Startursache nicht verdecken.
            # Auch Ctrl+C mitten im Start muss bereits aktive PIOs stoppen.
            try:
                self.close()
            except BaseException:
                pass  # Originalfehler erhalten; app meldet Startabbruch als unbestaetigt.
            raise

    def _discard(self, channel):
        channel['pulse'], channel['time'] = None, None
        sm = channel['sm']
        # Stoppen macht das Leeren endlich. restart() allein leert den FIFO
        # nicht; danach verlangt wait(0)/wait(1) eine neue vollstaendige Flanke.
        sm.active(0)
        for _ in range(sm.rx_fifo()):
            sm.get()
        sm.restart()
        sm.active(1)

    def invalidate(self, now):
        """Unbekannt alte Pulse verwerfen; nichts davon darf erneut freigeben."""
        self.last_poll = now
        error = None
        for channel in self.channels.values():
            try:
                self._discard(channel)
            except BaseException as current:
                if error is None:
                    error = current
        if error is not None:
            raise error

    def poll(self, now):
        previous = self.last_poll
        gap = time.ticks_diff(now, previous) if previous is not None else None
        if gap is None or gap < 0 or gap > self.max_poll_ms:
            # Auch der erste Poll kann Pulse aus einer langen Initialisierung
            # enthalten. Keine Verbrauchszeit als vermeintliche Empfangszeit.
            self.invalidate(now)
            return
        self.last_poll = now
        for channel in self.channels.values():
            pending = channel['sm'].rx_fifo()
            if pending >= 4:
                # Nicht verbundener RX-FIFO: 4 Worte. Bei Fuellung kann push(noblock)
                # neuere Pulse verloren haben; die alten Werte sind unbrauchbar.
                self._discard(channel)
                continue
            # Nur den Snapshot lesen: auch bei schnellen Eingangsflanken bleibt
            # dieser Poll begrenzt. Spaetere Worte bleiben fuer den naechsten Poll.
            for _ in range(pending):
                pulse = channel['sm'].get()
                channel['sequence'] += 1
                if 900 <= pulse <= 2100:
                    # Die Capture-Zeit liegt nach dem letzten geleerten Snapshot.
                    # Dessen Zeit ist eine konservative Untergrenze, kein exakter
                    # Hardwarezeitstempel. So verlaengert Lesen den Timeout nicht.
                    channel['pulse'], channel['time'] = pulse, previous
                else:
                    channel['pulse'], channel['time'] = None, None

    def fresh(self, axis, now):
        stamp = self.channels[axis]['time']
        return stamp is not None and 0 <= time.ticks_diff(now, stamp) < self.timeout

    def all_fresh(self, now):
        return all(self.fresh(axis, now) for axis in self.channels)

    def close(self):
        error = None
        for channel in self.channels.values():
            channel['pulse'], channel['time'] = None, None
            try:
                channel['sm'].active(0)
            except BaseException as current:
                if error is None:
                    error = current
        # Alle Kanaele zuerst versuchen, dann den ersten Fehler weiterreichen.
        if error is not None:
            raise error
