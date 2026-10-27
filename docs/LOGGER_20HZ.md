# Logger: kurze Reaktionstests mit 20 Hz

Aktuell vorbereitet: [Logger0.3.0 und konkreter Bodenvergleich](LOGGER_030_TEST.md)
auf `codex/manual-flight-tests-20hz`.30-Byte-Records,0.1-Grad/s-Gyro,
73008 B RAM,Schema3 mit getrennten Gyro-/Lageflags; Rate/90-s-Budget erhalten.
Vorab-Flashpruefung und gezaehlter Export, neue IMU-Bereiche/Wiederfang noch
physisch nachzuweisen. Die folgende Beschreibung dokumentiert0.2.0/R1..R3;
deren bestandene Ergebnisse gelten nicht automatisch fuer die neue Firmware.

Branch: `codex/response-logger-20hz`, Basis `8f6ed38`. R1/R2 am2026-10-25
funktional bestanden:608/1800 schnelle Zeilen, praktisch20 Hz, keine Timing-
oder Steuerunterbrechung nach Startfreigabe, Vollpuffer/Export bestanden.
Kein GPS-Fix in diesen Laeufen. [Auswertung](testdaten/fluglogger/AUSWERTUNG_020.md).
Der getestete0.1.9-Stand bleibt auf `codex/manual-flight-logger`.

R3 hat inzwischen GPS-Fixlast, BOOT-Start und1800 schnelle Zeilen mit19.996 Hz
bestaetigt, ohne Timingfehler oder erneute RC-Sperre. Kraeftige Bewegung ging
mit IMU-Messbereichsueberschreitung einher; MANUAL lief weiter, neun schnelle
IMU-Messungen sind ungueltig. Den Lauf nicht als fault-frei bezeichnen.
[R3-Befund und Grenzen](testdaten/fluglogger/R3_response20_manual_gps/AUSWERTUNG.md).
Jetzt Stand sichern, Einbau/Modell pruefen und ersten kurzen MANUAL-Datenflug
vorbereiten. Kein Loggerfix oder identischer Wiederholungslauf angezeigt.
Die folgenden R1/R2-Anweisungen dokumentieren den bereits bestandenen Ablauf.

## Aufnahme und Speicher

In `firmware/config.py` vor dem Start waehlen:

- `LOGGER_PROFILE='response20'` (hier Standard): 1800 schnelle Records mit
  Ziel 20 Hz plus 132 vollstaendige 1-Hz-Snapshots/Ereignisse.
- `LOGGER_PROFILE='snapshot1'`: bisherige 632 volle Records, etwa zehn Minuten.

Schnell gespeichert werden Roll/Nick (0.01 Grad), drei Gyro-Raten (Grad/s),
drei RX-Pulse und drei Servo-Kommandos (us), vorige Loopperiode, Modus/Fault
und Gueltigkeitsflags. Beschleunigung, relative Gier, GPS/Barometer und RX-Alter
bleiben in den vollen Snapshots. GPS wird weiterhin mit seiner bisherigen Rate
gelesen; haeufigeres Kopieren ergibt keine neuen Positionsmessungen.

Das schnelle Format hat 36 Byte: 64800 B plus 19008 B fuer volle Records =
83808 B Nutzdaten. Die eingesparten 7200 B gegenueber dem bisherigen Puffer
lassen Platz fuer Zusatzcode. Die Startreserve bleibt 65536 B. Rund 90 Sekunden
**aufgenommene** Zeit ueber beliebig bediente CH3-Segmente; kein Flugtimer.
Viele Zustandsereignisse koennen den vollen Snapshotpuffer vorher fuellen.

CH3 unten pausiert beide Datenstroeme, oben nimmt beide auf. Voller Puffer
beendet nur Aufnahme, MANUAL laeuft weiter. Kein Ueberschreiben, kein Flash im
Loop. Nach Landung unten, BOOT 2 s, alle Speichermeldungen/Tuerkis abwarten.
Versorgungs-/USB-Folge unveraendert: [Bordstart](BORDSTART_LOGGER.md).

## Dateien und Auswertung

Ein Lauf liefert drei Dateien mit gemeinsamem Stamm:

- `flight_...csv`: bestehende volle Snapshots und Segment-/Zustandsereignisse.
- `flight_..._response.csv`: schneller Datenstrom, eigene lueckenlose Sequenz.
- `flight_...json`: Bericht, Schema 2, inklusive `response_log` mit Dateiname,
  Samplezahl, Kapazitaet, Intervall-Minimum/Mittel/Maximum und `missed_samples`.

Beide CSVs haben dieselbe relative ms-Zeitbasis. Segmentgrenzen aus dem vollen
CSV verwenden; schnelle Zeilen tragen keine eigene Segmentnummer. Zeitstempel
bezeichnet den Logger-Eintritt nach PWM: Sensorwert und Ausgabekommando stammen
aus derselben Iteration, ihre exakten Capture-/Wirkzeiten werden nicht gemessen.
Servo-Pulse sind keine gemessenen Ruderausschlaege. `period_us=-1` bedeutet
unbekannt oder >=65535 us; die genaue maximale Periode steht in diagnostics.
`status_bits`: Bit0 IMU gueltig, Bit1 Neutralfreigabe, Bit2 Steuer-RX frisch,
Bit3 PWM vorhanden. Ungueltige IMU-Werte werden leer exportiert.

20 Hz ist ein Zielraster von 50 ms. Variable Loopzeit erzeugt Jitter; verpasste
Termine werden gezaehlt, niemals durch identische Nachholzeilen ersetzt.
Pausen zaehlen nicht als verpasste Termine. Massgebend sind echte CSV-Abstaende,
`missed_samples`, Sensorfrische und die unveraenderte 50-ms-Steuerungsgrenze.

## Jetzt konkret am Boden

1. Bei sicher getrennten Versorgungen wie bisher **config.py, flight_start.py,
   flight_logger.py und neu response_log.py** auf den MCU kopieren.
   `calibration.json` erhalten. `AUTO_START=False`, `START_MODE='sensor'`,
   `LOGGER_BOOT_MODE=None`, `LOGGER_PROFILE='response20'`. Soft-Reboot;
   keine vorherigen App-/Loggerimports. Keine neue Kalibrierdatei noetig.
   Ohne Mac stattdessen `LOGGER_BOOT_MODE='sensor'` fuer R1 bzw. `'manual'`
   fuer R2 setzen und die bekannte Violett/BOOT/Weiss-Startfolge nutzen.
   Vor dem Quellenwechsel die oben verlinkte BEC-/USB-Folge einhalten.
2. Zuerst mit stromlosen Servos, Sender/Receiver und allen Sensoren an:
   `import flight_start; flight_start.run('sensor')`. Gyro-Ruhe abwarten,
   draussen GPS-Gruen. CH3 oben etwa15 s, unten etwa5 s, oben etwa15 s.
   Unten/BOOT2 s, drei Dateien unter `docs/testdaten/fluglogger/R1_response20/`
   sichern. Erwartet: SENSOR/Servo0, zwei Abschnitte mit etwa600 schnellen
   Zeilen, volle Snapshots etwa1 Hz, sauberer Export. RAM-Abbruch/Fehler:
   Konsole sichern; Reserve nicht verkleinern.
3. Danach MANUAL-Tischlauf mit bisherigen Strom-/Neutral-/Ruderchecks:
   `flight_start.run('manual')`. Erst30 s aufnehmen,10 s pausiert steuern,
   erneut30 s aufnehmen. Auf stufige Bewegung/Aussetzer achten. Bei Fehler
   sauber stoppen und sichern. Daten nach `R2_response20_manual/`.
4. Bei unauffaelligem Verlauf im selben Lauf weiter aufnehmen, bis die Kapazitaet
   nach insgesamt etwa90 s Aufnahme erreicht ist (Orange). Kurz normale kleine
   Ruderkommandos pruefen: MANUAL muss weiter reagieren. Dann CH3 unten/BOOT,
   sichern. Erwartet:1800 schnelle Zeilen, `full=true`, abschliessendes FULL-
   Ereignis, keine Timing-/RC-Unterbrechung. Orange allein beweist FULL nicht;
   JSON pruefen. Bei voller Kapazitaet keine weiteren Samples im selben Lauf.

Hosttests pruefen Datenformat, Jitter/Auslassungen, Segmentpausen, Vollpuffer,
Fehler/Export und beide Profile. MicroPython/Unix prueft Kompatibilitaet und
Speichertrend; echte Startreserve, 20-Hz-Rate und MANUAL-Timing sind Boardtests.
Danach kurze MANUAL-Datenfluege neu bewerten; die neue Rate ist noch kein
Nachweis von Flugstabilitaet oder abgestimmten Gains.
