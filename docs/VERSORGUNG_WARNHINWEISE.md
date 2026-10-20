# Versorgungsbefund und Warnhinweise — Tischtests

## Bericht, nicht Messung

Am 2026-10-12 wurde beim Programmstart bzw. nahe dem Servostart eine kurze
Unterbrechung steckdosenversorgter Geraete gemeldet. Versorgung kam von selbst
zurueck. Mac am Netzladegeraet; MCU via Mac-USB-C; BEC laut Besitzer nur am
Servoversorgungszweig, nicht am MCU-5-V-Pin. Vier Servos waren versorgt/in Betrieb.
Die Beschriftung lautet 5 V @ 3 A und zusaetzlich gross 20 A. Modell, Peak-Rating,
Strom-/Spannungsverlauf und genauer Zeitpunkt sind unbekannt.
Hoehen-/Seitenruder gingen zu diesem Zeitpunkt noch direkt zum Receiver. Diese
Servos konnten daher unabhaengig von app.run() bereits Pulse erhalten und Strom aufnehmen.

Update 2026-10-13: alle Achsen-Funktionstests laut Besitzer bestanden;
[Testbericht](TESTBERICHT_2026-10-13.md). Das klaert die Ursache der damaligen
Unterbrechung und die Versorgungsreserve nicht. Die folgenden Hinweise bleiben gueltig.

## Beste Diagnose mit diesen Angaben

Neuer, davon getrennter Befund 2026-10-18: Ausschlag beim USB-Abziehen ohne
Ctrl+C, BEC/Receiver/Servos weiter versorgt, gemeinsame Masse laut Besitzer
erhalten. Bei korrektem Stop nicht beobachtet. Das ist kein Nachweis zur Ursache
der frueheren Raum-/Steckdosenunterbrechung. Details und Logbefunde:
[Auswertung T1/T2](testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T1_T2.md).
Verlust des MCU-Signals/Versorgungsuebergang ist eine Arbeitshypothese; die
elektrische Signalform wurde nicht gemessen. Fehlende Pulse sind kein
1500-us-Neutralbefehl; Servoreaktion ist modellabhaengig
([Pololu](https://www.pololu.com/blog/17/servo-control-interface-in-detail)).

Neuer, davon getrennter Befund **2026-10-19: USB-Anstecken** bei vorher bereits
versorgtem BEC/Empfaenger und eingeschaltetem Sender. Hoehen-/Seitenrudersignale
an GP6/GP7; beide Ruder schlugen maximal aus und blieben dort. Nach Kenntnis
des Besitzers lief kein Programm, Thonny war offen. Die bisherige IMU war ohne
Versorgung, SDA/SCL/GND blieben angeschlossen. GY-63 war angeschlossen,
GPS noch nicht. Kondensator laut Besitzer 1000 uF / 10 V, parallel am geregelten
5-V-Ausgang, Minus an GND. Dieser gemeldete Anschluss und die Nennspannung
sind plausibel; das beweist weder Transientenverhalten noch Ereignisursache.
Barometerlog und getrennte Befunde:
[GY-63-Auswertung](testdaten/barometer_tests/AUSWERTUNG.md).

Der neue Sensorstarter konfiguriert im baro-Profil nur GP10/GP11 und verwendet
weder IMU noch Servo-PWM. Der Hoststand main.py startet mit AUTO_START=False
keinen Regler. Nachtrag: Die vom Besitzer jetzt gezeigte MCU-main.py hat
dieselbe Startlogik, AUTO_START laut Besitzer False. Der Dateistand zum
Ereignis bleibt laut Besitzer unbekannt; boot.py nicht uebermittelt.
Thonny offen allein sagt weder Autostart noch aktives Programm sicher aus.
Unversorgte IMU bedeutet hier deshalb nicht automatisch eine berechnete
Maximalkorrektur. **Am ehesten zu pruefen: Signal-/Versorgungsuebergang,
Rueckspeisung und abweichende Startdateien.** Ausloesender Puls und Ursache
bleiben ohne Messung/MCU-Dateiabgleich offen.

- Vor USB kann der bereits versorgte Empfaenger Spannung auf unversorgte
  MCU-Eingaenge legen. Beim RP2040 ist die absolute GPIO-Grenze IOVDD+0.5 V,
  nicht ein von der Versorgung unabhaengiger 3.3-/5-V-Grenzwert. RX-Pegel und
  Schutzbeschaltung pruefen; tatsaechlicher Stromfluss hier nicht gemessen.
  [RP2040-Datenblatt, Tabelle 622](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf).
- Signalleitungen koennen unversorgte Bauteile je nach interner Schutzbeschaltung
  rueckspeisen. Eine IMU ohne VCC, aber mit SDA/SCL am versorgten System ist
  deshalb kein sauber abgetrennter Sensor. Pullups und konkrete Platine bestimmen
  den Pfad. Das ist eine Hypothese fuer diesen Aufbau, kein Nachweis der Ursache.
  [TI: Powered-off protection](https://www.ti.com/document-viewer/lit/html/scda015).
- Keine laufenden Servoimpulse bedeutet keine zugesicherte Neutralstellung.
  Manche Digitalservos halten einen zuletzt erkannten Befehl; das erklaert nicht
  allein, wie der Maximalbefehl zustande kam. Auch Signal-/GND-Verwechslung,
  Versorgungseinbruch oder ein anderer MCU-Autostart sind nicht ausgeschlossen.
- Ein korrekt angeschlossener Kondensator kann Spannungsspitzen/-einbrueche
  beeinflussen; er erzeugt keine gueltigen Servopulse. Ohne Anschlussplan,
  Polaritaet/Daten und Messung weder Ursache noch Loesung behaupten.

Bei diesem Befund zuerst BEC-/Servoversorgung aus, danach USB trennen.
Keine Endausschlaege fuer Diagnose absichtlich mit montierten Servos wiederholen.
IMU bei getrennten Quellen wieder normal versorgen oder vollstaendig abstecken;
Sensorchecks nur mit USB, BEC/Receiver/Servos aus. main.py, config.AUTO_START
und vorhandene boot.py auf dem MCU bei ausgeschaltetem BEC als Text pruefen,
nicht zum Zentrieren einen unbekannten Regler starten. Kondensator gehoert bei
entsprechender Auslegung parallel an den vorgesehenen BEC-Versorgungszweig,
bei gepoltem Typ Minus an GND; niemals an einen GPIO. Auch nach Abschalten
moegliche Restladung beachten. Vor erneutem Aktuatorbetrieb Aufbau eingrenzen;
falls erforderlich mit geeigneter Messtechnik ohne belastete montierte Ruder.
Kein Boot-Neutral-PWM als ungepruefter Workaround: es schuetzt nicht vor
Ereignissen, die vor Ausfuehrung der Firmware auftreten.

## Einordnung der Raum-/Steckdosenunterbrechung vom 2026-10-12

1. **Raum-/Steckdosenversorgung:** Eine kurze Unterbrechung der Versorgung
   bzw. einer gemeinsamen Anschlussstelle passt am besten zum berichteten
   Ausfall mehrerer netzversorgter Geraete und selbsttaetiger Rueckkehr. Das ist
   eine Arbeitshypothese. Steckdosenleiste, Netzteil und Installation sind nicht geprueft.
2. **Moegliche servo-bezogene Stoerung:** Beginnende Servobewegung/Haltekraft
   kann einen Stromsprung verursachen. Ein zu schwacher BEC, Leitungsabfall oder
   schlechte gemeinsame Masse kann Niedervoltgeraete stoeren. Vier Servos sind
   fuer einen 3-A-Zweig kein automatisch qualifizierter Aufbau. Das erklaert
   allein noch keinen Stromausfall anderer steckdosenversorgter Geraete.
3. **USB-/Ladegeraet-/Verdrahtungsfehler:** Wegen der USB-/Masseverbindung und
   des angeschlossenen Mac-Ladegeraets kann ein weiterer Fehler nicht ausgeschlossen
   werden. Ein Rueckspeisepfad oder ein Ladegeraetefehler ist nicht nachgewiesen.

Programmstart kann ein **Ausloeser einer Niedervolt-Last** sein, beweist aber
keine Ursache im Stromnetz. Auch umgekehrte Kausalitaet ist moeglich: die
Versorgungsstoerung koennte den MCU/USB-Start beeinflusst haben. Weder "die
Firmware war schuld" noch "sicher harmlos" ist durch die Angaben belegt.

Fuer den verwendeten 5-V-Zweig mit **3 A** planen. Die 20-A-Aufschrift darf
nicht als 5-V-Servo-Stromfreigabe benutzt werden; ihre Bedeutung verlangt das
Geraetedatenblatt. Servotypen und Spitzenstroeme fehlen. Eine gemeinsame
Stromleiste ersetzt weder ausreichende BEC-Leistung noch saubere Verdrahtung.
Siehe [Pololu: Servostrom und Versorgung](https://www.pololu.com/blog/16/electrical-characteristics-of-servos-and-introduction-to-the-servo-control-interface).

## Warnhinweise fuer die naechsten Tests

- USB nicht zum Beenden des Tests abziehen. Ctrl+C, beide Exportmeldungen,
  danach zuerst BEC-/Receiver-/Servoversorgung aus. USB zum Thonny-Download
  angeschlossen lassen und zuletzt trennen. Bei unvollstaendiger Abschaltung
  zuerst Servoversorgung trennen. Korrekte Bedienfolge ist keine Absicherung
  gegen einen unerwarteten MCU-Stromausfall.
- Alle Quellen trennen, bevor Signalleitungen umgesteckt werden. Nur ein Ausgang
  darf einen Servosignal-Draht treiben: Receiver ODER MCU. Keine parallelen Signalausgaenge.
- MCU ueber USB, Servo-Plus ueber passenden BEC, gemeinsame GND. Kein BEC-Plus
  an MCU-5-V/USB-VBUS bei gleichzeitig angeschlossenem USB. Der
  [Waveshare-Schaltplan](https://files.waveshare.com/upload/4/4c/RP2040_Zero.pdf)
  zeigt den gemeinsamen USB-/VSYS-Versorgungszweig; Board/Revision abgleichen.
- Fuer beaufsichtigte Niedervolttests Mac vom Netzladegeraet trennen und aus
  seinem Akku betreiben, auch andere netzgespeiste USB-/Dock-Verbindungen trennen.
  Das entfernt den beschriebenen Ladegeraetpfad, garantiert aber keine sichere Verdrahtung
  und schuetzt den USB-Port nicht vor einem Niedervolt-Kurzschluss.
- Vor MANUAL/PWM die RX-Signalpegel, Stromfreigabe des BEC und Leitungsfuehrung
  pruefen. Keine Servos aus MCU-3V3 speisen. Nur eine neue Achse pro Schritt,
  kleine Ausschlaege; keine absichtliche Servo-Blockade als Belastungstest.
- Niedervolt-Strom und 5-V-Spannung unter normaler Last nach Datenblatt beurteilen.
  Ein langsames Multimeter kann kurze Einbrueche uebersehen. Noch keine gleichzeitigen
  grossen Bewegungen mehrerer neuer Achsen, solange Stromreserve unbekannt ist.
- Versorgungsunterbrechung, USB-Disconnect, Reset, auffaellige Erwaermung, Brummen
  oder Blockieren: Test stoppen und Aufbau klaeren. Bei erneutem Ausfall anderer
  Steckdosengeraete, Geruch/Knacken oder Schutzschalterausloesung betroffene
  Netzgeraete nicht weiter zum Testen verwenden; fachkundige Hilfe hinzuziehen.
  [Electrical Safety First](https://www.electricalsafetyfirst.org.uk/safety-advice/home-and-people/summer-tips/)
  behandelt solche Netzsymptome als Warnzeichen. Keine Netzspannungsmessung,
  kein Oeffnen des Ladegeraets und keine absichtliche Wiederholung des Ausfalls.

## Was die neue Diagnoseausgabe belegt

v0.2.2 meldet GYRO_CAL, GYRO_DONE und PWM_START_REQUEST mit MCU-Tickzeit.
Waehrend der Gyro-Ruhekalibrierung erstellt die App noch keine eigene Servo-PWM.
Erst kalibrierte frische Neutralframes erlauben den PWM-Start. Initiales
Trimneutral kann trotzdem eine Bewegung/Haltekraft und Stromaufnahme ausloesen.
PWM_START_REQUEST bezeichnet einen Versuch, keine garantierte erfolgreiche Aktivierung.
Die Deadline wird danach erneut geprueft; blockierte Hardware bleibt unbeherrscht.
Zeitmarken helfen bei spaeteren normalen Tests, sind aber keine Strommessung.
