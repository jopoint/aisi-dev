# AISI Decision Log

Last updated: 2026-09-30

Statuses:

- **Accepted** — treat as binding until deliberately superseded.
- **Frozen** — accepted and protected for the current Study/pilot.
- **Provisional** — current implementation or working assumption; may change after explicit review.
- **Open** — a decision is still required.

## D001 — Shared metric world

Status: **Accepted**

- AISI uses a `500 × 500 cm` world/ROI.
- Center is `(250, 250) cm`.
- TouchDesigner scale is `1 cm = 0.0052 TD units`.
- Axis and rotation conversion must be traced end-to-end before changes.

## D002 — Canonical polygon geometry

Status: **Accepted**

- Collision, ROI, separation, clearance, repair, and debug rendering use canonical table polygons/supports.
- Do not add parallel hard-coded geometry.
- Legacy rectangles remain supported through explicit rectangular dimensions.

## D003 — Table types

Status: **Accepted**

- `summit`: trapezoidal Vitra Scout Summit.
- `sprint`: trapezoidal Vitra Scout Sprint.
- `rect`: `160 × 80 cm` rectangle.
- All currently relevant physical tabletop heights are `74 cm`.

## D004 — Format-bound assignment

Status: **Accepted**

- A format generator binds a semantic slot/role to a specific `table_id`.
- A second global min-cost slot permutation must not reorder those roles afterward.
- Final targets return in original scene order to preserve OSC source/target index coupling.

## D005 — Transformation strength

Status: **Accepted**

- `strength = 0` means exact source poses and no repair.
- `strength > 0` uses source/target blending followed by one final hard-constraint repair.
- Rotation interpolation follows the shortest angular path.
- Repair may override the visually requested strength when necessary for hard constraints.
- Invalid collision/ROI results must not be silently reported as valid.

## D006 — Maximum layout capacity

Status: **Accepted**

- The current `500 × 500 cm` layout-generation path supports at most five tables.
- Six tables must fail before synthesis/repair instead of silently using stale templates.

## D007 — Quelladaptiver Rect Input mit Präsentationsrolle

Status: **Accepted — physische Raumvalidierung bleibt offen**

- Die festen Input-Slots aus Commit `5141e77` sind fachlich abgelöst.
- Die Hauptausdehnung der Source bestimmt die Präsentationsachse. Der an einem
  Endpunkt räumlich am stärksten vom Rest abgesetzte Tisch wird automatisch zur
  Präsentationsrolle; die übrigen Tische werden ohne ID-basierte Rollen nach
  minimaler Bewegung als Zuhörerformation zugeordnet.
- Der Präsentationstisch blickt zu den Zuhörenden, die Zuhörenden blicken zur
  Präsentation. Die semantische Umkehrung wird bei symmetrischen Rect-Tischen
  durch Facing und Sitzseite abgebildet.
- Jeder Tisch besitzt genau eine `70 cm` tiefe Sitz-/Bewegungsfläche an seiner
  Längsseite, mit abgerundeten außenliegenden Ecken. Footprints und Flächen
  müssen im vollständigen `100-%`-Ziel innerhalb der ROI und gegenseitig frei
  sein.
- Für Count 5 darf eine diagonal nicht vollständig passende Formation auf die
  nächstliegende Raumachse ausweichen; die präsentierende Source-Seite bleibt
  erhalten.
- `strength = 0` behält die exakte Source-Pose. Teilstärken bleiben sichtbare
  Source/Target-Interpolation mit Tisch-Kollisions- und ROI-Reparatur.
- Die virtuelle Prüfung über Room Editor, Learning-Format-Interface, OSC und
  TouchDesigner ist akzeptiert; diese bestätigt keine physische Aufstellung,
  Projektion oder Bewegungsqualität im Raum.

## D008 — Rect Groupwork topology

Status: **Accepted und produktiv umgesetzt**

- Starre absolute Zielslots sind verworfen.
- Zielwinkel dürfen nicht auf `0°`, `90°` oder ein anderes Raster beschränkt
  werden.
- `table_id` dient ausschließlich der Identität und der Wiederherstellung der
  ursprünglichen Scene Order, nicht der Pair-Bildung oder Rollenvergabe.
- Jede Groupwork-Sitz-/Bewegungszone muss vollständig innerhalb der
  `500 × 500 cm` ROI liegen.
- Der Rect Pair-Seam beträgt `8 cm`.
- Ein Rect-Singleton erhält zwei mindestens `60 cm` tiefe Sitz-/Bewegungs-
  streifen über die vollständige Breite seiner Längsseiten, jedoch keine
  Sitzflächen an den Stirnseiten. Die zwei dem Tisch abgewandten Ecken jedes
  Streifens sind mit `30 cm` Radius abgerundet; die dem Tisch zugewandte
  Sitzkante bleibt über die volle Breite gerade.
- Ein Rect-Pair erhält eine elliptische mindestens `60 cm` auskragende
  Clearance um seine gemeinsame Geometrie. Die Kurve statt einer quadratischen
  Hülle reduziert die Gewichtung der Pair-Ecken und lässt frei gedrehte Paare zu.
- Die Zielrotation eines Rect-Pairs erhält die axiale mittlere Orientierung
  seiner beiden Source-Tische als starke Präferenz. Die Lage der beiden
  Source-Zentren allein bestimmt keinen Paarwinkel.
- Das aggressive Clearance-Profil minimiert ohne Bewegungsbudget zuerst die
  gesamte Überlappungsfläche aller Sitz-/Bewegungszonen. Erst bei gleicher
  Überlappung minimiert es Bewegung und maximiert anschließend Inselabstand.

Die frühere Auswertung mit globalen Mittelpunkt-Templates, ID-sortierter
Slotbindung und orthogonalen Zielwinkeln darf nicht als Entscheidungsgrundlage
oder Produktionsmodell verwendet werden.

Der produktive Suchkern enumeriert für Counts 2–5 alle Pair-/Singleton-
Partitionen, prüft beide Mitgliederzuordnungen eines Pairs und optimiert lokale
Gruppenmittelpunkte sowie freie Winkel. Er wählt lexikographisch zuerst die
Zonenüberlappung, danach maximale und gesamte Verschiebung, Rotationsänderung,
Kreuzungen und Inselabstand. Bei Teilstärken repariert ein zweiter adaptiver
Suchlauf den geblendeten Zwischenstand mit derselben vollständigen
Inselgeometrie. Die Kandidatenprüfung nutzt dafür die kanonischen Tisch-
Footprints sowie ausschließlich diese beschlossenen Inselzonen; die frühere
einseitige Standard-Clearance ist kein zusätzliches, widersprüchliches
Kriterium. Die begrenzte lokale Kandidatenauswahl muss außerdem je Richtung
orientierungstreue Außenvarianten erhalten, damit sie eine valide
überlappungsfreie Pair-/Singleton-Partition nicht vor der Gesamtauswahl
verwirft. Die Details und bestätigten Plots stehen in
`docs/RECT_GROUPWORK_ADAPTIVE_PROTOTYPE.md`.

## D008a — Validierung über die Simulationspipeline

Status: **Accepted**

- Rect Groupwork wurde einzeln über Learning-Format-Interface,
  Simulationsadapter und lokalen OSC-Ausgang geprüft. Der Room Editor konnte
  in der vorliegenden Automationsumgebung nicht offen gehalten werden und
  bleibt als manuelle GUI-Prüfung offen.
- Das Learning-Format-Interface speichert wieder eine Umbauintensität von
  `0–100 %`; der OSC-Sender übergibt sie unverändert an die Layoutsynthese.
  Neue oder ältere State-Dateien ohne Wert starten kompatibel bei `100 %`.
- Erst nach diesen Einzelprüfungen folgt ein kurzer gemeinsamer Durchlauf für
  Formatwechsel, Scene Order, vollständige Layoutvorschläge und gemeinsame
  OSC-Schnittstellen.

## D009 — Discussion topology

Status: **Accepted**

- Discussion verwendet einen zentrierten, nach innen gerichteten Ring.
- Die absolute globale Ringrotation ist semantisch nicht relevant.
- Die deterministische Winkelreihenfolge der Source stabilisiert die
  Slotbindung und Teilbewegungspfade.
- Die freie globale Ringrotation wird für Counts 2–4 kontinuierlich so gewählt,
  dass die größte, dann die gesamte Tischbewegung minimal wird. Für Count 5
  gilt dieselbe Reihenfolge innerhalb der clearance-zulässigen Phasen. Die
  kreuzungsfreie Winkelreihenfolge der Source bleibt dabei erhalten.
- Jeder Rect-Discussion-Tisch erhält die beidseitigen, an den Außenkanten
  abgerundeten Längsseiten-Sitz-/Bewegungsflächen aus Groupwork, jedoch mit
  einer Tiefe von `50 cm` (Groupwork bleibt bei `60 cm`). Diese Flächen müssen
  im fertigen `100-%`-Ziel vollständig im ROI liegen und dürfen dort keinen
  anderen Tisch blockieren. Zwischenstände der Umbauintensität bleiben die
  sichtbare Source/Target-Interpolation mit Kollisions-/ROI-Reparatur.
- Für Count 5 darf der gemeinsame Mittelpunkt geringfügig von der ROI-Mitte
  abweichen, damit der zentrische Ring samt vollständigen Flächen passt.
- Die virtuelle Prüfung der Counts 1–5 am 2026-09-29 bestätigt
  Überlappungsfreiheit, ROI-Einhaltung und die gemeinsame Mitte. Die physische
  Raumprüfung bleibt offen.
- Die Einzelprüfung über Room Editor, Learning-Format-Interface, OSC-Sender
  und TouchDesigner-Simulation wurde am 2026-09-30 akzeptiert. Eine physische
  Raumprüfung ist damit ausdrücklich noch nicht ersetzt.

## D010 — Scout Groupwork semantics

Status: **Deferred/Open**

- Do not hard-code a universal wide-wide, narrow-narrow, or wide-narrow Scout pairing rule.
- The geometry layer must support arbitrary later side pairings.
- Scout-specific seating and layout grammar require a dedicated design decision.

## D011 — Physical calibration protection

Status: **Frozen**

- Floor and tabletop homographies, local corrections, edge blend, projector transforms, masks/order, scale, and footprints are protected.
- Tabletop plane is `z = 74 cm`.
- Do not edit calibration as part of unrelated feature work.
- Physical correctness must be tested in the running authoritative `.toe` project and room.

## D012 — TouchDesigner source of truth

Status: **Accepted**

- The authoritative project is the manually maintained external `AISI_v2.toe`.
- Repository builders and `.toe` snapshots are references/reconstruction aids only.
- Never overwrite the master from builders without explicit instruction.

## D013 — Rendering backends

Status: **Accepted**

- Interactive Room Editor on macOS: `TkAgg`.
- Headless plot generation: `Agg`, selected before importing `pyplot`.
- Shared plotting modules remain backend-neutral.

## D014 — Study task structure

Status: **Accepted as design intent**

T1–T4 are arranged as:

| | low/limited occlusion | increased occlusion |
| --- | --- | --- |
| simpler layout | T1 | T2 |
| denser layout | T3 | T4 |

This is a deliberate 2×2 design structure, not a single linear complexity scale. Whether density and occlusion are sufficiently orthogonal for factorial inference remains a methodological question.

## D015 — Study conditions

Status: **Frozen for current pilot**

- Floor-only and Dual-surface are within-study guidance conditions.
- The paper/method description must match the actual rendering behavior.
- Do not automatically characterize Dual-surface as “identical floor guidance plus extra tabletop information” if guidance is spatially redistributed between surfaces.

## D016 — Active trial version

Status: **Frozen**

- Active trial definition: `pilot_v7`.
- Matching snapshot: `trials_pilot_v7.json`.
- T1–T4 einschließlich A/B-Geometrie sind byte-inhaltlich aus `pilot_v6`
  übernommen; `pilot_v7` ergänzt nur die Familiarization-Konfiguration.
- Any geometry change creates a new named snapshot before replacing `trials.json`.
- Session metadata records the active definition SHA-256.

## D017 — A/B transformation

Status: **Frozen**

- B preserves relative task geometry while changing viewpoint.
- T1/T3 use viewing axis `x = 250`.
- T2/T4 use viewing axis `y = 250`.
- Tests enforce the task-specific transformation and involution behavior.

## D018 — Study state mappings

Status: **Frozen**

- Mode: Tracking `0`, Study `1`, AISI `2`.
- Condition: Floor-only `0`, Dual-surface `1`.
- Phase: Home `0`, Ready `1`, Active `2`, Complete `3`.
- Preserve OSC addresses and numeric mappings.

## D019 — Objective arrival

Status: **Frozen for current implementation**

- translation error threshold: `≤ 8 cm`;
- rotation error threshold: `≤ 5°`;
- confirmation requires `0.5 s` continuously inside tolerance;
- objective arrival and participant-declared completion are distinct events.

## D019a — Familiarization vor der Study

Status: **Frozen for current pilot**

- Vor Block 1 liegt eine zeitlich offene Familiarization mit genau einem
  Rect-Tisch.
- Source ist `(160, 250, 0°)`, Target ist `(260, 250, 25°)`, der neutrale
  Teilnehmerstart ist `(250, 440)` mit `40 cm` Radius.
- `FLOOR_ONLY` und `DUAL_SURFACE` verwenden exakt dieselbe Geometrie und die
  vorhandenen Study-Visualisierungsregeln; ein Live-Wechsel in beide Richtungen
  ist erlaubt.
- Practice zählt nicht als T1–T4, erhöht `run_index` und `attempt` nicht und
  erscheint nicht in `study_metrics`.
- Rohdiagnostik bleibt zulässig, ist aber mit `study_workflow=FAMILIARIZATION`,
  `trial_role=PRACTICE`, `is_practice=true` und
  `task_id=FAMILIARIZATION` markiert.
- Familiarization ist eine TASK-Auswahl ohne eigene Workflow-, Reset- oder
  Finish-Schaltflächen. Die Auswahl von T1–T4 führt zu `READY_FOR_STUDY`, lädt
  den Trial und startet ihn nicht; der Start bleibt separat.

## D020 — Study outcome hierarchy

Status: **Proposed; not yet a binding analysis plan**

Recommended hierarchy from project discussion:

- Primary: completion time plus a movement/efficiency measure.
- Secondary: position/rotation accuracy and objective arrival.
- Exploratory: initial action latency, corrections, arrival-to-completion behavior, and qualitative strategies.

Finalize this before data collection/analysis claims. With a small pilot sample, emphasize effect sizes, uncertainty, and task-specific patterns over strong interaction claims.

## D021 — Tracking baseline

Status: **Frozen unless tracking work is explicitly requested**

- Current-room OBB tracking, table association, occlusion/reacquisition behavior, tracking-only projection, and adaptive smoothing form the present baseline.
- Do not tune thresholds or smoothing incidentally during layout or Study UI work.

## D022 — Runtime and participant data

Status: **Accepted**

- Runtime state, calibration captures, debug outputs, training artifacts, and Study run logs are not staged by default.
- No new participant-data storage, telemetry, upload, or network service without explicit approval.
