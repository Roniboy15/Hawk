# Validierung — v0.2.2-bench

Hostlauf am 2026-10-13: 68 automatische Tests bestanden, CPython 3.9.6.
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
- Nick-/Gier-Vorzeichenpaar -1/-1 bewahrt MANUAL-Pulsrichtung und ordnet
  Nase-hoch/Rechtsgier negativen Koerperkommandos zu. Beide Knueppelrichtungen
  aller drei Achsen erzeugen in MANUAL/STABILIZE die gleiche Pulsrichtung.
  Nick-/Gier-Gegenkorrektur wird auch am berechneten PWM-Puls geprueft.

Beim ersten Hostlauf mit den neuen Zeichen scheiterten zwei alte Erwartungen
an positive Nick-/Gierkommandos bei 1800-us-RX. Sie wurden wie beim Rolltest
an die konfigurierte RX-Polung angepasst; zusaetzliche Pulspruefungen sichern
die zweite Vorzeichenstufe ab. Regler-/Filteralgorithmen und Gains sind unveraendert.

## Besitzerbericht: Roll-Tischtest am 2026-10-12

Der Besitzer bestaetigt korrekte MANUAL-Ruderwirkung und korrekte Rollstabilisierung
nach gemeinsamer Umkehr von RECEIVER.roll.sign und SERVOS.roll.sign auf -1.
Zuvor geprueft: Rechtsknueppel liefert kleinere RX-Pulse; rechte Tragflaeche
absenken ergibt positiveren angezeigten Rollwinkel.

Getesteter Rollstand (Commit 4b92223): VERSION=0.2.1-bench, AUTO_START=False, START_MODE='manual', nur Roll
aktiv, angle_gain=2.0, rate_p=2, rate_i=0, Servo-Limit=200 us, Trim=0.
Der damalige MANUAL-Startmodus war ein bewusstes Tischtestprofil; SENSOR bleibt
der erste Schritt fuer neuen/geaenderten Hardwareaufbau. Keine weitere
Gain-Erhoehung aus diesem Bericht ableiten.

Dies ist ein Besitzerbericht ueber Richtung/Funktion, keine unabhaengige
Hardwaremessung oder Flugfreigabe. Exakte MCU-Dateien, MicroPython-Version,
Kalibrierdatei, Worst-Case-Zeiten und Versorgungsmessungen sind noch nicht archiviert.
Die unten aufgefuehrten elektrischen/Timing-/Fehlerpruefungen bleiben offen.

Der Besitzer schloss den grundlegenden Roll-Funktionstest ab. Der Folgecommit
4716a63 bereitete v0.2.2 fuer Nick/Gier vor: SENSOR, Roll+Nick, nur Roll als
richtungsgeprueft markiert. Das ist der historische Vorbereitungsstand.

## Besitzerbericht: alle Achsen, Eingang am 2026-10-13

Der Besitzer meldet alle Achsentests bestanden und die Sender-/Servozeichen
nach unserer Koerperkonvention angepasst. Der lokale Diff gegen 4716a63 zeigt
Roll/Nick/Gier aktiv, alle als richtungsgeprueft markiert, STABILIZE als Testmodus
und RECEIVER/SERVOS jeweils sign=-1. Pins, Limits, Gains, I=0 und Trim=0 sind
unveraendert. Die physische Richtung/Funktion gilt als vom Besitzer bestaetigt.

Der gelieferte Auszug enthaelt 51 STABILIZE-Samples mit allen drei Ausgaengen,
neutralen Sollwerten, Gier-Gegenkorrektur passend zur Rechnung und keinen
protokollierten Puls an einer konfigurierten Grenze. Vollstaendige Auswertung,
Herkunft und Rohdaten: [TESTBERICHT_2026-10-13.md](TESTBERICHT_2026-10-13.md).
Die Samples beweisen keine mechanische Wirkung, Funkverlustreaktion,
Versorgungsreserve oder Laufzeitgrenze. Exakte MCU-Dateien, Runtime,
calibration.json und tatsaechliche physische Pinpfade sind noch nicht archiviert.

Gespeicherter Abschlussstand: VERSION=0.2.2-bench, AUTO_START=False,
START_MODE='sensor', ACTIVE_AXES und DIRECTION_CHECKED_AXES beide
('roll','pitch','yaw'), RX-/Servozeichen jeweils -1/-1. SENSOR ist die einzige
bewusste Abweichung vom gemeldeten STABILIZE-Testprofil. Er erzeugt keine MCU-PWM.
Damit ist die grundlegende Achsen-Funktionsphase abgeschlossen; naechster
Schritt ist [Fehler-/Timingqualifikation am Tisch](NAECHSTE_SCHRITTE.md).

## Offener Versorgungsbefund am 2026-10-12

Vor den ersten Signalanzeigen wurde eine kurze Unterbrechung aller berichteten
steckdosenversorgten Geraete bemerkt. Versorgung kehrte laut Besitzer von selbst
zurueck. Mac am Netzladegeraet, MCU via Mac-USB-C; BEC 5 V laut Besitzer nur an
Servos, nicht am MCU-5-V-Pin. Zeitpunkt innerhalb des Starts, Verhalten des MCU,
genauer Stromkreis und Ursache sind unbekannt. Kein Kausalnachweis zur Firmware.

Weitere Besitzerangaben: BEC-Aufschrift 5 V @ 3 A, zusaetzlich 20 A; vier Servos.
Hoehen-/Seitenrudersignale waren zu diesem Zeitpunkt noch direkt am Receiver.
Der spaetere Funktionstest klaert die Ursache der Unterbrechung nicht.
Bestmoegliche Diagnose und begrenzter Niedervolt-Testaufbau ohne angeschlossenes
Mac-Netzladegeraet: [VERSORGUNG_WARNHINWEISE.md](VERSORGUNG_WARNHINWEISE.md).
Softwarevorbereitung geht weiter; daraus folgt keine elektrische Freigabe und
keine Erlaubnis, einen Netzfehler absichtlich zu reproduzieren.

## Weiterhin ohne unabhaengigen Hardware-/Messnachweis

- PIO-Programm/StateMachines und elektrische Pegel auf dem konkreten Board.
- Exakte Sensoridentitaet, Skalierung und Filtergenauigkeit unter Last/Vibration;
  grundlegende Funktion wird inzwischen vom Besitzer bestaetigt.
- Servoversorgung bei drei Achsen, BEC-Einbrueche, Brownouts/Busblockaden.
- Worst-Case-Laufzeiten inklusive Ausgabe, Garbage Collection, Interrupts.
- Gemessene mechanische Grenzen und reproduzierbare quantitative Ruderwirkung;
  grundlegende Richtung aller drei Achsen wurde vom Besitzer bestaetigt.
- Flugzeugdynamik, Kurvenflug, Stall, Hoehen-/Energieverhalten.
- Funkverlust, Reichweite, Antenne und Verhalten bei gehaltenen RX-Pulsen.
- PIO-Neustart/FIFO-Leerung auf dem Board, insbesondere bei anliegender High-Phase.
- Garantierte Reaktionszeit bei permanentem Bus-/CPU-Haenger oder fehlerhafter
  PWM-Abschaltung; unabhaengiger Hardware-Bypass fehlt.
- Archiv der konkreten MCU-Dateien/Runtime/Kalibrierung und physischen Pinpfade;
  Konsolensamples und Richtungsbestaetigungen ersetzen diese Erfassung nicht.
- Anti-Windup bei Servo-Trim plus nonzero rate_i bleibt offen. Fuer Tischtests rate_i=0.

Ein bestandener Hosttest ist kein Flugtest. Nach Hardware-/Polungsaenderungen
betroffene Richtungsbestaetigung zuruecknehmen und SENSOR, MANUAL, dann STABILIZE
wiederholen. Anleitungen: [ROLL_TISCHTEST.md](ROLL_TISCHTEST.md) und
[PITCH_YAW_TISCHTEST.md](PITCH_YAW_TISCHTEST.md). Keine Aussagen zur Flugtauglichkeit.
