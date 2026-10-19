# BN-180 und GY-63/MS5611 zuerst pruefen

Stand 2026-10-18, Branch codex/gps-baro-bringup ab Tischtestcommit 913a9e6.
Ziel dieses Schritts: Daten empfangen, Gueltigkeit/Einheiten pruefen und am Boden
vergleichen. Noch keine GPS-Regelung, Hoehenhaltung oder autonome Kreisfunktion.
Der Besitzer moechte anschliessend mit dem bisherigen MCU-MANUAL-Durchgang
Flugdaten sammeln und akzeptiert dessen Abhaengigkeit vom MCU. Das ist eine
Projektentscheidung; ein unabhaengiger Rueckweg wird dadurch nicht geschaffen.
Timing wird weiter gemessen, ohne exakt 100 Hz als pauschale Einstiegshuerde
fuer die Sensorentwicklung zu behandeln.

## Module und gesicherte Angaben

Screenshot/Bestellangabe und Besitzer: BN-180, M8030-KT; GY-63 mit
MS5611-01BA03. GY-63-Pins: VCC, GND, SCL, SDA, CSB, SDO, PS.
Das BN-180 hat vier Anschlussleitungen; PPS/TX bezeichnen hier LEDs,
nicht zwei zusaetzliche benoetigte GPIO-Leitungen.

Beitian nennt fuer BN-180 NMEA, 9600 Baud, 1 Hz als Defaults und eine typische
Versorgung mit 5 V. Die Herstellerseite nennt 3.6..5.5 V; die vom Besitzer
gelieferte Beschreibung nennt 3.0..5.5 V. Fuer den ersten Test 5 V verwenden.
Damit ist die Zuordnung der tatsaechlichen Kabel noch nicht bewiesen.

**Vor dem Anschliessen des GPS muessen VCC/GND/TX/RX eindeutig zugeordnet sein.**
Keine Kabelfarbe oder Steckeransicht raten. TTL ist keine verbindliche Zusage
fuer 3.3-V-Pegel; GPIO vertraegt keine direkte RS-232-Verbindung. Anschlussplan
und TX-Pegel der konkreten Platine abgleichen. Die bisherigen Angaben enthalten
keine Kabel-Pinfolge. Bis dahin GPS nicht auf Verdacht verbinden.

## Verdrahtung fuer diesen Test

Zuerst laufende Programme stoppen und USB sowie BEC/Batterie trennen.
**BEC/Servobatterie bleibt fuer diese Sensortests aus.** Anschliessend nur MCU
und Sensoren per USB versorgen. Bestehende IMU-/Servo-/Receiverpins bleiben erhalten.
GP sind GPIO-Nummern, nicht die physischen Pinpositionen.

| Modulanschluss | MCU / Verbindung | Bemerkung |
| --- | --- | --- |
| GY-63 VCC | MCU 3V3 | Erster Test auf 3.3-V-Versorgungs-/Signalniveau |
| GY-63 GND | MCU GND | Gemeinsame Masse |
| GY-63 SDA | GP10 | Eigener I2C1-Bus, 100 kHz |
| GY-63 SCL | GP11 | IMU bleibt auf I2C0, GP4/GP5 |
| GY-63 PS | 3V3 | I2C-Modus; vorhandene Platinenbeschaltung beachten |
| GY-63 CSB | GND | Erwartete Adresse 0x77; CSB darf nicht schweben |
| GY-63 SDO | Nicht verbinden | Im I2C-Modus unbenutzt |
| BN-180 VCC | USB-5-V-Pin des MCU | Erst nach eindeutigem Kabelabgleich; kein BEC-Plus dazu verbinden |
| BN-180 GND | MCU GND | Erst nach Kabelabgleich |
| BN-180 TX | GP13, UART0 RX | Nur bei bestaetigtem kompatiblem Signalpegel |
| BN-180 RX | Nicht verbinden, isolieren | Wir empfangen nur und konfigurieren das GPS nicht |
| GP12 | Nicht verbinden | Reservierter UART0-TX-Pin, sendet keine Befehle |

Beim GY-63 die Modulbeschaltung/Versorgung pruefen: Datenblattangaben des
MS5611-Chips sind keine vollstaendige Schaltungsgarantie fuer jede GY-63-Kopie.
I2C-Pullups duerfen die Signalleitungen nicht auf 5 V ziehen. Zum Aendern der
Verdrahtung wieder alle Quellen trennen. GPS und Barometer zuerst einzeln testen.

## Software hochladen

Diese sechs Dateien aus firmware/ gehoeren zusammen ins MCU-Wurzelverzeichnis:

- config.py, diagnostics.py, logger.py
- gps.py, ms5611.py, sensor_test.py

Vorhandene calibration.json erhalten; dieser Test liest oder aendert sie nicht.
AUTO_START bleibt False, START_MODE bleibt sensor. Nach Upload Soft-Reboot.
Anschliessend die folgenden Aufrufe am >>>-Prompt der Thonny-Shell ausfuehren.
Nicht gleichzeitig app.run(), start_test.py oder einen anderen Sensorstarter starten.
Ein Import allein startet nichts; sensor_test.run() ist der bewusste Teststart.

## S1 — Barometer, zuerst 60 Sekunden

Nach gepruefter Barometerverdrahtung, GPS zunaechst abgesteckt:

```python
import sensor_test
sensor_test.run('baro', duration_s=60)
```

Erwartet: Adresse 0x77, PROM CRC OK, Druck p in Pa, Temperatur T in Grad C.
Nach zwei Sekunden Wartezeit werden 20 Messungen zum Startdruck gemittelt;
danach erscheint h_rel in Metern relativ zu diesem Druck. Das setzt keine
Lagen-/RC-Kalibrierung neu und speichert keine dauerhafte Hoehenreferenz.

1. Etwa 20 s ruhig liegen lassen: Druck/Temperatur sollen plausibel und die
   Hoehenanzeige ruhig sein. Sensortemperatur muss nicht exakt der Raumluft entsprechen.
2. Sensor langsam etwa 1..2 m anheben, kurz halten, wieder absenken:
   Druck muss sinken, relative Hoehe steigen; danach ungefaehr zurueckkehren.
3. Nicht auf den Sensor blasen oder die Druckoeffnung abkleben. Zum Vergleich
   braucht es lokalen Absolutdruck; Wetterapps zeigen oft auf Meereshöhe
   reduzierten Druck. 100000 Pa = 1000 hPa.

S1 funktional bestanden: keine Fehler im JSON, neue Barometerwerte,
reference_pa gesetzt, plausible Werte und richtige Hoehenaenderungsrichtung.
CRC bestaetigt die Konsistenz der gelesenen PROM-Werte, nicht allein die Chipidentitaet.
Jitter/Drift notieren; diese Anzeige ist noch kein kalibriertes Thermikvario.

## S2 — GPS draussen, 180 Sekunden

Erst Kabel-/Pegelzuordnung klaeren und spannungsfrei anschliessen. Dann unter
freiem Himmel mit Antennenoberseite nach oben, Modell/GPS zunaechst ruhig halten:

```python
import sensor_test
sensor_test.run('gps', duration_s=180)
```

Keine Indoor-Fix-Garantie und keinen Fix nach exakt 26 s verlangen. Schon ohne
Fix sollten Pruefsummen-gueltige Saetze eintreffen. fix=0 und leere Koordinaten
sind dann richtig; sie duerfen nicht als Position 0/0 ausgegeben werden.

1. Im JSON gps_counters.sentences/updates pruefen. Beide sollen ansteigen;
   wiederholte checksum_errors deuten auf Baud-/Leitungs-/Pegelfehler hin.
2. Auf fix=1 warten: frische gueltige GGA/RMC derselben UTC-Epoche. Position
   mit dem bekannten Standort/Karte vergleichen. Satelliten und HDOP mitnotieren;
   HDOP ist keine zugesicherte Genauigkeit in Metern.
3. Nach Fix etwa 10..20 m gehen und wieder anhalten. Position/Geschwindigkeit
   muessen sinnvoll reagieren. Im Stillstand kann der Kurs springen; course_usable
   bleibt unter der konfigurierten 2-m/s-Schwelle false. Das ist ein Diagnosemerkmal,
   keine spaetere Navigationsfreigabe.

GPS-Hoehe ist GGA-Hoehe ueber MSL; Barometerhoehe hier relativ zum Startdruck.
Beide Zahlen muessen daher nicht gleich sein. GPS-Kurs ist Bewegungsrichtung
ueber Grund, keine IMU-Gier und keine Ausrichtung im Stand. GPS-Geschwindigkeit
ist Groundspeed, keine Airspeed. Ein 1-Hz-Fix ist kein bereits validierter Kreisregler.

S2 funktional bestanden: wiederholt plausible, frische Positionsdaten mit
passendem Standort/Bewegungsverlauf und ohne fortgesetzte Datenfehler. LEDs
allein reichen nicht. Bei bytes=0 zuerst Zuordnung/Versorgung/TX->RX pruefen;
bei Bytes ohne gueltige Saetze Baudrate/Pegel abgleichen, nicht wahllos umstecken.

## S3 — Gemeinsam, 180 Sekunden

Nach S1/S2 beide Sensoren anschliessen und denselben Aussenversuch wiederholen:

```python
import sensor_test
sensor_test.run('both', duration_s=180)
```

GPS-Fix und neue Barometerdaten sollen gemeinsam bestehen bleiben. Genau diese
Dateipaare und deine physische Beobachtung sichern, dann die MANUAL-Integration
planen. Diese Sensortests erzeugen keinerlei Servo-PWM und messen keinen MANUAL-
oder STABILIZE-Regelkreis. Ihre Laufzeiten sind nur die des Sensorstarters.

## Stop, Dateien und Grenzen

Lauf endet nach der angegebenen Zeit oder mit Ctrl+C. Auf **beide** Meldungen
Sensor-CSV gespeichert / Sensor-JSON gespeichert warten. USB bleibt zum Download
angeschlossen; BEC bleibt aus. Unterordner pro Lauf auf dem Mac verwenden.
Dateinamen sensors_<ticks>_<index>.csv/json werden nicht wiederverwendet.

- CSV: 5 Hz, **nur die letzten 200 Zeilen**, etwa 40 s. Kein vollstaendiger Fluglog.
- JSON: Konfiguration, Runtime, Fehlerphase/Text, GPS-Zaehler, erste vier gueltige
  NMEA-Saetze, PROM, Startdruck, Messanzahl und Timingstatistik des ganzen Laufs.
- Leere CSV-Zahlen bedeuten unbekannt/ungueltig, Alter -1 bedeutet unbekannt.
  Frische bezieht sich auf Softwareempfang, nicht auf einen Hardwarezeitstempel.
- GPS nach Pollpause >100 ms: Altdaten verwerfen, neue Saetze verlangen. Kein
  Warten auf Fix im Regelkreis; ADC-Konvertierungen brauchen jeweils bis 9.04 ms
  und werden hier ueber getrennte Pollaufrufe abgewartet.
- Fehler werden fuer diesen Sensor verriegelt und mit Phase/Text gespeichert.
  Ein Sensorfehler darf nicht still durch einen alten Wert als frisch ersetzt werden.

Hoststand dieser Vorbereitung: 120 Tests bestanden (94 bisherige und 26 neue).
Das bestaetigt Parser/Mathematik/Testablauf, keine physische Sensorfunktion.

Rohlogs bleiben normalerweise ausserhalb Git; ausgewaehlte Nachweise spaeter
mit Auswertung versionieren. Bei unvollstaendigem Export beide Dateien pruefen,
keinen vollstaendigen Lauf behaupten. Noch keine realen Sensorergebnisse liegen vor.

## Danach: MANUAL-Flugdaten vorbereiten

Naechster Codeumfang nach bestandenem S1/S2/S3: Sensorpolling begrenzt in den
bisherigen MANUAL-Ablauf integrieren, gemeinsame Zeitbasis fuer IMU/RC/Ausgaenge/
GPS/Barometer und ganze Fluege aufzeichnenden Speicherweg implementieren. Den
Mehraufwand am Boden messen; keine blockierenden ADC-Wartezeiten in app.run().
Der jetzige 200-Zeilen-Ring reicht dafuer nicht. Ein gepackter RAM-Puffer fuer
z.B. 600 Samples bei 1 Hz (10 min) plus fortlaufende Zeit-/Fehleraggregate ist
ein moeglicher erster Entwurf; den RAM-Bedarf auf dem MCU messen. Noch nicht
implementiert. Speicherrate, Flugdauer und Medium bewusst festlegen;
Flash-Schreiben mit aktiver Steuerung ist im aktuellen
Regelkreis weiterhin ausgeschlossen. Deshalb ist S3 noch kein sofortiger Flugstart.

Danach manuell Daten sammeln, Zeiten/Fehler und Datenqualitaet bewerten, dann
naechsten Schritt waehlen. Ein autonomer Kreis benoetigt zusaetzlich Kreis-/Kurs-
fuehrung, gueltige Sensorzustände, Modus-/Uebernahmeverhalten und eine passende
Nick-/Geschwindigkeitsstrategie. GPS und Barometer allein implementieren das nicht.

## Primaerquellen

- [Beitian BN-180](https://www.beitian.com/sys-pd/9.html): Modul-/Schnittstellenangaben.
- [TE MS5611-Datenblatt](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet): Kompensation, I2C, Wandlungszeit.
- [Hersteller-Appnote AN520, AMSYS-Archiv](https://www.amsys-sensor.com/downloads/notes/MS5XXX-C-code-example-for-MS56xx-MS57xx-MS58xx-AMSYS-an520e.pdf): CRC und Testvektor; deren MS5607-Formeln nicht fuer MS5611 uebernehmen.
- [u-blox 8/M8 Protokoll](https://content.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf): NMEA-GGA/RMC und Einheiten.
- [MicroPython RP2](https://docs.micropython.org/en/v1.29.0/rp2/quickref.html),
  [UART](https://docs.micropython.org/en/v1.29.0/library/machine.UART.html),
  [I2C](https://docs.micropython.org/en/v1.29.0/library/machine.I2C.html): Schnittstellen auf der gemeldeten Runtime.
