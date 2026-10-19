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

## 2. Jetzt konkret: S1, S2, S3

Der eigene Vorbereitungscommit auf dem neuen Branch umfasst:
GPS-NMEA-Empfang, MS5611-Treiber und separater sensor_test ohne app/PWM.
Gains, Servozeichen und Kalibrierung werden dafuer nicht umgestellt.

1. **Anschluss klaeren:** GY-63-Pins sind bekannt. Beim BN-180 fehlen noch
   eindeutige Kabelzuordnung und Bestaetigung des TX-Signalpegels. Die gelieferte
   Spezifikation ersetzt diese Angaben nicht. Keine Kabelfarben raten.
2. **S1 Barometer:** GY-63 an I2C1 GP10/GP11, erst Druck/Temperatur, dann
   relative Hoehenaenderung beim Anheben pruefen. Keine Neukalibrierung der Lage.
3. **S2 GPS:** BN-180 TX an UART0 RX GP13 nach Anschluss-/Pegelabgleich;
   9600 Baud, draussen gueltige GGA/RMC und Standort/Bewegung pruefen.
4. **S3 gemeinsam:** beide Sensoren 180 s betreiben und Logs sichern.
   Erhaltene Werte, Gueltigkeit, Datenalter, Fehler und Laufzeiten vergleichen.

**Alle Verdrahtungstabellen, Uploaddateien und genauen Aufrufe stehen in
[SENSOREN_TEST.md](SENSOREN_TEST.md).** BEC/Servos bleiben fuer diesen Schritt aus.
Noch keine echten Sensorergebnisse oder Flugdaten vorhanden.

## 3. Anschliessend: MANUAL-Logger integrieren

Nach S1/S2/S3 bauen wir auf den bisherigen MANUAL-Durchgang auf. Der separate
Sensorstarter steuert keine Ruder und ist daher noch kein MANUAL-Flugprogramm.

- Sensorpolling mit begrenztem Aufwand in den MANUAL-Ablauf integrieren;
  keine ADC-Wartepausen oder GPS-Fix-Warteschleife zwischen RC und Servoausgabe.
- Bordversorgung fuer MCU/Sensoren sowie bewussten Start und Logabschluss nach
  Landung festlegen. Ein angeschlossener Mac ist keine Bordversorgung; beim
  spaeteren Download keine ungeregelten Versorgungsquellen parallel verbinden.
- IMU, RC, Servoausgaben, GPS, Barometer und Iterationszeiten auf gemeinsamer
  Zeitbasis aufzeichnen. Datenalter und Fehlerkontext mit speichern.
- Ganze Fluege abdecken: jetzige 200-Zeilen-Ringe reichen nicht. Gewuenschte
  Flugdauer/Rate und Speicherweg festlegen. Ein erster Entwurf fuer kurze
  Datenfluege kann ein gepackter RAM-Puffer mit 600 Samples bei 1 Hz fuer 10 min
  sein, ergaenzt um Zeit-/Fehleraggregate jeder Iteration. RAM-Reserve auf dem
  konkreten MCU pruefen; nicht automatisch eine Speicherkarte voraussetzen.
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
keine garantierte Worst-Case-Grenze. Die 120 Hosttests pruefen Logik, keine
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

Auf codex/gps-baro-bringup bleiben, S1/S2/S3 ausfuehren und protokollieren.
Der Vorbereitungsstand ist hostgeprueft; physische Ergebnisse werden spaeter
in einem getrennten Ergebniscommit gesichert.
Der alte Tischtestbranch bleibt die Vergleichsbasis. Erst fuer die nachfolgende
MANUAL-Loggerintegration bei Bedarf vom dann passenden Commit einen eigenen
Branch anlegen. Kein automatischer Merge/Push/Flug-Release-Tag.
