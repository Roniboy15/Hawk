"""RC-PWM mit RP2040-PIO messen und auf -1..+1 normieren.

Hauptteile: pulse_capture (Hardwaremessung), Receiver.poll(), normalize().
Logik: eigener PIO-Zustandsautomat pro aktivem Kanal; weder I2C noch Python-
Interruptlatenz bestimmt die Pulsmessung. Min/Mitte/Max stammen aus expliziter
RC-Kalibrierung. Asymmetrische Wege werden getrennt normiert. Trimmung wird
als Eingabe sichtbar und nicht heimlich als neue Mitte gelernt.
Timeout erkennt nur fehlende Pulse, NICHT den Funkverlust, wenn der Receiver
alte/FailSafe-Pulse weiterliefert. Dies muss separat am Receiver getestet werden.
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
    def __init__(self, settings, axes, timeout_ms):
        self.channels = {}
        self.timeout = timeout_ms
        try:
            for index, axis in enumerate(axes):
                pin = Pin(settings[axis]['pin'], Pin.IN, Pin.PULL_DOWN)
                sm = rp2.StateMachine(index, pulse_capture, freq=2000000,
                                      in_base=pin, jmp_pin=pin)
                self.channels[axis] = {'sm': sm, 'pulse': None, 'time': None,
                                       'sequence': 0}
                sm.active(1)
        except Exception:
            self.close()
            raise

    def poll(self, now):
        for channel in self.channels.values():
            while channel['sm'].rx_fifo():
                pulse = channel['sm'].get()
                channel['sequence'] += 1
                if 900 <= pulse <= 2100:
                    channel['pulse'], channel['time'] = pulse, now
                else:
                    channel['pulse'], channel['time'] = None, None

    def fresh(self, axis, now):
        stamp = self.channels[axis]['time']
        return stamp is not None and time.ticks_diff(now, stamp) < self.timeout

    def all_fresh(self, now):
        return all(self.fresh(axis, now) for axis in self.channels)

    def close(self):
        for channel in self.channels.values():
            channel['sm'].active(0)
