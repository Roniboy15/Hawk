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
