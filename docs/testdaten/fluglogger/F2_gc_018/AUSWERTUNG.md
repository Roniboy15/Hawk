# F2 0.1.8: gezielter MANUAL-Bodenvergleich bestanden

Unveraenderte CSV/JSON plus Besitzerkonsole, ausgewertet am2026-10-22.
288.274 s Gesamtlauf, ein Segment ueber276.321 s,273 Samples und Start/Stop:
275 Zeilen, Sequenz0..274 lueckenlos, Sampleabstaende1000..1044 ms.
Sauberer BOOT-Stop, shutdown_ok=true, errors leer, kein voller Puffer.

- Keine TIMING-Trips und keine Faults. Nach Startfreigabe bei560 ms durchgehend
  MANUAL in14645 Iterationen, keine erneute RX_TIMEOUT-/WAIT_NEUTRAL-Phase.
  Die anfaengliche RX_TIMEOUT-Meldung liegt vor Freigabe/PWM und ist Startzustand.
- Periode maximal45.709 ms, Arbeit44.898 ms;4.291 ms Abstand zur50-ms-Grenze.
  Mittlere Periode19.638 ms (50.92 Hz), zuvor0.1.7:15.598 ms. Haeufigere Heap-
  Pruefung/GC kostet Durchsatz; der beobachtete Aussetzer tritt hier nicht auf.
- Geplante GC1770-mal statt viermal im kuerzeren0.1.7-Lauf, maximal24.656 ms.
  Schlechteste Periode: IMU4815 us, Steuerung3393, Diagnose612, BOOT390,
  GPS1577, Baro1642, CH3459, Record/LED630, Rest32090, ausserhalb101.
  Das passt zur geplanten GC plus Heapscan am Loopende. Automatische GC bleibt
  aktiv; IMU-Phasenmax29.383 ms beweist keine vollstaendige Beseitigung
  ungeplanter GC. Kleinster abgefragter freier Heap3328 B: momentaner Wert,
  keine Aussage ueber dauerhaft freien RAM oder einen bewiesenen Speicherverlust.
- Alle275 Zeilen: MANUAL, frische Steuer-RX, Freigabe/PWM aktiv, IMU und Baro
  gueltig.825 Achsenvergleiche mit echten normalize()/command()-Funktionen
  ergeben exakt die konfigurierten Pulse. Ranges Roll1300..1700 us,
  Nick/Gier1350..1650 us. Das prueft gespeicherte Werte, keine physische Latenz.
- Keine IMU-Saettigung. Baro96525..96536 Pa, relative Hoehe-0.676..0.285 m,
  Datenalter0..126 ms. Fruehere Saettigung/Hoehensprung bleiben unerklaert.
- GPS2304 Saetze/576 Updates, keine Pruefsummen-/Parse-/Pollgapfehler, aber
  kein Fix und keine Koordinaten. Volle Verarbeitung mit gueltigem Fix offen.

Gezielter F2-Bodenvergleich hinsichtlich Softwarekontinuitaet/Export bestanden;
keine allgemeine Flugfreigabe oder physische Latenzmessung. Kein Firmwarewechsel
aufgrund dieses Ergebnisses, keine neuen Hosttests fuer reine Dokumentation.
Letzter Firmware-Regressionslauf:197 bestanden.

Naechster Schritt: Stand sichern; bewussten Loggerstart und MCU-Bordversorgung
ohne Mac festlegen. main.py/AUTO_START=True startet derzeit den alten Controller,
nicht diesen Logger; USB bei alleiniger USB-Versorgung nicht im Betrieb abziehen.
Danach kombinierter MANUAL-Bodentest draussen mit GPS-Gruen, insgesamt etwa10 min
Aufnahme in zwei CH3-Segmenten mit Pause, normale Steuerbewegungen, BOOT-Export.
GPS-Fixlast, Aufnahmedauer, Pause/Wiederaufnahme und Zeiten gemeinsam pruefen.
Bedienung: [FLUGLOGGER_TEST.md](../../../FLUGLOGGER_TEST.md).

SHA-256 der Rohdateien:

```text
flight_813555_0.json: a419872435c2c6e5bdaf2f48b1311aade4a5efbd02afeae26884ea8254e454ab
flight_813555_0.csv: 2a6d70e0e18a600357df78203e5f43a30589a2af2a625b61036ae9000ed707a9
```
