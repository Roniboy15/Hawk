# R3: 20-Hz-Logger mit GPS und Bordstart bestanden, IMU-Messbereich erreicht

Auswertung am2026-10-25 von flight_285838_0.json, flight_285838_0.csv und
flight_285838_0_response.csv. Besitzer berichtet: alles verlief wie geplant,
Hawk wurde oft kraeftig bewegt, um Verhalten bei mechanischer Beanspruchung
zu beobachten. Zur konkreten Bewegung beim ersten IMU-Ereignis erinnert er
sich nicht sicher. Tatsachliche Kraefte, Einbauzustand und Versorgungsspannungen
wurden dabei nicht unabhaengig gemessen.

## Direkt belegt

| Merkmal | Befund |
| --- | --- |
| Firmware / Einstieg | Logger0.2.0, response20, schema2, boot_button, MANUAL |
| Gesamtdauer | 250.492 s |
| Aufnahme | zwei Segmente, zusammen89.978 s |
| Schneller Datenstrom | 1800 Zeilen, Sequenz0..1799 vollstaendig |
| Voller Datenstrom | 93 Zeilen, davon88 periodische Samples und5 Ereignisse |
| Datenrate | 19.996 Hz, mittlerer Abstand50.009455 ms |
| Einzelabstaende | 13..92 ms, missed_samples=0 nachgerechnet |
| Steuerung | ab560 ms MANUAL, danach keine erneute RX-Sperre/Neutralfreigabe |
| Timing | keine Trips; Loop maximal46.053 ms, Arbeit45.157 ms |
| Abschluss | FULL, danach8.375 s Lauf, sauberer ground_button-Stop/Export |
| GPS | alle93 vollen Zeilen Fix und Ready,6..12 Satelliten, HDOP0.93..1.69 |
| GPS-Datenalter | GGA/RMC maximal1072 ms, keine Parse-/Checksum-/Pollgapfehler |
| Start-RAM | 66624 B frei,1088 B ueber der verlangten65536-B-Reserve |

Die beiden CSVs haben46 bzw.17 Spalten, streng steigende Zeitstempel und
lueckenlose Sequenzen. Zahlen/Segmente/Formate stimmen mit JSON ueberein.
Alle schnellen Zeilen liegen innerhalb der zugehoerigen CH3-Aufnahmefenster.
Kein Ueberschreiben, kein Loggerfehler, alle drei Dateien vollstaendig lesbar.

Segment1:132.595..172.759 s,803 schnelle Zeilen, Ende durch CH3.
Pause19.544 s. Segment2:192.303..242.117 s,997 Zeilen, Ende durch Vollpuffer.
Kein verpasster Rastertermin bedeutet nicht gleichmaessige50-ms-Abstaende;
bei der Auswertung die tatsaechlichen Zeitstempel verwenden.

Alle1800 schnellen Zeilen bleiben MANUAL, Steuer-RX frisch, freigegeben und
PWM vorhanden. Insgesamt5679 Achsenkommandos aus beiden CSVs mit den echten
normalize()/command()-Funktionen, JSON-Kalibrierung und Einstellungen geprueft:
keine Abweichung, auch bei IMU_RUNTIME. Die Laufdiagnose bestaetigt MANUAL
fuer12039 Iterationen nach Freigabe. Das bestaetigt Softwareausgaben und die
Besitzerbeobachtung; Signalformen, mechanische Ausschlaege und Ende-zu-Ende-
Latenz wurden nicht gemessen.

GPS:2549 checksum-gueltige Nachrichten,128 GGA- und128 RMC-Fixsaetze,
keine Parser-/Pruefsummen-/Pollgapfehler. Aufnahme begann bereits mit Ready.
Damit sind die gegenueber R1/R2 offene Fixlast und der bewusste BOOT-Bordstart
im20-Hz-Profil funktional nachgewiesen. Kein Nachweis vermessener Positions-
genauigkeit. Barometer bleibt in allen93 Zeilen gueltig, relativ1.60..4.41 m;
Temperatur10.14 ->7.52 C. Handbewegung, Temperatur und Druckeinfluesse sind
nicht getrennt, daraus keine reale Steig-/Sinkleistung ableiten.

## IMU-Messbereich: Datenqualitaet eingeschraenkt, MANUAL blieb aktiv

Bei211.294 s in der App-Diagnose setzt IMU_RUNTIME. Der erste gespeicherte
Rohsatz lautet (ax,ay,az,Temperatur,gx,gy,gz):

```text
(-10350, 5302, 32767, -1727, 3133, -11169, 5340)
```

az=32767 ist positive Vollaussteuerung. Der Treiber konfiguriert den
Beschleunigungsbereich auf+/-2 g und erkennt Rohwerte ab32700 als Saettigung;
die Gyro-Rohwerte dieses Satzes liegen unter ihrer Grenze. Damit ist die
Messbereichserkennung belegt. Kraeftige Handbeschleunigung ist angesichts der
Besitzerangabe plausibel; der exakte Bewegungszeitpunkt und die physikalische
Ursache sind nicht bewiesen. Kein belegter Logger-/RC-Ausfall oder I2C-Abbruch.

Neun schnelle Zeilen zwischen211.372 und226.270 s sind IMU-ungueltig: Lage-
und Gyrofelder bleiben leer, die RC-/Servo-Kommandos sind weiter enthalten.
Das sind neun gespeicherte ungueltige Messungen, keine gesicherte Anzahl
physischer Stoesse oder Saettigungsereignisse. Dazwischen/anschliessend kommen
gueltige IMU-Werte zurueck:1791 von1800 schnellen Zeilen sind gueltig.
Die IMU_RUNTIME-Markierung bleibt wie vorgesehen verriegelt (616 schnelle
Zeilen mit Fault, davon607 mit wieder frischer IMU). Nicht alle nachfolgenden
Messungen sind dadurch automatisch ungueltig; Gueltigkeitsbits beachten.
Frische allein bestaetigt keine exakte Lage unter dynamischer Beschleunigung.

Eine volle Zustandszeile hat ebenfalls leere IMU-Felder, alle88 periodischen
vollen Samples sind IMU-frisch. Die erste Faultzeile liegt im CSV bei211.372 s:
App-Diagnose und Session-CSV haben hier78 ms versetzte Startreferenzen.
Das ist kein gemessener Steueraussetzer. Beide CSV-Stroeme teilen ihre Zeitbasis.

## Konsequenz und naechster Schritt

GPS-/Bordstart-/Aufnahme-/Export- und MANUAL-Kontinuitaetstest bestanden.
Den gesamten Lauf nicht als fault-frei bezeichnen. Kein Firmwarefix fuer den
MANUAL-Logger erforderlich; Messbereich/Gueltigkeitsmarkierung nicht lockern.
Vor spaeteren STABILIZE-/Navigationsversuchen die IMU-Bereichsauslegung und
Lageschaetzung unter Last gesondert behandeln. Handbewegungen liefern keine
aerodynamische Ruderwirksamkeit oder abgestimmten Gains.

Jetzt Implementierung und R1..R3 als nachvollziehbaren Commit sichern.
Auf demselben Branch bleiben, ohne Push/Merge/Flugfreigabe zu unterstellen.
Einbau, gesicherte Stecker/Leitungen, Schwerpunkt, Versorgung und Ruderwirkung
fuer das vollstaendige Modell anhand der [Einbauanleitung](../../../EINBAU_UND_MANUAL_DATENFLUG.md)
pruefen. Nach Umbau/gedrehter IMU Achsenzuordnung und Kalibrierung wie dort
behandeln; nicht blind nur eine neue Nullage speichern.

Danach ist der naechste praktische Entwicklungsschritt ein kurzer, ausschliesslich
MANUAL geflogener Datenflug mit unveraenderten Gains. Start ruhig kalibrieren,
GPS-Gruen abwarten, erst kurz vor dem Start CH3 oben (90 s gemeinsame
Aufnahmekapazitaet). Nach Landung CH3 unten, BOOT2 s, Tuerkis/Export abwarten,
dann geordnet abschalten. Wind, Dauer und Steuerbewegungen als Flugnotiz sichern.
Keine absichtlichen Grenzmanoever zur Datenerzeugung. Kein weiterer identischer
GPS-Bodenlauf aus diesen Ergebnissen erforderlich; nach Einbauaenderungen die
betroffenen Verbindungen/Funktionen erneut pruefen.

## Rohdateien (SHA-256)

```text
flight_285838_0.json
a98a3598a0626682f9ddd0486f7d8c3b0d49397909e5196ee58eb317c3dd5aae
flight_285838_0.csv
fb21bc3d31940198b619b28094731672f13d213c314874b0840f8ebfc6b72c98
flight_285838_0_response.csv
c72cb98a1f6f6a81b25c615bc3a1ff5314b7e0e86bbcf9aa0a3b5d8eb01734c8
```
