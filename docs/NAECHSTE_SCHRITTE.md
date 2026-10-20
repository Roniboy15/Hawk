# Aktueller Weg: Sensoren pruefen, manuell Daten sammeln, neu bewerten

Besitzerentscheidung vom 2026-10-18: pragmatisch zur nutzbaren Flugfunktion
weiterarbeiten. GPS/Barometer und manuelle Messfluege werden vorbereitet;
Timingverbesserung bleibt Arbeit, exakt 100 Hz ist keine pauschale Sperre fuer
Sensorentwicklung. Der Besitzer moechte weiterhin den MCU-MANUAL-Durchgang
verwenden und akzeptiert dessen Abhaengigkeit vom MCU. Ausfallfreiheit ist damit
nicht nachgewiesen. Unabhaengiger Rueckweg bleibt eine Engineering-Empfehlung.

## 1. Erledigt und gesichert

Tischteststand **913a9e6** auf codex/bench-fault-validation committed. Neuer
Branch **codex/gps-baro-bringup** wurde von diesem Commit erstellt; main blieb
unveraendert. Keine Veroeffentlichung oder MCU-Uebertragung durch Git.

T1-Wiederholung/T2/T3 funktional bestaetigt, T5 Stabilisierung und T6 Fehlersperre
bestaetigt. T4 bleibt bewusst offen. Der lose Stecker erklaert den Gierverlust;
Verbindung vor Wiederholungen sichern. T5: im Mittel 74.92 Hz, work maximal
32.323 ms, keine harte 50-ms-Ueberschreitung. Erster T1-IMU_RUNTIME bleibt offen.
Die [Testauswertung](testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T3_T5_T6.md)
haelt die Nachweise und ihre Grenzen fest.

## 2. Sensorfunktion abgeschlossen; neue Vollaufzeichnung noch pruefen

Der eigene Vorbereitungscommit auf dem neuen Branch umfasst:
GPS-NMEA-Empfang, MS5611-Treiber und separater sensor_test ohne app/PWM.
Gains, Servozeichen und Kalibrierung werden dafuer nicht umgestellt.

1. **Anschlussstand:** GY-63-Pins bekannt. Beim konkreten BN-180 ist laut
   Besitzerbeschreibung weiss = GPS-TX; NMEA-Empfang bestaetigt die funktionierende
   Datenverbindung. Andere Farben nicht raten; TX-Spannungspegel nicht gemessen.
2. **S1 Barometer funktional bestanden:** GY-63 an I2C1 GP10/GP11 liefert
   plausible Druck-/Temperaturwerte. Anheben mit ungefaehr passender positiver
   Hoehenaenderung im selben Lauf vom Besitzer bestaetigt. Keine Neukalibrierung
   der Lage erforderlich; absolute Genauigkeit/Drift nicht quantifiziert.
3. **S2 GPS funktional bestanden:** gps_2 hat Fix nach 74.820 s und keine
   Pollpausen. Konsole zeigt Hinweg mit West-/Suedanteil und Rueckweg nach
   Osten/Nordosten. [Auswertung](testdaten/gps_tests/AUSWERTUNG_GPS_2.md).
4. **S3 gemeinsam funktional bestanden:** 172.972 s, sauberer Ctrl+C-Abschluss,
   GPS und Barometer zusammen, keine protokollierten Sensorfehler/Pollpausen.
   Besitzerweg: Sueden eben, Westen bergauf, Osten bergab, Norden eben.
   Gespeichert ist nur das Ende: Testversion 0.1.0 / Schema 1, 200 von 841
   Zeilen, letzte 40.963 s. Neuer RAM-Puffer 0.2.0 damit physisch noch offen.
   [S3-Auswertung](testdaten/S3_gps_and_baro/AUSWERTUNG.md).

**Alle Verdrahtungstabellen, Uploaddateien und genauen Aufrufe stehen in
[SENSOREN_TEST.md](SENSOREN_TEST.md).** BEC/Servos bleiben fuer diesen Schritt aus.
Erster GY-63-Lauf ausgewertet: 60.002 s, 594 Messungen, CRC korrekt, keine
protokollierten Fehler. S1 mit Logpruefung und Besitzerbeobachtung funktional
bestanden; GPS/S2 und gemeinsamer S3 ebenfalls funktional bestanden.
Beim naechsten Bodenlauf konsistente Module, Soft-Reboot, Sensor-Test 0.2.0 /
Schema 2 und vollstaendige Aufzeichnung pruefen. Keine weitere Huegelrunde allein
deshalb. S3 zeigt Hoehenspruenge bis 2.21 m in 0.201 s; Kompensation stimmt,
Einbau-/Anstroemeinfluesse sind noch nicht geklaert. Noch kein validiertes Vario.
[Barometer-Auswertung](testdaten/barometer_tests/AUSWERTUNG.md).

Aktueller USB-Startbefund (2026-10-19): bereits versorgte Hoehen-/Seitenruder
an GP6/GP7 schlugen beim USB-Anstecken aus, waehrend die IMU ohne Versorgung
an ihren Signalleitungen hing. Zuerst BEC aus; IMU mitversorgen oder bei
getrennten Quellen ganz abstecken. Weitere reine Sensorchecks nur USB,
BEC/Receiver/Servos aus. Vor erneutem Betrieb versorgter montierter Servos
MCU-Startdateien, aktuelle Verdrahtung und Versorgungs-/Signalverhalten klaeren;
keine absichtliche Wiederholung der Endausschlaege. Das blockiert die isolierten
Sensorchecks nicht und aendert nicht die akzeptierte MCU-Abhaengigkeit.

## 3. Jetzt konkret: Einbau und MANUAL-Logger

Nach S1/S2/S3 bauen wir auf den bisherigen MANUAL-Durchgang auf. Der separate
Sensorstarter steuert keine Ruder und ist daher noch kein MANUAL-Flugprogramm.
Der konkrete [Einbau-/MANUAL-Arbeitsplan](EINBAU_UND_MANUAL_DATENFLUG.md) enthaelt
Anschluesse, Versorgung, 180-Grad-IMU-Umbau und die naechsten Codeaufgaben.
Nach Freigabe Sensorstand committen, dann codex/manual-flight-logger davon
abzweigen. Aktive IMU-Zeichen bleiben bis zum mechanischen Umbau unveraendert.

Einbauentscheidung: Oberseite der IMU bleibt oben, X zeigt kuenftig nach hinten.
Dann body_axes=(0,1,2), body_signs=(-1,-1,1) einstellen, neu waagerecht
kalibrieren und Sensor-/Ruder-/Stabilisierungsrichtungen pruefen. Kalibrieren
allein erkennt die umgekehrte Laengsrichtung nicht. RC-Kalibrierung erhalten.
5 V/GND/3V3 als Verteilung ist sinnvoll: GPS an 5 V, IMU und GY-63 an 3V3.
MCU-Bordversorgung und USB-Pfad vorher klaeren, keine zwei 5-V-Quellen parallel.

- Sensorpolling mit begrenztem Aufwand in den MANUAL-Ablauf integrieren;
  keine ADC-Wartepausen oder GPS-Fix-Warteschleife zwischen RC und Servoausgabe.
- Bordversorgung fuer MCU/Sensoren sowie bewussten Start und Logabschluss nach
  Landung festlegen. Ein angeschlossener Mac ist keine Bordversorgung; beim
  spaeteren Download keine ungeregelten Versorgungsquellen parallel verbinden.
- IMU, RC, Servoausgaben, GPS, Barometer und Iterationszeiten auf gemeinsamer
  Zeitbasis aufzeichnen. Datenalter und Fehlerkontext mit speichern.
- Ganze Fluege abdecken: Controller-Logs sind weiterhin begrenzte Ringe;
  der neue volle Sensorpuffer hat noch keine IMU/RC/Servo-Daten. Gewuenschte
  Flugdauer/Rate und Speicherweg festlegen. Ein erster Entwurf fuer kurze
  Datenfluege kann ein gepackter RAM-Puffer fuer 5 min bei 1 Hz
  sein, ergaenzt um Zeit-/Fehleraggregate jeder Iteration. RAM-Reserve auf dem
  konkreten MCU pruefen; nicht automatisch eine Speicherkarte voraussetzen.
  Bei vollem Puffer nur Logging anhalten, MANUAL-Steuerung fortsetzen.
  Boden-Stop/Export bei noch eingeschalteter Versorgung implementieren;
  nicht per Timer die Steuerung waehrend eines Flugs beenden.
  Das ist ein Implementierungsplan, noch keine vorhandene Funktion.
  Flashzugriffe bleiben aus der
  aktiven Regelschleife ausgeschlossen; Speicherloesung bewusst implementieren.
- Verhalten der gesamten MANUAL-Integration zuerst am Boden pruefen, einschliesslich
  Mehrlast, fehlender Sensorwerte und sauberem Start/Stop. Sensorstoerung darf
  nicht aus Versehen die manuelle Steuerung durch einen blockierenden neuen
  Programmteil aufhalten. Blockaden des bestehenden MCU-Pfads bleiben ein Risiko.

Danach die geplanten manuellen Datenfluege beurteilen und durchfuehren, Daten
sichern, Empfang/Barometer/Timing vergleichen und den naechsten Umfang festlegen.
Das ist eine Entwicklungsempfehlung, keine Zusage, dass Hardware nicht ausfaellt.

## 4. Timing/Faults parallel und anhand der Daten bearbeiten

Die 100-Hz-Zielrate ist kein Naturgesetz. Eine andere Regelrate kann sinnvoll
sein, braucht aber eine bewusste Auslegung und Bewertung. Schwellen nicht nur
veraendern, um Warnungen verschwinden zu lassen. Weder 75 Hz allein noch das
Ausbleiben eines 50-ms-Faults beweisen gute oder schlechte Flugregelung.

Naechste sinnvolle Diagnoseergaenzungen bei MANUAL-Integration:

- Laufzeiten fuer IMU/Filter, RX, Regler, PWM, Zusatzsensoren und Diagnose aufteilen.
  Messaufwand mit erfassen, keine Print-/Flashausgabe pro Iteration.
- Ersten Automatikfault mit Phase, Typ und begrenztem Exceptiontext exportieren;
  der erste T1-IMU_RUNTIME laesst sich aus seinem Faultcode allein nicht erklaeren.
- RX-Verwerfungen nach ungueltigem Puls, FIFO und Pollpause unterscheiden.
- Nach Messung gezielt Allokationen/Formatierung/Puffer/Mathematik verbessern.
  Die [MicroPython-Dokumentation](https://docs.micropython.org/en/v1.29.0/reference/speed_python.html)
  beschreibt diese Reihenfolge. GC ist hier eine Hypothese, keine bewiesene Ursache.

Vergleichsmessungen mit gleichen Einstellungen sichern; keine alten Fehlerdaten
ersetzen. Drei 60-s-Laeufe sind ein sinnvoller Reproduzierbarkeitsvergleich,
keine garantierte Worst-Case-Grenze. Die 131 Hosttests pruefen Logik, keine
realen Ausfuehrungszeiten. T4, Versorgung und Receiver-Failsafe bleiben offen;
[Sicherungs-/Versorgungsbefunde](VERSORGUNG_WARNHINWEISE.md) weiter mitfuehren.

## 5. Danach ein autonomer Kreis als eigener kleiner Umfang

GPS und Barometer liefern Messwerte. Fuer einen autonomen Kreis braucht es
zusaetzlich gepruefte Positions-/Kursgueltigkeit, Kreisfuehrung und Roll-Sollwerte,
Nick-/Geschwindigkeitsstrategie, Grenzen und klare Aktivierung/Uebernahme.
GPS-Kurs ist kein Kompass und Groundspeed keine Airspeed. Null-Gierrate ist
keine automatische Kurvenkoordination. Diese Funktionen werden nach der
Datenauswertung schrittweise ergaenzt; perfekte Thermiknavigation ist dafuer
nicht vorab noetig. Einen fertigen Kreisregler gibt es im jetzigen Code nicht.

## Git fuer den laufenden Schritt

Sensorabschluss auf codex/gps-baro-bringup und anschliessender neuer Branch
wurden vom Besitzer am 2026-10-20 freigegeben.
Er enthaelt Ergebnisse, UART-Korrektur und neuen hostgeprueften RAM-Puffer mit
offenem Hardwarecheck. Abschluss committen und den neuen Branch
codex/manual-flight-logger direkt davon erstellen. main ist noch sieben
Commits hinter der aktuellen Branchbasis; nicht dort neu anfangen.
Push/PR und Merge nach main sind gesonderte Schritte; main muss den
Loggerfortschritt nicht aufhalten. [Git-Ablauf](GIT.md).
