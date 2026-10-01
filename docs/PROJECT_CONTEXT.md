# AISI Project Context

Last updated: 2026-09-30

## 1. Purpose

AISI is a research prototype for adaptive, spatially augmented learning environments. It senses and tracks room objects, represents the room in a shared metric coordinate system, generates or loads target configurations, and communicates spatial transformations through projections on the floor and on tabletops.

The current repository contains three related but distinct lines of work:

1. general AISI layout generation (`input`, `groupwork`, `discussion`);
2. the controlled dual-surface Study pipeline;
3. live computer vision/tracking and TouchDesigner integration.

Do not assume that a change in one line should alter the others.

## 2. Evidence and confidence

This handoff distinguishes three evidence levels:

- **Repository-confirmed:** directly inspected in the local checkout on 2026-09-28.
- **History-reported:** reported in prior project chats or agent completion notes, but not re-run during handoff creation.
- **Physical-room-reported:** reported as tested in the physical setup; cannot be established from repository checks alone.

## 3. Repository state at handoff

Repository-confirmed:

- macOS checkout: `/Users/Johannes/dev/Promotion_Prototypen/AISI`
- branch: `vision/wip-dark-proposals`
- HEAD: `5141e77` — `Finalize Rect input templates`
- remote branch matched after the Rect Input checkpoint was pushed.

Dirty tracked files:

- `AGENTS.md`
- `NOTES.md`
- `TODO.md`
- `docs/DECISIONS.md`
- `docs/PROJECT_CONTEXT.md`

Untracked analysis code and generated directories:

- `docs/RECT_GROUPWORK_DECISION_SESSION.md`
- `scripts/analyze_rect_groupwork_decision_basis.py`
- `data/aisi/debug/rect_layout_templates/final_rect_templates_2026-09-25/`
- `data/aisi/debug/rect_layout_templates/groupwork_templates_analysis_2026-09-25/`
- `data/aisi/debug/rect_layout_templates/input_5_table_3plus2_analysis_2026-09-25/`
- `data/aisi/debug/rect_layout_templates/input_layout_audit_2026-09-25/`
- `data/aisi/debug/rect_layout_templates/staggered_input_analysis_2026-09-25/`
- `data/aisi/debug/rect_layout_templates/groupwork_decision_basis_2026-09-28/`

These changes belong to the user. Do not clean, reset, overwrite, or bulk-stage them.

## 4. Coordinate system and physical setup

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

## 5. Main runtime paths

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

Validierungsreihenfolge: Nach jeder produktiven Format-Umsetzung wird das
Format einzeln über die Simulationspipeline mit Room Editor,
Learning-Format-Interface und OSC geprüft. Ein kurzer gemeinsamer Durchlauf
folgt erst danach und prüft Formatwechsel sowie gemeinsame Schnittstellen.

State files:

- `data/aisi/scenes/simulated/live_scene.json`
- `data/aisi/state/learning_format.json`

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

Die aktive Definition `pilot_v7` übernimmt T1–T4 unverändert aus `pilot_v6`
und ergänzt davor eine nicht-experimentelle Familiarization. Sie verwendet
einen Rect-Tisch von `(160, 250, 0°)` nach `(260, 250, 25°)` und einen neutralen
Teilnehmerstart bei `(250, 440)`. Der Controller-Ablauf lautet
`HOME → FAMILIARIZATION → READY_FOR_STUDY → EXPERIMENTAL`. Familiarization ist
direkt als TASK auswählbar und besitzt keine separate Workflow-Zeile oder
eigene Reset-/Finish-Schaltflächen. Während der Übung kann die Versuchsleitung
bei identischer Geometrie zwischen `FLOOR_ONLY` und `DUAL_SURFACE` wechseln.
Die Auswahl von T1–T4 beendet die Übung und lädt den gewählten Trial, startet
ihn aber nicht. Erst danach kann der Trial separat gestartet werden.
Practice-Ereignisse erhöhen weder Run- noch Attempt-Zähler und sind durch
`is_practice=true`, `trial_role=PRACTICE` sowie
`task_id=FAMILIARIZATION` automatisch aus `study_metrics` ausgeschlossen.

### Vision/tracking path

Current code is primarily under `src/vision/`; earlier sensing/replay infrastructure remains under `src/aisi_sensing/`.

History- and physical-room-reported baseline:

- Rect tables are detected with OBB geometry and transformed to world coordinates;
- multi-table association, occlusion handling, and reacquisition were stabilized;
- the physical test later showed no new track “rebirths” during the referenced run;
- a tracking-only projection mode renders an inner tabletop contour and outer floor contour;
- adaptive smoothing is lighter during motion and stronger at rest.

Treat this as a frozen baseline unless a task explicitly concerns tracking.

## 6. TouchDesigner architecture

The authoritative manually maintained project is external to the repository:

`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.toe`

Repository builders and snapshots are references, not guaranteed representations of the current physical graph.

Physical-room-reported structure:

- modes include Calibration and Content;
- Content can switch between Tracking and AISI/Study paths;
- floor content, tabletop content, and table masks share downstream calibration/projector stages;
- floor/tabletop/mask ordering is physically consequential;
- Calibration + Floor requires a black table-mask input so the inverted mask becomes white and leaves the floor image unchanged.

Bekannte Plot-Backend-Regel:

- Der interaktive Room Editor verwendet `tkinter` direkt und initialisiert kein
  Matplotlib-Backend. Dadurch bleibt sein Import in nicht-grafischen Tests frei
  von macOS-Tk-Initialisierung.
- Headless PNG-/Debug-Generierung wählt `Agg`, bevor `pyplot` importiert wird.

- Room Editor uses `TkAgg` on macOS;
- `scripts/generate_rect_layout_debug_plots.py` selects `Agg` before importing plotting code;
- shared `debug_plotter.py` remains backend-neutral.

## 7. Table geometry

Repository-confirmed canonical types:

| Type | Physical reference | Shape |
| --- | --- | --- |
| `summit` | approximately `157 × 70 × 74 cm` | trapezoidal |
| `sprint` | approximately `82 × 60 × 74 cm` | trapezoidal |
| `rect` | `160 × 80 × 74 cm` | rectangular |

The polygon-aware geometry migration is committed. Relevant logic includes canonical footprints, directional supports, polygon collision/ROI checks, and polygon-aware debug rendering.

Important decisions:

- layout roles are format-bound to table IDs;
- target output is restored to original scene order;
- `strength = 0` yields exact source poses without repair;
- `strength > 0` blends before one final hard-constraint repair;
- the current overall capacity is five tables.

Scout-specific seating/pairing semantics are not finalized. The geometry layer should support later choices without hard-coding one Scout layout grammar now.

## 8. Rect layout generation

### Input — quelladaptive Präsentationsformation

Die festen Rect-Input-Slots aus Commit `5141e77` sind durch eine
quelladaptive Präsentation-plus-Zuhörer-Formation ersetzt. Die
Präsentationsachse folgt der Hauptausdehnung der Source. Der am stärksten vom
Rest abgesetzte Endtisch wird automatisch zur Präsentation; die übrigen Tische
werden unabhängig von ihrer `table_id` mit minimaler Bewegung in die kompakte
Zuhörerformation gebunden. Die Ausgabe bleibt für OSC in der ursprünglichen
Scene Order.

Jeder Rect-Tisch hat genau eine semantische Sitzseite: `70 cm` tief, entlang
der vollständigen Längsseite und an den außenliegenden Ecken abgerundet. Die
Präsentation blickt zur Zuhörerformation, die Zuhörenden entgegengesetzt zur
Präsentation. Alle Tische und Sitzflächen müssen bei `100 %` vollständig in
der ROI liegen und sich nicht überlappen. Für Count 5 weicht die Zielachse nur
bei ansonsten nicht einpassbarer Diagonalgeometrie auf die nächstliegende
Raumachse aus.

Repository- und virtuelle Einzelprüfung über Room Editor,
Learning-Format-Interface, OSC und TouchDesigner sind akzeptiert. Die
physische Raumprüfung für Aufstellung, Projektion und Bewegungsqualität bleibt
offen.

### Groupwork — quelladaptiv produktiv umgesetzt

Für Rect-Groupwork zählen `2–5` werden alle Pair-/Singleton-Partitionen aus
der Ausgangsszene abgeleitet. Starre Zielslots, orthogonale Winkelraster und
eine ID-basierte Paarbildung sind verworfen. `table_id` bewahrt ausschließlich
Identität und ursprüngliche Scene Order.

Der Pair-Seam beträgt `8 cm`. Ein Singleton besitzt zwei volle, je `60 cm`
tiefe Sitz-/Bewegungsstreifen ausschließlich an den Längsseiten; ein Pair
besitzt eine elliptische, mindestens `60 cm` auskragende Clearance. Sämtliche
Zonen müssen vollständig in der ROI liegen. Die beiden äußeren Ecken jedes
Singleton-Streifens sind mit `30 cm` Radius abgerundet, während die Sitzkante
am Tisch über die volle Länge gerade bleibt. Das aggressive Profil minimiert
zuerst Zonenüberlappung, dann maximale und gesamte Bewegung, Rotation,
Kreuzungen und schließlich den Inselabstand.

Die produktive Synthese nutzt denselben Suchkern wie die bestätigten
Count-3-/Count-5-Plots. Bei Teilstärken wird der geblendete Zwischenstand mit
dieser vollständigen Inselgeometrie repariert, nicht mit der generischen
einseitigen Clearance-Reparatur. Für unveränderte Live-Szenen werden Ergebnisse
kurz zwischengespeichert. Die Kandidatensuche prüft nur kanonische Tisch-
Footprints und die beschlossenen Inselzonen; dadurch entfällt die zusätzliche,
fachlich überholte einseitige Standard-Clearance-Prüfung.
Die axiale mittlere Orientierung der beiden Source-Tische ist außerdem eine
starke Präferenz für die Zielrotation eines Pairs; die reine
Source-Verbindungsachse darf sie nicht überschreiben.
Die begrenzte Kandidatenauswahl erhält dafür pro Richtung eine
orientierungstreue Außenvariante, damit eine überlappungsfreie globale
Partition nicht bereits lokal verloren geht.

Repository-validiert am 2026-09-29:

- fokussierte Rect-, Footprint- und Geometrietests: `44` erfolgreich;
- Regressionen für Rotation, Translation, ID-Unabhängigkeit, Determinismus,
  bessere Zuordnung und vollständige Zonenprüfung erfolgreich;
- Learning-Format-Interface, Simulationsadapter und lokaler OSC-Ausgang für
  die Count-5-Regression mit fünf Zieltabellen erfolgreich geprüft.

Die grafische Room-Editor-Interaktion sowie die TouchDesigner- und physische
Raumprüfung bleiben offen. Sie sind nicht durch lokale JSON-/OSC-Prüfungen
abgedeckt.

Die Learning-Format-Simulationsoberfläche steuert Format, Sichtbarkeit von
Personen/Stühlen und die Umbauintensität (`0–100 %`). Der gespeicherte Wert
wird unverändert an die Live-Layoutsynthese übergeben; ältere State-Dateien
ohne Wert starten kompatibel bei `100 %`.

### Discussion

Repository- und virtuell bestätigte Architektur (2026-09-29):

- zentrierter, nach innen gerichteter Ring;
- ROI-sichere Geometrie aus Polygonen und Support-Werten;
- deterministische Winkelreihenfolge der Source stabilisiert Slotbindung und
  Teilbewegungen;
- die absolute globale Ringrotation ist semantisch nicht relevant.

Die freie globale Ringrotation wird mit dem lexikographischen Ziel „maximale,
dann gesamte Bewegung minimieren“ gewählt; bei Count 5 nur innerhalb der
clearance-zulässigen Phasen. Die Source-Winkelreihenfolge bleibt erhalten;
dadurch entstehen keine gekreuzten Zuordnungswege.

Jeder Rect-Discussion-Tisch hat zwei abgerundete, ausschließlich entlang der
Längsseiten liegende Sitz-/Bewegungsflächen mit `50 cm` Tiefe. Diese sind für
den fertigen `100-%`-Zielzustand als harte ROI- und Tischblockierungsbedingung
geprüft. Bei einer niedrigeren Umbauintensität bleibt die sichtbare
Source/Target-Interpolation mit Kollisions-/ROI-Reparatur erhalten. Der
Fünfer-Ring wird für den Zielzustand ohne die frühere zusätzliche Ringreserve
gepackt; sein gemeinsamer Mittelpunkt darf sich nur minimal innerhalb des ROI
verschieben. Die `60 cm`-Groupwork-Flächen bleiben davon unberührt.

Die generierten Counts 1–5 wurden virtuell auf Überlappungsfreiheit,
ROI-Einhaltung und die gemeinsame, nach innen gerichtete Mitte geprüft.
Die Plots zeigen insbesondere für Count 3 und Count 5 eine plausible
regelmäßige Ringanordnung. Eine physische Raum- und TouchDesigner-Prüfung
steht weiterhin aus; daraus folgt derzeit keine Änderungsanforderung.
Die aktuelle Fünf-Tisch-Live-Szene wurde außerdem durch den
Simulationsadapter mit vollständiger Umbauintensität geprüft; sie erzeugt
einen gültigen Discussion-Ring aus der produktiven Layout-Pipeline, nicht aus
dem statischen Fallback.
Die Einzelprüfung in der laufenden TouchDesigner-Simulation ist am 2026-09-30
fachlich akzeptiert worden. Das bestätigt die virtuelle Pipeline, nicht die
physische Raumwirkung oder Projektorkalibrierung.

## 9. Study design and implementation

### Active trials

Repository-confirmed:

- `trials.json` version: `pilot_v7`;
- status: `frozen_for_study`;
- `trials_pilot_v7.json` is the matching frozen snapshot;
- T1–T4 geometry is unchanged from `pilot_v6`; `pilot_v7` adds only the
  non-experimental Familiarization;
- eight trials: T1–T4 × A/B;
- T1/T2 use one active table and no distractors;
- T3/T4 use one active table and two static distractor tables;
- A/B variants are task-specific geometric counterparts;
- tests assert exact coordinates, A/B transforms, participant positions, ROI safety, and snapshot metadata.

The Study README states:

- T1/T3 use viewing axis `x = 250`;
- T2/T4 use viewing axis `y = 250`;
- B is formed by rotating the complete A layout 180° around the workspace center and then mirroring across the participant viewing axis.

### Study task logic

Design intent from project history:

| | low/limited occlusion | increased occlusion |
| --- | --- | --- |
| simpler layout | T1 | T2 |
| denser layout | T3 | T4 |

This is a deliberate 2×2 task-creation logic, but the physical factors may not be perfectly orthogonal. Statistical claims about isolated density or occlusion effects therefore require methodological justification.

T3/T4 matching history:

- T3 reference path: approximately `435 cm`, cumulative rotation `195°`;
- T4 reference path: approximately `427 cm`, cumulative rotation `180°`;
- intended distinction: T3 dense/low-occlusion, T4 dense/high-occlusion.

### Conditions and phases

Repository-confirmed integer mappings:

- modes: Tracking `0`, Study `1`, AISI `2`;
- conditions: Floor-only `0`, Dual-surface `1`;
- phases: Home `0`, Ready `1`, Active `2`, Complete `3`.

The two experimental conditions compare floor-only guidance with dual-surface guidance. Describe the visual-information difference exactly as implemented: Dual-surface may redistribute guidance spatially, not merely add tabletop graphics to an otherwise identical floor rendering.

### Arrival and logging

Repository-confirmed:

- objective translation tolerance: `8 cm`;
- objective rotation tolerance: `5°`;
- confirmation duration: `0.5 s` continuously inside tolerance;
- participant-declared completion is recorded separately;
- arrival entered/confirmed/exited events are logged;
- tracking loss and post-arrival behavior are represented in analysis metrics;
- session metadata includes the active trial-definition SHA-256;
- logs are append-only and participant/session/attempt aware.

The distinction between objective arrival and declared completion is secondary/exploratory unless the analysis plan promotes it explicitly.

## 10. Known documentation drift and risks

Repository-confirmed documentation drift:

- the root `README.md` still describes simulation as the primary workflow and vision as not actively driving the prototype; this no longer captures the committed Study/tracking work;
- the README still describes old rectangular serialization and older layout priorities that have been superseded by polygon geometry and later Study work;
- `docs/PROJECT_STATE_2026-05.md` is a historical snapshot, not current state;
- Rect Input counts 1–5 are now committed and represented in the current handoff documents.

Potential Study-definition inconsistency to review before the next pilot:

- some human-readable `notes` in `trials.json` do not literally match the numeric poses (for example “no rotation” can be misleading for rectangular 180°-equivalent orientations, and a note about one trial target equaling another source should be checked against the actual coordinates).

Do not change frozen geometry casually; first decide whether only the prose notes are wrong or the trial data itself needs a new version.

## 11. Validation status

Repository-confirmed at handoff:

- current branch and dirty diff were inspected;
- current trial definitions and exact-geometry tests were inspected;
- Rect Input and geometry verification passed 33 focused tests after commit `5141e77`;
- Rect Input plots for counts 1–5 were regenerated and visually reviewed;
- `git diff --check` passed before and after the Rect Input commit.

History-reported:

- committed Study/tracking milestones were tested before their commits;
- Groupwork audit reported 7 passing Rect template tests and no production-code changes for that audit;
- headless Rect debug plotting completed after the `Agg` fix.

Physical-room-reported:

- calibration is sufficiently accurate for the current prototype;
- tracking-only projection followed table position and rotation sufficiently well;
- recent reacquisition testing showed no new rebirths in the referenced run.

Future reports must keep these evidence levels separate.
