# Lab-Inbetriebnahme am 2026-10-19

Aktueller gespeicherter Prüfstand nach Folgeblock am 2026-10-21:
`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.151_tabletop_targets_validated.toe`.
Durch Johannes gespeichert, erneut geöffnet und physisch bestätigt: Sources
folgen flüssig, ausschließlich eigene Tabletop-Zielkonturen. Stabile Vorschläge,
Formatwechsel, Abgang/Rückkehr, Chairs Off/On und Tracking → AISI bestanden,
Boden unverändert. Folgeblock abgeschlossen; 125 fokussierte Tests bestanden.
Git-Übergabe des Folgeblocks am 2026-10-26 auf
`codex/lab-inbetriebnahme-20261021`, anschließend an `cac6365`.
Frühere Abschnitte beschreiben den historischen Verlauf; der verworfene
Renderzweig-Helfer und sein Versuchstest werden nicht versioniert. Produktiver
Tabletop-Helfer ist ausschließlich `clip_aisi_tabletop_targets.py`.

## Geprüfter Startpfad

Kamera → `.venv_yolo` / `src.vision.tools.run_vision_pipeline` →
`data/vision/live/current_room_rect.jsonl` → `.venv` /
`aisi.app.vision_live_to_aisi_scene` →
`data/aisi/scenes/live/vision_live_scene.json` → `.venv` /
`aisi.app.sim_scene_to_osc` → OSC `127.0.0.1:9000` → TouchDesigner.

Bereits laufende Vision und Scene-Adapter wurden weiterverwendet. Der
Lernformat-Server läuft auf Port 8080; Study-Control bleibt zur Moduswahl
bestehen. Johannes bestätigt MODE AISI. TouchDesigner 2022.29850 hat
`AISI_v2.144_coherent_chairs_validated.toe` geöffnet und belegt UDP-Port 9000.
Die Datei und alle Kalibrierungs-/Projektionsparameter wurden nicht verändert.
Es werden keine automatischen Fensteraufnahmen verwendet.

## Behobene Betriebsblockade

Der vorhandene Sender lief mit `--tracking-only`; dadurch wurden weder
Layout-Synthese noch synthetische Chairs ausgeführt. Zusätzlich war
`adaptive_layout_preview` im Lernformat-State ausgeschaltet.

Am 2026-10-19 um 10:28 Uhr wurde ausschließlich diese Sender-Prozesskette
ersetzt und die Vorschau aktiviert. Genau eine Sender-Prozesskette ist
nachgewiesen; die zwei Python-Prozesse sind Windows-venv-Eltern-/Kindprozess.
Vision, Adapter, Lernformat-Server und Study-Control wurden nicht neu gestartet.

Aktueller Senderbefehl aus dem Repository-Verzeichnis, mit `PYTHONPATH=src`:

```powershell
.\.venv\Scripts\python.exe -u -m aisi.app.sim_scene_to_osc --scene data/aisi/scenes/live/vision_live_scene.json --study-active-binding data/aisi/state/study_active_track.json --study-table-tracks-binding data/aisi/state/study_table_tracks.json --require-fresh-live-scene --host 127.0.0.1 --port 9000 --interval 0.05
```

Diesen Befehl nur nach Beenden des bestehenden Senders verwenden. Für einen
Kaltstart enthält `scripts/run_current_room_vision_to_osc.ps1` den passenden
Vision-/Adapter-/Layout-Pfad, startet aber weder Lernformat-Server noch
Study-Control und aktiviert die Teilnehmer-Vorschau nicht selbst.
`scripts/run_sim_pipeline.ps1` verwendet dagegen die Room-Editor-Szene.
Beide Launcher nicht zusätzlich zur laufenden Pipeline ausführen.

Lokale Sicherung und Senderprotokolle:
`data/aisi/debug/lab_integration_20261019_102845/`.
`learning_format.before.json` sichert den früheren State;
`sender.before.json` enthält die frühere Tracking-only-Prozesskette samt
Argumenten. Für eine Rückkehr zum bisherigen Tracking-/Study-Betrieb den
Layout-Sender ersetzen, den gesicherten Tracking-only-Befehl verwenden und
bei Bedarf den vorherigen Lernformat-State wiederherstellen. Ein Moduswechsel
in Study-Control allein schaltet den Python-Sender nicht auf Tracking-only um.

## Nachweise und offene Prüfung

- Python 3.12.6, erforderliche AISI-Imports und CUDA-Verfügbarkeit geprüft.
- 39 fokussierte Tracking-/Adapter-/Lernformat-/Launcher-Tests bestanden.
- Sieben Groupwork-Vorschautests bestanden; hierfür `PYTHONPATH=src;tests`
  setzen, da der Test eine benachbarte Testdatei importiert.
- Aktuelle Live-Szene enthält zwei Rect-Tische. Offline ergeben Input,
  Groupwork und Discussion bei vier Teilnehmenden jeweils zwei Ziele und
  vier Chairs. Lokaler OSC-Recorder bestätigt Indexbindung und negierte
  Source-/Target-Rotationen; dabei keine Netzwerkpakete versendet.
- Laufender neuer Sender meldet frische Szene, Groupwork, zwei gesendete
  Tische und vier Chairs; Fehlerprotokoll leer. Dies belegt noch nicht den
  Empfang einzelner Kanäle oder die korrekte physische Projektion.
- Sichtprüfung durch Johannes angefragt. Einzelvalidierung der anderen
  Formate und anschließender gemeinsamer Formatwechsel-Check bleiben offen.

## Befund nach erster Raumprüfung: AISI-Positionen auf beiden Achsen vertauscht

Johannes bestätigt zwei Zielkonturen und vier Chairs, meldet aber gespiegelte
Ausgabe. Blaue Source-Konturen sind in `floor_tabletop_control` (Container COMP)
sichtbar, fehlen jedoch im Raum und am Projektorausgang.

Eine ausschließlich temporäre Expansion der gespeicherten Version 144 zeigt:
`tables_active_callbacks` (Text DAT) und
`chairs/chairs_active_callbacks` (Text DAT) innerhalb von
`comp_layout_proposal` verwenden `tx=(x−250)*0.0052`, `ty=(250−y)*0.0052`.
Tracking und physische Tischmasken verwenden dagegen
`tx=(250−x)*0.0052`, `ty=(y−250)*0.0052`. Beide Tischpositionsachsen und die
Chair-Positionen sind damit entgegengesetzt. Die Skalierung bleibt identisch.
Die frühere allgemeine Koordinatenangabe in diesem Handoff beschreibt den
Simulationszweig und darf nicht als Nachweis physischer Ausrichtung gelten.

Der gespeicherte Projektorpfad liest `null_tabletop_masked` (Null TOP), also
die maskierte Tabletop-Ausgabe. Die Kontrollansicht rendert Source und
Tabletop-Motion separat. Falsch positionierte Source-Konturen außerhalb der
physisch korrekt positionierten Tischmasken sind daher eine plausible Ursache
für ihr Verschwinden; dies ist noch kein Live-Nachweis des Maskenbildes.

Rücknehmbarer Helfer: `td_builders/repair_aisi_world_axes.py`.
Er ersetzt nur vier Positionsausdrücke im Tisch-Callback und zwei im
Chair-Callback, prüft beide vollständig vor Mutation und sichert die
ursprünglichen Texte im bestehenden COMP. Rotationen, Radien, Skala,
OSC-Werte, Layouts, Masken und Projektionsoperatoren bleiben unverändert.
Keine automatische Speicherung oder Force-Cook. Live-Bestätigung siehe unten.
27 fokussierte Tests bestanden; beide echten Callbacks aus der gespeicherten
Version 144 offline erfolgreich korrigiert, kompiliert und idempotent geprüft.

Manuell im TouchDesigner-Python-Textport ausführen:

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\repair_aisi_world_axes.py', encoding='utf-8').read(), 'repair_aisi_world_axes.py', 'exec'))
```

Danach blaue Source-Konturen auf den realen Tischen und den beiden
Projektorausgängen sowie Floor-Ziele/Chairs prüfen. Kein Sender-Neustart nötig.
Bei Bedarf in derselben Textport-Sitzung rücknehmen:
`restore_aisi_world_axes(op)`. Speichern bleibt manuell durch Johannes.

Johannes bestätigt nach manueller Ausführung am 2026-10-19: blaue
Source-Konturen liegen auf den realen Tischen, Ziele und Chairs sind richtig
ausgerichtet. Damit ist die Achsenkorrektur für diese reale Zwei-Tisch-
Groupwork-Stichprobe bestätigt. Eine Speicherung des
korrigierten TD-Projekts oder ein erneuter Öffnungscheck ist nicht bestätigt.
Weitere Format-/Count-Prüfungen bleiben getrennt offen.

Input wurde anschließend über den vorhandenen Lernformat-Server aktiviert,
bei unverändert vier Teilnehmenden und 100 %. Preflight und laufendes
Senderprotokoll bestätigen zwei Tischziele/vier Chairs, Fehlerprotokoll leer.
Physische Input-Sichtprüfung angefragt; Discussion und gemeinsamer
Formatwechsel-Test folgen erst nach den Einzelbestätigungen.

Johannes meldet anschließend eingefrorene Tracking-/Layout-Anzeige und weiter
sichtbares Groupwork trotz Input-Wahl. Lesende Laufzeitprüfung um 10:44 Uhr:
Vision-JSONL und Live-Szene frisch, genau eine Layout-Senderkette aktiv,
fortlaufend Input mit wechselnden Posen protokolliert, Fehlerlog leer;
TouchDesigner besitzt UDP-Port 9000. Sender deshalb nicht neu gestartet.
Stillstand zwischen TD-Empfang und Darstellung noch einzugrenzen.
`td_builders/inspect_live_layout_flow.py` ist als lesende Textport-Diagnose
vorbereitet (Timeline, OSC-Werte, DAT-Zeilen, Instanzparameter und Fehler;
kein Force-Cook, keine Speicherung). Syntax geprüft; Live-Ausgabe offen.

Johannes bestätigt anschließend die Ursache: TouchDesigner war nicht auf
Play. Nach Aktivierung ist der Stillstand behoben; kein OSC-Neustart und
keine weitere Code-/Graphänderung erforderlich. Die vorbereitete Diagnose
musste dafür nicht ausgeführt werden. Input bleibt zur separaten physischen
Sichtprüfung aktiv; daraus wird noch keine Input-Formatfreigabe abgeleitet.

## Erste Formatfreigabe und Pfeilkorrektur

Johannes bestätigt anschließend Input, Discussion und Groupwork im Raum:
Source-Konturen folgen den Tischen, Ziele und Chairs liegen plausibel,
das Bild bleibt ruhig. Dies ist eine qualitative erste Live-Stichprobe mit
der aktuellen Tischkonfiguration; keine vollständige Count-/Gruppenmatrix,
Tracking-Ausfallprüfung oder erneuter Öffnungscheck.

Neuer Befund anhand des Screenshots: Bei großem Overlap läuft der
AISI-Tabletop-Pfeil über den Target-Mittelpunkt hinaus bis zur Source-Kante.
Die gespeicherte Version 144 bestätigt: `motion_tabletop_helpers` (Text DAT)
unter `table_motion_line_tabletop_geo` (Geometry COMP) begrenzt das Ende
ausschließlich am Schnittpunkt des Mittelpunktstrahls mit der Source-
Innenkontur, auch wenn der Target-Mittelpunkt davor liegt.

Vorbereitet: `td_builders/repair_aisi_arrow_endpoint.py` begrenzt die
bestehende Strecke auf den näheren Punkt aus Target-Mittelpunkt und
Source-Innenkontur. Damit bleiben Richtung und Länge beim Übergang stetig;
kein Überlaufen bei großem Overlap. Bestehende Polygonberechnung wird
wiederverwendet, kein neuer Footprint. Nur der AISI-Tabletop-Pfeil-Callback
in Template und Instanzen wird geändert. Study-/Floor-Pfeile, Layouts,
Tischmasken und Projektionsstufen bleiben unverändert. Alle Callbacks
werden vor Änderung geprüft; Sitzungssicherung und Rücknahme enthalten.
Keine Speicherung und kein Force-Cook.

Vier Regressionstests bestanden. Die tatsächlichen sechs gespeicherten
Callbacks aus Version 144 wurden offline korrigiert und mit 1152 Fällen
über Richtungen, Source-Rotationen und Entfernungen geprüft; kompiliert und
idempotent. Live-Ausführung und Overlap-Nachprüfung noch offen.

Manueller Textport-Aufruf:

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\repair_aisi_arrow_endpoint.py', encoding='utf-8').read(), 'repair_aisi_arrow_endpoint.py', 'exec'))
```

Rücknahme in derselben Sitzung: `restore_aisi_arrow_endpoint(op)`.
Danach großen Overlap sowie Annäherung an den Zielmittelpunkt und eine
größere Entfernung prüfen; kein Sender-Neustart erforderlich.

Johannes bestätigt die Endpunktkorrektur anschließend als passend. Neuer
Auftrag: AISI-Motion-Pfeile sollen wie Study bei gemeinsam erfüllten
Positions-/Winkeltoleranzen (≤ 8 cm und ≤ 5°, Rect axial modulo 180°)
verschwinden und bei Annäherung kleiner werden. Keine zusätzliche zeitliche
Bestätigung für die Pfeilsichtbarkeit, entsprechend der bestehenden Study-
Pfeilberechnung; Study-Controller und Arrival-Logging bleiben unverändert.

`td_builders/repair_aisi_arrow_arrival.py` ergänzt ausschließlich die AISI-
Floor-/Tabletop-Pfeil-Callbacks in Template und Instanzen. Bestehende
Sichtbarkeit bleibt zusätzlich maßgeblich. Innerhalb beider Toleranzen werden
Pfeile ausgeblendet; Spitzenlänge wird wie Study auf höchstens die halbe
Schaftlänge begrenzt, statt konstant 0,075 TD zu bleiben. So schrumpfen auch
die beiden Spitzenbalken zusammen mit dem bereits verkürzten Tabletop-Schaft.
Die Endpunktkorrektur bleibt erhalten. Sitzungssicherung einschließlich
Spitzenparametern, Vorabprüfung und Rücknahme enthalten; kein Force-Cook,
kein Speichern, keine Projektions-/Masken-/Layoutänderung.

23 fokussierte Tests bestanden. Alle zwölf realen gespeicherten Callbacks
aus Version 144 mit vorangehender Endpunktkorrektur offline kompiliert,
idempotent und in 300 Fällen geprüft. Live-Ausführung steht aus:

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\repair_aisi_arrow_arrival.py', encoding='utf-8').read(), 'repair_aisi_arrow_arrival.py', 'exec'))
```

Rücknahme: `restore_aisi_arrow_arrival(op)`. Live beide Toleranzen gemeinsam,
nur einen erfüllten Fehler, Annäherung und erneutes Entfernen prüfen.

Johannes bestätigt die Toleranz-/Spitzenkorrektur live: Pfeile werden kleiner,
verschwinden innerhalb der Toleranz und erscheinen beim Entfernen wieder.
Damit ist diese visuelle Stichprobe bestanden. Speicherung/erneutes Öffnen
der drei manuellen TD-Korrekturen ist weiterhin nicht bestätigt.
Nächster Prüfblock: kontrollierte Bewegung eines Tisches, Beobachtung von
Source-/ID-Zuordnung, Zielreaktion und Stabilität nach dem Loslassen.

Während der angefragten Einzeltischbewegung 25 Sekunden lesend beobachtet:
243 Samples, durchgehend Scene Order `table_00, table_01`, maximale
Scene-Dateialterung 0,073 s, keine Lesefehler. `table_00` bewegt sich über
18,68 cm in X und 27,91 cm in Y; `table_01` bleibt innerhalb 0,21/0,09 cm.
Größter Abstand aufeinanderfolgender 100-ms-Samples für den bewegten Tisch
5,21 cm. Kein Identitätsverlust in dieser Stichprobe; kein Nachweis für
Verdeckung/Kreuzung und keine eigenständige Latenzmessung. Visuelle
Bestätigung der Kontur-/Zielreaktion durch Johannes noch offen.

Johannes bestätigt anschließend die Bewegungsstichprobe: alles ruhig,
Kontur-/Zuordnung passend. Er beobachtet kontinuierliche Anpassung des
generierten Layouts bei Bewegung. Dies entspricht dem bestehenden
quelladaptiven Live-Pfad; keine Latch-/Freeze-Funktion ergänzt oder fachlich
neu festgelegt. Nächste Stichprobe: Input-Count 4 → 3 → 4 mit zwei Tischen.

Johannes bestätigt Count 3: genau drei sichtbare Kreise, stabile Source-
Konturen und Tischzuordnung. Auf seinen Auftrag zurück auf vier geschaltet;
Sender bestätigt wieder zwei Tische/vier Chairs. Sichtbestätigung für die
Rückkehr steht aus.

Neue Gestaltungsanforderung: rote/orange Chair-Konturen sind im Raum schlecht
erkennbar; Weiß und gleiche Stärke wie Ziel-Tischkonturen gewünscht.
`repair_chair_visual_style.py` übernimmt die Stärke aus dem bestehenden
`aisi_table_visual_style` (Text DAT), aktuell 2,5 cm statt 1,5 cm, und setzt
das vorhandene gemeinsame Chair-Material auf Weiß. Template + 15 Instanzen,
unveränderter Außenradius und erhaltene Radius-/Positionsbindung. Keine
Masken-/Projektionsänderung, kein Force-Cook/Speichern; Sitzungssicherung
und Rücknahme enthalten. Fünf Tests bestanden, alle 16 gespeicherten
Ring-Callbacks offline kompiliert und idempotent geprüft.

Manuell im TD-Python-Textport:

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\repair_chair_visual_style.py', encoding='utf-8').read(), 'repair_chair_visual_style.py', 'exec'))
```

Rücknahme: `restore_chair_visual_style(op)`. Live Weiß, Konturstärke und vier
sichtbare Kreise prüfen; Speicherung bleibt manuell.

Johannes bestätigt anschließend vier weiße Kreise, im Raum gut erkennbar.
Damit sind Count-Rückkehr 3 → 4 und Chair-Darstellung für diese Stichprobe
bestätigt. Nächste Live-Stichprobe: Groupwork vier Personen/eine Gruppe
mit zwei Tischen, anschließend Vergleich zu zwei Gruppen.

Johannes bestätigt Groupwork 4/1: zwei Ziel-Tische als Pair, vier weiße
Chairs plausibel verteilt, Source-Konturen folgen, ruhiges Bild. Auf seinen
Auftrag anschließend auf vier Personen/zwei Gruppen umgeschaltet;
Adapter-Preflight bestätigt zwei Tischziele und vier Chairs. Sichtprüfung
der getrennten Gruppen steht aus.

Johannes bestätigt Groupwork 4/2: zwei getrennte Tischgruppen mit jeweils
zwei Chairs, folgende Source-Konturen und ruhiges Bild. Damit ist der
Gruppenwechsel 4/1 → 4/2 für diese Zwei-Tisch-Szene live bestätigt.
Als nächste Stichprobe Discussion mit sechs Personen aktiviert:
Preflight bestätigt zwei Ziele und sechs Chairs, einschließlich der beiden
gemeinsamen Stirnplätze. Sichtprüfung steht aus.

Johannes bestätigt Discussion 6: Zweiergruppe mit kleinem Spalt, sechs
Chairs wie beschrieben, Source-Konturen folgen und ruhiges Bild.
Weitere Prüfung ausdrücklich mit den zwei vorhandenen Tischen.
Discussion 6 → 4 aktiviert; Offline-Vergleich auf derselben frischen Source
bestätigt exakt gleiche Tischziele und Reduktion auf vier Chairs. Live sollen
nur die beiden Stirnplätze verschwinden; Sichtbestätigung steht aus.

Johannes bestätigt Discussion 6 → 4: beide Stirn-Chairs verschwunden,
Tischziele und vier Längsseitenplätze unverändert, ruhiges Bild.
Nächster Test: bestehende Chair-Sichtbarkeit ausgeschaltet. Der Sender setzt
dabei die Radien der vier aktiven Slots auf null; alle Chair-Kreise sollen
verschwinden, Tischkonturen/Pfeile bleiben. Live-Bestätigung steht aus.

Johannes bestätigt Chair-Sichtbarkeit Off: alle vier Kreise verschwunden,
Source-/Zielkonturen und Pfeile laufen unverändert weiter. Damit ist das
Ausblenden aller aktiven Chairs über echte OSC-Nullradien für diese
Stichprobe nachgewiesen (kein Count-0-Test, kein isolierter Einzelslot-Test).
Chairs danach wieder eingeschaltet; Wiedererscheinen noch zu bestätigen.

Johannes bestätigt Chair-On: alle vier weißen Kreise an denselben Plätzen
zurück, ruhiges Bild. Chair-Off/On-Stichprobe damit abgeschlossen.
Nächster Schritt: kurzer gemeinsamer Formatwechsel Input → Groupwork 4/2 →
Discussion 4 bei gleicher Source und 100 %, mit Prüfung auf alte Elemente,
Source-/Pfeilkontinuität und ruhiges Bild. Endzustand Discussion vorgesehen.

Johannes bestätigt den vollständigen gemeinsamen Durchlauf Input →
Groupwork 4/2 → Discussion 4: jeweils vier Chairs, keine alten Ziele/Pfeile,
folgende Source-Konturen und ruhiges Bild. Discussion bleibt aktiv.
Damit ist der gemeinsame Formatwechsel für die aktuelle Zwei-Tisch-Szene
live bestätigt, ohne Aussage zu höheren Counts oder vier/fünf Tischen.
Nächste Integrationstichprobe: Moduswechsel AISI → Tracking → AISI über
Study-Control bei unverändertem Layout-Sender. Tracking soll nur aktuelle
reale Tischkonturen zeigen und AISI-Ziele/Pfeile/Chairs ausblenden; Rückkehr
soll Discussion 4 wieder anzeigen. Keine Study-Session starten.

Abgleich nach der Rückmeldung: State-Datei und Sender meldeten tatsächlich
noch Groupwork 4/2. Deshalb den gewünschten Endzustand Discussion über den
bestehenden HTTP-Endpunkt erneut gesetzt. Die visuelle Nutzerbestätigung
des Formatdurchlaufs bleibt erhalten; die Ursache der abweichenden
abschließenden UI-/State-Auswahl ist nicht geklärt.

Johannes bestätigt AISI → Tracking → AISI: Tracking zeigt nur reale
Tischkonturen, AISI wieder Discussion-Ziele/Pfeile/vier weiße Chairs;
Konturen folgen weiter. Modustrennung für diese Stichprobe bestanden.

## Study-Control-Oberfläche

Auf Johannes' Auftrag zeigt Study-Control außerhalb MODE Study nur die
Moduswahl. Teilnehmerangaben, Task, Variant, Study Condition, Trial Phase
und Study-Status liegen in einem nur in Study sichtbaren Frame. Die manuelle
Study-Target-Eingabe samt UI-Handler und Target-Zeile im Status ist entfernt.
Controller-API, Trial-/Familiarization-Ziele, OSC, Enums und Logs unverändert.

30 bestehende Study-Control-Tests bestanden. Zusätzlich echter Tkinter-Check
mit lokalem OSC-Recorder (keine Netzwerkpakete/Logs/Bildaufnahme): AISI →
Study → Tracking → Study → AISI blendet den Frame korrekt ein/aus;
keine Target-Eingabe vorhanden. Die laufende alte UI muss für den neuen
Code ersetzt werden. Reguläres automatisches Schließen über Accessibility
scheitert ohne Screenshot an `coordinate input geometry is unavailable`;
keine Fensteraufnahme und kein erzwungenes Beenden vorgenommen.

Alte Study-Control manuell schließen und aus dem Repository starten:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m aisi.app.study_control --mode 2
```

Layout-Sender, Vision und TouchDesigner weiterlaufen lassen. Dies startet
Study-Control in AISI mit einer neuen regulären Steuersitzung; kein Trial
wird gestartet. Live-Sichtprüfung der angepassten Oberfläche noch offen.

Johannes bestätigt den manuellen Study-Control-Neustart und die neue UI:
Einstellungen ausschließlich in Study sichtbar, Study Target entfernt;
AISI → Study → Tracking → AISI funktioniert. UI-Liveprüfung bestanden.

Nächster Prüfblock ist die Neustartfestigkeit des manuell korrigierten
TD-Graphen. Vor erneutem Öffnen muss Johannes eine neue benannte Version
speichern und deren tatsächlichen Dateipfad bestätigen. Vorschlag:
`AISI_v2.145_lab_layout_validated.toe`, sofern der Name noch frei ist.
Keine automatische Speicherung, kein Überschreiben der autoritativen
Masterdatei und kein Schließen des ungesicherten Graphen. Nach Bestätigung
zunächst gespeicherte Callbacks/Parameter offline prüfen, danach manueller
Öffnungscheck mit weiterlaufender Python-Pipeline.

Johannes hat stattdessen manuell
`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.146_lab_layout_validated.toe`
gespeichert und den Graphen offengelassen. Die Datei wurde lesend in eine
temporäre Kopie expandiert. `toeexpand` liefert trotz vorhandener Expansion
einen nichtnull Exitcode; die folgenden Inhaltsnachweise wurden deshalb
direkt an den tatsächlich expandierten Dateien geführt.

Gespeichert nachgewiesen: AISI-Tisch-/Chair-Achsen; Pfeil-Endpunktbegrenzung
im Template und den zwei aktuellen Tischinstanzen; Toleranz-Wrapper und
schrumpfende Spitzen in beiden Pfeilzweigen derselben drei Wurzeln; alle
16 Chair-Ring-Callbacks mit 0,013 TD (= 2,5 cm) Stärke und erhaltener
Valuea-Radiusbindung. Callbacks kompilieren offline. Gemeinsames Chair-
Material ist Constant MAT mit denselben gespeicherten Defaultparametern
wie das bestehende weiße Motion-Material (RGB-Defaults werden ausgelassen),
Chair-Geometrien verweisen weiter auf dieses Material.

Version 146 ist damit der neue manuell gesicherte Lab-Prüfstand. Erneutes
Öffnen und visuelle Wiederholungsstichprobe bleiben offen. Originaldatei
und laufender Graph wurden bei der Offline-Prüfung nicht verändert.

Johannes bestätigt den erneuten Öffnungscheck von Version 146 auf Play:
Source-Konturen folgen, vier weiße Chairs und Discussion-Ziele vorhanden,
Pfeile einschließlich Endpunkt/Toleranz korrekt, ohne Helfer erneut
auszuführen. Gesicherter Stand damit für diese Stichprobe neu geöffnet
und live bestätigt. Keine zusätzliche Behauptung zu höheren Tischzahlen.

Nächste Live-Stichprobe nach Öffnung: Input mit zwei Personen und zwei
verfügbaren Tischen. Ein Tisch soll aktiv zwei Chairs erhalten, der andere
ein Parkziel ohne Chairs; beide Source-/Zielidentitäten bleiben erhalten.
Preflight bestätigt zwei Tischziele/zwei Chairs; UI entsprechend gesetzt.
Keine physische Umsetzung der Parkpose angefordert. Sichtbestätigung offen.

Johannes bestätigt Input 2: zwei Chairs am aktiven Ziel, zweites Ziel ohne
Chairs am Rand geparkt, beide Source-Konturen folgen, keine alten Discussion-
Elemente und ruhiges Bild. Danach Input auf vier Personen erhöht;
Preflight bestätigt zwei Ziele und vier Chairs. Rückkehr beider Tische in
aktive Input-Rollen und Entfernen des Parkziels visuell noch zu bestätigen.

Johannes bestätigt Input 2 → 4: beide Tische aktiv, vier Chairs, Parkziel
verschwunden, Source-Konturen folgen und Bild ruhig. Park-/Aktiv-Rückkehr
damit für diese Zwei-Tisch-Szene bestätigt. Nächste Stichprobe Input 6:
beide verfügbaren Tische mit je drei Personen; Preflight besteht mit zwei
Zielen und sechs Chairs. UI auf sechs gesetzt, Sichtbestätigung offen.

Johannes bestätigt Input 6 mit zwei Tischen: je drei weiße Chairs,
sechs insgesamt, keine Parkpose, Sources folgen und ruhiges Bild.
Danach Groupwork 6/2 aktiviert; Preflight bestätigt zwei Ziele und sechs
Chairs. Live-Erwartung: zwei getrennte Dreiergruppen an je einem Tisch.
Sichtprüfung dieser Gruppenbelegung noch offen.

Johannes bestätigt Groupwork 6/2: zwei getrennte Ziele mit jeweils drei
Chairs, sechs Kreise insgesamt, Source-Konturen folgen und ruhiges Bild.
Danach auf Groupwork 6/1 gewechselt; Preflight bestätigt zwei Tischziele
und sechs Chairs. Erwartet ist das gemeinsame Pair mit sechs Plätzen;
Live-Bestätigung offen.

Johannes bestätigt Groupwork 6/1: gemeinsames Pair, sechs Chairs plausibel,
keine alten Gruppen, folgende Source-Konturen und ruhiges Bild. Weitere
Prüfungen auf seinen Wunsch bündeln, keine Detailbestätigung je Umschaltung.
Zusammenhängender Durchlauf vorbereitet: Groupwork 6/2 → Input 2 → Input 6 →
Discussion 6 → Groupwork 4/1 → Discussion 4, je sechs Sekunden. Alle sechs
Anfragen vorab auf aktueller Source erfolgreich geprüft. Endzustand
Discussion 4/Chairs On/100 % vorgesehen; gemeinsame visuelle Bewertung folgt.

Gebündelter Durchlauf technisch abgeschlossen: sechs HTTP-Umschaltungen
erfolgreich, 180 Scene-Samples, durchgehend `table_00, table_01`, maximale
Scene-Dateialterung 0,090 s. Senderprotokoll zeigt die Format-/Countwechsel,
Fehlerprotokoll weiterhin leer. Endzustand Discussion 4, Chairs On, 100 %.
Gemeinsame visuelle Rückmeldung für den Durchlauf noch offen.

Johannes bestätigt den gesamten gebündelten Durchlauf als ruhig, ohne
hängen gebliebene Elemente. Nächster gebündelter Test: kontrollierter
Layout-Sender-Neustart mit identischen Argumenten und anschließendem
Format-/Countwechsel. Vision, Adapter und TD bleiben bestehen. Alte
Senderlogs erhalten; neue Ausgabe unter `sender.restart.stdout.log` und
`sender.restart.stderr.log` im bisherigen Lab-Debugordner.

Wiederanlauf technisch bestanden: genau eine neue Sender-Prozesskette
(venv-Elternprozess PID 26328, Kind PID 18924), frische Szene vor
OSC-Freigabe erkannt, vorherigen Discussion-4-State übernommen. Anschließend
Input 2 → Groupwork 6/1 → Discussion 6 → Discussion 4, je sechs Sekunden,
erfolgreich über HTTP umgeschaltet und vom neuen Sender protokolliert.
Fehlerlog leer. Endzustand Discussion 4, Chairs On. Visuelle Gesamtbewertung
nach Neustart noch offen; kein Neustart von Vision/Adapter/TD durchgeführt.

Johannes bestätigt auch den Sender-Wiederanlauf samt Durchlauf visuell:
Darstellung selbstständig erholt, anschließend insgesamt ruhig.
Nächster gebündelter Test: nur Live-Scene-Adapter kontrolliert ersetzen,
danach Format-/Countwechsel bei weiterlaufender Vision, Sender und TD.
Adapter-Startargumente unter `adapter.restart.before.json` gesichert,
neue Logs `adapter.restart.stdout.log`/`adapter.restart.stderr.log`.

Adapter-Wiederanlauf technisch bestanden: neue Kette PID 30288/22380,
genau ein Adapter und unverändert ein Sender. Alte JSONL-Historie wird
übersprungen, frische Leerszene und danach aktuelle Frames publiziert.
Anschließend Input 2 → Groupwork 4/2 → Discussion 6 → Discussion 4
durchgeführt; 120 Samples mit stabiler Scene Order `table_00, table_01`,
maximales Scene-Dateialter 0,074 s. Beide Fehlerlogs leer. Endzustand
Discussion 4, Chairs On. Visuelle gemeinsame Bestätigung noch offen.

Johannes bestätigt den Adapter-Wiederanlauf visuell: Tracking/Darstellung
kommen selbstständig zurück, anschließende Wechsel ruhig.

## Vision-Wiederanlauf und Leerszenen-Korrektur

Vorprüfung des Vision-Neustarts zeigt einen Runtime-Fehler: eine vom Live-
Adapter geleerte Szene führt im teilnehmendenbasierten Input/Groupwork/
Discussion zu `LayoutConstraintError`. Der laufende Sender verwirft dann
den gesamten Durchlauf, wodurch alte TD-Daten stehen bleiben können.
Gezielte Korrektur in `prepare_scene_output`: nur bei expliziter Quelle
`vision_live_to_aisi_scene`, Metadatenmodus `tables_only` und exakt leerer
Tischliste leere Tabellen-/Personen-/Chair-/Zieldaten zurückgeben. Bestehender
Sendeloop publiziert dadurch Null-Counts. Planer und Kapazitätsprüfungen
bleiben unverändert; teilweise fehlende Tische werden weiterhin regulär
validiert. 37 fokussierte OSC-/Adapter-Tests bestanden, einschließlich
Startup-/Stale-Leerszenen und unveränderter Ablehnung unzureichender
Discussion-Tischzahl. Simulationsszenen bleiben im bestehenden Prüfpfad.

Fix durch gezielten Senderersatz aktiviert; anschließend nur Vision mit
denselben Kamera-/Modell-/Trackingargumenten neu gestartet. Argumente vorab
gesichert; neue Logs `sender.liveempty.*.log` und `vision.restart.*.log` im
bisherigen Lab-Debugordner. Kameraeinstellungen und Kalibrierung unverändert.
Sender protokolliert während der Initialisierung zweimal null Tische/Chairs,
danach selbstständig zwei Tische/vier Chairs. Input 4 → Groupwork 4/2 →
Discussion 4 anschließend verarbeitet, beide Fehlerlogs leer.

Eine direkte Diagnose-Dateilesung traf eine bestehende Windows-Dateisperre;
die Runtime verwendet bereits den dafür vorgesehenen RetainingSceneReader.
Nachprüfung mit diesem Reader: 39 Samples, durchgehend `table_00, table_01`,
maximales Scene-Dateialter 0,064 s. Kein Identitätswechsel in dieser
Stichprobe; Vision-IDs sind grundsätzlich nicht über Neustarts garantiert.
Endzustand Discussion 4/Chairs On/100 %. Visuelle Gesamtbestätigung des
Vision-Wiederanlaufs einschließlich Verschwinden/Rückkehr noch offen.

Johannes bestätigt Vision-Wiederanlauf visuell: Darstellung verschwindet
während Unterbrechung, kommt selbstständig korrekt zurück, anschließende
Wechsel ruhig. Leerszenen-Korrektur damit auch im Raum bestätigt.
Abschließender gebündelter Starttest: Vision, Adapter und Layout-Sender
gemeinsam stoppen, dann Adapter → Sender → Vision mit bisherigen Argumenten
starten. Alle drei Prozessketten vorab geprüft; `joint.before.json` sichert
Argumente, neue Logs `adapter.joint.*`, `sender.joint.*`, `vision.joint.*`.
TD und Study-Control bleiben offen. Dies ist kein Rechner-/TD-Kaltstart.

Gemeinsamer Wiederanlauf technisch bestanden: genau eine unabhängige
Prozesskette je Vision/Adapter/Sender, alle drei Fehlerlogs leer.
Adapter publiziert frische Leerszene, Sender liefert während Initialisierung
Null-Counts, danach wieder aktuelle Zwei-Tisch-Szene. Anschließender
Input-4 → Groupwork-4/2 → Discussion-4-Durchlauf verarbeitet. Endzustand
Discussion 4, Chairs On, 100 %. Visuelle Gesamtbestätigung noch offen.

## Git-Ausführungskontext

Die Sandbox läuft als `STUDIOPCFRACTAL\CodexSandboxOffline` (SID-Endung 1011),
das Repository gehört `STUDIOPCFRACTAL\johan` (SID-Endung 1005). Deshalb
verweigert Git innerhalb der Sandbox den Zugriff wegen `dubious ownership`.
Lesende Git-Aufrufe außerhalb der Sandbox laufen als `johan` und funktionieren.
Keine `safe.directory`-Ausnahme und keine Berechtigungsänderung vorgenommen.

Branch `vision/wip-dark-proposals`, HEAD `536ffee`; vier Commits vor der
lokalen Origin-Referenz, ohne neuen Fetch. Vorhandene Änderungen an
`src/vision/pipeline.py`, `tests/test_vision_table_association.py` und der
simulierten Szene bleiben erhalten. Keine Layout-Regeln oder Vision-Parameter
im Rahmen dieser Inbetriebnahme geändert.

Vollständiger Anwendungs-Wiederanlauf am 2026-10-19 technisch durchgeführt:
TD und Study-Control durch Johannes geschlossen. Vision-Fenster-Schließen
beendet die cv2.imshow-Schleife nicht; Q/Esc beendet regulär. Kein nachgewiesener
Supervisor-Neustart. Verbliebene fünf AISI-Prozessketten gezielt beendet,
Nullbestand einschließlich TD geprüft, danach alle fünf mit gesicherten
Argumenten neu gestartet. Startbefehle: full_restart.before.json; neue Logs:
full.<Modul>.stdout/stderr.log im bestehenden Lab-Debugordner.
Discussion 8 automatisch wieder ready mit vier Tischen/acht Chairs, alle fünf
Fehlerlogs leer. TD-Version 149 interaktiv geöffnet und Learning-Format-Seite
im Codex-Browser angefordert. Play, sichtbare Study-Control und physischer
Wiederanlauf-/Format-/Modustest noch durch Johannes zu bestätigen.

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

## Git-Übergabe — 2026-10-21

Die abgeschlossene Lab-Inbetriebnahme wird mit Integrationscode, TD-Helfern,
106 erneut bestandenen fokussierten Tests und Projektdokumentation gesichert.
Laufzeitdaten, Debug-Ausgaben und Kalibrierungsdateien bleiben ausgeschlossen;
auch die lokale TD-Datei Version 149 wird nicht über Git übertragen.
Die zuvor vorhandenen Vision-Änderungen und die simulierte Live-Szene bleiben
unverändert außerhalb dieses Commits.

Der lokale Branch enthält vier ältere, noch nicht gepushte Commits, darunter
Study-Auswertungen und Debug-Plots. Deshalb erfolgt die datenfreie Übergabe
auf `codex/lab-inbetriebnahme-20261021`, direkt auf Basis von
`origin/vision/wip-dark-proposals`, ohne diese älteren Daten-Commits.
Der ursprüngliche lokale Branch und seine Historie bleiben erhalten.

## Neustartbefund am 2026-10-21: falscher Sender-Startpfad

Nach manuellem Pipeline-Neustart meldet Johannes nur einen Tisch und fehlenden
Layoutstatus. Prozessargumente belegen den Start über
`scripts/run_current_room_tracking_only.ps1`: `--tracking-only` und
`--tracking-table-id table_00`. Vision und Adapter liefern gleichzeitig fünf
aktuelle Tische. Der Tracking-only-Sender veröffentlicht absichtlich keinen
Layoutstatus; MODE AISI in Study-Control ändert diese Prozessoptionen nicht.

Nur die Senderkette wurde durch den oben dokumentierten Layout-Sender ersetzt,
mit beiden Study-Bindings, `--require-fresh-live-scene` und `--interval 0.05`.
Vision/Adapter/TD und fachliche UI-Eingaben unverändert. Anschließend HTTP-Status
`ready`, Input 8, fünf Tische und acht gesendete Chairs; Senderfehlerlog leer.
Sicherung/Protokolle lokal unter `data/aisi/debug/restart_sender_20261021/`.
Physische Sichtbestätigung nach diesem Austausch noch offen.

Für künftigen AISI-Layoutbetrieb den Vision→Scene→OSC-Layoutpfad verwenden,
nicht `run_current_room_tracking_only.ps1`. Der vorhandene
`scripts/run_current_room_vision_to_osc.ps1` ist der Layout-Launcher; er startet
weder Study-Control noch Learning-Format-Server. Vollständige validierte
Senderargumente stehen im Abschnitt „Geprüfter Startpfad“. Bestehende Pipeline
vor erneutem Launcheraufruf beenden, damit kein zweiter Sender entsteht.

## Tischbezogene Tabletop-Zielkonturen — Umsetzung vorbereitet, 2026-10-21

Auf Johannes' Auftrag neuer rücknehmbarer Textport-Helfer:
`td_builders/isolate_aisi_tabletop_targets.py`. Untersuchung einer temporären
Expansion der unveränderten TD-Version 149 bestätigt gemeinsame Tabletop-
Zielausgabe, gemeinsame physische Maske und passende lokale Tischflächen in
Template/vier gespeicherten Instanzen. Der laufende Count kann davon abweichen;
der Helfer adressiert fünf native Item-Pfade und funktioniert ohne Neubau bei
Count-Wechseln. Fehlende Instanzen/Source-Verfügbarkeit sperren ihren Zielanteil.

Neuer isolierter COMP `aisi_own_tabletop_targets`: fünf Target-Render TOPs,
jeweils bestehende Tabletop-Kamera, Source-Flächengeometrie desselben Items,
Masken-Render TOP und kopierte bisherige Reorder-/Maskenoperation. Erst nach
Einzelbeschneidung addieren. Sources/Tabletop-Pfeile bleiben im separaten
bisherigen gemeinsamen Maskenzweig erhalten. Nur Eingang von
`null_tabletop_masked` (Null TOP) auf neuen Modus-Switch umstecken; bei
Tracking/Study unverändert den ursprünglichen `mask_tabletop` (Composite TOP)
verwenden. Originalrenderer und physische Maskenkette bleiben unangetastet.

Vorbedingungen prüfen Verschaltung/Kamera/Geometrien. Vor Anschluss fertig
aufbauen; bei Fehlern ursprünglichen Eingang wieder verbinden und nur eigenen
neuen COMP entfernen. Parameter-/Verbindungsfingerprint für Kalibrierung,
Projektorausgabe, originale Floor-/Tabletop-Renderer und Masken vor/nachher.
Kein Force-Cook, keine Speicherung. Rücknahme:
`restore_aisi_tabletop_targets(op)`; Sicherung enthält dauerhafte Operatorpfade.

59 fokussierte Tests bestanden, darunter synthetischer Bildfluss mit zwei
Zielen, die beide Tischflächen schneiden: pro Fläche nur eigenes Ziel statt
Summe beider Ziele; auch Source-Abgang/Count-Reduktion. Weitere Tests prüfen
Originalpfad in Tracking/Study, wiederholten Aufruf, Rücknahme und Rollback
bei Erstellfehler. Gespeicherte Template-/Instanzgeometrien separat gelesen.
Diese Checks belegen noch keine reale Projektion oder GPU-Performance.
Manuelle Anwendung, gebündelte Raumprüfung und neue TD-Sicherung offen.

Manuell im TD-Python-Textport:

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\isolate_aisi_tabletop_targets.py', encoding='utf-8').read(), 'isolate_aisi_tabletop_targets.py', 'exec'))
```

Gebündelt prüfen: eigene/fremde Zielkontur bei Teilüberlappung, mehrere Tische
bewegen/drehen, Tischabgang/Rückkehr und Count-Wechsel, Formatwechsel sowie
Tracking → AISI. Source-/Pfeildarstellung und Floor unverändert, keine fremden
Zielkonturen auf Tabletop, keine neuen Aussetzer/Flackern; GPU-Belastung live
beobachten. Kalibrierung, Homographien und Edge-Blend unverändert.

Live-Anwendung meldet erfolgreichen Aufbau, Johannes sieht danach jedoch keine
Tabletop-Informationen. Rücknahme sofort angeleitet; deren Ausführung noch nicht
bestätigt. Konkreter Kontextfehler gefunden: die kopierte Source-/Pfeil-Geometrie-
Expression verwendet parent().findChildren und sucht im neuen Unter-COMP statt
im Layout-COMP. Korrigiert auf native absolute Pfade für alle fünf Source-/
Pfeilpaare, vor Anschluss echte OP-Auswahl prüfen, ebenso aktive Ziele/Masken.
62 Tests bestanden. Dies erklärt die fehlenden Sources/Pfeile; vollständige
Bildkorrektheit ist noch nicht physisch nachgewiesen.

Der manuelle Helfer bereitet ab jetzt standardmäßig nur eine getrennte Vorschau
vor und lässt den ursprünglichen Ausgang aktiv. Eigene ältere aktive Version
wird zunächst zurückgenommen. Vorschau-TOP:
`comp_layout_proposal/aisi_own_tabletop_targets/slot4_add`.
Erst nach Sichtprüfung `activate_aisi_tabletop_targets(op)` verwenden; bekannte
Operatorfehler verhindern die Aktivierung. Keine neue Live-Erfolgsbehauptung.

## Renderzweig verworfen; Polygon-Clipping vorbereitet — 2026-10-21

Johannes meldet starke Verzögerung bereits bei vorbereiteter Vorschau. Weiterhin
sichtbare fremde Ziele sind im nicht aktivierten Vorschauzustand erwartbar, da
der ursprüngliche Ausgang aktiv bleibt. Sofortige vollständige Rücknahme des
Vorschauzweigs angeleitet. Zusätzliche Render-/Maskenpässe sind verworfen.

Neuer Helfer `td_builders/clip_aisi_tabletop_targets.py`: ausschließlich
Tabletop-Target-SOP-Callbacks in Template/Instanzen ergänzen. Ursprüngliche
Kontur erzeugen, ihre Polygone geometrisch an der vorhandenen kanonischen
Source-Fläche desselben Items beschneiden. Source-Fläche mit bestehenden
Source-/Target-Geo-Posen ins Target-Lokalsystem transformieren; kein neuer
Footprint, keine neuen Koordinatenkonventionen. Fehlende Source sperrt Target.
Tracking/Study umgehen die Beschneidung. Keine zusätzlichen Renderer, keine
Änderung an bestehenden Render-, Masken- oder Projektorparametern. Alter eigener
Vorschauzweig wird vor Anwendung entfernt und ursprünglicher Ausgang verbunden.
Kein Force-Cook/Speichern; Callback-Rücknahme mit
`restore_clipped_aisi_tabletop_targets(op)`, auch für inzwischen neue Replikate.

49 fokussierte Tests bestanden; zusätzlich 240 Fälle mit echten gespeicherten
TD-149-Target-Callbacks und Style-DAT geprüft. Live-Anwendung/Performance und
physische Zielisolation noch offen. Der alte Renderzweig-Helfer lässt sich nicht
mehr versehentlich direkt aktivieren. Keine Erfolgsbehauptung für neue Variante.

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\clip_aisi_tabletop_targets.py', encoding='utf-8').read(), 'clip_aisi_tabletop_targets.py', 'exec'))
```

Vor Test des Polygon-Clippings wünscht Johannes am 2026-10-21 einen erneuten
Pipeline-Neustart zur Lag-Eingrenzung. Vision/Adapter/Layout-Sender mit exakt
aktuellen Argumenten neu gestartet; TD, Study-Control, Format-UI unverändert.
Startliste/Logs: `data/aisi/debug/pipeline_restart_20261021_102642/`.
Erster Startversuch scheiterte nach Prozessende an der Modulnamensauswertung;
Start aus gesicherten Argumenten unmittelbar abgeschlossen, ohne Doppelstart.
Danach fünf Tische/acht Chairs, Discussion, Benutzerstärke 0.95 beibehalten,
Status ready, drei Fehlerlogs leer. Adapter-Frame-ID steigt in zwölf Stichproben
von 132 auf 179; grober sekundengenauer Vision-Zeitstempel maximal ca. 1.08 s
alt. Kein belastbarer Ende-zu-Ende-Latenznachweis daraus. Polygon-Clipping noch
nicht angewendet; TD-Vorschau-Rücknahme und subjektiver Lag durch Johannes zu
bestätigen, keine Behebung der Verzögerung behauptet.

## Discussion-Lag: Live-Versand von Planung entkoppelt — 2026-10-21

Johannes grenzt den weiterhin sichtbaren Lag ein: Vision direkt, TD/Projektion
verzögert; Input flüssig, Discussion langsam. Die frühere Einordnung allein
über 95 % war unvollständig: neue Fünf-Tisch-Discussion-8-Szene braucht auch bei
100 % ca. 2068 ms ohne Profiler. cProfile weist den Hauptanteil _solve_topology,
_attach_parking und _compact_park_targets zu. Posegenaue Cache-Schlüssel werden
bei Trackingrauschen neu; keine Cache-Quantisierung/Layout-Regeländerung.

`aisi.app.live_layout_worker`: genau ein Hintergrundauftrag, keine anwachsende
Queue. Der Discussion-Vorschaupfad im Sender wartet nicht mehr synchron auf
Layoutberechnung. Währenddessen aktuelle Sources auf letzten gültigen Slots,
Live-Occupancy und bestehende Study-Track-Kanäle weiter senden; letzte Ziele/
Chairs erhalten. Ergebnisse bei veränderter Anfrage, IDs/Reihenfolge, ROI,
Geometrie oder aktiver Bindung verwerfen. Source-Posen eines abgeschlossenen
Vorschlags vor Versand auf aktuellen Stand bringen, ohne Slotpermutation.
Leere Szenen/Tracking-only/Input/Groupwork bleiben auf bisherigen direkten
Pfaden. Bei Formatwechsel Ergebnis invalidieren. Ziele können weiterhin langsamer
neu berechnet werden; keine Echtzeitgarantie für Discussion-Planung behauptet.

68 fokussierte Tests bestanden, darunter blockierter Planner bei fortlaufenden
Source-Nachrichten, keine Warteschlange, veraltete Anfrage, Invalidierung,
Fehler/Recovery und Erhalt der ID-Bindung. Offline-Integration mit realer Szene:
92 Source-Updates in fünf Sekunden, Median 51.0 ms, maximal 65.7 ms Abstand.
Nur Sender mit unveränderten Argumenten neu geladen; Input 8, fünf Tische, ready,
Fehlerlog leer. Logs lokal `data/aisi/debug/discussion_async_20261021/`.
Physische Discussion-Prüfung noch offen; neuer Polygon-Clipping-Helfer bleibt
bis dahin unangewendet. Kalibrierung/Geometrie/Layout-Regeln unverändert.

## Neuer Auftrag: Vorschläge nach Generierung stabil halten — 2026-10-21

Johannes erklärt die fortlaufende quelladaptive Neuberechnung ausdrücklich für
nicht notwendig: nur Sources sollen nach der Generierung weiterlaufen; der
Vorschlag bleibt stabil. Umsetzung für Input, Groupwork und Discussion im
Layout-Vorschaupfad: einmal gültigen vollständigen Vorschlag pro Anfrage und
Inventar speichern, aktuelle Source-Posen per ID bei jedem Versand auffrischen.
Target-/Chairdaten bleiben bei Bewegung/Rotation/Jitter unverändert. Bei
geänderter Anfrage, ROI, Tischinventar/-reihenfolge/-geometrie oder manueller
Generierungsrevision neue Planung. Count/Abgang und veraltete Ziele weiterhin
explizit behandeln. Tracking-only und Legacy-Passthrough unverändert.

Format-UI bietet „Neu generieren“. Additiver lokaler State layout_revision wird
UI/Sender/Status konsistent mitgeführt; keine OSC-Vertragsänderung. Sichtbarkeits-
toggles lösen keine Neuplanung aus. Nebenfehler korrigiert: POST ohne
presentation_side darf bestehende Vortragsseite nicht leeren, sonst würde etwa
Chairs Off/On unabsichtlich Layout-Eingaben ändern.

73 Tests bestanden; synthetische Source-Bewegung/-Rotation hält Ziele und
Chairs unverändert, Revision/Inventar invalidieren, UI-Button/Persistenz geprüft.
Offline-Integration reale Discussion-Szene: initial 1945.1 ms, anschließend 100
bewegte Source-Updates bei identischen Zielen/Chairs, im Mittel 0.144 ms je Update.
Sender und UI mit bisherigen Argumenten neu geladen; aktueller Zustand Input 8,
100 %, fünf Tische, ready, neuer Knopf im HTTP-HTML, Senderfehlerlog leer.
Logs lokal `data/aisi/debug/stable_proposal_20261021/`.
Gebündelte physische Prüfung und Rückkehr zum noch unangewendeten Polygon-
Clipping stehen aus. Frühere Beobachtung kontinuierlich quelladaptiver Ziele
ist damit bewusst abgelöst, nicht rückwirkend als Implementierungsfehler gewertet.

Johannes bestätigt am 2026-10-21 die neue Vorschlagsbindung im Raum:
Vorschläge bleiben stabil, Sources folgen flüssig. Rückkehr zum Tabletop-Fix
explizit beauftragt. Aktueller HTTP-Zustand Groupwork 15/4, fünf Tische, 100 %,
Revision 1, ready; diesen Zustand nicht ungefragt ändern. Polygon-Clipping-
Helfer erneut fokussiert geprüft; vor Callback-Mutation jetzt vorhandene Source-
Punkte und tatsächliche TD-Primitive-vertices-API prüfen. Keine zusätzlichen
Renderer. Manuelle Anwendung und physische Prüfung weiterhin ausstehend.

Johannes bestätigt Polygon-Clipping v2 live am 2026-10-21: eigene Zielkonturen
wieder sichtbar, fremde erscheinen nicht mehr auf Tischplatten. Sources und
Pfeile bleiben flüssig. Erste physische Zielisolation damit bestanden; noch
keine neue TD-Sicherung. Laufzeitabgleich Groupwork 15/4, fünf Tische, 100 %,
Revision 1, ready; Senderfehlerlog leer. Nächster gebündelter Liveblock:
Formate bei gleichbleibend 15 Personen wechseln, Sources über eigene/fremde
Ziele bewegen/drehen, Tischabgang/Rückkehr, Chairs Off/On und Tracking → AISI.
Erwartung: Vorschlag bei reiner Bewegung stabil, eigene Tabletop-Ziele korrekt
beschnitten, keine fremden Ziele/alten Elemente, nach Wechsel/Rückkehr ruhiges
Bild. Testresultat dieses Folgeblocks noch offen; Kalibrierung unverändert.

## Gebündelte Tabletop-Abnahme bestanden — 2026-10-21

Johannes bestätigt Formatwechsel, Tischabgang/-rückkehr, Chairs Off/On und
Tracking → AISI: nur eigene Zielkonturen auf den Tabletops, Bodenausgabe
unverändert, Sources/Pfeile und gesamte Darstellung flüssig. Polygon-Clipping
v2 und stabile Vorschläge damit für diesen gebündelten Lab-Durchlauf bestanden.
Aktueller Laufzeitstatus Input 15, fünf Tische, 100 %, Revision 1, ready;
Senderfehlerlog leer. Kalibrierung/Homographien/Edge-Blend unverändert.

Johannes möchte den Stand sichern. Neue manuelle TD-Sicherung und anschließender
Öffnungscheck noch ausstehend. Im TD-Ordner existiert bereits
`AISI_v2.150_Grafik_überarbeitet.toe`; diese Datei nicht überschreiben.
Vorschlag für neue Sicherung: `AISI_v2.151_tabletop_targets_validated.toe`.
Prozessargument nennt weiterhin die beim Prozessstart geladene Version 149;
dies beweist nicht den aktuellen Save-As-Pfad. Keine automatische TD-Speicherung.
Abschließende Codeprüfung: 125 fokussierte Tests bestanden, git diff --check
ohne Fehler. Physische Bestätigung und Codeprüfung getrennt dokumentiert.

## Sicherung und Öffnungscheck abgeschlossen — 2026-10-21

Johannes bestätigt `AISI_v2.151_tabletop_targets_validated.toe` gespeichert und
neu geöffnet: Sources folgen flüssig, nur eigene Tabletop-Zielkonturen, alles
passt. Datei lesend verifiziert: 360684 Bytes, SHA-256
`39e27cdba8c8214413282c1fd5ee5263750b606fe07229fcede3894aa2240543`.
Aktueller Status Groupwork 8/4, fünf Tische, 100 %, Revision 1, ready;
Senderfehlerlog leer. Kein Force-Cook, keine automatische Speicherung oder
Änderung des geschützten Masters. Abschluss auf ausdrücklichen Auftrag;
kein weiterer physischer Prüfschritt dieses Folgeblocks offen. Repository-
Änderungen dieses Folgeblocks bleiben uncommittet, bis Git-Sicherung beauftragt ist.

## Git-Übergabe des abgeschlossenen Folgeblocks — 2026-10-26

125 fokussierte Tests erneut bestanden. Übertragen werden ausschließlich
stabile Vorschlagsbindung/Discussion-Worker, UI-Regenerierung, produktives
Tabletop-Polygon-Clipping, lesender Diagnosehelfer, zugehörige Tests und
Projektstand. Der verworfene Renderzweig und sein Versuchstest bleiben lokal.
Laufzeitdaten, Debug-Ausgaben, Kalibrierungsdateien, simulierte Live-Szene und
fremde Vision-Änderungen sind ausgeschlossen. Die physische TD-Datei 151 bleibt
außerhalb von Git. Folgecommit auf `codex/lab-inbetriebnahme-20261021`, ohne die
älteren lokalen Study-Auswertungs-/Debug-Commits zu übertragen. Der ursprüngliche
lokale Branch und alle fremden Änderungen bleiben erhalten.
