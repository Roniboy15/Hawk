# F2 0.1.7: zwei softwarebedingte MANUAL-Unterbrechungen

141.740 s, ein Segment, 130 Samples/138 Zeilen, Sequenz0..137 vollstaendig.
BOOT-Stop/shutdown_ok, errors leer, kein voller Puffer. GPS1136 Saetze ohne
Pruefsummen-/Parse-/Pollgapfehler, kein Fix. Kein IMU-Saettigungsereignis in
diesem Lauf; die fruehere Saettigung ist damit nicht erklaert.

| Ereignis ab Kontrollstart | Periode | Frische RC wieder nach | MANUAL wieder nach |
| --- | --- | --- | --- |
| 19.161 s | 51.156 ms | 20 ms | 541 ms |
| 127.166 s | 50.807 ms | 19 ms | 2981 ms |

TIMING verwirft alle RC-Kanaele und neutralisiert alle drei Ausgaenge auf1500 us.
Beim ersten Ereignis waren die Knueppel neutral; dies erklaert plausibel,
warum erst das zweite aufgefallen ist. Dort verhindern ausgelenkte Knueppel
die sofortige erneute Neutralfreigabe. Kein nachgewiesener Funkverlust.
Die Zeitangaben stammen aus diagnostics.events; CSV-Zeitbasis beginnt etwa80 ms
frueher bei der Loggerinitialisierung. fault_iterations zaehlt den verriegelten
Fehlerzustand, nicht einzelne Aussetzer.

Langsamste vorangehende Iteration1255 (us): IMU/Lage29306, Steuerung3305,
Diagnose671, BOOT381, GPS10368, Baro740, CH3563, Record/LED4782, Rest936,
ausserhalb104. Summe51156. Geplante GC liegt im Rest und war daher nicht
die lange IMU-Phase. Automatische GC dort bleibt eine starke Hypothese,
kein direkt gemessener GC-Aufruf. Mittlere Periode15.598 statt zuvor17.569 ms;
unterschiedliche Laeufe, kein kontrollierter Geschwindigkeitsbenchmark.

## Kleine Korrektur 0.1.8

Nur config.py: gc_poll_ms200 ->20, Versionskennung. Zeitgrenzen, freie
Heap-Schwelle32 KiB, 15-ms-Arbeitsbudget, automatische GC, Neutralgate,
Kalibrierung, Pins, Gains, Rate und Puffer bleiben unveraendert.
Die alte Abfrage kann waehrend200 ms mehrere tausend kurzlebige Objekte
verpassen: min_free_bytes31200 wurde nur bei den Abfragen gemessen, nicht
kontinuierlich. Nur vier geplante GCs im realen Lauf beweisen keine geringe
Gesamtzahl von Bereinigungen. MicroPython kann bei einer erfolglosen
Allokation automatisch sammeln, siehe [gc-Dokumentation](https://docs.micropython.org/en/v1.29.0/library/gc.html).

Gezielte MicroPython1.29/Unix-Probe, echter aktueller IMU-/Lagecode, fake Bus,
1000 Schritte, Heap512 KiB mit gehaltenen Bloecken auf70112 B frei begrenzt:

| Abfrage | ungeplante Heap-Anstiege ohne geplante GC | geplante GC | kleinster abgefragter Heap |
| --- | --- | --- | --- |
| 200 ms | 71 | 3 | 30848 B |
| 20 ms | 0 | 124 | 24032 B |

Heap-Anstieg ist ein Indikator fuer automatische GC, keine Instrumentierung
jedes internen Aufrufs. Automatische GC bleibt aktiv, threshold=-1. Virtuelle
Zeit:12-ms-Arbeit plus3-ms-Rest je Schritt, Heapabfrage7 ms und GC24 ms.
Die Zeiten sind modelliert; Unix64-Bit-Heap ist kein RP2040-Laufzeitnachweis.
Probe: [gc_schedule_probe.py](gc_schedule_probe.py). Host-only, niemals auf dem
Board starten. Neben dem Skript einen machine.py-Stub mit Pin=I2C=object anlegen;
Unix-MicroPython mit math/float/struct/json und -X heapsize=512K verwenden,
Skriptargumente: absoluter firmware-Pfad, dann200 bzw.20; je eigener Prozess.

197 Hosttests bestehen. Neue Heapdruck-Regression scheitert mit alter
200-ms-Einstellung (76 ungeplante GCs im Modell), besteht mit20 ms.
Gesamtlaufzeit/RC-Guards bleiben durch vorhandene 60-ms-Fehlerinjektion geprueft.
Besitzer meldet gc.threshold()=-1 nach erneutem Oeffnen der Konsole; ob dabei
ein Reset erfolgte ist unklar, daher kein Beweis fuer den vorherigen Lauf.

Naechster Besitzerschritt: nur config.py ersetzen, calibration.json erhalten,
Soft-Reboot und kurzer MANUAL-Bodenvergleich0.1.8; [Bedienfolge](../../../FLUGLOGGER_TEST.md).
Keine weiteren unveraenderten0.1.7-Wiederholungen. Noch keine bestaetigte
Behebung auf dem Board, kein Datenflug mit den nachgewiesenen Unterbrechungen.

SHA-256 der unveraenderten Rohdateien:

```text
flight_231333_0.json: 78b2f34f46690365165794028e2ef39c3043c99b68d8c72cc2192299b9f5d146
flight_231333_0.csv: 615383744de752843909e36c51e76986e09d817b26003f66f6f934e3824634a8
```
