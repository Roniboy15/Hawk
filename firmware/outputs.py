"""Servopulse erzeugen; Signalgrenzen, Vorzeichen und Rudertrim anwenden.

Hauptfunktionen: command() (reine Rechnung), Outputs.write()/neutral()/close().
Logik: Offset in us -> Richtung -> feste Servo-Trimmung -> begrenzter Puls.
Y-Kabel der beiden Querruder bleibt auf einem Rollausgang GP3. Die Mechanik
muss die gegenlaeufigen Ruderbewegungen erzeugen; getrennte Differenzierung
ist mit diesem Y-Kabel nicht moeglich. Ausschlaggrenzen gelten auch mit Trim.
Bei Programmende PWM abschalten; mechanisches Verhalten ohne Pulse pruefen.
"""
from machine import Pin, PWM
from attitude import clamp


def command(offset, settings):
    center, limit = settings['center'], settings['limit']
    value = center+settings['trim']+settings['sign']*offset
    return int(clamp(value, center-limit, center+limit))


class Outputs:
    def __init__(self, settings, axes):
        self.settings = settings
        self.devices = {}
        try:
            for axis in axes:
                cfg = settings[axis]
                self.devices[axis] = PWM(Pin(cfg['pin']), freq=50,
                                        duty_ns=command(0, cfg)*1000)
        except BaseException:
            # Auch ein Stop per Ctrl+C waehrend des Starts muss Teil-PWM stoppen.
            try:
                self.close()
            except BaseException:
                pass  # Startursache erhalten; app verbietet dann den Logexport.
            raise

    def write(self, offsets):
        pulses = {}
        for axis, device in self.devices.items():
            pulse = command(offsets.get(axis, 0), self.settings[axis])
            device.duty_ns(pulse*1000)
            pulses[axis] = pulse
        return pulses

    def neutral(self):
        return self.write({})

    def close(self):
        error = None
        for axis, device in self.devices.items():
            # Jede Massnahme und jede Achse versuchen, auch wenn eine scheitert.
            # 0 Duty und GPIO-low sind weitere Abschaltversuche, kein HW-Bypass.
            try:
                device.duty_ns(0)
            except BaseException as current:
                if error is None:
                    error = current
            try:
                device.deinit()
            except BaseException as current:
                if error is None:
                    error = current
            try:
                Pin(self.settings[axis]['pin'], Pin.OUT, value=0)
            except BaseException as current:
                if error is None:
                    error = current
        if error is not None:
            raise error
