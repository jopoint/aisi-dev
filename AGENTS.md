# AISI — Instructions for Codex

## Goal

AISI is a research prototype for adaptive, spatially augmented learning environments.

Prefer:
- reliable, minimal, reversible changes
- existing interfaces and dependencies
- explicit assumptions over invented requirements
- focused tests over broad refactoring

The user's current prompt overrides this file. More specific `AGENTS.md` files may add local rules.

## Working Method

- Inspect the relevant implementation and data flow before editing.
- Make the smallest coherent change that satisfies the task.
- Preserve interfaces unless the task explicitly requires changing them.
- Ask only when a decision materially affects physical behavior, calibration, data contracts, or study data.
- Do not modify unrelated files, formatting, dependencies, or generated artifacts.
- Run the narrowest relevant existing tests/checks.
- Report code-level verification separately from TouchDesigner or physical-room validation.
- Inspect the final diff when Git access allows it.

## Repository

Root:
`C:\dev\Promotion_Prototypen\AISI`

Main Python areas:
- `aisi`: interpretation, layout generation, simulation, OSC
- `aisi_sensing`: sensing/replay
- `vision`: computer vision/tracking

Do not assume their dependencies, entry points, or tests are interchangeable.

Never manually edit generated artifacts such as:
- `*.egg-info`
- `__pycache__`
- compiled/cache files

Primary simulation launcher:
`scripts/run_sim_pipeline.ps1`

Important live interfaces:
- `data/aisi/scenes/simulated/live_scene.json`
- `data/aisi/state/learning_format.json`

Preserve compatibility and atomic writes when changing their producers or consumers.

## Coordinate / Geometry Rules

ROI/world space is `0–500 cm` on X and Y.

TouchDesigner conversion currently uses:
- center `(250,250) cm`
- `1 cm = 0.0052 TD units`
- X: `(world_x - 250) * 0.0052`
- Y: `-(world_y - 250) * 0.0052`

Trace the complete scene → OSC → TouchDesigner path before changing:
- axes
- units
- origins
- rotation signs/directions
- coordinate transforms

Use the repository's canonical table-geometry implementation where available. Do not introduce parallel hard-coded table dimensions or footprint logic.

Keep source and target poses associated with the same `table_id` / OSC index.

## TouchDesigner Protection

Authoritative physical TouchDesigner master:

`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.toe`

Do not modify, regenerate, overwrite, move, or rename it unless Johannes explicitly requests it.

Repository `.toe` files and builders are development snapshots/reconstruction tools, not automatically the source of truth for the active physical graph.

The following are protected unless explicitly requested:
- floor/tabletop homographies
- calibration points
- projector transforms
- local correction grids/shaders
- edge blending
- physical/world scale
- projector footprints
- floor/tabletop mask ordering

If a requested feature appears to require changes there, report this before editing.

Do not infer the active manual TouchDesigner graph solely from repository builders.

## OSC / Integration Safety

Preserve existing OSC contracts unless migration is explicitly requested.

In particular:
- keep source/target tables paired by index
- preserve compatibility aliases where they exist
- preserve numeric value types expected by TouchDesigner
- consider object-count, missing-object, stale-object, and visibility behavior

Do not claim physical projection/tracking correctness unless it was tested in the running `.toe` project or physical room.

## Dependencies

Inspect existing imports/environment before adding dependencies.

Do not broaden dependency declarations as an incidental change. Report missing declarations unless the task explicitly includes dependency maintenance.

Prefer existing standard-library or repository solutions over new dependencies when practical.

## Validation / Completion

Before declaring a task complete:

1. Run the narrowest applicable existing automated tests/checks.
2. Run a relevant synthetic/offline integration check when appropriate.
3. Inspect the diff if Git permits.
4. Report:
   - changed files
   - important assumptions
   - tests/checks performed
   - remaining risks
   - any required TouchDesigner or physical-room validation

Do not invent a repository-wide test/lint/typecheck command if none is documented.

## Git Safety

If Git reports dubious ownership:
- do not add `safe.directory`
- do not change global Git configuration
- do not bypass the protection
- continue with safe file inspection/editing where possible
- report that Git status/history/diff verification was blocked

Never discard unrelated user changes.

## Research / Physical Safety

- Do not add participant-data storage, telemetry, uploads, or logging without explicit approval.
- Avoid new network services unless requested.
- Treat coordinate, scale, and projection changes as physically consequential.
- Prefer deterministic behavior and explicit configuration for study sessions.

## Communication

Be concise and result-oriented.

For substantial tasks, report:
- what changed
- verification result
- remaining risk
- next concrete check

When referring to known TouchDesigner nodes, use `name (operator type)`.
