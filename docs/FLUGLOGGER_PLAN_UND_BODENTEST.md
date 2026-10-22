# Fluglogger: CH3-Bedienung, Datenpaket und erste Bodenmessungen

Stand 2026-10-21, codex/manual-flight-logger. Besitzerwunsch ersetzt den alten
Fuenf-Minuten-/1-Hz-Entwurf: **kein Flugtimer**, Aufnahmebeginn und -ende per
freiem Gaskanal CH3. Kein Triebwerk vorhanden. Zunaechst vorhandenen Board-Flash
am Boden vermessen, keine neue Speicherhardware voraussetzen.
Besitzer nennt mindestens etwa **zehn Minuten gesamte Aufnahme pro Flug** als
Dimensionierungsziel, ausdruecklich keinen Abschalttimer.

**L1/L2 ausgewertet:** CH3 unten 998 us/oben 1998 us, Dateien korrekt,
Flash-Schreibzyklen aber bis 181.709 ms. Deshalb keinen normalen Dateiwriter
in den MANUAL-Loop einbauen. [Ergebnisbericht](testdaten/logger_boden/AUSWERTUNG_L1_L2.md).
**L3 0.1.4 bestanden:** frueh reservierte 91008 B in 40 Bloecken passen mit
dem Modulumfang, danach 68656 B frei (65536 B Reserve plus 3120 B Spielraum).
Der Besitzer hat **1-Hz-Gesamtdatensaetze im RAM** fuer die ersten MANUAL-
Basisdatenfluege bestaetigt. Flash erst nach Landung/Programmstop, BOOT ist
zugaenglich. Loggerprototyp 0.1.0 ist implementiert. Erster gemeinsamer F1-Lauf
belegt Bedienung/Export, aber neun Zeitueberschreitungen >50 ms und keinen
GPS-Fix am Fenster. [F1-Auswertung](testdaten/fluglogger/F1_sensor/AUSWERTUNG.md).
[L3-Auswertung](testdaten/logger_boden/AUSWERTUNG_L3.md).

**Aktualisierung2026-10-22:** F2 MANUAL mit Logger0.1.8 hat den gezielten
Bodenvergleich ohne Timing-/RC-Unterbrechung bestanden; GPS-Fix und zehn
Minuten Aufnahme bleiben offen. Zuerst Bordversorgung/bewussten Loggerstart
ohne Mac vorbereiten. [Aktuelle Testfolge](FLUGLOGGER_TEST.md),
[Befund](testdaten/fluglogger/F2_gc_018/AUSWERTUNG.md).
Die folgenden Entwurfsabschnitte dokumentieren auch fruehere Optionen.
flight_start reserviert vor Imports und waehlt
das Profil nur im RAM. app.run(session=...) nutzt optional GPS/Baro/CH3/LED/BOOT
nach Servoausgabe, misst deren Kosten und exportiert erst nach Hardwarestop.
Der bisherige Aufruf ohne Session und AUTO_START=False bleiben erhalten.
Keine laufenden Flashzugriffe, keine neuen Gains/Achsensigns/Kalibrierdateien.
Standalone-Bordstart ohne Thonny ist noch nicht eingerichtet. Keine neue
isolierte L3-Wiederholung; Hardwaremessung durch Besitzer, nicht Agenten.

## Bedienung des spaeteren Flugloggers

| Knueppel / Ereignis | Aufnahme | Flugsteuerung |
| --- | --- | --- |
| Unterer Anschlag bestaetigt | Aus; noch gepufferte Daten geordnet abschliessen | Weiter MANUAL |
| Oberer Anschlag bestaetigt | Ein; neues Segment mit eigener Kennung | Weiter MANUAL |
| Zwischenstellung | Vorherigen Zustand behalten | Weiter MANUAL |
| CH3 ungueltig/zu alt | Aufnahme pausieren, Ereignis/Status melden | Kein zusaetzlicher Ausfall der Steuerachsen |
| Speicher voll / Schreibfehler | Aufnahmefehler anzeigen; alte Daten erhalten | Weiter MANUAL |

Beim Einschalten zuerst stabil unten verlangen. Oberer Anschlag beim Booten
startet nicht versehentlich die Aufnahme. Vorschlag: 200 ms stabile
Endbereichsbestaetigung. L1 plus Besitzerzuordnung: unten 998 us, oben 1998 us.
Vorbereitet sind <=1200 us aus und >=1800 us ein, sign=+1. Die physische
Polung kann bei anderen Sendern abweichen;
RecordingSwitch unterstuetzt beides. Die Zwischenstellung setzt nur den
Bestaetigungstimer zurueck, nicht den aktuellen Aufnahmezustand.

CH3 ist kein vierter Regelkanal: nicht zu ACTIVE_AXES hinzufuegen, nicht in die
Neutralpruefung fuer Roll/Nick/Gier aufnehmen und nicht durch seinen Verlust
receiver.all_fresh() fuer diese drei Achsen false werden lassen. Bestehende
Reaktionen auf echten Verlust der Steuerkanaele bleiben bestehen.
Wenn am Empfaenger moeglich, CH3-Failsafe auf Aufnahme aus setzen und am Boden
pruefen. Weitergelieferte alte/Failsafe-Pulse sind fuer den MCU weiterhin frisch;
aus dem Pulstimeout allein laesst sich kein sicherer Funkverlustnachweis ableiten.

Aufnahme aus darf niemals app.run() beenden, PWM abschalten oder im Flug
einen langen CSV-/JSON-Export starten. Aufnahmezustand, ausstehende Schreibdaten
und Dateischluss sind getrennte Zustaende. Nach erneutem oben beginnt ein
weiteres Segment; alte Segmente nicht ueberschreiben. Nach Landung erst
ausschalten, wenn die Statusanzeige den Abschluss aller Schreibdaten bestaetigt.

## GPS-Bereitschaft und Anzeige

Verifiziert bei Beitian fuer BN-180: **blaue TX-LED blinkt bei Datenausgabe**,
PPS-LED beginnt nach 3D-Fix zu blinken. Die TX-LED belegt keinen Fix; PPS belegt
nicht, dass unsere Software die UART-Daten erfolgreich verarbeitet.

Vorschlag fuer die vorhandene MCU-RGB-LED: Farbe zeigt Datenbereitschaft,
Blinkmuster Aufnahme. Gruen dauerhaft = bereit/keine Aufnahme, gruen blinkend
= Aufnahme mit gueltigem GPS. Rot = GPS aktuell nicht bereit; bei Aufnahme
weiter blinkend. Speicher-/Loggerfehler mit klar abweichendem orangefarbenem
Fehlermuster kennzeichnen. Die endgueltigen Muster vor Einsatz dokumentieren.
LED ist im Prototyp implementiert; finale Muster/Tests siehe FLUGLOGGER_TEST.md.
Einbau muss sie sichtbar lassen oder einen
externen Indikator vorsehen. Die genaue LED-Platine/Ansteuerung vor Test abgleichen.

Softwarebereitschaft aus frischen, gueltigen, pruefsummengeprueften GGA/RMC
derselben UTC-Epoche, gueltigen Koordinaten und stabilen Folgeupdates ableiten.
Vorschlag: fuenf aufeinanderfolgende neue Fixepochen, Alter maximal 2.5 s,
mindestens sechs benutzte Satelliten und HDOP <=2.5. Das sind vorgeschlagene
Qualitaetskriterien, keine vermessene Positionsgenauigkeit. Zwischen GGA/RMC
derselben naechsten Epoche nicht bei jedem einzelnen Poll die LED flackern
lassen; den letzten vollstaendigen Fix getrennt mit seinem Alter bewerten.
Gueltigkeit beim Logsample trotzdem explizit speichern, alte Werte nicht neu datieren.

GPS-Verlust im Flug darf weder MANUAL noch die uebrige Datenaufnahme beenden.
Fehlende Koordinaten als fehlend markieren. Kein blockierendes Warten auf Fix;
der Besitzer entscheidet anhand der Anzeige ueber den Start. Logging darf auch
ohne Fix die uebrigen Daten und den Empfangsfehler dokumentieren.

## Vorgeschlagenes Datenpaket

Die folgende Tabelle ist der urspruengliche Entwurf fuer hoehere Datenraten.
Die erste implementierte Version nutzt nach Besitzerwahl 1 Hz fuer alle Gruppen;
Details/Felder/46-Spalten-Schema in [FLUGLOGGER_TEST.md](FLUGLOGGER_TEST.md).
Nach L2 benoetigt er einen anderen Speicherpfad. Die vorgeschlagene einfachere
RAM-Variante zeichnet alle Gruppen zunaechst gemeinsam mit 1 Hz auf; die
interne Sensorabfrage und MANUAL-Ausgabe werden dadurch nicht auf 1 Hz reduziert.
Laufzeitaggregate jeder Iteration und wichtige Zustandsereignisse bleiben wichtig.

| Gruppe | Zielrate | Inhalt |
| --- | --- | --- |
| Schnelle Flugreaktion | **25 Hz** als erster Entwurf, 50 Hz bei nachgewiesenem Platz-/Timingbudget | Zeit, Sequenz, Gyro xyz, RX-Pulse aller drei Achsen und CH3, kommandierte Servo-Pulse, Modus/Fault/Gueltigkeit, Perioden-/Arbeitszeit |
| Lage / Beschleunigung | **10 Hz** | Roll/Nick/Gier, kalibrierte Beschleunigung xyz, Sensoralter/Gueltigkeit |
| Barometer | **10 Hz**, nur neue Messungen | Druck, Sensortemperatur, relative Hoehe, Alter; D1/D2 fuer Nachrechnung |
| GPS | **1 Hz**, aktuelle Empfaengerrate | Datum/UTC, lat/lon, GGA-Hoehe MSL, Groundspeed, Kurs und dessen Nutzbarkeit, Fixqualitaet, Satelliten, HDOP, Alter |
| Diagnose | Jede Iteration aggregieren, etwa 1 Hz Status | Phasenlaufzeiten/Maxima, RX-Alter/Status, Deadline-/FIFO-/Verwerfungszaehler, Sensor-/Loggerfehler, belegter/freier Puffer, verworfene Records |
| Ereignisse | Bei Aenderung | Aufnahme an/aus, Kanalverlust, Fixverlust/-wiederkehr, Fehler, voller Speicher; mit Zeit/Segmentkennung |
| Metadaten | Pro Start / Segmentzuordnung | Codeversion/Commit, Konfiguration/Gains/Servo-Grenzen, verwendete Kalibrierung/Achsen, Runtime, Resetgrund, Startzeit/Bootkennung, Schema |

25/50 Hz sind Ziele fuer die schnellen Daten, keine Zusage, dass der aktuelle
75..100-Hz-Controller samt Zusatzsensoren/Dateisystem das schafft.
Nur gelesene Samples speichern; keine interpolierten Zwischenmessungen als
echte Messungen ausgeben. GPS nicht 50-mal pro Sekunde duplizieren und dadurch
hoeheren Informationsgehalt vortaeuschen. GPS vorerst nicht umkonfigurieren.
Zeitgesteuert ohne Nachholschleife aus echten Samples abtasten, tatsaechliche
Zeitabstaende/ausgelassene Termine erfassen. Periodische Konsolenausgaben im
spaeteren Flugprofil vermeiden; Messphasen/Schreibpufferarbeit zeitlich erfassen.

Zum Platzsparen binaere Records mit Typ, Laenge, Sequenz, monotoner Zeit und
Pruefsumme; CSV und Diagramme auf dem Mac erzeugen. Vollstaendige Records
nach unvollstaendigem Dateiende wiederfinden koennen. Eine fehlende Endmarke
als unsauberen Abschluss zeigen, nicht als fehlerfreien Flug.

Gier aus der jetzigen IMU ist kein absoluter Kompasskurs, GPS-Kurs im Stillstand
keine Rumpfausrichtung und Groundspeed keine Airspeed. Servo-Pulse sind
kommandierte Ausgaben, keine gemessenen Ruderwinkel. MANUAL-Daten erlauben
Reaktions-/Verzoegerungsabschaetzung; die PID-Gains werden darin nicht erprobt.
Spaetere Gainabstimmung braucht gezielte, getrennte Stabilisierungsversuche.

Aktualitaet: der bisherige Apppfad liest nach verriegeltem Automatikfault die
IMU nicht weiter. Mit Flugsession wird weiter gelesen, ohne die Sperre zu
loeschen; ungueltige Daten werden explizit fehlend gespeichert. Keine
eingefrorenen Winkel als neue Messungen ausgeben.

## Reicht mehr als 1 MB freier Flash?

L2 misst vor den Testdateien 1265664 freie Bytes (1.207 MiB).
Freier Flash ist kein freier RAM. Er allein belegt weder kurze Schreibpausen
noch unbegrenzte Aufnahmedauer. Beispielbudget, noch kein implementiertes
Dateischema: 32 Bytes je schnellem Record, 24 Bytes je Lage-/Beschleunigungsrecord,
32 Bytes je Barorecord, 64 Bytes je GPSrecord, 32 Bytes je Sekundenstatus;
Ereignisse/Metadaten/Dateisystem kommen hinzu. Das benoetigt gezielte binaere
Kodierung/Skalierung, ohne CSV-Text oder staendige Wiederholung langsamer Werte.
Diese Packgroessen muessen beim spaeteren Encoder mit Rundungs-/Bereichstests
bestaetigt werden; sie sind keine gemessene Dateigroesse.

| Reaktionsrate | Nutzdaten pro Sekunde | Rechnerische Kapazitaet bei 1 MiB frei minus 128 KiB Reserve |
| --- | --- | --- |
| 50 Hz | 2256 B/s | etwa 6.8 min |
| 25 Hz | 1456 B/s | etwa 10.5 min |
| 10 Hz | 976 B/s | etwa 15.7 min |

Das sind Schaetzungen der Speicherfuellung, **keine programmierte Flugzeitgrenze**.
25 Hz liegt bei genau 1 MiB frei fuer zehn Minuten knapp; fuer Ereignisse und
Dateisystem Platz einrechnen und die echte freie Kapazitaet aus L2 verwenden.
Mit einem groesseren vollstaendigen 64-Byte-Record bei jedem schnellen Sample
waeren es bei 50 Hz nur etwa vier Minuten. Deshalb die Datenraten trennen.
Ereignisse/Dateisystem reduzieren die Kapazitaeten. Keine stillen Ringverluste, automatischen
Loeschungen oder heimlichen Ratenwechsel. Wenn der Speicher nicht reicht,
Rate vor dem Flug bewusst waehlen oder spaeter Speicher erweitern. Die
Steuerung weiter betreiben, wenn Logging wegen Platzmangel beendet werden muss.

Verifizierter RP2-v1.29-Quelltext: Flash-Erase/Program deaktivieren Interrupts
und XIP, ein genutzter zweiter Kern wird angehalten. PWM-Hardware kann dabei
den alten Puls weiter ausgeben; neue Knueppelwerte werden dadurch noch nicht
verarbeitet. Ein Dateizugriff kann mehrere solche Aktionen benoetigen.
Ein Python-Thread/zweiter Kern allein entkoppelt das nicht. Kleine RAM-Puffer
reduzieren Zugriffe, garantieren aber keine maximale Schreib-/Synczeit.
Auch eine SD-Karte waere ohne Messung keine Echtzeitgarantie.

Deshalb erst separate Flashmessung, dann gegebenenfalls einen gepufferten
Schreibpfad mit Gesamtlast am Boden pruefen. Mittelwert allein reicht nicht;
write, flush, sync, close und Dateisystempflege koennen blockieren. Ein
isoliertes Maximum unter 50 ms reicht bei zusaetzlicher Controllerlast nicht
automatisch aus. Deadlinegrenzen nicht zum Verstecken der Pausen aufweiten.

## Abgeschlossen: L1 CH3 vermessen

1. Alle Versorgungen trennen. **Alle vier Servos stromlos machen.** Fuer den
   Test nur den Empfaenger ueber den BEC versorgen; MCU ueber USB. GND gemeinsam,
   BEC-Plus nicht mit MCU-USB-5-V verbinden. Der RX braucht fuer Pulse Versorgung;
   "BEC aus" allein waere deshalb fuer diesen Kanaltest keine sinnvolle Anleitung.
2. CH3-Signal an **GP14**, nur mit 3V3-kompatiblem Signalpegel. GP ist GPIO-Nummer.
   Keine Plusleitung an GP14. Aktuelle config.py, diagnostics.py, receiver.py,
   logger_bench.py hochladen; calibration.json erhalten, AUTO_START=False,
   Soft-Reboot. Kein app/start_test/bench_test parallel starten.
3. In der Thonny-Shell:

   ```python
   import logger_bench
   logger_bench.run_channel()
   ```

4. Unten etwa drei Sekunden halten, oben drei Sekunden, Mitte kurz pruefen,
   wieder unten. **Die gedruckten Pulswerte unten und oben jeweils notieren**;
   das JSON-Min/Max allein verrät die physische Polung nicht.
   Im Sender-Kanalmonitor pruefen, dass CH3 keine Mischer auf Roll/Nick/Gier
   ausloest; der Aufnahmeknueppel darf keine Ruderkommandos veraendern.
5. Ctrl+C, Meldung `CH3-Test gespeichert` abwarten. logger_channel_*.json
   unter docs/testdaten/logger_boden/L1/ auf dem Mac sichern. Noch keine
   RC-Kalibrierdatei fuer die Steuerachsen aendern, keine Schwellen raten.

## Abgeschlossen: L2 Flash messen

1. Testprogramme stoppen. Fuer L2 **BEC/Empfaenger/Servos aus**, MCU per USB.
   Kein app/PWM aktiv, main-Autostart aus. Sensoren normal versorgen oder
   bei getrennten Quellen vollstaendig abstecken; keine aktiven Signale an
   unversorgten Modulen. config.py, diagnostics.py, logger_bench.py hochladen,
   Soft-Reboot; calibration.json erhalten.
2. In der Thonny-Shell:

   ```python
   import logger_bench
   logger_bench.run_storage()
   ```

3. Der Test erstellt **drei neue 64-KiB-Dateien**, mit 512/1024/4096-Byte-
   Bloecken. Er misst open/write/flush/os.sync/close sowie komplette
   write+flush+sync-Zyklen und liest den Inhalt zurueck. Keine alten Dateien
   werden geloescht/ersetzt. Bei zu wenig freiem Platz fuer 192 KiB plus
   128 KiB Reserve startet er nicht. Er hat einen begrenzten Testumfang,
   keinen Timer fuer den spaeteren Fluglogger.
4. Bis `Flash-Test beendet` warten; bei Ctrl+C wird ein Teilbericht versucht.
   logger_storage_*.json unter docs/testdaten/logger_boden/L2/ sichern.
   Relevant: verified fuer alle drei Dateien, freie Bytes, Maxima und Zahl
   der Zielperioden-/Deadlineueberschreitungen je Operation.
5. Die .bin-Dateien sind nur Testmuster, keine Flugdaten. Nach Berichtdownload
   gezielt nur diese Testmusterdateien bei gestopptem Programm entfernen,
   damit weitere Messungen nicht am Platz scheitern. Keine Kalibrierdateien
   oder Rohdaten anderer Versuche loeschen. Kein automatisches Loeschen im Test.

L2 erfasst keine Servos, UART-/I2C-Mehrlast und keine garantierte Worst-Case-
Grenze. Readback belegt den aktuell lesbaren Dateiinhalt, keine garantierte
Erhaltung bei Stromausfall. Bei schnellen Ergebnissen folgt ein Gesamtlastvergleich; bei langen
Pausen Speicher-/Datenpfad aendern, statt sofort Fluglogging freizuschalten.
Zunaechst ein Lauf; Wiederholungen/naeher voller Flash nur gezielt nach Befund.

## Jetzt konkret: L3 mit kleinen RAM-Bloecken wiederholen

**Abgeschlossen:** Die folgende Anleitung dokumentiert die erfolgreiche
Vorprobe 0.1.4. Nicht erneut ausfuehren; der aktuelle naechste Schritt ist
[F1 aus FLUGLOGGER_TEST.md](FLUGLOGGER_TEST.md).

Selteneres Flash-Schreiben wuerde die gemessenen Pausen nur seltener machen.
Ohne Flash-Schreiben waehrend der Steuerung entfaellt dieser Stoerpfad ganz.
Bei 1 Hz sind GPS/Flugweg und langsame Hoehen-/Lageaenderungen sichtbar;
schnelle Ruderreaktionen oder Schwingungen sind damit nur eingeschraenkt
auswertbar. Dies ersetzt keinen hochaufloesenden Gain-Test.

Fuer einen noch zu definierenden Gesamtdatensatz budgetieren wir 144 Bytes.
600 Samples plus 32 Ereignisrecords benoetigen 91008 Bytes. Zehn Minuten
sind hier ein Dimensionierungsziel, kein Timer. Die spaetere App soll den
verfuegbaren Puffer mit Reserve ausnutzen und bei Fuellung nur Aufnahme beenden,
nicht MANUAL. Kein automatisches Ueberschreiben und kein Flash bei CH3-aus im Flug.

1. **BEC/Empfaenger/Servos aus, MCU per USB.** Kein anderes Testprogramm laeuft,
   AUTO_START=False. Alle Pythondateien aus firmware/ konsistent auf den MCU
   laden, einschliesslich der neuen ram_buffer.py; vorhandene calibration.json
   erhalten, keine JSON-Datei ersetzen. IMU/Sensoren normal mitversorgen oder
   bei abgeschalteten Quellen vollstaendig trennen, nicht VCC allein abstecken.
   Soft-Reboot, danach nur logger_bench importieren, nicht vorab app/sensor_test
   starten/importieren. Die Imports brauchen app und seine Abhaengigkeiten, fuehren
   aber keine run()-Funktion oder Hardwareinitialisierung aus.
2. In Thonny:

   ```python
   import logger_bench
   logger_bench.run_ram()
   ```

3. Im Bericht test_version **0.1.4** pruefen. Die Probe reserviert **zuerst**
   91008 Nutzbytes als **40 Bloecke** (39 * 2304 B plus 1152 B), importiert danach
   denselben Modulumfang wie 0.1.3 und haelt die Bloecke dabei. Sie prueft jeden
   Recordanfang/-schluss und nach Imports/Inhaltsprobe/GC die **65536 B Reserve**
   einschliesslich Blockoverhead. Auch der Compilerbedarf muss passen.
   Danach Pufferfreigabe, dann JSON. Kein Flug/Servo/Receiver/Sensor wird gestartet.
   Der Lauf braucht keine zehn Minuten; 600 s dienen nur zur Pufferdimensionierung.
   Erfolgreiche Bloecke/Bytes zaehlen; bei MemoryError den freien Heap vor
   Teilpufferfreigabe und die Fehlermeldung erfassen. Heapzusammenfassung vor
   Puffer/bei Blockfehler sowie gegebenenfalls Traceback erscheinen in der Konsole.
4. Neuen logger_ram_*.json **und die komplette zugehoerige Konsolenausgabe** nach
   docs/testdaten/logger_boden/**L3_frueh/** sichern. Alle drei alten Berichte
   erhalten. Relevant: status, allocation_ok, content_verified,
   free_before_bytes, free_after_allocation_bytes, requested_bytes, reserve_bytes,
   storage_strategy, block_count und max_block_bytes. Erwartet: fits_preliminary,
   allocation_ok=true, content_verified=true, runtime_modules_imported=true,
   allocation_order=buffer_before_runtime_imports, runtime_modules_preloaded=[],
   mindestens 65536 B nach Imports/Inhaltsprobe, 91008 Nutzbytes/40 tatsaechlich
   angelegte Bloecke/maximal 2304 B pro Block. free_before_bytes liegt jetzt
   VOR den grossen Imports und ist nicht direkt mit 0.1.3 vergleichbar.
   Auch bei erneutem Fehler sichern: allocated_blocks, allocated_payload_bytes,
   last_block_request_bytes, allocator_failed, free_at_allocator_failure_bytes,
   failure_location und error grenzen die Ursache ein. block_count=40 bezeichnet
   nur das Ziel, nicht erfolgreich angelegte Bloecke. Ein Fehlerbericht ist hier
   ein verwertbares Diagnoseergebnis, keine Aufforderung zum unveraenderten Wiederholen.
   fits_preliminary bedeutet nur, dass diese Vorprobe passt;
   echte Controllerobjekte und ein tatsaechlicher Encoder fehlen noch.
5. Bei insufficient_ram, insufficient_reserve, allocation_failed,
   runtime_import_failed oder anderem
   Fehlerstatus nicht die Reserve
   blind verkleinern. Datei zur Auswertung sichern; dann Paket/Rate/Codebedarf
   gezielt beurteilen. L1/L2 dafuer nicht erneut starten. Bei Erfolg folgt die
   echte Loggerintegration und ein Bodenvergleich mit allen realen Objekten;
   die neuen Blockobjekte muessen auch dort in die Reserve passen.

Stromverlust/Reset vor dem spaeteren Export verliert RAM-Daten. Der finale
Programmstop muss nach Landung bewusst bedient werden, die Versorgung bis
zum Abschluss bleiben. Einen normalen CH3-Wechsel oder Receiververlust nie
als Befehl zum Abschalten der Steuerung/Exportieren interpretieren. Ein
zugaenglicher Bodentaster bzw. eine gepruefte Bordbedienung ist noch zu planen;
RESET eignet sich nicht zum Speichern. Der BOOT-Taster ist eine moegliche,
noch ungepruefte Option; auch dessen Abfrage hat laut RP2-Doku einen kurzen
kritischen Flashabschnitt und muss im Gesamtablauf bewertet werden.

## Flugnotiz und weitere sinnvolle Punkte

Pro Flug Datum/UTC, Code/Setup, Wind, Schwerpunkt/Zuladung, Akku, Startart und
Segmente notieren. Manoever mit ungefaehrer Zeit seit Aufnahmebeginn nennen
(z.B. "00:20 kurzer Rechtsimpuls, 00:35 Geradeaus"). Dieselben Achsenzeichen
wie im Log benutzen. Keine gleichzeitigen Gain-/Montage-/Verkabelungsaenderungen
im Vergleich. Ein MANUAL-Basisflug zuerst, spaeter gezielte Regeltests.

Vor Bordbetrieb weiterhin Start-/Logabschluss ohne Mac und finalen Strompfad
testen. Akku- oder 5-V-Spannung wird mit der jetzigen Verdrahtung nicht gemessen;
ein Log kann kurze Versorgungseinbrueche nicht ausschliessen. Resetgrund und
unsauberes Logende helfen bei der Diagnose, beweisen aber nicht deren Ursache.
Ein Spannungsteiler/Spannungssensor waere eine spaetere Hardwareergaenzung,
kein bereits vorhandener Messkanal.

## Primaerquellen

- [Beitian BN-180](https://www.beitian.com/sys-pd/9.html): TX-/PPS-LED und 1-Hz-Default.
- [Waveshare RP2040-Zero](https://www.waveshare.com/rp2040-zero.htm),
  [Schaltplan](https://files.waveshare.com/upload/4/4c/RP2040_Zero.pdf): vorhandene RGB-LED, GP16.
- [MicroPython RP2 Flash v1.29.0](https://github.com/micropython/micropython/blob/v1.29.0/ports/rp2/rp2_flash.c): kritische Flashabschnitte, Erase/Program, Core-Lockout.
- [RP2040 SDK Hardware APIs](https://www.raspberrypi.com/documentation/pico-sdk/hardware.html): XIP und Flash-Zugriffsbedingungen.
- [MicroPython os v1.29.0](https://docs.micropython.org/en/v1.29.0/library/os.html): statvfs und sync.
- [MicroPython rp2 v1.29.0](https://docs.micropython.org/en/v1.29.0/library/rp2.html): BOOTSEL-Abfrage, jetzt im expliziten Loggerprototyp, Hardwarecheck offen.
