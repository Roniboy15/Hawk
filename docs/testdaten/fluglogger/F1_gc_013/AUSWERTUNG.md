# F1 / 0.1.3: orange Komponentenwarnung, 2026-10-21

[JSON](flight_265737_0.json), [CSV](flight_265737_0.csv), unveraenderte Kopien
der vom Besitzer bereitgestellten Downloads. Besitzer brach wegen schnellem
orangem Blinken ab. Orange stammt hier vom GPS-Komponentenfehler, nicht Full.

**Verifiziert:** errors.gps = MemoryError / allocating 640 bytes. Kein
Aufnahmesegment, null Samples/CSV-Datenzeilen; CSV hat nur die Kopfzeile.
logger_disabled=false, full=false: der GPS-Fehler sperrt die Aufnahme nicht
automatisch; ein Aufnahmestart ist in diesem Bericht nicht nachgewiesen.
SENSOR ohne PWM, Ctrl+C nach 64.399 s, shutdown_ok=true, partielle letzte
Iteration. Barometer wurde initialisiert und bildete eine Druckreferenz.

Startreserve bestanden: 66736 B frei, Startup-GC 24.099 ms. Laufzeit-GC:
count=0, deferred=1566, min_free_bytes=384. Das Minimum ist nicht zwingend
der freie Speicher im Moment der GPS-Ausnahme. Contiguous heap layout und
automatischer GC-Zustand sind nicht protokolliert; keine definitive Aussage
ueber diese beiden moeglichen Einfluesse auf den MemoryError.

**Fehler in 0.1.3:** mem_free() lief jede Iteration, vor der Entscheidung
ueber das 15-ms-Arbeitsfenster. Die Abfrage verbraucht selbst Zeit; dadurch
kann sie jede anschliessende GC verhindern. Laufzeitschleifenrest maximal
7.623 ms statt zuvor 1.204 ms. Das ist ein Indiz fuer zusaetzliche Kosten,
keine isolierte Messung einer einzelnen Heap-Abfrage.
MicroPython implementiert mem_free ueber gc_info/Heap-Durchlauf:
[modgc.c](https://raw.githubusercontent.com/micropython/micropython/v1.29.0/py/modgc.c),
[gc.c](https://raw.githubusercontent.com/micropython/micropython/v1.29.0/py/gc.c).

Nur zwei GPS-Saetze / 119 Bytes vor dem gelatchten Fehler. Ein Timingtrip bei
0.514 s, max. 50.181 ms, Mittelperiode 20.423 ms. Wegen ausgefallener GPS-
Last ist die geringere Tripzahl kein bestandenes Timingresultat.

**0.1.4:** Zeitbudget vor Heap-Abfrage pruefen; Heap nur alle 200 ms abfragen.
Bei niedrigem freien Speicher Anforderung merken. Nach Abfrage vorhandenen
Abstand zur echten Deadline anhand Start-/bisheriger GC-Dauer pruefen. Falls
zu knapp: im naechsten passenden Loop ohne erneuten Heapscan bereinigen.
Automatische GC wird nicht umgestellt; ihr Zustand wird jetzt im JSON erfasst.
Puffer, Startreserve und Deadline bleiben erhalten; alle Kosten bleiben in
Work/Period. GPS-Komponentenfehler werden weiterhin nicht still zurueckgesetzt.

Drei neue Tests mit langsamer Heap-Abfrage reproduzierten den Fehler vor der
Korrektur und bestehen danach; insgesamt 192 Hosttests. Hardwarewirkung noch
offen. Naechster Lauf: flight_logger/config 0.1.4, Soft-Reboot, SENSOR drinnen,
ein 60-90-s-Segment, CH3 unten/BOOT, CSV/JSON/Konsole nach F1_gc_014/ sichern.
Bei erneutem Orange sauber beenden und Bericht sichern; kein unveraenderter
0.1.3-Wiederholungslauf und noch kein F2. [Bedienung](../../../FLUGLOGGER_TEST.md).

SHA-256 JSON: `6a6fad5181cb6912d714177f1d7ec5b47687767db960818634dd37d97f0dbac1`

SHA-256 CSV: `89f87b77243faf695c041a13b394499f9d695a27e3d6c85685f8feec98810850`
