# Architektur und Weg zum autonomen Thermiksegler

## Jetzt implementiert

Die main.py bleibt klein. app.run() verbindet die Module; keine Hardware-
Initialisierung passiert beim blossen Import von app. Initialisierung und
PWM-Freigabe erfolgen erst beim Aufruf und nach expliziter Kalibrierung.

Sensor -> korrigierte Beschleunigung/Drehraten -> Quaternion-Lage ->
Solllage aus Sender -> Quaternionfehler im Koerperrahmen -> Sollrate ->
begrenzter PI-Drehratenregler -> Servotrim und Ausgangsgrenzen.

Koerperkonvention X-vor/Y-links/Z-oben: +Roll rechts, +Nick Nase runter,
+Gier Nase links. Das fruehere positive-Nick=Nase-hoch wurde in der Anleitung
korrigiert; Quaternion-/Gyrorechnung und Level-Schema 1 bleiben unveraendert.
SENSOR/MANUAL dienen der physischen Vorzeichenpruefung. STABILIZE verlangt
alle aktiven Achsen in DIRECTION_CHECKED_AXES, bevor Hardware startet.

Der Filter ist Mahony-artig ohne Bias-Integrator und kein EKF. Die
Beschleunigung wird nur nahe 1g und mit begrenzter Innovation zur Korrektur
verwendet. Das verhindert nicht jeden Fehler durch Kurvenflug/Vibrationen.
Yaw ist relativ zum Start, driftet und wird nicht als absoluter Kurs geregelt.

Der aeussere Roll-/Nickregler benutzt den kuerzesten Quaternionfehler,
statt Euler-Winkelraten direkt mit koerperfesten Gyroachsen gleichzusetzen.
Winkelsollwerte werden trotzdem mit Euler-Roll/Nick vorgegeben: Nick nahe
90 Grad liegt ausserhalb dieses Boden-Reglers. Keine Kunstflugregelung.
Roll alleine darf ueber 70 Grad gehen; der alte dauerhafte Winkelabbruch entfällt.
Pitch >75 Grad ergibt softwareseitigen manuellen Ersatz, nicht Neutral-Lock.

## Betriebsmodi

| Zustand | Verhalten |
| --- | --- |
| SENSOR | Keine Servopulse; Messung/Anzeige |
| WAIT_NEUTRAL | Vor erster Aktivierung keine Pulse; nach RX-Ausfall Trim-Neutral |
| MANUAL | Kalibrierte Senderkommandos auf begrenzte Servoausgaenge |
| STABILIZE | Roll/Nick-Sollwinkel, optional Gier-Sollrate |
| MANUAL_FALLBACK | Bei Automatikfehler manuelle Senderkommandos, Fehler verriegelt |
| RX_TIMEOUT | Servo-Trimneutral; Wiederfreigabe nach gueltigen Neutralframes |

Trimneutral kann je nach Flugzeug ungeeignet als Funkverlustverhalten sein.
Dies ist ein Boden-Testzustand, kein fertig definierter Flug-Failsafe.
Es gibt weder einen in-flight Mode-Schalter noch einen Hardware-Bypass.
Ein Softwarefallback hilft nicht, wenn MCU oder Bus blockieren. Besitzerentscheidung
2026-10-18: dieses Risiko fuer geplante MCU-MANUAL-Datenfluege akzeptieren,
Sensorentwicklung fortsetzen und anhand der Messdaten neu bewerten. Ein
unabhaengiger Rueckweg bleibt eine Empfehlung, kein neu erfundener Stop fuer
Sensorarbeit. Eine autonome Kreisfunktion ist separat zu implementieren.

## Zeitverlust und RC-Alter (v0.2.1)

Der PIO-FIFO liefert Pulsbreiten ohne Capture-Zeitstempel. Bei normalen Polls
wird der vorige Poll als konservative Zeituntergrenze gespeichert. Das kann
einen Puls etwas frueher als noetig ablaufen lassen, aber Lesen macht ihn
nicht kuenstlich jung. Nur der FIFO-Snapshot wird gelesen; neue Worte bleiben
fuer den naechsten Poll. Der unverknuepfte FIFO hat vier Worte; ein voller FIFO
wird wegen moeglicher verworfener neuerer Pulse nicht als frischer RX akzeptiert.

Beim ersten Poll, einer negativen Tick-Differenz oder einer Pause ueber dem
Pollbudget werden PIOs gestoppt, FIFO-Worte verworfen und Capture neu gestartet.
Neue vollstaendige Pulse sind danach erforderlich. Das Pollbudget wird aus
MAX_LOOP_US abgeleitet; RX_TIMEOUT_MS muss groesser sein. ticks_diff behandelt
normalen Zaehlerumlauf; Stillstand ueber die halbe Tickperiode bleibt mehrdeutig.

Die App prueft Startabstand, Laufzeit nach Sensor-/RC-Zugriff und vor PWM-Ausgabe.
Erkannte Zeitueberschreitung verriegelt TIMING, verwirft RC, setzt die Freigabe
zurueck und schreibt Trimneutral, sofern PWM bereits aktiv ist. Vor der ersten
Freigabe bleiben Pulse aus. Erst neue Neutralframes erlauben MANUAL_FALLBACK;
STABILIZE bleibt bis zum Neustart gesperrt. Ein dauerhaft blockierender Zugriff
kann weiterhin nicht von dieser Schleife unterbrochen werden.

Abschalten versucht jede PWM-Achse und jeden PIO auch nach einem Fehler.
PWM versucht Duty=0, deinit und GPIO-low jeweils separat. Teilweiser Startabbruch
oder Aufraeumfehler verbieten den Logexport und die Erfolgsmeldung. Diagnose
erfolgt nach den Ausgangs-/Abschaltversuchen. Dies bleibt Software, kein Bypass.

MicroPython-API-Bezug: [StateMachine](https://docs.micropython.org/en/latest/library/rp2.StateMachine.html),
[PIO/FIFO](https://docs.micropython.org/en/latest/library/rp2.html),
[Tick-Arithmetik](https://docs.micropython.org/en/latest/library/time.html),
[PWM](https://docs.micropython.org/en/latest/library/machine.PWM.html).
Die v0.2.3-Laufberichte dokumentieren MicroPython v1.29.0 / RP2040-Zero.

v0.2.2 ergaenzt Startphasen-Tickzeiten und Gyroachsen/Gier-Sollrate in den CSV-Logs.
CSV-Auswerter muessen den Header lesen; Winkelzeichen und Kalibrierdatei bleiben
kompatibel. Optional ausgewaehlte RC-Kalibrierachsen bewahren vorhandene Kanaele
und Levelreferenz. Alle drei Achsenfunktionen sind seit 2026-10-13 vom Besitzer
bestaetigt, RX-/Servozeichen jeweils -1/-1. Der gespeicherte Stand bleibt SENSOR,
AUTO_START=False; die Richtungsbestaetigungen bleiben erhalten. Versorgung und
Fehler-/Timingqualifikation sind separat offen; siehe
[Testbericht](TESTBERICHT_2026-10-13.md) und [naechste Schritte](NAECHSTE_SCHRITTE.md).

## Tischtest-Diagnose (v0.2.3)

diagnostics.py sammelt min/max/Mittelwerte und Zaehler statt komplette 100-Hz-
Verlaeufe: period ist der Abstand zweier Iterationsstarts inklusive vorheriger
Diagnose, Statistik, sleep und Scheduler; pre_output bis unmittelbar vor write();
write ist die Outputs.write()-Dauer; work reicht von Start bis nach Konsole/CSV-
Formatierung, ohne anschliessenden Statistik-Update und sleep. Erster Startabstand
wird nicht als volle Periode gewertet. Abgebrochene letzte Iteration ist markiert.

CSV bleibt 200 Zeilen, jetzt 30 Spalten; zusaetzliche Zustandszeilen werden sofort
auch zwischen 10-Hz-Samples gespeichert und verkuerzen ggf. den Ringzeitraum.
RX-Pulse/konservative Alter/Sequenzen, Gate und Ausgabedauer sind enthalten.
0-Pulse bedeuten "keine Ausgabe/Eingabe", -1 bei Alter/Zeit "unbekannt/nicht aktiv".
Die bis zu 64 Ereignisse halten Modus/Fault/PWM/Freigabe/RX/Servo-Kommandos.
Zeitmaxima und Modus-/Faultzaehler umfassen jede abgeschlossene Iteration und
gehen beim Ueberschreiben von CSV/Ereignissen nicht verloren. Kein Flash im Loop.

Nach bestaetigter PWM-/PIO-Abschaltung exportiert die App CSV plus JSON mit
verwendeter Konfiguration, Kalibrierung und Runtime. JSON ersetzt keine Code-
Sicherung oder Messung am GPIO. Ein langsamer Print kann erst bei Rueckkehr bzw.
naechster Iteration erkannt werden; permanente Blockade bleibt unbeherrscht.
Erfassung kostet RAM/CPU und muss auf dem Board gemessen werden. API:
[ticks_diff](https://docs.micropython.org/en/latest/library/time.html).

bench_test.py bietet explizite RAM-Profile und setzt cfg nach Rueckkehr zurueck;
kein Start beim Import. pitch-range setzt nur die reale Grenze voruebergehend
auf 20 Grad. tools/analyze_bench.py ist ein reiner Hostauswerter; keine MCU-Imports.
Fehlende/alte/ungueltige Daten oder verlorene Ereignisse erzeugen keinen PASS.
Pruefanleitung: [FEHLER_TISCHTEST.md](FEHLER_TISCHTEST.md).

## Separate GPS-/Barometer-Vorbereitung

Der Branch codex/gps-baro-bringup ergaenzt GPS-NMEA und MS5611 an freien Pins:
UART0 RX GP13 (TX GP12 unverbunden), I2C1 SDA/SCL GP10/GP11. IMU bleibt auf
I2C0. Neue Einstellungen stehen in config.py; app.run() nutzt sie nur mit
expliziter Fluglogger-Session, nicht im bisherigen Start ohne Session.

gps.py begrenzt Rahmen-/UART-Lesen und prueft GGA/RMC, Pruefsumme und Datenalter.
Ein gemeinsamer Fix braucht gueltige frische Saetze derselben UTC-Epoche.
Seit Sensor-Test 0.1.1 lesen Empfang und Altdatenverwerfen hoechstens die mit
UART.any() gemeldete Menge innerhalb ihres Limits. Feste Laengen koennen auf
RP2 trotz timeout=0 auf nachkommende Zeichen warten. Receiver-Fixzaehler bleiben
bei Frischeverlust erhalten, waehrend die aktuelle Navigationsgueltigkeit geloescht
wird. Hosttests pruefen das mit zeitlich eintreffenden Bytes, keine MCU-Zeitgarantie.
ms5611.py prueft PROM-CRC, kompensiert Temperatur/Druck und wartet die ADC-
Wandlungen ueber Zustandswechsel statt blockierendes sleep ab. sensor_test.py
startet diese Adapter explizit ohne Receiver/PWM und exportiert einen begrenzten
Datensatz plus Laufbericht. Ab Sensor-Test 0.2.0 statt Ring ein fester gepackter
Puffer fuer die ganze angeforderte Dauer mit standardmaessig 2 Hz: 83 Bytes je
Sample, ca. 30 kB/180 s oder 50 kB/300 s. Groessenlimit und gemeldetes freies
RAM inklusive Reserve vor Hardwarestart pruefen; kein stilles Ueberschreiben.
CSV erst nach Stop erzeugen; JSON-Schema 2 nennt Kapazitaet, Speichermenge und
all_samples_retained. Das ist weder Navigation noch ein MANUAL-Fluglogger.

Naechster Integrationsschritt nach den physischen Sensorchecks: Daten gemeinsam
mit dem bisherigen MANUAL-Durchgang aufzeichnen, Zusatzaufwand messen und einen
Speicherweg fuer ganze Datenfluege implementieren. Anleitung und Nachweisgrenzen:
[SENSOREN_TEST.md](SENSOREN_TEST.md).

## Kalibrierung, Referenz, Trimmung

- Accel Offset/Skalierung: die vorlaeufig gemessenen sechs Lagen sind in config.
- Gyrooffset: bei jedem Start aus stationaeren Samples, nicht persistent.
- Montagekoordinaten: feste, rechtshaendige Transformation in SENSOR.
- Level: explizite geometrische Roll-/Nickreferenz in calibration.json.
- RC: explizite Min/Mitte/Max pro aktivem Eingang in calibration.json.
- Servotrim: feste Verschiebung der Ruderlage in us in SERVOS.
- Fluglagentrim: Verschiebung neutraler Roll-/Nick-Sollwinkel in Grad.

Die Sendertrimmung sieht auf dem PWM-Kanal wie ein Knueppelausschlag aus.
Der MCU kann beides nicht eindeutig unterscheiden. Deshalb kein automatisches
Lernen der Mitte im Flug. Neutralfreigabe nach Aktivierung nicht erneut
verlangt, ausser nach RX-Ausfall. Eindeutige Trimmkommandos und begrenzte
Trimmanpassung sind spaetere Funktionen, noch nicht implementiert.
rate_i ist vorhanden, aber standardmaessig 0; ein I-Anteil kann dauerhaft
benoetigten Ruderausschlag lernen, ersetzt aber nicht Fluglagen-/RC-Kalibrierung.

## Thermik: weitere Entwicklungsschritte

1. Belastbarer Flugsteuerkern: verifizierter Sensor, Stromversorgung,
   Rueckfallebene/Moduswahl, Empfaenger-Failsafe, reale Worst-Case-Zeiten.
   Gier-Koordination statt blinder Null-Gierratenregelung im Kurvenflug.
2. Hoehen- und Geschwindigkeitszustand: Barometer/Vario, Airspeedmessung,
   GPS fuer Position/Bodengeschwindigkeit, passende Filter/Sensorfusion.
   Barometrisches Steigen allein ist nicht automatisch Luftmassensteigen:
   Geschwindigkeitsaenderung und Eigen-Sinken des Seglers mitberuecksichtigen.
3. Energie-/Geschwindigkeitsregelung: abgestimmte Nick-/Airspeedregelung;
   Stallgrenzen, Hoehenreserve, unterschiedliche Sinkpolare bei Bankwinkeln.
4. Navigation: sichere Sollpositionen/Kurs, Windversatz, Kreisradius und
   Roll-Sollwerte. Neue navigator.py liefert Sollwerte an vorhandene Regler.
5. Thermikerkennung/-zentrierung: aus geschaetztem Luftmassensteigen und
   Position ein Thermikmodell ableiten; soaring.py entscheidet ueber
   Einkreisen/Verlassen und liefert Anforderungen an Navigation.
6. Simulation mit Flugzeugdynamik und synthetischen Thermiken, anschliessend
   Logging und schrittweise Flugvalidierung mit erprobter Rueckfallebene.

ArduPlane-Soaring ist eine Designreferenz, keine Aussage, dass unser kleiner
Controller alle entsprechenden Sensoren und Funktionen schon besitzt.
Die Module fuer Navigation/Thermik werden erst geschrieben, wenn die
Zustandschaetzung und Aktuatorik belastbar genug sind. Keine leeren Module,
die Autonomie nur vortaeuschen.

## Speicherentscheidung

Aktueller Loggerumfang auf codex/manual-flight-logger: CH3 schaltet Aufnahme
bei unveraendertem MANUAL, kein fester Flugtimer. recording.py ist reine
Schaltlogik; logger_bench.py stellt explizite CH3-/Flash-Bodenmessungen bereit.
app.run(session=...) ist optional angebunden, schreibt im laufenden Loop
weiterhin nicht auf Flash; ohne Session bleibt der bisherige Ablauf erhalten.
Zielraten/Formatbudget, qualifizierte GPS-Anzeige und Speicherentscheidung
nach Messung: [Flugloggerplan](FLUGLOGGER_PLAN_UND_BODENTEST.md).
L2 vom 2026-10-21 zeigt korrekten Readback, aber bis 181.709 ms fuer einen
Schreibzyklus; aktueller Dateiwriter bleibt aus der Steuerung ausgeschlossen.
L3 hat den 1-Hz-RAM-Puffer mit Export nach Programmstop am Boden vorgeprueft.
Encoder/Flugloggerintegration sind jetzt hostgeprueft implementiert, siehe unten.
Erster L3-Lauf mit 0.1.1: 164880 B Gesamtfreiraum, aber Allokation von 91008 B
am Stueck scheitert. Ab 0.1.2 verwaltet ram_buffer.RecordBuffer gleich grosse
Records in kleinen vorab reservierten bytearrays; kein Record ueberquert eine
Blockgrenze. Standardprobe: 632 * 144 B in 40 Bloecken, maximal 2304 B je Block.
slot(index) liefert Block/Offset fuer pack_into, ungueltige Indizes werden
abgewiesen. Keine Aufnahmeverwaltung, kein Ueberschreiben/Verkleinern. Die Probe
misst nach Inhaltspruefung/GC die verbleibende 64-KiB-Reserve inklusive
Objekt-/Listenoverhead; Erfolg ist weiterhin nur vorlaeufig. Auch die Blockvariante
scheitert im Besitzerlauf bei 162608 B Gesamtfreiraum, ohne gespeicherten genauen
Fehlerort. 0.1.3 instrumentiert deshalb den Allokator: echte Erfolgszaehler,
letzte Anforderung, freier Heap beim Fehler vor Cleanup, Fehlermeldung und
Heapzusammenfassung/Traceback in der Konsole. Die Nutzdatengroesse bleibt gleich.
Resultat 0.1.3: 35 Bloecke/80640 B erfolgreich, Block 36 scheitert mit
2304-B-MemoryError bei 79552 B freiem Heap. Fragmentierung ist stark indiziert;
die genaue Heapkarte fehlt. 0.1.4 reserviert alle Recordbloecke vor den grossen
Modulimports und haelt sie waehrend derselben Imports. Erst danach Inhaltsprobe
und Reservepruefung; auch Compilerfehler werden gemeldet und der Puffer freigegeben.
Besitzerlauf 0.1.4 hat bestanden: 40 Bloecke, Inhalt/Imports bestaetigt, 68656 B
frei. Die fruehe Allokation ist fuer diese Vorprobe physisch bestaetigt.
[L3-Befund](testdaten/logger_boden/AUSWERTUNG_L3.md).

Neue explizite Integration (Logger 0.1.0): flight_start reserviert den vollen
Puffer vor Imports und waehlt sensor/manual nur im RAM; kein Autostart.
flight_records kodiert 144 B pro Ganzdatensatz. flight_logger kapselt CH3
auf eigenem PIO-Index, GPS-/Barometerpolling, GPS-Bereitschaft, NeoPixel und
debouncten BOOT-Stop. Die drei Steuerkanaele behalten ihre Frische-/Neutraldomaene.
app.run(session=None) bleibt der bisherige Pfad; mit Session Zusatzarbeit nach
Servoausgabe, vor Workmessung. Zeitueberschreitungen werden weiter erkannt.
Bei verriegeltem Automatikfehler wird nur in der Logger-Session weiter IMU
gelesen; Fault bleibt gesetzt und ungueltige alte Winkel werden nicht neu datiert.

Logger 0.1.6 nutzt vorhandene StageTiming-Felder fuer SENSOR und MANUAL.
Die langsamste Periode bewahrt die Phasen der vorausgehenden Iteration;
Auswertung/Export erfolgen nach Stop. Feste Arrays entstehen vor der
Startup-Reservepruefung, Messkosten bleiben im Loop sichtbar. Das lokalisiert
den F2-TIMING-Aussetzer, aendert aber weder Schutz-/Neutralfreigabe noch Latenz.

0.1.7 entpackt IMU-Register mit struct.unpack_from und rechnet feste Komponenten
ohne Generatoren; Filtergleichungen, Koordinaten und Grenzen bleiben erhalten.
IMU haelt genau einen first_saturation-Rohsatz (ax,ay,az,T,gx,gy,gz), kein Ring.
app uebernimmt ihn nach Abschaltung als imu_first_saturation_raw ins JSON.

0.1.8 verkuerzt ausschliesslich gc_poll_ms200 ->20. Der freie Heap kann
zwischen200-ms-Abfragen bereits erschoepft sein; dann sammelt automatische GC
in einer beliebigen Phase. Budgetgepruefte geplante GC bleibt am Loopende,
automatische GC aktiv. Haeufigere Heapscans kosten selbst Zeit und garantieren
keine Deadline; alle Kosten und bisherigen Fehlerreaktionen bleiben sichtbar.

Kein paralleler Text-Ring bei Flugsession. Bei vollem RAM/Loggerfehler stoppt
nur Aufnahme. Nach bestaetigtem PWM-/Steuer-PIO-/Aux-PIO-/UART-Stop folgen CSV/JSON.
Bei Exportfehler bleibt der Puffer in flight_start._pending referenziert;
save_pending ist ohne bestaetigten Stop gesperrt und nutzt neue Dateinummern.
Reale Startup-Reserve, BOOT-/LED-Kosten und Gesamtloop werden in F1/F2 geprueft:
[Testanleitung](FLUGLOGGER_TEST.md). Kein eigentlicher Bord-Autostart eingerichtet.

Code und Kalibrierdatei bleiben im Board-Flash (2 MB insgesamt, Firmware
benoetigt einen Teil). RAM ist 264 KB inklusive MicroPython. Ein fester
Logring begrenzt RAM-Verbrauch; kein Flash-Schreiben in der Regelschleife.
20 Sekunden RAM-Ring reichen fuer den aktuellen Bodenvergleich. Fuer
Fluglogs muss zwischen grosserem RAM-Ring, gepufferter SD oder Telemetrie
entschieden werden. Blockierende Schreibzeiten und Stromausfallverhalten
muessen dann gemessen werden. Keine Speicherkarte fuer den Code noetig.
