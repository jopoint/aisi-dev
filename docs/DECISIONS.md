# AISI Decision Log

Last updated: 2026-09-28

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

Status: **Accepted in current worktree**

- The current `500 × 500 cm` layout-generation path supports at most five tables.
- Six tables must fail before synthesis/repair instead of silently using stale templates.

## D007 — Rect Input templates

Status: **Provisional until the dirty worktree is reviewed and committed**

- Counts 1–5 use explicit deterministic slots.
- All rotations are `0°` and facing is `−Y`.
- Slots are:

```text
1: (250,250)
2: (140,250), (360,250)
3: (122,150), (250,250), (378,350)
4: (140,155), (360,155), (140,345), (360,345)
5: (110,150), (250,250), (390,150), (110,350), (390,350)
```

- Old global `220 cm` column and `190 cm` row rules are not the new general generator rules.

## D008 — Rect Groupwork topology

Status: **Provisional/Open**

- Current topology: pairs plus optional singleton.
- Rect pairs are vertical at `rotation = 0°`, with outward-facing seating sides.
- Current seam gap is `4 cm`, yielding `84 cm` center separation.
- The pair represents a shared work island, not face-to-face seating across the seam.

Still open:

- whether `4 cm` is enough for physical and tracking tolerance;
- final coordinates for counts 3–5;
- whether the singleton is pedagogically an individual station or part of an open group;
- whether all seat/movement zones must be fully inside the ROI (recommended: yes);
- implementation of the final count-5 solution.

## D009 — Discussion topology

Status: **Accepted**

- Discussion uses a centered inward-facing ring.
- Global ring rotation is semantically unimportant.
- Deterministic source angular order stabilizes binding and partial-strength paths.

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

- Active trial definition: `pilot_v6`.
- Matching snapshot: `trials_pilot_v6.json`.
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
