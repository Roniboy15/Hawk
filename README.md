# Segelflug-Controller — Version 0.2.0, Bodenversuch

Modulare MicroPython-Firmware fuer RP2040-Zero und das bereits getestete
MPU-kompatible SY-104-Modul (WHO_AM_I 0x72). Konventionelles Flugzeug mit
getrenntem Hoehen-/Seitenruder; beide Querruder ueber ein Y-Kabel auf GP3.
Das Projekt bereitet die Architektur fuer autonomes Thermikkreisen vor.
Diese Version implementiert Sensoranzeige, manuellen Durchgang, Roll-/Nick-
Winkelregelung und optional Gier-Drehratenregelung, aber keine Flugnavigation.

**Zuerst nur am Boden, ohne laufenden Motor/Propeller testen.** Die bisher
funktionierende Firmware auf dem Mac sichern. Die neue Regelung ist eine
Weiterentwicklung, kein unveraenderter Ersatz: ihre Parameter haben andere
Bedeutungen und wurden bisher nur am Host simuliert. PIO, I2C, Timing und
Ruderwirkungen muessen auf deinem Board neu geprueft werden.

## Start hier

1. [THONNY.md](docs/THONNY.md): Dateien hochladen, kalibrieren, Roll erneut testen,
   Nick hinzufuegen, anschliessend Gier.
2. [GIT.md](docs/GIT.md): Repo auf dem Mac einrichten und kleine Aenderungen sichern.
3. [ARCHITEKTUR.md](docs/ARCHITEKTUR.md): Module, Trimmung, Fehler und Thermik-Roadmap.
4. [VALIDIERUNG.md](docs/VALIDIERUNG.md): getestete und noch offene Eigenschaften.

## Dateien

| Datei in firmware/ | Aufgabe / Einstieg |
| --- | --- |
| config.py | Einziger Ort fuer Pins, Achsen, Grenzwerte und Reglerparameter |
| main.py | Autostart; standardmaessig deaktiviert |
| start_test.py | In Thonny ausfuehren, ruft app.run() auf |
| app.py | Regelschleife und Zustandswechsel |
| calibration.py | JSON-Einstellungen pruefen und speichern |
| calibrate_rc.py | Explizite RC-Min/Mitte/Max-Erfassung |
| calibrate_level.py | Geometrische Roll-/Nickreferenz erfassen |
| imu.py | Sensorregister, Achsenkorrektur, Gyro-Ruhekalibrierung |
| attitude.py | Quaternionfilter, Lage und Koerperrahmen-Winkelfehler |
| receiver.py | Drei moegliche RC-PWM-Eingaenge mit PIO |
| control.py | Regler und einmalige Neutralfreigabe |
| outputs.py | Servopulse, Vorzeichen, Trim und Grenzwerte |
| logger.py | Begrenzter RAM-Ring, CSV-Export nach dem Stoppen |

Alle Python-Dateien enthalten am Anfang Aufgabe, Hauptfunktionen und Logik.
Tests und Dokumentation gehoeren auf den Mac, nicht auf den MCU.

## Hardwareplan

GP bedeutet GPIO-Nummer, niemals physische Pinposition.

| Funktion | Anschluss | Startzustand |
| --- | --- | --- |
| MPU SDA / SCL | GP4 / GP5 | Aktiv |
| MPU VCC / GND | MCU 3V3 / gemeinsame Masse | Aktiv |
| CH1 Querruder-Signal | GP2 | Aktiv, Pegel muss 3,3-V-kompatibel sein |
| Querruder Y-Kabel-Signal | GP3 | Ein gemeinsamer Ausgang |
| CH2 Hoehenruder-Signal | GP8 | Erst nach Anschluss pitch aktivieren |
| Hoehenruder-Servo-Signal | GP6 | Erst nach Anschluss pitch aktivieren |
| CH4 Seitenruder-Signal | GP9 | Optional |
| Seitenruder-Servo-Signal | GP7 | Optional |
| CH3 Gas | Bleibt ausserhalb dieses MCU-Programms | Kein MCU-Motorausgang |
| Receiver/Servo Plus | BEC 5 V | Ausreichende Strombelastbarkeit pruefen |
| Alle GND | Gemeinsame Minusleiste | Auch MCU-GND anschliessen |

MCU im USB-Test ueber USB versorgen, BEC-Plus nicht an dessen 5-V-Pin.
Bei allen zusaetzlichen RC-Eingaengen Signalpegel pruefen/anpassen. Die
Receiver-Versorgungsspannung sagt nicht die Spannung der PWM-Pulse aus.
Servos nicht aus dem 3V3-Pin des MCU speisen. Motorversorgung beim Umstecken aus.

Die beiden Querruder muessen mechanisch gegenlaeufig funktionieren. Ein
Y-Kabel liefert beiden Servos denselben Puls und erlaubt keine getrennte
Software-Differenzierung. Die vorhandene funktionierende Mechanik beibehalten.

## Noch keine Flugfreigabe

- Die Kennung 0x72 und Registerantworten beweisen nicht den exakten Chiptyp.
- Kein unabhaengiger Hardware-Bypass, kein getesteter Watchdog/Redundanzpfad.
- Kein Mode-Kanal: bei vier genutzten RC-Kanaelen fehlt ein dedizierter
  Umschaltkanal. START_MODE ist eine Boden-Testeinstellung; die Moduswahl
  ueber Sender/Hardware muss vor einem Flug separat geplant werden.
- Ein Receiver, der bei Funkverlust alte Pulse liefert, wird NICHT durch
  den Pulse-Timeout erkannt. Antenne, Reichweite und Receiver-Failsafe testen.
- Nickwinkelhaltung bedeutet weder Hoehenhaltung noch Schutz vor Stall.
- Quaternionfilter ist kein Navigations-EKF; Beschleunigungen im Kurvenflug
  koennen seine Gravitationskorrektur beeinflussen.
- MANUAL_FALLBACK bedeutet Software-Ersatz bei laufendem MCU und gueltigem RX,
  keinen sicheren Weiterflug bei CPU-Haenger, Stromausfall oder blockiertem I2C.

## Tests auf dem Mac

Keine Zusatzpakete erforderlich (Python 3):

```bash
python3 -m unittest discover -s tests -v
```

## Quellen / Designbezug

Eigenstaendige Python-Implementierung, kein kopierter oder portierter ArduPilot-Code.
Die Trennung von RC-Kalibrierung, Servotrim, Lageschaetzung und Regler orientiert
sich an etablierten Autopilot-Architekturen:

- https://ardupilot.org/plane/docs/new-roll-and-pitch-tuning.html
- https://ardupilot.org/plane/docs/rc-throw-trim.html
- https://ardupilot.org/plane/docs/soaring-4_1.html
- https://docs.micropython.org/en/latest/library/rp2.html
- https://docs.micropython.org/en/latest/library/rp2.StateMachine.html
- https://www.waveshare.com/wiki/RP2040-Zero
