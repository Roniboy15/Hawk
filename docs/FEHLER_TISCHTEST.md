# Konkreter Tischtest — v0.2.3-bench

Ziel: Startfreigabe, Signalverlust/Wiederfreigabe, verriegelten Automatik-Fault
und beobachtetes Timing pruefen. Pins, Servozeichen -1/-1, Gains und Grenzen
bleiben wie beim bestandenen Drei-Achsen-Test. Nur beaufsichtigt am Tisch.
Keine absichtliche Netzstoerung, Buskurzschluesse oder Servo-Blockaden.

## Einmal vorbereiten

1. Bisherige MCU-Dateien und calibration.json in einem eigenen Mac-Ordner sichern.
   Die Kalibrierung nicht neu erfassen, solange Montage/Sender unveraendert sind.
2. Laufende Regelung stoppen. Bei Verkabelungsaenderungen USB und BEC/Batterie
   trennen. Bestehende GPIO-Belegung: RX Roll GP2, Nick GP8, Gier GP9;
   Servo Roll GP3, Nick GP6, Gier GP7. GP sind GPIO-Nummern, keine Pinpositionen.
3. Alle **15 Pythonmodule** aus firmware/ auf den MCU laden, einschliesslich
   der neuen diagnostics.py und bench_test.py. calibration.json erhalten.
   tools/, tests/ und docs/ bleiben auf dem Mac. Danach Soft-Reboot.
4. config.py bleibt AUTO_START=False, START_MODE='sensor', alle drei Achsen aktiv,
   alle bestaetigt. Testprofile setzen den Modus nur im RAM; keine Datei-Aenderung
   fuer T1–T6 erforderlich. Der Import von bench_test startet keine Hardware.
5. Vor Aktuatortests die vorhandene Niedervoltversorgung beurteilen:
   [VERSORGUNG_WARNHINWEISE.md](VERSORGUNG_WARNHINWEISE.md). BEC-Aufschrift ist
   5 V @ 3 A fuer vier Servos; Stromreserve ist weiterhin unbekannt. Mac aus Akku,
   kein Netzladegeraet/Dock; gemeinsame Masse, keine BEC-Plus-Verbindung zum MCU-5-V.
   Ruder freihalten, Modell abstuetzen, Servoversorgung zum Trennen erreichbar.

Alle folgenden Pythonbloecke sind **MCU-Aufrufe fuer dich**, nicht Mac-Befehle.
Nach Soft-Reboot am `>>>`-Prompt in der **Thonny-Shell** ausfuehren. Danach
nicht zusaetzlich F5/start_test.py starten: das wuerde einen weiteren Run beginnen
bzw. je nach Thonny-Verhalten die RAM-Einstellung neu laden.

## Fuer jeden Lauf gleich

Sender/Versorgung bereit, Modell waehrend ca. sechs Sekunden Gyrokalibrierung
unbewegt lassen. Einen unten genannten Test starten. Am Ende Ctrl+C, dann auf
`PWM/PIO ausgeschaltet`, `RAM-Log gespeichert: bench_...csv` UND
`Laufbericht gespeichert: bench_...json` warten. Erst dann Versorgung trennen.
Bei unvollstaendiger Abschaltung Versorgung trennen und Ursache klaeren;
in diesem Fall wird bewusst kein CSV/JSON exportiert.

Beide Dateien **nach jedem Lauf** auf den Mac in getrennte Ordner herunterladen,
z.B. logs/T1/, logs/T2/, logs/T3-roll/. Nicht umbenennen; gleiche Nummer gehoert
zusammen. Vor dem naechsten Lauf sichern: Board-Dateinamen koennen sich bei
Neustarts wiederholen. Mechanische Beobachtung im
[Testprotokoll](TESTPROTOKOLL_FEHLER.md) notieren; Logpulse sind keine GPIO-Messung.

## T1 — SENSOR und voller Diagnose-Ring (30 Sekunden)

```python
import bench_test
bench_test.run('sensor')
```

Nach der Kalibrierung 30 Sekunden laufen lassen, davon 10 Sekunden ruhig,
dann kleine langsame Bewegungen um die Achsen. Knueppel bewegen.
Erwartet: Version 0.2.3-bench, SENSOR, plausible Winkel/RX, `servo={}` und
keine MCU-Servopulse. Der Ring wird voll und muss danach begrenzt weiterlaufen.
Das Modell muss auch ohne neue Pulse sicher liegen; Servos koennen letzte
Positionen halten. Stoppen und Dateien nach logs/T1/ sichern.

PASS: keine Resets/MemoryError/Faults, keine MCU-Ausgabe; gueltiger CSV/JSON-Bericht.
Auswertung auf dem Mac: `--expect sensor`.

## T2 — Start mit nichtneutralem Knueppel

Modell waagerecht, Rollknueppel etwa ein Viertel aus der Mitte halten, alle
anderen Knueppel neutral. Dann starten:

```python
import bench_test
bench_test.run('manual')
```

Nach Gyrokalibrierung den Knueppel noch **3 Sekunden** aus der Mitte halten.
Erwartet: WAIT_NEUTRAL, noch `servo={}`, keine neu gestartete MCU-PWM.
Dann alle Knueppel zentrieren und **2 Sekunden** warten. Erst nach 25 neuen
gemeinsamen Neutralframes darf MANUAL mit den drei Servopulsen erscheinen.
Kleine Roll-/Nick-/Gierkommandos einmal pruefen, stoppen, nach logs/T2/ sichern.

PASS: keine Aktivierung vor Neutralfreigabe; danach bekannte MANUAL-Wirkung.
Auswertung: `--expect neutral-gate`.

## T3 — Je ein fehlender Eingang beim Start

Fuer Roll, Nick und Gier **drei separate Laeufe**:

1. USB und BEC/Batterie trennen. Nur die zu pruefende RX-Signalleitung am
   MCU-Eingang trennen: GP2 / GP8 / GP9. Kein Servoausgang, Plus oder GND.
   Freies Leitungsende isolieren. Alle anderen Verbindungen unveraendert.
2. Versorgung wieder wie vorbereitet herstellen, Sender neutral. Das Profil
   `bench_test.run('manual')` aus T2 starten und nach Kalibrierung **5 Sekunden** warten.
3. Erwartet: RX_TIMEOUT, der betroffene RX-Wert fehlt, `servo={}` auf allen Achsen.
   Trotz der beiden gesunden Kanaele darf keine PWM gestartet werden.
4. Stoppen/Dateien sichern, alle Quellen trennen, Leitung exakt wiederherstellen.

PASS je Kanal: keine gemeinsame Freigabe/Ausgabe bei fehlendem Eingang.
Ordner logs/T3-roll/, logs/T3-pitch/, logs/T3-yaw/; jeweils `--expect missing-rx`.
Der interne GPIO-Pulldown haelt einen offenen Eingang niedrig. Keine bewusste
Unterbrechung der Masse; kein Kabelabziehen unter Spannung.

## T4 — Laufender Signalverlust und Wiederfreigabe

**Dafuer vorher spannungsfrei einen passenden einfachen Signalschalter einbauen.**
Er unterbricht nur den Weg Receiver-Signal -> MCU-Eingang, nicht Versorgung,
Masse oder Servosignal. Offene Stellung laesst den MCU-Eingang am internen
Pulldown; RX-/MCU-Ausgaenge nie parallel verbinden. Wenn dieser vorbereitete
Testadapter fehlt, T4 als OFFEN markieren; T1/T2/T3/T5 sind trotzdem moeglich.

```text
Receiver CH1/CH2/CH4 Signal ---- Schalter ---- MCU GP2/GP8/GP9
```

Pro Kanal einen eigenen Lauf; beim Umsetzen eines Schalters immer alle Quellen
trennen. Zu Beginn Schalter geschlossen und Knueppel neutral:

1. `bench_test.run('manual')` starten, MANUAL abwarten.
2. Rollknueppel etwa ein Viertel halten, damit eine Abweichung von Neutral
   sichtbar ist. Schalter des Testkanals oeffnen, **1 Sekunde** warten.
3. Erwartet: RX_TIMEOUT und **alle drei** Pulswerte Trimneutral, hier 1500 us.
   Auch bei Nick-/Gierverlust muss der Rollausgang neutral werden.
4. Schalter schliessen, Rollknueppel weiter aus der Mitte, **1 Sekunde** warten.
   Erwartet: WAIT_NEUTRAL; alle drei Ausgaenge bleiben Trimneutral.
5. Alle Knueppel zentrieren, **2 Sekunden** warten. Nach 25 neuen Neutralframes
   wieder MANUAL. Kleines Kommando funktioniert wieder.
6. Sofort stoppen/sichern. Die ganze Ereignisfolge nach erster Aktivierung
   innerhalb etwa 10 Sekunden halten, damit auch der CSV-Ring sie enthaelt.

PASS: MANUAL -> RX_TIMEOUT -> WAIT_NEUTRAL -> MANUAL, keine Steuerkommandos
waehrend der Sperre. Ordner logs/T4-roll/ usw.; jeweils `--expect rx-recovery`.
Die genaue Zeit vom letzten physischen RX-Puls bis zum Servoausgang benoetigt
eine Signal-/Ausgangsmessung. Konsolenanzeige mit 4 Hz und Handschalter liefern
diesen Nachweis nicht. RX_TIMEOUT_MS=100 ist eine Codegrenze, keine gemessene
Garantie bei Bus-/CPU-Haengern.

## T5 — Normale Drei-Achsen-Stabilisierung und Timing (60 Sekunden)

```python
import bench_test
bench_test.run('stabilize')
```

Nach Kalibrierung/Neutralfreigabe 60 Sekunden: 20 Sekunden ruhig, 20 Sekunden
kleine langsame Roll-/Nick-/Gierbewegungen, 20 Sekunden kleine Knueppelkommandos
und kombinierte Bewegungen. Keine neuen Gains, keine absichtlichen Blockaden.
Konsole 4 Hz und Log 10 Hz wie gespeichert. Erwartet: STABILIZE bleibt aktiv,
richtige Gegenkorrektur, keine Resets/Faults/Anschlaege oder auffaellige Versorgung.

Beim Stop gilt: TIMING-Erkennungen=0; kein gemessener Wert ueber 50000 us.
Fuer das 100-Hz-Ziel sollte `work.max_us < 10000` sein. Ein etwas groesserer
`period.max_us` kann Scheduler-Jitter enthalten; Anzahl/Maxima mit beurteilen.
Rechenzeit ueber 10 ms ist ein Befund zur Klaerung, auch ohne harten TIMING-Fault.
Maxima sind Beobachtungen jeder abgeschlossenen Iteration, keine Worst-Case-Garantie.
Nach logs/T5/ sichern; `--expect stabilize`. Fuer Reproduzierbarkeit dreimal
mit eigenen Unterordnern wiederholen, sofern der erste Lauf unauffaellig ist.

## T6 — Verriegelung eines echten Winkelgrenz-Faults

Erst wenn die vorigen Aktuatortests unauffaellig sind. Ein Helfer bzw. sichere
Auflage muss vorsichtiges Neigen des montierten Modells erlauben.

```python
import bench_test
bench_test.run('pitch-range')
```

Nur dieser Aufruf setzt die absolute Nickgrenze im RAM auf 20 Grad. Zuerst
STABILIZE bei waagerechtem Modell abwarten. Dann die Nase langsam um etwa
25–35 Grad anheben, bis `PITCH_RANGE` / MANUAL_FALLBACK erscheint. Wenn kein
sicheres Neigen moeglich ist oder STABILIZE am Anfang nicht erreicht wird, stoppen
und T6 OFFEN notieren. Nicht auf 90 Grad drehen oder den Sensor abziehen.
Die Grenze gilt fuer absoluten Sensor-Nick; pitch_down ist relativ zur
Levelreferenz (absolut = pitch_down + calibration.level.pitch).

Modell wieder waagerecht, Knueppel neutral, 3 Sekunden warten: MANUAL_FALLBACK
muss bestehen bleiben. Kleine Knueppelkommandos funktionieren; eine Neigung
darf keine aktive Gegenkorrektur mehr erzeugen. Winkel/Gyroanzeigen koennen ab
dem Fault eingefroren sein, weil die fehlerhafte Automatik keine IMU-Daten mehr liest.
Stoppen/sichern, danach Soft-Reboot; normale 75-Grad-Grenze und SENSOR sind wieder
die Datei-Defaults. Profil stellt die RAM-Werte auch bei normaler Rueckkehr wieder her.

PASS: STABILIZE -> MANUAL_FALLBACK mit PITCH_RANGE, keine automatische
Rueckkehr zu STABILIZE bei waagerechtem Modell. Nach logs/T6/; `--expect pitch-range`.
Das testet den Winkelgrenz-/Verriegelungspfad, **keinen I2C-Ausfall oder CPU-Haenger**.
IMU_RUNTIME/TIMING sind fuer diesen Schritt auf dem Host simuliert geprueft;
kein riskanter physischer Fehler wird durch den Starter eingespritzt.

## Auf dem Mac auswerten und zurueckmelden

Im Projektordner, Dateinummer durch den tatsaechlichen Namen ersetzen:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/analyze_bench.py logs/T1/bench_123.csv --expect sensor
```

Das Tool findet bench_123.json im selben Ordner. PASS gilt fuer die gespeicherte
Softwarefolge; die Ruder-/Versorgungsbeobachtung separat bewerten. FAIL oder
UNVOLLSTAENDIG bedeutet klaeren, nicht durch Neustarts uebergehen. Alte v0.2.2-Logs
haben diese Diagnosespalten nicht und reichen fuer diese Auswertung nicht.

Zurueckmelden: ausgefuelltes Protokoll, Ausgabe des Auswerters und pro Lauf beide
Dateien. Rohlogs bleiben unter logs/ ausserhalb Git. Danach entscheiden wir anhand
der Befunde ueber Timing/Empfaenger-Failsafe und den unabhaengigen Rueckweg.
Sender-Aus ist ein eigener Empfaengertest: laufend erzeugte Hold-/Failsafe-Pulse
werden vom Controller weiterhin als frische Eingaben gesehen.
