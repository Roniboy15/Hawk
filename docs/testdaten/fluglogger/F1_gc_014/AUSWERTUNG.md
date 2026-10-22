# F1 / Logger 0.1.4: GPS-Speicherfehler

Unveraenderte Rohberichte: flight_68106_0.json und flight_62671_0.json/CSV.
Im ersten Lauf war der Sender laut Besitzer nicht verbunden. Das erklaert
fehlende CH3-Aufnahme, aber nicht den in beiden Laeufen gleichen GPS-MemoryError.

Der letzte Lauf dauert 18.570 s: ein Segment, zwei Samples, vier CSV-Zeilen,
sauberer Ctrl+C-Stop, keine PWM und keine Timing-Trips (Periode max. 43.219 ms).
GC arbeitet: 27 geplante Bereinigungen, max. 24.502 ms, automatische GC aktiv.
GPS stoppt nach 85 Bytes/zwei Saetzen mit `MemoryError ... allocating 640 bytes`.
Die kurze Laufzeit mit frueh abgeschaltetem GPS qualifiziert die Loopzeiten nicht.
Rot ohne Fix ist normal; Orange meldet hier den GPS-Komponentenfehler.

## Reproduktion und kleine Korrektur

Separater Hostversuch mit offiziellem MicroPython v1.29.0, Unix/arm64, 256-KiB-Heap;
keine Hardware. `reproduce_heap.py` legt gezielt einen fragmentierten Heap an.
`gps_before` ist die vor dieser Korrektur gesicherte gps.py, `gps_after` die neue.
Die beiden temporaeren Module muessen fuer den Hostinterpreter importierbar sein.
Aufruf: `micropython -X heapsize=256K reproduce_heap.py gps_before 507`, danach
entsprechend `gps_after 507`. Die Fuellzahl ist an diesen Interpreter angepasst;
kein portabler Boardtest. Vollstaendige Ausgaben: [reproduction.txt](reproduction.txt).

- Vorher: 131712 B frei, Fehler exakt 640 in checked_fields/Pruefsummen-Generator.
- Nachher: 132704 B frei, gleicher Satz korrekt geprueft, keine neuen QSTR-Eintraege.
- Zusatzversuch ohne Fragmentierung, gleicher ASCII-Satz: vorher 74 neue
  internierte Strings, nachher null.

MicroPython interniert bei Textiteration einzelne Zeichen. Ein voller QSTR-Pool
muss als groesserer zusammenhaengender Block wachsen. Der Fehlertext nennt hier
irrefuehrend die 640 Pool-Eintraege statt der tatsaechlichen Allokationsgroesse.
Quellen: [Stringiterator](https://github.com/micropython/micropython/blob/v1.29.0/py/objstrunicode.c),
[QSTR-Pool und m_malloc_fail(new_alloc)](https://github.com/micropython/micropython/blob/v1.29.0/py/qstr.c).
Das reproduzierte Verhalten erklaert den Boardbefund sehr gut; dessen genaue
Fehlerzeile wurde im Boardbericht nicht gespeichert.

Logger 0.1.5 ersetzt ausschliesslich die Textiteration der Pruefsummen-/ASCII-
Pruefung durch Byteiteration, mit Codekommentar; config traegt die neue Kennung.
Keine neue GC-Strategie, keine niedrigere Kapazitaet oder hoehere Deadline.
193 CPython-Tests bestehen, einschliesslich strenger ASCII-/Hex-Faelle.
Naechster Boardnachweis: gps.py/config.py ersetzen, SENSOR ca. 60 s mit einem
Segment und stromlosen Servos. Kein Orange/GPS-Fehler, weiterlaufende GPS-Zaehler
und normale Zeitpruefung; anschliessend Bericht auswerten. Kein neuer L3.
