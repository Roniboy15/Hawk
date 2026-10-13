# Git auf dem Mac: einmal einrichten, danach kleine Aenderungen sichern

Das Paket enthaelt den Code und repository.bundle mit dem vorbereiteten
lokalen Git-Repository/Startcommit. Kein GitHub-Repository wurde angelegt oder
veroeffentlicht. Ein lokales Repo funktioniert ohne Konto und ohne Internet.

## 1. Git pruefen

Terminal oeffnen:

```bash
git --version
```

Wenn macOS Git/Entwicklerwerkzeuge installieren moechte, der Installations-
aufforderung folgen. Danach nochmals pruefen. Python 3 fuer Tests muss auf
dem Mac vorhanden sein; Thonny bringt einen Interpreter mit, aber dessen
Vorhandensein garantiert keinen python3-Befehl im Terminal.

## 2. Vorbereitetes Repo klonen

ZIP im Downloads-Ordner entpacken; angenommen der entpackte Ordner heisst
segelflug-controller. Einen Projektordner auf dem Mac anlegen und das Bundle
klonen (Pfade bei anderer Ablage anpassen):

```bash
mkdir -p ~/Documents/Projekte
cd ~/Documents/Projekte
git clone ~/Downloads/segelflug-controller/repository.bundle segelflug-controller
cd segelflug-controller
git remote remove origin
git config user.name "Dein Name"
git config user.email "deine-adresse@example.com"
git status
git log --oneline -5
```

Die beiden Identitaetswerte durch deine eigenen ersetzen. Die Konfiguration
gilt nur fuer dieses Projekt; der vorbereitete Startcommit ist als Codex
gekennzeichnet, nicht als von dir geschrieben. origin zeigt beim Klonen nur
auf das lokale Bundle und wird deshalb entfernt. Die Arbeitskopie auf deinem
Mac ist ab jetzt die verbindliche Quelle fuer Codeaenderungen.

Alternative, falls du keinen vorbereiteten Verlauf verwenden willst: den
entpackten Codeordner verwenden, dort git init -b main, git config wie oben,
git add firmware docs tests README.md .gitignore, git commit -m "Startversion".
repository.bundle nicht mitcommitten. Die Alternative ist nicht erforderlich,
wenn du bereits mit git clone begonnen hast.

## 3. Eigene funktionierende Einstellungen sichern

Bekannte Richtungen/Pins in firmware/config.py kontrollieren. Die neu auf dem
MCU erstellte calibration.json nach firmware/ herunterladen. Dann:

```bash
git status
git diff
git add firmware/config.py firmware/calibration.json
git diff --staged
git commit -m "RC- und Lagenkalibrierung fuer mein Flugzeug"
```

Wenn calibration.json noch nicht existiert, erst kalibrieren; nicht eine leere
Datei erstellen. Beim Umstecken USB und Servo-/BEC-Versorgung trennen.
Dieser Segler hat kein Triebwerk.

### Aktueller Abschlussstand (2026-10-13)

Alle Achsen-Funktionstests sind laut Besitzer bestanden. Die aktuelle Arbeit
liegt auf `codex/receiver-timing-hardening`; der Besitzer hat den Abschlusscommit
und Folgebranch am 2026-10-13 freigegeben. Die zusammengehoerigen Konfigurations-/
Test-/Doc-Aenderungen gemeinsam stagen und committen, dann davon `codex/bench-fault-validation`
abzweigen. main ist derzeit aelter und enthaelt diese Aenderungen noch nicht.
Details: [NAECHSTE_SCHRITTE.md](NAECHSTE_SCHRITTE.md).

Staging ist die Auswahl des naechsten Commitinhalts: `git add` erfasst auch
Aenderungen an bestehenden Dateien und Loeschungen. `git diff --staged` zeigt
diese Auswahl. Spaetere Datei-Aenderungen brauchen erneut `git add`.
Committen speichert einen lokalen Snapshot; weder Upload noch Flugfreigabe.

## 4. Jede kleine Aenderung: derselbe Ablauf

Beispiel: nur Roll-Reglerparameter aendern.

```bash
git switch -c codex/roll-abstimmung
```

Dann config.py lokal in Thonny bearbeiten und auf dem Mac speichern. Danach:

```bash
git diff
python3 -m unittest discover -s tests -v
```

Geaenderte Firmwaredatei auf MCU hochladen, Stop/Soft-Reboot, Bodenversuch
ausfuehren. Ergebnis kurz notieren. Wenn die Aenderung sinnvoll ist:

```bash
git add firmware/config.py
git diff --staged
git commit -m "Roll-Regler am Fluegel ruhiger abgestimmt"
git status
```

Ein Commit pro zusammengehoeriger Aenderung: nicht jede einzelne Zeile,
aber auch nicht Sensor, Verkabelung und alle Regler auf einmal. Dokumentation
mitcommitten, wenn Bedeutung oder Testablauf sich aendert. Vor einem Branch-
Wechsel nicht gespeicherte Arbeit zuerst committen, sonst kann sie mitwandern.

Nach bestandenem Vergleich die Testversion in main uebernehmen:

```bash
git switch main
git merge --ff-only codex/roll-abstimmung
git tag -a v0.2.1-roll-boden -m "Roll am Boden geprueft"
```

Wenn --ff-only scheitert: nicht erzwingen. Es gibt parallele Aenderungen;
erst Verlauf ansehen und die Zusammenfuehrung bewusst entscheiden.

## 5. Alte funktionierende Version ansehen/wieder testen

```bash
git log --oneline --decorate -10
git switch -c codex/vergleich-alte-version v0.2.0-bench
```

So entsteht ein eigener Branch vom markierten Stand. Alle Firmwaredateien
dieses Stands zusammen hochladen; Code- und Kalibrierformate muessen passen.
MCU-Speicher aendert sich durch Git nicht automatisch. Nach dem Vergleich:

```bash
git switch main
```

Commits auf main rueckgaengig machen, ohne den Verlauf zu loeschen:
git revert COMMIT_ID. Das erzeugt einen neuen Gegen-Commit; bei Konflikten
zuerst klaeren. git reset --hard ist fuer diesen Lernablauf nicht noetig.

## 6. Optional spaeter GitHub als Sicherung

GitHub anmelden, neues **privates** leeres Repository segelflug-controller
anlegen. Dort weder README noch Gitignore automatisch erstellen, weil lokal
schon ein Verlauf existiert. Dann die von GitHub gezeigte URL verwenden:

```bash
git remote add origin https://github.com/DEIN_NAME/segelflug-controller.git
git push -u origin main
git push origin --tags
```

Die Authentifizierung nach GitHub-Anleitung einrichten, kein Passwort/Token
in Code oder Commit speichern. Nach spaeteren Commits: git push.
main ist der gepruefte Stand; laufende Experimente bleiben auf Testbranches.

## Merksatz

Mac speichern -> Diff pruefen -> Hosttests -> MCU-Upload -> Neustart ->
Bodentest -> geaenderte Geraetekalibrierung zurueck auf Mac -> Commit -> optional Push.
