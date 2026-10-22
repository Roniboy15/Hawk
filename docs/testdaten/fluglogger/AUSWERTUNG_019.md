# Logger 0.1.9: BOOT-Start und GPS-Fixbetrieb funktional bestanden

Auswertung der vier unveraenderten CSV/JSON-Paare am 2026-10-22.
Besitzer berichtet: alle Bedienversuche liefen wie geplant, draussen SENSOR
und MANUAL, bei MANUAL keine bemerkten Aussetzer. Hawk wurde hangauf getragen,
in Gehrichtung gehalten und entsprechend den Steuerbewegungen von Hand geneigt.
Diese Beobachtungen sind kein Datenflug und keine gemessene Ruderverzoegerung.

| Lauf | Gesamtdauer | Samples / Zeilen | Segmente | Max. Periode | Timing-Trips |
| --- | --- | --- | --- | --- | --- |
| B1 flight_55245_0 | 37.170 s | 17 / 19 | 1 | 45.252 ms | 0 |
| B1 flight_224687_0 | 49.925 s | 15 / 17 | 1 | 45.606 ms | 0 |
| SENSOR draussen flight_242896_0 | 176.465 s | 71 / 73 | 1 | 45.619 ms | 0 |
| MANUAL draussen flight_284513_0 | 265.652 s | 187 / 191 | 2 | 45.656 ms | 0 |

## Direkt belegt

Alle vier: logger_version0.1.9, start_method=boot_button, errors leer, kein
voller Puffer, shutdown_ok=true und stop_reason=ground_button. Sequenzen ab0
vollstaendig; Anzahl/Typen der CSV-Zeilen passen zu JSON. Alle IMU-/Barowerte
sind gueltig, kein erster Saettigungsrohsatz. SENSOR erzeugt durchgehend0-Pulse.
Startreserve67088 B bei SENSOR/66992 B bei MANUAL liegt ueber65536 B.
Die tatsaechliche Versorgung/Spannungsqualitaet wird nicht im Bericht gemessen;
ordnungsgemaessen BEC-Aufbau nach Anleitung nur als Besitzerbericht fuehren.

MANUAL nach Neutralfreigabe bei581 ms durchgehend aktiv:12463 Iterationen,
keine erneute RX_TIMEOUT-/WAIT_NEUTRAL-Phase, keine Faults. Die anfaengliche
RX_TIMEOUT-Meldung liegt vor Aktivierung/PWM.573 gespeicherte Achsenwerte
mit den echten normalize()/command()-Funktionen nachgerechnet: keine Abweichung.
Mittlere Periode21.262 ms (47.03 Hz), pre_output maximal9.909 ms, write1.586 ms.
Maximale Periode hat4.344 ms Abstand zur bestehenden50-ms-Grenze; keine
garantierte Obergrenze fuer andere Lasten. Geplante GC1517-mal/max24.651 ms,
kleinster abgefragter Heap3712 B; keine Komponenten-/Speicherfehler gemeldet.

MANUAL-Segment1:46.647..140.890 s (94.243 s),93 Samples.
Pause19.614 s. Segment2:160.504..256.555 s (96.051 s),94 Samples.
Aufnahme zusammen190.294 s, also etwa3 min10 s. Sampleabstaende innerhalb
der Segmente1000..1043 ms. Pause beendet weder PWM noch MANUAL.

GPS im MANUAL-Lauf:2994 Saetze,266 gueltige GGA und266 RMC, keine Pruefsummen-/
Parse-/Pollgapfehler. Alle191 Zeilen haben gueltigen GPS-Fix und GPS-ready.
9..12 benutzte Satelliten, HDOP1.01..2.02, Datenalter maximal1118 ms.
SENSOR draussen ebenfalls alle73 Zeilen mit gueltigem Fix; ready in68 Zeilen,
zuvor noch nicht alle Qualitaets-/Folgeepochenkriterien erreicht. Kein Fehler:
Aufnehmen ohne ready ist erlaubt.90 gueltige GGA/RMC, bis10 Satelliten.

## Gehweg und Hoehe: qualitative Plausibilitaet

MANUAL-Segment1: etwa110.5 m aufsummierter GPS-Punktweg, Endversatz gegen den
ersten Samplepunkt41.6 m westlich/73.5 m suedlich. Baro-Hoehe0.31 ->12.31 m.
Segment2: etwa117.3 m Punktweg, Endversatz37.6 m oestlich/58.0 m noerdlich,
Baro12.58 ->7.50 m. Das passt qualitativ zu Hangaufweg mit anschliessendem
teilweisen Rueckweg; die Originalstrecke ist nicht unabhaengig vermessen.
Punktweglange enthaelt GPS-Streuung und ist keine exakte Gehstrecke.

Baro insgesamt0.05..12.84 m; groesster Nachbarschritt0.875 m in1.016 s.
Temperatur19.02 ->etwa7 C zeigt deutlichen Temperaturuebergang; reale Hoehe,
Handbewegung, Anstroemung und Drift sind nicht getrennt. Keine Millimeter-
genauigkeit oder erneute fruehere15-m-Sprungursache aus diesen Daten ableiten.
GPS-Hoehe ist kein verlaesslicher Ersatz: im SENSOR-Lauf512.7 ->487.5 m
zwischen erstem/letztem Sample bei Baro3.63 ->6.35 m, deutliche Abweichung.

Das Halten in Gehrichtung macht IMU-yaw nicht zum Kompass. MANUAL-Groundspeed
bleibt unter2 m/s; GPS-course_valid ist deshalb durchgehendfalse. Yaw/Kurs-
Uebereinstimmung ist hier nicht qualifiziert. Handneigung nach Ruderkommando
prueft keine aerodynamische Reaktion und liefert keine Flug-Gainabstimmung.

## Abschluss und verbleibender Schritt

B1-Bedienung/Reserve/Export sowie SENSOR/MANUAL mit GPS-Fix und CH3-Pause
sind im getesteten Umfang funktional bestanden. Kein neuer Firmwarebedarf
aus diesen Ergebnissen; keine Wiederholung der kurzen Einzeltests erforderlich.
Der geplante Zehn-Minuten-Dauertest ist weiterhin offen: MANUAL lief insgesamt
4 min26 s, Aufnahme nur3 min10 s. Naechster gezielter Bodenlauf im endgueltigen
Einbau: etwa10 min Aufnahme in zwei Segmenten, gueltiger GPS-Fix, normale
Steuerbewegungen, geordneter Export. Kein neuer Timer, keine neuen Gains.
Danach Ergebnisse fuer den ersten MANUAL-Datenflug bewerten; Flugverhalten,
elektrische Lastreserve und unabhaengiger Rueckweg sind damit nicht zertifiziert.

Branch codex/manual-flight-logger beibehalten.0.1.9 plus diese Nachweise bilden
einen gemeinsamen Checkpoint; der Besitzer hat diesen Commit jetzt beauftragt.
Nur Dokumentation/Nachweisauswahl in dieser Auswertung, keine Firmwareaenderung
oder neue Host-Regressionsrunde. Letzter Firmwarelauf:201 Tests bestanden.

## SHA-256 der Rohdateien

```text
B1/flight_55245_0.json 43aec7b6def65cd9313f325928ab91ec508559ca5ddbd520ac8b41d65f006471
B1/flight_55245_0.csv  672930a122e47d9f94174b01bf0f23ced034cb38d4e0c02741cccc9bbd8a1015
B1/flight_224687_0.json f73bb28ad761ea61ce3901d85710f334d317b9f287d92f840f84bc731aca7cfd
B1/flight_224687_0.csv  16bad5e818674789ea16dce15a7bc369dc0e21188e52c63b3b1a647d7394dc10
SENSOR/flight_242896_0.json c4091dc8d5360b0d9e4fa42809788f1f648c8c6d5f8cc1a7a11bb7b6c73cffb8
SENSOR/flight_242896_0.csv  42c8ff151869a1f433623b7e6aa915c6bed5e702a4ae80c69809d9d6c2818a02
MANUAL/flight_284513_0.json 27b7f1593b434d2cc6b19ae3defcf6446e29de5bbe7719d5331198e40432e16a
MANUAL/flight_284513_0.csv  3a4952d7a7bae6407a87cdbd70467455392fe9b0fc6e6c994174cb2201f7e0b8
```
