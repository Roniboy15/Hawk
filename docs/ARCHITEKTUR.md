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
Ein Softwarefallback hilft nicht, wenn MCU oder Bus blockieren.

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
Die konkrete installierte MicroPython-Version ist noch zu dokumentieren.

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

Code und Kalibrierdatei bleiben im Board-Flash (2 MB insgesamt, Firmware
benoetigt einen Teil). RAM ist 264 KB inklusive MicroPython. Ein fester
Logring begrenzt RAM-Verbrauch; kein Flash-Schreiben in der Regelschleife.
20 Sekunden RAM-Ring reichen fuer den aktuellen Bodenvergleich. Fuer
Fluglogs muss zwischen grosserem RAM-Ring, gepufferter SD oder Telemetrie
entschieden werden. Blockierende Schreibzeiten und Stromausfallverhalten
muessen dann gemessen werden. Keine Speicherkarte fuer den Code noetig.
