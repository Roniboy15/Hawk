# Validierung — v0.2.1-bench

Hostlauf am 2026-10-11: 51 automatische Tests bestanden, CPython 3.9.6.
Alle 13 Firmwaredateien werden zusaetzlich per AST im RAM auf Python-Syntax
geprueft. Dies bestaetigt keine MicroPython-/PIO-Kompilation oder Board-Laufzeit.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## Geprueft

- RC-Mitte/Endpunkte inklusive asymmetrischer Wege und stetiger Totzone.
- Freigabe nur bei neuen Frames; Trimmen nach Freigabe bleibt aktiv.
- RX-Verlust fordert neue Freigabe und neutralisiert.
- Lageinitialisierung aus Gravitation, Roll/Nick/Gier-Integration, Normierung.
- Rollintegration ueber 70 Grad ohne Fehler; kuerzester Weg ueber +/-180 Grad.
- Vorzeichen der Beschleunigungs-Driftkorrektur.
- Quaternionfehler im Koerperrahmen bei kombiniertem Roll/Nick.
- Begrenzte Servoausgaenge inklusive Trim und Vorzeichen.
- Symmetrische Anti-Windup-Grenzen der Regler (kein Trim/I-Integrationstest).
- Kalibrierdatei-Roundtrip und ungueltige Kalibrierungen/Transformationen.
- Begrenzter Logring und Reihenfolge.
- Echte app.run()-Zustandslogik mit simulierten Hardwaremodulen:
  Startfreigabe, Steuerkommando, Sensorfehler, RX-Verlust und Timingfehler.
- SENSOR-Modus ohne PWM, gemeinsame Roll-/Nickausgaenge, Gier-Sollrate.
- Echte Receiver.poll()-Logik mit simuliertem PIO-FIFO: unbekannter Startpuffer,
  konservatives Alter, Pollpause, voller FIFO, ungueltige Pulse, Tick-Umlauf
  und begrenztes Lesen auch bei gleichzeitig eintreffenden Worten.
- Verzoegerter Read: bereits der erste Ausgang nach Rueckkehr ist neutral;
  neue Neutralframes erlauben manuellen Ersatz, aber keine erneute Automatik.
- Verzoegerte RC-/Reglerrechnung startet keine PWM; langsamer PWM-Start wird
  nach Rueckkehr neutralisiert. MANUAL/SENSOR behandeln Zeitverlust ebenfalls.
- Ungueltige Scheduler-/Regler-/Sensorparameter und NaN-Trim werden abgelehnt;
  Fehlkonfiguration verhindert jede Hardware-Konstruktion im App-Start.
- Ctrl+C bei partiellem PWM-/PIO-Start und Cleanupfehler: weitere Abschaltversuche,
  Receiver-Abschaltung nach PWM-Fehler, kein falscher Erfolg/Flash-Logexport.

## Nicht auf Hardware geprueft

- PIO-Programm/StateMachines und elektrische Pegel auf dem konkreten Board.
- Registerzugriffe/Filterverhalten des Moduls 0x72 mit dieser neuen Firmware.
- Servoversorgung bei drei Achsen, BEC-Einbrueche, Brownouts/Busblockaden.
- Worst-Case-Laufzeiten inklusive Ausgabe, Garbage Collection, Interrupts.
- Reale Ruderwirkungen und mechanische Grenzen.
- Flugzeugdynamik, Kurvenflug, Stall, Hoehen-/Energieverhalten.
- Funkverlust, Reichweite, Antenne und Verhalten bei gehaltenen RX-Pulsen.
- PIO-Neustart/FIFO-Leerung auf dem Board, insbesondere bei anliegender High-Phase.
- Garantierte Reaktionszeit bei permanentem Bus-/CPU-Haenger oder fehlerhafter
  PWM-Abschaltung; unabhaengiger Hardware-Bypass fehlt.
- Nick-Vorzeichenkonvention und Anti-Windup bei Servo-Trim plus nonzero rate_i
  sind noch offen. Fuer den Roll-Tischtest rate_i=0 belassen.

Ein bestandener Hosttest ist kein Flugtest. Der konkrete Upload beginnt
deshalb mit SENSOR, nur Roll aktiv, dann MANUAL, dann STABILIZE.
Siehe [ROLL_TISCHTEST.md](ROLL_TISCHTEST.md). Nick-Vorzeichen zuerst aufloesen,
weitere Achsen anschliessend schrittweise aktivieren. Keine Aussagen zur Flugtauglichkeit.
