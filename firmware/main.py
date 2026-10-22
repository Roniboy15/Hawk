"""MicroPython-Startdatei; entscheidet nur ueber automatischen Start.

Hauptlogik: AUTO_START=False und LOGGER_BOOT_MODE=None starten keinen Regler.
Optionaler Logger-Bordstart wartet vor Sensor-/RC-/PWM-Start auf BOOT.
Keine Servo-PWM wird von main.py selbst erzeugt. Das garantiert keine
ruhenden Ruder bei bereits versorgten Servos: fehlende Pulse sind kein
Neutralbefehl, und elektrische Start-/Versorgungsuebergaenge bleiben moeglich.
Zum kontrollierten Test start_test.py in Thonny ausfuehren. Erst nach
Bodentests kann AUTO_START=True gesetzt werden; das macht keine Flugfreigabe.
"""
import config

if config.LOGGER_BOOT_MODE is not None:
    if config.AUTO_START:
        raise ValueError('Logger-Bordstart verlangt AUTO_START=False')
    from flight_start import run
    run(config.LOGGER_BOOT_MODE, wait_for_button=True)
elif config.AUTO_START:
    from app import run
    run()
else:
    print('Kein Autostart. Fuer Bodenversuch start_test.py ausfuehren.')
