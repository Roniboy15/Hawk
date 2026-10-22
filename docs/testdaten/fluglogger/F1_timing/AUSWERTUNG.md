# F1-Timing / Logger 0.1.1, 2026-10-21

[JSON](flight_242233_0.json), [CSV](flight_242233_0.csv),
[Konsole vom Besitzer](konsole.txt). Rohdateien unveraendert.
Besitzer: zwei Segmente, Hawk etwas bewegt, Indoor-Test.

**Bedienung/Speicherung bestaetigt; TIMING weiter offen.** 60.162 s laut
Bericht, 3831 Iterationen, 32 CSV-Zeilen (28 Samples + zwei Starts/zwei Stops).
Segmente 16.479..31.275 s und 40.193..54.535 s, Pause 8.918 s.
shutdown_ok=true, ground_button, errors={}, kein voller Puffer, keine PWM.
RAM nach Start 67920 B, 2384 B ueber der verlangten 64-KiB-Reserve.

17 Perioden >50 ms, Maximum 53.689 ms; Work maximal 53.046 ms (elf >50 ms).
TIMING ab 1.154 s; Mittelperiode 15.673 ms, ca. 63.80 Hz. Die neue Diagnose
kostet selbst Zeit; Tripraten zwischen den Versionen sind kein isolierter
Nachweis einer Hardwarestoerung oder Verschlechterung des Controllers.

Die langsamste Periode folgt auf Iteration 3198: IMU/Lage 30.130 ms,
Steuerung 2.280 ms, Diagnose 0.683 ms, Eintritt/BOOT 0.453 ms, GPS 16.347 ms,
Barometer 1.773 ms, CH3 0.589 ms, Records/LED 0.681 ms, Rest 0.641 ms.
Phasensumme 53.577 ms plus 0.112 ms ausserhalb ergibt exakt 53.689 ms.
Andere, nicht gleichzeitige Maxima: Diagnose 25.126 ms, Eintritt/BOOT 24.979 ms,
Barometer 27.007 ms, Records/LED 29.073 ms, GPS 37.364 ms. Nicht addieren.
Diese verteilten Pausen passen zu automatischer Speicherbereinigung, beweisen
sie nicht; ein Phasenwert trennt GC nicht von der dort ausgefuehrten Arbeit.
[MicroPython: Allokation](https://docs.micropython.org/en/v1.29.0/reference/constrained.html),
[GC-Verhalten](https://docs.micropython.org/en/v1.29.0/library/gc.html).

Quellbefund: GPS erzeugte jede Iteration ein neues Snapshot-Dictionary samt
Hilfsfunktion; Bytezaehlung rief je Byte eine Methode auf. 0.1.2 verwendet
im Logger einen vorab angelegten Snapshot und zaehlt Bytes je Datenblock.
Kohaerente Fixe werden bei neuer Epoche separat kopiert, damit gemischte/stale
Saetze den Cache nicht veraendern. Die bereits vorhandene Start-GC wird als
startup_gc_us vermessen (vor dem Loop); das misst noch nicht jede Flug-GC.
187 Hosttests bestehen. Deadline, Freigabe,
Gains, Kalibrierung, Datenrate und GC-Modus bleiben erhalten. Wirkung auf
Boardzeiten ist noch nicht nachgewiesen.

Bewegung sichtbar: Roll -49.6..20.9 Grad, Nick -23.4..18.8 Grad. Bei 46.254 s
IMU nach Zeitverlust ungueltig, Lagefelder korrekt leer statt eingefroren.
GPS: 480 Saetze, keine Parser-/Pruefsummenfehler/Pollpausen, kein Indoor-Fix.

Separater Barometerbefund: 17.487 auf 18.493 s, Druck 95562 auf 95736 Pa,
Hoehe +0.304 auf -15.045 m, Temperatur 25.03 auf 25.04 Grad C. Druck bleibt
danach etwa auf dem neuen Niveau. Etwas Tischbewegung belegt keinen 15-m-Abstieg.
Besitzer verneint Beruehren/Abdecken/Aenderungen, meldet weiterhin VCC/PS an
3V3 und GND/CSB an GND. Das entspricht dem Anschlussplan, erklaert den Sprung
aber nicht. Ursache offen; keine Filter-/Referenzkorrektur auf Verdacht.
Barometer beeinflusst diese Steuerung nicht; automatische Hoehenfuehrung
ist damit nicht validiert.

Naechster Schritt: gps.py/flight_logger.py/config.py aus 0.1.2, ein ruhiger
60-90-s-SENSOR-Vergleich drinnen, ein Segment reicht. BOOT-Stop; CSV/JSON/
Konsole unter F1_vergleich_012/ sichern. Kein neuer L3 oder Kalibrierlauf.
[Bedienung](../../../FLUGLOGGER_TEST.md). Noch kein Commit/Merge.

SHA-256 JSON: `aba452770b029eba81a7d5d3b618057e5c2920bb23214595f9a8102dbf2efe75`

SHA-256 CSV: `dc09ac92e577be89ca3ed90307661fe7bb4874f986fe5a8be3c341cbd5b95a81`
