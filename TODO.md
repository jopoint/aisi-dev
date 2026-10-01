# AISI TODO / Handoff Checklist

Last updated: 2026-09-30

This list separates immediate repository hygiene, current layout work, Study readiness, and deferred research work. Do not execute all items automatically; use it to select a coherent next task.

## Completed — Rect Input checkpoint

- [x] Inspect `git status` and the complete diff before editing.
- [x] Review the Rect Input implementation in:
  - `src/aisi/generation/layout_synthesizer.py`
  - `tests/test_rect_template_layouts.py`
  - `scripts/generate_rect_layout_debug_plots.py`
  - `NOTES.md`
- [x] Re-run the focused Rect layout tests in the actual repository environment.
- [x] Re-run `git diff --check`.
- [x] Inspect the final count-1–5 Input plots, especially counts 3 and 5.
- [x] Keep the generated debug directories untracked for this checkpoint.
- [x] Commit and push the Rect Input block after explicit user approval.
- [ ] Validate Rect Input counts 1–5 in the physical room.

Completed in `5141e77` (`Finalize Rect input templates`). `NOTES.md` remains a
separate uncommitted documentation change, and the generated debug directories
remain untracked. Repository and plot verification is complete; physical-room
validation remains open.

Completion criteria:

- the dirty diff is understood;
- tests are current rather than only history-reported;
- no unrelated/runtime artifacts are staged;
- Input counts 1–5 are deliberately committed and pushed.

## P0 — Quelladaptiver Rect Input mit Präsentationsrolle

- [x] Feste Slots, globales Facing `−Y` und die frühere `0°`-Vorgabe ablösen.
- [x] Präsentationsachse und räumlich vordersten Präsentationstisch aus der
  Source ableiten; Zuhörer ohne ID-basierte Rollen lokal zuordnen.
- [x] Je eine volle, außen abgerundete `70 cm`-Sitz-/Bewegungsfläche an der
  semantischen Längsseite pro Tisch als harte Zielbedingung prüfen.
- [x] Counts 1–5 im Room Editor, Learning-Format-Interface, OSC und
  TouchDesigner-Simulation bei `100 %` visuell prüfen.
- [x] Nach der Sichtprüfung einen fokussierten Input-Commit erstellen.

## Verworfen — starre Rect-Groupwork-Entscheidungsgrundlage

- [x] Treat full seat/movement clearance inside the ROI as a hard requirement.
- [x] Analyze pair seams of `4`, `6`, `8`, `10`, and `12 cm`.
- [x] Maximize the minimum footprint gap between separate islands.
- [x] Compare an independent singleton with a singleton attached to an open group.
- [x] Validate candidate geometry with the canonical table footprints and directed clearance zones.
- [x] Generate and inspect only the count-3 and count-5 comparison plots.
- [x] Record a recommendation without changing production Groupwork logic.

Diese Auswertung darf nicht weiterverwendet werden: Die globalen Zielpositionen,
die orthogonalen Zielwinkel und die ID-basierte Slotbindung ignorieren die
Ausgangsgeometrie. Ihre Plots bleiben nur als negative Regression-Cases erhalten.

## P0 — Quelladaptiver Rect-Groupwork-Prototyp

- [x] Alle Pair-/Singleton-Partitionen für Counts 2–5 enumerieren.
- [x] Lokale, frei gedrehte Gruppen aus den beteiligten Ausgangstischen ableiten.
- [x] Beide Mitgliederzuordnungen je Pair prüfen.
- [x] Harte Kollisions-, ROI- und vollständige Clearance-Prüfungen integrieren:
  Singletons mit zwei vollen `60 cm`-Streifen nur an Längsseiten, Pairs mit
  einer elliptischen `60 cm`-Clearance.
- [x] Im aggressiven Clearance-Profil Zonenüberlappungen ohne Bewegungsbudget
  minimieren; erst danach Bewegungsaufwand und Inselabstand optimieren.
- [x] Rotations-/Translationsäquivarianz, ID-Unabhängigkeit, Determinismus und
  bessere Zuordnung gegenüber dem verworfenen ID-Referenzmodell testen.
- [x] Aussagekräftige Count-3- und Count-5-Plots mit Zuordnung und Metriken erzeugen.
- [x] Die Prototyp-Plots fachlich bestätigen: aggressive Clearance-Auswahl mit
  `0 cm²` Zonenüberlappung für Count 5 ist akzeptiert.
- [x] Die produktive, quelladaptive Rect-Groupwork-Implementierung beauftragen
  und für Counts 2–5 umsetzen.
- [x] Rect Groupwork einzeln über Learning-Format-Interface,
  Simulationsadapter und lokalen OSC-Ausgang prüfen.
- [x] Die Simulationspipeline auf vollständige Layoutvorschläge (`100 %`)
  festlegen und die veränderbare Umbauintensität aus Interface und Zustand
  entfernen.
- [x] Die Count-5-Kandidatensuche auf die beschlossenen Inselzonen begrenzen;
  die lokale Vorauswahl behält dabei auch orientierungstreue, nach außen
  versetzte Kandidaten für eine überlappungsfreie Gesamtkomposition.
- [x] Rect-Paarrotationen an der axialen mittleren Source-Ausrichtung stark
  priorisieren; eine räumliche Verbindungsachse allein darf die Tischrotation
  nicht mehr bestimmen.
- [x] Die zwei Singleton-Sitzstreifen an ihren vom Tisch abgewandten Ecken mit
  `30 cm` Radius abrunden; die vollständige gerade Sitzbreite am Tisch bleibt
  erhalten.
- [ ] Die interaktive Rect-Groupwork-Prüfung im Room Editor sowie in
  TouchDesigner manuell durchführen.
- [ ] Nach den Einzelprüfungen einen kurzen formatübergreifenden Pipeline-
  Durchlauf für Formatwechsel, Scene Order, vollständige Layoutvorschläge und
  OSC-Kopplung machen.

## P0 — Pilot/Study readiness review

- [x] Eine nicht-experimentelle Familiarization vor Block 1 ergänzen: ein
  Rect-Tisch, identische Geometrie für Floor-only und Dual-surface, direkte
  Auswahl in der TASK-Zeile ohne eigene Practice-Schaltflächen, keine
  Trial-Zählung und automatischer Ausschluss aus
  `study_metrics` (`pilot_v7`; T1–T4 unverändert aus `pilot_v6`).
- [ ] Familiarization im autoritativen TouchDesigner-Projekt und im physischen
  Raum prüfen, einschließlich Live-Wechsel beider Visualisierungsmodi.

- [ ] Physically run all eight `pilot_v7` trials in both conditions (T1–T4
  geometry unchanged from `pilot_v6`).
- [ ] Verify HOME, READY, ACTIVE, and COMPLETE transitions in the authoritative TouchDesigner project.
- [ ] Verify floor-only and dual-surface visuals match the written method description.
- [ ] Verify active-table binding and distractor binding for T3/T4 under real tracking.
- [ ] Verify objective arrival (`8 cm`, `5°`, `0.5 s`) behaves acceptably with real tracking jitter.
- [ ] Verify participant-declared completion remains independent from objective arrival.
- [ ] Verify logs, session manifest, attempt/run indices, tracking-loss intervals, and trial-definition hash.
- [ ] Review `trials.json` human-readable notes for consistency with numeric poses.
- [ ] If geometry changes are required, create `trials_pilot_v7.json` before updating the active file.

Done when:

- a complete participant-like session can be run without manual data repair;
- visuals, tracking, controller state, and logs stay synchronized;
- every physical deviation is either fixed or documented.

## P1 — Freeze the analysis plan before data collection

- [ ] State one primary research question comparing Floor-only and Dual-surface.
- [ ] State a secondary/exploratory question about task-specific differences.
- [ ] Describe T1–T4 as a 2×2 design structure without claiming unverified orthogonality.
- [ ] Define exactly what information appears on each surface in each condition.
- [ ] Choose primary, secondary, and exploratory outcomes.
- [ ] Decide whether the small sample is framed as pilot/exploratory.
- [ ] Predefine treatment of aborted trials, tracking loss, missing objective arrival, and repeated attempts.
- [ ] Document apparatus accuracy, tracking frequency/latency, projection, and calibration sufficiently for the paper.

Done when:

- implementation, Study protocol, and paper language use the same definitions;
- metrics are prioritized before inspecting participant outcomes.

## P1 — Documentation sync

- [ ] Update the root `README.md`; its current prototype-status, vision, geometry, and priority sections are outdated.
- [ ] Mark `docs/PROJECT_STATE_2026-05.md` clearly as historical or replace it with a dated current state.
- [ ] Link `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, and `TODO.md` from the README.
- [ ] Ensure macOS and Windows launch instructions reflect actual supported workflows.
- [ ] Document the current Study controller, active trial version, logging, and metrics commands.
- [ ] Keep physically confirmed facts separate from repository-only verification.

## P1 — Focused regression commands to establish

There is no canonical repository-wide command. Confirm and document the narrowest working commands for:

- [ ] Rect template layouts and geometry;
- [ ] Study trial definitions;
- [ ] Study control/state transitions;
- [ ] Study tracking/binding;
- [ ] Study logging and metrics;
- [ ] TouchDesigner builder structure tests;
- [ ] vision table association and tracking-only OSC.

Do not install optional dependencies merely to expand test scope.

## P2 — General layout follow-up

- [x] Discussion Counts 1–5 nach der Fünf-Tisch-Kapazitätsänderung virtuell
  und in der TouchDesigner-Simulation prüfen (2026-09-30); die physische
  Raumprüfung bleibt offen.
- [ ] Verify mixed Summit/Sprint/Rect layouts after current Rect-specific work is stable.
- [ ] Design Scout-specific seating and Groupwork semantics as a dedicated task.
- [ ] Decide which Summit/Sprint sides may pair and how seating zones are derived.
- [ ] Preserve generic polygon support so the decision does not require a geometry rewrite.

## P2 — Tracking follow-up

- [ ] Keep the current tracking baseline frozen until a reproducible failure is recorded.
- [ ] If tuning resumes, capture the failing scene/log first and compare against the successful reacquisition baseline.
- [ ] Separate table detection, association, smoothing, projection alignment, and Study binding when diagnosing failures.

## P2 — Repository hygiene

- [ ] Decide whether `.gitignore` should cover recurring debug/runtime folders.
- [ ] Never blanket-ignore data that is intentionally versioned, such as frozen trial definitions.
- [ ] Keep model files, calibration captures, run logs, and generated plots under explicit policy rather than ad hoc staging.

## Open decisions requiring Johannes

- [x] Der Rect-Groupwork Pair-Seam beträgt `8 cm`.
- [x] Every Groupwork seat/movement zone must lie completely inside the `500 × 500 cm` ROI.
- [x] Groupwork-Singletons sind eigenständige Arbeitsstationen.
- [x] Rect-Singletons erhalten zwei volle, ausschließlich an den Längsseiten
  liegende `60 cm`-Sitz-/Bewegungsstreifen; Pairs erhalten eine elliptische
  `60 cm`-Clearance um die gemeinsame Gruppe. Alle Flächen liegen in der ROI.
- [ ] Is `pilot_v7` ready for data collection, or still a pre-pilot
  configuration? (T1–T4 geometry remains `pilot_v6`.)
- [ ] Which measures are formally primary versus exploratory?
- [x] Commit the finalized Rect Input block before Groupwork implementation starts (`5141e77`).
