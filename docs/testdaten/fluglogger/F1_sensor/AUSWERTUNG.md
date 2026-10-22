# F1 SENSOR / Logger 0.1.0, ausgewertet am 2026-10-21

Rohdateien unveraendert: [JSON](flight_327002_0.json),
[CSV](flight_327002_0.csv). Besitzer meldet funktionierende Bedienung und
einen Test **drinnen/am Fenster**. Die Konsolenausgabe wurde nicht mitgesichert;
die Fehlerfolge ist im JSON enthalten.

**Ergebnis:** Aufnahme/Pause/Wiederaufnahme, RAM-Aufzeichnung und BOOT-Export
funktionieren in diesem Lauf. SENSOR blieb ohne PWM. F1 ist insgesamt noch
nicht abgeschlossen: wiederholte harte Zeitueberschreitungen; GPS-Fix und
gruene Bereitschaftsanzeige in diesem Lauf nicht nachgewiesen. Kein Hinweis
auf einen protokollierten IMU-/Barometerausfall.

## Was die Startmeldung bedeutet

app.py gibt getrennt `Zustand: <Modus> Fehler: <Fault oder ->` aus.
`SENSOR` ist der gewuenschte Modus ohne Servoausgabe, kein Fehlertext.
Das erste JSON-Ereignis bei 6 ms hat `mode=SENSOR`, `fault=''`: kein Fault.
Bei 7812 ms / Iteration 566 wechselt der Fault auf `TIMING` und bleibt gesetzt.
Alle 39 CSV-Zeilen entstehen spaeter und enthalten deshalb `fault=TIMING`.

Die genaue gelesene Konsolenzeile ist ohne Mitschnitt nicht rekonstruierbar.
Die Ereignisse belegen aber sowohl den fehlerfreien ersten Zustand als auch
den nachfolgenden echten Zeitfehler. `errors={}` betrifft die Loggerkomponenten
und hebt diesen separat erfassten Steuerungsfault nicht auf.

## Verifizierte Daten

| Pruefung | Befund |
| --- | --- |
| Geraet / Runtime | Waveshare RP2040-Zero, MicroPython v1.29.0 |
| Konfiguration | SENSOR, AUTO_START=false; 1-Hz-Aufnahme, 50-ms-Deadline |
| Gesamtdauer laut Bericht | 115288 ms; enthaelt Initialisierung/Abschluss vor Berichterstellung |
| CSV / RAM | 39 Zeilen, 46 Spalten, fortlaufende Sequenzen 0..38, steigende Zeiten |
| Aufnahme | 35 periodische Samples, zwei Starts und zwei Stops |
| Segment 1 | 55543..75857 ms, 20 Samples, aktiv fuer 20.314 s |
| Pause | 14.214 s zwischen Stop 1 und Start 2; keine Zeilen dazwischen |
| Segment 2 | 90071..106159 ms, 15 Samples, aktiv fuer 16.088 s |
| Sampleabstaende | Start/Samples innerhalb eines Segments: 1000..1033 ms |
| Abschluss | shutdown_ok=true, stop_reason=ground_button |
| Speicherzustand | full=false, logger_disabled=false, errors={} |
| RAM nach realen Startobjekten | 69616 B frei, 4080 B ueber der geforderten 65536-B-Reserve |
| Servoausgabe | alle drei servo_* Felder immer 0; alle 8299 Iterationen SENSOR |

91008 B Puffer wurden reserviert. Dieser kurze Lauf validiert weder einen
voll gefuellten Puffer noch die RAM-/Timingreserve mit PWM-Objekten in MANUAL.
CSV und Bericht sind hinsichtlich Zeilen/Samples/Segmenten konsistent.

## Sensoren und GPS

Alle CSV-Zeilen haben valid_bits=5: IMU und Barometer gueltig, GPS ungueltig.
IMU-Alter jeweils 0 ms; keine IMU_START-/IMU_RUNTIME-/PITCH_RANGE-Ereignisse.
Roll ca. 3.92..4.04 Grad, Nick ca. -1.91..-1.84 Grad; der gespeicherte
Ausschnitt zeigt wenig Lagebewegung. Das ersetzt keinen Richtungstest.

Barometer: 95542..95547 Pa, 24.08..24.12 Grad C, relative Hoehe
0.159..0.600 m, Datenalter 0..113 ms; Startreferenz 95548.8 Pa.
Kein Komponentenfehler; absolute Hoehen-/Temperaturgenauigkeit nicht geprueft.

GPS: 25875 Bytes, 920 pruefsummengueltige Saetze, 230 GGA-/RMC-Updates,
keine Parser-/Pruefsummenfehler oder Pollpausen. GGA-Fixsaetze=0,
RMC-Fixsaetze=0, maximal benutzte Satelliten=0. Die Schnittstelle arbeitet,
aber der Empfaenger hat in diesem Lauf keinen Fix gemeldet. Alle Koordinaten
bleiben korrekt leer, gps_ready bleibt aus. Ein Indoor-Test am Fenster ist
eine plausible Empfangserklaerung; ein Geraetedefekt ist daraus nicht belegt.
Der Freiluft-Fix der frueheren S2/S3-Laeufe bleibt als eigener Nachweis erhalten.

## Tatsaechlicher Zeitfehler und Bedeutung fuer MANUAL

8298 gemessene Schleifenabstaende: Mittel 13.881 ms (ca. 72.04 Hz),
Maximum 50.940 ms, **neun Abstaende >50 ms**. Arbeitszeit: Mittel 13.294 ms,
Maximum 50.337 ms, zwei Messungen >50 ms. diagnostics.timing_trips=9.
Arbeitszeit endet vor dem Diagnoseabschluss; der naechste Schleifenabstand
enthaelt auch diesen Rest. Deshalb sind die beiden Ueberschreitungszaehler
nicht gleichzusetzen. 1-Hz-CSV-Samples allein zeigen die seltenen Spitzen nicht.

Der erste Trip liegt lange vor dem ersten Aufnahmestart bei 55.543 s.
Reine 1-Hz-Recordkodierung ist daher keine ausreichende Erklaerung aller Trips.
GPS/Barometer/BOOT/LED sowie der normale Controller laufen auch in Aufnahmepausen.
Es wurden im aktiven Loop nach dem vorliegenden Quellstand keine Dateien
geschrieben; L2-Flashpausen sind kein nachgewiesener Grund dieses F1-Befunds.
Exakte MCU-Quelldateihashes und eine Aufteilung nach Rechenschritten fehlen.
Garbage Collection, Sensor-/Treiberarbeit oder sonstige Laufzeitkosten sind
moegliche Untersuchungsrichtungen, keine bewiesene Ursache.

Die bestehende App verwirft bei erkannten Zeitverlusten gepufferte RC-Daten
und setzt die Neutralfreigabe zurueck. Bei aktiven Ausgaengen werden neutrale
Kommandos ausgegeben; bevor MANUAL wieder freigegeben wird, sind erneut
frische Neutralframes erforderlich. Bei nichtneutralen Knueppeln kann die
Sperre somit deutlich laenger dauern als der einzelne 51-ms-Zeitabstand.
Das ist per Quellcode verifiziert, in diesem SENSOR-Lauf gab es keine PWM.
Bei 98105 ms zeigt auch die CSV `rc_armed=false` trotz frischer RC-Daten.
Dieses Verhalten darf nicht als ungestoerter MANUAL-Durchgang bewertet werden.

## Naechster Schritt

1. Vor F2 die seltenen Zeitspitzen gezielt lokalisieren: begrenzte Messwerte
   fuer IMU/Steuerung, GPS, Barometer, BOOT/LED und Recordkodierung vorbereiten.
   Messaufwand und RAM-Bedarf ebenfalls erfassen; fruehe Pufferreservierung,
   64-KiB-Reserve und bestehende Deadline beibehalten. Inzwischen als 0.1.1
   fuer SENSOR implementiert; [konkreter Diagnoselauf](../../../FLUGLOGGER_TEST.md).
2. Danach ein gezielter F1-Diagnoselauf ohne versorgte Servos draussen mit
   freier Sicht: auf Gruen warten, zweimal aufnehmen/pausieren, BOOT-Stop.
   CSV/JSON **und Konsole** getrennt unter F1_timing/ sichern. Kein weiterer L3
   und keine neue Kalibrierung allein wegen dieses Befunds.
3. Nach Auswertung/gezielter Korrektur F2 MANUAL: kleine Steuerbewegungen bei
   Aufnahme an/aus, Verhalten der Neutralfreigabe und gesamte Zeitstatistik.
   Erst danach eigenstaendigen Bordstart/Versorgung und Datenflug vorbereiten.

Keine Grenzwerterhoehung oder Entfernung der Faultreaktion zur Schoenung des
Ergebnisses. Der konkrete Handlungsbedarf ist die wiederholte Freigaberuecknahme,
nicht das blosse Verfehlen des 100-Hz-Ziels. Firmware/Gains/Signs/Kalibrierung
wurden bei dieser Auswertung nicht veraendert; kein neuer Test ist angelaufen.
Auf codex/manual-flight-logger bleiben, noch kein Merge/Commit durch diese Auswertung.

SHA-256 der unveraenderten Rohdateien:

- JSON: `5d2a5cf5e8fd623f1a9d2ab1b3b30dcffa067260ebb51ea277b28662c0ffda8b`
- CSV: `b57fe32da40cabec45776c165bfbb62ca725d7a04505a677862fa0a3885fca16`
