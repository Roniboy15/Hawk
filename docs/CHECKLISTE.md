### 1. Arbeit beginnen

- [ ] Beaufsichtigten Tischtest vorbereiten; dieser Segler hat kein Triebwerk/Gas.
- [ ] Batterie vom BEC trennen, bevor du Kabel umsteckst.
- [ ] Im Terminal den Projektordner öffnen:

  ```bash
  cd /Users/jarontreyer/Desktop/Hawk/segelflug-controller
  git status
  ```

- [ ] Prüfen: Auf welchem Branch bin ich? Gibt es uncommittete Änderungen?
- [ ] Bei einem **neuen Entwicklungsschritt** vom passenden, committeden
  Abschlussstand abzweigen. Fuer den jetzigen Folgeschritt ist das der neue
  Commit auf `codex/receiver-timing-hardening`, nicht die aeltere main:

  ```bash
  git switch -c codex/bench-fault-validation
  ```

- [ ] Bei einem **laufenden Schritt** auf dessen Branch wechseln:

  ```bash
  git switch codex/receiver-timing-hardening
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
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
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
- [ ] Roll/Nick/Gier-Funktionstests laut Besitzer abgeschlossen;
  [Testbericht](TESTBERICHT_2026-10-13.md) sichern. Weiter mit
  [konkreten Fehler-/Timingtests T1–T6](FEHLER_TISCHTEST.md) und
  [Protokoll](TESTPROTOKOLL_FEHLER.md). Fuer Wiederholungschecks
  [PITCH_YAW_TISCHTEST.md](PITCH_YAW_TISCHTEST.md) und
  [VERSORGUNG_WARNHINWEISE.md](VERSORGUNG_WARNHINWEISE.md) verwenden.
- [ ] Neue Achse erst SENSOR/MANUAL pruefen, dann DIRECTION_CHECKED_AXES erweitern.
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
- [ ] Bei **„Abschalten unvollstaendig“** Versorgung trennen und Fehler klaeren;
  in diesem Fall wird kein Log exportiert.
- [ ] Benötigte `bench_…csv`-Dateien auf den Mac herunterladen.
- [ ] Ab v0.2.3 den passenden `bench_…json`-Laufbericht ebenfalls sichern;
  mit tools/analyze_bench.py und dem passenden Testprofil auswerten.
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

- [ ] Zusammengehörige Dateien stagen: neue, geaenderte oder geloeschte Dateien
  fuer den naechsten Commit auswaehlen. `git add` speichert diese Auswahl im
  Index, aendert weder den MCU noch GitHub. Beispielsweise:

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
  git push -u origin codex/name-des-schritts
  ```

  Danach genügt:

  ```bash
  git push
  ```

Auch Zwischenstände dürfen committed werden. Beschreibe ehrlich, wenn etwas noch nicht funktioniert.

### 8. Entwicklungsschritt abschließen

**Nur wenn der abgegrenzte Schritt geprüft ist:** Bodenfunktion, elektrische
Qualifikation und Flugfreigabe im Committext getrennt benennen. Fuer den aktuellen
Abschluss ist ein Commit plus neuer Folgebranch geplant; Merge/Tag sind optional.

- [ ] Offene Änderungen committen.
- [ ] In `main` übernehmen:

  ```bash
  git switch main
  git merge --ff-only codex/name-des-schritts
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

- [ ] Den nächsten Entwicklungsschritt von dem Commit mit den benoetigten
  Aenderungen beginnen. Das ist nur dann `main`, wenn dieser Stand dorthin
  uebernommen wurde; sonst vom abgeschlossenen Entwicklungsbranch abzweigen.

**Deine tägliche Kurzliste:**

**Status prüfen → Branch wählen → ändern → Hosttests → Upload → Neustart → nötige Kalibrierung → Bodentest → Logs sichern → Batterie trennen → Commit → optional Push.**

**Merge und Versionstag erst nach Abschluss eines geprüften Entwicklungsschritts.**
