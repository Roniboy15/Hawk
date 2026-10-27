# Flugdaten und Git im bestehenden Repository

Ein separates Daten-Repository ist **nicht erforderlich**. Ausgewaehlte Logs,
Auswertungen und Diagramme koennen weiter unter `docs/testdaten/` liegen und
mit Git versioniert werden. Genau so werden R4 und F1 jetzt gesichert.
Ein zusaetzliches Archiv wird erst interessant, wenn viele Flugserien/Bilder
das Repository unhandlich machen oder Daten unabhaengig von Branchwechseln
verfuegbar sein sollen. Das ist eine Option, keine notwendige Migration.

Nicht jede Datei muss versioniert werden: ausgewaehlte Referenzlaeufe mit
Befunden und Testbeispielen hier, kuenftige Massendaten bei Bedarf separat
sichern. Git-Ignore-Regeln lassen automatisch erzeugte Logs zunaechst aus;
Referenzdateien bewusst auswaehlen. Pro Lauf gehoeren zusammen:

- unveraenderte CSV/Response/JSON, Konsole und Diagramme;
- Firmware-Commit/Branch, bei uncommittierter Firmware zusaetzlich Patch/Kopie;
- tatsaechliche Boardkonfiguration, Logger-/Schemainfo, Lauf-ID und Dateihashes;
- Masse/Schwerpunkt/Trimmung, Wetter, Flugablauf und Zwischenfaelle.

Kalibrierung mitarchivieren, auf dem MCU dabei nichts ueberschreiben. Aeltere
Reports ohne Firmware-Commit ueber Logger-Version und gespeicherte Konfiguration
zuordnen; keinen exakten geflogenen Gitstand erfinden.

## Daten auf einem Branch lassen?

Ja: Datencommit auf eigenem Branch lassen und diesen nicht in den Codebranch
mergen. Neue Branches vom Datencommit enthalten seine Dateien aber bereits.
Git legt gemeinsame Dateien nicht pro Branch als unabhaengige Vollkopie an;
ein Datenbranch trennt auch nicht die gesamte Speicher-/Klonhistorie des Repos.

Getrennte Code-/Datencommits sind sinnvoll. Mit [cherry-pick](https://git-scm.com/docs/git-cherry-pick)
lassen sich einzelne Codecommits uebernehmen, einschliesslich benoetigter
Codevorgaenger, Konfliktpruefung und erneuten Tests. Ein normaler Merge bedeutet
nicht „nur Code-Dateien“: er integriert den Branchverlauf mit dessen Aenderungen.
Gemischte Commits selektiv zu uebernehmen wird schnell unuebersichtlich;
fuer viele kuenftige Flugserien kann ein separates Archiv einfacher werden.

[`.gitignore`](https://git-scm.com/docs/gitignore) betrifft unversionierte
Dateien, entfernt keine getrackten Daten/alten Commits. Bestehende Nachweise
vorerst erhalten. Nach verifizierter Archivkopie spaeter gezielt aus kuenftigen
Codesnapshots entfernen; alte Historie bleibt. Keine Historie umschreiben,
nur um die ersten kleinen Logs loszuwerden. Koordinaten bei Backup/Remotezugriff
bewusst behandeln.

## Jetzt

Besitzer hat Commit und Push auf `codex/manual-flight-tests-20hz` beauftragt:
R4/F1-Nachweise und Firmware/Tests/Dokumentation in getrennten Commits sichern.
Keine Daten verschieben/entfernen, kein weiteres Repository noetig. Ein
normaler Merge dieses Branches wuerde auch die versionierten R4-/F1-Daten
mitnehmen. Getrennte Commits allein machen daraus keinen Firmware-only-Merge.

Nach ueberprueften Bodenergebnissen den zusammenhaengenden Projektstand nach
main integrieren: Firmware **und Tests, Werkzeuge, README, Dokumentation**,
hier auch bewusst versionierte Nachweise. README benennt jeweils implementierte
Funktionen, tatsaechliche Nachweise und offene Tests. Nur Quellcode zu uebernehmen
wuerde Anleitung und Teststand auseinanderlaufen lassen.

GitHub zeigt normalerweise `main`; ein Push des Entwicklungsbranches macht
dessen README nicht zur Startseite des Repositories. Bis zur Integration den
Branch im GitHub-Auswahlfeld waehlen bzw. den direkten Branchlink verwenden.
Optional kann ein separater README-Hinweis auf main zur aktiven Entwicklung
verweisen; heute ist kein main-Merge/-Commit beauftragt.
