# Erster MANUAL-Datenflug mit 20-Hz-Logger

Branch: `codex/manual-flight-tests-20hz`, direkt von0c1e3ba erstellt.
Der gepruefte Logger0.2.0 mit R1..R3 bleibt auf `codex/response-logger-20hz`.
Hier werden Flugkonfiguration, kleine notwendige Anpassungen und Flugnachweise
gesichert. Der Logger braucht fuer diesen Schritt keine neue Laufzeitfunktion.
Die225 Hosttests und R3 sind Bodennachweise, keine pauschale Flugfreigabe.

## 1. Ruderausschlaege am Modell einstellen

Besitzerangabe: Airframe ist eine Dream-Flight Libelle, bereits erfolgreich
mit direkter Receiver-/Servo-Ansteuerung geflogen. damalige Pulsbereiche und
gemessene Ausschlaege sind unbekannt. Der Empfaengerbetrieb hatte ebenfalls
einen durch Sender/Empfaenger bestimmten Pulsbereich. Der MCU normalisiert
diesen und skaliert ihn zusaetzlich auf `SERVOS[axis]['limit']`.

Aktueller Code bei center1500/trim0:

| Ruder | limit (us je Seite) | MCU-Pulsbereich | Libelle Low / High Rates |
| --- | --- | --- | --- |
| Quer | 200 | 1300..1700 us | 12 / 18 mm hoch und runter |
| Hoehe | 150 | 1350..1650 us | 11 / 14 mm hoch und runter |
| Seite | 150 | 1350..1650 us | 20 / 25 mm rechts und links |

Modellwerte aus der [offiziell verlinkten Dream-Flight-Anleitung](https://cdn.shopify.com/s/files/1/0263/8893/files/Manual_Libelle_May2014_1.pdf?15039821228917312629=),
gedruckte S.17 (PDF-S.22), Hersteller-Link auf der [Produktseite](https://dream-flight.com/products/libelle-dlg).
Sie sind Ziele am Ruder, keine Umrechnungsvorgabe in Mikrosekunden. Fuer den
ersten Datenflug die Low Rates oder einen bekannten bewaehrten Flugstand
verwenden. Der modifizierte Einbau muss die Wege frei zulassen.

Bei ausgeschalteten Quellen zunaechst Gestaenge/Scharniere/Kabel auf freien
Weg pruefen. Danach im bekannten, beaufsichtigten MANUAL-Bodenbetrieb messen:
Lineal bzw. Markierung hinter der Ruderhinterkante, immer derselbe Messpunkt.
Jeweils von Neutral bis zum Knueppelendpunkt, beide Richtungen getrennt.

| Messung bei aktuellem limit | Ist (mm) | Ziel fuer ersten Flug (mm) |
| --- | --- | --- |
| Hoehe hoch / runter | offen / offen | 11 / 11 |
| Seite rechts / links | offen / offen | 20 / 20 |
| Quer rechts hoch / runter | offen / offen | 12 / 12 |
| Quer links hoch / runter | offen / offen | 12 / 12 |

Wenn die Wege zu klein sind, limit fuer die betroffene Achse am Boden
schrittweise anpassen und erneut messen. Die vorhandene Konfiguration reicht;
Gains oder Senderkalibrierung sind dafuer kein Ersatz. Vor jedem Upload
sauber stoppen/Versorgung trennen, calibration.json erhalten, Soft-Reboot.
Kein universeller sicherer1000..2000-us-Bereich: Servohebel, Ruderhorn,
Scharniere und Freigaengigkeit bestimmen die zulaessigen Endpunkte.
Bei Anschlagen, Verspannen oder dauerndem Brummen sofort zuruecknehmen;
keine Blockiertests. [Pololu: Servo-Endpunkte](https://www.pololu.com/blog/17/servo-control-interface-in-detail).

limit gilt fuer MANUAL UND als Regler-Ausgabegrenze. Eine Aenderung wird mit
den gemessenen Ruderwegen separat committed und am Modell geprueft. Bei
gewuenschtem asymmetrischem Weg erst Mechanik/Mitte pruefen; der aktuelle
Parameter ist symmetrisch. Bei trim!=0 gelten weiter center+/-limit als
absolute Grenzen. Sender-Endpunkte/Trims nicht nebenbei veraendern: sie
beeinflussen Neutralfreigabe und die gespeicherte RC-Zuordnung.

## 2. Vor dem ersten Flug

- Vollstaendiges Flugmodell mit Akku, Haube und Elektronik wiegen und den
  Schwerpunkt neu pruefen. Libelle-Anleitung S.16: Ausgangsposition5 mm hinter
  dem Carbonholm, nicht weiter als6 mm dahinter. Kein alter Schwerpunktwert
  ohne Kontrolle nach Zusatzgewicht. Messstelle und Markierung aus der
  Abbildung auf S.16 der Anleitung verwenden.
- Akku, BEC, Leisten, Stecker und Gestaenge sichern; keine losen Jumper oder
  Kabel im Ruderweg.5 V/3V3 unter normalen gleichzeitigen Servobewegungen
  pruefen. Der bekannte BEC ist mit5 V/3 A beschriftet; Kondensator und Leiste
  vergroessern seine Dauerleistung nicht.
- IMU fest/achsparallel, GPS-Antenne zum Himmel, Barometer druckoffen und vor
  direkter Anstroemung geschuetzt. Nach Umsetzen der IMU ggf. Achsenabbildung,
  Levelreferenz und Richtungen korrigieren: [Einbauanleitung](EINBAU_UND_MANUAL_DATENFLUG.md).
- Ruder neutral, richtige Richtung, freie gemessene Wege, keine ungewollten
  Sender-Mischer. CH3 muss ausschliesslich Aufnahme schalten; das Y-Querruder
  erlaubt hier keine getrennten Flaperons. Keine neue Launch-/Flap-Mischung.
- Reichweitentest/Failsafe nach Anleitung des konkreten Senders/Empfaengers.
  Die MCU-Neutralreaktion erkennt fehlende Pulse; Receiver-Hold/Failsafepulse
  sind ein anderes Verhalten. Keine MCU-Stromverlustversuche mit den Rudern.

## 3. Starten, fliegen, sichern

Vorab alte Flugdaten auf dem Mac sichern und Platz auf dem MCU freigeben;
calibration.json erhalten. Der bestehende Export prueft vorsorglich bis zu
1088512 B freien Flash inklusive Reserven (volle132/1800 Records). Fuer einen
vollen Lauf deshalb rund1.1 MB freihalten; freier RAM ersetzt diesen Platz nicht.

1. Am Board `AUTO_START=False`, `LOGGER_PROFILE='response20'`,
   `LOGGER_BOOT_MODE='manual'`; Repository-Default fuer LOGGER_BOOT_MODE bleibt
   None. Keine neue Firmware fuer den Bordstart erforderlich: R3 hat ihn
   bestaetigt. MCU an geregeltem BEC5 V, USB ab. Sender an, Knueppel neutral,
   CH3 unten. [USB/BEC-Trennung](BORDSTART_LOGGER.md) einhalten.
2. Einschalten: Violett, BOOT2 s, bei Weiss loslassen. Gyro-Kalibrierung ruhig
   abwarten, MANUAL-Ruderwirkung pruefen. Draussen GPS-Gruen abwarten, Haube
   bereits geschlossen. Keine Aufnahme waehrend dieser Wartezeit.
3. Ruhiges geeignetes Flugfenster/offenes Gelaende waehlen. Fuer die erste
   Runde empfiehlt die Herstelleranleitung einen normalen geraden Gleitwurf
   vor staerkeren Discusstarts. CH3 erst kurz vor dem Start oben; dann ist
   Gruen blinkend zu sehen. Etwa90 s Aufnahme insgesamt, kein Flugtimer.
4. Ausschliesslich MANUAL: gewohnte kleine Steuerbewegungen, keine absichtlich
   extremen Lasten/Stalls oder Gains-Experimente. Der getestete IMU-Bereich
   ist2 g/250 Grad/s; Saettigung markiert Daten und verriegelt Automatik,
   MANUAL blieb in R3 aktiv. Das ist kein Stabilisierungstest.
5. Nach Landung CH3 unten, BOOT2 s nur am Boden. Bis Tuerkis/Export fertig
   versorgt lassen. Dann abschalten, MCU5 V vom BEC-Netz trennen, erst danach
   Mac-USB fuer Download anschliessen. Akku aus allein trennt diese5-V-Schiene
   nicht sicher von USB. Alle drei Dateien und calibration.json sichern.
6. Pro Flug einen eigenen Ordner unter docs/testdaten/flugtests/ nutzen.
   Kurz notieren: Codecommit, gemessene Wege, Masse/Schwerpunkt, Einbau-/IMU-
   Ausrichtung, Wind, Startart, Aufnahme-/Flugverlauf und Auffaelligkeiten.
   RAM ist nach Stromverlust weg; nichts vor bestaetigtem Export ausschalten.

Nach dem Flug zuerst Vollstaendigkeit, GPS-/IMU-Gueltigkeit, Timing und
MANUAL-Kontinuitaet auswerten. Fuer Gains interessieren dann Ruderkommandos
gegen Gyro-/Lageantwort, noch keine automatischen Gain-Aenderungen. Bei
IMU-Saettigung die markierten Abschnitte gesondert behandeln. Vor einem
spaeteren STABILIZE-/Kreisflug Messbereich und Verhalten unter Last auslegen.
