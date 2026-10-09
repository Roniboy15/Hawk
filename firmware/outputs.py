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
        except Exception:
            self.close()
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
        for axis, device in self.devices.items():
            device.deinit()
            Pin(self.settings[axis]['pin'], Pin.OUT, value=0)
