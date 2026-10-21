# Dynamische Tischanzahl und fehlende Tische

Stand: 2026-10-19

## Ausgangspunkt

Der reguläre Zwei-Tisch-Inbetriebnahmeblock ist abgeschlossen. Johannes
bestätigt zuletzt den gemeinsamen Neustart von Vision, Adapter und Sender:
selbstständige Systemrückkehr und ruhiger anschließender Formatdurchlauf.
TD-Version 146 ist manuell gespeichert und erneut geöffnet geprüft.
Einzelbelege: [Lab-Inbetriebnahme](LAB_INBETRIEBNAHME.md).

Neuer Auftrag: Tischzugänge/-abgänge im ROI prüfen sowie in der Learning
Format UI auf fehlende Tische für eine angeforderte Formation hinweisen.

## Bestehendes Verhalten und Entscheidung

Der Adapter hängt neue Tisch-IDs an die bekannte Scene Order an; fehlende
Tracks bleiben für die bestehende Grace von 15 gültigen Vision-Frames
erhalten und werden danach entfernt. Zurückkehrende bekannte IDs behalten
ihren ursprünglichen Platz in der Reihenfolge. Physische Track-Reidentifikation
ist von der Vision abhängig; keine neuen Trackingparameter eingeführt.
Geometrisch gültige veränderte Szenen werden kontinuierlich neu geplant.

Bei ungültiger neuer Anfrage verwirft der Sender weiterhin den ganzen
OSC-Durchlauf. Johannes entscheidet ausdrücklich: letzte gültige Anzeige
sichtbar lassen und in der UI als veraltet kennzeichnen. Dies betrifft die
stehen gebliebene gesamte Anzeige; auch darin enthaltene Source-Werte
werden in abgelehnten Durchläufen nicht neu ausgegeben. Keine ungültige
Formation als gültig ausgeben, keine automatische Änderung von Count,
Gruppen oder Format. Vollständig geleerte Live-Szenen behalten den bereits
geprüften Sonderfall mit Null-Counts und ausgeblendeter alter Darstellung.

## Umgesetzter UI-Hinweis

`layout_runtime_status.py` veröffentlicht den lokalen Status des tatsächlichen
Senders in `data/aisi/state/layout_status.json`. Keine zweite Synthese im
Webserver. Status enthält aktuelle Tischanzahl, Anfrageparameter, Zeitstempel
und Berechnung/aktiv/ungültig/keine Tische. Bei ungültigem Layout wird der
vorhandene Planerfehler unverändert weitergegeben; damit enthält etwa
Discussion 7 die benötigten vier und die vorhandenen zwei Tische.

Der vorhandene Webserver liefert `/layout-status`; die bestehende Seite
fragt den Status jede Sekunde ab und zeigt den Fehler mit dem ausdrücklichen
Hinweis auf die veraltete letzte Anzeige. Keine Seitenneuladung beim
Statuswechsel und keine HTML-Interpretation von Fehlermeldungen. Status einer
anderen Anfrage wird als ausstehend angezeigt; nach 15 Sekunden ohne
Aktualisierung erscheint keine aktuelle Senderrückmeldung. Statusschreiben
maximal einmal pro Sekunde bei identischem Inhalt, Änderungen sofort;
atomare Dateien und fehlertolerant gegenüber Windows-Dateisperren.
OSC-Verträge und Layoutregeln bleiben unverändert.

Sender und Lernformat-Server gezielt neu gestartet. Aktuelle Logs im
Lab-Debugordner heißen `sender.status.*.log` und `learning.status.*.log`;
Vision, Adapter, Study-Control und TD bleiben aktiv.

## Prüfung und nächster Raumtest

- 47 fokussierte Tests bestanden: Status/Anfragebindung/Fehler/Recovery,
  Statusalter und Schreibfehler, bestehende UI/OSC-/Adaptertests sowie
  spontane neue Tisch-ID, Abgang nach Grace und Wiederkehr in stabiler Order.
- Live-HTTP-Integration bestanden: Statuspanel vorhanden, Discussion 7 bei
  zwei Tischen meldet „Discussion benötigt für 7 Personen 4 Tische; nur 2
  verfügbar.“; Rückkehr auf Discussion 4 meldet selbstständig `ready` und
  „Layout aktiv.“. Beide Anforderungen durch tatsächlichen Sender verarbeitet.
- Endzustand Discussion 4, zwei Gruppen als gespeicherter Parameter,
  Chairs On und 100 %. Physischer Zugang/Abgang eines dritten Tisches und
  visuelle UI-Prüfung stehen noch aus.

Gebündelt im Raum: Browserseite einmal neu laden, dritten Tisch vollständig
in den ROI bringen und wieder entfernen, automatische Tischzahl/Planung und
stabile Zuordnung beobachten. Danach in der UI Discussion 7 wählen:
Hinweis auf vier benötigte Tische und veraltete letzte Anzeige prüfen,
anschließend wieder Discussion 4; Warnung muss verschwinden. Nur eine
gemeinsame Rückmeldung, sofern kein Fehler den Ablauf unterbricht.

## Live-Ergebnis

Johannes bestätigt den gebündelten Raumtest: Dritter Tisch wird beim
Hinein-/Hinausschieben korrekt berücksichtigt. Discussion 7 zeigt bei
fehlenden Tischen den Hinweis; bei Rückkehr zu vier Personen verschwindet
er. Ein vierter hineingeschobener Tisch wird ebenfalls erkannt und lässt
die Fehlermeldung automatisch verschwinden. Damit sind Tischzahlwechsel
und Auflösung einer zuvor ungültigen Anfrage durch zusätzliche reale Tische
live bestätigt. Dies ist noch keine vollständige geometrische/physische
Validierung aller Vier-Tisch-Discussion-Counts oder Tracking-Verdeckungen.

Lesender Endzustandsabgleich nach Rückmeldung: Discussion 6, drei erkannte
Tische (`table_00`, `table_01`, `table_02`), sechs Chairs, 100 %, Status
`ready`/„Layout aktiv.“. Senderprotokoll bestätigt drei Tische/sechs Chairs,
Fehlerlog leer. Keine Umschaltung im Rahmen des Abschlussabgleichs.

Dieser Prüfblock ist abgeschlossen. Nächster eigenständiger Block:
Vier-Tisch-Discussion einschließlich Stufenwechsel 6 ↔ 7 und zusätzlicher
Eckplätze prüfen, sobald vier Tische für diesen Durchlauf im ROI stehen.

## Vier-Tisch-Discussion: Stufenwechsel 6 ↔ 7

Johannes fordert die gebündelte Prüfung an und bringt den vierten Tisch
erneut in den ROI. Zunächst weiterhin drei Tische beobachtet, ohne
Umschaltung; danach vier Tische stabil erkannt:
`table_00`, `table_01`, `table_02`, `table_04`. Die neue ID wird nicht als
Wiederkehr einer früheren ID behauptet. Offline-Preflight mit dieser realen
Source besteht für Discussion 6 und 7: vier Ziele, sechs/sieben Chairs,
rund 0,35/0,33 s. Durchlauf 6 → 7 → 6 mit je zehn Sekunden aktiviert.
Bei sechs Personen Zweiergruppe plus zwei Parktische, bei sieben vier
aktive Tische im Rechteck; visuelle Gesamtbestätigung noch offen.

Durchlauf technisch abgeschlossen: alle drei Stufen melden `ready` mit
vier verfügbaren Tischen, Sender bestätigt 6/7/6 Chairs, Fehlerlog leer.
Scene Order bleibt durchgehend `table_00, table_01, table_02, table_04`.
Endzustand Discussion 6 mit vier realen Tischen. Visuelle Gesamtbewertung
von Topologiewechsel, Parken/Rückkehr und Chair-Altlasten angefragt.

Johannes bestätigt den gesamten Durchlauf als passend: Wechsel Zweiergruppe
mit Parktischen → Vier-Tisch-Rechteck → zurück ohne beanstandete Altlasten
oder Unruhe. Vier-Tisch-Discussion 6 ↔ 7 damit für diese Source technisch
und live bestanden. Endzustand bleibt Discussion 6 mit vier realen Tischen.
Nächster eigener Prüfblock: Discussion 8–12 einschließlich Eckplätze.

## Vier-Tisch-Discussion: Counts 8–12 und Eckplätze

Auf Johannes' Auftrag vier vorhandene reale Tische beibehalten und alle
Counts 8–12 auf derselben frischen Source vorgeprüft: vier Tischziele,
passende Chair-Anzahl, exakt gleiche Tischziele innerhalb dieser Stufe.
Offline erste Anfrage rund 0,36 s, weitere Counts 0,002–0,004 s.
Gebündelte Live-Folge 8 → 9 → 10 → 11 → 12 → 8 mit acht Sekunden je Count.
Erwartung: acht Längsseitenplätze, zusätzlich ein bis vier Eckplätze;
bei zehn zuerst gegenüberliegende Ecken. Rückkehr zu acht prüft Entfernen
der Eckplätze. Visuelle Gesamtbestätigung noch offen.

Durchlauf technisch beendet: Status in allen sechs Stufen `ready`, jeweils
vier verfügbare Tische; Scene Order durchgehend
`table_00, table_01, table_02, table_04`. Sender bestätigt steigende Chair-
Counts, Fehlerlog leer. Endzustand Discussion 8. Gemeinsame Sichtbewertung
von Eckplatzverteilung und vollständigem Rückwechsel angefragt.

Johannes bestätigt Discussion 8–12 einschließlich Rückkehr zu acht:
Eckplätze plausibel ergänzt und vollständig entfernt, ruhiges Bild,
keine hängen gebliebenen Elemente. Dieser Prüfblock ist bestanden.

Nächster gebündelter Vier-Tisch-Block: Groupwork 8/4 → 12/4 → 12/2 → 8/2,
danach Discussion 8. Erwartet vier getrennte Gruppen, danach zwei Pairs;
vor Live-Umschaltung alle Anfragen auf derselben Source vorprüfen.

Technisch bestanden: alle fünf Vorprüfungen (0,32–0,59 s) und Live-Stufen
ready, passende Counts im Senderprotokoll, Fehlerlog leer. Vier Tisch-IDs
durchgehend in stabiler Scene Order. Endzustand Discussion 8, vier Tische,
Chairs On/100 %. Gemeinsame visuelle Bewertung der Groupwork-Gruppen/
Pairs und Rückkehr zu Discussion noch offen.

Johannes bestätigt den Groupwork-Durchlauf vollständig: vier getrennte
Gruppen/zwei Pairs plausibel, Chair-Wechsel vollständig, ruhiges Bild.
Prüfblock bestanden. Weitere Live-Prüfungen auf seinen Auftrag pausiert,
weil `floor_tabletop_control` (Container COMP) keine blauen Source-Konturen
mehr zeigt. Screenshot zeigt Ziele/Chairs/Pfeile ohne Source-Konturen.
Gespeicherte Version 146 enthält weiterhin Source/Motion-Auswahl im
Kontroll-Render TOP; dies belegt nicht den aktuellen Live-Ausdruck oder
den Geometrie-/Materialzustand nach den Tischzahlwechseln.
Lesende Diagnose `td_builders/inspect_layout_control_sources.py` vorbereitet,
Syntax geprüft: erfasst Auswahl/Kamera/Lichter/Composite und aktuelle
Source-Geometrien/Primitive/Material. Kein Force-Cook, keine Graphänderung.
Live-Bericht unter `data/aisi/debug/layout_control_sources.json` noch offen.

Live-Bericht gelesen: vier fehlerfreie Source-Geometrien, jeweils vier
Konturprimitive/16 Punkte, renderbar und korrektes blaues Study-Material.
Der Kontroll-Renderer liefert für seine dynamische Geometry-Expression
jedoch `None`, während der reguläre Tabletop-Renderer die gleichen Source-
Geometrien auflöst. Konkrete Leerstelle damit im Kontroll-Renderer nachgewiesen;
Ursache der leeren dynamischen Expression nach Tischzahlwechseln noch nicht
abschließend erklärt. Keine Material-/Geometriereparatur erforderlich.

`repair_layout_control_selection.py` ersetzt nur den Geometry-Parameter
dieses vorhandenen Render TOP durch native absolute Pfade für Source und
Tabletop-Motion der fünf unterstützten Slots. TD löst vorhandene Slots
selbst auf; keine Python-Operatorabfrage/Type-Filterung mehr in dieser
Auswahl. Auch bestehende Nicht-Rect-Source-Geometrien würden damit in dieser
isolierten Kontrollansicht angezeigt. Keine neue Geometrie, keine Kamera-/
Material-/Composite-/Projektorausgabeänderung. Parameterzustand in Sitzung
gesichert, Rücknahme enthalten; prüft Auswahl nach Setzen und rollt bei
fehlenden Sources zurück. Kein Force-Cook/Speichern. Zwei fokussierte Tests
bestanden. Erzeugungs-/Updatehelfer auf dieselbe native Auswahl angepasst,
damit ein späteres Update die dynamische Expression nicht zurückbringt.

Manuell im TD-Python-Textport:

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\repair_layout_control_selection.py', encoding='utf-8').read(), 'repair_layout_control_selection.py', 'exec'))
```

Rücknahme: `restore_layout_control_selection(op)`. Vier blaue Konturen in
der Kontrollansicht visuell prüfen; physische Projektion soll unverändert
bleiben. Live-Ausführung noch offen. Endzustand laut State-Datei Groupwork
8/2 (vom vorher geplanten Discussion-Endzustand abweichend); nicht umgeschaltet.

Johannes bestätigt die manuelle Auswahlkorrektur: vier blaue Source-
Konturen in `floor_tabletop_control` sichtbar und folgen den Tischen,
Projektorausgabe unverändert. Reparatur für den aktuellen Stand bestanden;
neue manuelle Speicherung/erneutes Öffnen nach dieser Korrektur noch offen.
Nächster angefragter gebündelter Block: fünften Tisch in ROI aufnehmen,
dann Discussion 12 → 13 → 14 → 15 → 12 inklusive Pentagon und Rückkehr.
Vorher keine Count-Umschaltung; auf stabile Erkennung von fünf Tischen
warten und alle Anfragen auf der tatsächlichen Source vorprüfen.

## Fünf-Tisch-Discussion: Rechteck ↔ Pentagon

Johannes meldet fünften Tisch im ROI. Fünf Tische anschließend stabil
erkannt: `table_00`, `table_01`, `table_02`, `table_04`, `table_05`.
Alle Counts 12–15 auf derselben tatsächlichen Source vorgeprüft: fünf
Tischziele und passende Chair-Anzahl. Count 12 rund 1,98 s, Count 13 rund
1,63 s; weitere Pentagon-Counts rund 0,003–0,004 s, exakt gleiche Tischziele
bei 13/14/15. Live-Folge 12 → 13 → 14 → 15 → 12 mit zehn Sekunden je
erfolgreich berechneter Stufe gestartet. Bei zwölf vier aktive Tische plus
Parkziel, ab dreizehn fünf aktive Tische im Pentagon. Gemeinsame visuelle
Prüfung einschließlich Source-Konturen nach fünftem Tischzugang offen.

Durchlauf technisch abgeschlossen: alle fünf Stufen ready mit fünf
verfügbaren Tischen; Sender zeigt passende 12/13/14/15/12 Chair-Counts,
Fehlerlog leer. Scene Order durchgehend unverändert. Endzustand Discussion
12, fünf reale Tische, Chairs On und 100 %. Gemeinsame Sichtbewertung von
Pentagon/Zwischenplätzen, Park-Rückkehr und fünf folgenden Source-Konturen
noch offen. Keine zusätzlichen TD-Helfer während dieses Durchlaufs ausgeführt.

Johannes bestätigt den gesamten Fünf-Tisch-Discussion-Durchlauf: Pentagon/
Plätze plausibel, Rückkehr zum Rechteck mit Parktisch sauber, alle fünf
Source-Konturen folgen und ruhiges Bild. Damit Discussion 12 ↔ 13–15 live
bestanden; auch Kontrollviewer-Auswahl nach fünftem Tischzugang bestätigt.
Nächster gebündelter Block: Input 4 → 8 → 10 → 12 → 15 → 4 bei fünf
verfügbaren Tischen, mit Preflight vor jeder neuen Live-Folge.

Fünf-Tisch-Input technisch abgeschlossen: alle fünf unterschiedlichen
Anfragen vorgeprüft (erste ca. 1,76 s, weitere 0,004–0,016 s), danach
4/8/10/12/15/4 jeweils ready und fünf Tischziele bei passendem Chair-Count.
Scene Order durchgehend `table_00, table_01, table_02, table_04, table_05`,
Fehlerlog leer. Endzustand Input 4, fünf verfügbare Tische, Chairs On/100 %.
Gemeinsame visuelle Bestätigung von Aktiv-/Parkwechsel, Verdichtung,
15 sichtbaren Chairs und vollständiger Rückkehr noch offen.

Johannes bestätigt den Fünf-Tisch-Input-Durchlauf vollständig: Park-/Aktiv-
wechsel und Verdichtung plausibel, alle 15 Chairs sichtbar, beim Rückwechsel
keine alten Kreise und ruhiges Bild. Prüfblock bestanden. Aktueller
Endzustand unverändert Input 4 mit fünf verfügbaren Tischen.

## Noch offene Prüfblöcke

1. Fünf-Tisch-Groupwork: fünf Gruppen, Pairs/Singletons, hohe Belegung,
   Parken und Rückkehr; bisher nur Zwei-/Vier-Tisch-Groupwork live geprüft.
2. Gemeinsamer Fünf-Tisch-Format-/Moduswechsel und Abgang/Rückkehr eines
   aktuell benötigten Tisches mit UI-Warnung/Recovery. Fehlende Tischzahl
   für eine neu gewählte Anfrage und Zugang zusätzlicher Tische sind bereits
   bestätigt, aber kein vollständiger aktiver Verlust-/Wiederkehrdurchlauf.
3. Tracking bei Verdeckung, enger Begegnung/Kreuzung und Wiedererkennung.
   Keine Trackingparameter ohne konkreten reproduzierten Fehler ändern.
4. Bewegte reale Tische, Maskenränder, ROI-Ränder und Projektorüberlappung
   formatübergreifend prüfen; bestehende Kalibrierung unverändert lassen.
5. Kontrollviewer-Korrektur als neue TD-Version manuell sichern, erneut
   öffnen und abschließenden Start aus beendetem Lab-Zustand inklusive
   Bedienoberflächen prüfen. Gemeinsamer Python-Neustart ist bereits
   bestanden, TD/Study-Control waren dabei jedoch offen.

Die vollständige Study-Session (Familiarization, pilot_v8, Bedingungen,
Binding, Arrival und Logs) ist ein separater noch offener Validierungsblock.
Teiltransformationsstärken und Summit/Sprint bleiben separate Folgearbeit;
die heutigen Formatdurchläufe nutzten 100 % und Rect-Tische.

## Fünf-Tisch-Groupwork

Auf Johannes' Auftrag alle fünf Tische im ROI beibehalten und folgende
Anfragen auf derselben aktuellen Source vorgeprüft:
5/5, 15/5, 15/2, 4/1, 10/5 (Personen/Gruppen). Alle fünf bestehen mit
fünf Tischzielen und passendem Chair-Count; Zeiten ca. 0,97/1,08/2,26/3,01/
1,00 s. Gebündelte Live-Folge mit zehn Sekunden Beobachtungszeit nach
gültigem Status gestartet. Abgedeckt: fünf kleine Gruppen, fünf
Dreiergruppen, zwei große Gruppen mit Pairs, geringe Belegung mit
Parktischen und Rückkehr zu fünf Gruppen. Endzustand 10/5 vorgesehen.
Visuelle Gesamtbestätigung noch offen.

Fünf-Tisch-Groupwork technisch abgeschlossen: 5/5 → 15/5 → 15/2 → 4/1 →
10/5 durchlaufen, alle Anfragen ready mit fünf erkannten Tischen, passende
Chair-Counts, Fehlerlog leer. Durchgehend stabile Scene Order
`table_00, table_01, table_02, table_04, table_05`. Endzustand Groupwork 10/5,
Chairs On/100 %. Visuelle Gesamtrückmeldung zu Gruppen/Pairs, hoher Belegung,
Park-/Aktiv-Rückkehr und Source-Konturen noch offen.

Johannes bestätigt Fünf-Tisch-Groupwork vollständig: Gruppen/Pairs plausibel,
hohe Belegung gut erkennbar, Park-/Aktiv-Rückkehr sauber, alle Sources
folgen, keine alten Elemente und ruhiges Bild. Prüfblock bestanden.
Nächster gemeinsamer Fünf-Tisch-Integrationstest: Input 15 → Discussion 15 →
Groupwork 15/5, dabei alle 15 Chairs Off/On, danach Discussion 8.
Vorprüfungen bestehen; danach manuell Tracking → AISI prüfen.

Gemeinsamer Format-/15-Chair-Off/On-Durchlauf technisch abgeschlossen:
alle Anfragen ready bei fünf Tischen, stabile Scene Order und Fehlerlog leer.
Chair-Sichtbarkeit am Ende wieder On, Discussion 8 aktiv. Gemeinsame
visuelle Rückmeldung und manueller Tracking → AISI-Check bei fünf Tischen
noch offen. Keine TD-Änderungen in diesem Durchlauf.

Johannes bestätigt den gemeinsamen Fünf-Tisch-Integrationstest: alle
Formatwechsel, 15 Chairs Off/On und Tracking → AISI sauber; danach Ziele,
Pfeile und acht Chairs wieder vorhanden, ruhiges Bild. Prüfblock bestanden.

## AISI-Bodenpfeile bis Zielmittelpunkt

Neuer expliziter Auftrag: Bodenpfeile sollen ebenfalls bis zum Mittelpunkt
des Ziel-Tisches reichen statt an dessen Außenkontur zu enden.
`repair_aisi_floor_arrow_endpoint.py` ersetzt ausschließlich den bisherigen
Target-Ray-Schnittpunkt durch den Target-Mittelpunkt im bestehenden
Floor-Pfeil-Callback, in Template und aktuellen Instanzen. Source-Kantenstart,
Overlap-Ausblendung und der Arrival-/Spitzen-Wrapper bleiben erhalten;
Study-/Tabletop-Pfeile, Projektionsstufen und Layouts unverändert.
Sitzungssicherung, Vorabprüfung und Rücknahme enthalten; kein Force-Cook
und keine Speicherung. Zehn fokussierte Pfeiltests und 576 Fälle auf den
drei realen gespeicherten Floor-Callbacks aus Version 146 bestanden:
Zielende korrekt, Source-Start/Sichtbarkeit erhalten, idempotent.

Manuell im TD-Python-Textport:

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\repair_aisi_floor_arrow_endpoint.py', encoding='utf-8').read(), 'repair_aisi_floor_arrow_endpoint.py', 'exec'))
```

Rücknahme: `restore_aisi_floor_arrow_endpoint(op)`. Live-Endpunktprüfung
und neue manuelle TD-Sicherung nach Viewer-/Floor-Pfeilkorrektur noch offen.

Johannes meldet anhand zweier Screenshots fehlende Bodenpfeile trotz
hinreichend entferntem Target-Mittelpunkt. Ursache im bestehenden Callback
reproduziert: `visible = not overlap` blendet bei jeder Tischüberschneidung
aus, auch wenn der Target-Mittelpunkt außerhalb des Source-Footprints liegt.
Der Endpunkt-Helfer wurde erweitert: Sichtbarkeit richtet sich nun nach der
vorwärts gerichteten Strecke zwischen Source-Kantenschnitt und Target-Mitte
(> 0,002 TD, vorhandene Study-Mindestlänge), statt nach globalem Overlap.
Liegt die Mitte im Source-Tisch, bleibt der Bodenpfeil verborgen; der
Tabletop-Pfeil führt die innere Strecke. Arrival-Wrapper und schrumpfende
Spitzen bleiben erhalten. Keine neue Footprint-Geometrie.

Elf fokussierte Tests bestanden. 96 Fälle auf drei echten gespeicherten
Callbacks geprüft; Teil-Overlap mit früher fehlendem Pfeil reproduziert
und korrigiert, Source-Start unverändert, Target-Mitte als Ende, Innenziel/
Arrival weiterhin verborgen. Upgrade aus Original und bereits angewandtem
Endpunkt-Fix sowie Idempotenz geprüft. Denselben Textport-Aufruf erneut
ausführen; Live-Prüfung offen. Vorhandene Sitzungssicherung bleibt erhalten
und stellt bei Rücknahme den Zustand vor dem ersten Endpunkt-Fix wieder her.

Johannes bestätigt die erweiterte Bodenpfeilkorrektur live: Pfeile auch bei
Teilüberlappung sichtbar und bis Zielmittelpunkt, ruhiges Bild.
Nächster gebündelter Fehler-/Recovery-Test: Discussion 15 bei fünf Tischen
aktivieren, einen benötigten Tisch aus ROI entfernen, UI-Ablehnung mit vier
Tischen/veralteter letzter Anzeige beobachten, Tisch wieder hineinbringen.
Automatische Erholung auf ready/fünf Tische überwachen; danach Discussion 8
wiederherstellen. Physischer Ablauf durch Johannes, keine Trackingparameter
geändert. Vorprüfung Discussion 15 besteht.

Fehler-/Recovery-Durchlauf technisch bestanden: zunächst fünf Tische/ready,
danach vier Tische/invalid mit „Discussion benötigt für 15 Personen 5 Tische;
nur 4 verfügbar.“, nach Rückkehr fünf Tische/calculating → ready. Gültige
Erholung sechs Sekunden stabil beobachtet, dann Discussion 8 gesetzt.
Der kurz beim Tischabgang beobachtete Status „ready/5“ stammt noch aus dem
vorigen Senderdurchlauf; anschließend korrekte invalid/4-Rückmeldung.
Visuelle Gesamtbestätigung von veralteter Anzeige, Warnung und Rückkehr
noch offen. Keine automatischen Änderungen fachlicher Eingaben während
der ungültigen Phase; Rückstellung auf acht erst nach gültiger Erholung.

Endzustandsabgleich: IDs `table_01, table_02, table_04, table_05, table_06`;
die zuvor vorhandene `table_00` ist nach dem längeren Abgang nicht erhalten.
Rückkehr/Neuberechnung mit neuer Track-ID funktioniert; Wiedererkennung
derselben physischen Identität über diese Unterbrechung ist nicht nachgewiesen.
Trackingparameter unverändert. Senderfehlerlog leer, Discussion 8 ready.

## Live-Sources bei ungültigem Zielvorschlag

Johannes präzisiert nach dem Abgangstest: die letzte Source-Position des
fehlenden Tisches darf nicht weiter angezeigt werden. Nur der veraltete
Zielvorschlag soll bestehen bleiben. Laufende Source-Anzeige davon getrennt.

Sender ergänzt `/table/<index>/source_available` als Integer für fünf Slots.
Bei abgelehnter Layoutanfrage bleiben Ziel-/Chairdaten unverändert, aktuelle
Source-Posen werden aber anhand der IDs des letzten gültigen Vorschlags
in denselben Slots aktualisiert. Fehlende IDs erhalten Verfügbarkeit 0;
nachrückende/neue IDs dürfen keinen alten Zielslot stillschweigend übernehmen.
Ohne bekannte gültige Slotzuordnung Verfügbarkeit 0 statt erfundener Zuordnung.
Live-Occupancy- und bestehende Study-Track-Kanäle bleiben auch während der
Ablehnung frisch. Bestehende Koordinaten-/Rotationskonventionen unverändert.
Bei neuer gültiger Planung wird Slotzuordnung wieder aus Scene Order übernommen.

TD-Helfer `repair_aisi_source_presence.py` ergänzt ausschließlich die
Render-Sichtbarkeit der vorhandenen Source-/Floor-Motion-/Tabletop-Motion-
Geometrien in Template und Instanzen um die Source-Verfügbarkeit. Alte
Sichtbarkeitsregeln bleiben als UND-Bedingung erhalten, Ziele/Chairs und
Projektionsparameter unberührt. Fehlende Source und ihre Pfeile verschwinden,
erkannte Sources bleiben beweglich. Sitzungssicherung/Rücknahme enthalten;
kein Force-Cook und keine Speicherung. Bestehende Tracking-Grace unverändert;
Ausblenden erfolgt, sobald der Adapter die Tisch-ID tatsächlich entfernt.

51 fokussierte Tests bestanden, insbesondere fehlende ID in altem Slot,
weiterer erkannter Tisch ohne Slotverschiebung, keine Zielkanaländerungen,
Vorzeichen, unbekannte Slotzuordnung und Erhalt bisheriger Sichtbarkeit.
Sender/UI neu geladen, Logs `sender.presence.*`/`learning.presence.*`.
Zusätzlich gestarteter, nicht auf Port 8080 lauschender UI-Prozess beim
Neuladen bereinigt; alte Startbefehle gesichert. Neuer Sender läuft fehlerfrei,
UI-Text unterscheidet nun ausdrücklich veraltete Ziele von Live-Sources.

Manuell im TD-Python-Textport:

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\repair_aisi_source_presence.py', encoding='utf-8').read(), 'repair_aisi_source_presence.py', 'exec'))
```

Rücknahme: `restore_aisi_source_presence(op)`. Live-Anwendung und erneuter
gebündelter Abgang-/Rückkehrtest noch offen. Neue TD-Sicherung ebenfalls offen.

Johannes bestätigt die manuelle Helferausführung und den selbst durchgeführten
Abgang-/Rückkehrtest vollständig als funktionierend. Live-Source-Ausblendung
und automatische Rückkehr bei erhaltenem veraltetem Zielvorschlag damit
für diese Stichprobe bestanden. Keine erneute automatisierte Wiederholung
erforderlich. Neue manuelle TD-Sicherung inklusive Kontrollviewer-, Floor-
Pfeil- und Source-Verfügbarkeitskorrekturen weiterhin nicht bestätigt.

Johannes bestätigt am 2026-10-19 eine neue manuell gespeicherte TD-Version
mit anschließendem erneutem Öffnen: alle jüngsten Live-Korrekturen funktionieren
weiterhin. Versionsnummer/Dateipfad noch nicht erfasst; Version 146 ist deshalb
nicht als diese neue Sicherung auszugeben. Nächster gebündelter Prüfblock:
Verdeckung, Wiedererkennung und enge Tischbegegnung. Vor Beginn Discussion 8,
vier erkannte Tische, Status ready, Sender-Fehlerlog leer. Raumprüfung dieses
Robustheitsblocks noch offen; keine Trackingparameter geändert.

Gebündelte Tracking-Robustheitsprüfung am 2026-10-19 durch Johannes im Raum
bestanden: Nach Verdeckung, enger Begegnung und Abgang/Rückkehr folgen alle
Source-Konturen wieder korrekt. Keine vertauschten oder eingefrorenen Konturen,
ruhiges Bild. Qualitative Stichprobe; Erhalt derselben Track-ID über längere
Abwesenheit nicht nachgewiesen. Anschließender Laufzeitcheck: Discussion 8,
vier Tische, ready, Sender-Fehlerlog leer. Trackingparameter unverändert.
Nächster offener Block: physische Projektion/Masken an ROI-Rändern und in
der Projektorüberlappung; Kalibrierung bleibt geschützt.

Projektions-/Maskenblock am 2026-10-19 durch Johannes im Raum bestanden:
Auch in der Projektorüberlappung und an ROI-Rändern saubere Konturen und
Helligkeit, keine Bodenpfeile auf Tischflächen, ruhiges Bild. Qualitative
Stichprobe; Kalibrierung, Homographien und Edge-Blend nicht verändert.
Laufender TD-Prozess öffnet laut CommandLine die manuell gesicherte Datei
`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.149_lab_layout_validated.toe`.
Damit ist der zuvor unbekannte Versionspfad erfasst. Nächster Block:
vollständiger Anwendungs-Wiederanlauf einschließlich TD und Bedienoberflächen,
kein Windows-Neustart. Vorhandene Startargumente bleiben maßgeblich.

## Abschluss der Lab-Inbetriebnahme — 2026-10-19

Johannes bestätigt den vollständigen Anwendungs-Wiederanlauf einschließlich
TouchDesigner und Bedienoberflächen im Raum: Sources folgen, alle Formatwechsel
und Tracking → AISI funktionieren sauber, keine alten Elemente, ruhiges Bild.
Der Inbetriebnahmeblock ist damit auf ausdrücklichen Auftrag abgeschlossen.
Gesicherter TD-Prüfstand: `AISI_v2.149_lab_layout_validated.toe` im bekannten
physischen TouchDesigner-Verzeichnis. Kein erneuter Helferaufruf erforderlich.
Abschlusscheck: Discussion 8, vier erkannte Tische, Status ready; alle fünf
`full.*.stderr.log` leer. Dokumentationsdiff geprüft; keine neue Codeänderung.

Abgedeckt sind die dokumentierten Rect-Stichproben mit zwei bis fünf Tischen,
Input/Discussion/Groupwork, Chairs/Moduswechsel, dynamischer Tischanzahl,
veraltetem Zielvorschlag mit aktuellen Sources, Verdeckung/enger Begegnung,
ROI-Rändern/Projektorüberlappung und Wiederanlauf. Keine Vollmatrix oder
Identitätserhaltung über beliebig lange Abwesenheit behauptet. Kalibrierung,
Homographien, Edge-Blend und Layout-Regeln im Inbetriebnahmeblock unverändert.
Separat offen bleibt die vollständige Study-/Pilot-Validierung; ein Windows-
Neustart ist nicht Bestandteil des bestätigten Anwendungs-Wiederanlaufs.
