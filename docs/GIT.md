# Git fuer den aktuellen Hawk-Stand

Update2026-10-27: weiter auf `codex/manual-flight-tests-20hz`.
Besitzer beauftragt Commit/Push des aktuellen Standes. R4-/F1-Nachweise
und Firmware/Tests/Dokumentation getrennt sichern. Ein separates Daten-Repo
ist optional; ausgewaehlte Logs/Diagramme bleiben hier. Nach main gehoeren
auch README, Tests, Werkzeuge und relevante Dokumentation; normaler Merge
uebernimmt ebenfalls versionierte Daten. [Datenstrategie](DATEN_UND_GIT.md).
Logger0.3.0 hat244 Hosttests, Boardvergleich noch offen. Kein main-Merge
beauftragt; Push auf den Entwicklungsbranch aktualisiert die main-README nicht.
R4/F1 sind als **a3d7ceb** separat gesichert; die anschliessende Aenderung
enthaelt Logger0.3.0 samt Tests, aktueller README und Bedienung.
Folgende Angaben sind historische Schritte.

Update2026-10-25: Logger0.2.0 samt R1..R3 wurde als **0c1e3ba** auf
`codex/response-logger-20hz` gesichert. Der Besitzer hat direkt davon den
neuen Branch **codex/manual-flight-tests-20hz** fuer20-Hz-MANUAL-Datenfluege
beauftragt; er ist jetzt aktiv. main bleibt unveraendert, kein Push/Merge.
Flugsetup und neue Messfluege hier in eigenen Commits sichern, insbesondere
Ruderweg-Aenderungen getrennt vom geprueften Loggercheckpoint.
Nach Fluegen kann dieser Branch geprueft nach main integriert werden; er
enthaelt auch die vorherigen Sensor-/Loggerarbeiten. Merge kombiniert die
Historie; zum Verwenden eines aelteren Standes Branch wechseln und passende
Firmware auf den MCU uebertragen. Git allein aendert das Board nicht.
Die folgende Beschreibung ist der historische Sensor-/Logger-Uebergang.

Sensorabschluss und anschliessender Branchwechsel wurden am 2026-10-20 vom
Besitzer freigegeben. Die folgende Bestandsaufnahme beschreibt den Ausgangsstand
vor diesem Abschlusscommit.
Das vorhandene Repository weiterverwenden, nicht neu klonen oder origin ersetzen.

## Wo wir stehen

- Aktueller Branch: **codex/gps-baro-bringup**, letzter Commit **bbdf934**.
- Der vorherige Tischtestabschluss **913a9e6** ist darin enthalten.
- Lokal zeigt main auf **57a5ed2** und ist Vorfahr des aktuellen HEAD;
  dazwischen liegen sieben Commits, noch ohne den vorbereiteten Abschluss.
- Remote: https://github.com/Roniboy15/Hawk.git. Der gespeicherte origin-Stand
  zeigt dieselben Spitzen; ohne neues Fetch ist das keine Live-Auskunft von GitHub.
- Die uncommittierten Aenderungen enthalten Sensorbefunde, UART-Korrektur,
  vollstaendigen Sensor-RAM-Puffer mit offenem Hardwarecheck sowie Einbauplan.
  Dieser Inhalt wird im freigegebenen Abschlusscommit gesichert; Push und
  Merge sind weiterhin gesonderte, nicht beauftragte Schritte.

Der Sensorbranch umfasst damit auch fruehere Roll-/Nick-/Gier-/Fehlertestarbeit,
die main noch fehlt. Bei einer spaeteren Pull Request den gesamten Unterschied
pruefen, nicht nur die zuletzt angefassten GPS-Dateien.

## Die Begriffe

| Schritt | Bedeutung |
| --- | --- |
| Speichern | Dateiinhalt im Arbeitsordner aendern |
| Stage / git add | Genaue Dateiversion fuer den naechsten Commit auswaehlen; auch bestehende Dateien und Loeschungen |
| Commit | Lokalen zusammenhaengenden Snapshot mit Beschreibung anlegen |
| Branch | Benannten Entwicklungsstand verfolgen; neue Arbeit kann vom aktuellen Commit ausgehen |
| Push | Lokale Commits zum GitHub-Branch uebertragen |
| Fetch | Remote-Verlauf herunterladen, Arbeitsdateien noch nicht zusammenfuehren |
| Pull | Fetch und anschliessende Integration in den gerade ausgecheckten Branch |
| Pull Request (PR) | Vorschlag zur Pruefung/Zusammenfuehrung eines Branches auf GitHub |
| Merge | Branchverlaeufe zusammenfuehren, z.B. Sensorstand nach main |

Keiner dieser Schritte uebertraegt Firmware auf den MCU oder ersetzt einen
Hardwaretest. Ein Commit darf sinnvollerweise auch eine Vorbereitungsfassung
mit klar dokumentierten offenen physischen Tests sichern.

## Empfohlener naechster Ablauf

1. Vorbereiteten Diff samt ausgewaehlten Rohdaten ansehen, 131 Hosttests und
   die offenen Hardwarepunkte in VALIDIERUNG/S3-Auswertung beachten.
2. Nach Besitzerfreigabe passenden Inhalt stagen, `git diff --staged` pruefen
   und auf codex/gps-baro-bringup committen. Vorgeschlagene Nachricht:
   **Sensorchecks auswerten und vollstaendige RAM-Aufzeichnung vorbereiten**.
3. Direkt von diesem neuen Abschlusscommit **codex/manual-flight-logger**
   erstellen. Nicht zuerst auf das aeltere main wechseln. main bleibt dabei
   unveraendert; der Loggerbranch enthaelt alle bisherigen Ergebnisse.
4. Den Logger als eigenen Umfang entwickeln und testen, neue Codeaenderungen
   und spaetere physische Ergebnisse in nachvollziehbaren Commits sichern.

Die dazugehoerigen Befehle gehoeren zum freigegebenen Ablauf. Schema:

```sh
git status --short --branch
git diff
# Passende Dateien explizit mit git add auswaehlen.
git diff --staged
git commit -m "Sensorchecks auswerten und vollstaendige RAM-Aufzeichnung vorbereiten"
git switch -c codex/manual-flight-logger
```

Die Rohdaten enthalten Standortkoordinaten. Vor einem spaeteren Push bewusst
entscheiden, ob diese in das betreffende GitHub-Repository gehoeren; ein
lokaler Commit allein veroeffentlicht sie noch nicht. Keine Zugangsdaten,
zufaelligen Downloads oder leeren Geraetekalibrierungen mitstagen.

## Wann main aktualisieren und was pull dabei tut

Der neue Loggerbranch kann sofort vom Sensorabschluss weiterarbeiten. Ein
Merge nach main muss diesen Fortschritt nicht aufhalten. main erst bewusst
zum dokumentierten Integrationsstand machen; ein Merge ist keine Flugfreigabe.

Wenn der Sensorabschluss zu GitHub soll: den Sensorbranch pushen und eine
Pull Request **codex/gps-baro-bringup -> main** erstellen. Die PR beschreibt
die Ergebnisse und die Grenzen: neuer RAM-Puffer noch nicht physisch bestaetigt,
kein integrierter MANUAL-Fluglogger, Start-/Versorgungsbefunde weiterhin offen.
Vor Merge den gesamten Branchvergleich und Tests pruefen. Push/PR/Merge sind
hier Empfehlungen, kein bereits ausgefuehrter Auftrag.

Nach einem Merge auf GitHub kann die lokale main-Kopie aktualisiert werden:

```sh
# Erst mit sauberem/gesichertem Arbeitsordner wechseln.
git fetch origin
git switch main
git pull --ff-only origin main
git switch codex/manual-flight-logger
```

`pull` auf dem Loggerbranch wuerde nicht einfach main aktualisieren. Es wirkt
auf den gerade aktiven Branch. `--ff-only` verweigert eine unbeabsichtigte
neue Zusammenfuehrung bei auseinanderlaufenden Verlaeufen. Falls es scheitert:
Verlauf ansehen, nicht mit reset/force umgehen.

Alternativ ist nach bewusstem Abgleich ein lokaler Fast-Forward moeglich:

```sh
git switch main
git merge --ff-only codex/gps-baro-bringup
git switch codex/manual-flight-logger
```

Das ist eine Alternative zum obigen PR-Weg, kein zusaetzlich noetiger Schritt.
Bei parallel veraendertem main vorher vergleichen. Bei einem Squash-Merge
entstehen andere Commit-IDs; den davon abhaengigen Loggerbranch anschliessend
bewusst abgleichen, statt geteilte Branchhistorie blind umzuschreiben.
Alte Testbranches vorerst als Vergleich behalten; kein automatisches Loeschen,
kein Force-Push, kein Flug-Release-Tag fuer einen Sensorfunktionstest.

## Version auf dem Modell nachvollziehbar halten

Nach Aenderung: Mac-Dateien speichern, Diff/Hosttests, passende Firmwaremodule
zusammen hochladen, Soft-Reboot, Bodenpruefung, Ergebnis sichern. Eine bestehende
calibration.json beim Upload erhalten und vor Montage-/Kalibrierarbeit separat
herunterladen. Geaenderte Geraetekalibrierung mit Datum/Commit/Montage zuordnen.
Codecommit und Testbericht koennen getrennte Commits sein. Dadurch bleibt klar,
welcher Code getestet wurde und welche Ergebnisse erst spaeter dazu kamen.
