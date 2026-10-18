# Thonny: Sicherung, Upload, Kalibrierung und Achsentests

**Aktueller v0.2.3-Schritt:** [FEHLER_TISCHTEST.md](FEHLER_TISCHTEST.md).
Die [Auswertung T1/T2](testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T1_T2.md)
enthaelt einen ersten T1-Sensorfehler, eine bestandene T1-Wiederholung und einen
USB-Stromverlustbefund. Korrigierte Stopfolge verwenden, als naechstes T3 MANUAL;
vor weiterer Stabilisierung Sensorbefund/Timing klaeren.
Alle 15 Firmwaremodule hochladen, vorhandene calibration.json erhalten. Danach
die dortigen bench_test.run(...)-Aufrufe am Shell-Prompt verwenden. Kein Import-
Autostart; Testmodi liegen nur im RAM. Die folgenden Abschnitte bleiben als
grundlegende Inbetriebnahme-/Kalibrieranleitung bestehen.

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
