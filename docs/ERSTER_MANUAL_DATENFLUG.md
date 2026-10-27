# Erster MANUAL-Datenflug mit 20-Hz-Logger

Aktueller naechster Schritt: [Logger0.3.0 am Boden vergleichen](LOGGER_030_TEST.md).
Speicherpruefung, groessere IMU-Bereiche und Lage-Wiederfang sind implementiert,
noch nicht am Board bestaetigt. Die nachfolgenden Flugbefunde gehoeren0.2.0.

Erste Fluege inzwischen durchgefuehrt (2026-10-27):
[Auswertung der sechs Aufnahmen](testdaten/fluglogger/flights/F1/AUSWERTUNG.md).
MANUAL/GPS/Barometer funktionieren im gespeicherten Lauf; IMU-Startsaettigung,
Lage-Wiederfang und Vorab-Exportplatzpruefung sind jetzt die naechsten Arbeiten.
Die folgende Bedienfolge bleibt die Beschreibung des bisherigen Standes.

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

Besitzerstand2026-10-27, in Code und R4-JSON gleich, bei center1500/trim0:

| Ruder | limit (us je Seite) | MCU-Pulsbereich | Besitzerangabe am Modell | Libelle Low / High Rates |
| --- | --- | --- | --- | --- |
| Quer | 230 | 1270..1730 us | 13 mm | 12 / 18 mm hoch und runter |
| Hoehe | 400 | 1100..1900 us | 12 mm | 11 / 14 mm hoch und runter |
| Seite | 350 | 1150..1850 us | 19/20 mm | 20 / 25 mm rechts und links |

Der Besitzer will mit diesen Wegen den ersten MANUAL-Datenflug durchfuehren
und meldet alle Ruder frei und funktionsfaehig. Die Angaben sind keine
unabhaengige Messung: bei Quer/Hoehe wurden Richtungen und beide Querruder
nicht getrennt beziffert; bei19/20 mm fehlt die Rechts-/Links-Zuordnung.
Schwerpunktoptimierung und Sichern aller Komponenten sind noch angekuendigt,
nicht als erledigt dokumentiert. [R4-Bodenbefund](testdaten/fluglogger/R4_response20_limits_indoor/AUSWERTUNG.md).

Modellwerte aus der [offiziell verlinkten Dream-Flight-Anleitung](https://cdn.shopify.com/s/files/1/0263/8893/files/Manual_Libelle_May2014_1.pdf?15039821228917312629=),
gedruckte S.17 (PDF-S.22), Hersteller-Link auf der [Produktseite](https://dream-flight.com/products/libelle-dlg).
Sie sind Ziele am Ruder, keine Umrechnungsvorgabe in Mikrosekunden. Die
Besitzerangaben liegen etwa im Bereich der Low Rates, Quer/Hoehe etwas darueber.
Das allein bestaetigt keine Symmetrie oder Flugabstimmung. Der modifizierte
Einbau muss die Wege frei zulassen.

Bei ausgeschalteten Quellen zunaechst Gestaenge/Scharniere/Kabel auf freien
Weg pruefen. Danach im bekannten, beaufsichtigten MANUAL-Bodenbetrieb messen:
Lineal bzw. Markierung hinter der Ruderhinterkante, immer derselbe Messpunkt.
Jeweils von Neutral bis zum Knueppelendpunkt, beide Richtungen getrennt.

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
absolute Grenzen. Sender-Endpunkte vor dem Flug festlegen; Trimmung wie unten
behandeln. Die RC-Mitte wird durch Trimmen nicht automatisch neu gelernt.

### Trimmen nach Freigabe und waehrend der Aufnahme

Ja: nach der ersten Neutralfreigabe bleibt MANUAL bei frischen RC-Signalen
freigegeben. Sendertrimmung ist ein normales Steuerkommando; weder Trimmen
noch CH3-Aufnahme/Pause fordert selbst eine neue Neutralfreigabe.
Eine4-%-Totzone um die gespeicherte RC-Mitte bleibt aber aktiv: kleine erste
Trimmklicks innerhalb dieser Zone bewegen das Ruder noch nicht. Ausserhalb
wirkt die normale skalierte MANUAL-Kennlinie, keine direkte Pulsdurchleitung.

Ab Logger0.3.0 gilt im **MANUAL-Profil**: nach RX-/Timingausfall bis zu neuen
gueltigen Frames aller Steuerachsen Trimneutral ausgeben; danach das aktuelle
Kommando ohne erneutes Zentrieren/Zuruecktrimmen uebernehmen.25 Neutralframes
werden nur vor der ersten Aktivierung verlangt, erneut nach Programmneustart.
Alte/gepufferte Pulse bleiben gesperrt. Automatikfaults bleiben verriegelt;
das STABILIZE-Profil behaelt vorerst seine Neutral-Wiederfreigabe.
Starke dauerhafte Trimmung kann die erste Startfreigabe erschweren; nach der
Landung Mechanik/Konfiguration pruefen, nicht im Flug neu kalibrieren.
Trimmrichtung und ungefaehren Zeitpunkt in der Flugnotiz vermerken: die Logs
enthalten RX-/Servo-Pulse, aber keinen separaten Sender-Trimmwert.

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
calibration.json erhalten.0.3.0 prueft Platz vor dem Start und zaehlt den
Export nach Hardwarestop exakt; die alte~1.1-MB-Schwelle aus0.2.0 entfaellt.
Bei4096-B-FS-Bloecken sind konservativ507904 B fuer ein volles Paket inkl.
128-KiB-Reserve vorgesehen,884736 B fuer zwei,1261568 B fuer drei. Anzeige
des Boards beachten; jeder Start hat weiterhin nur90 s gemeinsamen RAM.

1. Am Board `AUTO_START=False`, `LOGGER_PROFILE='response20'`,
   `LOGGER_BOOT_MODE='manual'`; die aktuelle Besitzer-Arbeitskopie setzt auch
   START_MODE='manual' und body_signs=(-1,-1,1). R4-Referenz und Mapping passen
   zusammen; das ersetzt keine physische Richtungspruefung nach einem Umbau.
   Keine neue Firmware fuer den Bordstart erforderlich: R3 hat ihn
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

### Mehrere Fluege und Speicher

Die1800 schnellen Records reichen fuer ungefaehr90 s AUFNAHME insgesamt pro
Programmstart, nicht pro CH3-Segment oder Flug. CH3 unten pausiert nur: keine
Speicherung und kein Leeren des RAM. Mehrere kurze Fluege sind im selben Lauf
moeglich, wenn die gemeinsame Aufnahmezeit hineinpasst und die Versorgung
zwischen den Fluegen bleibt. Bei FULL endet nur die Aufnahme; MANUAL laeuft
weiter. Sehr viele Segmente/Zustandsereignisse koennen zuvor den132-Zeilen-
Vollsnapshot-Puffer fuellen.

Fuer wieder etwa90 s beim naechsten Flug: landen, CH3 unten, BOOT2 s,
Export/Tuerkis abwarten, abschalten und fuer den naechsten Flug neu starten.
Erneut BOOT-Freigabe, ruhige Gyro-Kalibrierung, RC-Neutralfreigabe und GPS-ready.
BOOT beendet dabei das Steuerprogramm; nach dem Export fliegt es nicht weiter.
Die Dateien erhalten neue Namen, alte Laeufe werden nicht ueberschrieben.

RAM begrenzt die Aufnahme, Flash nimmt erst nach dem Stop die CSV/JSONs auf.
Vor JEDEM Export muss genuegend Flash frei sein: bis1088512 B fuer einen
vollen Lauf einschliesslich konservativer Text-/Dateisystemreserve. Dieser
freie Platz muss auch neben schon gespeicherten Fluegen noch vorhanden sein.
R4 belegt als gemessene Groessenordnung112959 B fuer41.691 s Aufnahme;
daraus keine feste Fluganzahl oder volle90-s-Dateigroesse ableiten. Vor dem
Flugtag alte Logs auf dem Mac sichern und bei Bedarf nur gesicherte Logs vom
Board entfernen. RAM-Verlust durch Ausschalten kann freier Flash nicht retten.

Nach dem Flug zuerst Vollstaendigkeit, GPS-/IMU-Gueltigkeit, Timing und
MANUAL-Kontinuitaet auswerten. Fuer Gains interessieren dann Ruderkommandos
gegen Gyro-/Lageantwort, noch keine automatischen Gain-Aenderungen. Bei
IMU-Saettigung die markierten Abschnitte gesondert behandeln. Vor einem
spaeteren STABILIZE-/Kreisflug Messbereich und Verhalten unter Last auslegen.
