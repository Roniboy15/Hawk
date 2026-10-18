# T1, T1-Wiederholung und T2 — Auswertung / USB-Stromverlust

Eingang/Auswertung 2026-10-18. Besitzer meldet erwartete T1-/T2-Funktion und
starken Ruderausschlag beim USB-Trennen. Nach Rueckfrage: Ausschlag nur beim
Abziehen **ohne vorheriges Ctrl+C**, nach korrektem Beenden nicht beobachtet.
BEC/Receiver/Servos blieben dabei versorgt; direkte gemeinsame Masse blieb laut
Besitzer erhalten. Einzelruder, Dauer und elektrische Signalform sind nicht erfasst.

## Quellen und Zuordnung

Aktueller Stand: **T1-Wiederholung und T2 bestehen das Softwareprotokoll**,
jeweils mit Timingbefund. Der erste T1 hatte einen nicht geklaerten IMU_RUNTIME.
Die urspruenglichen T1.csv/T1.json wurden vom Besitzer durch den Wiederholungslauf
ersetzt. Die Rohdateien des ersten Laufs sind nicht mehr an ihrem alten Pfad vorhanden;
die bereits ausgelesenen Erstbefunde und Hashes bleiben hier getrennt erhalten.

Aktuelle Dateien wurden von der Auswertung nicht veraendert. Bytegleiche
Archivkopien sichern die aktuellen Laeufe gegen weitere Ersetzung:

- T1-Wiederholung: [CSV](archiv/T1_Wiederholung_83191/T1.csv),
  [JSON](archiv/T1_Wiederholung_83191/T1.json); Originalname laut JSON: bench_83191.csv.
- T2: [CSV](archiv/T2_57722/T2.csv), [JSON](archiv/T2_57722/T2.json);
  Originalname laut JSON: bench_57722.csv.
- Erster T1: urspruenglicher CSV-Name laut damaligem JSON bench_80968.csv.

Beide JSON-Berichte nennen v0.2.3-bench, Waveshare RP2040-Zero und MicroPython
v1.29.0 vom 2026-08-24. Repo-Basis: 4a1f889; exakte MCU-Quelldateien sind damit
nicht unabhaengig belegt. Beide melden keyboard_interrupt und shutdown_ok=true:
Sie protokollieren sauber beendete Laeufe. Der eigentliche USB-Stromverlust ist
ausserhalb des gespeicherten Laufprotokolls nicht messbar.

Die Dateien wurden T1/T2 genannt. Der CLI-Auswerter verlangt bislang den im JSON
genannten CSV-Namen. Deshalb wurden read_csv()/inspect_run() aus dem unveraenderten
tools/analyze_bench.py direkt auf die archivierten Paare angewendet.

| Datei | SHA-256 |
| --- | --- |
| T1.csv erster Lauf (ersetzt) | 6d9a06ce036535ce4fea97c99b8e4d670d9b3bf46c91d2ba5fa7853eddba5398 |
| T1.json erster Lauf (ersetzt) | ab374d77e00418f7ac907814052d5ac51446547956944717e8879bd5f09a7f58 |
| T1.csv Wiederholung | ae6d654fb54c1d9ea6683b67d4d6c42c38b619cf4909fbb3f49e74f57b7ec87b |
| T1.json Wiederholung | 60e1629bb192aeab430d0690c23229da5db1f777e00fd7b365f59987decf958e |
| T2.csv | 0aa59e6bdf8fe88bc551033fb79ca2d61b6fb87988ae3921385c28c1256dc9ba |
| T2.json | 978fb653fafbfd6b50f30beefeea7065e3421b6ca0e0bf59d2c04423d4e00eef |

## Ergebnisse aus den Daten

| Pruefung | T1 erster Lauf | T1 Wiederholung | T2 Neutralfreigabe |
| --- | --- | --- | --- |
| Softwareprotokoll | **FAIL: IMU_RUNTIME** | **PASS** | **PASS** |
| Abgeschlossene Iterationen | 5627 | 5478 | 923 |
| CSV-Zeilen vorhanden / insgesamt | 200 / 576 | 200 / 564 | 96 / 96 |
| Hard-Timing-Erkennungen / verlorene Ereignisse | 0 / 0 | 0 / 0 | 0 / 0 |
| Max. Startabstand | 28.917 ms | 29.624 ms | 30.799 ms |
| Max. work-Zeit | 28.297 ms | 29.003 ms | 29.988 ms |
| work > 10 ms | 658 (11.69 %) | 752 (13.73 %) | 139 (15.06 %) |
| Mittlere Frequenz aus Startabstand | ca. 95.02 Hz | ca. 94.27 Hz | ca. 93.54 Hz |

**Erster T1 (vor Ersetzung ausgelesen):** Alle gespeicherten Servowerte sind 0, Ereignisse haben pwm=false.
Der Software-Nachweis fuer SENSOR ohne Ausgang stimmt. Bei ms=51228, Iteration
4837, wird jedoch IMU_RUNTIME verriegelt; 791 abgeschlossene Iterationen tragen
diesen Fault. Der Modus bleibt SENSOR, weil select_mode() SENSOR auch bei Fault
so benennt. Lage/Gyro werden ab dann nicht mehr aktualisiert. Der vollstaendige
Lauf gilt nicht als fehlerfrei bestanden, auch wenn vor 30 s noch kein Fault vorlag.

IMU_RUNTIME kann aus Sensor-/Buszugriff, Saettigungspruefung oder Filterrechnung
kommen. Der konkrete Exceptiontext steht nur in der Konsole, nicht in diesen
Dateien. I2C-Fehler oder Saettigung sind Hypothesen. Benoetigt wird die vorhandene
Zeile `Automatik aus: ...`; keine Fehlergrenze auf Verdacht vergroessern.

**T1-Wiederholung:** letzte CSV-Zeit 58085 ms, 5478 abgeschlossene Iterationen,
fault_iterations leer, ausschliesslich SENSOR und keine PWM-Konstruktion. Damit
ist dieser Wiederholungslauf fehlerfrei im Softwareprotokoll. Die Wiederholung
beweist nicht die Ursache oder Beseitigung des Fehlers im ersten Lauf.

**T2:** RX_TIMEOUT beim Anlauf, WAIT_NEUTRAL ab ms=29 ohne PWM, neutral_count=0
bei ausgelenktem Rollkanal. Bei ms=4262 wird nach genau 25 gemeinsamen
Neutralframes MANUAL mit 1500-us-Kommandos auf allen Achsen aktiv. Keine Faults.
Aktive gespeicherte Pulsbereiche: Roll 1500..1520 us, Nick 1500..1541 us,
Gier 1500..1554 us, innerhalb der konfigurierten Grenzen. Physische Funktion
vom Besitzer bestaetigt; GPIO-Signalform und Zwischenwerte sind nicht gemessen.

**Timing:** Kein beobachteter Wert erreicht die 50-ms-Abbruchgrenze. Die
100-Hz-Zielperiode wird nicht durchgaengig erreicht. Ursache (Konsole/GC/I2C/
Diagnose usw.) unbekannt. Gains und Deadline nicht zum Kaschieren aendern.

## USB-Trennen und Bedienreihenfolge

Outputs.close() setzt bei laufender CPU Duty=0, deinitialisiert PWM und treibt
GPIO-low. Das ist **keine dauerhafte 1500-us-Neutral-PWM**. Bei abruptem
Versorgungsausfall wird diese Sequenz nicht verlaesslich ausgefuehrt.

Arbeitshypothese: Ausschlag beim Verlust/Uebergang des Steuersignals mit weiter
versorgten Servos. Gemeinsame Masse ist laut Besitzer vorhanden. Konkrete Flanke,
Pegelstoerung oder Servoreaktion sind ungemessen. Signalverlust bedeutet nicht
pauschal Neutralstellung; Reaktion ist modellabhaengig
([Pololu](https://www.pololu.com/blog/17/servo-control-interface-in-detail)).
Aktive RX-Signale an unversorgtem MCU sind zusaetzlich elektrisch zu pruefen:
IO-Spannungsgrenzen gelten relativ zu IOVDD; eine Rueckspeisung/Teilverversorgung
ist hier nicht nachgewiesen
([RP2040, Tabelle 622](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)).
Kein BEC-Plus als schnelle Abhilfe an den MCU-5-V/USB-Zweig anschliessen.

Kuenftig: **Ctrl+C -> beide Speichermeldungen -> BEC-/Receiver-/Servoversorgung
aus -> Dateien bei weiterhin angeschlossenem USB ueber Thonny herunterladen ->
USB zuletzt trennen.** Ausschlag nicht nochmals absichtlich nachstellen.
Der saubere Stop war laut Besitzer unauffaellig. Ungewollter MCU-Stromausfall
bleibt ein Systemrisiko; unabhaengiger Rueckweg ist vor Flugbetrieb erforderlich.

## Damalige naechste Schritte nach T1/T2

Der folgende Plan haelt den damaligen Stand fest. T3/T5/T6 wurden anschliessend
durchgefuehrt, T4 bewusst ausgelassen. Aktueller Nachweis und verbleibende
Arbeiten: [Auswertung T3/T5/T6](AUSWERTUNG_T3_T5_T6.md) und
[NAECHSTE_SCHRITTE.md](../../NAECHSTE_SCHRITTE.md).

1. T1-Wiederholung (SENSOR ohne Ausgabe) und T2-Neutralfreigabe funktional
   akzeptieren; Abschaltreihenfolge wie oben verwenden. Weitere Wiederholungen
   in eigenen Laufordnern ablegen, keine alten Fehlerdaten ersetzen.
2. Als naechsten beaufsichtigten Test T3 im MANUAL-Profil gemaess Anleitung:
   je Kanal spannungsfrei den fehlenden Eingang vorbereiten, danach starten;
   alle PWM-Ausgaenge muessen gesperrt bleiben. Bei Fault/auffaelligem Verhalten
   stoppen und Konsole plus CSV/JSON sichern. USB nie als Teststop abziehen.
3. Vor T5-Stabilisierung den ersten Sensorbefund und Jitter/CPU-Budget untersuchen.
   Vorhandenen T1-Exceptiontext sichern, falls noch verfuegbar. Ein gezielter
   weiterer Sensor-Diagnoselauf kann mit nur MCU/IMU und getrennter BEC-Batterie
   erfolgen; fehlende RX-Werte sind dann erwartet. Keine Fehlerschwellen erhoehen.
4. T6 nicht unveraendert anwenden: Levelreferenz Nick=13.889891 Grad plus T2-
   Startanzeige pitch_down=4.63 ergibt absolut ca. 18.52 Grad, nur 1.48 Grad bis
   zur festen 20-Grad-Testgrenze. Das belegt keinen Kalibrierfehler, verlangt aber
   eine zur tatsaechlichen Referenz passende Testgrenze/Richtung.
