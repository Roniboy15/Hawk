# Drei-Achsen-Funktionstest — v0.2.2-bench

Eingang/Auswertung am 2026-10-13. Der Besitzer meldet alle Achsentests bestanden
und hat die Vorzeichen an die Koerperkonvention angepasst. Genaue Testzeit,
MicroPython-Version und die tatsaechlichen MCU-Dateien wurden nicht mitgeliefert.
Dies schliesst die grundlegende Funktionsphase ab, keine Flug-/Versorgungsfreigabe.

## Bestaetigtes Profil und Herkunft

Lokaler Diff gegen den Vorbereitungscommit 4716a63:

| Achse | RX sign | Servo sign | RX / Servo GPIO | rate_p | Pulsgrenzen bei Trim=0 |
| --- | --- | --- | --- | --- | --- |
| Roll | -1 | -1 | GP2 / GP3 | 2 | 1300..1700 us |
| Nick | -1 | -1 | GP8 / GP6 | 1 | 1350..1650 us |
| Gier | -1 | -1 | GP9 / GP7 | 1 | 1350..1650 us |

Alle Achsen aktiv und als richtungsgeprueft markiert; AUTO_START=False,
Testmodus STABILIZE. Alle rate_i=0, Trims=0; Winkel-/Ratengrenzen unveraendert.
Der gespeicherte Abschlussstand setzt START_MODE bewusst auf SENSOR zurueck;
Zeichen, Achsenbestaetigungen und Gains bleiben erhalten. Git aendert den MCU nicht.

Der Besitzerbericht ist der Nachweis fuer die physische Richtung/Funktion.
Die Tabelle zeigt die Softwarebelegung; der Log beweist die realen Signalpfade
und mechanischen Ruderwirkungen nicht. Vor der Testreihe waren Nick/Gier direkt
am Receiver; eine unabhaengige Erfassung des jetzigen Pinpfads fehlt weiterhin.

Die gelieferten 51 Konsolenzeilen sind ohne Aenderung der Messwerte unter
[testdaten/2026-10-13_stabilize_3achsen.txt](testdaten/2026-10-13_stabilize_3achsen.txt)
gesichert. Fuer das Textarchiv wurden nur nachgestellte Leerzeichen entfernt
und ein abschliessender Zeilenumbruch ergaenzt (9376 Bytes). Quelle:
Besitzeranhang "Eingefuegter Text.txt", 9426 Bytes,
SHA-256 `be549ba59979c86a17fa3e080ce109096047c210df98cf1947ca564a94f56b13`.
Kein Zeitstempel/CSV-Header im Auszug; weder Vollstaendigkeit noch Dauer ableitbar.

## Im Log direkt nachpruefbar

| Groesse | Minimum | Maximum | Einheit |
| --- | --- | --- | --- |
| Roll | -8.3 | 2.6 | Grad |
| Nick (pitch_down) | -0.9 | 7.3 | Grad |
| Rollrate gx | -18.1 | 18.8 | Grad/s |
| Nickrate gy | -11.8 | 13.8 | Grad/s |
| Gierrate gz (links positiv) | -100.2 | 78.9 | Grad/s |
| RX Roll | 1495 | 1496 | us |
| RX Nick | 1493 | 1494 | us |
| RX Gier | 1501 | 1502 | us |
| Servo Roll | 1443 | 1528 | us |
| Servo Nick | 1489 | 1516 | us |
| Servo Gier | 1399 | 1578 | us |

Alle Zeilen melden STABILIZE ohne angehaengten Fehler. Soll-Roll, Soll-Nick
und Soll-Gierrate sind ueberall 0.0. Kein protokollierter Servoausgang erreicht
die konfigurierten Pulsgrenzen. Nicht protokollierte Zwischenwerte sind unbekannt.
Die Ausgabe ist nur auf eine Nachkommastelle gerundet und nominell 4 Hz;
daraus lassen sich keine 100-Hz-Regelschleifenzeiten oder kurzen Fehler ableiten.

## Einordnung aus der Regelrechnung

Gier: Neutraler Knueppel fordert 0 Grad/s. Bei rate_p=1, I=0, sign=-1,
center=1500 und trim=0 gilt hier `Puls = int(1500 + gz)`; die Grenzen werden
im Auszug nicht erreicht. Fuer alle 51 Zeilen betraegt die Abweichung zwischen
gedrucktem Puls und `1500 + gedrucktem gz` -1.0..0.0 us, passend zu Rundung
und ganzzahliger Ausgabe. Beispielsweise links +69.4 Grad/s -> 1569 us;
rechts -100.2 Grad/s -> 1399 us. Mit der vom Besitzer bestaetigten Servopolung
sind das jeweils Gegenkorrekturen. Das ist Drehratendaempfung, kein Kurshalten.

Roll/Nick: Die protokollierten Korrekturen passen qualitativ zur Lage-/Ratenregelung.
Z.B. Roll=-7.3 Grad und gx=-12.7 Grad/s ergeben 1445 us; der Regler korrigiert
gegen Linksbank/Linksrollen. Pitch_down=6.2 und gy=-1.1 ergeben 1511 us:
Gegenwirkung zum positiven Nase-runter-Lagefehler trotz kleiner Gegenrate.
Eine exakte Quaternion-Nachrechnung benoetigt die fehlende Levelreferenz und
Orientierung; die entkoppelte Winkelrechnung ist nur eine Naeherung.

Der kleine Nickweg folgt hier aus kleinen Neigungen, neutralen Knueppeln und
rate_p=1. Daraus ergibt sich kein belegter Bedarf, die Gains zu erhoehen.
Ein von Hand bewegtes Modell schliesst den Regelkreis ueber seine Aerodynamik
nicht; ein Tischtest kann Flugstabilitaet oder Flugabstimmung nicht belegen.

## Akzeptanz und offene Nachweise

- Grundlegende Achsen-Richtung/Funktion: PASS nach Besitzerbericht.
- Software-Pulsrechnung im Auszug: plausibel; Gier quantitativ konsistent.
- Beide Knueppelrichtungen im Auszug: nicht enthalten, nur Besitzerbericht.
- RX-Ausfall/Wiederfreigabe, Timing-/Sensorfehler, Shutdown: nicht im Auszug.
- Versorgungsreserve/Brownout, Signalpegel, mechanische Grenzen: nicht gemessen.
- Fruehere Netzunterbrechung: Ursache weiterhin unbekannt; dieser Test klaert sie nicht.
- Exakter Board-Code, Runtime, Kalibrierung: noch zu archivieren.

68 Hosttests bestehen; Firmware-Syntaxpruefung und offene Punkte stehen in
[VALIDIERUNG.md](VALIDIERUNG.md). Der folgende Entwicklungsabschnitt ist
[Fehler-/Timingqualifikation](NAECHSTE_SCHRITTE.md), weiterhin beaufsichtigt am Tisch.
