# AISI — Instructions for Codex

## Purpose

AISI is a research prototype for adaptive, spatially augmented learning environments. It perceives tables, chairs, and people in an approximately 5 × 5 m room, computes alternative spatial configurations, and projects live guidance onto the floor and tabletops.

The current priority is a stable, understandable prototype for research and teaching experiments. Prefer reliable, minimal changes over speculative architecture or broad refactoring.

## Evidence Levels

Keep these sources of truth separate:

1. **Repository-verified:** behavior visible in checked-in source, builders, configuration, tests, or artifacts.
2. **Physical/manual setup:** behavior reported from the manually maintained TouchDesigner project or room setup but not fully represented by builders.
3. **Unverified/ambiguous:** information that must be checked with Johannes before it is treated as authoritative.

Do not infer the current physical TouchDesigner graph solely from a builder. Conversely, do not describe manually reported components as repository-verified.

## Working Method

- Inspect the relevant code and data flow before editing.
- Before a non-trivial change, state which files/components you expect to touch and why.
- Make the smallest coherent change that satisfies the request.
- Preserve existing interfaces unless the task explicitly requires changing them.
- Do not silently invent missing requirements. State assumptions; ask when a choice would materially affect physical behavior, calibration, data contracts, or study data.
- Run the narrowest relevant existing tests or executable checks after editing.
- Report code-level verification separately from checks that require the running `.toe` project or physical room.
- Do not modify unrelated files, formatting, dependencies, or generated artifacts.

## Repository Areas

The repository contains three parallel Python areas. Confirm their current boundaries before choosing imports, entry points, or tests:

- `aisi`: scene interpretation, target generation, layout synthesis, simulation, and OSC integration
- `aisi_sensing`: sensing/replay functionality and its own applications/tests
- `vision`: vision and tracking utilities, with dependencies that may differ from the base project

Do not assume that dependencies or tests for one area cover the others.

Generated artifacts such as `src/aisi_sensing.egg-info/` and `__pycache__/` directories must not be manually edited. Do not add or commit them. If they are tracked already, report this rather than deleting them without an explicit cleanup request.

## Primary Simulation Workflow

The repository-verified launcher is:

- `scripts/run_sim_pipeline.ps1`

It launches the room editor, learning-format server, and OSC sender with `PYTHONPATH=src`.

Relevant simulation entry points:

- `src/aisi/app/sim_room_editor.py`
- `src/aisi/app/learning_format_server.py`
- `src/aisi/app/sim_scene_to_osc.py`

Live file contracts:

- `data/aisi/scenes/simulated/live_scene.json`: current simulated scene
- `data/aisi/state/learning_format.json`: selected learning format, person/chair visibility, and `transformation_strength`

Treat these paths and their serialized fields as live interfaces. Preserve atomicity and compatibility when editing their producers or consumers.

## Other Entry Points

Sensing replay:

- `aisi_sensing.apps.run_replay`

Offline layout and conversion tools:

- `src/aisi/app/run_synthetic_test.py`
- `src/aisi/app/run_regression_suite.py`
- `src/aisi/app/convert_vision_snapshot_to_aisi.py`

If an entry point no longer exists, locate its replacement and report the discrepancy. Do not recreate it solely because it appears in this document.

## Layout-Generation Pipeline

Trace the actual implementation before changing layout behavior. The intended pipeline includes:

1. scene loading
2. scene interpretation
3. target schema/profile selection
4. `generate_target_structure`
5. `synthesize_layout`
6. hard-constraint repair
7. optional source/target blending using `transformation_strength`
8. static fallback where required

`aisi.app.sim_layout_rules.compute_target_layout` is a higher-level integration point, not the complete layout-generation architecture.

Changes to this pipeline must preserve hard constraints and clearly distinguish generated, blended, repaired, and fallback results.

## Coordinate System and Rotation

- The simulated scene/ROI spans `0–500 cm` on both axes.
- `(250, 250) cm` is the ROI center, not the scene-space origin.
- During conversion, the ROI center becomes the TouchDesigner origin.
- TouchDesigner scale: `1 cm = 0.0052 TD units`.
- Typical position conversion:
  - `tx = (world_x_cm - 250) * 0.0052`
  - `ty = -(world_y_cm - 250) * 0.0052`
- In the current simulation-to-OSC path, both source and target rotations are negated before being sent to TouchDesigner.

Always distinguish scene-space rotation, serialized/live-scene rotation, OSC rotation, and TouchDesigner rotation.

Before changing signs, origins, units, axes, rotation direction, or transforms, trace the complete path from scene/sensing through OSC to TouchDesigner.

## Table Types and Geometry

Physical/domain table dimensions:

| Type | Physical dimensions |
| --- | --- |
| `summit` / Scout Summit | 157 × 70 × 74 cm; the manually maintained TD contour may use 160 cm width and a 102 cm narrower side |
| `sprint` / Scout Sprint | 82 × 60 × 74 cm |
| `rect` / `Rect160x80` | 160 × 80 × 74 cm |

Numeric type mapping used for TouchDesigner compatibility:

- `summit = 0`
- `sprint = 1`
- `rect = 2`

Current simulator limitation: `sim_room_editor.py` assigns table types cyclically but currently gives every simulated table the same `133 × 67 cm` footprint. Layout constraints consume serialized width and height, so do not assume the type name implies the physical dimensions in simulated scenes.

Preserve both the human-readable type and numeric `type_id` where the current OSC implementation emits both. Do not rename types or normalize dimensions without checking all producers, layout consumers, and TouchDesigner consumers.

## OSC Contract

Current table channels:

- `/table/{i}/source_x`
- `/table/{i}/source_y`
- `/table/{i}/source_rot`
- `/table/{i}/target_x`
- `/table/{i}/target_y`
- `/table/{i}/target_rot`
- `/table/{i}/x`, `/table/{i}/y`, `/table/{i}/rot` — compatibility aliases
- `/table/{i}/width`
- `/table/{i}/height`
- `/table/{i}/type`
- `/table/{i}/type_id`

Current person/chair channels:

- `/person/{i}/x`
- `/person/{i}/y`
- `/person/{i}/radius`
- `/chair/{i}/x`
- `/chair/{i}/y`
- `/chair/{i}/radius`

Zero radius is currently used to hide people and chairs. Preserve this lifecycle/visibility behavior unless an explicit migration is requested.

The OSC receiver port is expected to be `9000`; confirm it in configuration before changing or documenting it elsewhere.

Rules:

- Keep source and target tables paired by index.
- Maintain compatibility aliases unless an explicit migration is requested.
- Preserve expected value types; numeric TouchDesigner CHOP channels must remain numeric.
- Check object counts, missing objects, zero-radius visibility, and stale-object behavior.
- There are currently no dedicated checked-in OSC contract tests. Add focused tests when practical, but do not pretend such coverage already exists.

## TouchDesigner: Repository-Verified Structure

The checked-in builders construct or reference the following current components:

- `comp_io`
- `comp_layout_proposal`
- `comp_calibration`
- `comp_tabletop_calibration`
- `comp_output`

The generic builder removes `comp_render` but does not recreate it.

In `td_builders/build_aisi_td.py`, the repository-verified switch inputs are:

- `0`: layout proposal
- `1`: floor calibration render
- `2`: tabletop calibration render

Do not label these inputs `FLOOR`, `TABLETOP`, and `BOTH` unless inspection of the specific active `.toe` file confirms a separate layer-mode switch.

The Python scene side supports variable-length lists in several places, but the checked-in TouchDesigner builders explicitly create four tables and, in newer variants, four people and four chairs. Treat the current TD graph as fixed-count until it is deliberately made dynamic.

## TouchDesigner: Physical/Manual Setup

The following have been reported from the manually maintained physical setup but are not fully constructed by the checked-in builders:

- two projector-specific pipelines
- floor homography per projector
- a separate layer mode for floor/tabletop/both
- post-homography masking and edge blending

Names such as `comp_projector_0`, `comp_projector_1`, and `comp_homography_floor` may exist in the manual `.toe`, but must not be treated as repository-verified without inspecting that file.

Reported rendering intent:

- tabletop: source-table interior contours and fine-positioning guidance
- floor: target-table contours, movement paths, people, and chairs
- source tables: green
- target tables: blue
- chairs: green
- people: yellow

The authoritative TouchDesigner master file is external to the repository:

- `C:\\Users\\johan\\OneDrive\\Dokumente\\AISI_DEV\\touchdesigner\\AISI_v2.toe`

Treat `AISI_v2.toe` as the source of truth for the active physical/manual TouchDesigner setup. The `.toe` files checked into the repository, including `touchdesigner/aisi_step_28_manual_person_chair_test.toe`, and the step 25, 26, 29, and generic builders are development snapshots or partial reconstruction tools; they are not authoritative for the current physical graph.

Do not modify, regenerate, overwrite, move, or rename `AISI_v2.toe` unless Johannes explicitly requests it. Before an authorized change, preserve a dated backup or work on a copy. If the file is unavailable to the current workspace, report that limitation rather than inferring its contents from repository builders.

## Calibration Is Protected

The physical dual-projector floor and tabletop calibration is currently considered complete. Do not modify the following unless Johannes explicitly requests calibration work:

- floor or tabletop homographies
- calibration point tables
- projector transforms or 180° corrections
- local correction grids/shaders
- edge-blend setup
- physical/world scale or projector footprints
- floor/tabletop mask ordering

If a requested feature appears to require calibration changes, stop and explain why before editing those areas.

## Layout and Rendering Constraints

- Keep source and target poses associated with the same table index.
- Use serialized table geometry when computing layouts, collisions, paths, or constraints; do not infer it from the type name while the simulator uses uniform dimensions.
- Report any mismatch between physical table geometry, serialized geometry, and TD-rendered geometry.
- Floor target outlines are intended to use the real table contour without arbitrary padding.
- Tabletop guidance may use an inward offset for visibility and fine positioning.
- Preserve table-mask ordering after homography in the physical/manual pipeline.
- Do not hard-code new assumptions about object count. State explicitly whether a change affects dynamic Python lists, fixed-count TD builders, or both.

## Dependencies and Generated Files

- Inspect the relevant environment and imports before installing or changing dependencies.
- `sim_scene_to_osc.py` requires `python-osc`, which is currently not represented in the base `pyproject.toml` dependencies.
- Vision tools use additional dependencies, including PyTorch, that may not be represented in the base project dependencies.
- Do not broaden dependency declarations as an incidental change. Report missing declarations and change them only when the task includes dependency maintenance.
- Never edit `*.egg-info`, `__pycache__`, compiled Python files, or other generated caches.

## Testing and Validation

There is currently no canonical repository-wide test, lint, format, type-check, tox, or pre-commit command documented. Do not invent one.

Before declaring a task complete:

1. Inspect the relevant configuration and existing tests.
2. Run the narrowest applicable existing `pytest` target or executable check.
3. For OSC changes, verify exact addresses, types, visibility semantics, object counts, and representative values; add focused coverage where practical.
4. Run an applicable offline regression or synthetic entry point for layout changes when safe.
5. Inspect the diff for accidental changes.
6. State which TouchDesigner or physical-room behaviors remain untested.
7. Summarize changed files, assumptions, verification results, and a short manual test procedure.

Existing automated tests primarily cover `aisi_sensing` and a vision tracking utility; do not imply that the `aisi` layout generator or OSC contract has broad automated coverage.

Do not claim that projection alignment, visual quality, or physical tracking works unless it was verified in the physical setup.

## Git Safety

If Git rejects the repository because of dubious ownership:

- do not change global Git configuration or add `safe.directory` without explicit approval
- do not bypass the protection
- continue with safe file inspection where possible
- report that status/history/diff verification was blocked

Never discard or overwrite unrelated user changes.

## Research and Physical-Output Safety

- Do not add storage, telemetry, uploads, or logging of participant-related data without explicit approval.
- Avoid new network services or external dependencies unless requested.
- Treat projection behavior as physically consequential: coordinate or scale errors can place content far outside the intended area.
- Prefer deterministic behavior and explicit configuration for study sessions.

## Communication Style

- Use concise, practical explanations.
- Refer to TouchDesigner nodes as `name (operator type)` when the type is known, for example `person_xform (Transform TOP)` or `table_types (Table DAT)`.
- Lead with the result and next concrete check.
- For larger tasks, separate observed state, proposed change, implementation result, and remaining physical verification.

## Task-Specific Instructions

The user's current prompt overrides this file. More specific `AGENTS.md` files in subdirectories may add local rules for their scope.
