# Logger0.3.0: Speicher und Discus-Messbereich

2026-10-27, `codex/manual-flight-tests-20hz`: implementiert,244 Hosttests
bestanden, noch nicht am RP2040 getestet. [Erste Flugbefunde](testdaten/fluglogger/flights/F1/AUSWERTUNG.md)
bleiben unveraendert. Keine neuen Gains, Ruderausschlaege oder Airspeed-Funktion.

## Aenderungen

- MANUAL verlangt Neutral nur vor der ersten Aktivierung. Nach RX-/Timing-
  ausfall mit neuen gueltigen Frames aller Steuerachsen aktuelle Kommandos
  sofort wieder annehmen, kein Zuruecktrimmen. Fehlende/alte Pulse bleiben
  gesperrt. STABILIZE behaelt seine Neutral-Wiederfreigabe; Automatikfaults
  bleiben verriegelt. Wiederaufnahme im MANUAL-Profil noch am Boden pruefen.
- Vor BOOT/IMU/RC/PWM: freien Flash lesen und Anzahl voller Exportpakete
  anzeigen. Kein Paket frei: Rot/Abbruch vor Hardwarestart. Alte Dateien
  weder loeschen noch ueberschreiben. Nach Hardwarestop dieselben CSV-/JSON-
  Ausgaben ohne Datei durchzaehlen, erst dann exportieren. Die alte pauschale
  ~1-MB-Schwelle entfaellt;128 KiB Flashreserve bleiben erhalten.
- IMU nominal +/-16 g /2000 Grad/s statt +/-2 g /250 Grad/s. Registerreadback
  und passende Umrechnung2048 LSB/g bzw.16.4 LSB/(Grad/s). Bestehende g-Offsets,
  Skalierung, Achsen, RC-/Levelkalibrierung bleiben erhalten. Ruhige
  Gyro-Nullpunktbestimmung bei jedem Start wie bisher.
- Accel-Clipping verwirft gueltige Gyrodrehung nicht mehr. Gyro-Clipping,
  Lesefehler oder uebersprungene Zeit machen die Lage ungueltig. JSON enthaelt
  ersten Saettigungs-Rohsatz und getrennte Accel-/Gyro-Zaehler.
- Endliche Quaternionrotation statt Eulernaeherung bei schneller Drehung.
  Die25-Grad-Korrektursperre bleibt bei Bewegung. Erst nach2 s mit
  Drehrate<3 Grad/s und Beschleunigungsbetrag1+/-0.05 g grosse Lagefehler
  langsam korrigieren, maximal5 Grad/s. Unter5 Grad Restfehler Lage wieder
  gueltig markieren. Kein sprungweises Neu-Nullen oder Loeschen eines
  verriegelten Automatikfehlers, keine automatische STABILIZE-Freigabe.

Diese Ruhebedingungen sind eine Heuristik, kein Stillstands-/Genauigkeitsbeweis
im Flug. Relative Gier bleibt ohne absolute Referenz. Die bisherigen Spitzen
waren bereits abgeschnitten: wahre Maxima unbekannt. Auch16 g/2000 Grad/s
garantieren deshalb keine saettigungsfreien Starts; Schutzschwellen bleiben.
Die [Haendlerbeschreibung](https://www.bastelgarage.ch/mpu-6050-3-axis-accelerometer-with-gyroscope)
nennt MPU-6050 und diese Bereiche. Kennung0x72 passt nicht zum normalen
MPU-6050; tatsaechlicher Chip unbestaetigt. Grundlage: [InvenSense-Register0x1B/0x1C](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map.pdf).
Registerreadback ersetzt keine physische Skalierungspruefung.

## Kapazitaet und Schema3

**90 s bleiben die gemeinsame RAM-Aufnahmezeit pro Start**, ueber alle
CH3-Segmente. Drei Pakete im Flash bedeuten drei Starts mit jeweils Stop/Export,
nicht270 s in einem RAM-Puffer. FULL beendet weiter nur Aufnahme, kein
Flashzugriff im Flugloop.20 Hz/1800 schnelle und132 volle1-Hz-/Ereignisrecords.

Gyro schnell: int16 mit0.1 Grad/s Aufloesung, maximal0.05 Grad/s Rundung,
statt float32. Winkel weiter0.01 Grad.30 statt36 B pro schnellem Record,
zusammen73008 statt83808 B RAM-Nutzdaten.64-KiB-Startreserve nach echten
Laufzeitobjekten bleibt; physischer Nachweis mit neuer Firmware offen.
Volle Snapshots behalten float32 im RAM; CSV6 signifikante Stellen,
GPS-Koordinaten8 Nachkommastellen. Spalten/Zeitbasis bleiben unveraendert.

JSON/CSV-Schema3 ergaenzt Gueltigkeit; alte Schema2-Dateien anders auswerten:

| Datei | Neues Flag | Bedeutung |
| --- | --- | --- |
| volles CSV `valid_bits` | Bit6 /64 | aktueller Gyro gueltig |
| volles CSV `valid_bits` | Bit7 /128 | Lage nach Filterkriterien gueltig |
| Response `status_bits` | Bit4 /16 | aktueller Gyro gueltig |
| Response `status_bits` | Bit5 /32 | Lage nach Filterkriterien gueltig |

Bit0 bleibt volle IMU-Gueltigkeit. Gyro-/Lagewerte getrennt leer ausgeben,
wenn ungueltig. Bitnamen, `tilt_recoveries` und Speicherplan stehen im JSON.

Konservatives20-Hz-Budget bei4096-B-FS-Bloecken:376832 B je vollem Paket,
inklusive64-KiB-JSON-Budget, dazu einmal131072 B Reserve.

| Volle Pakete | Noetiger freier Flash vor Start |
| --- | --- |
| 3 | 1261568 B |
| 2 | 884736 B |
| 1 | 507904 B |

Board berechnet aus aktueller Blockgroesse/Belegung. Beim frueheren Freistand
1265664 B passen rechnerisch3; neue Firmware/alte Dateien koennen2 ergeben.
Tatsaechliche Exporte sind oft kleiner. Keine Garantie gegen Stromverlust oder
FS-Fehler. Bei Exportfehler eingeschaltet lassen und Fehlermeldung sichern;
ungesicherter RAM geht beim Ausschalten verloren.

## Jetzt konkret am Boden

1. Alte Boardlogs extern sichern. Quellen trennen wie beim [Bordstart](BORDSTART_LOGGER.md).
   Zusammen hochladen: **config.py, imu.py, attitude.py, control.py, app.py,
   flight_records.py, response_log.py, flight_logger.py, flight_start.py**.
   `calibration.json` erhalten; keine neue Kalibrierdatei allein wegen des
   Messbereichs. Soft-Reboot; keine alten Imports weiterverwenden.
2. Zuerst **SENSOR, Servoversorgung aus**. Fuer Thonny vorher
   `LOGGER_BOOT_MODE=None` setzen, dann
   `import flight_start; flight_start.run('sensor')`. Ohne Mac stattdessen
   `LOGGER_BOOT_MODE='sensor'`: Arbeitskopie steht aktuell auf'manual'!
   Erwartet:0.3.0,16-g/2000-Grad/s-Register bestaetigt, ruhige Kalibrierung,
   danach groessenordnung1 g und nahe0 Grad/s in Ruhe. Bei Faktorfehler,
   Kalibrierabbruch oder fehlender64-KiB-Reserve stoppen.
3. Draussen GPS bereit werden lassen. Etwa eine Minute sanft um alle Achsen
   bewegen, danach mindestens20 s ruhig ablegen; fast verkehrte Lage kann
   etwa40 s Wiederfang brauchen. Keine heftigen Wuerfe/Schlaege am eingebauten
   Modell. CH3 unten, BOOT2 s, drei Speichermeldungen/Tuerkis abwarten.
4. Mit angezeigten mindestens3 (sonst2) freien Paketen insgesamt3 (sonst2)
   Laeufe bis FULL aufnehmen und **einzeln exportieren**. Alte Dateien auf
   dem Board lassen; zwischen Laeufen erst nach Tuerkis normal neu starten.
   Alle drei Dateien pro Lauf und Konsole sichern. Das prueft insbesondere
   den bisher fehlgeschlagenen zweiten Export.
5. Kurzer **MANUAL-Bodenvergleich** (`flight_start.run('manual')` bzw.
   `LOGGER_BOOT_MODE='manual'`) mit GPS, Aufnahme/Pause, Ruderbewegungen,
   normalem Stop. Steuerwirkung, keine erneute RX-Sperre/Timing-Trips und
   vollstaendige Exporte anhand der Logs pruefen. Sensor-/MANUAL-Lauf koennen
   die Speicherpruefung mit abdecken. Danach naechsten MANUAL-Datenflug planen.

Gesamtmasse/Schwerpunkt/Trimmung der Zielkonfiguration dokumentieren. Airspeed
kann spaeter separat hinzukommen. Kein numerisches Gain-Tuning aus alten
ungueltigen Winkeln. Kein neuer Branch fuer diese Korrekturen erforderlich.

Hosttests: drei1800-Werte-Exporte bei simulierten1265664 B, Dateinamenschutz,
Reserve/Startabbruch, maximaler JSON-Ereignisring, CSV-Grenzen, Register/
Skalierung, schnelle Mehrachsendrehung, ruhiger60/120/180-Grad-Wiederfang.
Keine MCU-/PIO-/Servozeiten gemessen. Zaehlexport verwendet dokumentierten
[MicroPython1.29-IOBase-Stream](https://docs.micropython.org/en/v1.29.0/library/io.html)
fuer `json.dump`; aktueller MicroPython-Unix-Lauf nicht ausgefuehrt.
