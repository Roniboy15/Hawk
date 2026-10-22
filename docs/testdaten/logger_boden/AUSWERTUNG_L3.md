# L3: RAM-Vorprobe, ausgewertet am 2026-10-21

**L3 0.1.4 hat bestanden:** 40 Bloecke/91008 B vollstaendig angelegt und
geprueft, nach denselben Modulimports noch 68656 B frei. Die geaenderte
Allokationsreihenfolge funktioniert in diesem Lauf. Die RAM-Vorprobe ist damit
abgeschlossen; weitere Messung im echten kombinierten Logger, kein neuer L3.
Die vorherigen Fehler bleiben unten als Entwicklungsevidenz erhalten.

## Verifizierter Befund des Besitzerlaufs

[Unveraenderter Rohbericht](L3/logger_ram_357044_0.json): Bench 0.1.1,
Schema 1, MicroPython v1.29.0, Waveshare RP2040-Zero.

| Feld | Ergebnis |
| --- | --- |
| status / allocation_ok | allocation_failed / false |
| Freies RAM vor Allokation | 164880 B |
| Ziel | 632 Records zu budgetierten 144 B = 91008 B |
| Zusaetzliche Reserve | 65536 B |
| Rechnerischer Rest vor Objekt-/Listenoverhead | 8336 B |
| Freies RAM nach Freigabe/GC | 164688 B |
| estimated_capacity_samples | 689, nur rechnerischer Wert aus Gesamtfreiraum |
| Echte Controllerobjekte / finaler Recordencoder | beide noch nicht vorhanden |
| flight_timing_qualified | false |

Der Code 0.1.1 ordnet MemoryError beim Anlegen des einzelnen bytearray diesem
Status zu. Es entstand kein Fluglog. Die Zahl 689 ist **keine** erfolgreich
reservierte Kapazitaet. Der Bericht enthaelt weder eine Messung des groessten
freien Bereichs noch eine Heapkarte; die Differenz von 192 B nach dem Lauf
belegt fuer sich allein kein Speicherleck.

## Einordnung und gezielte Aenderung

gc.mem_free() beschreibt den gesamten freien Heap, nicht die Groesse eines
einzelnen nutzbaren Bereichs. Ein fragmentierter oder auf mehrere Bereiche
verteilter Heap ist mit dem Ergebnis vereinbar; die genaue Ursache ist noch
nicht nachgewiesen. gc.collect() gibt unerreichbare Objekte frei und garantiert
keinen zusammenhaengenden 91-kB-Bereich. Grundlagen:
[MicroPython gc v1.29](https://docs.micropython.org/en/v1.29.0/library/gc.html),
[Speicherverwaltung](https://docs.micropython.org/en/v1.29.0/develop/memorymgt.html),
[Allocator-Quellcode](https://github.com/micropython/micropython/blob/v1.29.0/py/gc.c).

Bench **0.1.2** nutzt ram_buffer.RecordBuffer:

- 16 Records pro vollem Block: 39 * 2304 B plus 1152 B fuer die letzten acht.
  Gesamt weiter 91008 B, kein stilles Reduzieren von Kapazitaet oder Datenrate.
- Jeder Record liegt vollstaendig in einem Block. slot(index) liefert Block und
  Byteoffset fuer spaeteres pack_into, ohne die gesamte Aufnahme zu kopieren.
  Ungueltige Indizes werden abgewiesen; kein Ring/Ueberschreiben.
- Alle Bloecke werden vorab angelegt. Teilallokationen/Abbruch werden freigegeben;
  der JSON-Export erfolgt erst nach Pufferfreigabe. Keine Hardwareinitialisierung.
- Unterschiedliche Marker an Anfang/Ende jedes Records werden geschrieben und
  danach kontrolliert. Erst nach GC der temporaeren Pruefobjekte wird die echte
  freie Reserve gemessen. Objekt-/Listenoverhead ist damit eingeschlossen.

Neu protokolliert: storage_strategy=record_aligned_blocks, block_count=40,
max_block_bytes=2304, content_verified und gegebenenfalls failure_phase.
fits_preliminary verlangt erfolgreiche Allokation/Inhaltsprobe und mindestens
65536 B verbleibende Reserve. Auch kleinere Bloecke koennen noch scheitern;
die Zusatzobjekte brauchen ebenfalls Platz. Die neue Variante ist hostgeprueft,
der Besitzerlauf mit dieser Variante ist im folgenden Nachtrag ausgewertet.

## Nachtrag: Blocklayout 0.1.2 ebenfalls gescheitert

[Unveraenderter zweiter Rohbericht](L3_bloecke/logger_ram_1246428_0.json), vom
Besitzer aus Downloads bereitgestellt und bytegleich ins Repository kopiert:

| Feld | Ergebnis |
| --- | --- |
| test_version / status | 0.1.2 / allocation_failed |
| failure_phase | allocate, vor Inhaltspruefung |
| Freies RAM vor dem Versuch | 162608 B |
| Geplante Nutzbytes / Reserve | 91008 B / 65536 B, unveraendert |
| Rechnerischer Rest vor Zusatzobjekten | 6064 B |
| storage_strategy | record_aligned_blocks |
| Geplant: block_count / max_block_bytes | 40 / 2304 B |
| allocation_ok / content_verified | beide false |
| Freies RAM nach Freigabe/GC | 162400 B |

**40 ist die geplante Blockanzahl, keine bestaetigte Allokation.** Version 0.1.2
speichert weder die Anzahl bereits erfolgreicher Bloecke noch die genaue
MemoryError-Meldung. Daher wissen wir nicht, ob der Fehler beim ersten Block,
spaeter oder schon bei der Pufferverwaltung auftrat. Es ist insbesondere nicht
belegt, dass der Heap keinen einzigen 2304-B-Bereich hatte. Die neue Version
ist im Bericht erkennbar; saemtliche Boarddateien sind damit nicht unabhaengig
identifiziert. Kein Nachweis eines defekten Sensors oder MCU aus diesem Befund.

### Was 0.1.3 anders misst

- allocated_blocks und allocated_payload_bytes sind echte Erfolgszaehler;
  block_count bleibt das Ziel. last_block_request_bytes ist die letzte Anforderung.
- Bei Fehler im bytearray-Aufruf wird free_at_allocator_failure_bytes **vor**
  Freigabe der bisherigen Bloecke erfasst. allocator_failed unterscheidet diesen
  Fall von einem Fehler ausserhalb des Block-Allokators.
- error und failure_location erhalten die Fehlermeldung und den Kontext;
  MicroPython druckt zusaetzlich den Traceback mit Quellzeilen in die Konsole.
- micropython.mem_info() druckt vor dem Puffer und bei einem Blockfehler die
  Heapzusammenfassung. Diese Konsolenausgabe mit sichern; sie ist nicht im JSON.
  Die Ausgabe/Einheiten sind implementierungsabhaengig, nicht jeden Wert als
  Bytes interpretieren. Sie zeigt auf RP2 auch den groessten freien Bereich.

Die Zusatzdiagnose braucht selbst RAM; der gemessene Ausgangswert kann deshalb
von 0.1.2 abweichen. Ein fehlgeschlagener Diagnoselauf ist trotzdem verwertbar.
Nutzdatenziel, Blockgroesse und Reserve bleiben gleich; kein automatischer
Versuch mit kleinerem Puffer, keine Absenkung der Qualitaetsanforderungen.
Grundlagen: [mem_info-Dokumentation](https://docs.micropython.org/en/v1.29.0/library/micropython.html#micropython.mem_info),
[gc_dump_info-Implementierung](https://github.com/micropython/micropython/blob/v1.29.0/py/gc.c).

## Diagnoseergebnis 0.1.3: Fehler am 36. Block

[Unveraenderter dritter Rohbericht](L3_diagnose/logger_ram_2167178_0.json),
vom Besitzer bereitgestellt und bytegleich archiviert:

| Feld | Ergebnis |
| --- | --- |
| Version / Status | 0.1.3 / allocation_failed |
| allocated_blocks / allocated_payload_bytes | 35 / 80640 B |
| Letzte Anforderung | 2304 B, der 36. Block |
| error | memory allocation failed, allocating 2304 bytes |
| allocator_failed / failure_location | true / block_allocator |
| Freies RAM vor Versuch / beim Fehler | 161440 B / 79552 B |
| Fehlende Nutzbytes bis zum Ziel | 10368 B |
| Freies RAM nach Freigabe/GC | 161136 B |
| allocation_ok / content_verified | beide false |

Der Fehler liegt jetzt nachweisbar beim Block-Allokator, nicht nur unbestimmt
in der Pufferverwaltung. 161440 - 79552 - 80640 = 1248 B sonstige Netto-Belegung
bis zum Fehler; das ist kein separat vermessener Objektbedarf. Die Zieldaten
wurden nicht vollstaendig angelegt oder geprueft. Nach Freigabe fehlen 304 B
gegenueber vorher; daraus allein kein Speicherleck ableiten.

Die Kombination aus grossem Gesamtfreiraum und gescheiterter 2304-B-Allokation
ist ein starker Hinweis auf Fragmentierung. Eine Heapkarte/groesste freie
Blocklaenge ist in diesem JSON nicht enthalten; die angekuendigte Konsole
wurde hier nicht mitgeliefert. Die genaue Verteilung bleibt daher unbekannt.
Aus den 35 erfolgreichen Bloecken keine niedrigere garantierte Flugdauer
ableiten und nicht still auf 560 Records verkuerzen.

## Gezielte Aenderung in 0.1.4

Grosse dauerhaft benoetigte Puffer frueh anlegen ist eine von MicroPython
beschriebene Massnahme gegen Fragmentierung. Umgekehrt brauchen spaetere
Quellcodeimports temporaeren Compiler-RAM. Beides muss gemeinsam passen:
[MicroPython v1.29: RAM und Fragmentierung](https://docs.micropython.org/en/v1.29.0/reference/constrained.html#fragmentation).

Der neue Ablauf reserviert zuerst alle 40 Recordbloecke, haelt sie referenziert,
importiert dann **dieselben** Module app/gps/ms5611/sensor_test/recording und
prueft anschliessend Recordinhalt und mindestens 65536 B freie Reserve nach GC.
AUTO_START/START_MODE, Pins, Gains und Steuerung bleiben unveraendert.

allocation_order=buffer_before_runtime_imports identifiziert den neuen Ablauf.
runtime_modules_imported=true bestaetigt die abgeschlossene Importphase;
runtime_modules_preloaded zeigt bereits vorher geladene Testmodule. Vorher
Soft-Reboot, nur logger_bench importieren. free_before_bytes und
estimated_capacity_samples beziehen sich ab jetzt auf den Stand **vor** den
grossen Imports; keine Kapazitaetszusage daraus ableiten. Entscheidend bleibt
free_after_allocation_bytes nach Imports/Inhaltsprobe. Ein Compiler-/Importfehler
ergibt runtime_import_failed; auch dann wird der ganze Puffer vor JSON freigegeben.
Kein Entfernen von Modulen, kein kleinerer Datensatz, keine verringerte Reserve.

## Vierter Lauf: 0.1.4 bestanden

[Unveraenderter Rohbericht](L3_frueh/logger_ram_36572_0.json), bytegleich archiviert:

| Feld | Ergebnis |
| --- | --- |
| Version / Status | 0.1.4 / fits_preliminary |
| allocated_blocks / allocated_payload_bytes | 40 / 91008 B |
| allocation_ok / content_verified | beide true |
| allocation_order | buffer_before_runtime_imports |
| runtime_modules_preloaded / runtime_modules_imported | [] / true |
| Freies RAM vor grossen Imports | 206944 B |
| Freies RAM mit Puffer nach Imports/Inhaltsprobe/GC | 68656 B |
| Verlangte Reserve / zusaetzlicher Spielraum | 65536 B / 3120 B |
| Freies RAM nach Pufferfreigabe | 160560 B |
| error / allocator_failed | null / false |

Die gesamte Nutzdatenmenge und Reserve wurden im vorgesehenen Ablauf bestaetigt.
Die Differenz zwischen Start- und Endfreiraum ist kein Lecknachweis: nach dem
Lauf sind die erst spaeter importierten Module weiterhin geladen. Auch die
rechnerischen 982 Samples im Bericht sind kein neuer Kapazitaetsnachweis;
dieser Wert stammt vor grossen Imports. 632 Records wurden tatsaechlich geprueft.

Der Erfolg stuetzt die Fragmentierungsdiagnose und die fruehe Allokation als
wirksame Massnahme. Ein Lauf beweist keine allgemeine RAM-/Timinggarantie.
Der Bericht markiert korrekt: echter Encoder/Controllerobjekte fehlen,
flight_timing_qualified=false. 3120 B sind der Spielraum **ueber** der
64-KiB-Reserve, nicht das gesamte verbleibende RAM.

## Naechster Schritt

Besitzer bestaetigt danach 1 Hz fuer erste MANUAL-Basisfluege und einen
zugaenglichen BOOT-Taster. Ein neuer expliziter Loggerprototyp ist implementiert,
noch nicht auf dem MCU gemeinsam geprueft. Er nutzt denselben 144-B-/632-Record-
Puffer, prueft vor PWM echte Objekte/Reserve und exportiert erst nach Hardwarestop.
**Jetzt F1 SENSOR mit CH3/LED/BOOT/Export** aus
[FLUGLOGGER_TEST.md](../../FLUGLOGGER_TEST.md), danach F2 MANUAL. Keine pauschale
Wiederholung von L1/L2/L3, keine Autostart-Aktivierung und kein Flugtimer.

Hoststand vor Loggerintegration: **161 Tests bestanden** (96 Steuerung, 35 Sensoren, 30 Logger/Puffer).
Neue Abdeckung umfasst einen simulierten Heap ohne Allokationen >4096 B,
vollstaendige Records ueber alle Blockgrenzen, exakte letzte Blockgroesse,
Indexgrenzen, Freigabe bei MemoryError/Ctrl+C vor Export, Inhaltsfehler und
unveraendert strikte RAM-Reserve. Zwei weitere Regressionen pruefen
Fehlerdiagnose vor Teilpufferfreigabe und die Unterscheidung zwischen
Block-Allokator und Fehlern ausserhalb davon. Hosttests beweisen keine MCU-Heapgroesse.
Weitere drei Regressionen pruefen: Reservierung vor Imports mit strikter Reserve
nachher, Freigabe aller Bloecke bei Compiler-/Importfehler/Ctrl+C und den echten
run_ram-Einstieg mit derselben Reihenfolge. Keine Hardwareinitialisierung im Test.
Neuer kombinierter Loggerprototyp: 183 Hosttests bestanden; Details in
[VALIDIERUNG.md](../../VALIDIERUNG.md). Der physische F1-Lauf ist offen.

SHA-256 des Originals:
`133e17709bb0ff2a6bd73799ed5f8c204408b0bae96ae1c4bd19c1f9dc1a5575`.
SHA-256 des Blocklayout-Berichts:
`ac0c46a86e5e0384868d53ab2a015250e0d3d834bf8b8c0977dc52e4ac0d5761`.
SHA-256 des Diagnoseberichts:
`3e685ac739b8fdcbab252d50b1053959fadd11d58d0454710ca9bc774c3019b1`.
SHA-256 des erfolgreichen fruehen Laufs:
`0f236ab18aac5d6460b42eb1402997906dc58a7b68612b50b817c2e7a50ee801`.
Kein Hardwarezugriff durch den Agenten.
