# Gemeinsamer MANUAL-Logger: 0.1.9 mit Bordstart und GPS getestet

**Aktueller Befund:** B1 zweimal sowie SENSOR/MANUAL draussen mit GPS-Fix
funktional bestanden. Alle Laeufe ohne Fault/Timing-Trip, mit BOOT-Start und
sauberem Export. MANUAL nach Startfreigabe ohne erneute RC-Sperre, maximal
45.656 ms; zwei Segmente mit187 Samples vollstaendig. Besitzer bemerkte keinen
Aussetzer. [Auswertung](testdaten/fluglogger/AUSWERTUNG_019.md).
Kein weiterer Firmwarewechsel noetig. Zehn Minuten Aufnahme bleiben offen:
MANUAL-Gesamtlauf4 min26 s, davon nur3 min10 s Aufnahme.201 Hosttests im letzten
Firmwarelauf bestanden; keine pauschale Garantie aus diesen Bodenlaeufen.

## Jetzt konkret: nur noch den Zehn-Minuten-Aufnahmelauf ergaenzen

Logger0.1.8 ist als8b9adde gesichert. Auf ausdruecklichen Besitzerwunsch bleiben
wir auf codex/manual-flight-logger.0.1.9 ergaenzt nur den optionalen bewussten
Bordstart;201 Hosttests bestehen, Bedienung/Reserve jetzt auch auf dem Board
bestaetigt. BEC-Spannungsqualitaet wurde nicht gemessen.

Keine erneuten B1-/SENSOR-/kurzen MANUAL-Versuche erforderlich. Auf dem Board
den funktionierenden0.1.9-Stand beibehalten, LOGGER_BOOT_MODE='manual',
AUTO_START=False. Im endgueltigen Einbau nach der folgenden Folge insgesamt
etwa10 min aufnehmen. Fuer USB weiterhin die5-V-Verbindung zum MCU trennen,
nicht nur Batterie ausschalten; [Bordstart-/Versorgungsfolge](BORDSTART_LOGGER.md).
Vorherige F3-Dateien behalten, neuen Lauf in eigenem Unterordner sichern.

Anschliessend F3 am Boden mit unveraenderten Gains/Zeichen:

1. Drauessen nach normaler Gyro-Ruhekalibrierung MANUAL/Neutralfreigabe und
   dauerhaft gruene GPS-Bereitschaft abwarten. CH3 bleibt zunaechst unten.
2. CH3 oben, etwa5 min aufnehmen; normale kleine Steuerbewegungen.
3. CH3 unten, etwa10 s weitersteuern: Pause ohne Export/PWM-Stop.
4. Erneut oben fuer etwa5 min, danach unten und BOOT2 s. Das ist eine
   Testdauer, kein neuer automatischer Abschalttimer im Programm.
5. Export abwarten, danach Versorgung abschalten. CSV/JSON/Konsole unter
   docs/testdaten/fluglogger/F3_gps_dauer_019/ sichern. Bei Aussetzer/Fehler
   vorher sauber abbrechen. Keine Stromverlustversuche.

Ziel: zwei vollstaendige Segmente ohne Fault/RC-Sperre, gueltige frische GPS-
Positionen und IMU-/Barowerte, kein full und sauberer Export nach etwa10 min
Aufnahme. GPS-Datenlast mit Fix ist im kurzen0.1.9-Aussenlauf abgedeckt; zehn
Minuten Gesamtspeicherung noch nicht. Steuerschrittigkeit/gefuehlte Latenz zusaetzlich als Beobachtung
notieren;1-Hz-Daten messen keine schnellen Reaktionen.

L3 0.1.4 hat bestanden: 91008 B in 40 Bloecken, Inhalt geprueft, nach allen
Imports noch 68656 B frei. Das ist eine RAM-Vorprobe, kein Lauf mit den echten
Sensor-/PIO-/PWM-Objekten. Kein weiteres isoliertes L3 notwendig.
[Rohbefund](testdaten/logger_boden/AUSWERTUNG_L3.md).

Besitzerwahl: erste MANUAL-Basisdaten mit **1 Hz**, BOOT bleibt erreichbar.
Der erste gemeinsame SENSOR-Lauf ist ausgewertet: CH3/BOOT/Export funktionieren,
aber neun Schleifenabstaende >50 ms setzen TIMING. GPS lieferte am Fenster
keinen Fix. [F1-Auswertung](testdaten/fluglogger/F1_sensor/AUSWERTUNG.md).
0.1.1 ergaenzt diese Diagnose ausschliesslich im Logger-SENSOR-Profil.
Die bestehenden 50-ms-Grenzen und Neutralfreigaben bleiben erhalten.
Der [0.1.1-Diagnoselauf](testdaten/fluglogger/F1_timing/AUSWERTUNG.md) zeigt
17 Zeitueberschreitungen, verteilt auf mehrere Phasen. GC ist eine plausible,
unbewiesene Ursache. 0.1.2 entlastet GPS mit wiederverwendetem Snapshot und
Bytezaehlung je Block. startup_gc_us misst die ohnehin vorhandene Bereinigung
beim Start. [0.1.2 ist ausgewertet](testdaten/fluglogger/F1_vergleich_012/AUSWERTUNG.md):
sieben Trips in 90.734 s statt 17 in 60.162 s, maximal 51.355 ms. Noch nicht
behoben. Barometer diesmal ohne den alten 15-m-Sprung. Start-GC 23.898 ms.
0.1.3 plant Bereinigung nach kurzen Iterationen bei <32 KiB frei; automatische
GC, Startreserve und 50-ms-Grenze bleiben bestehen.
**0.1.3 ist fehlgeschlagen:** GPS-MemoryError, orange Warnung, kein Segment.
Die Heap-Abfrage verhinderte ihre eigene GC-Freigabe. 0.1.4 prueft das Budget
vorher, fragt nur alle 200 ms ab und merkt bereits faellige GC ohne neuen
Heapscan. [Befund](testdaten/fluglogger/F1_gc_013/AUSWERTUNG.md).
Autostart bleibt aus; main.py und gespeicherter START_MODE bleiben unveraendert.
Noch kein selbststaendiger Bordstart ohne Thonny. Flugfreigabe ist das nicht.

## Abgeschlossen: F2-Vergleich am Tisch mit 0.1.8

1. Gegenueber 0.1.7 **nur config.py** auf dem MCU ersetzen;
   calibration.json erhalten. AUTO_START=False, keine neue RC-/Lagekalibrierung.
   Bei ausgeschalteten Quellen Befestigung, Masse und Ruderfreiheit pruefen.
   MCU/alle Sensoren zuerst normal versorgen, danach BEC/Empfaenger/Servos
   fuer diesen beaufsichtigten Tischtest. Sender an, neutral, CH3 unten.
2. Soft-Reboot, danach nur:

   ```python
   import flight_start
   flight_start.run('manual')
   ```

   Hawk waehrend der Gyro-Ruhekalibrierung unbewegt halten und
   MANUAL-/Neutralfreigabe abwarten. Startmeldung muss Logger 0.1.8 zeigen.
3. CH3 oben, etwa30 s alle Ruder neutral lassen. Hawk waehrend des ganzen
   Tests ruhig liegenlassen; danach normale kleine Bewegungen aller Ruder,
   insgesamt **4-5 Minuten** aufnehmen. Ein Segment genuegt. Beim ersten
   Messbereichsfehler, TIMING, Aussetzer oder Orange sauber stoppen/sichern.
   Keine Endanschlaege erzwingen oder Stromausfaelle nachstellen.
4. CH3 unten, BOOT zwei Sekunden halten, Speichermeldungen/Tuerkis abwarten,
   erst dann abschalten. JSON, CSV und Konsole unter
   docs/testdaten/fluglogger/F2_gc_018/ sichern, alte Daten behalten.

Erwartete Diagnose: stage_timing mit neun Phasen statt null. Der langsamsten
Periode ist preceding_stages_us der vorigen Iteration zugeordnet (IMU/Lage,
RC/Regler/PWM, Diagnose, BOOT, GPS, Barometer, CH3, Record/LED, Rest/GC).
Auch ohne erneuten Trip hilft die Verteilung der Laufzeiten. RAM-Reserve
bleibt 65536 B; bei Startabbruch Konsole sichern und Reserve nicht verkleinern.
197 Hosttests bestehen; Schutz-/Neutralfreigabe und Zeitgrenze bleiben erhalten.
runtime_gc sollte nun regelmaessige geplante Bereinigungen statt nur vier im
gesamten Lauf zeigen; massgebend bleiben keine TIMING-Trips/Steuerunterbrechungen
und saubere Sensor-/Exportdaten. Haeufigere Abfragen kosten ebenfalls Zeit.
Seit0.1.7 im JSON: imu_first_saturation_raw mit sieben signed Rohwerten
(ax,ay,az,Temperatur,gx,gy,gz), oder null. Der erste auffaellige Satz bleibt
auch nach Erholung gespeichert. Saettigungsgrenzen bleiben gleich; die Ursache
bei ruhendem Hawk wird anhand des Rohsatzes eingegrenzt.

Der beobachtete Steueraussetzer trat im0.1.8-Vergleich nicht mehr auf.
GPS-Fix/Gruen, etwa zehn Minuten Aufnahme sowie
Bordversorgung/BOOT-Start sind jetzt implementiert, physisch noch offen. AUTO_START=True startet
in main.py den bisherigen Controller, nicht den Logger. USB-Abziehen verliert
bei USB-Versorgung RAM; BEC-/USB-5-V-Quellen nicht parallel verbinden.

## Was diese Version tut

- flight_start reserviert zuerst 632 * 144 B, dann importiert er Fluglogger/app.
  Explizites run('sensor')/run('manual') oder optionaler BOOT-Bordstart;
  kein Start beim Import. LOGGER_BOOT_MODE=None ist der Standard.
- CH3 unten (998 us) pausiert, oben (1998 us) startet ein neues Segment.
  200 ms bestaetigen, beim Start zuerst unten; Mitte behaelt den Zustand.
- Keine Aufnahmezeitgrenze. Volle Kapazitaet stoppt nur Aufnahme, kein
  Ueberschreiben. Ereignisse nutzen dieselben Slots: 600 Sekunden bei 1 Hz
  plus etwa 32 Ereignisse sind die Dimensionierung, keine unbegrenzte Kapazitaet.
- Sensoren/RC/MANUAL werden weiterhin im normalen Loop bedient. 1 Hz betrifft
  nur gespeicherte Gesamtdatensaetze, nicht die Abfrage-/Servofrequenz.
- CH3-Verlust beendet nur Aufnahme, erneuter Start verlangt unten->oben.
  Eigener PIO-Index 3, getrennte Frischebewertung von Roll/Nick/Gier auf 0/1/2.
- BOOT im laufenden Programm erst loslassen. Nach Landung CH3 unten und
  **BOOT zwei Sekunden halten**. Bei laufender Aufnahme wird der Druck ignoriert.
  Das ist eine bewusst am Boden bediente Abschaltung, keine Flugzustandserkennung.
- Erst PWM, Steuer-PIO, CH3-PIO und UART schliessen, dann CSV/JSON schreiben.
  CH3 unten loest niemals einen Export aus. RESET/Stromverlust speichert nichts.
- Kein Flash im Loop. BOOT-Abfrage, LED, Sensoren und Packen werden als Arbeit
  mitgemessen; die bestehenden Zeitfehlerreaktionen bleiben aktiv.
- Nach Aufbau von App/RC/Zusatzsensoren und vor erster PWM mindestens 65536 B
  freie RAM-Reserve nach GC verlangen. PWM-Objekte entstehen erst nach Neutral-
  freigabe; deren spaeterer Bedarf/GC-/Loopzeiten gehoeren zum MANUAL-Bodencheck.
- Sensor-/Aufnahmefehler sind sichtbar. Fehler des Loggers stoppen Aufnahme;
  bestehende Steuerungsfehlerreaktionen gelten weiterhin. Eine blockierte MCU
  wird dadurch nicht zu einem unabhaengigen MANUAL-Pfad.

## LED am RP2040-Zero

| Anzeige | Bedeutung |
| --- | --- |
| Violett dauerhaft, vor Start | Bordstart wartet auf bewussten BOOT-Druck |
| Weiss, vor Start | BOOT bestaetigt; loslassen, dann Gyro-Kalibrierung ruhig abwarten |
| Rot dauerhaft | Keine Aufnahme, GPS noch nicht bereit |
| Gruen dauerhaft | Keine Aufnahme, GPS bereit |
| Rot/Gruen blinkend, etwa 2 Hz | Aufnahme, GPS entsprechend nicht bereit/bereit |
| Orange schnell blinkend | Voller Puffer oder Komponenten-/Loggerfehler; JSON pruefen |
| Blau nach BOOT-Stop | Export laeuft, Versorgung behalten |
| Tuerkis dauerhaft | CSV und JSON geschrieben und sync abgeschlossen |
| Rot nach Exportfehler | Daten gegebenenfalls noch im RAM; nicht resetten/ausschalten |

Diese Farben bilden GPS-/Aufnahme-/Komponentenstatus ab, nicht alle
Steuerungsfaults: ein TIMING-Fault kann auch ohne orange Anzeige vorliegen.
Konsole und JSON diagnostics deshalb ebenfalls pruefen.

Bereit: fuenf unterschiedliche, aufeinanderfolgende gueltige GGA/RMC-Epochen,
mindestens sechs benutzte Satelliten, HDOP <=2.5, Datenalter <2500 ms.
Bei kurz gemischten GGA/RMC-Epochen bleibt das letzte kohärente Paar mit seinem
echten Alter erhalten; No-Fix/Stale macht es ungueltig. Das ist eine
Empfangsqualitaetsanzeige, kein Nachweis vermessener Positionsgenauigkeit.
Aufnahme ist auch ohne GPS moeglich und dokumentiert dann fehlende Koordinaten.

Grundlagen: [Waveshare-Schaltplan, WS2812B an GPIO16](https://files.waveshare.com/upload/4/4c/RP2040_Zero.pdf),
[MicroPython NeoPixel](https://docs.micropython.org/en/v1.25.0/library/neopixel.html),
[BOOTSEL API v1.29](https://docs.micropython.org/en/v1.29.0/library/rp2.html#rp2.bootsel_button).
BOOTSEL-Abfrage deaktiviert kurz Flashzugriff/Interrupts; Dauer muss im
Gesamtlauf geprueft werden. LED ist ein NeoPixel, kein einfaches Pin-an/aus.

## F1 jetzt konkret: Sensoren, CH3 und Speichern ohne Servo-PWM

1. Bei abgeschalteten Quellen alle **Servoversorgungen trennen**. Fuer CH3
   braucht der Empfaenger BEC und gemeinsame Masse; Servos bleiben stromlos.
   MCU per USB, keine zweite 5-V-Quelle parallel an USB/VBUS. IMU/GY-63 normal
   mitversorgen oder vollstaendig trennen, keine unversorgte IMU an SDA/SCL lassen.
   Fuer diesen gemeinsamen Lauf werden alle drei Sensoren normal versorgt.
2. **Alle Pythondateien aus firmware/** konsistent hochladen, darunter neu
   flight_start.py, flight_logger.py und flight_records.py sowie die geaenderten
   app.py/receiver.py/config.py. **calibration.json erhalten**. Keine neue
   RC-/Lagekalibrierung fuer diesen Codewechsel. Sensorachsenzuordnung nur
   anpassen, wenn die IMU tatsaechlich ummontiert wurde; dann Richtungen neu pruefen.
3. AUTO_START=False, Soft-Reboot. Danach nur:

   ```python
   import flight_start
   flight_start.run('sensor')
   ```

   Nicht vorher app/flight_logger/sensor_test importieren: sonst geht die in L3
   bestaetigte fruehe Reservierung verloren. Standard run() waehlt ebenfalls sensor.
4. Hawk fuer die vorhandene Gyro-Ruhekalibrierung etwa sechs Sekunden unbewegt
   halten. Diese Kalibrierung schreibt keine calibration.json. Sender/Empfaenger
   an, CH3 unten. Konsole muss SENSOR zeigen; es entstehen **keine Servo-Pulse**.
   Startup meldet freien RAM nach echten Objekten. Scheitert Reserve/Import:
   komplette Konsole sichern, keine Reserve verkleinern und kein MANUAL starten.
5. Draussen auf dauerhaft Gruen warten (mehrere neue Fixepochen nach erstem Fix).
   CH3 nach oben, etwa 10-15 s sammeln: Gruen blinkt. Hawk vorsichtig bewegen
   oder ein paar Meter gehen; Sensor-/GPS-Reaktion ist dadurch im Log sichtbar.
6. CH3 unten, etwa 5-10 s pausieren: dauerhaft Gruen, **kein Export/Programmende**.
   Dann erneut oben fuer etwa 10-15 s: neues Segment, blinkend.
7. CH3 unten bestaetigen lassen, BOOT zwei Sekunden halten. Nicht RESET druecken,
   nicht beim Einschalten BOOT halten. Blau beim Speichern, danach Tuerkis und
   beide Speichermeldungen in Thonny abwarten. Erst dann BEC/Empfaenger aus.
8. flight_*.csv und zugehoerige flight_*.json bei weiter verbundenem USB in
   docs/testdaten/fluglogger/F1_sensor/ kopieren. Danach USB trennen. Konsolenausgabe
   mit sichern, besonders bei Fehlern. Nie denselben Rohbericht ueberschreiben.

Erwartet: shutdown_ok=true, stop_reason=ground_button, segments=2, kein full,
errors leer, zwei Datenabschnitte mit Pause im Zeitverlauf, alle servo_* Werte 0,
keine STABILIZE-Ausgabe. Fehlende GPS-/Hoehenwerte vor Bereitschaft sind explizit
fehlend. Die Laufzeit bestimmt der Besitzer; die obigen Zeiten sind Bedienbeispiele.
Historisch zeigten die ersten Laeufe TIMING. Der aktuelle gezielte Indoor-Lauf
0.1.5 hat keine Trips; Freiluft-GPS-Bereitschaft im gemeinsamen Logger bleibt offen.
`Zustand: SENSOR Fehler: -` bedeutet Modus SENSOR ohne Fault. Ein spaeteres
`Fehlerwechsel: TIMING` ist dagegen eine echte Zeitueberschreitung. Leere
Logger-errors im JSON bedeuten nicht automatisch eine fehlerfreie Steuerung.
Siehe [Befund und gezielter naechster Schritt](testdaten/fluglogger/F1_sensor/AUSWERTUNG.md).

## Weitere Loggerpruefungen nach F2

F2 prueft zunaechst MANUAL bei Aufnahme/Pause. CH3-Signalverlust, Puffergrenze
und BOOT-Abfrage/LED-Timing bleiben weitere gezielte Bodenpruefungen; sie sind
im kurzen F2 nicht automatisch mitgeprueft. Keine abrupten Stromverlustversuche
an montierten Rudern.

Danach Bordversorgung und bewussten Start ohne Mac nach BORDSTART_LOGGER.md testen,
erst dann erster MANUAL-Datenflug. AUTO_START nicht einschalten: main.py startet
weiter den bisherigen Controller, nicht den neuen Logger. Kein Mischen neuer
Gains, IMU-Umbau und Erstflug desselben Teststands.

## Daten und Grenzen

CSV hat 46 benannte Spalten; JSON sichert Version/Settings, bestehende
RC-/Lagekalibrierung, Sensor-PROM, Baro-Startdruck, GPS-Zaehler, Modus-/Fehler-
ereignisse sowie Timingaggregate jeder abgeschlossenen Iteration.
kind kennzeichnet sample/start/stop/channel_invalid/full/state. segment
verbindet zusammengehoerende Aufnahmeabschnitte. ms beginnt bei Logger-
initialisierung nach Gyro-Ruhekalibrierung, GPS-UTC steht zusaetzlich im Log.

IMU: Koerperwerte nach Achsentransformation/Offset, Beschleunigung in g,
Gyro in Grad/s; +Roll rechts, +Nick Nase runter, +Gier Nase links. Lage relativ
zur gespeicherten Waagerechtreferenz; yaw_relative ist kein absoluter Kompass.
Ungueltige IMU liefert leere Felder, niemals frisch datierte eingefrorene Winkel.
imu_age_ms ist die Zeit seit der letzten gueltigen erfassten Kontrolliteration.

GPS: Dezimalgrad (+Nord/+Ost), Hoehe MSL in m, Geschwindigkeit ueber Grund
in m/s, Kurs ab Nord im Uhrzeigersinn. Koordinaten als double, uebrige
Gleitkommawerte float32; keine zusaetzliche Genauigkeit gegenueber dem Empfaenger.
Baro: Pa, Grad C, Hoehe relativ zum gemittelten Startdruck (20 neue Werte nach
2 s); keine AGL-/Terrainmessung. Roh-ADC D1/D2 werden in diesem 144-B-Paket nicht
gespeichert; sie stehen weiter im separaten Sensortest zur Verfuegung.

valid_bits und status_bits sind Bitmasken; JSON listet Bitnamen in Reihenfolge
ab Bit 0. Fehlende Pulse 0, unbekanntes RX-/GPS-Alter -1, 32767 bedeutet
mindestens 32767 ms. baro_age_ms 65534 bedeutet mindestens 65534 ms, -1 unbekannt.
work_to_log_us endet vor dem Packen/LED-Update; die JSON-Workstatistik enthaelt
auch diese Arbeit. period_us ist der ganze Startabstand zur vorigen Iteration.
RX-Alter ist die konservative PIO-Schaetzung, kein exakter Capture-Zeitpunkt.
1 Hz ist fuer Basisflugweg/langsame Veraenderungen, keine schnelle Gain-/Schwingungsanalyse.

Bei Exportfehlern bleiben vorhandene Records in flight_start._pending erhalten.
Programm bleibt gestoppt; Versorgung nicht trennen und keinen Soft-Reboot.
Nach gezielter Behebung des Speicherproblems kann flight_start.save_pending()
mit neuer Dateinummer erneut exportieren. Ohne bestaetigte Hardwareabschaltung
ist dieser Aufruf gesperrt. Ein Neustart der Aufnahme ueberschreibt keine
ungesicherten Records. Stromverlust verliert weiterhin alle ungesicherten RAM-Daten.

Git: auf codex/manual-flight-logger bleiben. L3-Nachweise und Loggerprototyp
bilden einen pruefbaren Commit; F1/F2-Ergebnisse danach separat sichern.
Kein Merge mit main, bevor der kombinierte Stand dokumentiert getestet wurde.
