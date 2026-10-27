# HAWK – Segelflugcontroller und Flugdatenlogger

MicroPython-Firmware fuer den Waveshare RP2040-Zero in einer Dream-Flight
Libelle ohne Motor. MANUAL steuert Quer-, Hoehen- und Seitenruder ueber den
MCU; IMU, BN-180-GPS und GY-63/MS5611 liefern Messdaten. Langfristiges Ziel
ist autonomes Thermikkreisen. **Navigation und autonomer Kurvenflug sind noch
nicht implementiert; die bisherigen Flugtests waren MANUAL-Datenfluege.**

## Aktueller Stand – 27. Oktober 2026

Entwicklung auf [`codex/manual-flight-tests-20hz`](https://github.com/Roniboy15/Hawk/tree/codex/manual-flight-tests-20hz).
Diese README beschreibt den Stand des ausgewaehlten Branches. `main` ist der
separat gepflegte Integrationsstand; ein Push auf den Entwicklungsbranch
aktualisiert `main` nicht.

| Stand | Nachweis und Grenze |
| --- | --- |
| Logger0.2.0 | R1–R4 am Boden, danach sechs echte MANUAL-Flugsegmente; letzter Flug durch FULL abgeschnitten |
| Erster gespeicherter Fluglauf | 90.021 s Aufnahme,1800 schnelle Werte, keine Timing-/RC-Unterbrechung nach Freigabe; GPS/Barometer nutzbar |
| IMU der Fluglaeufe | Messbereichsueberschreitungen und anhaltende Lagefehler nach Discusstarts; daraus keine Winkelregler-Gains ableiten |
| Logger0.3.0 in diesem Branch | Speicherpruefung, groessere IMU-Bereiche, Lage-Wiederfang und MANUAL-Wiederaufnahme implementiert;244 Hosttests bestanden, Boardvergleich steht aus |

[Flugauswertung mit Hoehenprofil und Flugwegen](docs/testdaten/fluglogger/flights/F1/AUSWERTUNG.md),
[R4-Bodenbefund](docs/testdaten/fluglogger/R4_response20_limits_indoor/AUSWERTUNG.md),
[Validierung](docs/VALIDIERUNG.md). Physische Nachweise fuer0.2.0 qualifizieren
nicht automatisch die neue0.3.0-Firmware. MCU-Hardwaremessungen und bestaetigte
Flugabstimmung bleiben getrennt von Softwaretests.

## Was der aktuelle Code kann

- MANUAL mit kalibrierten PWM-Eingaengen, begrenzten Servoausgaengen und
  Startfreigabe durch neutrale Knueppel. Nach erster Freigabe nimmt MANUAL
  bei RX-/Timingwiederkehr neue gueltige Steuerframes ohne erneutes Zentrieren
  an. Fehlende/alte Pulse steuern nicht; waehrend erkanntem RX-Ausfall stehen
  die Ausgaenge auf Trimneutral. Programmneustart verlangt wieder Startfreigabe.
- Roll-/Nick-Winkelregelung und Gier-Drehratenregelung fuer beaufsichtigte
  Tests. Automatikfehler bleiben verriegelt; kein selbsttaetiger Wiedereinstieg
  nach einem Fehler. STABILIZE behaelt vorerst die Neutral-Wiederfreigabe.
- Loggerprofil `response20`:20-Hz-Roll/Nick/Gyro/RX/Servokommandos plus volle
  1-Hz-Snapshots mit Beschleunigung, GPS, Barometer und Status. CH3 unten
  pausiert, oben zeichnet auf. Alle Segmente teilen1800 schnelle Records,
  also rund90 s **pro Start**, kein fester Flugtimer. FULL beendet nur Aufnahme.
- Alternativ `snapshot1`:632 volle Records bei1 Hz fuer laengere Messungen.
  Aufzeichnung in RAM, Export erst nach bestaetigtem Hardwarestop. BOOT2 s
  bei pausierter Aufnahme beendet den Lauf. Vor Abschalten alle Speichermeldungen/
  Tuerkis abwarten; Stromverlust vor Export verliert RAM-Daten.

0.3.0 prueft Flashplatz vor dem Start und zaehlt den Bodenexport genau durch,
bei unveraenderter128-KiB-FS-Reserve. IMU nominal +/-16 g /2000 Grad/s mit
Registerreadback; gueltige Gyrodrehung bleibt bei Accel-Clipping erhalten.
Langsamer Lage-Wiederfang nutzt ruhige Messbedingungen, keine absolute
Gierreferenz. Schnelles Format30 B, Gyro0.1 Grad/s, CSV/JSON-Schema3 mit
getrennten Gyro-/Lageflags. Details und Grenzen in der Testanleitung.

## Jetzt weiterarbeiten

1. [Konkreter0.3.0-Bodenvergleich und Dateiliste](docs/LOGGER_030_TEST.md):
   zuerst SENSOR ohne Servoversorgung, Speicher fuer zwei/drei getrennte
   volle Laeufe sowie MANUAL-Wiederaufnahme pruefen. Kalibrierung erhalten.
2. [Bordstart und USB/BEC-Trennung](docs/BORDSTART_LOGGER.md),
   [Einbau und Sensoranschluesse](docs/EINBAU_UND_MANUAL_DATENFLUG.md).
3. [MANUAL-Flugbedienung, Trimmung und Ruderwege](docs/ERSTER_MANUAL_DATENFLUG.md).
   Zielmasse/Schwerpunkt dokumentieren; Airspeed-Sensor folgt spaeter separat.
4. [Naechste Schritte](docs/NAECHSTE_SCHRITTE.md),
   [Architektur](docs/ARCHITEKTUR.md), [Thonny](docs/THONNY.md).

Arbeitskonfiguration: `AUTO_START=False`, `LOGGER_PROFILE='response20'`,
`LOGGER_BOOT_MODE='manual'`, `START_MODE='manual'`, Sensoroberseite oben/X nach
hinten (`body_signs=(-1,-1,1)`). Fuer SENSOR zuerst den passenden Startmodus
waehlen; `AUTO_START=True` ist nicht der Logger-Bordstart. Dateien auf dem
Board koennen vom Git-Branch abweichen; Git uebertraegt keine Firmware.
Ruderlimits230/400/350 us; Besitzerangaben Quer/Hoehe/Seite13/12/19–20 mm.

## Flugdaten und Git

Ausgewaehlte Logs, Berichte und Diagramme bleiben unter `docs/testdaten/` und
werden hier mit Git versioniert. Ein separates Daten-Repository ist optional,
keine Voraussetzung. Nicht jede kuenftige Flugdatei muss ins Code-Repository;
Massendaten koennen spaeter extern gesichert werden. Jeder Lauf soll verwendete
Firmware/Konfiguration und Flugnotizen nachvollziehbar zuordnen.

Nach `main` gehoeren zusammen Firmware, Tests, Werkzeuge, README und relevante
Dokumentation. Ein normaler Merge uebernimmt auch versionierte Datenaenderungen
des Branches. Eine reine Firmwareauswahl waere ein eigener,
gezielt zu pruefender Integrationsschritt. README und offene Testpunkte bei
jeder Integration aktualisieren. [Datenstrategie](docs/DATEN_UND_GIT.md),
[Git-Ablauf](docs/GIT.md).

## Dateien


| Datei in firmware/ | Aufgabe / Einstieg |
| --- | --- |
| config.py | Einziger Ort fuer Pins, Achsen, Grenzwerte und Reglerparameter |
| main.py | Startwahl; Logger wartet bei konfiguriertem Bordstart auf BOOT |
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
| response_log.py | Kompakter20-Hz-RAM-Strom, CSV nach Hardwarestop |

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
| BN-180 TX / Versorgung | GP13 / geregelte5 V und GND | GPS-RX bleibt unbeschaltet |
| GY-63 SDA / SCL | GP10 / GP11 | I2C1, VCC/PS an3V3, GND/CSB anGND |
| CH3 Loggerbefehl | GP14 | Unten Pause, oben Aufnahme |

MCU im USB-Test ueber USB versorgen, BEC-Plus nicht zugleich an dessen5-V-Pin.
Bordbetrieb ueber geregelte BEC5 V nach Bordstartanleitung; BEC-/USB5 V nicht
parallel verbinden. SDO des GY-63 bestimmt die im Treiber erkannte Adresse.
Die Tabelle beschreibt die Software-Pinbelegung; der Logauszug ist kein
unabhaengiger Nachweis der physischen Verkabelung oder Signalpegel.
Bei allen zusaetzlichen RC-Eingaengen Signalpegel pruefen/anpassen. Die
Receiver-Versorgungsspannung sagt nicht die Spannung der PWM-Pulse aus.
Servos nicht aus dem 3V3-Pin des MCU speisen. Versorgung beim Umstecken trennen.

Die beiden Querruder muessen mechanisch gegenlaeufig funktionieren. Ein
Y-Kabel liefert beiden Servos denselben Puls und erlaubt keine getrennte
Software-Differenzierung. Die vorhandene funktionierende Mechanik beibehalten.

## Offene Grenzen

- Die Kennung 0x72 und Registerantworten beweisen nicht den exakten Chiptyp.
- Kein unabhaengiger Hardware-Bypass, kein getesteter Watchdog/Redundanzpfad.
- CH3 schaltet ausschliesslich die Aufnahme. MANUAL/STABILIZE werden vor dem
  Start konfiguriert; kein implementierter Flugmodus-Umschalter am Sender.
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
