# Naechster Schritt nach den Tischtests

Stand 2026-10-18: Roll/Nick/Gier funktionieren laut Besitzer. T1-Wiederholung,
T2 und alle drei T3-Varianten sind durch CSV/JSON bestaetigt. T5 bestaetigt
Stabilisierung, T6 die PITCH_RANGE-Verriegelung. **T4 bleibt auf Besitzerwunsch
OFFEN**; es wurde kein vorbereiteter Signalschalter eingebaut.

Die [aktuelle Auswertung](testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T3_T5_T6.md)
trennt bestandene Funktionen von offenen Befunden. T5 erreicht nur ca. 74.92 Hz,
99.44 % der work-Zeiten liegen ueber dem 10-ms-Ziel. T6 zeigt spaeter Gier-
Pulsverlust mit korrekter Trimneutral-Reaktion; laut spaeterer Besitzerbestaetigung
war ein Stecker herausgefallen. Der erste T1-IMU_RUNTIME und
unkontrollierte Ausschlaege bei abruptem MCU-Stromverlust sind nicht geklaert.
Gains, Vorzeichen, Kalibrierung und die harte 50-ms-Grenze bleiben unveraendert.
Keine Flugfreigabe und noch keine Flug-Gainabstimmung aus diesen Tischtests.

## 1. Steckverbindung sichern

Der Besitzer bestaetigt nachtraeglich: bei T6 war ein Stecker herausgefallen.
Das erklaert den Gier-Pulsverlust ab 49.402 s bei weiterlaufendem Roll-/Nickempfang.
Die Software reagierte wie vorgesehen mit Trimneutral; der Befund wird als
erklaerte Steckunterbrechung gefuehrt, nicht als ungeklaerter Empfangsfehler.
Der genaue Steckort und elektrische Verlauf sind nicht unabhaengig gemessen.

Bei getrennter USB- und BEC-Versorgung die betroffene Verbindung wiederherstellen,
festen Sitz und Zugentlastung pruefen. Danach zuerst SENSOR mit fortlaufenden
RX-Sequenzen aller drei Kanaele pruefen, bevor erneut Servos angesteuert werden.
Keine Live-Umverdrahtung und kein erneutes absichtliches
USB-Abziehen bei eingeschalteten Servos. Die korrigierte Stop-/Downloadfolge
in [FEHLER_TISCHTEST.md](FEHLER_TISCHTEST.md) bleibt verbindlich.
T4 darf fuer diesen Entwicklungsschritt offen bleiben; vor Abschluss der
Signalverlustqualifikation braucht es einen kontrollierten Nachweis.

## 2. Konkreter naechster Codeumfang: Laufzeit- und Fehlerdiagnose

Ziel: Aus den pauschalen Timing-/Faultbefunden die langsame Phase und die Art
des Empfangs-/Sensorfehlers bestimmen. Noch nicht in dieser Doku-Runde implementiert.

1. **Laufzeit je Phase:** IMU-Lesen, Lagefilter, Receiver, Regler, PWM und
   Diagnose/Konsole/CSV getrennt mit begrenzten RAM-Zaehlern erfassen. Bestehende
   Gesamtzeiten beibehalten; Messaufwand selbst mitbeurteilen. Kein Print pro
   Iteration, kein Flashzugriff waehrend der Schleife. Der T5-Mittelwert ist
   bereits zu hoch; einzelne Jitterspitzen zu verringern reicht nicht aus.
2. **Ersten Automatikfault dauerhaft beschreiben:** Zeitpunkt, Phase, Faultcode,
   Exceptiontyp und begrenzten Exceptiontext einmal im RAM speichern und nach
   bestaetigtem Stop ins JSON exportieren. Vorhandenen Fault nicht mit einem
   spaeteren Folgefehler ueberschreiben. Damit wird ein weiterer IMU_RUNTIME
   auch ohne noch sichtbare Thonny-Konsole untersuchbar.
3. **RX-Verwerfungen unterscheiden:** pro Kanal begrenzte Zaehler fuer
   ungueltige Pulsbreite, vollen FIFO und Pollpause sowie letzte gueltige
   Sequenz/Alter exportieren. Startverwerfung getrennt zaehlen. Das ergaenzt
   RX_TIMEOUT, ohne Funkverlust aus weiterhin gueltigen Hold-Pulsen zu behaupten.
4. **Erst nach Messung gezielt optimieren:** wiederholte Objekt-/Stringerzeugung,
   Sensorpuffer, Quaternionrechnung und Diagnoseaufwand anhand der Phasenwerte
   beurteilen; immer nur eine belegte Ursache aendern. Keine ungepruefte I2C-
   Takterhoehung, GC-Abschaltung oder lockeren Sicherheitsgrenzen als Abkuerzung.

Diese Reihenfolge ist eine Engineering-Empfehlung aus den Messwerten.
Speicherallokation/GC ist eine Hypothese, keine nachgewiesene Ursache. Die
[MicroPython-Dokumentation](https://docs.micropython.org/en/latest/reference/speed_python.html)
beschreibt Heap-/GC-Pausen und empfiehlt zuerst die langsame Stelle zu messen.
Sie betrifft den Entwicklungsstand; konkrete APIs gegen die installierte Runtime
pruefen, keine dort genannten neuen Features ungeprueft uebernehmen.

**Abnahme dieses Codeumfangs:**

- Bestehende 94 Hosttests weiter erfolgreich; gezielte neue Tests fuer erste
  Faultursache, begrenzte Counter, alle RX-Verwerfungsarten, Tick-Umlauf und
  Export erst nach Shutdown. CSV-/JSON-Schema bei Erweiterung bewusst behandeln.
- AUTO_START=False, SENSOR ohne PWM, Neutralgate, Ausgabebegrenzung und
  verriegelter Ersatzmodus bleiben erhalten. Kein Upload/Hardwarestart durch
  Hostwerkzeuge oder Modulimport.
- Danach physisch T1 und T5 mit identischen Einstellungen wiederholen; Laufpaare
  getrennt sichern, keine alten Fehlerdateien ersetzen. T5 mindestens dreimal
  60 s. Phasenmittel/-maxima, Ueberschreitungen und unerwartete RX-/IMU-Ereignisse
  gegen die jetzigen Daten vergleichen. SENSOR kann mit getrennter Servobatterie
  untersucht werden; fehlende RX-Werte sind dann erwartet.
- 100 Hz erst als nachgewiesen bezeichnen, wenn die beobachtete Rechenzeit
  einschliesslich Diagnose in das 10-ms-Budget passt und Periodenjitter beurteilt
  ist. Beobachtete Maxima bleiben keine Worst-Case-Garantie. Falls 100 Hz mit
  dieser Architektur nicht erreichbar sind, die Regelrate spaeter bewusst neu
  auslegen und validieren; nicht nur den Konfigurationswert herabsetzen.

## 3. Git: Ergebnisse sichern, dann Codearbeit abtrennen

Aktuell: codex/bench-fault-validation, Quellcommit 4a1f889; derselbe Commit liegt
auf origin/codex/bench-fault-validation. f66ccd1 schloss die erste Achsenphase ab.
main liegt noch beim aelteren Stand 57a5ed2 und enthaelt diese Arbeit nicht.

**Empfehlung, hier noch nicht ausgefuehrt:**

1. Jetzt Testauswertung, Rohdaten und korrigierte Bedien-/Projektunterlagen
   gemeinsam auf dem aktuellen Branch committen. Ein Commit mit ehrlich
   dokumentierten offenen Befunden ist sinnvoll; T4 muss dafuer nicht bestanden
   sein. Die .gitignore-Ausnahmen erfassen nur die vier ausgewaehlten T5-/T6-
   Dateien; sonst wuerden deren bench_-Namen beim normalen git add fehlen.
2. Danach fuer die oben abgegrenzte Codearbeit codex/timing-fault-diagnostics
   **vom neuen Ergebniscommit** erstellen. So bleiben Messbasis und folgende
   Implementierung vergleichbar. Nicht vom alten main abzweigen.
3. main zunaechst unveraendert lassen; kein Flug-Release-Tag. Push ist eine
   separate Sicherung nach Review, kein MCU-Upload. Ein spaeterer Merge kann
   bewusst einen Bodenversuchsstand mit offenen Punkten enthalten.

Beispiel nach Pruefung aller angezeigten Dateien:

```sh
git status
git diff
git add .gitignore AGENTS.md README.md docs
git diff --staged
git commit -m "Tischtestergebnisse und offene Befunde dokumentieren"
git switch -c codex/timing-fault-diagnostics
```

## 4. Weitere Prioritaeten bis zum Thermikkreisen

1. **Versorgung und unabhaengiger Rueckweg:** BEC 5 V @ 3 A fuer vier Servos,
   gemeinsame Masse, Pegel, USB-Stromverlust und Receiver-Failsafe qualifizieren.
   Stromleiste allein belegt keine Stromreserve. Modelle/Schaltplan erfassen,
   dann Receiver-zu-Servo-Umschaltung planen, die auch ohne funktionierenden MCU
   wirkt. Signalausgaenge nicht parallel verbinden. T4 ersetzt diesen Bypass nicht.
   [Versorgungsbefunde](VERSORGUNG_WARNHINWEISE.md) bleiben offen.
2. **Kontrollierte Fehlerqualifikation:** T4 und gemessene Reaktionszeiten
   nachholen, wenn ein geeigneter Testaufbau vorhanden ist. Hang-/Resetverhalten
   und Sensor-Busblockaden untersuchen. Ein Watchdog ersetzt keinen unabhaengigen
   manuellen Weg; keine riskanten Kurzschluesse zur Fehlereinspritzung.
3. **Dynamik/Simulation:** Flugzeugdynamik, kombinierte Achsen, Aktuatorgrenzen
   und koordinierte Kurven. Null-Gierrate ist keine fertige Kurvenkoordination.
   Vor I-Anteil Trim-/Anti-Windup-Integration beheben. Tischbewegungen sind keine
   Flug-Gainabstimmung; Flugversuche erst nach den offenen Systemnachweisen.
4. **Zustand/Energie/Navigation:** Airspeed, Hoehe/Vario und Position, danach
   Energie-/Geschwindigkeitsregelung, Navigation, zuletzt Thermikerkennung und
   Zentrierung. Nickwinkelhaltung ist keine Hoehen-/Stallregelung.
   [ARCHITEKTUR.md](ARCHITEKTUR.md) beschreibt den groesseren Zusammenhang.
