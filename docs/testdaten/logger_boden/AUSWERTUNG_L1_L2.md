# L1/L2: CH3 und Flash, ausgewertet am 2026-10-21

**L1 funktioniert. L2 speichert korrekt, zeigt aber fuer den vorhandenen
MANUAL-Ablauf zu lange blockierende Dateizugriffe.** Das ist ein Ergebnis der
Speicherpruefung, kein Scheitern der Sensoren oder der gesamten Flugsteuerung.
Die Messung lief separat ohne Controller/PWM; eine reale Ruderreaktion wurde
dabei nicht gemessen. Rohberichte bleiben unveraendert.

## L1: Aufnahmekanal CH3

- GP14, 1300 frische Frames, gemessener Bereich **998..1998 us**.
- Letzter Puls 998 us, Ende keyboard_interrupt, shutdown_ok=true.
- Besitzer bestaetigt: erster und letzter Knueppelzustand waren unten.
  Zusammen mit dem letzten Messwert ordnet das **998 us dem unteren Anschlag**
  zu; der andere gemessene Anschlag ist 1998 us oben. Keine separate Zeitreihe
  oder unabhaengige elektrische Pegelmessung im JSON.
- Vorbereitete Schwellen: <=1200 us aus, >=1800 us ein, sign=+1,
  200 ms Bestaetigung, dazwischen Zustand halten, zuerst unten verlangen.
  In config.RECORDING_CHANNEL gesichert, noch nicht in app.run() aktiviert.

Die Pulsverbindung ist funktional bestaetigt. Aufnahmeschaltlogik, Servo-
Unabhaengigkeit, Sender-Mischer und Receiver-Failsafe sind durch diesen
einzelnen Rohpulstest nicht gemeinsam physisch qualifiziert.

## L2: Dateiinhalte und freie Kapazitaet

Alle drei Testdateien laut MCU-Test vollstaendig geschrieben und erfolgreich
zurueckgelesen: jeweils 65536 Bytes, errors=[], verified=true. stop_reason=complete,
sync_supported=true, passende Operations-/Zyklusanzahlen fuer jede Blockgroesse.
Die .bin-Testmuster liegen hier nicht vor; deren Inhalt ist durch den berichteten
MCU-Readback, nicht durch eine zweite unabhaengige Pruefung am Mac belegt.

Vor Testdateien **1265664 Bytes frei** (1.207 MiB), danach 1056768 Bytes.
Differenz 208896 Bytes fuer 196608 Bytes Nutzmuster: 12288 Bytes zusaetzlicher
Dateisystembelegung. Die nachher geschriebene JSON-Datei ist in diesem
free_after_data-Wert noch nicht enthalten. Nicht linear als garantierten
Overhead fuer alle spaeteren Logdateien behandeln.

Das geplante schnelle Datenpaket bei 25/10/1 Hz braucht geschaetzt 1456 B/s,
also 873600 Bytes fuer zehn Minuten. Vor dem Test bleiben nach 128-KiB-Reserve
1134592 Bytes: kapazitiv voraussichtlich ausreichend, vor weiterem Code/
Metadaten-/Dateisystemverbrauch. Das bestaetigt **nicht** die Schreibzeit.
Bei 50-Hz-Schnelldaten waeren es im bisherigen Budget 1353600 Bytes fuer zehn
Minuten, bereits mehr als der gemessene freie Platz vor Reserve/Overhead.
Die Testmuster nach Berichtssicherung gezielt bei gestopptem Programm loeschen,
wenn ihr Platz wieder genutzt werden soll; keine Kalibrierdateien entfernen.

## L2: blockierende Zeiten

| Block | write max | flush max | write+flush+sync-Zyklus max | Zyklusmittel | over_deadline-Zyklen |
| --- | --- | --- | --- | --- | --- |
| 512 B | 72.098 ms | 110.578 ms | 156.845 ms | 56.858 ms | 58 / 128 |
| 1024 B | 70.702 ms | 109.616 ms | 181.709 ms | 61.262 ms | 35 / 64 |
| 4096 B | 70.312 ms | 114.338 ms | 177.703 ms | 81.707 ms | 16 / 16 |

Insgesamt 109 von 208 Zyklen im berichteten over_deadline-Zaehler. Der
0.1.0-Bericht speichert die Zaehler-Schwelle selbst noch nicht; im zugehoerigen
Repository steht MAX_LOOP_US=50000. Unabhaengig davon ueberschreiten die
gemessenen Maxima eindeutig diese aktuelle 50-ms-Grenze. Ab Benchmark 0.1.1
werden die verwendeten Timing-Schwellen explizit mitgespeichert.

open maximal 6.481 ms, close maximal 0.120 ms, sync maximal 0.062 ms. Die
langen Zeiten stecken in write/flush, nicht hier in os.sync oder close.
Guter mittlerer Durchsatz ist trotzdem moeglich (etwa 9/17/50 kB/s je Fall).
Fuer RC-Steuerung ist die einzelne Pause entscheidend, nicht nur Bytes/s.

Der vorhandene Controller wertet >50 ms als Timingfehler, verwirft RC-Puffer
und verlangt neue Neutralframes. Ein flush von 114 ms ist ausserdem laenger
als RX_TIMEOUT_MS=100. Hardware-PWM kann den letzten Puls weiter ausgeben,
verarbeitet dabei aber keine neue Knueppelbewegung. Das sind Folgerungen aus
der gemessenen Pause und dem aktuellen Code, keine Messung mit bewegten Servos.
Nicht durch vergroesserte Deadlines oder ausgeblendete Loggerzeiten kaschieren.

## Hilft seltener speichern?

Seltener Flash schreiben senkt die Haeufigkeit, beseitigt aber keine einzelne
70..180-ms-Pause. Ein groesserer Schreibstapel kann sogar laenger blockieren.
Weniger haeufig flushen ist keine gemessene Garantie: schon write allein
erreicht in allen drei Faellen ueber 70 ms. Kleinerer RAM-Puffer/Thread oder
vorab angelegte LittleFS-Datei bieten ebenfalls keine belegte obere Zeitgrenze.

**Pragmatische Alternative mit derselben Hardware:** fuer die ersten
MANUAL-Datenfluege vollstaendige Sensordatensaetze mit etwa **1 Hz im RAM**
sammeln und erst nach dem Flug/Ende der Steuerung auf Flash exportieren.
GPS liefert ohnehin 1 Hz. Lage/Gyro/Barometer werden intern weiterhin normal
abgefragt; nur die gespeicherte Zeitreihe wird grober. Gut fuer Sensorfunktion,
Flugweg und langsamen Hoehenverlauf, begrenzt fuer schnelle Flugreaktionen/
Gainanalyse. Keine zehn Minuten bei 25 Hz mit dieser kleinen RAM-Loesung behaupten.

Ein noch zu implementierender kompakter Gesamt-Datensatz mit budgetierten
144 Bytes braucht fuer 600 Samples plus 32 Ereignisrecords **91008 Bytes**.
Das ist eine Groessenschaetzung, keine bestehende Encoderdefinition. L3 prueft
diesen zusammenhaengenden Puffer plus **65536 Bytes freie Reserve** nach
Modulimports. Reale Controllerobjekte/Encoder fehlen dabei noch: ein Erfolg
ist vorlaeufig und muss in der fertigen App nach Initialisierung bestaetigt werden.

Kein Flugtimer: CH3 bleibt Start/Stop der Aufnahme; bei vollem RAM nur Aufnahme
beenden und anzeigen, MANUAL weiter betreiben. CH3 aus im Flug loest keinen
Flash-Export aus. Stromverlust/Reset vor Export verliert RAM-Daten. Fuer den
Bordbetrieb einen expliziten, nur nach Landung bedienten Programmstop/Export
vorsehen und Versorgung bis zum Abschluss behalten; nicht durch einen
Receiververlust oder eine gewoehnliche Knueppelstellung automatisch ausloesen.

Naechster konkreter Bodenversuch: **L3 RAM** aus
[Loggerplan](../../FLUGLOGGER_PLAN_UND_BODENTEST.md). L1/L2 nicht pauschal wiederholen.
Eine eigene Speicherhardware oder reservierter interner Speicherbereich mit
anderem Treiber bleibt eine Alternative fuer hoehere Raten. Raw-Flash darf
nicht in vermeintlich freie Bereiche des gemounteten Dateisystems schreiben.

## Herkunft und Pruefung

Beide Berichte: Test 0.1.0, Schema 1, MicroPython v1.29.0, Waveshare RP2040-Zero.
Zaehlwerte, Groessen, Timingbereiche und Dateipaar-Konfiguration am Host
abgeglichen. Keine Hardwarekommandos durch den Agenten.

- [L1 JSON](L1/logger_channel_98943_0.json), SHA-256
  `9c144b004c06158699c48489bc7b8bea9bc734491737dca050c087119f0fb76b`
- [L2 JSON](L2/logger_storage_275085_0.json), SHA-256
  `f0eabbb222c0ed10137a464ed44acf6e11f64ea5aaacd89b29bb5c6968861315`

Quellengrundlage fuer den Flashpfad:
[MicroPython RP2 v1.29.0](https://github.com/micropython/micropython/blob/v1.29.0/ports/rp2/rp2_flash.c),
[LittleFS-Entwurf](https://github.com/littlefs-project/littlefs/blob/master/DESIGN.md).
