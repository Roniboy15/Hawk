"""MicroPython-Startdatei; entscheidet nur ueber automatischen Start.

Hauptlogik: AUTO_START ist standardmaessig False. main.py startet dann
keinen Regler und erzeugt selbst keine Servo-PWM. Das garantiert keine
ruhenden Ruder bei bereits versorgten Servos: fehlende Pulse sind kein
Neutralbefehl, und elektrische Start-/Versorgungsuebergaenge bleiben moeglich.
Zum kontrollierten Test start_test.py in Thonny ausfuehren. Erst nach
Bodentests kann AUTO_START=True gesetzt werden; das macht keine Flugfreigabe.
"""
import config

if config.AUTO_START:
    from app import run
    run()
else:
    print('Kein Autostart. Fuer Bodenversuch start_test.py ausfuehren.')
