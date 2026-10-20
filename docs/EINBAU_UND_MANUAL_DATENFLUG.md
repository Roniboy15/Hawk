# Einbau und erster MANUAL-Datenflug: konkreter Arbeitsplan

Stand 2026-10-20. S1/S2/S3 sind funktional bestanden; siehe
[S3-Auswertung](testdaten/S3_gps_and_baro/AUSWERTUNG.md).
Der naechste Codeumfang ist ein MANUAL-Fluglogger, keine neue Stabilisierung
oder autonome Kreisfuehrung. Die folgenden Bordstart-/Loggerfunktionen sind
ein Implementierungsauftrag, noch keine im aktuellen Code vorhandene Flugfunktion.
Die akzeptierte MCU-Abhaengigkeit des bisherigen MANUAL-Durchgangs bleibt.

## 1. Versorgung vor dem festen Einbau aufzeichnen

Die drei Leisten **5 V, GND und 3V3** sind als Verteilung sinnvoll, aber nicht
alle Sensoren gehoeren an 3V3. Jede Plusleiste hat genau eine passende Quelle;
die Minusleiste ist gemeinsam. Leitungen/Stecker dauerhaft beschriften.

| Verbraucher | Versorgung | Hinweise |
| --- | --- | --- |
| IMU SY-104 | Geregelte 3V3, gemeinsame Masse | Gleicher Stand wie bisheriger Test; exakter Chip nicht gesichert |
| GY-63/MS5611 | Geregelte 3V3, gemeinsame Masse | Auch I2C-Pullups nur nach 3V3 |
| BN-180 GPS | Geregelte 5 V, gemeinsame Masse | Beitian nennt 3.6..5.5 V, typisch 5 V; 3V3 liegt darunter |
| Empfaenger / vier Servos | BEC 5 V, gemeinsame Masse | Zulassung der konkreten Komponenten beachten; Lastreserve messen |
| RP2040-Zero an Bord | Geeignete geregelte Quelle am dafuer vorgesehenen 5-V-Eingang | Versorgungspfad und spaeteren USB-Anschluss vorher festlegen |

**Nicht verbinden:** 7.4-V-Batterie direkt mit 5-V-/3V3-Verbrauchern; 5 V mit
3V3; Ausgaenge verschiedener Regler miteinander. Die 3V3-Leiste kommt vom
MCU-Regler oder einer bewusst ausgelegten separaten Quelle, nicht von zwei
parallel geschalteten Reglern. Gesamtstrom und Spannungsabfall am Sensor pruefen.

Beim RP2040-Zero darf BEC-5-V am Board nicht einfach gleichzeitig mit Mac-USB-5-V
zusammengeschaltet werden. Den dokumentierten Board-Schaltplan und den
tatsaechlichen Versorgungs-/USB-Pfad beachten; kein automatisches Quellen-ORing
wie bei einer anderen Platine voraussetzen. Fuer Entwicklung eine Quelle
verwenden, fuer spaeteren USB-Datenzugriff einen geeigneten, geprueften
Versorgungs-/Trennpfad vorsehen. Nicht erst am montierten Modell ausprobieren.

Die Aufschrift **5 V @ 3 A** ist die bekannte BEC-Ausgangsangabe; grosses
"20 A" belegt keine 20-A-Reserve fuer vier Servos. Eine Stromleiste und der
1000-uF/10-V-Kondensator vergroessern die Dauerleistung des BEC nicht.
Kondensator parallel zum geregelten 5-V-Ausgang, Minus an GND, mechanisch sichern.
Unter normaler gleichzeitiger Bewegung aller vier Servos 5 V und 3V3 an den
Verbrauchern beobachten/messen, auch mit niedrigerem Batteriestand. Kein
absichtliches Blockieren von Rudern. Ein Multimeter allein schliesst kurze
Einbrueche nicht aus; bei Auffaelligkeiten Strom/Spannungsverlauf messen.

Servostrom und dessen Rueckleitung direkt ueber ausreichend dimensionierte
Verteilung fuehren; nicht durch duenne Sensor- oder MCU-Masseleitungen.
MCU/Sensoren brauchen trotzdem eine zuverlaessige gemeinsame Signalmasse.
BEC und Hochstromleitungen moeglichst vom Sensor-/Antennenbereich fernhalten.

Der fruehere Endausschlag bei USB-Anschluss ist durch S3 nicht geklaert.
Vor einem weiteren betriebenen Aktuatoraufbau Startdateien und Strompfad
pruefen; die IMU nicht unversorgt an aktiven SDA/SCL lassen. Unkontrollierten
Endausschlag nicht absichtlich wiederholen. Dieser konkrete Startbefund ist
etwas anderes als das vom Besitzer akzeptierte Fehlen eines MCU-Bypasses.

## 2. Sensoranschluesse beibehalten

GP bezeichnet GPIO-Nummern, keine physischen Pinpositionen. Alle Quellen vor
Arbeiten an den Leitungen trennen. Nach Einbau alle Verbindungen durchpruefen.

| Modul / Pin | Verbindung |
| --- | --- |
| IMU VCC / GND | 3V3 / gemeinsame Masse |
| IMU SDA / SCL | GP4 / GP5, I2C0 mit 100 kHz |
| GY-63 VCC / GND | 3V3 / gemeinsame Masse |
| GY-63 SDA / SCL | GP10 / GP11, I2C1 mit 100 kHz |
| GY-63 PS / CSB | 3V3 / GND: I2C, erwartete Adresse 0x77 |
| GY-63 SDO | Offen lassen |
| BN-180 VCC / GND | Geregelte 5 V / gemeinsame Masse |
| BN-180 TX | GP13, UART0 RX, 9600 Baud; beim Besitzerexemplar weisses Kabel |
| BN-180 RX / MCU GP12 | Nicht verbinden, getrennt isolieren; keine GPS-Konfiguration vorgesehen |

Der funktionierende NMEA-Empfang bestaetigt keine Spannungsmessung:
GPS-TX und RC-Pulse muessen zu RP2040-3V3-Eingaengen passen. 5-V-Versorgung
eines Moduls ist keine Zusage ueber dessen Ausgangssignal. VCC/GND-Zuordnung
nicht aus Kabelfarben anderer Exemplare ableiten. Keine 5-V-I2C-Pullups.
I2C-Leitungen kurz, fest und fern von Servoleitungen halten; nach geaenderter
Kabellaenge beide Busse im endgueltigen Aufbau erneut pruefen.

## 3. IMU: Oberseite oben, X nach hinten

Das ist fuer den bestaetigten bisherigen Achsenaufbau eine Drehung um 180 Grad
um Z. Sensor-X zeigt nach hinten, Y nach rechts, Z bleibt oben. **Erst beim
mechanischen Umbau** in firmware/config.py innerhalb SENSOR einstellen:

```python
'body_axes': (0, 1, 2),
'body_signs': (-1, -1, 1),
```

Die aktive Repository-Konfiguration bleibt bis dahin beim getesteten alten
Aufbau. Nicht nur X umkehren: das waere keine rechtshaendige Drehung. Dieselbe
Abbildung gilt fuer Beschleunigung und Gyro. Die vorhandenen Rohsensor-
acc_offset/acc_scale bleiben fuer dieselbe IMU erhalten; diese werden vor der
Achsenabbildung angewendet. Bei einem neuen Sensor ist das gesondert zu bewerten.

Eine neue Waagerechtkalibrierung allein erkennt diese 180-Grad-Drehung nicht,
weil die Gravitation im Stand unveraendert ist. Deshalb in dieser Reihenfolge:

1. calibration.json vom MCU auf dem Mac sichern. Alle Versorgungen trennen,
   IMU fest montieren und reale Achsenpfeile/Leitungen kontrollieren.
2. Neue Achsenabbildung einstellen. DIRECTION_CHECKED_AXES fuer die erneute
   Richtungspruefung voruebergehend leeren; AUTO_START=False beibehalten.
   Konsistent hochladen, calibration.json erhalten, Soft-Reboot; BEC bleibt aus.
3. Mit fest eingebauter IMU Flugzeug geometrisch waagerecht/ruhig ablegen und
   `import calibrate_level; calibrate_level.run()` ausfuehren. Das speichert
   Level und neue Achsenmetadaten, ohne die vorhandene RC-Kalibrierung zu ersetzen.
   Aktualisierte calibration.json wieder sichern. Nicht zuerst app im SENSOR-
   Modus starten: dessen Startpruefung lehnt die alte Leveldatei nach geaenderter
   Achsenabbildung absichtlich ab. Die Datei nicht als Umgehung loeschen.
4. Jetzt im SENSOR-Modus Richtungen und Gyro kontrollieren: rechte Flaeche
   tiefer ergibt +Roll, Nase tiefer +pitch_down, Drehen der Nase nach links
   +Gierrate. Gier ist hier Drehrate/integrierter Winkel, kein absoluter
   Kompasskurs. Gyro-Ruheoffset wird beim App-Start ohnehin neu gemessen;
   dabei Modell ruhig halten.
5. MANUAL-Wirkung und jede betroffene Stabilisierung am Boden neu pruefen,
   erst dann die geprueften Achsen wieder eintragen. RX-/Servozeichen nicht
   umkehren, um eine falsche IMU-Zuordnung zu kaschieren.

Bei willkuerlich schraegem Einbau reichen diese Vorzeichen/Vertauschungen nicht
fuer die vollstaendige Montagekorrektur; die jetzige Implementierung unterstuetzt
rechtwinklige Achsenzuordnungen. Deshalb die IMU achsparallel fest montieren.

## 4. Mechanischer Einbau

- **IMU:** steif zum Rumpf, achsparallel, moeglichst nahe am Schwerpunkt;
  keine lose Platine oder schwingende Befestigung. Abstand zu vibrierenden
  Servos und Kabelkraefte auf die Platine vermeiden.
- **GPS:** Antennenoberseite zum Himmel; keine Metall-/Carbonabschirmung
  darueber. Antenne von BEC, Stoerquellen und Hochstromleitungen absetzen,
  Empfang im geschlossenen Rumpf pruefen. Kein unbelegter fester Mindestabstand.
- **Barometer:** Druckausgleich zur Aussenluft, vor direkter Anstroemung/
  Staudruck und BEC-Waerme geschuetzt. Druckport nicht zukleben, vergiessen oder
  luftdicht einschliessen. S3-Hoehenspruenge sind Anlass fuer diesen Einbaucheck,
  keine gesicherte Diagnose von Wind als Ursache.
- **Kabel/Leisten:** fest verriegelte/gesicherte Verbindungen, Zugentlastung,
  Isolierung, gesicherter Akku und Kondensator. Lose Steckbruecken sind keine
  dauerhaft zuverlaessige Flugverkabelung. Keine Leitung in Servogestaenge,
  Ruderweg, Antenne oder bewegliche Klappe; Schwerpunkt nach Einbau pruefen.
- **Zugang:** Start-/Stopbedienung und Datendownload ohne Ziehen an live
  versorgten Signalleitungen oder Ausbau der Achsenreferenz ermoeglichen.

## 5. Naechster Codeauftrag: MANUAL-Fluglogger

Vorgeschlagener neuer Branch: **codex/manual-flight-logger**, vom noch
freizugebenden Sensorabschlusscommit. Folgende Punkte dort implementieren:

1. Bestehenden MANUAL-Durchgang und seine Neutralfreigabe beibehalten.
   GPS/MS5611 nur mit begrenztem Aufwand pollen; keine Fix-Warteschleife,
   ADC-Sleeps oder Flashausgabe in der aktiven Steuerung. Fehlendes GPS/
   Barometer darf die MANUAL-Ausgabe nicht beenden oder auf alte Daten warten.
2. Gemeinsame Zeitbasis fuer IMU-Lage/Gyro, RX, tatsaechlich kommandierte
   Servopulse, GPS, Barometer, Gueltigkeit/Alter, Modus/Fault und Schleifenzeit.
   Gesamte Iterationszeiten weiter aggregieren; Zusatzsensorzeit gesondert
   sichtbar machen. 1-Hz-Samples ersetzen keine Zeitstatistik jeder Iteration
   und keine hochaufloesende Regleranalyse.
3. Zunaechst **5 min bei 1 Hz** als begrenzten MANUAL-Datenflug planen,
   gepackten RAM-Bedarf mit den zusaetzlichen Feldern berechnen und freie
   Reserve auf dem echten MCU pruefen. Das ist ein Startvorschlag, kein schon
   zugesicherter Speicherumfang. Puffer vor Steuerungsstart reservieren.
   Wenn er voll ist: Logging klar als voll markieren, MANUAL-Steuerung weiter
   betreiben; keinen automatischen Programmabbruch oder Ringverlust verstecken.
4. Bewussten Bordstart und **nur am Boden** bedienten Stop/Export entwerfen.
   AUTO_START=False startet nach Einschalten noch kein MANUAL-Programm.
   Ein eigenes, geprueftes Startprofil ist noetig; kein stiller Defaultwechsel
   fuer alle Sensor-/Thonnytests. Einen zugaenglichen dedizierten Bodeneingang
   fuer Stop/Export vorsehen und gegen unbeabsichtigte Betaetigung sichern.
   Nicht durch einen Flugtimer die manuelle Steuerung abschalten.
5. Nach Landung Versorgung bis zum abgeschlossenen Export erhalten: Stop
   beendet die Steuerung/Outputs bewusst, danach erst CSV/JSON schreiben.
   Erst nach Abschluss ausschalten. Fuer das Herunterladen Mac-USB erst im
   zuvor geklaerten Strompfad anschliessen. Ein voller RAM-Puffer geht bei
   stromlosem Ausschalten verloren; einfach Akku ziehen sichert keine Daten.

Der vorhandene sensor_test 0.2.0 ist dafuer eine Speicher-/Treiberbasis, aber
enthaelt noch keine IMU-/RX-/Servodaten. app/bench verwendet weiterhin den
alten Ring. Die hier genannten Punkte sind noch zu entwickeln und zu testen.

## 6. Bodenlauf im finalen Aufbau, danach erster Datenflug

Vor dem Flug mit der integrierten Version: richtige Achsen und Ruderwirkung,
sicheres Start-/Neutralverhalten, stabile Bordversorgung bei ueblicher
gleichzeitiger Servolast, frische Zusatzsensorwerte und vollstaendigen Log-
Stop/Export am Boden nachweisen. Die mechanische Absicherung ersetzt keine
Signalpruefung. Receiver-Reichweite/Failsafe und uebliche Modellflugchecks
bleiben erforderlich. Die neue Vollaufzeichnung kann dabei geprueft werden;
keine weitere Huegelrunde als pauschale Vorbedingung.

Erster Datenflug bewusst MANUAL, begrenzt auf den getesteten Speicherumfang;
keine automatische Aktivierung von STABILIZE oder Kreisfuehrung. Anschliessend
Dateien mit Konfiguration, Kalibrierung und Montagefoto sichern und Versorgung,
GPS/Barometerqualitaet sowie reale Laufzeiten bewerten. Danach Umfang der
naechsten Stabilisierung/Navigation festlegen. T4 und Timingarbeit bleiben
offen, ohne erneut einen unabhängigen MCU-Bypass als pauschale Sperre einzufuehren.

## Primaerquellen fuer die Hardwarehinweise

- [Beitian BN-180](https://www.beitian.com/sys-pd/9.html): Versorgung und Schnittstelle.
- [Waveshare RP2040-Zero-Schaltplan](https://files.waveshare.com/upload/4/4c/RP2040_Zero.pdf): Board-Versorgungspfad.
- [TE MS5611-Datenblatt](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet): Chipversorgung, I2C, Drucksensor.
- [u-blox M8 Hardware Integration](https://content.u-blox.com/sites/default/files/NEO-M8_HardwareIntegrationManual_(UBX-13003557).pdf): allgemeine GNSS-Antennen-/Stoerhinweise, nicht BN-180-Pinbelegung.
- [Pololu: Servo electrical characteristics](https://www.pololu.com/blog/16/electrical-characteristics-of-servos-and-introduction-to-the-servo-control-interface): lastabhaengige Servostroeme.
