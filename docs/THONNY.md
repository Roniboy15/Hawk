# Thonny: Sicherung, Upload, Kalibrierung und Achsentests

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
erzeugen. Bei Hoehenruder muss positiver Nick-Steuerwert die Nase heben.

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

## 7. Nick erst danach hinzufuegen

**Der folgende Ausbau ist zurueckgestellt, bis die Nick-Vorzeichenkonvention
aufgeloest und getestet ist. Aktuell nur Roll aktivieren.** Die positive
Nickvorgabe im bisherigen manuellen Ablauf passt nicht zur beschriebenen
X-vor/Y-links/Z-oben-Quaternionkonvention; Servozeichen nicht blind uebernehmen.

Strom trennen. CH2-Signal -> GP8, Hoehenrudersignal -> GP6, Servo Plus BEC5V,
Minus gemeinsame Masse. Eingang vorher auf GPIO-vertraeglichen Pegel bringen.
Kein Servo-Datendraht bleibt direkt am entsprechenden Receiverausgang.

```python
ACTIVE_AXES = ('roll', 'pitch')
START_MODE = 'sensor'
```

Sensor pruefen. calibrate_rc.py erneut fuer beide Kanaele ausfuehren (CH2
hinzugekommen). Dann manual und beide Knueppel/Ruder pruefen. Erst danach
stabilize: Nase oben -> Nase-ab-Ruderkommando; Nase unten -> Nase-auf.
Roll/Ruder bleiben korrekt. Danach kombinierte Bewegungen vorsichtig pruefen.
Fehlender CH2-Eingang verhindert jetzt die Freigabe beider Achsen.

## 8. Optional Gier

CH4 -> GP9, Seitenrudersignal -> GP7, Versorgung wie oben.
ACTIVE_AXES=('roll','pitch','yaw'), RC-Kalibrierung wiederholen.
Erst manual, dann stabilize. Seitliche Drehung -> entgegengesetzte
Gier-Drehratenkorrektur; fest gehaltene neue Richtung -> Korrektur klingt ab.
Es ist kein Kompass-/Kurs-Halten. Ein absichtlich ausgefuehrter Kurvenflug
braucht spaeter Turn-Koordination; die simple Gier-Daempfung ist dafuer noch
keine geeignete Flugabstimmung und kann gegen gewuenschte Drehung arbeiten.

## 9. Rudertrim versus Fluglagen-Trim

SERVOS['pitch']['trim'] verschiebt Hoehenruder-Trim in Mikrosekunden;
FLIGHT_ATTITUDE_TRIM['pitch'] verschiebt den neutralen Nick-Sollwinkel in Grad.
Das eine ersetzt das andere nicht. Beide vorerst nur am Boden veraendern.
Sendertrimmung bleibt ein sichtbarer Steuerbefehl; automatische Mittenwanderung
ist absichtlich nicht implementiert. Fuer eindeutige In-Flug-Trimmung braucht
es einen expliziten Befehl/Modus, bevor wir Werte im Flug speichern.

## 10. Logs

Loggt 10 Hz in einen RAM-Ring (200 Eintraege = letzte ca.20 Sekunden).
Ctrl+C stoppt zuerst PWM/PIO und schreibt danach bench_<ticks>.csv auf Flash.
CSV auf Mac in logs/ herunterladen. Logs werden nicht mit Git committed.
Vor Stromabschalten: auf erfolgreiche Speicherung warten. Stromausfall
verliert RAM-Logs. Alte CSV-Dateien nach Sicherung entfernen, sonst Flash voll.
Freien Speicher mit os.statvfs('/') pruefen. Kein SD-Modul fuer diesen Schritt.
Sowohl Printausgaben als auch RAM-Formatierung beeinflussen das Timing; echte
Board-Zeiten pruefen, bevor die Regelschleife als belastbar gelten kann.
