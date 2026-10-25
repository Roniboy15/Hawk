# Logger 0.2.0: SENSOR und MANUAL mit 20 Hz funktional bestanden

Nachtrag: Der hier noch offene GPS-/BOOT-Aussenlauf ist inzwischen als
[R3 ausgewertet](R3_response20_manual_gps/AUSWERTUNG.md). Die folgende
R1/R2-Auswertung und deren damaliger naechster Schritt bleiben nachvollziehbar.

Auswertung der sechs unveraenderten R1/R2-Dateien am 2026-10-25.
Besitzer berichtet, beide Tests haetten funktioniert und bei MANUAL seien
keine Unregelmaessigkeiten der Steuerbewegungen aufgefallen. Das ist eine
Bedienbeobachtung, keine gemessene Ende-zu-Ende-Ruderverzoegerung.

| Lauf | Dauer | Schnelle / volle Samplezeilen | Segmente | Datenrate | Max. Loopperiode | Timing-Trips |
| --- | --- | --- | --- | --- | --- | --- |
| R1 SENSOR, flight_202103_0 | 55.215 s | 608 / 29 | 2 | 19.990 Hz | 45.701 ms | 0 |
| R2 MANUAL, flight_610069_0 | 210.197 s | 1800 / 87 | 3 | 19.994 Hz | 45.655 ms | 0 |

## Direkt geprueft

- JSON meldet jeweils logger_version0.2.0, schema2, profile=response20,
  start_method=explicit, shutdown_ok=true, stop_reason=ground_button.
  errors und fault_iterations sind leer, kein IMU-Saettigungsrohsatz.
- Die CSVs haben46 bzw.17 Spalten, streng steigende Zeitstempel und lueckenlose
  Sequenzen ab0. Zeilen-/Sample-/Segmentzahlen stimmen mit JSON ueberein.
  Alle schnellen Zeilen liegen innerhalb der protokollierten CH3-Segmente.
- SENSOR: alle Servo-Kommandos0, keine PWM in der Gesamtdiagnose.
- MANUAL: ab597 ms durchgehend MANUAL,10499 aktive Iterationen. Danach kein
  RX_TIMEOUT/WAIT_NEUTRAL. Die zwei anfaenglichen RX_TIMEOUT-Iterationen liegen
  vor der Neutralfreigabe. Alle1800 schnellen Zeilen sind MANUAL, IMU gueltig,
  Steuer-RX frisch, freigegeben und PWM vorhanden.
- 5679 gespeicherte MANUAL-Achsenkommandos aus beiden CSVs wurden mit den
  echten normalize()/command()-Funktionen und der protokollierten Kalibrierung
  nachgerechnet: keine Abweichung. Ausgangsspannen: Roll1300..1700 us,
  Nick/Gier1350..1650 us. Das prueft Softwarekommandos, keine realen Pulsformen.
- Alle vollen Zeilen enthalten gueltige IMU-/Barodaten. Baro relativ R1
  -0.77..0.03 m, R2 -0.63..0.77 m. Kein Beleg fuer vermessene Hoehengenauigkeit.

## Segmente, Datenrate und Vollpuffer

| Lauf / Segment | Start..Ende (s) | Schnelle Zeilen | Ende |
| --- | --- | --- | --- |
| R1 / 1 | 11.826..27.716 | 318 | CH3 stop |
| R1 / 2 | 35.043..49.542 | 290 | CH3 stop |
| R2 / 1 | 12.629..44.642 | 640 | CH3 stop |
| R2 / 2 | 95.555..125.622 | 601 | CH3 stop |
| R2 / 3 | 156.367..184.274 | 559 | FULL |

R2 umfasst89.987 s Aufnahmefenster,1800 schnelle Zeilen und93 volle Zeilen
(87 Samples plus sechs Ereignisse). FULL ist die letzte volle Zeile; keine
Ueberschreibung oder spaetere Aufnahme. Der Lauf geht danach noch25.923 s
weiter, weiterhin ohne Modewechsel/Timingfehler in der Gesamtdiagnose.
Das passt zur Besitzerbeobachtung weiter funktionierender Steuerung.

Mittlerer Abstand innerhalb der Segmente: R1 50.024752 ms, R2 50.013912 ms.
Einzelabstaende R1 12..92 ms, R2 13..93 ms: im Mittel20 Hz, deutlicher Jitter.
Das50-ms-Raster aus den CSV-Zeiten nachgerechnet: missed_samples=0 wie in JSON.
Das bedeutet keine uebersprungenen Rastertermine, keine aequidistante Abtastung.
Fuer Reaktionsauswertung echte Zeitstempel verwenden. Beide Zeitbasen beziehen
sich auf Logger-Eintritt nach PWM, nicht auf exakte Sensor-/Ruderwirkzeitpunkte.

## Speicher, Laufzeit und offene GPS-Last

Startreserve bestanden: R1 65616 B, R2 65632 B frei, Grenze65536 B.
Der Abstand zur verlangten Reserve betraegt nur80/96 B; es sind weiterhin rund
64 KiB frei, nicht nur80/96 B. Zusaetzlichen Code nicht ohne neue RAM-Pruefung
hinzufuegen. 19008 B volle Records plus64800 B schnell =83808 B Nutzpuffer.

MANUAL mittlere Loopperiode19.947 ms, maximale Arbeit44.740 ms, maximale
pre_output10.398 ms, write1.541 ms.1312 geplante GCs, maximal24.744 ms;
kleinster abgefragter Heap3792 B. Kein Speicherfehler, keine Leak- oder harte
Laufzeitgarantie. Zeit-/Neutralgrenzen wurden nicht gelockert.

**Beide Laeufe hatten keinen GPS-Fix:** R1 440, R2 1686 checksum-gueltige
Nachrichten, keine Parse-/Pruefsummen-/Pollgapfehler, aber0 GGA-/RMC-Fixsaetze,
0 verwendete Satelliten und keine Koordinaten/Ready-Zeilen. Testort ist nicht
dokumentiert; daraus keinen GPS-Defekt ableiten. Der neue20-Hz-Loop mit
gueltigem Positionsfix und Ready-Verarbeitung ist damit noch nicht geprueft.
Die0.1.9-Fixlaeufe ersetzen diesen Lastvergleich nicht. Auch der BOOT-Bordstart
wurde in diesen beiden0.2.0-Laeufen nicht verwendet.

## Naechster Schritt

Kein Firmwarefix aus diesen Ergebnissen erforderlich. Im vorgesehenen Einbau
einmal draussen MANUAL mit normalem BOOT-Bordstart, freiem Himmel und stabil
gruener GPS-Bereitschaft pruefen. Dann60..90 s mit CH3 aufnehmen, normale
kleine Ruderbewegungen und eine Pause; nach BOOT-Stop alle drei Dateien unter
R3_response20_gps/ sichern. Bis GPS-Gruen warten, Aufnahme nicht vorher starten.
Versorgungsfolge und calibration.json wie in [der Anleitung](../../LOGGER_20HZ.md).
Danach anhand dieses Befunds den ersten kurzen MANUAL-Datenflug vorbereiten.
R1/R2 muessen dafuer nicht nochmals ohne Fix wiederholt werden. Noch keine
Gains-/Aerodynamikbewertung aus diesen Hand-/Bodentests.

## Unveraenderte Rohdateien (SHA-256)

```text
R1_response20/flight_202103_0.json
ab23d9dcf409aab56e9fecf5d04dd3930d7f90f74107110fdc5c08c6c5a7b8d3
R1_response20/flight_202103_0.csv
4641ea58b25e7a0b0d5a41243a92915592de9368426c43ff54e257a164c2b779
R1_response20/flight_202103_0_response.csv
9f104a6cd8f05a32e1c30d31b0c12e247997b74a7ee8eced2db23e3c368badb9
R2_response20_manual/flight_610069_0.json
3e3d8155139ee98c2af53d060b87f8e1ee5db2dc5e254b901f4ab9eb9f218547
R2_response20_manual/flight_610069_0.csv
3a3c0cb13dae2a8a51b201b6d5718fe58cd73e9c84390f4206cd75ad2476146e
R2_response20_manual/flight_610069_0_response.csv
3808ec69911e8db57aec48c9a6eac3ce76ec0d9f0713a4044fc075ceaf49550c
```
