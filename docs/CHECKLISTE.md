### 1. Arbeit beginnen

- [ ] Motor/Propeller für den Bodentest deaktivieren.
- [ ] Batterie vom BEC trennen, bevor du Kabel umsteckst.
- [ ] Im Terminal den Projektordner öffnen:

  ```bash
  cd ~/Documents/Projekte/segelflug-controller
  git status
  ```

- [ ] Prüfen: Auf welchem Branch bin ich? Gibt es uncommittete Änderungen?
- [ ] Bei einem **neuen Entwicklungsschritt** vom geprüften Stand abzweigen:

  ```bash
  git switch main
  git switch -c feature/name-des-schritts
  ```

- [ ] Bei einem **laufenden Schritt** auf dessen Branch wechseln:

  ```bash
  git switch feature/name-des-schritts
  ```

  Vor einem Branchwechsel offene Änderungen bewusst sichern.

### 2. Code ändern und prüfen

- [ ] Dateien **in deiner Projektkopie auf dem Mac** bearbeiten und speichern.
- [ ] Möglichst eine zusammengehörige Änderung auf einmal machen.
- [ ] Bei Änderungen an Pins, Achsen oder Parametern auch die Dokumentation anpassen.
- [ ] Änderungen ansehen:

  ```bash
  git diff
  ```

- [ ] Hosttests ausführen:

  ```bash
  python3 -m unittest discover -s tests -v
  ```

- [ ] Fehler beheben, bevor du die neue Version auf dem MCU testest.

### 3. MCU aktualisieren

- [ ] Laufendes Programm in Thonny stoppen.
- [ ] Bei Änderungen an der Verkabelung: **Batterie und USB vorher trennen.**
- [ ] Anschlüsse prüfen: gemeinsame Masse, richtige GPIOs, Polarität, Signalpegel.
- [ ] MCU ohne gedrückte BOOT-Taste per USB anschließen.
- [ ] In Thonny richtigen Interpreter und Port auswählen.
- [ ] Geänderte `.py`-Dateien ins **MCU-Wurzelverzeichnis** hochladen.
- [ ] Bei Versions-/Branchwechseln alle zusammengehörigen Firmwaredateien hochladen.
- [ ] **Keine ältere `calibration.json` versehentlich überschreiben.**
- [ ] MicroPython neu starten, damit importierte Module neu geladen werden.

**Git verändert den MCU nicht automatisch.** Nach einem Git-Wechsel oder einer Rückkehr zu einer alten Version ist ein passender Upload nötig.

### 4. Kalibrierung prüfen

| Was? | Wann wiederholen? |
|---|---|
| Beschleunigungs-Kalibrierung | Bei anderem Sensor oder auffälligen Messwerten |
| `calibrate_level.py` | Nach geänderter Montage, Achsenzuordnung oder Referenz |
| `calibrate_rc.py` | Nach neu aktiviertem Kanal oder geänderter Senderkonfiguration |
| Gyro-Ruhekalibrierung | Automatisch bei jedem Programmstart; Sensor etwa sechs Sekunden unbewegt lassen |

- [ ] Kalibrierprogramme nur bei gestoppter Regelung ausführen.
- [ ] Nach gespeicherter Kalibrierung `calibration.json` vom MCU auf den Mac herunterladen.
- [ ] Diese Datei zusammen mit der passenden Konfiguration versionieren.

**Die Lagenreferenz nicht bei jedem Einschalten neu speichern.** Sonst würde eine zufällige Startlage zur neuen Waagerechten.

### 5. Bodentest durchführen

- [ ] Sender einschalten und richtige Einstellungen prüfen.
- [ ] BEC/Batterie anschließen; MCU-Versorgung wie geplant herstellen.
- [ ] Bei neuen Funktionen zuerst `sensor`, dann `manual`, zuletzt `stabilize` testen.
- [ ] `start_test.py` ausführen.
- [ ] Während der Gyro-Kalibrierung nichts bewegen.
- [ ] Knüppel für die Freigabe mittig halten.
- [ ] Ausgabe prüfen: richtiger Modus, plausible Winkel, RC- und Servowerte.
- [ ] Ruderwirkung prüfen — nicht nur die sichtbare Servodrehrichtung.
- [ ] Mechanische Endanschläge, Brummen, Zittern und Erwärmung beachten.
- [ ] Erst einzelne Achsen, anschließend kombinierte Bewegungen testen.
- [ ] Ergebnis kurz notieren: Version, Parameter, Verhalten, offene Probleme.

### 6. Test beenden und Daten sichern

- [ ] Mit **Ctrl+C** stoppen.
- [ ] Auf **„PWM/PIO ausgeschaltet“** und die Log-Speicherung warten.
- [ ] Benötigte `bench_…csv`-Dateien auf den Mac herunterladen.
- [ ] **Batterie vom BEC trennen.**
- [ ] USB trennen, wenn du fertig bist oder umstecken möchtest.
- [ ] Sender ausschalten.
- [ ] Alte MCU-Logs erst nach Sicherung löschen, damit der Flash nicht voll wird.

Die RAM-Logs gehen beim Stromverlust verloren. Deshalb **erst stoppen und speichern, dann Versorgung trennen**.

### 7. Änderung mit Git sichern

- [ ] Nochmals prüfen:

  ```bash
  git status
  git diff
  ```

- [ ] Zusammengehörige Dateien auswählen, beispielsweise:

  ```bash
  git add firmware/config.py
  ```

  Falls ebenfalls geändert:

  ```bash
  git add firmware/calibration.json docs/THONNY.md
  ```

- [ ] Ausgewählte Änderungen kontrollieren und committen:

  ```bash
  git diff --staged
  git commit -m "Kurze Beschreibung der Änderung und Prüfung"
  ```

- [ ] Falls GitHub eingerichtet ist: beim ersten Push dieses Branches:

  ```bash
  git push -u origin feature/name-des-schritts
  ```

  Danach genügt:

  ```bash
  git push
  ```

Auch Zwischenstände dürfen committed werden. Beschreibe ehrlich, wenn etwas noch nicht funktioniert.

### 8. Entwicklungsschritt abschließen

**Nur wenn der gesamte Schritt geprüft ist:**

- [ ] Offene Änderungen committen.
- [ ] In `main` übernehmen:

  ```bash
  git switch main
  git merge --ff-only feature/name-des-schritts
  ```

- [ ] Falls der Merge abgelehnt wird: Ursache prüfen, nicht erzwingen.
- [ ] Einen wichtigen Stand markieren, mit einem **neuen, noch unbenutzten Versionsnamen**:

  ```bash
  git tag -a v0.3.0-nick-boden -m "Roll und Nick am Boden geprüft"
  ```

- [ ] Falls GitHub eingerichtet ist:

  ```bash
  git push origin main
  git push origin --tags
  ```

- [ ] Den nächsten Entwicklungsschritt wieder von der aktuellen `main` beginnen.

**Deine tägliche Kurzliste:**

**Status prüfen → Branch wählen → ändern → Hosttests → Upload → Neustart → nötige Kalibrierung → Bodentest → Logs sichern → Batterie trennen → Commit → optional Push.**

**Merge und Versionstag erst nach Abschluss eines geprüften Entwicklungsschritts.**
