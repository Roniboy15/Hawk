# Vorlage — Fehler-/Timing-Tischtest v0.2.3

Fuer den tatsaechlichen Lauf kopieren/ausfuellen, z.B. logs/testprotokoll.md.
Anleitung: [FEHLER_TISCHTEST.md](FEHLER_TISCHTEST.md).
PASS erst nach Softwareauswertung **und** passender physischer Beobachtung;
OFFEN ist kein PASS. Kein Flugnachweis.

- Datum/Zeit, Besitzer:
- Git-Stand/ungecommittete Aenderungen:
- Firmwareversion laut Startausgabe:
- MicroPython-Version (steht auch im JSON):
- Board/Sensor/Receiver/BEC-/Servomodelle:
- Aktuelle Versorgung/Masse/USB; Stromleiste bereits eingebaut?:
- Physische Pinpfade: Roll RX/Servo, Nick RX/Servo, Gier RX/Servo:
- Geraetekalibrierung und MCU-Dateien auf Mac gesichert?:
- Signalpegel-/Versorgungsmessungen vorhanden? Werte/Geraet oder OFFEN:
- Testadapter fuer T4 (nur Signalunterbrechung):

| Test | Physische Beobachtung | Auswerter | CSV/JSON-Dateien | PASS / FAIL / OFFEN |
| --- | --- | --- | --- | --- |
| T1 SENSOR 30 s | | | | |
| T2 Start nichtneutral, dann neutral | | | | |
| T3 Roll fehlt beim Start | | | | |
| T3 Nick fehlt beim Start | | | | |
| T3 Gier fehlt beim Start | | | | |
| T4 Rollverlust/Wiederfreigabe | | | | |
| T4 Nickverlust/Wiederfreigabe | | | | |
| T4 Gierverlust/Wiederfreigabe | | | | |
| T5 STABILIZE 60 s, Lauf 1 | | | | |
| T5 Lauf 2 | | | | |
| T5 Lauf 3 | | | | |
| T6 PITCH_RANGE verriegelt | | | | |

T5-Maxima/Zaehler aus JSON bzw. Auswerter (us):

| Lauf | period max | pre_output max | write max | work max | work > Sollperiode | TIMING-Erkennungen |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

- Ungewoehnliches Brummen/Zittern/Anschlag/Hitze, USB-Reset oder Versorgungsereignis:
- Exakte Reaktionszeit physisch gemessen? Verfahren/Werte oder OFFEN:
- Receiver bei Sender-Aus: keine Pulse / Hold-Pulse / gesetzte Pulse / OFFEN:
- Probleme, Abbruchgrund und benoetigte Folgepruefung:

Nach Abschluss gespeicherte Datei-Defaults SENSOR/AUTO_START=False sowie
Nickgrenze 75 Grad beibehalten. Testergebnisse nicht als Flugfreigabe markieren.
