# F2 MANUAL 0.1.5: Steuerkontinuitaet nicht bestanden

229.877 s, zwei Segmente, 145 Samples/152 CSV-Zeilen, Sequenzen 0..151
lueckenlos. BOOT-Stop/shutdown_ok, voller Puffer=false, Komponenten-errors leer.
GPS 1834 Saetze ohne Parse-/Pruefsummen-/Pollgapfehler, weiterhin kein Fix.
Besitzer: Ruder reagieren richtig, aber stufig/verzoegert gegenueber direktem
Empfaengeranschluss. Besitzer bestaetigt anschliessend: auch bei CH3 unten,
also pausierter Aufnahme. Sensor-/Lageberechnung und Speicherbereinigung laufen
in dieser Phase weiter; die Aufzeichnung allein erklaert das Gefuehl nicht.
Im zweiten Segment zeitweise keine Steuerbarkeit, danach
wieder normal. Das ist kein insgesamt bestandener MANUAL-Test.

## Aussetzer: aus Bericht und Code verifiziert

- t=152784 ms: Periode 51021 us > MAX_LOOP_US=50000. TIMING wird verriegelt;
  receiver.invalidate() verwirft bewusst ALLE Kanaele. Modus RX_TIMEOUT,
  Frische=false, alle drei Servoausgaenge 1500 us, PWM bleibt aktiv.
- t=152811 ms: frische Pulse aller drei Achsen wieder da, aber WAIT_NEUTRAL.
  Nick steht bei 1836 us und damit ausserhalb der Neutralfreigabe.
- t=157913 ms: 25 neue gemeinsame Neutralframes erreicht, MANUAL kehrt zurueck.
  Gesamtunterbrechung 5.129 s. Zwischendurch zeigen die Samples weiter
  frische Pulse und ausgelenkte Knueppel; alle Ausgaenge bleiben neutral.

Damit erklaert die Software beide Beobachtungen zum Aussetzer: alle drei Achsen
wurden neutralisiert, und die Sperre dauert ueber den einzelnen langsamen Loop
hinaus. Der Bericht belegt keinen bestimmten verlorenen Funk-/Empfaengerkanal.
Es gab einen Timing-Trip, nicht 4689 verschiedene Ausfaelle: diese Zahl zaehlt
spaetere Iterationen mit weiterhin verriegeltem TIMING-Fault.

## Stufige Reaktion: Befund und offene Ursache

Mittlere Periode 16.275 ms (~61.4 Hz), max. 51.021 ms; Work max. 50.262 ms.
Vor Ausgabe max. 33.013 ms; Ausgabeblock max. 25.571 ms; GC max. 24.660 ms.
Im Code ist PWM mit 50 Hz angefordert; neue Sollpulsbreiten kommen aus dem
unregelmaessigen Python-Loop. Alle gespeicherten MANUAL-Ausgaenge stimmen
exakt mit RC-Normierung/4-%-Totzone/konfigurierten Weggrenzen ueberein.
Es gibt keine MANUAL-Glaettung oder Slew-Begrenzung. 1 Hz betrifft die Datei,
nicht die Steuerung. Roll/Pitch/Yaw wurden in den Samples ausgelenkt.

Zusaetzliche Latenz/Jitter durch Verarbeitung und Speicherbereinigung ist
plausibel. Der Verursacher der 51-ms-Periode ist unbewiesen; stage_timing=null.
1-Hz-Samples messen weder Ende-zu-Ende-Latenz noch mechanische Stufigkeit.
Keine blinde PWM-Frequenzerhoehung, keine geaenderten Gains/Schutzgrenzen.

## Naechster Schritt

Logger 0.1.6 verwendet die schon vorhandene Phasenmessung auch in MANUAL.
Produktivcode: nur die Aktivierungsbedingung mit Kommentar und Versionskennung.
Keine neue Messinfrastruktur, feste Felder vor unveraenderter RAM-Reserve,
Messkosten bleiben in Work/Period; die Messung selbst kann Zeiten beeinflussen.
Bestehender echter App-Test mit 60-ms-GC prueft nun auch MANUAL-Phasenzuordnung:
vorher Fehler, nachher bestanden, gesamte Suite weiterhin 193 Tests bestanden.
Das ist Diagnose, der Steueraussetzer ist damit noch nicht behoben.

app.py/config.py ersetzen, Soft-Reboot, MANUAL am Tisch etwa drei Minuten mit
einem Segment und kleinen Steuerbewegungen. Bei Aussetzer sauber stoppen und
sichern. [Bedienfolge](../../../FLUGLOGGER_TEST.md). Danach langsamen Abschnitt
gezielt entlasten und Aussetzer/Bediengefuehl erneut pruefen, bevor Datenflug.
Schutz-/Wiederfreigabeverhalten nicht stillschweigend abschwaechen.

SHA-256 der unveraenderten Rohdaten:

```text
flight_322120_0.json: edc92797f2f2c8c6c5b82d9d41c83ed2289baea6e1ab02349b916fbda87f3bb4
flight_322120_0.csv: 40f34749e4df68145690d77619685f71fbad65ac213bb4e7ccf3fa49fd8351a9
```
