# F1 SENSOR 0.1.5: gezielter Innentest bestanden

Quelle: unveraenderte flight_344020_0.json/CSV und vom Besitzer gepostete Konsole.
137.227 s, 8796 Iterationen; stop_reason=ground_button, shutdown_ok=true.

- errors leer, keine Faults/Timing-Trips. Periode max. 49.500 ms, Arbeit
  max. 48.871 ms; mittlere Periode 15.591 ms (etwa 64.1 Hz).
- GPS durchgehend verarbeitet: 30825 Bytes, 1096 Saetze, 274 GGA/RMC-Updates,
  keine Pruefsummen-/Parse-/Pollgap-Fehler. Der bisherige MemoryError fehlt.
- Kein Positionsfix/keine GPS-Koordinaten. GPS-Bereitschaft mit gueltigen
  Koordinaten und der zugehoerige Verarbeitungspfad sind noch nicht boardgeprueft.
- Ein Segment: START bei 25.427 s, STOP bei 131.915 s, 105 Samples und
  zwei Ereignisse. CSV hat 107 Datenzeilen und lueckenlose Sequenzen 0..106.
  Sampleabstaende 1000..1036 ms; keine ueberschriebenen Records.
- Alle CSV-Zeilen SENSOR ohne Fault; servo_* immer null. IMU/Barometer in
  allen Records gueltig. Barometer 96025..96042 Pa / -0.349..1.147 m relativ.
- Startreserve 66400 B (864 B ueber Vorgabe); 170 geplante GC, max. 24.580 ms.
  Kleinster abgefragter freier Heap 11584 B, kein gemessenes Allzeitminimum.

Die GPS-Korrektur ist fuer diesen SENSOR-/No-Fix-Lauf am RP2040 bestaetigt.
Nur 0.500 ms Abstand zur 50-ms-Deadline: keine garantierte Reserve, kein Nachweis
fuer MANUAL/PWM, gueltigen GPS-Fix, zehn Minuten Aufnahme oder Flug.

Naechster Schritt: F2 MANUAL am Tisch mit denselben Dateien; CH3-Pause/Aufnahme
und identische Ruderwirkung pruefen, zwei kurze Segmente/BOOT-Export sichern.
Danach gueltigen GPS-Fix/Gruen, beabsichtigte Aufnahmedauer und eigenstaendige
Versorgung/Start im finalen Aufbau pruefen. Kein neuer Code fuer F2.
Siehe [Bedienfolge](../../../FLUGLOGGER_TEST.md).
Bei dieser Auswertung nur Dokumentation aktualisiert; keine Firmwareaenderung,
kein Hardwarezugriff und kein erneuter Hostregressionslauf (zuletzt 193 bestanden).

SHA-256 der Rohdateien:

```text
flight_344020_0.json: 991313828afe9e898e1dfa7ed49d0e69b74dd1b045956edc17095584bee327f9
flight_344020_0.csv: bae04069a9810102af3f3dd31438210dd445f6c7c6c1425fb9d2683f25bd2c71
```
