# F2 MANUAL 0.1.6: Zeitabschnitt eingegrenzt, IMU-Messbereich offen

Quelle: unveraenderte flight_385195_0.json/CSV und Besitzerkonsole.
283.299 s, ein Segment, 218 Samples/224 CSV-Zeilen, Sequenzen 0..223 korrekt.
BOOT-Stop/shutdown_ok, errors leer, kein voller Puffer. GPS2264 Saetze ohne
Pruefsummen-/Parse-/Pollgapfehler, weiterhin kein Fix. Kein bestandener Gesamttest.

## Zwei getrennte Ereignisse

1. t=187877 ms: IMU meldet Rohwert-Saettigung, IMU_RUNTIME wird verriegelt.
   Besitzer bestaetigt: Hawk lag ruhig, nur Ruder wurden bewegt. MANUAL bleibt
   aktiv; der betroffene geloggte Datensatz hat keine gueltigen IMU-Werte.
   Konsole meldet Saettigung zweimal; ein einzelner 1-Hz-Log kann Peaks verpassen.
   Welcher Rohkanal betroffen war, ist mit 0.1.6 nicht rekonstruierbar.
2. t=191824 ms: Periode53.154 ms >50 ms, TIMING-Erkennung zaehlt einmal.
   Schon vorhandenes IMU_RUNTIME bleibt als Faulttext stehen. Unabhaengig davon
   verwerfen die Zeitwaechter alle RC-Kanaele und setzen alle Ausgaenge1500 us.
   Frische Pulse nach25 ms, MANUAL t=192397 ms: Unterbrechung573 ms.
   Das ist keine nachgewiesene Funkstoerung und nicht allein eine Folge der
   zuvor gemeldeten IMU-Saettigung.

Worst-Period gehoert zur vorigen Iteration10975. Phasen (us):
IMU/Lage30284, Steuerung3470, Diagnose596, BOOT388, GPS8964, Baro2328,
CH3633, Record/LED5339, Rest1049, ausserhalb103. Zusammen53154.
Der geplante GC-Aufruf liegt im Rest und erklaert dessen langsame IMU-Phase
nicht. Automatische GC innerhalb der IMU-/Lagearbeit ist eine plausible,
nicht direkt gemessene Ursache. GC max24.746 ms; mittlere Periode17.569 ms.
Vibration oder elektrische/Busstoerung als Ursache der Saettigung bleiben
Hypothesen. Keine dieser Ursachen ist aus den fehlenden Rohwerten beweisbar.

## Kleine Entlastung 0.1.7 und erster Rohfehler

IMU.read entpackt denselben 14-B-Puffer direkt als sieben signed Big-Endian-Werte;
Saturationmaxima und die feste Achsentransformation brauchen keine Generatoren.
Attitude.update rechnet dieselben drei/vier Komponenten ohne kurzlebige Liste
und Normierungs-/Summengeneratoren. Keine geaenderten Messbereiche, Vorzeichen,
Filtergleichungen, Gains, Zeitgrenzen, Gate- oder GC-Strategie.

Ein erster gesaettigter Rohsatz bleibt unter IMU.first_saturation erhalten,
auch nach normalen Folgemessungen. Export nach Abschaltung:
imu_first_saturation_raw = [ax,ay,az,Temperatur,gx,gy,gz] (signed Rohzaehler),
sonst null. Schwellen unveraendert32700 fuer Accel und32095 fuer Gyro.
Kein wachsender Rohdatenlog, keine zusaetzliche Datei im laufenden Betrieb.

196 Hosttests bestehen. Neue Pruefungen: analytische Mehrachsenrotation mit
wechselnden Zeitschritten, alle zwoelf signed Saettigungsgrenzen und Erholung,
Rohsatzexport bei weiterlaufendem MANUAL. Die alte read-Methode scheitert in
allen zwoelf Rohsatzfaellen; neue besteht. Firmware-AST geprueft.

Separater MicroPython1.29.0/Unix-Vergleich ohne echten Bus, 100 IMU-/Lageschritte,
GC nur im begrenzten Hostmessfenster deaktiviert: temporaerer Heapverbrauch
742496 ->508896 B,31.46% weniger. Unix64-Bit-Heap/Float und fake Bus sind keine
RP2040-Zeitmessung oder garantierte Deadline. Probe und Ausgaben:
[allocation_probe.py](allocation_probe.py), [allocation_results.txt](allocation_results.txt).
Die Probe importiert vorher/nachher gesicherte temporaere Module; fuer eine
Wiederholung passende Module sowie einen machine.py-Stub in einem separaten
Hostverzeichnis bereitstellen. Nicht auf dem Board ausfuehren.

## Naechster Besitzertest

imu.py/attitude.py/app.py/config.py ersetzen, calibration.json erhalten,
Soft-Reboot. MANUAL am Tisch, Hawk ruhig befestigt; erst etwa30 s neutral,
dann normale kleine Ruderbewegungen, insgesamt4-5 min aufnehmen. Bei Fehler
sauber stoppen und JSON/CSV/Konsole unter F2_vergleich_017 sichern.
[Bedienfolge](../../../FLUGLOGGER_TEST.md). Keine Messbereichserhoehung auf
Verdacht. Aussetzer und Saettigungsursache sind noch nicht als behoben bestaetigt.

SHA-256 der unveraenderten Rohdateien:

```text
flight_385195_0.json: 06f9958783b3a41949989e45309dcfc858944f9ebb406b0a16462078352d2af0
flight_385195_0.csv: 34d5a85bfcaf8695c56b9707b70bed9bca1e56969b1a8ea08f56ae18b3221250
```
