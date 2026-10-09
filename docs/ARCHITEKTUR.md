# Architektur und Weg zum autonomen Thermiksegler

## Jetzt implementiert

Die main.py bleibt klein. app.run() verbindet die Module; keine Hardware-
Initialisierung passiert beim blossen Import von app. Initialisierung und
PWM-Freigabe erfolgen erst beim Aufruf und nach expliziter Kalibrierung.

Sensor -> korrigierte Beschleunigung/Drehraten -> Quaternion-Lage ->
Solllage aus Sender -> Quaternionfehler im Koerperrahmen -> Sollrate ->
begrenzter PI-Drehratenregler -> Servotrim und Ausgangsgrenzen.

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
