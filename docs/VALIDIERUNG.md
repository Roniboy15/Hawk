# Validierung — v0.2.2-bench

Hostlauf am 2026-10-12: 66 automatische Tests bestanden, CPython 3.9.6.
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
- Roll-Vorzeichenpaar: MANUAL-Pulse bleiben erhalten, kleinerer RX-Puls fordert
  positive Bank. Echte App-Logik plus reine Servo-Pulsrechnung prueft gleiche
  Knueppelrichtung in MANUAL/STABILIZE und Gegenkorrektur bei +/-10 Grad Bank.
- Negative Koerper-Nickanzeige bei Nase hoch und Pitch-Gegenkorrektur in beiden
  Richtungen. Gier-Gegenkorrektur bei Links-/Rechtsrate und Rueckkehr zur Trimlage
  nach Stop an neuer Richtung, ohne absolutes Kurs-Halten.
- Unbestaetigte neue Achse blockiert STABILIZE vor Hardwarestart; MANUAL bleibt
  fuer die Richtungspruefung erreichbar. Fehlender CH2 blockiert beide Achsen,
  CH2-Verlust neutralisiert beide.
- Selektive Nick-RC-Kalibrierung bewahrt Roll/Level; nicht aktive Achsen werden
  vor PIO-Start abgelehnt. Startphasenreihenfolge und erweiterte CSV-Spalten stimmen.
- Langsame PWM-Start-Diagnose ueberschreitet Deadline und erzeugt keine PWM.

## Besitzerbericht: Roll-Tischtest am 2026-10-12

Der Besitzer bestaetigt korrekte MANUAL-Ruderwirkung und korrekte Rollstabilisierung
nach gemeinsamer Umkehr von RECEIVER.roll.sign und SERVOS.roll.sign auf -1.
Zuvor geprueft: Rechtsknueppel liefert kleinere RX-Pulse; rechte Tragflaeche
absenken ergibt positiveren angezeigten Rollwinkel.

Getesteter Rollstand (Commit 4b92223): VERSION=0.2.1-bench, AUTO_START=False, START_MODE='manual', nur Roll
aktiv, angle_gain=2.0, rate_p=2, rate_i=0, Servo-Limit=200 us, Trim=0.
Der aktuelle MANUAL-Startmodus ist ein bewusstes Tischtestprofil; SENSOR bleibt
der erste Schritt fuer neuen/geaenderten Hardwareaufbau. Keine weitere
Gain-Erhoehung aus diesem Bericht ableiten.

Dies ist ein Besitzerbericht ueber Richtung/Funktion, keine unabhaengige
Hardwaremessung oder Flugfreigabe. Exakte MCU-Dateien, MicroPython-Version,
Kalibrierdatei, Worst-Case-Zeiten und Versorgungsmessungen sind noch nicht archiviert.
Die unten aufgefuehrten elektrischen/Timing-/Fehlerpruefungen bleiben offen.

Der Besitzer schliesst diesen grundlegenden Roll-Funktionstest ab. Naechster
Schritt ist SENSOR fuer Nick, dann MANUAL-Zeichenpruefung und STABILIZE, danach
Gier. v0.2.2 ist dafuer vorbereitet: SENSOR, Roll+Nick, DIRECTION_CHECKED_AXES
enthaelt bislang nur Roll. Ein direkt am Receiver betriebenes Hoehen-/Seitenruder
belegt noch keine Pruefung seiner MCU-Regelung.

## Offener Versorgungsbefund am 2026-10-12

Vor den ersten Signalanzeigen wurde eine kurze Unterbrechung aller berichteten
steckdosenversorgten Geraete bemerkt. Versorgung kehrte laut Besitzer von selbst
zurueck. Mac am Netzladegeraet, MCU via Mac-USB-C; BEC 5 V laut Besitzer nur an
Servos, nicht am MCU-5-V-Pin. Zeitpunkt innerhalb des Starts, Verhalten des MCU,
genauer Stromkreis und Ursache sind unbekannt. Kein Kausalnachweis zur Firmware.

Weitere Besitzerangaben: BEC-Aufschrift 5 V @ 3 A, zusaetzlich 20 A; vier Servos.
Hoehen-/Seitenrudersignale noch direkt am Receiver. Ursache bleibt unbekannt.
Bestmoegliche Diagnose und begrenzter Niedervolt-Testaufbau ohne angeschlossenes
Mac-Netzladegeraet: [VERSORGUNG_WARNHINWEISE.md](VERSORGUNG_WARNHINWEISE.md).
Softwarevorbereitung geht weiter; daraus folgt keine elektrische Freigabe und
keine Erlaubnis, einen Netzfehler absichtlich zu reproduzieren.

## Nicht auf Hardware geprueft

- PIO-Programm/StateMachines und elektrische Pegel auf dem konkreten Board.
- Registerzugriffe/Filterverhalten des Moduls 0x72 mit dieser neuen Firmware.
- Servoversorgung bei drei Achsen, BEC-Einbrueche, Brownouts/Busblockaden.
- Worst-Case-Laufzeiten inklusive Ausgabe, Garbage Collection, Interrupts.
- Weitere Ruderwirkungen, mechanische Grenzen und reproduzierbare quantitative
  Messungen; grundlegende Roll-Richtung wurde nur vom Besitzer bestaetigt.
- Flugzeugdynamik, Kurvenflug, Stall, Hoehen-/Energieverhalten.
- Funkverlust, Reichweite, Antenne und Verhalten bei gehaltenen RX-Pulsen.
- PIO-Neustart/FIFO-Leerung auf dem Board, insbesondere bei anliegender High-Phase.
- Garantierte Reaktionszeit bei permanentem Bus-/CPU-Haenger oder fehlerhafter
  PWM-Abschaltung; unabhaengiger Hardware-Bypass fehlt.
- Physische Sender-/Servozeichen von Nick/Gier sind noch offen. Die Koerperkonvention
  ist dokumentiert/hostgetestet; Checkbox ersetzt keinen Hardwaretest.
- Anti-Windup bei Servo-Trim plus nonzero rate_i bleibt offen. Fuer Tischtests rate_i=0.

Ein bestandener Hosttest ist kein Flugtest. Der konkrete Upload beginnt
deshalb mit SENSOR, nur Roll aktiv, dann MANUAL, dann STABILIZE.
Grundlegender Rolltest: [ROLL_TISCHTEST.md](ROLL_TISCHTEST.md). Naechste Achsen:
[PITCH_YAW_TISCHTEST.md](PITCH_YAW_TISCHTEST.md), je Achse erst physische Zeichen
pruefen, dann Stabilisierung. Keine Aussagen zur Flugtauglichkeit.
