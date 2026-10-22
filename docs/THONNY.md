# Thonny: Sicherung, Upload, Kalibrierung und Achsentests

**Neu auf codex/manual-flight-logger:** L3 0.1.4 bestanden. Jetzt Logger 0.1.0
gemeinsam im SENSOR-Profil pruefen: [FLUGLOGGER_TEST.md](FLUGLOGGER_TEST.md).
Alle Pythondateien aktualisieren, calibration.json erhalten, Soft-Reboot.
Danach nur `import flight_start` und `flight_start.run('sensor')`.
Servo-Versorgungen aus, Empfaenger fuer CH3 separat versorgen, Sensoren normal
versorgen. Zweimal CH3 oben/unten, dann unten und BOOT 2 s halten. Beide
Speichermeldungen/Tuerkis abwarten, flight_*.csv/.json nach
docs/testdaten/fluglogger/F1_sensor/ sichern. Kein neuer L3, keine neue Kalibrierung.
Der spaetere explizite MANUAL-Test bleibt eigener Schritt. Autostart bleibt aus;
main.py startet bei AUTO_START=True weiterhin den alten Controller, keinen Logger.

**F1 inzwischen ausgewertet:** Bedienung/Export funktionieren, es gibt aber
neun >50-ms-Zeitabstaende und TIMING; GPS am Fenster ohne Fix. Vor weiterem
Test gezielte Timingdiagnose vorbereiten, noch nicht zu F2 wechseln.
[Befund und Bedeutung der Startmeldung](testdaten/fluglogger/F1_sensor/AUSWERTUNG.md).

**Aktueller Schritt:** [GY-63/BN-180-Sensortests](SENSOREN_TEST.md) auf
codex/gps-baro-bringup. Dafuer die dort genannten sechs Module hochladen,
vorhandene calibration.json erhalten, AUTO_START=False. BEC/Receiver/Servos
bleiben aus; nur MCU/Sensoren per USB. Der Sensorstarter erzeugt keine
Neutralpulse und verhindert keine Bewegung anderweitig versorgter Servos.
Der erste GY-63-Messlauf ist ausgewertet; S1 mit Log und bestaetigter
Anhebereaktion funktional bestanden. GPS/S2 ist mit gps_2 samt Konsolenauszug
ebenfalls funktional bestanden; [Auswertung](testdaten/gps_tests/AUSWERTUNG_GPS_2.md).
S3 ist ebenfalls funktional bestanden, aber sein JSON meldet noch 0.1.0 und
den alten 200-Zeilen-Ring: [S3-Auswertung](testdaten/S3_gps_and_baro/AUSWERTUNG.md).
Beim naechsten Bodenlauf sechs Module konsistent hochladen, Soft-Reboot und
Sensor-Test **0.2.0** / JSON-Schema 2 pruefen. Das neue RAM-Log soll den ganzen
kurzen Lauf mit 2 Hz behalten; Hardwarecheck bleibt offen.
Keine erneute Lage-/RC-Kalibrierung allein fuer dieses Sensorupdate.
Beim geplanten IMU-Umbau dagegen Achsenabbildung anpassen, neue Levelreferenz
speichern und Richtungen pruefen; [genaue Einbauanleitung](EINBAU_UND_MANUAL_DATENFLUG.md).
Neuen [USB-Startbefund](testdaten/barometer_tests/AUSWERTUNG.md)
vor erneutem Betrieb der montierten Servos eingrenzen.

T1/T2/T3/T5/T6 sind in den jeweiligen Auswertungen dokumentiert, T4 bleibt
bewusst offen. Timing-/Fehlerdiagnose wird parallel fortgesetzt; aktueller Plan:
[NAECHSTE_SCHRITTE.md](NAECHSTE_SCHRITTE.md). Die folgenden Abschnitte bleiben
als grundlegende Inbetriebnahme-/Kalibrieranleitung bestehen, sind kein Auftrag
zur erneuten Kalibrierung oder zum Start eines Servotests fuer den Sensorcheck.

## 1. Bisherige funktionierende Version sichern

In Thonny die aktuelle MCU-Datei und roll_level_cal_v1.json oeffnen und auf
dem Mac in einem separaten Ordner sichern. Auch die tatsaechlichen Werte fuer
SENSOR_SIGN, SERVO_SIGN, RX_CENTER_US und deine Reglerparameter notieren.
Die hier beiliegende config.py kennt deine zwischenzeitlichen lokalen
Aenderungen nicht. Die neue kaskadierte Regelung hat andere Parametereinheiten.
Alte Werte deshalb nicht blind unter neuen Parameternamen einsetzen.

## 2. Alle Module hochladen

Thonny: MicroPython (Raspberry Pi Pico), richtigen USB-Port waehlen.
Ansicht -> Dateien zeigt lokale Dateien und MCU-Dateien. Alle Dateien aus
firmware/ in das **Wurzelverzeichnis des MCU-Dateisystems** hochladen, nicht
in einen firmware-Unterordner. Je nach Thonny-Version erfolgt dies ueber
Rechtsklick -> Upload/Hochladen oder Datei -> Speichern unter -> Raspberry Pi Pico.
Nicht nur start_test.py hochladen: seine Imports brauchen die anderen Module.

README, docs, tests und Git-Dateien bleiben auf dem Mac. Keine leere
calibration.json hochladen: die Kalibrierprogramme erzeugen sie auf dem MCU.
Die alte Referenzdatei bleibt unangetastet; fuer diese Version ist eine neue
Roll-/Nickreferenz noetig. AUTO_START=False verhindert Autostart durch main.py.

Nach Aenderungen Stop und Soft-Reboot ausfuehren (z.B. Ctrl+D am >>>-Prompt;
MicroPython-Neustart ueber Thonny ebenfalls moeglich). Python cached Imports:
eine neu gespeicherte config.py wirkt nicht automatisch in einem laufenden Prozess.
Bei USB-Neuverbindung ohne BOOT-Taste starten. RPI-RP2 als Finder-Laufwerk
ist der Bootloader, nicht der laufende MicroPython-Interpreter.

## 3. Sensor und Orientierung pruefen

config.py:

```python
START_MODE = 'sensor'
ACTIVE_AXES = ('roll',)
```

start_test.py auf dem MCU oeffnen und Run. Sensor fest montieren, X nach vorne,
Y links, Z oben; die Achsenmarkierung entscheidet, nicht die Kabelrichtung.
Kalibrierung benoetigt 6 Sekunden Ruhe. Bauteile nicht mit der Hand halten.
Rollanzeige und Nickanzeige langsam testen. Dieser Modus erzeugt keine PWM.
Wenn die Montage von der Standardorientierung abweicht, body_axes/body_signs
gemeinsam passend konfigurieren (rechtshaendig); nicht nur einen Gyrokanal
invertieren. Bei Unsicherheit zuerst Messdaten/Fotos pruefen lassen.

## 4. Neue Referenz und RC-Mitte speichern

Programm stoppen. calibrate_level.py ausfuehren: Flugzeug geometrisch eben
ablegen, Enter, Ruhepruefung abwarten. Speichert calibration.json.

Dann calibrate_rc.py ausfuehren: Sender ein, Delta-Mischer aus, Trimmungen
fuer das Projekt mittig. Pro aktivem Kanal fragt es zuerst 2 Sekunden
Neutral und dann 8 Sekunden beide Endanschlaege ab. An Endanschlaegen kurz
verweilen. Diese Messung ersetzt das Raten eines Werts wie 1500 oder 1375.
Eine vorhandene Referenz bleibt erhalten; vorhandene andere Kanaele auch.

calibration.json danach vom MCU auf den Mac in firmware/ herunterladen,
damit Git die Geraeteeinstellungen mitsichert. Achtung: spaetere vollstaendige
Uploads duerfen keine veraltete lokale Kalibrierdatei ueber die neuere MCU-Datei
kopieren. Code aktualisieren und Kalibrierdatei nur bewusst ersetzen.

## 5. Roll manuell vergleichen

In config.py START_MODE='manual'; dann Reset und start_test.py starten.
Knueppel nach der Ruhekalibrierung mittig halten. WAIT_NEUTRAL wird MANUAL.
Beide Querruder pruefen. 'rx' sind Eingangspulse, 'servo' Ausgangspulse.
Die Ausgaenge bleiben am Anfang auf +/-200 us um die jeweilige Servo-Mitte
begrenzt. SENSOR/WAIT_NEUTRAL erzeugt vor der ersten Freigabe keine Pulse.
Trimmbewegung nach Freigabe blockiert den Code nicht; nach RX-Ausfall wird
die Freigabe erneut verlangt. CH1 ist nicht mehr direkt am Servo angeschlossen.

Receiver.sign bestimmt Links/Rechts-Kommando, Servos.sign die Ruderwirkung.
In beiden Modi muss ein positiver Roll-Steuerwert physisch Rechtsrollen
erzeugen. In X-vor/Y-links/Z-oben muss positiver Nick-Steuerwert
Nase-runter-Wirkung erzeugen; Nase-hoch ist negativ. Gier positiv bedeutet links.

## 6. Roll stabilisiert testen

Fuer v0.2.1 zuerst [ROLL_TISCHTEST.md](ROLL_TISCHTEST.md) durcharbeiten.
Erkannte Timingfehler verwerfen RX-Puffer und verlangen neue Neutralframes,
bevor MANUAL_FALLBACK moeglich ist. RX_TIMEOUT/WAIT_NEUTRAL sind dabei erwartbar.

START_MODE='stabilize', Reset, start_test.py. Bei Knueppelmitte links/rechts
kippen; das Ruder muss entgegenwirken. Anschliessend vorgegebene Neigung
testen: wenn Istlage=Sollage und keine Drehrate, geht der Ausgang in Trimlage.
Die Regelung ist jetzt kaskadiert; unterschiedliche Reaktionen zum alten
Ein-Datei-Test sind moeglich. angle_gain hat Einheit 1/s, rate_p us/(Grad/s).
rate_i vorerst 0 belassen. Erst kleine Wege und langsame Bewegungen vergleichen.
Ueber 70 Grad Roll allein verriegelt der Code nicht mehr. Nick >75 Grad,
Gyro-/Accel-Saettigung oder Laufzeitfehler ergeben MANUAL_FALLBACK.
Wiederherstellung der Automatik nur durch Neustart am Boden.

## 7. Nick nach abgeschlossenem Roll-Funktionstest

Ab v0.2.2 gilt [PITCH_YAW_TISCHTEST.md](PITCH_YAW_TISCHTEST.md). Am 2026-10-13
meldet der Besitzer alle Achsentests bestanden; [Testbericht](TESTBERICHT_2026-10-13.md).
Die folgende Reihenfolge dient der erneuten Inbetriebnahme nach Umbauten.
Erforderlicher Signalpfad: CH2->GP8 und GP6->Servo, nur spannungsfrei umstellen;
nie Receiver und MCU gleichzeitig an den Servosignal-Draht anschliessen.
Versorgungsbefund und BEC 5 V @ 3 A beachten: [Warnhinweise](VERSORGUNG_WARNHINWEISE.md).

Gespeichert ist jetzt SENSOR mit allen drei Achsen und Zeichen jeweils -1/-1.
Fuer eine erneute Einzelpruefung das passende Profil der Achsenanleitung waehlen
und die betroffene Richtungsbestaetigung zuruecknehmen. Nase-hoch ergibt negativen pitch_down;
das ist die beibehaltene rechtshaendige Koerperkonvention. calibrate_rc.run(('pitch',))
kann nur den neuen Kanal erfassen. Erst MANUAL-Richtungen pruefen, dann
DIRECTION_CHECKED_AXES erweitern und STABILIZE testen. Rollzeichen/Gains beibehalten.

## 8. Gier nach bestandenem Nick-Test

Gleiche Anleitung, naechste Stufe: Signalpfad bei getrennter Versorgung auf
CH4->GP9 und GP7->Servo umstellen. SENSOR, nur neue Gier-RC-Kalibrierung,
MANUAL-Vorzeichen, Richtungsbestaetigung, dann STABILIZE. Positive Koerper-Gier
bedeutet links; Rechtskommando ist negativ. Nach dem Stop einer Drehung geht
Gier zur Trimlage, ohne zur alten Richtung zurueckzuregeln. Kein absolutes
Kurs-Halten, keine koordinierte Flugkurve oder Flugabstimmung.

## 9. Rudertrim versus Fluglagen-Trim

SERVOS['pitch']['trim'] verschiebt Hoehenruder-Trim in Mikrosekunden;
FLIGHT_ATTITUDE_TRIM['pitch'] verschiebt den neutralen Nick-Sollwinkel in Grad.
Das eine ersetzt das andere nicht. Beide vorerst nur am Boden veraendern.
Sendertrimmung bleibt ein sichtbarer Steuerbefehl; automatische Mittenwanderung
ist absichtlich nicht implementiert. Fuer eindeutige In-Flug-Trimmung braucht
es einen expliziten Befehl/Modus, bevor wir Werte im Flug speichern.

## 10. Logs

Loggt 10 Hz plus Zustandswechsel in einen RAM-Ring (200 Eintraege, etwa bis 20 Sekunden).
Ctrl+C stoppt zuerst PWM/PIO und schreibt danach bench_<ticks>.csv auf Flash.
Nach beiden Speichermeldungen zuerst BEC-/Receiver-/Servoversorgung ausschalten,
USB angeschlossen lassen und Dateien in Ansicht -> Dateien per Kontextmenue
herunterladen. Erst danach USB trennen. Nicht zum Aktualisieren der Dateiliste
USB im laufenden Test abziehen; das ist ein MCU-Stromausfall, kein Programmstop.
v0.2.3 schreibt auch bench_<ticks>.json mit Statistik/Runtime/Konfiguration/
Kalibrierwerten. **Beide Dateien** zusammen herunterladen; Maxima gelten fuer
jede abgeschlossene Iteration, auch wenn alte CSV-Zeilen ueberschrieben sind.
CSV auf Mac in logs/ herunterladen. Laufende Rohlogs werden nicht mit Git committed.
Ein bewusst ausgewaehlter kleiner Nachweis darf unter docs/testdaten/ zusammen
mit Testbericht und Herkunft versioniert werden; so ist der Achsentest von
2026-10-13 gesichert. Die Serienlogs bleiben ausserhalb der Versionshistorie.
Vor Stromabschalten: auf erfolgreiche Speicherung warten. Stromausfall
verliert RAM-Logs. Alte CSV-Dateien nach Sicherung entfernen, sonst Flash voll.
Freien Speicher mit os.statvfs('/') pruefen. Kein SD-Modul fuer diesen Schritt.
Sowohl Printausgaben als auch RAM-Formatierung beeinflussen das Timing; echte
Board-Zeiten pruefen, bevor die Regelschleife als belastbar gelten kann.
