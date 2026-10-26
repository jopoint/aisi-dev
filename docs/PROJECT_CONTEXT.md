# AISI Project Context

Stand: 2026-10-26

Aktueller abgeschlossener Lab-Prüfstand:
`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.151_tabletop_targets_validated.toe`.
Johannes bestätigt Speicherung und erneutes Öffnen: Sources folgen flüssig,
nur eigene Zielkonturen auf Tabletops, alles korrekt. Stabile Vorschläge,
Format-/Count-/Moduswechsel und unveränderte Bodenausgabe zuvor gebündelt
live bestätigt; 125 fokussierte Tests bestanden. Kalibrierung/Homographien/
Edge-Blend unverändert. Folgeblock abgeschlossen, keine weiteren Live-Schritte
daraus offen. Die folgenden Zwischenberichte sind historischer Verlauf.
Git-Übergabe des Folgeblocks am 2026-10-26 auf
`codex/lab-inbetriebnahme-20261021`, anschließend an `cac6365`.
Nur produktive Quellen, Tests und Projektdokumentation; Laufzeitdaten,
Debug-Ausgaben, Kalibrierung und fremde Vision-Änderungen ausgeschlossen.
Die physische TD-Datei 151 ist nicht Bestandteil der Git-Übergabe.

## 1. Purpose and workstreams

AISI is a research prototype for adaptive, spatially augmented learning environments. It senses and tracks room objects, represents the room in a shared metric coordinate system, generates or loads target configurations, and communicates spatial transformations through projections on the floor and on tabletops.

The repository contains three related but distinct workstreams:

1. general AISI layout generation (`input`, `groupwork`, `discussion`);
2. the controlled dual-surface Study pipeline;
3. live computer vision/tracking and TouchDesigner integration.

Do not assume that a change in one workstream should alter the others.

## 2. Evidence levels

Use these labels when reporting status:

- **Repository-confirmed:** inspected or tested in the local checkout.
- **History-reported:** reported in prior project work but not re-run in the current task.
- **Physical-room-reported:** tested in the physical setup; cannot be established from repository checks alone.

The current worktree is the source of truth for code state. Branch, HEAD, and dirty-file status must be checked live with Git rather than stored here.

## 3. Coordinate system and physical setup

Repository-confirmed:

- world/ROI: `500 × 500 cm`, X and Y each spanning `0–500`;
- world center: `(250, 250) cm`;
- TouchDesigner scale: `1 cm = 0.0052 TD units`;
- TD mapping: `tx = (x_cm - 250) * 0.0052`, `ty = -(y_cm - 250) * 0.0052`;
- the simulation-to-OSC path negates source and target rotations before transmission.

Physical-room-reported:

- two Optoma UHZ36STe ceiling projectors;
- overlapping projection footprints with edge blending;
- separate floor and tabletop homographies per projector;
- tabletop plane at `z = 74 cm`;
- floor and tabletop calibration considered complete and protected;
- a nominal projected `50 × 50 cm` square measured approximately `50 × 49 cm` after calibration.

The calibration pipeline must not be changed as collateral work.

## 4. Main runtime paths

Lab-Inbetriebnahme am 2026-10-19: bestehende Kamera-/Adapter-Pipeline geprüft,
Tracking-only-Sender gezielt durch Layout-Sender ersetzt und Teilnehmer-Vorschau
aktiviert. Live-Protokoll meldet zwei Tische und vier Chairs im Groupwork;
physische Sichtprüfung noch offen. Startbefehl, Rückkehr zum Tracking-Betrieb
und Git-Ausführungskontext: [Lab-Inbetriebnahme](LAB_INBETRIEBNAHME.md).
Erste Raumprüfung meldet auf beiden Achsen gespiegelte AISI-Ausgabe. Die
gespeicherte TD-Version 144 bestätigt entgegengesetzte Positionsvorzeichen
zwischen AISI-Callbacks und Tracking-/Tischmasken. Rücknehmbare Korrektur
vorbereitet und offline geprüft.
Johannes bestätigt anschließend die manuelle Ausführung und reale Prüfung:
Source-Konturen auf den Tischen, Ziele und Chairs korrekt ausgerichtet.
Dieser Nachweis gilt für die aktuelle Zwei-Tisch-Groupwork-Stichprobe;
Speichern/erneutes Öffnen und weitere Formatprüfungen bleiben offen.
Johannes bestätigt anschließend auch Input, Discussion und Groupwork im Raum:
Source-Konturen folgen den Tischen, Ziele/Chairs plausibel, ruhiges Bild.
Qualitative erste Live-Stichprobe, keine vollständige Count-Matrix.
AISI-Tabletop-Pfeile laufen bei großem Overlap über den Target-Mittelpunkt;
rücknehmbare Begrenzung am Zielmittelpunkt offline geprüft und zur manuellen
Live-Ausführung vorbereitet. Details im Lab-Handoff.
Weitere Lab-Bestätigung am 2026-10-19: Pfeil-Endpunkt/Toleranz und weiße
2,5-cm-Chair-Konturen manuell angewandt und im Raum bestätigt. Gemeinsamer
Formatwechsel Input → Groupwork 4/2 → Discussion 4 mit zwei realen Tischen
bestanden: vier Chairs, keine alten Elemente, folgende Source und ruhiges
Bild. Count-/Gruppen- und Off/On-Stichproben im Lab-Handoff. Speicherung und
erneuter Öffnungscheck der manuellen TD-Korrekturen weiterhin unbestätigt.
Moduswechsel AISI → Tracking → AISI anschließend ebenfalls live bestätigt.
Study-Control blendet auf neuen Auftrag alle Study-Bedienelemente außerhalb
von Study aus und enthält keine manuelle Target-Eingabe mehr. Controller,
Trial-Ziele und OSC unverändert; 30 Tests und Tkinter-Moduscheck bestanden.
Johannes bestätigt anschließend Neustart und manuelle Sichtprüfung:
Study-Einstellungen nur in Study, Target-Eingabe entfernt, Wechsel AISI →
Study → Tracking → AISI funktioniert. Speicherung/erneutes Öffnen der
manuellen TD-Korrekturen bleibt der nächste Prüfblock.
Johannes hat anschließend `AISI_v2.146_lab_layout_validated.toe` manuell
gespeichert. Die Korrekturen sind in einer temporär expandierten Kopie
nachgewiesen (einschließlich Template und 16 Chair-Ringen). Dieser Stand
ist der neue gespeicherte Lab-Prüfstand; erneutes Öffnen noch offen.
Erneutes Öffnen von Version 146 anschließend durch Johannes bestätigt:
Source-Folge, vier weiße Chairs, Discussion-Ziele und Pfeil-Endpunkt/Toleranz
funktionieren ohne erneute Helferausführung. Weitere Count-/Parkprüfung folgt.
Weitere Zwei-Tisch-Stichproben (Input bis sechs Personen, Groupwork 6/1 und
6/2, Park-/Aktivwechsel, gebündelte Formatwechsel) sowie Sender-/Adapter-
Wiederanlauf im Raum bestätigt; Einzelbelege im Lab-Handoff. Vor Vision-
Neustart Runtime-Leerszenenfehler behoben: explizit geleerte Live-Szenen
liefern Null-Counts statt Layout-Ablehnung. 37 OSC-/Adapter-Tests bestanden;
neuer Sender aktiv. Vision-Neustart und anschließende Formatwechsel technisch
bestanden, visuelle Gesamtbestätigung noch offen.
Johannes bestätigt anschließend Vision- und gemeinsamen Python-Wiederanlauf
visuell; regulärer Zwei-Tisch-Inbetriebnahmeblock abgeschlossen.
Neuer Block: spontane Tischzugänge/-abgänge und fehlende Tische für neue
Anfragen. Learning Format UI zeigt jetzt tatsächlichen Senderstatus und
Planerfehler, ohne eigene Layoutberechnung. Auf Johannes' Entscheidung
bleibt die letzte gültige Anzeige bei Ablehnung stehen und wird in der UI
als veraltet gekennzeichnet. 47 Tests und Live-HTTP-Fehler/Recovery bestanden;
physische Tischzahlwechsel noch offen. [Handoff](LAB_TISCHANZAHL.md).
Johannes bestätigt anschließend den physischen Tischzahlwechsel: dritter
Tisch hinein/heraus korrekt berücksichtigt, UI-Warnung bei Discussion 7
und fehlenden Tischen; Warnung verschwindet bei geringerem Count oder
Hinzufügen eines vierten Tisches. Prüfblock abgeschlossen. Lesender
Endzustand: Discussion 6, drei reale Tische, sechs Chairs, Status ready.
Anschließend vier reale Tische erkannt und Discussion 6 → 7 → 6 gebündelt
technisch/live bestätigt: stabile Scene Order, Zweiergruppe/Parken ↔
Vier-Tisch-Rechteck, keine beanstandeten Altlasten/Unruhe. Endzustand
Discussion 6 mit vier realen Tischen; höhere Discussion-Counts noch offen.
Discussion 8–12 einschließlich Eckplätzen und Rückkehr zu acht anschließend
technisch/live bestätigt: plausible Ergänzung, vollständiges Entfernen,
ruhiges Bild und keine alten Elemente. Groupwork mit vier Tischen folgt.
Vier-Tisch-Groupwork (vier Gruppen/zwei Pairs, acht/zwölf Personen) sowie
Fünf-Tisch-Discussion 12 → 13 → 14 → 15 → 12 danach live bestätigt.
Kontrollviewer-Source-Auswahl war zwischenzeitlich leer; native Pfadauswahl
repariert sie. Johannes bestätigt fünf folgende Source-Konturen nach fünftem
Tischzugang, unveränderte Projektion und ruhige Topologie-/Chair-Wechsel.
Aktuell gespeicherte TD-Version bleibt 146; neue Viewer-Korrektur noch nicht
als gespeichert bestätigt. Fünf-Tisch-Input ist der nächste Prüfblock.
Fünf-Tisch-Input 4 → 8 → 10 → 12 → 15 → 4 anschließend live bestätigt:
plausibles Parken/Verdichten, alle 15 Chairs sichtbar, Rückkehr ohne alte
Kreise und ruhiges Bild. Endzustand Input 4. Offene gebündelte Prüfblöcke
stehen in TODO und im Tischanzahl-Handoff; als Nächstes Fünf-Tisch-Groupwork.
Fünf-Tisch-Groupwork und gemeinsamer Fünf-Tisch-Format-/Modus-/15-Chair-Off/
On-Test danach live bestätigt. Aktiver Tischabgang/-rückkehr technisch
erfolgreich; Johannes präzisiert, dass nur Ziele veraltet stehen bleiben
dürfen, während fehlende Sources verschwinden müssen. Sender/UI dafür
erweitert (additive Source-Verfügbarkeit, ID-gebundene Slots, 51 Tests),
neu geladen. Manueller AISI-Sichtbarkeitshelfer und Nachprüfung noch offen.
Johannes bestätigt anschließend Helferausführung und Abgang-/Rückkehrtest
als funktionierend. Fehlende Sources/Pfeile verschwinden, Live-Sources und
veralteter Zielvorschlag sind getrennt. Neue manuelle TD-Sicherung der seit
Version 146 angewandten Viewer-/Floor-Pfeil-/Source-Sichtbarkeitskorrekturen
bleibt offen. Weitere Robustheits-/Projektionsprüfungen siehe TODO.

### General simulation/layout path

```text
Room Editor
→ data/aisi/scenes/simulated/live_scene.json
→ scene interpretation
→ target structure/layout synthesis
→ constraint repair
→ OSC
→ TouchDesigner
```

Main entry points:

- `aisi.app.sim_room_editor`
- `aisi.app.learning_format_server`
- `aisi.app.sim_scene_to_osc`

State files:

- `data/aisi/scenes/simulated/live_scene.json`
- `data/aisi/state/learning_format.json`

Validate each format individually through Room Editor, Learning-Format-Interface, and OSC before a short cross-format pass.

### Study path

```text
Study trial definition
→ Study controller/state machine
→ tracking binding and live source pose
→ OSC /study channels
→ TouchDesigner Study visuals
→ append-only JSONL logging
→ study_metrics analysis
```

Key files:

- `data/aisi/study/trials.json`
- `src/aisi/app/study_trials.py`
- `src/aisi/app/study_control.py`
- `src/aisi/app/study_tracking.py`
- `src/aisi/app/study_logging.py`
- `src/aisi/analysis/study_metrics.py`

Die aktive Study-Definition ist `pilot_v8`. T1–T3, Familiarization und sämtliche Teilnehmerstartpositionen bleiben unverändert aus `pilot_v7`. Nur alle T4-Tischposen werden gemeinsam um `+11 cm` in Welt-Y verschoben; X, Rotation und A/B-Transformation bleiben erhalten. Practice bleibt aus Trial-Zählern und `study_metrics` ausgeschlossen.

### Vision/tracking path

Current code is primarily under `src/vision/`; earlier sensing/replay infrastructure remains under `src/aisi_sensing/`.

Current baseline:

- Rect tables use OBB geometry transformed to world coordinates;
- multi-table association, occlusion handling, and reacquisition were stabilized;
- tracking-only projection renders an inner tabletop contour and outer floor contour;
- adaptive smoothing is lighter during motion and stronger at rest.

Treat tracking as frozen unless a task explicitly concerns tracking.

## 5. TouchDesigner architecture

The authoritative manually maintained project is external to the repository:

`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.toe`

Repository builders and `.toe` snapshots are references, not guaranteed representations of the active physical graph.

Aktueller Chair-Stand am 2026-10-07:

- Aktueller manuell gespeicherter Stand am 2026-10-07: `AISI_v2.141_coherent_chairs_validated.toe`, von Johannes nach erfolgreicher Radius-Reparatur bestätigt und dateisystemseitig verifiziert. In einer temporär expandierten Kopie sind Radius-Bindung und Callback für Template + 15 Instanzen nachgewiesen. Der frühere bereinigte Stand 137 wurde erneut geöffnet und geprüft; ein erneuter Öffnungscheck von 141 wird nicht behauptet. Speichern bleibt ausschließlich manuell durch Johannes.
- Der optionale Floor-Zweig unter `comp_layout_proposal` erreicht beide bestehenden Projektorpfade.
- Der bestehende `chairs`-Zweig ist auf 15 Slots erweitert. Bei Count 7 sind sieben Radien positiv und acht Null; die Positionen werden laufend gebunden.
- Debug und regulärer Floor verwenden dieselbe zentrale Chair-Geometrie. Der Floor verwendet `cam1`, 2000×2000 und addiert Chairs über den zentralen Composite.
- Der manuell ausgeführte Bildvergleich besteht: optionaler Floor Off bitgleich, beide Projektorausgänge reagieren auf On, Tabletop/Table-Mask bitgleich und Debug-/Preview-Schalter unabhängig vom regulären Zusatz.
- Die Viewer sind im laufenden Projekt nach `comp_layout_proposal/chair_debug` und `comp_layout_proposal/tables_chairs_virtual_preview` (jeweils Container COMP) kopiert. Johannes bestätigt den Migrationscheck: alle vier Viewerbilder und die sechs geprüften Floor-/Tabletop-/Masken-/Projektorbilder bitgleich. Die anschließende Bereinigung ist ebenfalls bestätigt: keine externen Referenzen, alte Top-Level-Komponenten, doppelte Debug-Geometrien und alter Chair-Zweig in `comp_output` entfernt; alle zehn geprüften Bilder bitgleich. Der bereinigte Stand ist in Version 137 gespeichert und nach erneutem Öffnen geprüft.
- Count 15 liefert vollständige OSC-Daten und 15 gültige Instanzen; Johannes bestätigt nach dem Diagnosecheck 15 sichtbare Kreise und danach reagierende Count-Wechsel. Der zunächst beobachtete Stillstand bei sieben Kreisen ist noch nicht abschließend erklärt. Johannes bestätigt auch den direkten Wechsel 3 → 15 → 3 nach erneutem Öffnen ohne Diagnose-/Force-Cook.
- Der isolierte TD-Radius-null-Test besteht: bei 15 gültigen Chairs verschwindet nur Chair 0, die anderen 14 Radien bleiben unverändert und beide Chair-Render reagieren. Callback und Chair 0 sind wiederhergestellt; keine neue Datei gespeichert. Ein Radius-null-Test über echte OSC-Nachrichten ist damit noch nicht bestätigt.
- Modussperren nach Wiederholung mit nachweislich regulären Chairs On durch Johannes bestätigt: Tracking, Study und Calibration liefern jeweils Switch-Index 0, AISI liefert 1. Der erste Durchlauf war wegen Chairs Off nicht aussagekräftig. Vollständige bildliche Modusvergleiche stehen noch aus.
- Johannes bestätigt 8 → 3 sowie die Counts 6, 9, 10, 11 und 15. Count 0 lässt sich in der bestehenden UI nicht eingeben; der vorher pauschal bestätigte Wechsel 1 → 0 wird deshalb nicht als gesicherter Count-null-Nachweis gewertet. Der Übergang 15 → 0 bleibt ungeprüft; die UI wird dafür nicht erweitert.
- Änderungen im Room Editor werden laut Johannes live in TD übernommen. Damit ist die Reaktion über die OSC-Brücke beobachtet; ein einzelner ungültiger Chair über echte OSC-Nachrichten und physische Projektionskorrektheit sind damit nicht bestätigt.
- Neue Stichprobe am 2026-10-07: neun sichtbare Kreise bei Count 9 und ebenfalls neun bei Count 10, zusätzlich auffällige Platzverteilung und links angeschnittene Kreise. Die Python-Ausgabe für dieselbe aktuelle Source enthält korrekt 9/10 Chairs; Version 140 enthält offline 15 korrekt zeilengebundene Chair-Instanzen. Der Livefehler ist damit erneut offen, ohne die bestandene Offline-Geometrieprüfung zu widerlegen. Ein manueller lesender Check ohne Force-Cook liegt in `td_builders/inspect_shared_chair_live_state.py`; Live-Ausgabe steht aus. Geschützte Kamera-/Projektionsparameter wurden nicht angepasst.
- Die anschließende manuelle Live-Ausgabe bestätigt Count 10, zehn positive DAT-Radien und vollständige Übereinstimmung OSC → DAT → Instanzparameter. Die empfangenen Positionen reproduzieren jedoch exakt den alten Python-Code (bis Float32-Rundung); der Sender lief seit 15:53 vor den Korrekturen. Gezielter Neustart um 17:48 mit aktuellem Code, genau ein Sender nachgewiesen, laufend zehn Chairs gemeldet; Study-Control unverändert. Die angeschnittenen Kreise sind durch die alten ROI-verletzenden Positionen erklärbar. Sichtbare Vollständigkeit nach Neustart ist noch von Johannes zu bestätigen; gegebenenfalls tatsächliche Ring-SOP-Geometrie prüfen.
- Nach Neustart bestätigt Johannes weiterhin neun sichtbare Kreise bei Count 10; die linken Kreise liegen jetzt vollständig innerhalb der Ansicht. Der verbleibende Fehler betrifft vermutlich die tatsächliche Ring-Geometrie, noch nicht bewiesen. Gezielter manueller Punkte-/Radius-Abgleich in `td_builders/inspect_shared_chair_ring_geometry.py` vorbereitet; keine Cook- oder Parameterreparatur vorgenommen, Live-Ausgabe offen.
- Ringpunkte-Bericht bestätigt die Ursache: nur Index 9 besitzt trotz Instanzradius 0,13 TD noch Nullradius-Geometrie mit Außenradius 0,001 TD. Manuelle Reparatur `td_builders/repair_shared_chair_radius_dependency.py` vorbereitet: explizite SOP-Radius-Bindung über den vorhandenen Custom-Parameter Valuea, gleicher Ring-Callback mit geänderter Radius-Lesezeile, Template + 15 Instanzen, rücknehmbar. Offline geprüft; Live-Ausführung, wiederholte Count-Wechsel und anschließendes manuelles Speichern noch offen. Kein Force-Cook und keine geschützten Änderungen vorgesehen.
- Johannes hat die Radius-Reparatur in Version 140 manuell ausgeführt: 16 Ringe einschließlich Template gebunden, kein Force-Cook und keine Speicherung. Danach sind bei Count 10 zehn Kreise sichtbar. Wiederholte Übergänge 9 → 10 → 9 → 10 und 3 → 15 → 3 sowie ein neuer manuell gespeicherter Stand bleiben noch zu bestätigen.
- Johannes bestätigt anschließend den Fehler als behoben und zeigt die manuell gespeicherte Version 141. Die Datei enthält nach Offline-Expansion tatsächlich die explizite Radius-Bindung und aktualisierte Callback-Lesezeile für Template + 15 Instanzen. Fehlender-Chair-Fehler abgeschlossen; erneutes Öffnen, echte OSC-Radius-null-Prüfung und aufgeschobene physische Raumprüfung bleiben getrennte Nachweise.

Detailed TD debug-node history belongs in `docs/TOUCHDESIGNER_SYNTH_CHAIR_DEBUG.md`, not here.

Physical-room-reported structure:

- modes include Calibration and Content;
- Content can switch between Tracking and AISI/Study paths;
- floor content, tabletop content, and table masks share downstream calibration/projector stages;
- floor/tabletop/mask ordering is physically consequential;
- Calibration + Floor requires a black table-mask input so the inverted mask becomes white and leaves the floor image unchanged.

Rendering/backend rules:

- the interactive Room Editor uses `tkinter` directly and avoids forcing a Matplotlib backend at import time;
- headless PNG/debug generation selects `Agg` before importing `pyplot`;
- shared plotting modules remain backend-neutral.

## 6. Canonical geometry

Repository-confirmed table types:

| Type | Physical reference | Shape |
| --- | --- | --- |
| `summit` | approximately `157 × 70 × 74 cm` | trapezoidal |
| `sprint` | approximately `82 × 60 × 74 cm` | trapezoidal |
| `rect` | `160 × 80 × 74 cm` | rectangular |

The polygon-aware geometry migration is complete. Canonical footprints/supports are used for collision, ROI, clearance, repair, and debug rendering.

Important implementation invariants:

- format roles remain bound to `table_id`;
- target output returns to original scene order;
- `strength = 0` yields exact source poses without repair;
- `strength > 0` blends before one final hard-constraint repair;
- overall layout-generation capacity is five tables.

For binding design rules, seating/clearance semantics, and format-specific constraints, see the relevant entries in `docs/DECISIONS.md`.

## 7. Current Rect layout-generation state

### Input

The fixed Rect Input slots have been replaced by a source-adaptive presentation-plus-audience formation.

Current state:

- Automatische Präsentationsachse seit 2026-10-08: gemeinsame axiale Source-Orientierung bevorzugt, Positionen bestimmen Präsentationsende und Rollen. Ohne eindeutige Orientierungsresultierende gilt die räumliche Hauptausdehnung; eine explizite Präsentationsseite bleibt verbindlich (D007).
- presentation role is inferred spatially rather than from `table_id`;
- active Rect tables use one semantic long-side seating/movement surface;
- Die gemeinsame Rect-Input-Synthese berücksichtigt diese Orientierungspräferenz im normalen und im Vorschaupfad; teilnehmendenbasierte Teilmenge, Parken und Chairs bleiben opt-in.
- virtual Room Editor / Learning-Format / OSC / TouchDesigner checks have been accepted;
- physical room validation remains open.

### Participant-based Input preview

Johannes bestätigt am 2026-10-15 Input für den Moment als passend. Qualitative
Rückmeldung zur aktuellen Anzeige; keine zusätzliche vollständige Count-/Seiten-
oder physische Raumprüfung. Gemeinsamer Formatwechsel-Check bleibt offen.

Der explizit aktivierte Simulationspfad plant aktive und geparkte Rect-Tische
nach Teilnehmendenzahl und leitet Chair-Marker aus ihren gerichteten Sitzflächen ab.

- Zielverhältnis: zwei Teilnehmende pro aktivem Tisch; erst mit allen verfügbaren Tischen bis zu drei pro Tisch, damit `1–15` bei fünf Rect-Tischen.
- Überkapazität scheitert ausdrücklich mit `LayoutConstraintError` vor Ausgabe; kein stilles Ersatzlayout.
- Parktische bleiben sichtbar, Ziele folgen der Source Scene Order; interne Auswahl und Chair-Reihenfolge sind ID-stabil.
- Chair-Kreise haben `25 cm` Radius und liegen vollständig in den kanonischen gerichteten `70 cm` Sitzflächen. Ihre Richtung folgt der Zielnormalen auch nach Raumachsen-Ausweichlösung.
- Die optionale Präsentationsseite wird in der bestehenden Rect-Synthese berücksichtigt; ohne Vorgabe bleibt die Source maßgeblich.
- Transformationsstärke 0 erhält auch geparkte Tischposen exakt, ohne Reparatur. Die vollständige gemeinsame Sitzflächenprüfung gilt für 100 %.
- Offline am 2026-10-07: 300/300 Fälle bestanden (vier Quellen × fünf Ausrichtungen × Counts 1–15), 300 deterministische Wiederholungen, 140 Scene-Order-Prüfungen, 60 Überkapazitätsablehnungen und 59 fokussierte Tests. Nachweise und Grenzen: [Prüfbericht](INPUT_GEOMETRY_VALIDATION.md).
- Zentrale TD-Struktur mit 15 Slots, OSC-Live-Reaktion und Modussperren sind laut Handoff geprüft. Count 0 ist ausgenommen; echte OSC-Radius-null-Prüfung und physische Raumvalidierung bleiben offen.
- Ohne Vorschau bleiben normale Chair-Daten und andere Formate unverändert.

Bei späteren Live-Prüfungen darf genau eine `sim_scene_to_osc`-Instanz auf
Port `9000` senden. Diese Validierung hat keinen Sender gestartet.

### Groupwork

Neue Spezifikation vom 2026-10-08, als Offline-Prototyp umgesetzt: `participants`
und `number_of_groups` bestimmen möglichst gleich große Teilnehmergruppen.
Eine Teilnehmergruppe darf mehrere räumlich zugehörige Tischcluster nutzen.
Die bisherigen Insel-`groups` des Geometriegenerators sind keine vollständige
Teilnehmergruppenzuordnung. Reguläre Stirnseitenplätze erhalten Vorrang vor
verdichteten Längsseitenplätzen; zusätzliche kanonische Stirnseitenstreifen
werden im neuen Offline-Modell bei Belegung geprüft. 65 fokussierte Tests und
zehn Integrationsfälle bestanden. Johannes aktualisiert die Tischwahl nach
der Live-Stichprobe: drei Personen optimal am Einzel-Tisch, darüber bevorzugt
ein Pair, sofern passend. Standard `group_capacity` ersetzt `few_tables`;
nutzbare Stirnseiten bleiben vor verdichteten Längsseiten bevorzugt. Die opt-in
Vorschau/OSC-Anbindung ist im Code ergänzt; Stärke 0 ohne Chairs/Reparatur,
positive Teilstärken mit Blend-before-repair und gebundenen Rollen. Über 15
Chairs werden im Adapter als technische Ausgabegrenze abgelehnt.
Getrennte Cluster werden zusätzlich auf überlappende 170 × 90 cm
Bodenkonturen geprüft und anschließend ohne Rollenwechsel räumlich entzerrt.
Die physische Geometrie und Pair-Seam bleiben unverändert.
Die Clusterwahl minimiert weiterhin den Gesamtweg. Die abschließende starre
Entzerrung nutzt freie Fläche für ein weiches 60-cm-Ziel zwischen Bodenkonturen
verschiedener Teilnehmergruppen (bestehende Sitzflächentiefe); zusätzliche Wege
sind bis dahin zulässig, danach wieder nachrangig. Das Ziel ist keine harte
Ablehnungsbedingung. In der aktuellen `15/4`-Quelle steigt der kleinste
Gruppenabstand von 0,5 auf 60,4 cm bei rund 2,4 s Offline-Laufzeit.
Pair-Seam, Sitzflächen, ROI und Parkregeln bleiben erhalten;
Singletons erhalten zusätzliche Source-abgeleitete Winkelkandidaten.
Der Vier-/Fünf-Singleton-Reparaturpfad nutzt inzwischen begrenzte Winkelannäherung
statt eines direkten gemeinsamen orthogonalen Fallbacks und prüft abgerundete
kanonische Flächen. Geparkte Groupwork-Tische stehen bei 100 % mit ihrer physischen
Längsseite am ROI-Rand und bleiben von der anschließenden Entzerrung ausgenommen.
Zusätzlich halten Parktische mindestens 60 cm physischen Kantenabstand zu aktiven
Tischen. Bei gleicher fachlicher Topologie-/Belegungspriorität minimiert die Zielauswahl
den Gesamtweg aller Tische; aktive Wege dienen danach als Gleichstandsentscheidung.
Groupwork-Parken darf mehrere ROI-Ränder nutzen, wenn dies den Parkweg verkürzt.
Bei fehlendem Parkplatz erhält ein zusammenhängendes Pair mit drei Singletons
Vorrang vor fünf getrennten aktiven Tischclustern für nur vier Gruppen.
Die Topologie `2 + 1 + 1 + 1` erhält dafür eine begrenzte Winkelannäherung als
Fallback; Rollen, ursprüngliche Source-Winkel und Scene Order bleiben erhalten.
Eine neue lokal festgefahrene `15/5`-Source wird nach erfolgloser normaler Suche
mit zusätzlichen Source-abgeleiteten Mittelpunkt-/radialen Startpositionen repariert.
Alle kanonischen Geometriebedingungen bleiben unverändert; kein Parkabstandsproblem.
Bei gleicher Tischzahl/Topologie wird das Pair bevorzugt stärker belegt;
`10/4` soll eine Dreiergruppe am Pair und `3 + 2 + 2` an Singletons erhalten,
sofern die vollständige Geometrie passt.
Rollen bleiben nach der Clusterbildung gebunden; keine globale Zielpermutation.
Johannes bestätigt die aktuelle `10/4`-Vorschau visuell als passend.
Der gemeinsame Offline-Abschlusscheck besteht 130/130 Anfragen (Counts 1–15,
zulässige Gruppen 1–5, Editor-/Live-Quelle), einschließlich gemeinsamer Geometrie,
Identität, Scene Order und Determinismus. Kapazitätsbeispiele und technische
15-Slotgrenze sind separat geprüft. Eine Editor-Sackgasse bei `13/4`–`15/4` wird
nach Reparaturfehlschlag durch erneute Kandidatensuche mit voller Konturprüfung
gelöst; zuvor gültige Pfade bleiben unverändert. 52 fokussierte Tests bestanden.
[Abschlussbericht](GROUPWORK_ABSCHLUSSCHECK.md); Live-Stichprobe der neuen
Konturreparatur, vollständige interaktive Einzelvalidierung und gemessene
Live-Laufzeit bleiben offen. Die Offline-Suche ist inzwischen durch frühe
kanonische Konfliktprüfung, unveränderte Bestwert-Auswahl und auf einen Aufruf
begrenzte Chair-Prüfcaches beschleunigt; Vergleichspläne bleiben exakt gleich.
Die zweite Stufe ergänzt sichere Weggrenzen in der Entzerrung sowie kanonische
Hüllrechteck-Vorprüfung und begrenzte, vollständig koordinatenabhängige
Geometriecaches.
Die dritte Stufe zieht im Teilnehmerpfad Sitzflächenkonflikte vor und bricht
unmögliche Teilkombinationen vor weiteren Anhängen ab. Konkreter `10/4`-Fallback
31,9 → 5,9 s offline, vollständiger Plan unverändert; 46 Tests bestanden.
Siehe [Laufzeit-Handoff](GROUPWORK_PERFORMANCE.md). Details: D008b und
[Groupwork-Handoff](GROUPWORK_PARTICIPANTS.md).

Source-adaptive Rect Groupwork for counts `2–5` is productively implemented.

Current state:

- all Pair/Singleton partitions are derived from source geometry;
- fixed slots, ID-based pairing, and orthogonal target-angle grids are obsolete;
- Pair seam is `8 cm`;
- Singleton and Pair clearance geometry follows the accepted rules in `D008`;
- source orientation strongly influences Pair target orientation;
- focused repository and OSC/simulation checks have passed;
- interactive Room Editor, TouchDesigner, and physical room validation remain open.

### Discussion

Stand der teilnehmerabhängigen Opt-in-Chair-Vorschau: 2026-10-15.

- 1–4 Personen: zwei parallele Rect-Tische mit 10 cm Spalt zwischen den Längskanten, bis zu zwei gegenüberliegende Plätze je äußerer Längsseite. 5–6: zusätzliche gemeinsame Stirnplätze, bei fünf nur ein Ende.
- 7–12: nach innen gerichtetes Vier-Tisch-Rechteck, maximal zwei Chairs je äußerer Längsseite. Für 9–12 zusätzliche äußere Eckplätze zwischen Nachbartischen, bei zwölf acht Längs- plus vier Eckplätze. 13–15: Fünf-Tisch-Pentagon mit zehn Längsplätzen und drei bis fünf Zwischenplätzen; höchstens zwei direkt je Längsseite.
- Zweiergruppe am 2026-10-15 auf Johannes’ Wunsch auf 10 cm physischen Spalt umgestellt (90 cm Mittelpunktabstand). Ursprüngliche 170 × 90 cm Floor-Konturen sollen vollständig bleiben; ihre Außenkanten treffen sich im Spalt. Gemeinsame Stirnflächen überspannen nun 170 cm statt 160 cm. 31 fokussierte Tests und 30 Offline-Fälle bestanden. Rücknahme der angewandten Kontur-Reparatur und erneute Generierung mit aktualisiertem Sender manuell erforderlich. [Anleitung](TOUCHDESIGNER_JOINED_FLOOR_CONTOURS.md).
- Eckflächen aus kanonischen Kontur-Stützpunkten und bestehenden 50-cm-Streifen abgeleitet, vollständig für ROI und Parkplanung reserviert. Maximal ein Chair je Ecke/Zwischenraum, bei zehn zunächst gegenüberliegende Eckplätze. Im Pentagon entstehen die Zwischenflächen an den Mittelpunkten der einander zugewandten kanonischen Stirnkanten. Zwischen-Chairs und ihre vollständigen Sitzflächen werden nach außen auf den Kreis der zehn Längsseiten-Chairs verschoben (nominal rund 26,5 cm; gemeinsamer Mittelpunktabstand rund 225,5 cm). Die bestehende Phasen-/Mittelpunktsuche wahrt die ROI; in der aktuellen Live-Ausgangsszene maximal 3,2 cm Tischverschiebung und 1° gemeinsame Drehung gegenüber dem vorherigen Ziel.
- Tischidentitäten und Posen bleiben innerhalb jeder Teilnehmerstufe stabil; nur die Chair-Belegung ändert sich. Die jeweilige Maximalbelegung 6/12/15 wird vorgeplant und begrenzt zwischengespeichert.
- Überzählige Tische werden mit einer Längsseite am ROI-Rand geparkt, mindestens 60 cm von aktiven Tischen entfernt; alle Tischidentitäten und die ursprüngliche Scene Order bleiben erhalten. Die Auswahl berücksichtigt den Gesamtbewegungsweg.
- Chair-Radius 25 cm; kanonische Sitzflächen 50 cm tief. Eigene Kantentangenz und höchstens 0,51 cm Rundungsüberstand sind zugelassen. Vollständige ROI- und Fremdkollisionsprüfung einschließlich Parktischen.
- Ohne expliziten Count bleibt `2 × verfügbare Tischanzahl` der Standardwert; die aktive Topologie folgt anschließend der Teilnehmerstufe. Bei zu wenigen Tischen oder mehr als 15 Personen klare Ablehnung.
- Bisherige Ring-/Geometriefunktionen und kompakte Parkplanung werden wiederverwendet. Begrenzte Ergebnis-Caches und Wiederverwendung identischer Parkgeometrie innerhalb einer Suche; kein Netzwerkversand in Offline-Checks.
- Umbauintensität am 2026-10-15 nach Johannes’ Freigabe: Stärke 0 erhält exakte Source ohne Chairs; positive Teilstärken dürfen von der festen Discussion-Zielform abweichen. Einzelne Tische folgen der Interpolation; kanonische Chair-/Sitzgeometrie wird pro gebundenem Tisch transportiert. Begrenzte Reparatur einzelner Posen statt starrer Gesamtform. Maximale Stufenbelegung, beide Ring-Bewegungsstreifen, volle ROI, Tisch-/Chair-Kollisionsfreiheit, freie Sitzflächen und Randparken mit 60 cm bleiben geprüft. 100 % unverändert, Rollen/Scene Order erhalten. Cache weiterhin 32 unabhängige Ergebniskopien. 26 fokussierte Tests und 210 Offline-Fälle aus zwei Szenen, Counts 1–15 bei 0/1/25/50/75/99/100 % bestanden; zusätzlich relative Tischabstände statt bloßer gemeinsamer Drehung geprüft. Quellen, Checks und Vergleich lokal unter `data/aisi/debug/discussion_relaxed_strength_2026-10-15/`; reproduzierbar mit `scripts/validate_discussion_strength.py`. Live-Reglerprüfung nach Sender-Neustart offen.
- Offline: 30 Fälle aus zwei Ausgangsszenen, alle Counts 1–15; Übergänge, Parkabstände, Identität/Scene Order, Determinismus und lokale OSC-Ausgabe geprüft. Kontrollplots und eingefrorene Quellen lokal unter `data/aisi/debug/discussion_pentagon_chair_circle_2026-10-15/`.
- Aktualisierung des gemeinsamen Pentagon-Chair-Kreises: 22 fokussierte Discussion-/Rect-Template-Tests bestanden; Input und Groupwork unverändert. Interaktive Chair-Einzelvalidierung und physische Prüfung bleiben offen.
- Der bisherige Tischring ohne Opt-in-Vorschau bleibt unverändert; seine frühere virtuelle Bestätigung gilt nicht automatisch für die neuen Chair-Stufen.

## 8. Study state

### Active trials

Repository-confirmed:

- `trials.json`: `pilot_v8`, `frozen_for_study`;
- zugehöriger eingefrorener Snapshot: `trials_pilot_v8.json`; `pilot_v7` bleibt erhalten;
- T1–T3 und Familiarization einschließlich Teilnehmerstarts unverändert aus `pilot_v7`;
- T4A/T4B: Source, Target und beide Statiktische um exakt `+11 cm` in Welt-Y verschoben, bei unverändertem X und unveränderter Rotation;
- Anlass: natürlicherer Referenzweg mit vorangehendem kurzen Tischende ohne künstliches anfängliches Zurücksetzen; physische Raumvalidierung bleibt offen;
- eight experimental trials: T1–T4 × A/B;
- T1/T2 use one active table and no distractors;
- T3/T4 use one active table and two static distractors;
- exact coordinates, A/B transforms, participant positions, ROI safety, and snapshot metadata are covered by tests.

Task logic:

| | low/limited occlusion | increased occlusion |
| --- | --- | --- |
| simpler layout | T1 | T2 |
| denser layout | T3 | T4 |

This is a deliberate 2×2 task-creation logic; physical factors may not be perfectly orthogonal, so factorial claims require methodological justification.

### Conditions and mappings

- modes: Tracking `0`, Study `1`, AISI `2`;
- conditions: Floor-only `0`, Dual-surface `1`;
- phases: Home `0`, Ready `1`, Active `2`, Complete `3`.

Dual-surface may spatially redistribute guidance rather than merely add tabletop graphics to otherwise identical floor guidance.

### Arrival and logging

- translation tolerance: `8 cm`;
- rotation tolerance: `5°`;
- confirmation duration: `0.5 s` continuously inside tolerance;
- objective arrival and participant-declared completion are distinct;
- arrival entered/confirmed/exited events are logged;
- tracking loss and post-arrival behavior are represented in analysis metrics;
- session metadata includes the active trial-definition SHA-256;
- logs are append-only and participant/session/attempt aware.

## 9. Documentation risks

Known drift outside these handoff files:

- the root `README.md` still describes older prototype status and layout/vision assumptions;
- `docs/PROJECT_STATE_2026-05.md` is historical;
- some human-readable notes in `trials.json` may not literally match the numeric poses and should be reviewed before the next pilot.

Do not change frozen trial geometry merely to resolve prose drift; determine first whether only the notes are wrong.

## 10. Validation principle

Keep repository-confirmed, history-reported, and physical-room-reported claims separate. A local test or virtual TouchDesigner check does not establish physical projection correctness.

### Floor-Renderer in Chair-Arbeitsdatei 137

Die gespeicherte Version 137 wurde am 2026-10-07 in einer temporären Kopie
mit `toeexpand` untersucht. `comp_layout_proposal/render_floor` (Render TOP)
hat eine aktive Geometry-Expression: Im Tracking-Modus werden Tracking-
Floor-Geometrien gewählt, ansonsten phasenabhängige Study-Geometrien.
Der als konstanter Parameterwert gespeicherte ältere Pfad zu
`item*/table_target_floor_geo` ist bei dieser Expression nicht maßgeblich.
Study-Geometrien sind zusätzlich nach Modus/Phase auf Sichtbarkeit begrenzt.
Ein leerer ursprünglicher Floor im AISI-Modus ist deshalb erklärbar und
belegt keinen Fehler der Chair-Integration: Chairs werden erst im zentralen
Composite hinzugefügt. Eine dauerhaft leere Darstellung auch im passenden
Tracking-/Study-Zustand wäre separat im laufenden Projekt zu untersuchen.
Johannes nimmt Count 0 aus dem aktuellen Prüfumfang; die physische
Raumprüfung ist derzeit nicht möglich und bleibt aufgeschoben.

### AISI-Floor und Study-Gestaltung — Live-Zwischenstand

Auf Basis von `AISI_v2.138_coherent_chairs_validated.toe` hat Johannes
`apply_aisi_study_visual_style.py` ausgeführt und die Darstellung bestätigt.
AISI rendert nun vorhandene Zieltischkonturen und Bodenpfeile in
`render_floor` (Render TOP); Tracking/Study behalten ihre bisherigen Zweige.
Rect-Ziele verwenden die weißen gestrichelten Study-Konturen (Floor
170 × 90 cm, Tabletop 150 × 70 cm, Strichstärke 2,5 cm), Rect-Source
die blaue durchgehende Tabletop-Kontur. Zentraler gemeinsamer Style-Code
liegt in `comp_layout_proposal/aisi_table_visual_style` (Text DAT);
vorhandene Item-Geometrien und Template werden weiterverwendet.
Chairs und Scout-Fallback bleiben unverändert.

Der Livebericht meldet `passed: true`: geschützte Einstellungen unverändert,
Chair- und Table-Mask-Bilder bitgleich, sichtbare Floor-Pixel, fünf Rect-Items
mit je vier Source- und zwölf Zielprimitiven je Oberfläche. Der Stand
ist laut Johannes manuell gespeichert. Die Dateien
`AISI_v2.139_aisi_floor_study_style.toe` und
`AISI_v2.140_coherent_chairs_validated.toe` sind am 2026-10-07 im
Projektordner verifiziert; Version 140 stimmt per SHA-256 mit der
unnumerierten Datei `AISI_v2_coherent_chairs_validated.toe` überein.
Kein TD-Zugriff, automatisches Speichern oder erneutes Öffnen während der
Offline-Validierung. Die physische Raumprüfung bleibt aufgeschoben.

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

Johannes erklärt am 2026-10-19 die separate Study-/Pilot-Validierung für
nicht mehr erforderlich. Sie ist damit kein offener Folgeauftrag der
abgeschlossenen Inbetriebnahme; daraus wird keine zusätzliche physische
Study-Testbestätigung abgeleitet. Study-Code und Trialdefinitionen unverändert.

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

Erster manueller Aufruf des Tabletop-Isolationshelfers bricht beim Transparent-
TOP ab: `par[name] = 0` wird von TD nicht als Wertzuweisung akzeptiert.
Korrigiert auf `par[name].val = 0`; Testdouble lehnt die falsche API nun ebenfalls
ab. 59 fokussierte Tests erneut bestanden. Fehler liegt vor Anschluss des neuen
Zweigs und im abgesicherten Rücknahmeblock; tatsächlicher TD-Rückfallzustand
nicht automatisch gelesen. Erneute Helferausführung/Liveprüfung noch offen.

Zweiter Live-Aufruf zeigt zusätzlich fehlenden Constant-TOP-Parameter bei
der angenommenen RGBA-Namensfolge. Helfer löst RGB und Alpha nun vollständig
vor Wertzuweisung auf (insbesondere alpha statt colora). Fehlende Parameter
liefern verfügbare Namen statt None-Zugriff. Testdouble erfindet keine Parameter
mehr; beide Alpha-Varianten und fehlender Kanal geprüft. 60 Tests bestanden,
erneute manuelle Anwendung offen. Keine reale Erfolgsbestätigung behauptet.

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

Lag-Eingrenzung am 2026-10-21: Johannes bestätigt Rücknahme des Renderzweigs,
Lag bleibt. GPU-Stichprobe 45 %, ca. 4.5/10 GiB belegt, keine belegte GPU-Sättigung.
Konkrete Offline-Messung derselben aktuellen Fünf-Tisch-Discussion-8-Szene:
prepare_scene_output bei Stärke 0.95 ca. 2287.9 ms, bei 1.0 ca. 0.3 ms.
Die laufende UI hatte 0.95 gespeichert; auf vorgesehenen 100-%-Betrieb über
bestehenden /set-Endpunkt zurückgestellt. Dies ist eine belegte Senderbremse,
kein vollständiger Ende-zu-Ende-Latenznachweis.
Währenddessen öffnet Johannes TD-Version 149 neu und startet Layout-Launcher;
zuvor laufende Adapter/Sender blieben offen, daher zwei Ketten je Modul.
Alle Adapter-/Senderprozesse gezielt bereinigt und genau eine validierte Kette
mit beiden Bindings/frischer Szene/0.05-s-Intervall gestartet; neue Vision/TD
beibehalten. Protokolle lokal `data/aisi/debug/lag_diagnosis_20261021/`.
Danach Discussion 8/100 %, fünf Tische, ready. Clipping-Helfer noch nicht live
angewendet, physische Lag-Bestätigung nach Bereinigung noch offen.

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

Erster manueller Polygon-Clipping-Aufruf bricht vor Mutation in der neuen
Vorprüfung ab: echte TD-Poly besitzt keine .vertices-Eigenschaft. Umgestellt
auf direkte Vertex-Iteration (for vertex in primitive); Testdouble enthält
keine erfundene vertices-Eigenschaft mehr. 16 fokussierte Checks bestanden.
Vorheriger Graph durch diesen Aufruf unverändert; erneute Anwendung offen.

Polygon-Clipping manuell angewendet: sechs Callbacks, keine zusätzlichen
Renderer. Johannes meldet anschließend keine Zielrechtecke mehr auf Tabletop,
Sources/Pfeile aber weiterhin sichtbar. Ursache noch offen: keine eigene
geometrische Überlappung, falsche Beschneidung oder TD-Callbackfehler unterscheiden.
Lesender Helfer inspect_tabletop_target_clip.py vorbereitet: aktuelle Source-/
Target-Posen, SOP-Fehler und tatsächliche Primitive; ungeclippte Kontur in reinem
Python-Recorder mit Originalfunktion nachbilden, erwarteten eigenen Schnitt
ermitteln. Keine TD-SOP-/Operator-Mutation, kein Force-Cook. Bericht nach
manueller Ausführung lokal data/aisi/debug/tabletop_target_clip.json auswerten.

Lesender Livebericht tabletop_target_clip.json beweist Ursache für leere Ziele:
Source-SOP enthält acht Punkte, aber die kanonische Fläche referenziert nur vier.
Vier zusätzliche unreferenzierte appendPoly-Defaultpunkte wurden fälschlich als
zusätzliche Randvertices verwendet. Alle fünf erwarteten Schnitte deshalb leer,
obwohl Source-/Target-Posen nahezu deckungsgleich; keine Callbackfehler.
Korrektur v2 verwendet ausschließlich Vertices des einen Source-Flächenpolygons,
keine Änderung am vorhandenen Surface-SOP oder physischer Maskenkette. Regressions-
fixture bildet zusätzliche unbenutzte Punkte ab. 18 fokussierte Tests bestanden;
Replay aller fünf berichteten Posen liefert wieder sichtbare Zielsegmente.
Helfer aktualisiert bestehende v1-Callbacks ohne doppelten Wrapper und behält die
ursprüngliche Rückfallkopie. Erneute manuelle Ausführung/Liveprüfung noch offen.

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
