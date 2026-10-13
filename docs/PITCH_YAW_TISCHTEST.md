# Nick und Gier — naechste beaufsichtigte Tischtests

Stand v0.2.2-bench. Grundlegender Roll-Funktionstest vom Besitzer bestanden;
Rollzeichen -1/-1 und rate_p=2 unveraendert. Elektrische/Timing-/Flugqualifikation
ist separat offen. Wir bleiben fuer diesen Ausbau auf dem bisherigen Branch.

Der Besitzer bestaetigt: Hoehen-/Seitenrudersignale gehen bisher DIREKT zum
Receiver. Receiverbetrieb prueft noch keinen dieser MCU-Ausgaenge. Zuerst
[VERSORGUNG_WARNHINWEISE.md](VERSORGUNG_WARNHINWEISE.md) beachten: BEC 5 V @ 3 A,
vier Servos, ungeklärte Netzunterbrechung. Die Software ist fuer den SENSOR-Schritt
vorbereitet, erzeugt dort keine PWM und autorisiert keine ungepruefte Versorgung.

## Koerperkonvention ohne Umbau des Filters

X vorwaerts, Y links, Z oben; rechtshaendig. Vorzeichen sind explizit:

| Positive Groesse | Bedeutung | Beobachtung/Befehl mit negativem Wert |
| --- | --- | --- |
| Rollwinkel / gx | Rechtsbank / Rechtsrollrate | Linksbank |
| Nickwinkel / gy | Nase runter / Nickrate nach unten | Nase hoch |
| Gierwinkel / gz | Nase links / Drehrate nach links | Nase rechts |

Dass Nase-anheben die Nickanzeige senkt, ist korrekt fuer diese Konvention.
Die fruehere positive-Nick=Nase-hoch-Anweisung ist damit ersetzt. Kein einzelnes
Gyrozeichen und keine Sensorachse nur fuer eine intuitivere Anzeige invertieren.
Level-JSON Schema 1 und die Quaternionmathematik bleiben unveraendert.
Gyro wird bei jedem Start nullpunktkalibriert; die geometrische Levelreferenz
nicht bei jedem Start neu speichern. Bei unveraenderter Montage weiterverwenden.

## A. Nick: Signalpfad bei ausgeschalteter Versorgung umstellen

1. MCU/USB und BEC/Batterie trennen. Die bestehende Rollverkabelung beibehalten.
2. Receiver CH2-Signal auf GP8 (MCU-Eingang), Servosignal Hoehenruder auf GP6
   (MCU-Ausgang). Den bisherigen direkten CH2-zu-Servo-Signalpfad entfernen.
3. Servo-Plus bleibt am passenden BEC, Masse gemeinsam. RX-Pegel vor GPIO-Anschluss
   auf 3,3-V-Kompatibilitaet pruefen; Versorgungsspannung beweist den Signalpegel nicht.
4. Alle zusammengehoerigen v0.2.2-Firmwaremodule hochladen, vorhandene MCU-Kalibrierung
   nicht ueberschreiben. Stop/Soft-Reboot wegen gecachter Imports.

Die vorbereitete Konfiguration ist:

```python
AUTO_START = False
START_MODE = 'sensor'
ACTIVE_AXES = ('roll', 'pitch')
DIRECTION_CHECKED_AXES = ('roll',)
```

## B. Nick: SENSOR und neue RC-Kalibrierung

Erster Sensorcheck auch nur mit MCU/IMU am USB moeglich: Servo-/BEC-Batterie
getrennt lassen, Mac aus Akku ohne Netzladegeraet. Dann sind fehlende RX-Werte
erwartbar und es gibt keine Servo-Batterielast. Fuer den spaeteren RX-/MANUAL-Test
erst den geprueften Niedervoltaufbau und passende BEC-Stromreserve herstellen.

start_test.py: ca. sechs Sekunden unbewegt. Nose-up muss pitch_down absenken,
nose-down erhoehen. Roll weiterhin wie vorher. gyro=(gx,gy,gz) nutzt Grad/s und
die gleichen Koerperzeichen. CH2 muss als rx['pitch'] erscheinen; Knueppel
bewegen und kleinere/groessere Pulse notieren. Keine Servo-PWM im SENSOR-Modus.
Das gilt fuer MCU-Ausgaenge; ein noch direkt am Receiver angeschlossenes Ruder
kann weiterhin Pulse bekommen. SENSOR schaltet die Servostromversorgung nicht ab.

Nach Stop nur den neuen Kanal kalibrieren, ohne Roll/Level neu zu erfassen:

```python
import calibrate_rc
calibrate_rc.run(('pitch',))
```

Dies ist ein bewusster MCU-Kalibrieraufruf fuer den Besitzer, kein Hostbefehl.
Neue calibration.json sichern. Ein normaler Start von calibrate_rc.py erfasst
weiterhin alle aktiven Kanaele; die Auswahl oben bewahrt den bestaetigten Rollstand.

## C. Nick: MANUAL-Zeichen festlegen

START_MODE='manual', Soft-Reboot. Alle aktiven RC-Kanaele brauchen gueltige
Neutralframes; fehlt CH2, werden beide Achsen nicht freigegeben. Mit kleinen
Kommandos am Hoehenruder pruefen, Rollgrenzen/Gains nicht veraendern.

RECEIVER['pitch']['sign'] so setzen, dass Nase-hoch-Knueppel einen NEGATIVEN
Nick-Sollwert ausgibt: bei steigendem RX-Puls -1, bei fallendem RX-Puls +1.
SERVOS['pitch']['sign'] so setzen, dass positives internes Kommando physisch
Nase-runter-Wirkung liefert: groesserer Puls bewirkt Nase runter => +1;
groesserer Puls bewirkt Nase hoch => -1. Defaultwerte sind keine Hardwarebestaetigung.

Nach jeder Konfigurationsaenderung Stop/Soft-Reboot. Pull-up und push-down muessen
physisch stimmen, Sollwerte muessen zur Koerperkonvention passen. MANUAL reagiert
auf den Knueppel, nicht auf das Anheben der Nase. rate_i=0 beibehalten, Limit=150 us.

## D. Nick: erst danach STABILIZE

Nach bestandenen SENSOR- und MANUAL-Zeichenchecks:

```python
DIRECTION_CHECKED_AXES = ('roll', 'pitch')
START_MODE = 'stabilize'
```

Die App blockiert STABILIZE fuer eine aktive, nicht bestaetigte Achse schon
vor Hardwareinitialisierung. Die Bestaetigung ist eine Bedienerangabe, kein
automatischer Verdrahtungsnachweis. Nach Neutralfreigabe kleine langsame Neigungen:
Bei geaenderten Pins, Sender-/Servozeichen oder Sensoranordnung Bestaetigung
fuer die betroffene Achse zuruecknehmen und Richtungspruefung wiederholen.
Nase hoch => Nase-runter-Korrektur; Nase runter => Nase-hoch-Korrektur.
Erst einzelne Achsen, dann kleine kombinierte Roll-/Nickbewegungen. Der kleine
Weg ist bei niedrigen Boden-Gains erwartbar; keine Gain-Erhoehung zum Erzwingen
voller Manual-Wege. Bei falscher Richtung, Zittern, Brummen oder Fehler stoppen.

## E. Gier erst nach bestandenem Nick-Test

Wieder Versorgung trennen. CH4-Signal auf GP9, Seitenrudersignal auf GP7;
direkten Receiver-zu-Servo-Signalpfad entfernen. Versorgung/Signalpegel wie oben.

```python
START_MODE = 'sensor'
ACTIVE_AXES = ('roll', 'pitch', 'yaw')
DIRECTION_CHECKED_AXES = ('roll', 'pitch')
```

Nase nach links drehen => gz positiv, nach rechts => gz negativ. Absolute
Gieranzeige ist relativ zum Start und driftet; sie ist keine Kursreferenz.
Dann stoppen und calibrate_rc.run(('yaw',)) fuer den neuen Kanal ausfuehren.

In MANUAL muss Rechtsruder einen NEGATIVEN Koerper-Giersollwert bedeuten:
RECEIVER.yaw.sign=-1 bei steigendem RX-Puls nach rechts, sonst +1.
SERVOS.yaw.sign=+1 wenn groesserer Servopuls Nase-links-Wirkung gibt, sonst -1.
Rechts/Links physisch und numerisch pruefen, rate_i=0 und Limit=150 us beibehalten.

Erst danach DIRECTION_CHECKED_AXES=('roll','pitch','yaw') und STABILIZE.
Neutraler Gierknueppel: Drehen nach links => Rechtskorrektur, nach rechts =>
Linkskorrektur. Drehung stoppen und neue Richtung festhalten: Ausgang geht
zur Trimlage, keine Rueckkehr zur alten Richtung. Ein Gierknueppelbefehl fordert
Drehrate, keinen Winkel. Das ist Tisch-Gierdaempfung; koordinierter Kurvenflug
und Flugabstimmung bleiben spaetere Aufgaben.

## Ergebnis je Stufe

Version/MCU-Runtime, Pinpfad, RX-/Servozeichen, Kalibrierung und Versorgung
notieren. SENSOR, MANUAL, STABILIZE je Achse getrennt PASS/FAIL protokollieren.
Vorzeitige Freigabe, neue Resets, USB-Ausfall oder Netzereignis abbrechen und
beurteilen. Keine aktive Umverdrahtung oder absichtliche Wiederholung eines Netzfehlers.
Ctrl+C, PWM/PIO-Abschaltung, Logexport abwarten; danach Versorgung trennen.
v0.2.2 CSV hat zusaetzlich Gyroachsen und Gier-Sollrate; Header beim Auswerten nutzen.
