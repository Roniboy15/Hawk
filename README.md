# Segelflug-Controller — Version 0.2.3, Bodenversuch

Modulare MicroPython-Firmware fuer RP2040-Zero und das bereits getestete
MPU-kompatible SY-104-Modul (WHO_AM_I 0x72). Konventionelles Flugzeug mit
getrenntem Hoehen-/Seitenruder; beide Querruder ueber ein Y-Kabel auf GP3.
Das Projekt bereitet die Architektur fuer autonomes Thermikkreisen vor.
Diese Version implementiert Sensoranzeige, manuellen Durchgang, Roll-/Nick-
Winkelregelung und optional Gier-Drehratenregelung, aber keine Flugnavigation.

**Aktuell: Sensorfunktionstests und Vorbereitung manueller Datenfluege;
autonome Flugfunktion ist noch nicht implementiert.** Der Segler hat
kein Triebwerk und kein Gas. Laut Besitzer sind alle Servos montiert und an
den vorgesehenen Kanaelen angeschlossen; Signalpegel und Ruderwirkungen
muessen trotzdem gemessen/geprueft werden. Eine gemeinsame Stromleiste ist geplant.
Die funktionierende Firmware und Geraetekalibrierung auf dem Mac sichern.
Am 2026-10-13 meldet der Besitzer die Funktionstests aller drei Achsen bestanden;
RX-/Servozeichen sind jetzt jeweils -1/-1. Die beigefuegten STABILIZE-Samples
passen zur Regelrechnung. Elektrische Grenzen, Fehlerreaktionen und
Worst-Case-Timing bleiben offen. Keine Flugabstimmung aus diesem Tischtest ableiten.

## Start hier

**Aktueller Schritt:** Logger0.2.0 auf `codex/response-logger-20hz` hat
R1/R2/R3 am Boden bestanden:20-Hz-Reaktionsdaten plus volle1-Hz-Snapshots,
GPS-Fix, BOOT-Bordstart, CH3-Pause und geordneter Export. R3 speichert1800
schnelle Zeilen (rund90 s), ohne Timing-Trip oder erneute RC-Sperre nach
Startfreigabe. Kraeftige Bewegung erreicht den IMU-Messbereich: neun schnelle
IMU-Datensaetze sind korrekt ungueltig, IMU_RUNTIME bleibt markiert, MANUAL
laeuft weiter. Kein Nachweis von Flugstabilitaet oder abgestimmten Gains.
225 Hosttests bestehen. [R3-Auswertung](docs/testdaten/fluglogger/R3_response20_manual_gps/AUSWERTUNG.md).

`LOGGER_PROFILE='response20'` waehlt diese kurze Aufnahme, `'snapshot1'`
weiterhin den1-Hz-Langzeitlogger. CH3 unten/oben pausiert/startet beide
Datenstroeme ohne Flugtimer; voller Puffer beendet nur Aufnahme. Nach Landung
CH3 unten, BOOT2 s, Tuerkis/alle Speichermeldungen abwarten, dann abschalten.
Nur RAM im Flug; Flash im Steuerloop blockierte in L2 bis181.709 ms.
`AUTO_START=False`, `START_MODE='sensor'`, `LOGGER_BOOT_MODE=None` bleiben
Repository-Defaults. Fuer den bewussten MANUAL-Bordstart am Board
`LOGGER_BOOT_MODE='manual'` waehlen, nicht AUTO_START=True.
[Loggerprofile/Bedienung](docs/LOGGER_20HZ.md), [Bordstart und USB/BEC](docs/BORDSTART_LOGGER.md).
Getesteter Stand:0c1e3ba. Weiter auf `codex/manual-flight-tests-20hz` fuer
Einbau/Ruderwege und kurzen MANUAL-Datenflug. Besitzer nennt als Modell die
Dream-Flight Libelle. [Konkrete Flugvorbereitung](docs/ERSTER_MANUAL_DATENFLUG.md),
[Einbauplan](docs/EINBAU_UND_MANUAL_DATENFLUG.md).
[SENSOREN_TEST.md](docs/SENSOREN_TEST.md) bleibt die Anleitung fuer Wiederholungen.
sensor_test.run('baro'/'gps'/'both') startet nur den separaten Funktionstest,
ohne Servo-PWM. Der gemeinsame Logger ist in SENSOR und MANUAL am Boden geprueft;
ein Kreisregler ist nicht implementiert. Der Besitzer moechte den
bisherigen MCU-MANUAL-Durchgang nutzen und akzeptiert die MCU-Abhaengigkeit;
Timing wird parallel weiter untersucht, ohne pauschale 100-Hz-Einstiegshuerde.

Vorherige [Fehler-/Timingtests T1–T6](docs/FEHLER_TISCHTEST.md):
T1-Wiederholung, T2 und T3 sind funktional bestaetigt. T5/T6 liefen laut Besitzer
wie erwartet; die Daten bestaetigen Stabilisierung und PITCH_RANGE-Verriegelung.
T4 bleibt bewusst offen. T6-Gier-Pulsverlust ist laut Besitzer durch einen
herausgefallenen Stecker erklaert; die Ausgaenge reagierten mit Trimneutral.
T5 erreicht im Mittel nur 74.92 Hz; Timing, erster T1-IMU_RUNTIME und MCU-
Stromverlust bleiben offen. Tischteststand ist als 913a9e6 gesichert,
Sensorabschluss als e177cb5 auf codex/gps-baro-bringup. Die anschliessende
1-Hz-Loggerarbeit liegt auf codex/manual-flight-logger. Barometer/S1 ist funktional bestaetigt;
GPS-Wiederholung gps_2 samt Konsole bestaetigt Fix und Bewegungsreaktion (S2).
S3 bestaetigt gemeinsamen Betrieb und sauberen Stop. Sein alter Dateistand
enthaelt nur die letzten 40.963 s; der neue 0.2.0-RAM-Puffer ist hostgeprueft,
physisch noch zu pruefen. Hoehenspruenge im Gehlog erfordern einen Einbaucheck,
keine Regleranpassung auf Verdacht:
[S3-Auswertung](docs/testdaten/S3_gps_and_baro/AUSWERTUNG.md).
[Aktuelle Auswertung](docs/testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T3_T5_T6.md),
[Vorgaengerbefunde T1/T2](docs/testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T1_T2.md).

1. [TESTBERICHT_2026-10-13.md](docs/TESTBERICHT_2026-10-13.md): abgeschlossener
   Achsen-Funktionstest, Logauswertung und Grenzen des Nachweises.
2. [NAECHSTE_SCHRITTE.md](docs/NAECHSTE_SCHRITTE.md): Sensorchecks, anschliessend
   MANUAL-Datenlogger, Datenbewertung und spaetere Kreisfuehrung.
3. [THONNY.md](docs/THONNY.md): Dateien hochladen, kalibrieren, Achsentests wiederholen.
4. [GIT.md](docs/GIT.md): Repo auf dem Mac einrichten und kleine Aenderungen sichern.
5. [ARCHITEKTUR.md](docs/ARCHITEKTUR.md): Module, Trimmung, Fehler und Thermik-Roadmap.
6. [VALIDIERUNG.md](docs/VALIDIERUNG.md): getestete und noch offene Eigenschaften.
7. [ROLL_TISCHTEST.md](docs/ROLL_TISCHTEST.md): Anleitung fuer erneute Rollpruefung.
8. [PITCH_YAW_TISCHTEST.md](docs/PITCH_YAW_TISCHTEST.md): Anleitung fuer erneute
   SENSOR/MANUAL/STABILIZE-Pruefung nach Umbauten.
9. [VERSORGUNG_WARNHINWEISE.md](docs/VERSORGUNG_WARNHINWEISE.md): beste Diagnose
   zum Versorgungsereignis und Warnhinweise fuer BEC 5 V @ 3 A / vier Servos.
10. [EINBAU_UND_MANUAL_DATENFLUG.md](docs/EINBAU_UND_MANUAL_DATENFLUG.md):
    Stromleisten, Sensorpins, IMU-Drehung und konkreter Logger-/Bodenlaufplan.

v0.2.1 verwirft RC-Puffer bei zu langer Pollpause/vollem FIFO, bewertet Pulsalter
konservativ und verhindert stabilisierte Kommandos nach einer erkannten
Deadline-Ueberschreitung. Timingfehler verlangen neue Neutralfreigabe vor dem
manuellen Ersatz. Parameterpruefung und Abschaltversuche sind erweitert.
Das ist Hostvalidierung, keine bestaetigte Hardwarequalifikation.

Der abgeschlossene v0.2.2-Stand startet SENSOR mit Roll+Nick+Gier; dort gibt es
keine MCU-Servopulse. AUTO_START bleibt False. Das Besitzer-Testprofil war
STABILIZE; zum erneuten Aktuatortest diesen Modus bewusst einstellen.
DIRECTION_CHECKED_AXES blockiert STABILIZE fuer ungepruefte neue Achsen.
Die Koerperkonvention bleibt +Roll rechts, +Nick Nase runter, +Gier Nase links;
pitch_down zeigt daher negative Werte beim Nase-anheben. Kalibrierschema 1
bleibt erhalten; calibrate_rc.run(('pitch',)) erfasst optional nur den neuen Kanal.
Startphasen/Tickzeiten und Gyro-/Gier-Sollrate helfen bei Diagnose; CSV ist erweitert.

v0.2.3 erfasst Zeitstatistiken jeder abgeschlossenen Iteration und bis zu 64
Zustandswechsel im RAM. Nach Stop entstehen bench_<ticks>.csv (30 Spalten) und
bench_<ticks>.json mit Konfiguration, Geraetekalibrierung, Runtime, Maxima und
Ereignissen. tools/analyze_bench.py wertet das Paar auf dem Mac aus. Der explizite
Starter bench_test.run(profile) kennt sensor, manual, stabilize und pitch-range;
er waehlt das Testprofil im RAM und stellt danach die gespeicherten Werte wieder her.

## Dateien

| Datei in firmware/ | Aufgabe / Einstieg |
| --- | --- |
| config.py | Einziger Ort fuer Pins, Achsen, Grenzwerte und Reglerparameter |
| main.py | Default ohne Start; optionaler Loggerstart nach BOOT-Freigabe |
| start_test.py | In Thonny ausfuehren, ruft app.run() auf |
| bench_test.py | Explizite Tischtestprofile aus der Thonny-Shell |
| app.py | Regelschleife und Zustandswechsel |
| calibration.py | JSON-Einstellungen pruefen und speichern |
| calibrate_rc.py | Explizite RC-Min/Mitte/Max-Erfassung |
| calibrate_level.py | Geometrische Roll-/Nickreferenz erfassen |
| imu.py | Sensorregister, Achsenkorrektur, Gyro-Ruhekalibrierung |
| attitude.py | Quaternionfilter, Lage und Koerperrahmen-Winkelfehler |
| receiver.py | Drei moegliche RC-PWM-Eingaenge mit PIO |
| control.py | Regler und einmalige Neutralfreigabe |
| outputs.py | Servopulse, Vorzeichen, Trim und Grenzwerte |
| logger.py | Begrenzter RAM-Ring, CSV-Export nach dem Stoppen |
| diagnostics.py | Zeitstatistik/Zustandsring, JSON-Laufbericht nach dem Stoppen |
| gps.py | Begrenzter NMEA-Empfang mit Pruefsumme, Fixstatus und Datenalter |
| ms5611.py | PROM-CRC, Druck-/Temperaturkompensation, ADC-Zustandsfolge |
| sensor_test.py | Separater GPS-/Barometertest und begrenzter CSV-/JSON-Export |
| recording.py | Reine CH3-Aufnahmeschaltlogik fuer die optionale Logger-Session |
| logger_bench.py | Explizite CH3-/Flash-Bodenmessungen, keine Servoausgabe |
| ram_buffer.py | Frueh reservierte Bloecke fuer ganze Records |
| flight_start.py | Explizit run('sensor'/'manual'), Puffer vor grossen Imports |
| flight_logger.py | CH3, GPS/Baro, LED/BOOT, Export nach bestaetigtem Stop |
| flight_records.py | 144-B-Encoder, 46 CSV-Spalten und reine Bodenstop-Logik |

Alle Python-Dateien enthalten am Anfang Aufgabe, Hauptfunktionen und Logik.
Tests und Dokumentation gehoeren auf den Mac, nicht auf den MCU.

## Hardwareplan

GP bedeutet GPIO-Nummer, niemals physische Pinposition.

| Funktion | Anschluss | Startzustand |
| --- | --- | --- |
| MPU SDA / SCL | GP4 / GP5 | Aktiv |
| MPU VCC / GND | MCU 3V3 / gemeinsame Masse | Aktiv |
| CH1 Querruder-Signal | GP2 | Aktiv, Pegel muss 3,3-V-kompatibel sein |
| Querruder Y-Kabel-Signal | GP3 | Ein gemeinsamer Ausgang |
| CH2 Hoehenruder-Signal | GP8 | Im abgeschlossenen Achsenprofil konfiguriert |
| Hoehenruder-Servo-Signal | GP6 | MCU-Pulswerte im Besitzerlog enthalten |
| CH4 Seitenruder-Signal | GP9 | Im abgeschlossenen Achsenprofil konfiguriert |
| Seitenruder-Servo-Signal | GP7 | MCU-Pulswerte im Besitzerlog enthalten |
| Gas/Triebwerk | Nicht vorhanden | Keine Throttle-Funktion |
| Receiver/Servo Plus | BEC 5 V | Ausreichende Strombelastbarkeit pruefen |
| Alle GND | Gemeinsame Minusleiste | Auch MCU-GND anschliessen |

MCU im USB-Test ueber USB versorgen, BEC-Plus nicht an dessen 5-V-Pin.
Die Tabelle beschreibt die Software-Pinbelegung; der Logauszug ist kein
unabhaengiger Nachweis der physischen Verkabelung oder Signalpegel.
Bei allen zusaetzlichen RC-Eingaengen Signalpegel pruefen/anpassen. Die
Receiver-Versorgungsspannung sagt nicht die Spannung der PWM-Pulse aus.
Servos nicht aus dem 3V3-Pin des MCU speisen. Versorgung beim Umstecken trennen.

Die beiden Querruder muessen mechanisch gegenlaeufig funktionieren. Ein
Y-Kabel liefert beiden Servos denselben Puls und erlaubt keine getrennte
Software-Differenzierung. Die vorhandene funktionierende Mechanik beibehalten.

## Noch keine Flugfreigabe

- Die Kennung 0x72 und Registerantworten beweisen nicht den exakten Chiptyp.
- Kein unabhaengiger Hardware-Bypass, kein getesteter Watchdog/Redundanzpfad.
- Kein implementierter Mode-Kanal. Da kein Gas vorhanden ist, verfuegbare
  Sender-/Receiverkanaele neu pruefen; keinen freien Kanal ungeprueft annehmen.
  START_MODE ist eine Boden-Testeinstellung; Moduswahl und unabhaengigen
  Hardware-Bypass vor einem Flug separat planen.
- Ein Receiver, der bei Funkverlust alte Pulse liefert, wird NICHT durch
  den Pulse-Timeout erkannt. Antenne, Reichweite und Receiver-Failsafe testen.
- Nickwinkelhaltung bedeutet weder Hoehenhaltung noch Schutz vor Stall.
- Quaternionfilter ist kein Navigations-EKF; Beschleunigungen im Kurvenflug
  koennen seine Gravitationskorrektur beeinflussen.
- MANUAL_FALLBACK bedeutet Software-Ersatz bei laufendem MCU und gueltigem RX,
  keinen sicheren Weiterflug bei CPU-Haenger, Stromausfall oder blockiertem I2C.
- Nick-/Gier-Konvention und physische Zeichen sind vom Besitzer funktional
  bestaetigt. Bei geaenderten Pins, Polung oder Montage die betroffenen Eintraege
  aus DIRECTION_CHECKED_AXES entfernen und SENSOR/MANUAL erneut pruefen.

## Tests auf dem Mac

Keine Zusatzpakete erforderlich (Python 3):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## Quellen / Designbezug

Eigenstaendige Python-Implementierung, kein kopierter oder portierter ArduPilot-Code.
Die Trennung von RC-Kalibrierung, Servotrim, Lageschaetzung und Regler orientiert
sich an etablierten Autopilot-Architekturen:

- https://ardupilot.org/plane/docs/new-roll-and-pitch-tuning.html
- https://ardupilot.org/plane/docs/rc-throw-trim.html
- https://ardupilot.org/plane/docs/soaring-4_1.html
- https://docs.micropython.org/en/latest/library/rp2.html
- https://docs.micropython.org/en/latest/library/rp2.StateMachine.html
- https://www.waveshare.com/wiki/RP2040-Zero
