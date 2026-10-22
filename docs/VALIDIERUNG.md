# Validierung — v0.2.3-bench

Letzter Hostlauf am 2026-10-22: 201 automatische Tests bestanden, CPython 3.9.6
(106 Steuerungs-, 37 Sensor-, 30 Logger-/Puffer- und 28 Flugloggertests).

Neue physische0.1.9-Nachweise: zwei B1 plus SENSOR176.465 s und MANUAL265.652 s
draussen mit GPS. Alle BOOT-Start/Export sauber, keine Faults/Timing-Trips;
MANUAL keine erneute RC-Sperre nach Freigabe,573 gespeicherte Achsenwerte exakt.
Alle191 MANUAL-Zeilen mit GPS-Fix/ready.187 Samples in zwei Segmenten sind nur
190.294 s Aufnahme; Zehn-Minuten-Test weiter offen. Tragen/Handneigen belegt
keine Flug-Gains oder aerodynamische Reaktion. Nur Dokumentation/Rohdatenauswahl
geaendert, keine neue Firmware oder Host-Regressionsrunde.
[Auswertung](testdaten/fluglogger/AUSWERTUNG_019.md).

0.1.9 ergaenzt den optionalen BOOT-Bordstart auf demselben Branch. Vier neue
Tests sichern Default-/Legacy-/Logger-Routing und Konfliktsperre, anfaenglich
gehaltenen/kurzen Taster sowie2-s-Halten/Loslassen ueber Tick-Umlauf, Abbruch
mit Pufferfreigabe und Startreihenfolge. Export nennt start_method. Vier
geaenderte Firmwaredateien kompilieren unter MicroPython1.29/Unix; keine
Hardwareausfuehrung/Reserve- oder BEC-Qualifikation dadurch. Der spaetere B1-
Nachweis steht oben; jetzt nur langen Aufnahmelauf ergaenzen. Defaults bleiben
AUTO_START=False, START_MODE='sensor', LOGGER_BOOT_MODE=None.

Physischer F2-0.1.8-Vergleich jetzt bestanden:288.274 s ohne Timing-/Fault-
oder erneute RX-Sperre nach Aktivierung. Max45.709 ms,273 Samples/275 Zeilen
vollstaendig,825 MANUAL-Achsenwerte exakt; sauberer Export. GPS empfaengt ohne
Fehler, hat aber keinen Fix.1770 geplante GCs, min abgefragter Heap3328 B;
kein Nachweis fuer jede Last/lange Laufzeit. Nur Nachweis/Dokumentation geaendert,
keine neue Firmware/Hosttests in dieser Auswertung.
[0.1.8-Bodenbefund](testdaten/fluglogger/F2_gc_018/AUSWERTUNG.md).

F2 0.1.7 hatte erneut zwei Trips (max51.156 ms), mit541/2981 ms Unterbrechung.
0.1.8 aendert nur das Heap-Abfrageintervall200 ->20 ms. Neue Heapdruck-
Regression scheitert mit alter Einstellung, besteht mit neuer; separate echte
MicroPython/Unix-Probe zeigt71 ->0 ungeplante Heap-Anstiege. Modellierte Zeiten,
keine Boardgarantie. [Befund/Probe](testdaten/fluglogger/F2_vergleich_017/AUSWERTUNG.md).
Der einzelne test_flight_logger-Lauf braucht aktuell Hardware-Stubs aus der
Gesamtsuite (sonst zwei Importfehler); der oben genannte Gesamtlauf besteht.

0.1.7 entlastet IMU.read/Attitude.update durch direktes Entpacken/feste
Komponenten statt kurzlebiger Listen/Generatoren. Gleiches Vorzeichen-/Bias- und
Normierungsverhalten, unveraenderte Range-/Zeitgrenzen. Drei neue Tests pruefen
analytische Mehrachsenrotation, alle zwoelf vorzeichenbehafteten Rangegrenzen
mit erstem Rohsatz/nachfolgender Erholung sowie Export bei weiterlaufendem MANUAL.
Die alte read-Methode scheitert an allen zwoelf Rohsatz-Pruefungen, die neue
besteht. Host-MicroPython-Probe:31.46% weniger temporaerer Heap im IMU/Lagepfad;
keine Messung von Bus/Boardlaufzeit. Firmware-AST geprueft.
[0.1.6-Befund/0.1.7-Vergleich](testdaten/fluglogger/F2_timing_016/AUSWERTUNG.md).

F2 0.1.5 zeigt einen echten 5.129-s-Steueraussetzer nach einer 51.021-ms-
Periode: TIMING -> globales RC-Verwerfen/Neutral -> erneute Neutralfreigabe.
Frische RC-Pulse waren nach 27 ms wieder da. Ursache des langen Abschnitts
unbekannt; stage_timing war im MANUAL-Bericht null. 0.1.6 aktiviert vorhandene
Phasenfelder auch fuer MANUAL. Der bestehende 60-ms-GC-Integrationstest prueft
nun zusaetzlich diese Phasenzuordnung, scheiterte vorher und besteht danach.
193 Tests bestehen erneut; das behebt den Aussetzer noch nicht.
[F2-Befund](testdaten/fluglogger/F2_manual_015/AUSWERTUNG.md).

0.1.5 prueft NMEA-Pruefsummen mit Bytewerten statt internierten Textzeichen.
Auf MicroPython 1.29.0/Unix scheitert die alte Funktion bei fragmentiertem Heap
mit exakt dem gemeldeten 640-Fehler; die neue besteht denselben Versuch.
Zusaetzlicher Hosttest sichert ASCII-/Hex-Pruefung. Neuer Boardlauf 0.1.5:
137.227 s ohne GPS-/Komponentenfehler oder Timing-Trip, 1096 GPS-Saetze,
105 Samples und sauberer BOOT-Export. Gezielt getesteter SENSOR-Fall bestanden;
kein Positionsfix, F2 MANUAL und laengerer Lauf noch offen. Maximal 49.500 ms
laesst nur 0.500 ms zur Deadline, keine garantierte Laufzeitreserve.
[Boardbefund](testdaten/fluglogger/F1_gps_015/AUSWERTUNG.md).
[Rohdaten und Reproduktion](testdaten/fluglogger/F1_gc_014/AUSWERTUNG.md).

0.1.4 korrigiert den physisch gemeldeten 0.1.3-GC-Aufschub; der GPS-Fehler blieb.
Drei zusaetzliche Regressionen simulieren langsame Heap-Abfrage, begrenzte
Abfragefrequenz und Wiederaufnahme einer faelligen GC ohne erneuten Scan.
Alle drei scheiterten vor der Korrektur. Die vorigen Tests hatten mem_free
ohne Laufzeit modelliert und konnten diesen Fehler deshalb nicht erkennen.
Reale Boardwirkung und Ursache jedes Speicherengpasses bleiben zu pruefen.

0.1.3: zwei neue Tests fuer geplante GC nur bei niedrigem freien Heap und
kurzer bisheriger Arbeit, Aufschub bei hoher Arbeit, kein Flash im Loop.
Bestehende App-Integration injiziert jetzt echte _collect_if_due()-Aufrufe mit
60-ms-Stub-GC: TIMING/Neutralstellung bleiben wirksam. Export sichert runtime_gc.
Physischer 0.1.2-Lauf bleibt mit sieben >50-ms-Perioden offen; kein Hosttest
belegt die Wirkung der neuen Planung auf dem Board.
Firmwaredateien und Hostauswerter werden zusaetzlich per AST im RAM auf Python-Syntax
geprueft. Dies bestaetigt keine MicroPython-/PIO-Kompilation oder Board-Laufzeit.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## Geprueft

Neu eingegangener kombinierter Loggerlauf: [F1 SENSOR](testdaten/fluglogger/F1_sensor/AUSWERTUNG.md).
CH3/BOOT/RAM-Export bestaetigt, keine PWM, aber TIMING ab 7.812 s mit neun
Schleifenabstaenden >50 ms. Kein IMU-/Barometerfehler; GPS am Fenster ohne Fix.
F1 daher teilweise bestanden; gemeinsame Zeitreserve, Freiluftbereitschaft
und F2 MANUAL offen. Rohdateien, Schema/Sequenzen, Zeilenzahlen, Gueltigkeitsbits
und Abschluss separat auf Konsistenz geprueft. Bei dieser Auswertung keine
Firmwareaenderung und kein neuer Hardware-/Hostregressionslauf.

Nachfolgend Logger 0.1.1: feste Phasenfelder nur im gemeinsamen SENSOR-Profil,
vor der bestehenden RAM-Reservepruefung angelegt. Vorige Phasen werden der
naechsten gemessenen Periode zugeordnet; Export erst nach Abschaltung.
Drei neue Tests pruefen Tick-Umlauf/Zuordnung/feste Listen, getrennte lange
GPS-/Barokosten bei pausierter Aufnahme und weiter wirksamen TIMING-Fault
in der echten App. Bestehender Exporttest prueft neue JSON-Felder. Kein
gewaehlter Grenzwert/Gain geaendert; keine Board-Messung durch den Agenten.

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
Neue Sensoren werden zuerst separat ohne app/PWM geprueft. Seit 2026-10-19
liegen echte GY-63- und GPS-Einzellaeufe vor; GPS-Positionsnachweis und
Flugnachweise fehlen weiter. Details in den Ergebnisabschnitten unten.

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

## Erster GY-63-Lauf und USB-Startbefund, Eingang 2026-10-19

baro.json: 60.002 s, 594 Barometermessungen, Adresse 0x77, gueltiges PROM/CRC,
errors={}, shutdown_ok=true. Die 200 aufbewahrten CSV-Zeilen sind strukturell
konsistent, frisch/gueltig; D1/D2 ergeben exakt den gespeicherten Druck und
die Temperatur. Druck 96322..96335 Pa, Temperatur 22.67..22.78 C. Hoehe
-0.31..+0.83 m. Nachtrag des Besitzers: Hawk im selben Lauf angehoben;
relative Anzeige stieg ungefaehr um die tatsaechliche Hubhoehe. **S1 funktional
bestanden** aus Logpruefung und Besitzerbeobachtung. Absolute Genauigkeit,
Drift und Wiederholbarkeit nicht quantifiziert; die bewegte Messspanne ist
kein reines Sensorrauschen. GPS nicht angeschlossen. Sensorstarter-work im Mittel
1.100 ms, maximal 23.365 ms, kein 50-ms-Trip; kein MANUAL-Regelkreistiming.

Separater Besitzerbefund: Hoehen-/Seitenruder an GP6/GP7 beim USB-Anstecken
maximal ausgeschlagen geblieben; BEC/Receiver/Sender vorher eingeschaltet,
IMU unversorgt mit SDA/SCL/GND verbunden. Nach Kenntnis des Besitzers kein
laufendes Programm, Thonny offen. Quelle sensor_test nutzt weder IMU noch PWM;
konkrete MCU-Startdateien, GPIO-Pulse und elektrische Ursache ungemessen.
Kein Nachweis eines Regler-/Vorzeichenfehlers. Weitere Sensorchecks mit BEC
aus; vor erneutem Aktuatorbetrieb Start-/Versorgungsbefund eingrenzen.
[Rohdaten, Fingerprints, Pruefungen und Grenzen](testdaten/barometer_tests/AUSWERTUNG.md).

## Erster GPS-Aussenlauf und UART-Korrektur, Eingang 2026-10-19

180.225 s, 908 pruefsummenkorrekte NMEA-Saetze, 360 GGA/RMC-Updates,
keine Pruefsummen-/Parserfehler. Datenverbindung bestaetigt; kein protokollierter
Positionsfix. Erste Rohsaetze melden No-Fix, die spaetere Receiverloesung ist
bei 314 Pollpausen/Zustandsruecksetzungen nicht rekonstruierbar. S2 bleibt offen,
S3 noch ausstehend. Besitzer identifiziert weiss = GPS-TX bei diesem Exemplar.
TX-Spannungspegel nicht gemessen; LED-Farben sind kein Positionsnachweis.

work erreicht 423.331 ms (324/8260 >50 ms), period maximal 423.541 ms.
Im Quellcode nachgewiesenes Risiko: Feste UART-Lesemengen warten auf RP2
auch bei timeout_char=0 auf nachkommende Zeichen. Normaler Empfang und
Altdatenverwerfen lesen seit Sensor-Test 0.1.1 nur bereits verfuegbare Bytes
innerhalb ihres Mengenlimits. Zwei Tests mit eintreffenden 9600-Baud-Bytes
scheiterten vor und bestehen nach der Korrektur. Dritter neuer Test prueft
persistente Receiver-Fixzaehler getrennt vom geloeschten aktuellen Fixstatus.
Die 100-ms-Frischegrenze wurde nicht gelockert. Alle 123 Hosttests bestehen;
verbesserte physische Laufzeit und Positionsfix sind noch nachzutesten.

CSV/JSON-Struktur, Flag-/Leerwertkonsistenz, erste NMEA-Saetze und Rohdatei-
Fingerprints geprueft. Auswertung und exakte Wiederholung nach Modulupdate:
[GPS-Aussenlauf](testdaten/gps_tests/AUSWERTUNG.md). Kein MANUAL-Fluglog und
keine Servo-/Hardwarequalifikation aus diesen Host- und Sensorergebnissen.

## GPS-Wiederholung und ganze kurze Sensorlogs, Eingang 2026-10-20

gps_2: erster Fix 74.820 s, 1883 saubere NMEA-Saetze, 106 GGA-/106 RMC-
Fixsaetze, maximal 12 benutzte Satelliten, keine Pollpausen/Parserfehler.
work-Mittel 2.090 ms, Maximum 33.329 ms, keine 50-ms-Ueberschreitung;
weiterhin nur Sensorstarter-Timing. CSV enthaelt die letzten 40.735 s, die
nachgereichte Konsole den frueheren West-/Sued-Hinweg und Ost-/Nord-Rueckweg.
S2 funktional bestanden mit Besitzerbeobachtung, keine vermessene absolute
Genauigkeit. Dateiversion noch 0.1.0 trotz neuer Zaehler; vor S3 konsistenten
Dateisatz/Soft-Reboot sicherstellen. [Auswertung](testdaten/gps_tests/AUSWERTUNG_GPS_2.md).

Auf Besitzerwunsch ab Sensor-Test 0.2.0 ganzer kurzer Lauf im gepackten RAM,
standardmaessig 2 Hz, statt Ueberschreiben nach 200 Zeilen. Sechs neue Hosttests:
voller 180-s-Export mit Anfang/Ende, gepackte Koordinaten/Leerwerte/Flags,
Mitternacht/Schaltsekunde/Datum, Ueberlauf ohne Ueberschreiben sowie Groessen-
und RAM-Limit vor Hardwarestart. Vorhandener Exporttest prueft weiter UART-
Abschaltung vor CSV-Schreiben. Alle 129 Tests bestehen. Neue Speicherung
physisch noch zu validieren: der inzwischen eingegangene S3-Lauf verwendet
weiter 0.1.0 / Schema 1. app/bench-Regelkreis bleibt unveraendert.

## S3 gemeinsam und geplanter IMU-Umbau, Eingang 2026-10-20

S3 funktional bestanden: 172.972 s, keyboard_interrupt/shutdown_ok, errors={},
GPS ohne Parser-/Pruefsummenfehler oder Pollpausen, 1671 Barometermessungen.
Alter 200-Zeilen-Ring exportiert letzte 40.963 s von 841 Samples. Der Nord-/
Ostanteil ist sichtbar, die komplette Sued/West-bergauf/Ost-bergab/Nord-Runde
nicht. Kompensation aus D1/D2/PROM fuer alle 200 CSV-Zeilen nachgerechnet;
Druck/Temperatur stimmen exakt. Hoehensprung 2.21 m in 0.201 s erfordert
ruhigen Einbau-/Anstroemtest, Ursache nicht bewiesen. Kein Vario-/Regelungsnachweis.
[Auswertung](testdaten/S3_gps_and_baro/AUSWERTUNG.md).

Besitzer bestaetigt geplante IMU-Drehung: Oberseite oben, X nach hinten.
Zwei neue Hostregressionen pruefen 180 Grad um Z mit body_signs=(-1,-1,1)
fuer Accel UND Gyro nach Rohsensoroffset/-skala sowie die Ablehnung alter
Levelmetadaten und Erhaltung der RC-Daten bei neuer Levelkalibrierung.
96 Steuerungs-/35 Sensortests, insgesamt 131 bestanden. Aktive Montagezeichen
bleiben unveraendert, bis die IMU tatsaechlich umgebaut wird. Hosttests ersetzen
keine SENSOR-/MANUAL-/Stabilisierungspruefung nach dem mechanischen Umbau.
[Einbauplan](EINBAU_UND_MANUAL_DATENFLUG.md).

## MANUAL-Logger-Vorbereitung: CH3 und Flash, 2026-10-20

15 neue Hosttests, insgesamt 146 bestanden. RecordingSwitch prueft
low-before-high, 200-ms-Bestaetigung/Zwischenstellung, invertierte Pulspolung,
Tick-Wrap, ungueltige Werte und erneute Freigabe nach Kanalverlust.
Es gibt noch keine Kopplung an app oder Servoausgabe.

logger_bench misst bei explizitem Bodenaufruf CH3 an freiem GP14 oder erzeugt
begrenzte neue Flash-Testdateien. Hosttests injizieren lange write/flush/sync/
close-Zeiten und pruefen, dass alle Phasen/komplette Schreibzyklen sichtbar
sind. Weitere Faelle: zu wenig Platz vor Dateistart, alte Daten/Kalibrierung
erhalten, Short-Write, falscher Dateiinhalt, Schreib-/Closefehler, Ctrl+C,
fehlendes sync, Pin-Konflikt und CH3-Bericht erst nach bestaetigtem PIO-Stop.
Nur temporaere Hostdateien/Stubuhr, keine MCU-/GPIO-Zugriffe.

Weder CH3-Anschlagpulse noch Flashlatenzen sind physisch gemessen. Kein
Fluglogger/LED aktiviert, kein Flash im vorhandenen Regler, kein Upload und
keine neue Flugqualifikation. **Kein fester Flugtimer** ist die neue Vorgabe;
Speicherfuellung bleibt eine gesonderte Grenze mit weiterlaufendem MANUAL.
[Plan und L1/L2-Anleitung](FLUGLOGGER_PLAN_UND_BODENTEST.md).

## L1/L2-Ergebnisse und L3-RAM-Vorbereitung, 2026-10-21

L1 bestaetigt CH3-Pulse 998..1998 us mit sauberem PIO-Stop. Zuordnung durch
Besitzernachtrag: unten 998/oben 1998. L2 verified fuer drei 64-KiB-Dateien,
keine Speicherfehler, aber write bis 72.098 ms, flush bis 114.338 ms und Zyklus
bis 181.709 ms. Damit ueberschreitet der getestete Dateiwriter die aktuelle
50-ms-Steuerungsgrenze. Keine Integration dieses Pfads in MANUAL.
[Rohberichte und Auswertung](testdaten/logger_boden/AUSWERTUNG_L1_L2.md).

Vier neue Hosttests fuer RAM-Probe: Zielpuffer/Reserve, zu wenig RAM ohne
Allokationsversuch, Fragmentierung/MemoryError ohne stilles Verkleinern,
tatsaechliche Reserve nach Allokation. 150 Tests bestanden. Neue Benchversion
0.1.1 sichert ausserdem Timing-Schwellen explizit. Die damalige L3-Vorbereitung
qualifiziert noch keine echte Fluglogger-App; Besitzerresultat folgt unten.

## L3-Ergebnis und Blockvariante, 2026-10-21

Besitzerlauf mit 0.1.1: allocation_failed bei 91008 B Einzelallokation, trotz
164880 B Gesamtfreiraum. Kein Beleg fuer die genaue Heapaufteilung oder eine
bereits passende Kapazitaet; [Auswertung](testdaten/logger_boden/AUSWERTUNG_L3.md).
Bench 0.1.2 nutzt vorab reservierte Recordbloecke, standardmaessig 39 * 2304 B
plus 1152 B. Gleiche 632 Records, gleiche 65536-B-Reserve; kein Flugtimer.
Inhaltsprobe kontrolliert alle Recordgrenzen. Fehler/Abbruch gibt Puffer vor
JSON-Export frei. RAM-Pruefung inklusive Objekt-/Listenoverhead nach GC.

Sechs zusaetzliche Hosttests gegenueber 150: Records ueber alle Blockgrenzen,
Index-/Freigabegrenzen, ungueltige Groessen ohne Allokation, fehlerhafte
Blockgroesse, Teilallokation mit MemoryError/Ctrl+C und Inhaltspruefungsfehler.
Bestehender Erfolgstest modelliert nun einen Heap, der >4096-B-Allokationen
abweist, aber alle 40 Zielbloecke aufnimmt. Bestehende Reserve-/Fehlerfaelle
bleiben abgedeckt. **156 Tests bestanden** bei dieser Vorbereitung; damals
noch keine MCU-Messung der Blockvariante und kein finaler Encoder/Gesamtlauf.

Nachtrag: Besitzerbericht 0.1.2, 162608 B vorher frei, allocation_failed in
Phase allocate. 40 Bloecke/maximal 2304 B sind Planwerte, kein Erfolgszaehler.
Vorliegendes JSON bestimmt weder konkreten Block noch MemoryError-Text.
Kein Nachweis der genauen Ursache; Report unveraendert unter L3_bloecke/ archiviert.
0.1.3 erfasst echte Erfolgszaehler/letzte Anforderung, freien Heap beim Fehler
vor Cleanup, MemoryError-Meldung und Kontext. mem_info/Traceback nur in Konsole.
Zwei neue Regressionen: Diagnose nach Teilallokation vor Freigabe und Fehler
ausserhalb des Block-Allokators ohne falsche Bytearray-Fehlerzuordnung.
**158 Hosttests bestanden** bei der Diagnosevorbereitung; Boardlauf folgt unten.

Resultat 0.1.3: 35 Bloecke/80640 B erfolgreich, 36. Block scheitert mit
2304-B-MemoryError bei 79552 B frei. failure_location=block_allocator. Kein
vollstaendiger Puffer, starker Fragmentierungshinweis; Konsole nicht vorliegend.
0.1.4 aendert gezielt die Reihenfolge: voller Puffer vor denselben grossen
Imports, Reserve erst nach Imports/Inhaltspruefung/GC. Kein reduzierter
Modulumfang, Datensatz oder Reservewert. Laufende Steuerung unveraendert.
Drei neue Regressionen pruefen Reihenfolge plus strikte Reserve nach Imports,
Pufferfreigabe bei Import-/Compilerfehler und Ctrl+C sowie den echten run_ram-
Einstieg mit dieser Reihenfolge. **161 Hosttests bestanden** bei Vorbereitung.
Besitzerlauf 0.1.4 bestaetigt inzwischen 40 Bloecke/91008 B, Inhalt/Imports
und 68656 B freie Reserve. Rohbericht unter L3_frueh/; Vorprobe abgeschlossen.

## Kombinierter Logger 0.1.0, 2026-10-21

Besitzer bestaetigt 1 Hz fuer erste Basisfluege und zugaenglichen BOOT.
Expliziter flight_start reserviert vor Imports, ruft app mit optionaler Session
im SENSOR/MANUAL-Profil auf und stellt RAM-Konfiguration nach Stop wieder her.
CH3 ist getrennt von Steuerachsen; GPS/Baro/LED/BOOT nach Ausgabe, vor
Workmessung. Keine Flashzugriffe im Loop. 144-B-Encoder, 46 CSV-Spalten,
Gueltigkeits-/Altersfelder, ganze Segmente, keine stille Ringueberschreibung.

22 zusaetzliche Hosttests: 16 fuer Encoder/BOOT/CH3/volle Kapazitaet/GPS-
Paarcache/Fehler/Export/Pending-Daten/Startupreserve/Launcher; sechs fuer
getrennte PIO-Domaenen und echte app.run-Integration. Geprueft sind insbesondere
weitere MANUAL-Kommandos nach Loggerfehler, Timingfault nach 60-ms-Zusatzarbeit,
kein Export bei Abschaltfehler und keine frisch geloggten alten IMU-Winkel.
Virtueller Lauf laeuft nach zehn Minuten und vollem Puffer weiter, ohne Dateien
zu schreiben. Exporttest sichert CSV/JSON erst nach bestaetigtem Stop und
ueberschreibt keinen vorigen Lauf. Speicherfehler behaelt RAM zur Wiederholung.
**183 Hosttests bestanden.** Pausierte Iterationen pollen weiter, erzeugen aber
keine Record-Snapshots/Hoehenrechnung; auch das ist hostgeprueft.
MicroPython-Compiler, echte RAM-Reserve mit
neuen Modulen/Objekten, GPIO16-NeoPixel, BOOTSEL-Kosten, PIO und Gesamt-Timing
sind damit nicht physisch validiert. F1/F2 stehen aus:
[FLUGLOGGER_TEST.md](FLUGLOGGER_TEST.md). Kein Hardwarezugriff durch den Agenten.

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
