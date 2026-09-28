# AISI — Instructions for Codex

## Goal

AISI is a research prototype for adaptive, spatially augmented learning environments. It combines room sensing, spatial interpretation, layout generation, study control, and projected guidance on floors and tabletops.

Prefer:

- reliable, minimal, reversible changes;
- existing interfaces and dependencies;
- explicit assumptions over invented requirements;
- focused tests over broad refactoring;
- deterministic behavior for study sessions;
- separate reporting of code verification and physical-room validation.

The user's current prompt overrides this file. More specific `AGENTS.md` files may add local rules.

## Current handoff

Read these files before substantial work:

- `docs/PROJECT_CONTEXT.md` — current architecture and verified state;
- `docs/DECISIONS.md` — accepted decisions and protected invariants;
- `TODO.md` — ordered work and open decisions.

The handoff was prepared on 2026-09-28 from:

- local repository inspection;
- branch and working-tree status;
- current source, tests, and study definitions;
- prior AISI project conversations.

Where a statement has not been re-tested, the handoff labels it as reported rather than verified.

## Working method

- Inspect the relevant implementation and data flow before editing.
- Make the smallest coherent change that satisfies the task.
- Preserve interfaces unless the task explicitly requires changing them.
- Ask only when a decision materially affects physical behavior, calibration, data contracts, study design, or participant data.
- Do not modify unrelated files, formatting, dependencies, or generated artifacts.
- Run the narrowest relevant existing tests/checks.
- Inspect the final diff when Git access allows it.
- Never discard unrelated user changes.

## Repository and current branch

Known local paths:

- macOS: `/Users/Johannes/dev/Promotion_Prototypen/AISI`
- Windows: `C:\dev\Promotion_Prototypen\AISI`

Handoff-time Git state:

- branch: `vision/wip-dark-proposals`
- HEAD: `6fae98a` (`Finalize study logging and metrics`)
- the branch matched `origin/vision/wip-dark-proposals` at inspection time;
- the worktree was dirty with Rect layout work and debug artifacts.

Do not overwrite or clean the dirty worktree. Inspect `git status` and the diff before editing.

## Main areas

- `src/aisi/`: scene interpretation, table geometry, layout generation, simulation, study control, logging, analysis, and OSC.
- `src/aisi_sensing/`: earlier sensing/replay pipeline.
- `src/vision/`: current computer vision and tracking.
- `td_builders/`: partial TouchDesigner builders and reconstruction helpers.
- `data/aisi/study/`: active and frozen study trial definitions.
- `tests/`: focused regression tests; there is no single canonical repository-wide test command.

Do not assume the dependencies, entry points, or tests of `aisi`, `aisi_sensing`, and `vision` are interchangeable.

Never manually edit generated artifacts such as:

- `*.egg-info`;
- `__pycache__`;
- compiled/cache files;
- runtime logs and debug plots unless the task explicitly concerns those artifacts.

## Current development focus

Two states coexist and must not be confused:

1. The Study/Tracking baseline is committed and should remain stable unless the user explicitly asks to change it.
2. Rect layout generation has newer uncommitted work. Rect Input counts 1–5 have explicit proposed/finalized templates in the worktree; Rect Groupwork counts 1–5 were audited but still require a deliberate implementation decision.

The current worktree, not an older README or chat summary, is the source of truth for code state.

## Study protection

`data/aisi/study/trials.json` is the active Study geometry and currently identifies itself as `pilot_v6`, `frozen_for_study`. `trials_pilot_v6.json` is the matching frozen snapshot.

Before changing active trial geometry:

1. inspect the active definition and tests;
2. create a new named snapshot (for example `trials_pilot_v7.json`);
3. update the active definition deliberately;
4. update exact-geometry and metadata tests;
5. regenerate plots and perform physical validation;
6. record the reason for the change.

Do not silently change:

- task/variant semantics;
- participant start positions;
- A/B counterbalancing transforms;
- arrival thresholds;
- logging schema;
- condition or phase integer mappings.

Do not add participant-data storage, telemetry, uploads, or network services without explicit approval.

## Coordinate and geometry rules

ROI/world space is `0–500 cm` on X and Y.

TouchDesigner conversion currently uses:

- center `(250, 250) cm`;
- `1 cm = 0.0052 TD units`;
- X: `(world_x - 250) * 0.0052`;
- Y: `-(world_y - 250) * 0.0052`.

Trace the complete scene → OSC → TouchDesigner path before changing axes, units, origins, rotation signs, or coordinate transforms.

Use the repository's canonical polygon/table-geometry implementation. Do not introduce parallel hard-coded footprint logic.

Keep source and target poses associated with the same `table_id` and OSC index.

Current physical table references:

- `summit`: Vitra Scout Summit, trapezoidal, approximately `157 × 70 × 74 cm`;
- `sprint`: Vitra Scout Sprint, trapezoidal, approximately `82 × 60 × 74 cm`;
- `rect`: rectangular, `160 × 80 × 74 cm`.

Scout-specific seating and pairing grammar remains intentionally deferred. Do not invent it as part of unrelated layout work.

## Layout-generation invariants

- Current layout capacity is at most five tables in the `500 × 500 cm` ROI.
- `transformation_strength = 0` means exact source poses with no repair.
- For `strength > 0`, blending occurs before final constraint repair.
- Rotations interpolate over the shortest angular path.
- Format-generated roles remain bound to their `table_id`; do not reintroduce a second global slot permutation.
- Output returns to original scene order for OSC compatibility.
- Collision and ROI violations must never be silently emitted as valid layouts.
- Preserve learning-format semantics for `input`, `groupwork`, and `discussion`.

For the exact current Rect Input slots and unresolved Groupwork questions, consult `docs/PROJECT_CONTEXT.md` and `docs/DECISIONS.md`.

## TouchDesigner protection

Authoritative physical TouchDesigner master:

`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.toe`

Do not modify, regenerate, overwrite, move, or rename it unless Johannes explicitly requests it.

Repository `.toe` files and builders are development snapshots/reconstruction tools, not automatically the source of truth for the active physical graph.

Protected unless explicitly requested:

- floor/tabletop homographies;
- calibration points;
- projector transforms;
- local correction grids/shaders;
- edge blending;
- physical/world scale;
- projector footprints;
- floor/tabletop mask ordering.

Do not infer the active manual TouchDesigner graph solely from repository builders. Do not claim projection correctness without testing the running `.toe` file in the room.

Known rendering convention:

- interactive Room Editor: `TkAgg` on macOS;
- headless PNG/debug generation: select `Agg` before importing `pyplot`;
- shared plotting modules should remain backend-neutral.

## OSC and integration safety

Preserve existing OSC contracts unless migration is explicitly requested.

In particular:

- keep source/target tables paired by index;
- preserve compatibility aliases;
- preserve numeric types expected by TouchDesigner;
- handle object count, missing objects, stale objects, and visibility explicitly;
- preserve Study enum mappings and `/study/...` addresses.

Do not claim physical projection/tracking correctness unless it was tested in the running TouchDesigner project or physical room.

## Dependencies

- Inspect existing imports and environments before adding dependencies.
- Do not broaden dependency declarations incidentally.
- Prefer existing standard-library or repository solutions.
- Do not install missing optional dependencies merely to make unrelated suites pass.

## Validation and completion

Before declaring a task complete:

1. Run the narrowest applicable tests/checks.
2. Run a relevant synthetic/offline integration check when appropriate.
3. Inspect the diff.
4. Report changed files, assumptions, tests, remaining risks, and required physical validation.

Do not invent a repository-wide test/lint/typecheck command if none is documented.

## Git safety

- Never reset, discard, or overwrite unrelated changes.
- Do not stage runtime data or generated debug artifacts unless requested.
- If Git reports dubious ownership, do not modify global Git configuration or bypass the protection.
- Do not create commits unless the user asks.

## Communication

Be concise and result-oriented. For substantial tasks report:

- what changed;
- verification result;
- remaining risk;
- next concrete physical or software check.

When referring to known TouchDesigner nodes, use `name (operator type)`.
