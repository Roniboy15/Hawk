# Segelflug-Controller — Version 0.2.2, Bodenversuch

Modulare MicroPython-Firmware fuer RP2040-Zero und das bereits getestete
MPU-kompatible SY-104-Modul (WHO_AM_I 0x72). Konventionelles Flugzeug mit
getrenntem Hoehen-/Seitenruder; beide Querruder ueber ein Y-Kabel auf GP3.
Das Projekt bereitet die Architektur fuer autonomes Thermikkreisen vor.
Diese Version implementiert Sensoranzeige, manuellen Durchgang, Roll-/Nick-
Winkelregelung und optional Gier-Drehratenregelung, aber keine Flugnavigation.

**Nur beaufsichtigte Tischtests; noch keine Flugfreigabe.** Der Segler hat
kein Triebwerk und kein Gas. Laut Besitzer sind alle Servos montiert und an
den vorgesehenen Kanaelen angeschlossen; Signalpegel und Ruderwirkungen
muessen trotzdem gemessen/geprueft werden. Eine gemeinsame Stromleiste ist geplant.
Die bisher
funktionierende Firmware auf dem Mac sichern. Der grundlegende Rolltest wurde
vom Besitzer bestaetigt; weitere Achsen, elektrische Grenzen und Worst-Case-Timing
sind noch zu pruefen. Keine Flugabstimmung aus diesem Tischtest ableiten.

## Start hier

1. [THONNY.md](docs/THONNY.md): Dateien hochladen, kalibrieren, Roll erneut testen,
   Nick hinzufuegen, anschliessend Gier.
2. [GIT.md](docs/GIT.md): Repo auf dem Mac einrichten und kleine Aenderungen sichern.
3. [ARCHITEKTUR.md](docs/ARCHITEKTUR.md): Module, Trimmung, Fehler und Thermik-Roadmap.
4. [VALIDIERUNG.md](docs/VALIDIERUNG.md): getestete und noch offene Eigenschaften.
5. [ROLL_TISCHTEST.md](docs/ROLL_TISCHTEST.md): grundlegender Rolltest vom Besitzer bestanden.
6. [PITCH_YAW_TISCHTEST.md](docs/PITCH_YAW_TISCHTEST.md): naechste Schritte,
   Signalpfad vom Receiver zum MCU umstellen, dann je Achse SENSOR/MANUAL/STABILIZE.
7. [VERSORGUNG_WARNHINWEISE.md](docs/VERSORGUNG_WARNHINWEISE.md): beste Diagnose
   zum Versorgungsereignis und Warnhinweise fuer BEC 5 V @ 3 A / vier Servos.

v0.2.1 verwirft RC-Puffer bei zu langer Pollpause/vollem FIFO, bewertet Pulsalter
konservativ und verhindert stabilisierte Kommandos nach einer erkannten
Deadline-Ueberschreitung. Timingfehler verlangen neue Neutralfreigabe vor dem
manuellen Ersatz. Parameterpruefung und Abschaltversuche sind erweitert.
Das ist Hostvalidierung, keine bestaetigte Hardwarequalifikation.

v0.2.2 startet SENSOR mit Roll+Nick; es erzeugt keine MCU-Servopulse.
DIRECTION_CHECKED_AXES blockiert STABILIZE fuer ungepruefte neue Achsen.
Die Koerperkonvention bleibt +Roll rechts, +Nick Nase runter, +Gier Nase links;
pitch_down zeigt daher negative Werte beim Nase-anheben. Kalibrierschema 1
bleibt erhalten; calibrate_rc.run(('pitch',)) erfasst optional nur den neuen Kanal.
Startphasen/Tickzeiten und Gyro-/Gier-Sollrate helfen bei Diagnose; CSV ist erweitert.

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
| CH2 Hoehenruder-Signal | GP8 | SENSOR-Profil vorbereitet; Signalpfad noch umstellen |
| Hoehenruder-Servo-Signal | GP6 | Laut Besitzer bisher direkt am Receiver |
| CH4 Seitenruder-Signal | GP9 | Nach Nick-Test hinzufuegen |
| Seitenruder-Servo-Signal | GP7 | Laut Besitzer bisher direkt am Receiver |
| Gas/Triebwerk | Nicht vorhanden | Keine Throttle-Funktion |
| Receiver/Servo Plus | BEC 5 V | Ausreichende Strombelastbarkeit pruefen |
| Alle GND | Gemeinsame Minusleiste | Auch MCU-GND anschliessen |

MCU im USB-Test ueber USB versorgen, BEC-Plus nicht an dessen 5-V-Pin.
Bei allen zusaetzlichen RC-Eingaengen Signalpegel pruefen/anpassen. Die
Receiver-Versorgungsspannung sagt nicht die Spannung der PWM-Pulse aus.
Servos nicht aus dem 3V3-Pin des MCU speisen. Versorgung beim Umstecken trennen.

Die beiden Querruder muessen mechanisch gegenlaeufig funktionieren. Ein
Y-Kabel liefert beiden Servos denselben Puls und erlaubt keine getrennte
Software-Differenzierung. Die vorhandene funktionierende Mechanik beibehalten.

## Noch keine Flugfreigabe

- Die Kennung 0x72 und Registerantworten beweisen nicht den exakten Chiptyp.
- Kein unabhaengiger Hardware-Bypass, kein getesteter Watchdog/Redundanzpfad.
- Kein implementierter Mode-Kanal. Da kein Gas vorhanden ist, verfuegbare
  Sender-/Receiverkanaele neu pruefen; keinen freien Kanal ungeprueft annehmen.
  START_MODE ist eine Boden-Testeinstellung; Moduswahl und unabhaengigen
  Hardware-Bypass vor einem Flug separat planen.
- Ein Receiver, der bei Funkverlust alte Pulse liefert, wird NICHT durch
  den Pulse-Timeout erkannt. Antenne, Reichweite und Receiver-Failsafe testen.
- Nickwinkelhaltung bedeutet weder Hoehenhaltung noch Schutz vor Stall.
- Quaternionfilter ist kein Navigations-EKF; Beschleunigungen im Kurvenflug
  koennen seine Gravitationskorrektur beeinflussen.
- MANUAL_FALLBACK bedeutet Software-Ersatz bei laufendem MCU und gueltigem RX,
  keinen sicheren Weiterflug bei CPU-Haenger, Stromausfall oder blockiertem I2C.
- Nick-/Gier-Konvention ist explizit, physische Servo-/Senderzeichen sind noch
  zu pruefen. DIRECTION_CHECKED_AXES erst nach SENSOR/MANUAL-Checks erweitern.

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
