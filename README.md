# AISI

AISI is a research prototype for adaptive, spatially augmented learning environments. It combines room sensing, table tracking, spatial interpretation, layout generation, study control, and projected guidance on floors and tabletops.

The prototype uses a shared `500 × 500 cm` world coordinate system and supports two related workflows:

- a controlled Floor-only versus Dual-surface Study using live Rect-table tracking;
- general AISI layout generation for `input`, `groupwork`, and `discussion` configurations.

## Current status

The current committed baseline includes:

- live Rect-table OBB detection and world-coordinate tracking;
- multi-table association, occlusion handling, and reacquisition;
- tracking-only OSC output and projected table outlines;
- Study control with T1–T4 × A/B trials;
- Floor-only and Dual-surface conditions;
- HOME, READY, ACTIVE, and COMPLETE phases;
- active-table binding and multi-table Study setup binding;
- append-only session/event logging and offline metric extraction;
- polygon-aware table geometry and layout constraints;
- TouchDesigner builders and tests for Study visuals.

The active Study definition is `pilot_v6` and is frozen in:

```text
data/aisi/study/trials.json
data/aisi/study/trials_pilot_v6.json
```

The current working tree may also contain newer, uncommitted Rect layout work. Read [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), [`TODO.md`](TODO.md), and [`AGENTS.md`](AGENTS.md) before making substantial changes.

## Repository structure

- `src/aisi/` — scene models, table geometry, layout generation, simulation, Study control, OSC, logging, and analysis.
- `src/aisi_sensing/` — earlier sensing, record/replay, inference, and debugging infrastructure.
- `src/vision/` — current computer vision and tracking pipeline.
- `scripts/` — launchers and diagnostic/artifact generators.
- `td_builders/` — partial TouchDesigner graph builders and reconstruction helpers.
- `touchdesigner/` — checked-in development snapshots; not the authoritative physical project.
- `data/aisi/study/` — active and frozen Study trial definitions.
- `tests/` — focused regression tests.
- `docs/` — calibration, Study, workflow, and project-state documentation.

## Source of truth and safety

The authoritative physical TouchDesigner project is maintained outside the repository:

```text
C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.toe
```

Repository `.toe` files and builders are references and reconstruction tools. Do not overwrite or regenerate the physical master unless explicitly requested.

The following are protected unless a task is explicitly about calibration:

- floor and tabletop homographies;
- calibration points and local correction shaders;
- projector transforms and footprints;
- edge blending;
- mask routing/order;
- world scale.

Physical projection and tracking quality must be validated in the running TouchDesigner project and room. Repository tests alone cannot establish physical correctness.

## Coordinate system

- World/ROI: `0–500 cm` on X and Y.
- Center: `(250, 250) cm`.
- TouchDesigner scale: `1 cm = 0.0052 TD units`.

World-to-TouchDesigner position conversion:

```text
tx = (x_cm - 250) * 0.0052
ty = -(y_cm - 250) * 0.0052
```

The simulation-to-OSC sender negates source and target rotations before transmission. Do not apply the same conversion twice in TouchDesigner.

## Table types and geometry

| Type | Physical reference | Geometry |
| --- | --- | --- |
| `summit` | Vitra Scout Summit, approximately `157 × 70 × 74 cm` | trapezoidal |
| `sprint` | Vitra Scout Sprint, approximately `82 × 60 × 74 cm` | trapezoidal |
| `rect` | `160 × 80 × 74 cm` | rectangular |

The domain/layout pipeline uses canonical polygon footprints for collision, ROI, separation, clearance, repair, and debug rendering. Do not introduce a second hard-coded geometry implementation.

Scout-specific seating and Groupwork semantics are not yet finalized.

## Setup

Python `3.10+` is required. The base package can be installed in an editable virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pip install python-osc
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pip install python-osc
```

The current-room YOLO/OBB workflow uses a separate `.venv_yolo` environment and additional model/runtime dependencies. Do not install those dependencies merely to run the base simulation or layout tests.

## Workflow 1: simulation and general layout generation

The simulation path is:

```text
Room Editor
→ live_scene.json
→ layout generation
→ OSC
→ TouchDesigner
```

Windows launcher:

```powershell
.\scripts\run_sim_pipeline.ps1
```

Individual modules:

```bash
python -m aisi.app.sim_room_editor
python -m aisi.app.learning_format_server
python -m aisi.app.sim_scene_to_osc
```

The Room Editor writes atomically to:

```text
data/aisi/scenes/simulated/live_scene.json
```

The learning-format server writes:

```text
data/aisi/state/learning_format.json
```

Do not run two OSC senders against port `9000` at the same time.

## Workflow 2: current-room tracking-only mode

The Windows tracking-only launcher starts:

1. the current-room Rect OBB vision pipeline;
2. the Vision-to-AISI scene adapter;
3. the tracking-only OSC sender.

```powershell
.\scripts\run_current_room_tracking_only.ps1
```

This path writes live vision output to dedicated files and does not overwrite the Room Editor scene:

```text
data/vision/live/current_room_rect.jsonl
data/aisi/scenes/live/vision_live_scene.json
```

Tracking-only mode performs no layout synthesis. Target compatibility values equal the current source pose so motion vectors remain zero.

Do not start `run_sim_pipeline.ps1` in parallel; it would start another OSC sender on the same port.

## Workflow 3: Study control

The Study controller publishes the complete Study state over OSC, binds live table tracks, records trials, and optionally opens its Tk interface:

```bash
python -m aisi.app.study_control --participant-id P001
```

Defaults:

- trials: `data/aisi/study/trials.json`;
- logs: `data/aisi/study/runs/`;
- live source scene: `data/aisi/scenes/live/vision_live_scene.json`;
- OSC destination: `127.0.0.1:9000`.

Study mappings:

| State | Values |
| --- | --- |
| Mode | Tracking `0`, Study `1`, AISI `2` |
| Condition | Floor-only `0`, Dual-surface `1` |
| Phase | Home `0`, Ready `1`, Active `2`, Complete `3` |

Objective arrival currently requires:

- translation error `≤ 8 cm`;
- rotation error `≤ 5°`;
- `0.5 s` continuously inside both tolerances.

Participant-declared completion is recorded independently.

Analyze one session directory or one or more JSONL files with:

```bash
python -m aisi.analysis.study_metrics data/aisi/study/runs/<session>
```

This produces `metrics.csv` and `metrics.json` unless another output directory is specified.

## Study trial geometry

`data/aisi/study/trials.json` is active. Frozen snapshots preserve earlier versions. Any geometry change must create a new named snapshot before replacing the active definition.

Current task design intent:

| | low/limited occlusion | increased occlusion |
| --- | --- | --- |
| simpler layout | T1 | T2 |
| denser layout | T3 | T4 |

This is a deliberate 2×2 design structure, but it is not automatically evidence that density and occlusion are perfectly orthogonal experimental factors.

## General layout generation

The layout pipeline supports:

- `input`;
- `groupwork`;
- `discussion`.

Important invariants:

- maximum current capacity: five tables;
- `transformation_strength = 0` returns exact source poses without repair;
- `strength > 0` blends before final hard-constraint repair;
- format roles remain bound to their `table_id`;
- output returns in original scene order for OSC;
- collision and ROI violations must not be silently emitted as valid layouts.

Rect Input counts 1–5 may have newer uncommitted templates in the current working tree. Rect Groupwork was recently audited and still requires final geometry decisions. Consult the handoff documents before continuing.

## OSC contracts

Default destination: `127.0.0.1:9000`.

General object lifecycle channels:

```text
/table/count
/person/count
/chair/count
```

General table channels include:

```text
/table/{i}/source_x
/table/{i}/source_y
/table/{i}/source_rot
/table/{i}/target_x
/table/{i}/target_y
/table/{i}/target_rot
/table/{i}/width
/table/{i}/height
/table/{i}/type_id
```

Source and target tables remain paired by index. Numeric `type_id` values are:

| `type_id` | Type |
| ---: | --- |
| 0 | `summit` |
| 1 | `sprint` |
| 2 | `rect` |

Study state uses `/study/...` addresses. Preserve established address names and integer mappings unless an explicit migration is requested.

## Plotting on macOS

- The interactive Room Editor uses `TkAgg`.
- Headless PNG generation must select `Agg` before importing `matplotlib.pyplot`.
- Shared plotting modules should stay backend-neutral.

## Tests and verification

There is no single canonical repository-wide test, lint, format, or type-check command. Run the narrowest relevant test modules for the changed area.

Examples:

```bash
python -m unittest tests.test_rect_template_layouts
python -m unittest tests.test_study_trials
python -m unittest tests.test_study_control
python -m unittest tests.test_study_tracking
python -m unittest tests.test_study_logging tests.test_study_metrics
python -m unittest tests.test_vision_table_association tests.test_tracking_only_osc
```

Also run `git diff --check` and inspect the final diff. Report software checks separately from TouchDesigner and physical-room validation.

## Data and Git hygiene

Do not stage runtime or generated artifacts by default, including:

- live scenes and state files;
- Study run logs and analysis output;
- calibration captures;
- vision debug JSONL and performance logs;
- training data/model outputs;
- generated layout/debug plots.

Never discard unrelated user changes. Do not create commits unless explicitly requested.

## Further documentation

- [`AGENTS.md`](AGENTS.md) — repository rules and protected interfaces.
- [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) — current architecture and evidence-backed status.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — accepted, frozen, provisional, and open decisions.
- [`TODO.md`](TODO.md) — prioritized work and open questions.
- [`data/aisi/study/README.md`](data/aisi/study/README.md) — trial-version and A/B transformation rules.
- [`docs/rect_tabletop_camera_calibration.md`](docs/rect_tabletop_camera_calibration.md) — current-room calibration/tracking workflow.

Before modifying the project, read `AGENTS.md` and inspect the current working tree.
