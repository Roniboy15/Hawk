# R4: neue Ruderwege, 20-Hz-Innenraumlauf mit kraeftiger Bewegung

Auswertung2026-10-27 der drei flight_229208_0-Dateien. Dies ist ein
Boden-/Handbewegungstest im Zimmer, kein Flugnachweis. Besitzer meldet alle
Ruder frei/funktionsfaehig und will nach Schwerpunktoptimierung und Sichern
aller Komponenten den ersten MANUAL-Flug machen. Diese beiden Arbeiten und
der Flug sind noch nicht als erledigt bestaetigt.

## Konfiguration und Besitzerangaben

Branch codex/manual-flight-tests-20hz, Basis00854b2 mit Besitzeranpassungen
in config.py. Code und JSON stimmen bei Limits, Empfaenger-/Servozeichen und
IMU-Mapping ueberein. AUTO_START=False; aktueller Besitzerstand setzt
LOGGER_BOOT_MODE='manual', START_MODE='manual', body_signs=(-1,-1,1).
Die gespeicherte Levelreferenz passt zu Mapping/Accelkorrektur. Dies beweist
keine mechanische Ausrichtung oder Ruderwirkung; diese sind Besitzerangaben.

| Achse | limit je Seite | erlaubte Pulse bei center1500/trim0 | gemeldeter Ruderweg |
| --- | --- | --- | --- |
| Quer | 230 us | 1270..1730 us | 13 mm |
| Hoehe | 400 us | 1100..1900 us | 12 mm |
| Seite | 350 us | 1150..1850 us | 19/20 mm |

Quer/Hoehe nicht nach Richtung bzw. beiden Querrudern getrennt angegeben;
Zuordnung der19/20 mm zu rechts/links unbekannt. Keine unabhaengige Messreihe
oder Aussage ueber die bisherigen Direkt-Receiver-Wege. Details und bereits
belegte Herstellerangaben: [Flugvorbereitung](../../../ERSTER_MANUAL_DATENFLUG.md).
Die Dateien zeichnen Quer1314..1730 us auf, Hoehe1100..1900 und Seite1150..1850.
Der untere Quer-Endpunkt wurde waehrend der Aufnahme also nicht erreicht.

## Gepruefte Daten

| Merkmal | Befund |
| --- | --- |
| Logger / Start | 0.2.0, response20, boot_button, MANUAL |
| Gesamtlauf | 211.419 s |
| Aufnahme | ein Segment,158.632..200.323 s, Dauer41.691 s |
| Schneller Strom | 833 Zeilen, Sequenz0..832 vollstaendig |
| Vollsnapshot | 43 Zeilen:41 periodische Samples, Start und Stop |
| Schnelle Rate | im Mittel20.000 Hz; Einzelabstaende13..90 ms |
| Verpasste Rastertermine | 0, aus Zeitstempeln nachgerechnet |
| Steuerung | MANUAL ab572 ms Appzeit, danach keine RX-Sperre/erneute Freigabe |
| Timing | 0 Trips; Periode maximal45.871 ms, Arbeit44.965 ms |
| Start-RAM | 66720 B frei,1184 B ueber65536-B-Startreserve |
| Abschluss | ground_button, shutdown_ok, full=false, logger_disabled=false |

Beide CSVs sind vollstaendig lesbar (46/17 Spalten); Sequenzen, Zeilenzahlen,
Ereignisse und streng steigende Zeitstempel stimmen mit JSON ueberein.
Alle schnellen Zeilen liegen im Aufnahmefenster. Alle833 schnellen und43
vollen Zeilen zeigen frischen Steuer-RX, Freigabe und vorhandene PWM.
Alle2628 Achsenkommandos mit den echten normalize()/command()-Funktionen,
JSON-RC-Kalibrierung und Limits nachgerechnet: keine Abweichung.
Das prueft Softwarewerte, keine elektrischen Wellenformen/Servo-Latenzen.
20 Hz ist ein Mittelwert auf dem50-ms-Raster, keine gleichmaessige Abtastung;
bei der Auswertung immer die echten Zeitstempel verwenden.

## IMU-Saettigung erneut vorhanden

Bereits vor der Aufnahme setzt IMU_RUNTIME (erste App-Diagnose bei89.803 s).
Erster auffaelliger Rohsatz (ax,ay,az,Temperatur,gx,gy,gz):

```text
(10393, -8628, 32767, 1502, -3462, 866, -1002)
```

az=32767 ist Vollaussteuerung des konfigurierten+/-2-g-Bereichs; die
Gyrowerte dieses ersten Satzes liegen unter ihrer Saettigungsgrenze.
Kraeftige Handbewegung ist eine plausible Ursache, kein bewiesener Nachweis
der tatsaechlichen Beschleunigung. Kein belegter RC-/Loggerausfall dadurch.

15 schnelle Zeilen bei180.643..192.694 s sind IMU-ungueltig, mit leeren
Lage-/Gyrofeldern.818 schnelle Zeilen sind wieder IMU-frisch; zwei der43
vollen Zeilen sind IMU-ungueltig. Die Faultmarkierung bleibt wie vorgesehen
verriegelt, daher tragen alle833 schnellen Zeilen IMU_RUNTIME. Das bedeutet
nicht833 ungueltige Messungen oder15 unabhaengige Stoesse. Die Steuerbits und
korrekt gemappten MANUAL-Kommandos bleiben in allen gespeicherten Zeilen aktiv.
Gueltige gespeicherte Gyro-Gierwerte reichen bis236.21 Grad/s; vor spaeterer
Stabilisierung/Kreisflug den2-g/250-Grad/s-Messbereich unter Last auslegen.
Frische Lagewerte unter Beschleunigung sind keine Genauigkeitsgarantie.

## GPS und Barometer

Die Annahme "ohne GPS-Signal" trifft auf die Aufnahme nicht ganz zu:
alle43 Vollzeilen haben ein frisches zusammenpassendes Positionsfixpaar.
Die Qualitaet bleibt aber unter den Bereitschaftskriterien:3..5 Satelliten,
HDOP4.73..5.59, keine einzige GPS-ready-Zeile. Konfiguriert sind mindestens6
Satelliten/HDOP<=2.5 fuer5 neue Fixepochen.2110 checksum-gueltige Saetze,
73 GGA- und73 RMC-Fixsaetze im Gesamtlauf, keine Parse-/Checksum-/Pollgapfehler.
Innenraumkoordinaten nicht fuer Positionsgenauigkeit oder Flugweg verwenden.
Fuer den vorgesehenen Datenflug draussen weiter auf GPS-Gruen warten.

Barometer in allen43 Zeilen gueltig:96245..96254 Pa, relativ0.127..0.917 m,
Temperatur22.74..22.95 C. Kein erneuter grosser Drucksprung in diesem
Ausschnitt; daraus keine nachgewiesene Hoehengenauigkeit oder Varioleistung.

## Konsequenz, Tests und Bedienung

Aufnahme/Export und MANUAL-Kontinuitaet sind fuer diesen Lauf funktional
bestaetigt; der Lauf ist wegen IMU-Saettigung nicht fault-frei. Keine neue
Logger-Laufzeitfunktion aus diesem Befund erforderlich. Handbewegungsdaten
liefern keine aerodynamischen Gains oder Flugstabilitaet.

225 Hosttests bestehen. Der erste Lauf zeigte veraltete Testvorgaben:
Flow-Tests hatten eine feste alte IMU-Referenz, der Trim-Grenztest setzte
implizit Quer-limit200 voraus. Nur diese Vorgaben angepasst: simulierte
Levelreferenz entspricht der aktuellen Konfiguration; der reine Grenztest
verwendet explizit seinen200-us-Beispielbereich. Keine Schutzpruefung entfernt,
keine Firmware-/Kalibrierdatei durch die Auswertung veraendert.

Trimmung waehrend freigegebenem MANUAL fordert keine erneute Neutralfreigabe;
nach echtem RX-/Timingverlust ist sie wieder erforderlich. Kleine Trimmwerte
koennen in der4-%-Totzone liegen. Aufnahme/Pause veraendert diese Logik nicht.
Mehrere Fluege teilen pro Programmstart1800 schnelle Records (ca.90 s gesamte
Aufnahme). CH3-Pause speichert/leert nichts; fuer neue90 s nach Landung stoppen,
Export abwarten und neu starten. [Genaue Bedienfolge](../../../ERSTER_MANUAL_DATENFLUG.md).

Die drei R4-Dateien belegen112959 B Flash. Der konservative Exportcheck
verlangt fuer diesen Lauf626048 B frei, fuer volle132/1800 Records1088512 B.
Alte Dateien brauchen zusaetzlich Platz; ohne aktuelle freie Boardkapazitaet
keine feste Zahl weiterer Fluege versprechen. RAM-Verlust durch Reset/
Stromausfall wird durch freien Flash nicht verhindert. Keine Dateien waehrend
laufender Steuerung schreiben, kein automatisches Fortsetzen nach BOOT-Stop.

## Unveraenderte Rohdateien (SHA-256)

Mit den drei Downloads bytegleich verglichen:

```text
flight_229208_0.json
61b858ed2b0b7a94ede191875b8a4fd35c7d1e268eeefb2b98b7211642164e55
flight_229208_0.csv
087088c3ca48f85a79b9da4e5057f41169d351aa06b7d4a68b34a652549c9a43
flight_229208_0_response.csv
457b1e4fb98b2e6ab29af62068ad080428c840073d74aaf2af716ae99ecc7ca1
```
