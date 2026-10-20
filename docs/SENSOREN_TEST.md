# BN-180 und GY-63/MS5611 zuerst pruefen

Stand 2026-10-20, Branch codex/gps-baro-bringup ab Tischtestcommit 913a9e6.
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

Nachtrag 2026-10-19: Besitzer bestaetigt fuer sein konkretes BN-180 **weiss =
GPS-TX-Ausgang** laut Beschreibung. Ein erster Aussenlauf liefert gueltige
NMEA-Saetze bei 9600 Baud. Andere Farben/Steckerbelegung nicht daraus ableiten;
TX-Spannungspegel ist damit nicht gemessen. Positionsnachweis ist inzwischen
mit gps_2 und S3 funktional erbracht; Historie und Softwarekorrektur unten bei S2.

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

**Nachtrag USB-Startbefund 2026-10-19:** Bei bereits versorgtem BEC schlugen
laut Besitzer Hoehen-/Seitenruder beim USB-Anstecken aus. Die bisherige IMU war
ohne Versorgung, SDA/SCL/GND aber angeschlossen. Fuer diesen Sensorstarter
bleiben BEC/Empfaenger/Servos deshalb wie vorgesehen aus. Keine Servo-PWM
bedeutet keine laufenden Neutralpulse; versorgte Servos sind damit nicht
automatisch gegen Bewegung abgesichert. IMU normal mitversorgen oder bei
getrennten Quellen vollstaendig abstecken, nicht nur VCC entfernen. IMU und
GY-63 koennen 3V3/GND teilen; ihre I2C-Busse bleiben getrennt. Nicht davon
ausgehen, dass unversorgte Baugruppen angeschlossene aktive Signale vertragen.
Details und offene Ursachen: [Versorgungsbefund](VERSORGUNG_WARNHINWEISE.md).

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

**S2 funktional bestanden am 2026-10-20:** gps_2 zeigt Fix nach 74.820 s,
keine Pollpausen, keine Pruefsummen-/Parserfehler und plausible Gehbewegung.
Der nachgereichte Konsolenauszug zeigt Hinweg mit West-/Suedanteil und
Rueckweg mit Ost-/Nordanteil. Absolute Genauigkeit ist nicht vermessen.
S3 ist inzwischen ebenfalls funktional bestanden; keine S2-Wiederholung allein
wegen des alten Ringpuffers.
[gps_2-Auswertung und Wegdiagramm](testdaten/gps_tests/AUSWERTUNG_GPS_2.md).

Der erste Lauf hatte keinen aufgezeichneten Fix und 314 Pollpausen. Seit 0.1.1
fordert der Empfangscode nur schon vorhandene UART-Bytes an. gps_2 enthaelt
die neuen Zaehler, meldet aber noch Version 0.1.0: vor S3 alle sechs Module
konsistent aktualisieren, calibration.json erhalten, Soft-Reboot. **Aktueller
Sensorstarter: 0.2.0 mit vollstaendigem RAM-Log.** Folgende S2-Anleitung bleibt
fuer spaetere Wiederholungen erhalten.

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
   Ab 0.1.1 zeigen gga_fix_sentences/rmc_fix_sentences, ob jemals gueltige
   einzelne Fixsaetze empfangen wurden; max_satellites_used ist das Maximum
   benutzter Satelliten aus GGA. Das sind Laufzaehler, kein aktueller Fix.
   Viele poll_gaps koennen die Beobachtung trotz sauberem Datenstrom zerstoeren;
   errors={} allein bestaetigt weder Fix noch ausreichend kurze Pollzeiten.
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

**S3 funktional bestanden am 2026-10-20:** 172.972 s, vom Besitzer mit Ctrl+C
beendet, gemeinsamer Betrieb ohne protokollierte Sensorfehler/Pollpausen.
Der Lauf meldet noch 0.1.0 / Schema 1: nur letzte 40.963 s im 200-Zeilen-Ring.
Die neue 0.2.0-Vollaufzeichnung ist damit noch nicht physisch validiert.
Hoehenspruenge trotz ebenem Wegabschnitt im finalen Einbau weiter pruefen.
[Auswertung und Nachweisgrenzen](testdaten/S3_gps_and_baro/AUSWERTUNG.md).
Die folgende Anleitung gilt fuer einen neuen Bodenlauf, nicht rueckwirkend fuer
die gespeicherten alten Dateien.

Nach S1/S2 beide Sensoren anschliessen und denselben Aussenversuch wiederholen.
Vorher sechs Module aktualisieren, Soft-Reboot und Version **0.2.0** pruefen.
BEC/Receiver/Servos bleiben aus; nur MCU/Sensoren ueber USB:

```python
import sensor_test
sensor_test.run('both', duration_s=180)
```

GPS-Fix und neue Barometerdaten sollen gemeinsam bestehen bleiben. Genau diese
Dateipaare und deine physische Beobachtung sichern, dann die MANUAL-Integration
planen. Diese Sensortests erzeugen keinerlei Servo-PWM und messen keinen MANUAL-
oder STABILIZE-Regelkreis. Ihre Laufzeiten sind nur die des Sensorstarters.
Nach Fix etwa 10..20 m gehen und zurueck, Barometer langsam anheben/absenken.
Die 180 s werden nun vollstaendig mit 2 Hz gespeichert; in neuem S3-Ordner sichern.

## Stop, Dateien und Grenzen

Lauf endet nach der angegebenen Zeit oder mit Ctrl+C. Auf **beide** Meldungen
Sensor-CSV gespeichert / Sensor-JSON gespeichert warten. USB bleibt zum Download
angeschlossen; BEC bleibt aus. Unterordner pro Lauf auf dem Mac verwenden.
Dateinamen sensors_<ticks>_<index>.csv/json werden nicht wiederverwendet.

- CSV ab 0.2.0: **ganzer kurzer Lauf mit 2 Hz**, gleiche 25 Spalten.
  Der alte 200-Zeilen-Ring galt nur fuer 0.1.x. Nicht mit Flashplatz verwechseln:
  Dateien loeschen vergroessert einen RAM-Ring nicht. Noch kein MANUAL-Fluglog.
- Kompakter Puffer: 83 Bytes/Sample, fuer 180 s ca. 30 kB, fuer 300 s ca. 50 kB.
  Dauer/Rate werden vor Hardwarestart reserviert; maximal 65536 Bytes und
  32768 Bytes geplanter RAM-Reserve. Zu grosser Lauf/zu wenig gemeldetes RAM:
  klare Fehlermeldung vor Start, keine stillen Verluste oder abgesenkte Rate.
  Dann Dauer/log_hz bewusst reduzieren. Die Reserve ersetzt keine MCU-Messung.
- JSON: Konfiguration, Runtime, Fehlerphase/Text, GPS-Zaehler, erste vier gueltige
  NMEA-Saetze, PROM, Startdruck, Messanzahl und Timingstatistik des ganzen Laufs.
- JSON-Schema 2: log.storage, capacity, record_bytes, allocated_bytes,
  free_before_bytes, reserve_bytes und all_samples_retained. Letzteres bestaetigt
  den Erhalt erfasster Samples, nicht zwingend volle Laufdauer oder GPS-Gueltigkeit.
  UTC steht im CSV nun mit drei Nachkommastellen. Stromverlust verliert RAM-Daten.
- Leere CSV-Zahlen bedeuten unbekannt/ungueltig, Alter -1 bedeutet unbekannt.
  Frische bezieht sich auf Softwareempfang, nicht auf einen Hardwarezeitstempel.
- GPS nach Pollpause >100 ms: Altdaten verwerfen, neue Saetze verlangen. Kein
  Warten auf Fix im Regelkreis; ADC-Konvertierungen brauchen jeweils bis 9.04 ms
  und werden hier ueber getrennte Pollaufrufe abgewartet.
- Fehler werden fuer diesen Sensor verriegelt und mit Phase/Text gespeichert.
  Ein Sensorfehler darf nicht still durch einen alten Wert als frisch ersetzt werden.

Hoststand 0.2.0: 131 Tests bestanden (96 Steuerungs- und 35 Sensortests),
einschliesslich neuer 180-Grad-Montage-/Kalibrierungsregressionen.
Das bestaetigt Parser/Mathematik/Testablauf, keine physische Sensorfunktion.

Rohlogs bleiben normalerweise ausserhalb Git; ausgewaehlte Nachweise spaeter
mit Auswertung versionieren. Bei unvollstaendigem Export beide Dateien pruefen,
keinen vollstaendigen Lauf behaupten. Erster GY-63-Lauf liegt seit 2026-10-19 vor:
60.002 s, 594 Messungen, Adresse 0x77, CRC korrekt, keine protokollierten Fehler.
Druck/Temperatur plausibel. Besitzer bestaetigt Anheben von Hawk im selben Lauf
mit ungefaehr passender positiver Hoehenaenderung: **S1 funktional bestanden**
aus Logpruefung und Besitzerbeobachtung. Absolute Genauigkeit/Drift nicht
quantifiziert. Die GPS-Wiederholung gps_2 samt Konsole bestaetigt Fix und
Bewegungsreaktion; S2 und gemeinsamer S3 funktional bestanden. Der separate
USB-Startbefund wird dadurch nicht geklaert.
[Auswertung und separater USB-Startbefund](testdaten/barometer_tests/AUSWERTUNG.md).

## Danach: MANUAL-Flugdaten vorbereiten

Naechster Codeumfang nach bestandenem S1/S2/S3: Sensorpolling begrenzt in den
bisherigen MANUAL-Ablauf integrieren, gemeinsame Zeitbasis fuer IMU/RC/Ausgaenge/
GPS/Barometer und ganze Fluege aufzeichnenden Speicherweg implementieren. Den
Mehraufwand am Boden messen; keine blockierenden ADC-Wartezeiten in app.run().
Der neue vollstaendige Sensorpuffer enthaelt noch keine IMU/RC/Servo-Daten und
ist nicht der Fluglogger. Ein gepackter RAM-Puffer fuer
z.B. 5 min bei 1 Hz plus fortlaufende Zeit-/Fehleraggregate ist
ein moeglicher erster Entwurf; den RAM-Bedarf auf dem MCU messen. Noch nicht
implementiert. Speicherrate, Flugdauer und Medium bewusst festlegen;
Flash-Schreiben mit aktiver Steuerung ist im aktuellen
Regelkreis weiterhin ausgeschlossen. Deshalb ist S3 noch kein sofortiger Flugstart.
Konkrete Anschluesse, Montage und Loggeraufgaben:
[Einbau-/MANUAL-Arbeitsplan](EINBAU_UND_MANUAL_DATENFLUG.md).

Danach manuell Daten sammeln, Zeiten/Fehler und Datenqualitaet bewerten, dann
naechsten Schritt waehlen. Ein autonomer Kreis benoetigt zusaetzlich Kreis-/Kurs-
fuehrung, gueltige Sensorzustände, Modus-/Uebernahmeverhalten und eine passende
Nick-/Geschwindigkeitsstrategie. GPS und Barometer allein implementieren das nicht.

## Primaerquellen

- [MicroPython struct](https://docs.micropython.org/en/v1.29.0/library/struct.html),
  [gc](https://docs.micropython.org/en/v1.29.0/library/gc.html): gepackte Puffer und RAM-Abfrage.

- [Beitian BN-180](https://www.beitian.com/sys-pd/9.html): Modul-/Schnittstellenangaben.
- [TE MS5611-Datenblatt](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet): Kompensation, I2C, Wandlungszeit.
- [Hersteller-Appnote AN520, AMSYS-Archiv](https://www.amsys-sensor.com/downloads/notes/MS5XXX-C-code-example-for-MS56xx-MS57xx-MS58xx-AMSYS-an520e.pdf): CRC und Testvektor; deren MS5607-Formeln nicht fuer MS5611 uebernehmen.
- [u-blox 8/M8 Protokoll](https://content.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf): NMEA-GGA/RMC und Einheiten.
- [MicroPython RP2](https://docs.micropython.org/en/v1.29.0/rp2/quickref.html),
  [UART](https://docs.micropython.org/en/v1.29.0/library/machine.UART.html),
  [I2C](https://docs.micropython.org/en/v1.29.0/library/machine.I2C.html): Schnittstellen auf der gemeldeten Runtime.
