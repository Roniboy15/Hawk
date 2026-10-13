# Roll-Tischtest — v0.2.1-bench

Naechster Schritt nach Hostvalidierung. Nur beaufsichtigter Tischtest, keine
Flugfreigabe. Der Segler hat kein Triebwerk/Gas; Servos sind laut Besitzer
montiert und angeschlossen. Stromversorgung, Signalpegel und Ruderwirkung
sind damit noch nicht qualifiziert. Kein unabhaengiger Hardware-Bypass vorhanden.

Stand 2026-10-12: Der Besitzer bestaetigt MANUAL und Rollstabilisierung mit
beiden Rollzeichen=-1 und rate_p=2. Das aktuelle gespeicherte Profil startet
MANUAL bei AUTO_START=False. Neue/geaenderte Hardware weiterhin zuerst SENSOR.
Der grundlegende Roll-Funktionstest ist damit vom Besitzer abgeschlossen;
Versorgungs-/Timingqualifikation bleibt separat offen. Weiter mit
[PITCH_YAW_TISCHTEST.md](PITCH_YAW_TISCHTEST.md) und
[VERSORGUNG_WARNHINWEISE.md](VERSORGUNG_WARNHINWEISE.md). Keine Flugfreigabe.

## Vorbereitung

- Bisherigen MCU-Code und calibration.json sichern. Alle zusammengehoerigen
  Firmwaremodule von v0.2.1 ins MCU-Wurzelverzeichnis uebertragen; vorhandene
  Kalibrierung bewusst erhalten. Danach Soft-Reboot wegen gecachter Imports.
- Vor Umstecken USB und Servo-/Receiverversorgung trennen. GPIO-Nummern,
  gemeinsame Masse, 3,3-V-kompatible Eingangspegel und vorhandene Versorgung
  pruefen. Die geplante Stromleiste ist noch kein getesteter Versorgungsaufbau.
- Flugzeug/Mechanik abstuetzen, Ruderbewegung freihalten, Servoversorgung
  zum sofortigen Trennen erreichbar halten. Ctrl+C benoetigt eine laufende CPU.
- Fuer alle Phasen AUTO_START=False, ACTIVE_AXES=('roll',), rate_i=0.
  Nick/Gier softwareseitig deaktiviert lassen, auch wenn schon angeschlossen.
- Version, MicroPython-Version, Konfiguration, Versorgung und Ergebnisse notieren.

## 1. SENSOR

START_MODE='sensor', Soft-Reboot, start_test.py. Fuer die Startkalibrierung
etwa sechs Sekunden ruhig liegen lassen. Langsam um die Rollachse neigen:
Rechtsbank muss zum positiven Rollwert passen, Linksbank zum negativen.
Bei ruhigem Halten plausible stabile Werte erwarten. Keine Servo-PWM.
Sensorfehler, unplausible Achsen oder TIMING erst klaeren, bevor es weitergeht.

## 2. Kalibrierung und MANUAL

RC-/Level-Kalibrierung nur bei gestoppter Regelung: fehlende Referenz speichern,
bei geaenderter Montage/Senderkonfiguration neu erfassen. Level nicht bei jedem
Start neu speichern. Schema 1 bleibt unveraendert; gespeicherte Werte sichern.

START_MODE='manual', Soft-Reboot, start_test.py. Vor erster Freigabe keine Pulse.
Nach 25 neuen Neutralframes muss MANUAL erscheinen. Langsame Knueppelbewegung
testen: beide Querruder muessen mechanisch gegenlaeufig sein; Rechtskommando
muss eine Rechtsrollwirkung erzeugen. Manual ist kalibrierter, begrenzter
Durchgang. Default-Rollgrenzen sind 1300..1700 us, Trimneutral 1500 us.
Bei abweichender Konfiguration deren tatsaechliche Grenzen verwenden.

## 3. STABILIZE, nur Roll

Nach bestandenem Sensor-/Manualtest START_MODE='stabilize', Soft-Reboot,
start_test.py. Neutralfreigabe abwarten. Bei Knueppelmitte kleine, langsame
Links-/Rechtsneigungen: Ruderwirkung muss der Neigung entgegenwirken.
Bei Sollbank=Istbank und ohne Drehrate geht das Kommando zur Trimlage.
Ein Knueppelausschlag fordert eine Banklage, nicht direkten Servo-Ausschlag.
Zuerst kleine Winkel und bestehende begrenzte Wege; noch keine Gain-Erhoehung.

Falsche Korrekturrichtung, Anschlag/Brummen, Zittern oder wiederholte
TIMING/IMU-Fehler: stoppen, Versorgung trennen und Ursache klaeren.
Nicht wiederholt resetten, um ein auffaelliges Verhalten zu uebergehen.

## Fehlerverhalten und Abschluss

- Erkannter Zeitverlust: TIMING bleibt verriegelt, aktive Ausgaenge gehen auf
  Trimneutral. RX_TIMEOUT, danach WAIT_NEUTRAL und nach neuen Neutralframes
  MANUAL_FALLBACK sind erwartbar. STABILIZE kehrt erst nach Neustart zurueck.
- Ein Receiver kann bei Senderausfall weiter Pulse liefern. Sender-Aus ist
  daher kein verlaesslicher Test des Pulse-Timeouts. Fehlende Pulse nur mit
  vorbereitetem Testaufbau/Signalquelle pruefen; keine Live-Umverdrahtung.
- Permanenter Bus-/CPU-Haenger bleibt unbeherrscht. Bei fehlender Reaktion
  Versorgung trennen; Softwarefallback ist keine unabhaengige Rueckfallebene.
- Ctrl+C: PWM/PIO-Abschaltung und danach Logexport abwarten. Bei Meldung
  "Abschalten unvollstaendig" Versorgung trennen; kein Export erfolgt.
- Log sichern und je Phase PASS/FAIL, Ruderwirkung, Modus, Fehler und Parameter
  dokumentieren. Erst wenn alle Rollphasen reproduzierbar bestehen, Nick-Konvention
  aufloesen und weitere Achsen vorbereiten. Ein Tischtest prueft keine Flugstabilitaet.
