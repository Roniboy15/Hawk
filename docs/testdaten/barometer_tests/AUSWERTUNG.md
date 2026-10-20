# GY-63: erster Messlauf und separater USB-Startbefund

Eingang/Auswertung: 2026-10-19. Quellstand auf dem Host: bbdf934,
Branch codex/gps-baro-bringup. Kein vollstaendiges Archiv/Abgleich der MCU-
Quelldateien. Der Besitzer zeigte nachtraeglich die aktuelle main.py und meldet
AUTO_START=False; der Dateistand zum Ereignis bleibt unbekannt. Keine
Hardwarebefehle oder Servobewegungen durch die Auswertung.

## Ergebnis und Herkunft

Der Barometer-Messpfad funktioniert im vorliegenden Lauf: neue Messwerte,
gueltiges PROM, plausible Groessenordnung, kein protokollierter Fehler.
**S1 funktional bestanden:** Nachtrag des Besitzers am 2026-10-19: Hawk wurde
im selben Lauf angehoben; die angezeigte relative Hoehe stieg ungefaehr um
die tatsaechliche Hubhoehe. Das bestaetigt die physische Anheberichtung und
die Groessenordnung nach Besitzerbeobachtung, ergaenzend zum geprueften Log.
Absolute Genauigkeit, Drift und Wiederholbarkeit sind damit nicht quantifiziert;
ein externer Druckvergleich liegt nicht vor und war keine S1-Funktionsvoraussetzung.
GPS war laut Besitzer nicht angeschlossen; S2/S3 bleiben offen.

Unveraenderte Besitzerdateien: [baro.csv](baro.csv), [baro.json](baro.json).
JSON nennt als urspruengliche CSV sensors_324351_0.csv; das Paar wurde vom
Besitzer lokal umbenannt. Beide Dateien sind strukturell/in den Werten konsistent,
haben aber keine gemeinsame kryptografisch gesicherte Laufkennung.

SHA-256:

| Datei | Fingerprint |
| --- | --- |
| baro.csv | 2692900d8e161f51104dfa58cbb75a4bdef206313a40de10f745e565d0eead12 |
| baro.json | 36d696ca0f1158d9138a5b56cac088e51005fe9f636b95706500ceb9bbda4b8b |

## Verifizierte Logwerte

| Merkmal | Befund |
| --- | --- |
| Profil | baro, test_version 0.1.0, control_version 0.2.3-bench |
| Runtime | MicroPython v1.29.0, Waveshare RP2040-Zero |
| Bus / Adresse | I2C1, SDA GP10, SCL GP11, 100 kHz / 0x77 |
| Dauer / Ende | 60002 ms / duration, shutdown_ok=true, errors={} |
| Barometerwerte, ganzer Lauf | 594, im Mittel ca. 9.90 Hz |
| PROM / CRC | [0, 43184, 43535, 25309, 21882, 32676, 26938, 7] / CRC 7 korrekt |
| Startdruck | 96331.5 Pa = 963.315 hPa |
| CSV | 297 erzeugte Zeilen, letzte 200 gespeichert, 19623..59800 ms |
| Druck, gespeicherter Ausschnitt | 96322..96335 Pa |
| Sensortemperatur, Ausschnitt | 22.67..22.78 Grad C |
| Relative Hoehe, Ausschnitt | -0.31..+0.83 m; letzte Zeile +0.13 m |
| Gueltigkeit / Datenalter, Ausschnitt | alle 200 Barometerwerte gueltig, Alter 60..74 ms |
| GPS | erwartungsgemaess keine Daten; false-GPS-Checks sind im Profil baro kein Fehler |

Hostpruefung mit Python-Standardbibliothek und den reinen ms5611-Funktionen:
CSV-Schema (25 Spalten), Zeilenanzahl, streng steigende Zeit, Flags und PROM-CRC
geprueft. Alle 200 gespeicherten D1/D2-Paare ergeben exakt den gespeicherten
Druck und die Temperatur. Relative Hoehe stimmt innerhalb 0.01 m mit der
Hostrechnung ueberein; maximale Abweichung 0.00563 m. Zentimeterformatierung
und Runtime-Arithmetik begrenzen den Vergleich; eine zentimetergenaue physische
Hoehenmessung wird daraus nicht abgeleitet.

Zwischen etwa 40 und 56 s steigt die relative Anzeige zeitweise gegen +0.8 m
und kehrt anschliessend nahe zum Startniveau zurueck. Der Besitzer bestaetigt
eine Anhebung im selben Lauf mit ungefaehr passender Hoehenanzeige. Exakte
Hubhoehe und Bewegungszeitpunkte wurden nicht angegeben; die Zuordnung zu
diesem konkreten Zeitfenster bleibt daher eine Interpretation. Die gesamte
Spanne ist bei diesem bewegten Versuch kein reines Sensorrauschen. Kein
Referenzgeraet fuer absoluten Druck oder geometrische Hoehe vorhanden.

Timing des **separaten Sensorstarters**, ganzer Lauf:

- period: Mittel 10.095 ms, Maximum 23.925 ms, keine Ueberschreitung von 50 ms.
- work: Mittel 1.100 ms, Maximum 23.365 ms; 63/5939 Iterationen (1.06 %) ueber
  10 ms. Ursache einzelner Spitzen nicht durch diese Aggregate aufgeschluesselt.
- period.over_period zaehlt 5938/5938, auch kleine Ueberschreitungen des
  10-ms-Sollabstands. Das ist nicht gleichbedeutend mit ueberlasteter Rechenzeit.

Das misst weder den MANUAL-/STABILIZE-Regelkreis noch dessen Zusatzlast mit
Sensorintegration. Der CSV-Ring enthaelt die ersten ca. 19.6 s nicht; JSON-Aggregate
decken den ganzen Lauf, aber keine elektrischen Einschalttransienten ab.

## Besitzerbericht: Endausschlaege beim USB-Anstecken

Separat vom Messlauf berichtet und am 2026-10-19 praezisiert:

- BEC mit Kondensator und Empfaenger bereits versorgt, Sender eingeschaltet.
- Hoehen-/Seitenrudersignale an MCU GP6/GP7, nicht direkt am Empfaenger.
- Beim USB-Anstecken beide Ruder maximal ausgeschlagen und dort geblieben.
- Nach Kenntnis des Besitzers lief noch kein Programm; Thonny war offen.
- Bisherige IMU auf GP4/GP5 ohne Versorgung, Signal- und Masseleitungen
  angeschlossen. Neues GY-63 angeschlossen, GPS nicht angeschlossen.
- Nachtrag: aktuelle main.py vom Besitzer als Text uebermittelt, entspricht
  der Startlogik des Repositorys; config.AUTO_START laut Besitzer False.
  Er laedt jeweils die neuesten Dateien hoch, kann den Stand zum Ereignis
  aber nicht bestaetigen. Inhalt/Existenz einer boot.py nicht mitgeteilt.
- Kondensator nach Praezisierung des Besitzers: 1000 uF / 10 V, parallel am
  geregelten 5-V-Ausgang, Minus an GND-Leiste. Anschluss/Nennspannung damit
  plausibel, aber nicht elektrisch nachgemessen; kein Ursachennachweis.

Das ist ein neuer Startbefund, getrennt vom USB-Abziehen am 2026-10-18 und
von der Raum-/Steckdosenunterbrechung am 2026-10-12. Gemeinsame Ursache ist
nicht nachgewiesen. Ob die Servos Kraft gegen einen mechanischen Anschlag
ausuebten, aktuelle GND-/Kondensatorverdrahtung, Strom-/Spannungsverlauf und
GPIO-Pulse zum Ereignis sind ungemessen. Abschalten wurde empfohlen;
eine Bestaetigung der Abschaltung liegt bei Erstellung noch nicht vor.

### Quellbefund und Arbeitshypothesen

sensor_test importiert weder app noch outputs/IMU und richtet im baro-Profil
nur I2C1 auf GP10/GP11 ein. main.py im Repository startet bei AUTO_START=False
keinen Regler. Eine unversorgte IMU erzeugt ueber diesen Sensorstarter deshalb
keine berechnete Ruderkorrektur. Die jetzt uebermittelte main.py und gemeldete
AUTO_START-Einstellung passen dazu. Ein abweichender frueherer Dateistand oder
anderer Autostart zum Ereignis ist dadurch nicht ausgeschlossen; boot.py offen.

Am ehesten zu untersuchen ist der Signal-/Versorgungsuebergang:

1. Ohne gestartete Ausgabe gibt dieser Code keine laufenden Neutralpulse aus.
   Fehlende oder gestoerte Pulse sind kein Neutralbefehl. Einzelne Digitalservos
   koennen eine zuletzt angenommene Stellung halten; konkretes Servomodell und
   empfangenes Signal fehlen. Das erklaert noch nicht den ausloesenden Puls.
2. Bereits versorgte RX-Ausgaenge koennen Spannung an noch unversorgte
   MCU-Eingaenge legen. Das RP2040-Datenblatt begrenzt GPIO-Spannung relativ
   zu IOVDD (absolut maximal IOVDD+0.5 V). RX-Pegel/Schutzbeschaltung und eine
   tatsaechliche Rueckspeisung wurden hier nicht gemessen.
3. Eine unversorgte IMU bei verbundenen SDA/SCL kann je nach Pullups und
   Schutzbeschaltung rueckgespeist werden oder Signale belasten. Das ist ein
   zusaetzlicher Stoerpfad, kein bewiesener Ausloeser dieser Servoausgaenge.
4. Falsche/lose Signal- oder Masseleitung, Versorgungseinbruch und abweichende
   MCU-Startdateien sind nicht ausgeschlossen. Der Kondensator allein ist
   weder als Ursache noch als Schutz vor falschen Servopulsen nachgewiesen.

Keine Gain-/Vorzeichenaenderung und kein automatisches Boot-Neutral-PWM als
unbelegter Workaround. Ein erst spaeter startendes Programm kann die Zeit vor
seinem Start nicht absichern. Hinweise/Quellen und weitere Abklaerung:
[VERSORGUNG_WARNHINWEISE.md](../../VERSORGUNG_WARNHINWEISE.md).

## Konkrete Fortsetzung

1. BEC-/Servoversorgung aus, dann USB trennen. Nur spannungsfrei umstecken;
   Kondensator kann nach dem Trennen noch Ladung halten.
2. IMU wieder an ihre bisherige 3V3-/GND-Versorgung anschliessen oder fuer den
   reinen Barometertest vollstaendig abstecken. Nicht nur VCC entfernen und
   Signalleitungen am versorgten System belassen. GY-63 und IMU duerfen ihre
   3V3-/GND-Versorgung teilen; die I2C-Busse bleiben getrennt.
3. Fuer weitere Sensorlaeufe bleibt BEC/Empfaenger/Servo aus, nur MCU/Sensoren
   per USB betreiben. Aktuelle main.py/AUTO_START sind durch den Besitzertext
   geprueft; falls eine boot.py vorhanden ist, diese bei ausgeschaltetem BEC
   als Text pruefen. calibration.json erhalten. Bei künftigen Laeufen den
   tatsaechlichen MCU-Dateistand mit sichern. Kondensator wie berichtet am
   5-V-Zweig belassen; keine Verbindung zwischen BEC-Eingang und Ausgang.
4. S1 ist mit Logpruefung und Besitzerbeobachtung funktional abgeschlossen;
   keine Wiederholung allein wegen der zuvor fehlenden Rueckmeldung noetig.
   Als Naechstes GPS-Kabel-/Pegelzuordnung klaeren und S2/S3 ohne Servoversorgung.
5. Vor erneutem Test mit versorgten montierten Servos den Startbefund eingrenzen.
   Bleibt er offen, Signal-/Versorgungsuebergang mit geeigneter Messtechnik
   untersuchen, ohne die montierten Ruder erneut an Endanschlaege zu fahren.
   Keine absichtliche Wiederholung durch BEC-vor-USB oder Spannungsausfall.

Sensorentwicklung geht weiter. Dieser aktuelle Endausschlagsbefund betrifft
gezielt den naechsten Betrieb versorgter Aktuatoren; er ist keine neue
pauschale Sperre wegen der vom Besitzer bereits akzeptierten MCU-Abhaengigkeit.
