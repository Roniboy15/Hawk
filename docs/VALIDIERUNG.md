# Validierung — v0.2.3-bench

Letzter Hostlauf am 2026-10-18: 120 automatische Tests bestanden, CPython 3.9.6
(94 bestehende Steuerungstests und 26 neue Sensortests).
Alle 18 Firmwaredateien und der Hostauswerter werden zusaetzlich per AST im RAM auf Python-Syntax
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

## Neu hostgeprueft fuer v0.2.3

- Je Roll/Nick/Gier: fehlender Eingang verhindert alle drei PWM-Ausgaenge;
  Kanalverlust neutralisiert alle, Rueckkehr mit nichtneutralem Knueppel sperrt
  weiter, neue gemeinsame Neutralframes geben MANUAL wieder frei.
- Automatikfaults IMU_RUNTIME, PITCH_RANGE und TIMING bleiben bei drei aktiven
  Achsen verriegelt; gueltiger RX ermoeglicht nur manuellen Ersatz.
- Per-Iteration-Zeitmaxima/Zaehler, Ausnahme der ersten Startdifferenz, begrenzter
  Ereignisring mit Ueberschreibzaehler, Tick-Umlauf und unbekanntes RX-Alter.
- Verzögerte Konsole steckt in work/period; nach Rueckkehr erkennt der naechste
  Loop den Timingverlust. Auch vor Ausgabe erkannte Controllerlatenz wird gezaehlt.
- Modus-/Fault-Wechsel werden zwischen periodischen CSV-Samples erfasst.
- JSON mit Konfiguration/Runtime/geladenen Kalibrierwerten erst nach bestaetigter
  Abschaltung; Start-/Cleanupfehler exportieren keinen Laufbericht.
- Frische, unveraenderte PWM-Pulse bleiben als gueltige Eingaben sichtbar:
  kein falscher Anspruch, damit Funkverlust erkannt zu haben.
- Expliziter bench_test-Einstieg blockiert AUTO_START=True/ungueltige Profile,
  stellt RAM-Modus/20-Grad-Testgrenze nach Startfehler und Ctrl+C wieder her.
- Hostauswerter akzeptiert passende Softwarefolgen, lehnt falsche Pulse/Faults,
  fehlende Felder/JSON, NaN, unvollstaendige Zeitstatistik und verlorene Ereignisse
  als PASS ab. CLI-Dateipaar und JSON-Roundtrip geprueft.

Keiner dieser Hosttests greift auf reale PIO/PWM/I2C zu. Neu eingegangene physische
T1-/T2-/T3-/T5-/T6-Ergebnisse sind unten getrennt erfasst. Die **Testanleitung T1–T6** steht in
[FEHLER_TISCHTEST.md](FEHLER_TISCHTEST.md), Vorlage:
[TESTPROTOKOLL_FEHLER.md](TESTPROTOKOLL_FEHLER.md). Sensor-/Zeitfehler bleiben
hier hostsimuliert; T6 prueft physisch nur den echten Winkelgrenz-Fault.

## Physische T1-/T2-Berichte, Eingang 2026-10-18

Die bereitgestellten JSON/CSV-Daten bestaetigen T2-Neutralfreigabe: nach
WAIT_NEUTRAL erst mit 25 gemeinsamen Neutralframes MANUAL/PWM. Erster T1:
SENSOR ohne PWM, aber IMU_RUNTIME bei 51.228 s, somit als Gesamtlauf FAIL.
Die nachgereichte T1-Wiederholung laeuft ca. 58 s ohne Fault/PWM und besteht
das Softwareprotokoll. Der erste Fehler bleibt ohne Exceptiontext ungeklärt.
Die ersten T1-Rohdateien wurden durch die Wiederholung ersetzt; Erstbefunde
und getrennte Fingerprints sowie Archivkopien der aktuellen Laeufe stehen in der
[Auswertung](testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T1_T2.md).

Kein harter Timingtrip, aber work-Maxima ca. 29–30 ms und wiederholte
10-ms-Ueberschreitungen: 100 Hz noch nicht durchgaengig qualifiziert. Runtime
und geladene Kalibrierung sind jetzt in den JSON-Dateien dokumentiert; konkrete
MCU-Quelldateien, GPIO-Signalformen und elektrische Reserve bleiben offen.

Besitzer bestaetigt extremen Ruderausschlag nur beim USB-Abziehen ohne Ctrl+C,
bei weiter versorgtem BEC/Receiver/Servos und erhaltener gemeinsamer Masse.
Korrekter Stop war unauffaellig. Das Ereignis ist keine widerlegte Software-
Pulsgrenze, sondern ein offener Systembefund bei MCU-Stromverlust; genaue
Signalursache ist ungemessen. Korrigierte Stop-/Downloadfolge in der Anleitung.
Die spaeter gemeldeten T3/T5/T6 stehen im folgenden Abschnitt. Wiederholungen
von T6 muessen die absolute Grenze und die aktuelle Levelreferenz beruecksichtigen.

## Physische T3-/T5-/T6-Berichte, Eingang 2026-10-18

Der Besitzer meldet alle drei Tests wie geplant funktional bestanden; **T4 bleibt
auf seinen Wunsch OFFEN**, weil kein Signalschalter eingebaut wurde. Die Rohdaten
bestaetigen T3 fuer jeden fehlenden Startkanal: die anderen Kanaele liefern neue
Pulse, RX_TIMEOUT bleibt aktiv, alle drei Ausgaenge ohne PWM. T5 bleibt nach
Neutralfreigabe ca. 95 s ohne Fault in STABILIZE. Nur ein T5-Laufpaar liegt vor.

T5 verfehlt das 100-Hz-Ziel: mittlerer Startabstand 13.347 ms (74.92 Hz),
work-Mittel 12.605 ms, Maximum 32.323 ms, 7132/7172 Iterationen ueber 10 ms.
Keine harte 50-ms-Ueberschreitung. Funktion bestanden, Timing weiter offen.

T6 verriegelt PITCH_RANGE bei 15.696 s nach zuvor aktivem STABILIZE und geht
in MANUAL_FALLBACK. Ab 49.402 s folgt zeitweiser Gier-Pulsverlust; zuletzt
RX_TIMEOUT bis zum Stop. Alle Ausgaenge dann Trimneutral, kein erneutes
STABILIZE. Nachtrag des Besitzers: ein Stecker war herausgefallen. Das ist die
vom Besitzer bestaetigte Ursache, passend zum protokollierten Gier-Pulsverlust;
kein weiter ungeklaerter Empfangsfehler. Verbindung vor Wiederholungen sichern.
Die zusaetzliche Folge ersetzt nicht den vorbereiteten T4-Verlust-/Wiederfreigabetest.
Auswertung, Originalpaare und Fingerprints:
[T3/T5/T6](testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T3_T5_T6.md).
Die danach geaenderte Projektprioritaet ist Sensorfunktion und anschliessend
MANUAL-Datenerfassung. Timing-/Faultdiagnose bleibt offen und wird fortgesetzt;
Reglerwerte bleiben unveraendert. Erster T1-IMU_RUNTIME bleibt ungeklärt.

## GPS-/Barometer-Vorbereitung, 2026-10-18

Tischtestabschluss 913a9e6, neuer Branch codex/gps-baro-bringup. Der Besitzer
akzeptiert den fehlenden unabhaengigen manuellen Rueckweg fuer seine geplanten
MANUAL-Datenfluege durch den MCU. Das ist keine Verifikation der Ausfallsicherheit.
Neue Sensoren werden zuerst separat ohne app/PWM geprueft; noch keine echten
GPS-/Barometer-Messdateien oder Flugnachweise vorhanden.

26 neue Hosttests pruefen:

- NMEA-Pruefsumme, geteilte Datenpakete, mehrere Talker, Koordinaten/Vorzeichen,
  Einheiten, No-Fix, Zeitablauf, abweichende UTC-Epochen, Kurs im Stillstand,
  ungueltige Felder und begrenzte UART-/Rahmenverarbeitung.
- MS5611-Datenblattvektor 100009 Pa / 20.07 C, CRC-Testvektor aus AN520,
  korruptes PROM, zweite Temperaturordnung, Messbereich, verzoegerte ADC-Abfrage,
  volle Wandlungswartezeit auch nach langsamem Busbefehl,
  Tick-Umlauf, mehrdeutige Adressen und relative Hoehenrichtung.
- Import ohne Hardware, Konflikte mit bestehenden GPIOs, Ctrl+C, UART-Cleanup
  auch nach Teilstart, verriegelte Sensorfehler, CSV-/JSON-Export nach Stop und
  Vermeidung des Ueberschreibens frueherer Laeufe.

Diese Tests bestaetigen weder Kabelfarben/Signalpegel noch die echte GY-63-
Platinenbeschaltung, GPS-Genauigkeit oder eine 100-Hz-Steuerung mit Zusatzsensoren.
Sensorstarter-Timing ist kein MANUAL-Regelkreistiming. Konkrete Tests und Grenzen:
[SENSOREN_TEST.md](SENSOREN_TEST.md).

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

Gespeicherter Abschlussstand f66ccd1: VERSION=0.2.2-bench, AUTO_START=False,
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
- Archiv der konkreten MCU-Quelldateien und Nachweis der physischen Pinpfade;
  Runtime-/Kalibrierungssnapshots sind inzwischen in den v0.2.3-JSONs enthalten.
- Anti-Windup bei Servo-Trim plus nonzero rate_i bleibt offen. Fuer Tischtests rate_i=0.

Ein bestandener Hosttest ist kein Flugtest. Nach Hardware-/Polungsaenderungen
betroffene Richtungsbestaetigung zuruecknehmen und SENSOR, MANUAL, dann STABILIZE
wiederholen. Anleitungen: [ROLL_TISCHTEST.md](ROLL_TISCHTEST.md) und
[PITCH_YAW_TISCHTEST.md](PITCH_YAW_TISCHTEST.md). Keine Aussagen zur Flugtauglichkeit.
