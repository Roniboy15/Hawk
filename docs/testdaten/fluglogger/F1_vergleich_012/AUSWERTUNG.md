# F1-Vergleich 0.1.2, 2026-10-21

[JSON](flight_177217_0.json), [CSV](flight_177217_0.csv), unveraenderte Rohdaten.
Besitzer hat Hawk in alle Richtungen bewegt und danach ruhen lassen. Kein
reiner Ruhelauf; die vorherige Anweisung wurde damit fuer die Bewegung erweitert.

**Logger funktioniert, Timing verbessert beobachtet, aber nicht behoben.**
90.734 s laut Bericht, 6001 Iterationen, 81 Zeilen: 78 Samples, Start/State/Stop.
Ein Segment 6.001..85.560 s, ground_button/shutdown_ok, errors={}, kein Full,
immer SENSOR/alle Servofelder null. RAM nach Start 67696 B, Reserve 65536 B.

Sieben Perioden >50 ms, Maximum 51.355 ms; drei Work-Werte >50 ms,
Maximum 50.640 ms. TIMING ab 17.686 s. Mittelperiode 15.096 ms / 66.24 Hz.
Vorher 0.1.1: 17 Trips in 60.162 s, max. 53.689 ms / 63.80 Hz. Weniger
beobachtete Trips bei laengerem Lauf; Bewegung/Umgebung nicht kontrolliert,
keine garantierte Rate oder vollstaendige Ursachenzuordnung daraus ableiten.

Langsamste Periode folgt auf Iteration 3419: IMU/Lage 30.163 ms, GPS 13.191 ms,
uebrige Phasen zusammen 7.896 ms, ausserhalb 0.105 ms; Summe 51.355 ms.
Start-GC erstmals direkt gemessen: **23.898 ms**. Unabhaengige Phasenmaxima
um 25..30 ms passen weiter zu GC an wechselnden Allokationsstellen. Dass
genau eine bestimmte Spitze automatische GC war, ist nicht direkt gemessen.

IMU-Bewegung sichtbar: Roll -25.7..28.7 Grad, Nick -28.9..18.0 Grad;
Endlage nahe Anfangslage. Ein IMU-ungueltiger Datensatz nach Zeitverlust
bleibt korrekt leer. GPS: 720 gueltige Saetze, kein Fix, keine Parser-/
Pruefsummenfehler oder Pollpausen; Indoor-Last, kein Freiluft-GPS-Nachweis.

**Barometer diesmal stabil:** 95763..95770 Pa, relative Hoehe -0.243..+0.375 m,
Temperatur 22.63..22.88 Grad C. Kein neuer 15-m-Sprung. Ursache des alten
Sprungs damit nicht geklaert; weder Bewegungsfehler noch elektrische Ursache
bewiesen. Keine automatische Hoehenfuehrung oder absolute Genauigkeit validiert.

0.1.3 plant GC nach bereits erfolgter Ausgabe/LED: bei <32768 B frei und
hoechstens 15 ms bisheriger Arbeit. Das tatsaechliche Arbeitslimit wird mit
Start-GC und 5-ms-Abstand zur unveraenderten 50-ms-Deadline weiter begrenzt.
Bei schwerer Iteration aufschieben; automatische GC bleibt aktiv. Alle Kosten
bleiben in Work/Period (SENSOR-Phase loop_tail). JSON runtime_gc erfasst Anzahl,
Maximaldauer, Verschiebungen, kleinstes beobachtetes freies RAM und Arbeitslimit.
Die 64-KiB-Startreserve/Pufferkapazitaet bleiben gleich. Dies ist eine Planung
anhand gemessener Startkosten, keine Garantie fuer spaetere GC-Laufzeiten.
189 Hosttests bestehen, einschliesslich echter App-Reaktion auf 60-ms-GC.

Naechster Besitzerlauf: nur flight_logger.py/config.py aktualisieren, Soft-
Reboot, gleicher SENSOR-Aufruf, ein Segment 60-90 s, CH3 unten/BOOT, Daten und
Konsole unter F1_gc_013/ sichern. Kein Pflichtweg nach draussen und keine
Neukalibrierung. [Bedienfolge](../../../FLUGLOGGER_TEST.md). Noch kein Commit.

SHA-256 JSON: `e894af2249ce89bf7d044ea85bad0d610c6c92bc5f0e71827c815979be3e7676`

SHA-256 CSV: `7fa7e7e257c037b6dda770941a3ac55366df215892d16c02f415538b67d4f877`
