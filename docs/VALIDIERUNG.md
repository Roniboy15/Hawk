# Validierung — v0.2.0-bench

24 automatische Hosttests bestanden. Alle Firmwaredateien werden zusaetzlich
auf Python-Syntax geprueft. Testausfuehrung: python3 -m unittest discover -s tests -v.

## Geprueft

- RC-Mitte/Endpunkte inklusive asymmetrischer Wege und stetiger Totzone.
- Freigabe nur bei neuen Frames; Trimmen nach Freigabe bleibt aktiv.
- RX-Verlust fordert neue Freigabe und neutralisiert.
- Lageinitialisierung aus Gravitation, Roll/Nick/Gier-Integration, Normierung.
- Rollintegration ueber 70 Grad ohne Fehler; kuerzester Weg ueber +/-180 Grad.
- Vorzeichen der Beschleunigungs-Driftkorrektur.
- Quaternionfehler im Koerperrahmen bei kombiniertem Roll/Nick.
- Begrenzte Servoausgaenge inklusive Trim und Vorzeichen.
- Anti-Windup und Reset-Verhalten der Regler.
- Kalibrierdatei-Roundtrip und ungueltige Kalibrierungen/Transformationen.
- Begrenzter Logring und Reihenfolge.
- Echte app.run()-Zustandslogik mit simulierten Hardwaremodulen:
  Startfreigabe, Steuerkommando, Sensorfehler, RX-Verlust und Timingfehler.
- SENSOR-Modus ohne PWM, gemeinsame Roll-/Nickausgaenge, Gier-Sollrate.

## Nicht auf Hardware geprueft

- PIO-Programm/StateMachines und elektrische Pegel auf dem konkreten Board.
- Registerzugriffe/Filterverhalten des Moduls 0x72 mit dieser neuen Firmware.
- Servoversorgung bei drei Achsen, BEC-Einbrueche, Brownouts/Busblockaden.
- Worst-Case-Laufzeiten inklusive Ausgabe, Garbage Collection, Interrupts.
- Reale Ruderwirkungen und mechanische Grenzen.
- Flugzeugdynamik, Kurvenflug, Stall, Hoehen-/Energieverhalten.
- Funkverlust, Reichweite, Antenne und Verhalten bei gehaltenen RX-Pulsen.

Ein bestandener Hosttest ist kein Flugtest. Der konkrete Upload beginnt
deshalb mit SENSOR, nur Roll aktiv, dann MANUAL, dann STABILIZE.
Nick/Gier erst schrittweise aktivieren. Keine Aussagen zur Flugtauglichkeit.
