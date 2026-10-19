# T3, T5 und T6 — Funktionsnachweise und offene Befunde

Eingang/Auswertung: 2026-10-18. Der Besitzer meldet T3, T5 und T6 wie erwartet
durchgefuehrt und funktional bestanden. T4 bleibt auf seinen Wunsch **OFFEN**:
der vorbereitete Signalschalter wurde nicht eingebaut.

Nachtrag zur Projektplanung am selben Tag: Tischteststand als **913a9e6**
gesichert. Der Besitzer priorisiert nun GPS-/Barometerchecks und danach manuelle
Datenfluege durch den MCU, bei akzeptiertem fehlendem unabhaengigem Rueckweg.
Timingarbeit laeuft weiter; die Messbefunde unten bleiben bestehen. Aktueller
Plan: [NAECHSTE_SCHRITTE.md](../../NAECHSTE_SCHRITTE.md).

Die CSV/JSON-Paare bestaetigen die unten abgegrenzten Softwarefolgen.
T5 verfehlt jedoch das 100-Hz-Ziel; T6 enthaelt zusaetzlichen Gier-Pulsverlust,
laut nachtraeglicher Besitzerbestaetigung durch einen herausgefallenen Stecker.
Deshalb ist dies kein pauschaler Abschluss aller Fehler-/Timingtests.
Firmware, Pins, Gains, Vorzeichen und Kalibrierung wurden hier nicht geaendert.

## Teststand

| Test | Ergebnis | Nachweis / Grenze |
| --- | --- | --- |
| T1 SENSOR, Wiederholung | PASS Funktion | Ohne Fault/PWM; erster T1 mit IMU_RUNTIME bleibt ungeklärt |
| T2 Neutralfreigabe | PASS Funktion | WAIT_NEUTRAL -> MANUAL erst nach 25 neuen Neutralframes |
| T3 fehlender Startkanal | PASS fuer Roll, Nick, Gier | Restempfang vorhanden, durchgaengig RX_TIMEOUT, keine PWM |
| T4 laufender Verlust/Rueckkehr | OFFEN, bewusst ausgelassen | Signalschalter fehlt; T3 ersetzt diesen Test nicht |
| T5 Drei-Achsen-STABILIZE | PASS Funktion; Timingziel nicht erreicht | Ein Lauf ca. 95 s; drei getrennte Wiederholungen nicht belegt |
| T6 PITCH_RANGE-Verriegelung | PASS Kernfunktion; Steckunterbrechung erklaert | Automatik verriegelt; Gierverlust mit Trimneutral, Stecker laut Besitzer herausgefallen |

Mechanische Wirkung und unauffaelliges Verhalten sind Besitzerbeobachtungen.
Die Dateien zeigen Softwarekommandos, keine gemessenen GPIO-Pulse, Versorgung
oder Flugzeugdynamik. Vorgaengerbefunde: [Auswertung T1/T2](AUSWERTUNG_T1_T2.md).

## Quellen und gemeinsame Einstellungen

- T3: [Roll CSV](T3/Roll.csv) / [JSON](T3/Roll.json),
  [Nick CSV](T3/Nick.csv) / [JSON](T3/Nick.json),
  [Gier CSV](T3/Yaw.csv) / [JSON](T3/Yaw.json).
- T5: [CSV](T5/bench_124724.csv) / [JSON](T5/bench_124724.json).
- T6: [CSV](T6/bench_292509.csv) / [JSON](T6/bench_292509.json).

Alle Berichte: v0.2.3-bench, Waveshare RP2040-Zero, MicroPython v1.29.0 vom
2026-08-24, JSON-Schema 1 / CSV-Schema 2, Stop per keyboard_interrupt und
shutdown_ok=true. Keine verlorenen Zustandsereignisse oder harten Timingtrips.
Repo-Quellbasis 4a1f889; bytegleiche MCU-Quelldateien sind damit nicht belegt.

Alle Achsen aktiv/richtungsbestaetigt, RX-/Servozeichen -1/-1, I=0, Trim=0.
Kalibrierung wie T1/T2; Nickreferenz 13.889891 Grad. T3 fordert MANUAL an,
T5/T6 STABILIZE. Nur T6 nutzt die absolute 20-Grad-Testgrenze, T3/T5 normal 75 Grad.

Die Rohdateien wurden nicht veraendert. read_csv()/inspect_run() des vorhandenen
Hostauswerters liefern fuer alle fuenf Paare PASS (Softwareprotokoll), jeweils
mit Timingwarnung. T3 wurde vom Besitzer umbenannt; die direkte API umgeht
nur die CLI-Dateinamenpruefung, expected='missing-rx'. T5/T6 passen zur CLI:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/analyze_bench.py docs/testdaten/Tischtests_v0.2.3-bench/T5/bench_124724.csv --expect stabilize
PYTHONDONTWRITEBYTECODE=1 python3 tools/analyze_bench.py docs/testdaten/Tischtests_v0.2.3-bench/T6/bench_292509.csv --expect pitch-range
```

Der Auswerter prueft bei T5/T6 die angeforderte Kernfolge. Er bewertet das
10-ms-Ziel als Warnung und verlangt bei T6 keinen stoerungsfreien RX bis zum
Stop. Die zusaetzlichen Befunde unten duerfen dadurch nicht verloren gehen.

## T3 — Start ohne jeweils einen Kanal

| Fehlender Kanal / Originalname im JSON | Iterationen | CSV-Zeilen | Letzte Zeit | work max. | period max. |
| --- | --- | --- | --- | --- | --- |
| Roll GP2 / bench_55608.csv | 755 | 78 | 7.893 s | 24.101 ms | 24.678 ms |
| Nick GP8 / bench_37424.csv | 810 | 83 | 8.416 s | 24.325 ms | 24.912 ms |
| Gier GP9 / bench_149569.csv | 1072 | 110 | 11.170 s | 24.749 ms | 25.334 ms |

Jeweils bleibt genau der benannte Eingang bei rx=0, sequence=0, age=-1.
Die beiden anderen Eingangssequenzen steigen an. Alle abgeschlossenen
Iterationen bleiben RX_TIMEOUT; keine Freigabe/PWM-Konstruktion, saemtliche
aufgezeichneten Servowerte 0, keine Automatikfaults. Der Startschutz ist fuer
alle drei Varianten protokolliert. Laufender Verlust ist damit nicht getestet.

## T5 — Stabilisierung funktioniert; 100-Hz-Ziel verfehlt

RX_TIMEOUT -> WAIT_NEUTRAL -> STABILIZE bei 0.511 s nach 25 gemeinsamen
Neutralframes. Danach kein Moduswechsel/Fault bis zur letzten CSV-Zeit 95.701 s.
7172 Iterationen, davon 7124 STABILIZE. CSV: 200 von 918 Zeilen, die letzten
20.8 s; JSON-Zaehler/Zustandsring umfassen den ganzen Lauf.

Pulsbereiche im erhaltenen CSV: Roll 1452..1616 us, Nick 1467..1549 us,
Gier 1468..1550 us. Innerhalb der Grenzen, kein gespeichertes Sample am Limit.
Zwischenwerte und verworfene CSV-Zeilen sind damit nicht beurteilt.

Mittlerer Startabstand **13.346916 ms, ca. 74.92 Hz**. work im Mittel
12.605179 ms, maximal **32.323 ms**; 7132/7172 Iterationen (**99.44 %**)
ueber 10 ms. Maximaler Startabstand 33.112 ms, pre_output 26.428 ms,
write 16.594 ms. Keine Ueberschreitung der harten 50-ms-Grenze. Korrekte
Ruderfunktion ist daher kein 100-Hz-Nachweis. Keine Gains/Deadline zum Kaschieren
aendern. Nur ein Laufpaar vorhanden; drei Wiederholungen spaeter nachweisen.

## T6 — Verriegelung bestaetigt; Gierempfang spaeter unterbrochen

STABILIZE ab 0.511 s. Bei **15.696 s**, Iteration 1196: PITCH_RANGE und
MANUAL_FALLBACK mit frischem RX und drei 1500-us-Ausgaengen. Der Fault bleibt
bis zum Stop; STABILIZE kehrt nicht wieder. Danach eingefrorene relative
Nickanzeige -33.93 Grad plus Levelreferenz ergibt ca. -20.04 Grad absolut:
passend zur negativen 20-Grad-Grenze, keine unabhaengige Winkelmessung.
T6-Kernfunktion ist damit protokolliert und vom Besitzer bestaetigt;
I2C-Ausfall/CPU-Haenger sind nicht physisch getestet.

Zusaetzlicher Verlauf, durchgaengig mit verriegeltem PITCH_RANGE:

| Zeit | Zustand / Gier-Eingang | Softwareausgabe |
| --- | --- | --- |
| 49.402 s | RX_TIMEOUT; rx=0, age=-1 | Alle drei 1500 us, Freigabe geloescht |
| 49.443 s | WAIT_NEUTRAL; RX wieder frisch | Weiter Trimneutral |
| 49.915 s | MANUAL_FALLBACK nach 25 Neutralframes | Automatik bleibt gesperrt |
| 50.528 s | RX_TIMEOUT; Alter 101 ms | Alle drei Trimneutral |
| 50.558 s | WAIT_NEUTRAL; frisch, 1221 us | Keine neue Steuerfreigabe |
| 50.649 s | RX_TIMEOUT; erneut 101 ms alt | Alle drei Trimneutral |
| 62.914 s, letzte CSV-Zeile | RX_TIMEOUT; Alter 12366 ms, Sequenz 2525 unveraendert | Alle drei 1500 us |

Roll-/Nicksequenzen laufen weiter bis 3147; gueltige Gierpulse fehlen bzw.
werden verworfen. Nachtrag des Besitzers am 2026-10-18: **ein Stecker war
herausgefallen**. Das ist die vom Besitzer bestaetigte Ursache und passt zum
protokollierten Gier-Pulsverlust. Damit wird dieser Befund nicht weiter als
ungeklaerter Receiver-/Softwarefehler gefuehrt. Der genaue Steckort und der
elektrische Verlauf sind nicht unabhaengig gemessen. Der Besitzer beendete den
Test danach; zwischen erstem RX_TIMEOUT und gespeichertem Stop liegen ca. 13.5 s.

RX_TIMEOUT priorisiert korrekt die Ausgabesperre ueber MANUAL_FALLBACK. Das
ersetzt **nicht T4**: zufaellige Steckunterbrechung statt vorbereitetem Aufbau,
Neutralwerte beim ersten Verlust, keine abgeschlossene Wiederkehr nach dem
letzten Verlust. Die urspruenglichen Rohdaten bleiben unveraendert erhalten.

## Offene Arbeiten

1. Die betroffene Steckverbindung bei getrennter USB-/BEC-Versorgung
   wiederherstellen, festen Sitz und Zugentlastung pruefen. Danach zuerst SENSOR
   mit frischen Sequenzen aller Kanaele. Die Ursache des T6-Gierereignisses ist
   durch Besitzerbestaetigung eingeordnet; Steckersicherung bleibt eine Aufgabe.
2. Laufzeiten nach IMU/Filter, RX, Regelung, PWM und Diagnose aufschluesseln;
   ersten Fault mit Phase/Exceptiontext im JSON erhalten. Anschliessend nach
   Messung optimieren. Erster T1-IMU_RUNTIME bleibt offen. Konkreter Folgeumfang:
   [NAECHSTE_SCHRITTE.md](../../NAECHSTE_SCHRITTE.md).
3. T4, Versorgung/USB-Verlust und Empfaenger-Failsafe bleiben offene Nachweise.
   Ein unabhaengiger Rueckweg bleibt empfohlen; der Besitzer akzeptiert dessen
   Fehlen fuer die geplanten MCU-MANUAL-Datenfluege. Damit ist das Risiko
   dokumentiert, nicht behoben oder als Ausfallsicherheit nachgewiesen.
4. Ergebniscommit 913a9e6 und Folgebranch codex/gps-baro-bringup sind erstellt;
   main bleibt unveraendert. Kein Merge/Push wurde durchgefuehrt. Der urspruengliche
   Plan eines reinen Timingbranches wurde durch die Sensorprioritaet ersetzt.

## Hostpruefung dieser Auswertung

Am 2026-10-18 erneut 94/94 Hosttests bestanden. Python-Syntax aller 15
Firmwaremodule, des Auswerters und der Tests per AST im RAM geprueft;
lokale Markdownlinks, Rohdaten-Fingerprints und bytegleiche T1-/T2-Archivkopien
kontrolliert. T5/T6 zusaetzlich ueber die regulaere Auswerter-CLI geprueft.
Keine Firmware-/Tool-/Testcodeaenderung, keine MCU-Kommandos oder Uploads.
Vier gezielte .gitignore-Ausnahmen machen die ausgewaehlten T5-/T6-Rohdateien
fuer einen normalen Ergebniscommit sichtbar; andere bench_-Logs bleiben ignoriert.

## Fingerprints der unveraenderten Rohdateien

| Datei | SHA-256 |
| --- | --- |
| T3/Roll.csv | 6287954d85528334122cc9598e4310266e445a97c60b50ef919191ff8c994316 |
| T3/Roll.json | 372a7f81e40ff37277072c39624521ee0ca7d967cb03a0a3a2cdc4d045307bdc |
| T3/Nick.csv | b88f88038d064432ba52bf3e747fd72ccc374cd4196df5059419e8dbab6c8a17 |
| T3/Nick.json | 845b90eb944a4cf1adea985a7b49b587e3f18883aeae205c0b4ec9c89be77020 |
| T3/Yaw.csv | 47eeaa7b9ab96fa20f1b0e22d7d7bc894c6e90c2c1f9728f24421eeaff681c9a |
| T3/Yaw.json | 10098fdb0cdd04cd740fa58046842f173e6b33c0bed8c9f45fea22c25dbe9b86 |
| T5/bench_124724.csv | 5c9e34b5fd9a86d96aac5e9a939f8fa3090b06005a284d435d16361f84c49f65 |
| T5/bench_124724.json | 020daca7966f217ce5a9a1d74886151376e98c120a5242ddb0e16ce88cc40201 |
| T6/bench_292509.csv | 322d6841d8d0e1de88d8d752849c5c69215d9df9066df99cb787b64d160b02c1 |
| T6/bench_292509.json | 056a989c994c81d9599e8445c560dd5e254ba68d5e527cb27f04e8882218aa7b |
