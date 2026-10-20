# Erster BN-180-Aussentest: Empfang bestaetigt, Positionsnachweis offen

Nachtrag 2026-10-20: [gps_2 mit Konsolenauszug](AUSWERTUNG_GPS_2.md)
bestaetigt Fix/Bewegungsreaktion und schliesst S2 funktional ab. Folgender
Bericht beschreibt unveraendert den ersten Lauf; naechster Schritt ist S3.

Eingang/Auswertung 2026-10-19, Branch codex/gps-baro-bringup.
Dateien: [gps.csv](gps.csv), [gps.json](gps.json), unveraendert erhalten.
Testversion laut JSON 0.1.0, control_version 0.2.3-bench. Kein vollstaendiges
Archiv der zum Test verwendeten MCU-Quelldateien. Nur Hostauswertung/-tests,
keine MCU-/GPS-Kommandos oder Servobewegungen durch die Auswertung.

## Ergebnis

**UART-Datenverbindung und NMEA-Dekodierung bestaetigt; S2 noch nicht bestanden.**
Das Modul liefert pruefsummenkorrekte Daten. Im Lauf wurde kein gemeinsamer
gueltiger GGA/RMC-Fix aufgezeichnet, daher keine nutzbare Position nachgewiesen.
Ein Fehler im Lesecode kann Daten verwerfen und die Beobachtung verfälschen;
er ist unten beschrieben und fuer Testversion 0.1.1 hostgeprueft korrigiert.
Ob das GPS spaeter selbst einen Fix hatte, ist mit diesem Lauf nicht sicher
entscheidbar. Es wird weder ein defektes GPS noch ein erfolgreicher Fix behauptet.

Besitzerbericht: draussen getestet; LED zuerst blau, spaeter rot und blau.
Weisses Kabel laut Beschreibung **GPS-TX-Ausgang**; erfolgreicher NMEA-Empfang
ist damit vereinbar. Diese Farbe nur fuer das konkrete Exemplar dokumentieren,
nicht als allgemeine BN-180-Pinfolge. TX-Spannungspegel nicht gemessen.
LED-Farben allein ersetzen keinen protokollierten Positionsnachweis.

## Verifizierte Logwerte

| Merkmal | Befund |
| --- | --- |
| Profil / Dauer / Ende | gps / 180225 ms / duration, shutdown_ok=true |
| Runtime | MicroPython v1.29.0, Waveshare RP2040-Zero |
| UART-Konfiguration | UART0 RX GP13, 9600 Baud, rxbuf 1024, max_read 256 |
| Ausgewertete Bytes | 46080, verworfene UART-Bytes sind darin nicht mitgezaehlt |
| NMEA-Saetze | 908 pruefsummenkorrekt; 360 GGA/RMC-Updates, 548 andere ignoriert |
| Empfangsfehler | checksum_errors=0, parse_errors=0, overlong=0, resyncs=0 |
| Pollpausen >100 ms | 314, mit Loeschen des aktuellen GPS-Zustands und Verwerfen von Altdaten |
| Positionsfix | first_paired_fix_ms=null, gps_fix_log_samples=0 |
| CSV | 635 erzeugte Zeilen, letzte 200 erhalten, 113452..179850 ms |
| CSV-Gueltigkeit | gps_valid/gga_valid/rmc_valid jeweils 0 in allen 200 Zeilen |
| CSV-Koordinaten / Geschwindigkeit / Kurs | alle leer, korrekt nicht als 0/0 dargestellt |
| Exceptions | errors={}, keine verriegelte Sensorausnahme; das ist kein Timing-PASS |
| Barometer | Profil gps, daher erwartungsgemaess keine Barometerdaten |

Die ersten vier Rohsaetze haben korrekte Pruefsummen. Der erste RMC-Satz
meldet Status V und Modus N, der erste GGA-Satz quality=0 und 00 benutzte
Satelliten. Das belegt **No-Fix zu Beginn**, nicht fuer die ganzen drei Minuten.
Die CSV zeigt ebenfalls satellites=0, aber dort fehlen die GGA/RMC-Zustaende
(Alter -1): Diese Nullen sind bei den vielen Ruecksetzungen kein belastbarer
Nachweis, dass der Receiver die ganze Zeit keine Satelliten genutzt hat.

Timing des separaten Sensorstarters, nicht des Flugreglers:

- work: Mittel 12.758 ms, Maximum **423.331 ms**; 324/8260 Iterationen >50 ms.
- period: Mittel 21.774 ms (ca. 45.93 Hz), Maximum **423.541 ms**;
  323/8259 Startabstaende >50 ms.
- Gespeicherte CSV-Zeilen im Abstand 201..435 ms, Mittel 333.658 ms.
  Die 200 Zeilen decken deshalb hier ca. 66.4 s statt nominell 40 s ab.

Hostpruefung: CSV-Schema mit 25 Feldern, 200 Zeilen passend zum JSON,
streng steigende Zeit, Gueltigkeitsflags, leere Positionsfelder und
Pruefsummen/Status der vier gespeicherten NMEA-Anfangssaetze geprueft.
CSV/JSON wurden vom Besitzer umbenannt (JSON nennt sensors_298386_0.csv);
keine gemeinsame kryptografisch gesicherte Laufkennung vorhanden.

| Datei | SHA-256 |
| --- | --- |
| gps.csv | 44b66d05f68d75ee801d2be15fc5693d6ff282508ca7748af89251d9c7eead14 |
| gps.json | e902f2a0c0646ca965afd865d6e7e2eb970abb7f1c8233c5c19bdf2c8a4eb020 |

## Fehler im Empfangscode und Korrektur 0.1.1

Der bisherige Code prueft UART.any(), fordert danach aber fest 256 Bytes an;
beim Verwerfen sogar 1024. Die RP2-Implementierung von MicroPython v1.29.0
erzwingt bei 9600 Baud mindestens 2 ms Zeichen-Timeout auch bei timeout_char=0.
Nach einem gelesenen Zeichen kann read deshalb weitere eintreffende Zeichen
abwarten. Ein kontinuierlicher 256-Byte-Burst dauert bei 8N1 etwa 267 ms.
Die Laengenbegrenzung allein macht diesen Aufruf also nicht wartefrei.

Der naechste Poll erkennt dann die selbst verursachte Pause >100 ms,
loescht GGA/RMC und verwirft weitere Daten. Dieser Mechanismus ist anhand
der Quellen und zwei Hosttests reproduziert. Die 314 Pollpausen, langen
Arbeitszeiten und genau 180*256 ausgewerteten Bytes passen dazu. Ohne
Phasenmessung auf dem MCU ist nicht jede einzelne Spitze zugeordnet;
weitere Ursachen wie Konsolenausgabe sind damit nicht ausgeschlossen.

Korrektur in gps.py: sowohl Empfang als auch Verwerfen fordern hoechstens
min(sofort verfuegbare Bytes, Mengenlimit) an. 100-ms-Frischegrenze, NMEA-
Pruefsummen und Anforderungen an einen gemeinsamen Fix bleiben erhalten.
Neue Zaehler gga_fix_sentences/rmc_fix_sentences/max_satellites_used halten
den jemals empfangenen Receiverstatus auch nach einer Zustandsruecksetzung
fest; sie sind keine aktuelle Navigationsgueltigkeit. Keine GPS-Konfiguration
gesendet, keine Aenderung an Steuerung, Vorzeichen, Gains oder Kalibrierung.

Zwei neue Tests mit zeitlich eintreffenden 9600-Baud-Daten scheiterten vor
der Korrektur und bestehen danach: normaler Empfang und Altdatenverwerfen
warten nicht auf zukuenftige Bytes. Ein dritter Test prueft die getrennten
Receiverstatus-Zaehler nach No-Fix, Fix und Frischeverlust. Insgesamt **123
Hosttests bestanden** (94 bestehende Steuerungs- und 29 Sensortests).
Das ist noch keine gemessene Zeitgarantie oder ein echter GPS-Fix mit 0.1.1.

Quellen: [MicroPython RP2 v1.29.0 UART-Implementierung](https://github.com/micropython/micropython/blob/v1.29.0/ports/rp2/machine_uart.c),
[UART.any/read](https://docs.micropython.org/en/v1.29.0/library/machine.UART.html).
NMEA-Felddefinitionen: [u-blox 8/M8 Protokoll](https://content.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf).

## Konkrete Wiederholung

1. BEC/Receiver/Servos aus; nur MCU/Sensoren per USB. Die sechs zusammengehoerigen
   Dateien aus [SENSOREN_TEST.md](../../SENSOREN_TEST.md) aktualisieren,
   calibration.json erhalten, Soft-Reboot. Sensor-Test muss **0.1.1** melden.
2. Draussen bei freier Himmelsicht und Antenne nach oben starten:
   `import sensor_test`, dann `sensor_test.run('gps', duration_s=300)`.
   Erst ruhig ablegen. In der Konsole auf GPS fix=1 und gefuellte lat/lon warten;
   Standort vergleichen. Ein Fix innerhalb dieser Dauer ist keine Garantie.
3. Nach Fix etwa 10..20 m gehen, anhalten und die Reaktion beobachten.
   course_usable kann bei langsamem Gehen korrekt 0 bleiben (Schwelle 2 m/s).
4. Nach den beiden Speichermeldungen neues Dateipaar in einen eigenen
   Unterordner, z.B. gps_tests/Wiederholung_0.1.1, sichern. Diesen ersten Lauf
   erhalten. Erneut Fixstatus, neue Receiverzaehler, Datenfehler und Pollpausen
   sowie work/period vergleichen. errors={} allein reicht nicht.
5. Bei weiterhin fehlender Position erst neue Daten auswerten: Fixsaetze >0
   bei vielen Pollpausen deutet auf Softwarebeobachtung; keine Fixsaetze bei
   stabilem Empfang erfordert Empfangsbedingungen/Antennenlage weiter zu pruefen.
   Beides sind Diagnosehinweise, keine alleinigen Ursachenbeweise.

S3 gemeinsam folgt nach bestaetigtem S2. Der separate USB-Endausschlagsbefund
bleibt offen fuer den naechsten Aktuatorbetrieb und wird durch GPS-Empfang
nicht geklaert. Die Sensorwiederholung selbst benoetigt keine Servoversorgung.
