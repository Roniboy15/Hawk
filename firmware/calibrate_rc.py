"""RC-Min/Mitte/Max am Boden erfassen; keine automatische Mittenwanderung.

Hauptfunktionen collect() sammelt nur neue Pulse; run() fuehrt pro aktivem
Kanal durch Mitte und Endpunkte. Sender normal konfigurieren, Trimmung fuer
dieses Projekt mittig. Dieser Segler hat kein Gas. Keine Servo-PWM wird aktiviert.
Gespeicherte Werte gelten fuer diese Senderkonfiguration. Spätere
Sendertrimmung verschiebt weiterhin das Kommando, nicht die gespeicherte Mitte.
"""
import time
import config as cfg
from receiver import Receiver
from calibration import load, save, check_channel


def collect(receiver, axis, duration_ms):
    start = time.ticks_ms()
    previous = receiver.channels[axis]['sequence']
    pulses = []
    while time.ticks_diff(time.ticks_ms(), start) < duration_ms:
        now = time.ticks_ms()
        receiver.poll(now)
        channel = receiver.channels[axis]
        if channel['sequence'] != previous:
            previous = channel['sequence']
            if receiver.fresh(axis, now):
                pulses.append(channel['pulse'])
        time.sleep_ms(5)
    if len(pulses) < 30:
        raise RuntimeError('Zu wenig RC-Pulse fuer '+axis)
    return pulses


def run():
    data = load(cfg.CALIBRATION_FILE)
    receiver = Receiver(cfg.RECEIVER, cfg.ACTIVE_AXES, cfg.RX_TIMEOUT_MS,
                        max_poll_ms=(cfg.MAX_LOOP_US+999)//1000)
    try:
        for axis in cfg.ACTIVE_AXES:
            input(axis+': Knueppel mittig loslassen, dann Enter: ')
            center_values = collect(receiver, axis, 2000)
            if max(center_values)-min(center_values) > 20:
                raise RuntimeError('Neutralwert schwankt: Verkabelung/Sender pruefen')
            center = int(sum(center_values)/len(center_values)+0.5)
            input(axis+': Nach Enter 8 s beide Endanschlaege bewegen: ')
            ends = collect(receiver, axis, 8000)
            ends.sort()
            # Kleine Quantile vermindern Einfluss einzelner Ausreisser.
            edge = max(1, len(ends)//50)
            channel = {'min': ends[edge], 'center': center, 'max': ends[-edge-1]}
            check_channel(channel)
            data['rc'][axis] = channel
            print(axis, channel)
        save(cfg.CALIBRATION_FILE, data)
        print('RC-Kalibrierung gespeichert. Sendertrimmung jetzt nicht veraendern.')
    finally:
        receiver.close()


if __name__ == '__main__':
    run()
