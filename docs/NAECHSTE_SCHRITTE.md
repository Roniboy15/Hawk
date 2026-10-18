# Nach dem Drei-Achsen-Funktionstest

Stand 2026-10-13: grundlegende Roll-/Nick-/Gierfunktion vom Besitzer bestaetigt.
Die Reglerwerte bleiben unveraendert, rate_i=0. Der naechste Schritt zum
Thermiksegler ist ein messbarer, reproduzierbarer Flugsteuerkern. Navigation
oder hoehere Gains wuerden die noch offenen Fehler-/Versorgungsfragen nicht klaeren.

## Jetzt abschliessen und den naechsten Branch beginnen

1. Den [Testbericht](TESTBERICHT_2026-10-13.md), Konfiguration und Testaenderungen
   gemeinsam auf `codex/receiver-timing-hardening` pruefen. Hosttests: 68 PASS.
2. Mit Besitzerbestaetigung vom 2026-10-13 stage/commit:
   `Drei-Achsen-Tischtest und Vorzeichen dokumentieren`.
3. Vom neuen Commit den Branch `codex/bench-fault-validation` anlegen.
   Der alte Branch bleibt als abgeschlossener Funktionsstand erhalten. main
   bleibt zunaechst unveraendert; nicht von dessen aelterem Stand abzweigen.
   Keine automatische Veroeffentlichung, kein MCU-Upload, kein Flug-Release-Tag.

Abschlusscommit f66ccd1 und Folgebranch sind erstellt. Die Softwarevorbereitung
ist als v0.2.3 auf codex/bench-fault-validation umgesetzt; Hardwaretests stehen aus.
Die konkrete Anleitung mit Profilaufrufen und PASS-Kriterien ist jetzt
[FEHLER_TISCHTEST.md](FEHLER_TISCHTEST.md), Protokoll:
[TESTPROTOKOLL_FEHLER.md](TESTPROTOKOLL_FEHLER.md). Mit T1 beginnen.
Ein spaeterer Merge kann diesen Umfang als Bodenversuchsstand uebernehmen,
ohne damit elektrische oder Flugqualifikation zu behaupten.

## Umfang des naechsten kleinen Entwicklungsschritts

**Fehlerreaktionen und reales Timing nachweisen.** Die folgende Software ist
umgesetzt und hostgeprueft. Physische T1–T6 gemaess konkreter Anleitung ausfuehren.

- Begrenzte RAM-Zeitstatistik fuer jede Iteration: Startabstand, Rechenzeit bis
  zur Ausgabe, gesamte Iteration inklusive Diagnose/Logging und Ueberschreitungen.
  Das vorhandene CSV-dt ist nur der Startabstand von protokollierten Samples.
  Statistiken nach Stop exportieren; kein Flashzugriff in der Regelschleife.
- Aktive Konfiguration und Fault-/Moduswechsel mit Zeitmarken protokollieren.
  RX-Alter/Sequenzen helfen, fehlende Pulse von neu eintreffenden gleichbleibenden
  Pulsen zu unterscheiden. Solche Pulse beweisen trotzdem keine Funkverbindung.
- Reproduzierbare Hostpruefungen fuer alle drei Achsen: je ein fehlender/ausfallender
  Kanal sperrt die gemeinsame Freigabe bzw. neutralisiert alle aktiven Ausgaenge;
  Rueckkehr bei nichtneutralem Knueppel bleibt gesperrt. Bestehende Sensor-/Timing-
  Verriegelung, tick-Umlauf und Cleanup auf Regressionen pruefen.
- Kleine Host-Auswertung fuer CSV/Header/Zeiten/Pulsgrenzen und ein Testprotokoll
  mit PASS/FAIL-Kriterien. Keine absichtlichen Stoerungen in Produktionsdefaults;
  simulierte Fehler bleiben im Hosttest, reale Signalunterbrechung ein vorbereiteter
  Signalschalter. Das separate Profil pitch-range nutzt nur voruebergehend eine
  echte 20-Grad-Nickgrenze und spritzt keinen IMU-/Timingfehler ein.

## Danach am Tisch zu erfassende Nachweise

Zuerst passende MCU-Dateien, MicroPython-Version, calibration.json, Konfiguration,
Receiver-/BEC-/Servomodelle und tatsaechliche Pinpfade sichern. BEC ist laut
Aufschrift 5 V @ 3 A fuer vier Servos; 20 A nicht als Servo-Stromreserve annehmen.
Versorgung fuer die Tests beurteilen; [Warnhinweise](VERSORGUNG_WARNHINWEISE.md)
bleiben gueltig. Keine Netzstoerung absichtlich nachstellen.

| Test | Erwartung des jetzigen Codes | Erforderlicher Nachweis |
| --- | --- | --- |
| Start mit fehlendem aktivem RC-Kanal | Kein PWM-Start | Zustandsfolge und Ausgangsmessung |
| Pulsverlust nach Aktivierung | Alle Ausgaenge Trimneutral | Zeit vom letzten gueltigen Puls bis Ausgabe |
| Rueckkehr mit Knueppel ausser Mitte | WAIT_NEUTRAL, keine Steuerkommandos | Erst 25 neue gemeinsame Neutralframes geben frei |
| RX-Rueckkehr ohne anderen Fault | Angeforderter Modus nach Neutralfreigabe | STABILIZE darf hier wiederkehren |
| Rueckkehr nach erkanntem TIMING-/IMU-Fault | MANUAL_FALLBACK bei frischem, freigegebenem RX | STABILIZE bleibt bis Neustart verriegelt |
| Ctrl+C/Shutdown | Alle PWM/PIO-Abschaltversuche, dann Logexport | Signal und mechanisches Verhalten ohne Pulse |
| Alle Achsen, Konsole/Logging aktiv | Zeitstatistik und Fault-Zaehler auswertbar | Wiederholungen und maximale beobachtete Zeiten |

Signalverlust nur mit vorbereitetem, elektrisch geeignetem Testaufbau erzeugen;
keine Live-Umverdrahtung. Sender-Aus ist ein separater Empfaenger-Failsafe-Test:
gehaltene/gesetzte PWM-Werte koennen fuer diesen Controller weiterhin gueltig sein.
Der Segler hat kein Gas; keinen Throttle-Failsafe oder freien Zusatzkanal annehmen.
Brownouts/CPU-Haenger nicht durch riskante Kurzschluesse erzwingen. Ein gemessener
Maximalwert ist noch keine garantierte Worst-Case-Grenze.

## Folgende Prioritaeten bis zum Thermikkreisen

1. **Versorgung und unabhaengige Rueckfallebene:** 5-V-Reserve/Ground-/USB-Aufbau
   qualifizieren und einen Receiver-zu-Servo-Weg entwickeln, der auch bei MCU-Ausfall
   funktioniert. Quellen nicht parallel auf einen Signaldraht verbinden. Erst
   Architektur und Fehlerfaelle pruefen, dann Hardware waehlen. Vor Flugversuchen
   braucht es einen erprobten Rueckweg und eine bewusste Moduswahl.
2. **Hang-/Neustartverhalten:** Sensor-Busblockaden, PWM waehrend Ausfall und nach
   Reset beurteilen. Ein Watchdog ist ein spaeterer Teil davon; er startet die MCU
   neu und ersetzt keinen unabhaengigen MANUAL-Pfad. Nach Aktivierung ist er laut
   [MicroPython-WDT-Dokumentation](https://docs.micropython.org/en/latest/library/machine.WDT.html)
   nicht abschaltbar; konkrete installierte Runtime und Startkalibrierung beachten.
3. **Simulation und Flugsteuerung:** Flugzeugdynamik, Rate-/Winkelregelung,
   kombinierte Achsen, Aktuatorgrenzen und koordinierte Kurven testen. Null-Gierrate
   ist keine fertige Kurvenkoordination. Vor I-Anteil die offene Trim-/Anti-Windup-
   Integration beheben; Tischbewegungen dienen nicht zur Flug-Gainabstimmung.
4. **Zustand/Energie/Navigation:** Airspeed, Hoehe/Vario und Position mit passenden
   Sensoren und Validierung, danach Energie-/Geschwindigkeitsregelung, Navigation
   und erst dann Thermikerkennung/-zentrierung. Reihenfolge und Risiken stehen in
   [ARCHITEKTUR.md](ARCHITEKTUR.md).

Zur begrifflichen Trennung von RC-Ausfall und Controller-/Versorgungsfehlern:
[ArduPlane-Failsafe-Dokumentation](https://ardupilot.org/plane/docs/apms-failsafe-function.html).
Sie ist eine Designreferenz, keine Anleitung, deren Parameter in diese Firmware
zu uebernehmen. Diese Roadmap ist unsere Engineering-Einschaetzung des aktuellen
Codes und der noch fehlenden Nachweise.
