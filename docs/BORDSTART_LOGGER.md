# Logger0.1.9 ohne Mac: bewusster BOOT-Start

Branch bleibt codex/manual-flight-logger. Basis ist8b9adde; diese Ergaenzung
ist inzwischen funktional auf dem Board getestet, siehe
[Auswertung aller0.1.9-Laeufe](testdaten/fluglogger/AUSWERTUNG_019.md).
BOOT-Start/Reserve/Export, SENSOR und kurzer MANUAL-Fixbetrieb bestanden;
zehn Minuten Aufnahme und elektrische Spannungsqualitaet noch offen.
AUTO_START=False und START_MODE='sensor'
bleiben Standard. Neue Einstellung LOGGER_BOOT_MODE=None deaktiviert Bordstart;
'sensor' oder 'manual' aktiviert ausschliesslich den passenden Logger.
Nicht AUTO_START=True setzen: das ist weiterhin der alte Controllerstart.

## Versorgung: Besitzer waehlt BEC5 V am RP2040-Zero

Bei getrennten Quellen geregelten BEC-Ausgang5 V mit dem am Board als5V
beschrifteten Eingang verbinden, Minus mit GND. Niemals7.4 V oder5 V an3V3.
IMU/GY-63 bleiben an3V3, GPS/Receiver/Servos an ihrer bisherigen5-V-Verteilung.
Gemeinsame Signalmasse erhalten; Servostrom nicht durch das MCU-Board fuehren.

Wichtig bei diesem Board: Der Hersteller-Schaltplan zeigt keine automatische
Trennung zwischen USB-Versorgung und externem5-V-Eingang. Deshalb:

- Bordtest: BEC als Quelle, USB vollstaendig abgezogen.
- Upload/Download: erst BEC/Batterie ausschalten und die **5-V-Verbindung vom
  gemeinsamen BEC-/Servonetz zum MCU physisch trennen**, dann Mac-USB einstecken.
  Nur die Batterie abzuschalten reicht nicht: USB koennte sonst die Servo-
  Verteilung ueber den5-V-Pin rueckwaerts speisen. GND darf verbunden bleiben.
- Niemals eine laufende USB-Sitzung durch Umstecken auf BEC uebernehmen.
  Nach Export geordnet abschalten, verkabeln, dann neu starten.

Der BEC versorgt nun auch den MCU. Deshalb5 V/3V3 unter normaler gleichzeitiger
Servobewegung im endgueltigen Aufbau pruefen;3 A und der1000-uF-Kondensator
sind keine gemessene Lastreserve. Keine Ruder blockieren oder Stromausfaelle
absichtlich erzeugen. Quelle: [Waveshare-Schaltplan](https://files.waveshare.com/upload/4/4c/RP2040_Zero.pdf).

## B1: bestanden; folgende Folge nur bei Bedarf wiederholen

1. BEC-Verbindung zum MCU wie oben trennen, Servostrom aus. Bei USB-Versorgung
   **main.py, config.py, flight_start.py und flight_logger.py** aktualisieren.
   calibration.json erhalten; keine neue RC-/Lagekalibrierung fuer den Code.
2. In config.py LOGGER_BOOT_MODE='sensor' setzen; AUTO_START=False und
   START_MODE='sensor' belassen. Speichern. Den neuen Start zuerst einmal bei
   geoeffnetem Thonny per Soft-Reboot beobachten: Violett, BOOT2 s/Weiss/loslassen,
   Gyro-Ruhe, Logger0.1.9/SENSOR und mindestens65536 B Startreserve. Dabei bleibt
   die MCU-5-V-Verbindung zum BEC getrennt, Servostrom aus. Den kurzen Lauf mit
   CH3 unten/BOOT2 s sauber beenden. Erst dann geordnet abschalten, USB entfernen.
3. Bei getrennten Quellen MCU an BEC5 V/GND anschliessen. Fuer CH3 den Receiver
   mitversorgen; die **Servoversorgungen bleiben getrennt**. Sensoren normal
   mitversorgen. Sender an, Steuerknueppel neutral, CH3 unten.
4. Ohne gedrueckten BOOT einschalten. **Violett** bedeutet: wartet, keine
   Sensor-/RC-PIO-/Servoaktivierung durch die App. Die RAM-Reservierung und
   reinen Modulimports sind bereits erfolgt. Violett ist keine Flugbereitschaft.
5. BOOT zwei Sekunden halten. Bei **Weiss** loslassen, dann Modell waehrend
   der etwa6-s-Gyro-Kalibrierung ruhig halten. Die LED ist dabei kurz aus;
   anschliessend folgt die bisherige rote/gruene GPS-Anzeige.
   BOOT niemals beim Einschalten halten: das kann den ROM-USB-Bootloader starten.
6. CH3 oben fuer etwa10-15 s, dann unten. BOOT2 s halten; Blau beim Export,
   danach Tuerkis abwarten. Erst dann BEC ausschalten und fuer den Download
   die5-V-Verbindung zum MCU wieder trennen, bevor Mac-USB angeschlossen wird.
7. CSV/JSON nach docs/testdaten/fluglogger/B1_bordstart_019/ sichern.
   Erwartet: logger_version0.1.9, start_method='boot_button', shutdown_ok=true,
   stop_reason='ground_button', SENSOR und durchgehend Servo-Pulse0.

Kurze Tastendruecke starten nicht. Ein beim Eintritt gehaltener Taster muss
erst losgelassen werden. Nach bestaetigtem Druck wartet der Start ebenfalls
auf Loslassen; kein Startdruck reicht in den spaeteren Stopdetektor hinein.
Bei abweichender LED/fehlendem Export nicht blind weiter testen. Versorgung
geordnet trennen und die Konsole am Mac nach obigem Quellenwechsel pruefen.
Die64-KiB-RAM-Startreserve bleibt verlangt; bei Abbruch nicht verkleinern.

## Danach F3: MANUAL mit GPS und zehn Minuten Aufnahme

Nach bestandenem B1 LOGGER_BOOT_MODE='manual' einstellen/hochladen; fuer den
USB-Zugriff jedes Mal den beschriebenen Quellenwechsel einhalten.
Die Startfolge mit Violett/BOOT/Weiss bleibt gleich. Nach Gyro-Kalibrierung
brauchen die drei Steuerachsen weiterhin frische Neutralframes vor PWM-Start.
Ruderwirkung zuerst am Boden bestaetigen. Danach den kombinierten
[F3-Bodentest](FLUGLOGGER_TEST.md) draussen: GPS-Gruen, zwei etwa5-min-Segmente
mit CH3-Pause, normale Steuerbewegungen, geordneter BOOT-Stop/Export.
Unter docs/testdaten/fluglogger/F3_gps_dauer_019/ sichern.

Die neue Taste ersetzt weder CH3 noch die Neutralfreigabe. CH3 unten pausiert
weiterhin nur Aufnahme; BOOT2 s bei pausierter Aufnahme beendet das Programm
und damit auch die Steuerung. Ausschliesslich am Boden bedienen.
Nach Export wird nicht automatisch neu gestartet. Thonny-Aufrufe
flight_start.run('sensor'/'manual') bleiben ohne vorgeschaltete Starttaste
verwendbar; ihr Bericht nennt start_method='explicit'.

201 Hosttests bestehen: Default/Logger-/Legacy-Routing, Konfliktsperre,
gehaltener/kurzer BOOT-Druck, Zwei-Sekunden-Halten mit Tick-Umlauf, Loslassen,
Abbruch mit Pufferfreigabe und Reihenfolge vor Controllerstart. Keine Hardware-
Ausfuehrung durch den Agenten, keine geaenderten Gains/Pins/Zeit-/RAM-Grenzen.
