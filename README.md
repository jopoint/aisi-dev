# AISI

AISI is a research prototype for adaptive, spatially augmented learning environments. It perceives tables, chairs, and people in an approximately 5 × 5 m room, interprets spatial configurations, generates alternative layouts, and provides projected guidance on floors and tabletops.

## Current prototype status

The primary development workflow is currently simulation-based:

```text
Room Editor → live_scene.json → layout generation → OSC → TouchDesigner
```

Repository-verified functionality includes simulated tables, people, and chairs; numeric object counts; source and target table poses; table type information; generated target layouts; and OSC transmission to TouchDesigner. The manually maintained TouchDesigner project uses Replicators for dynamic tables, people, and chairs.

Computer vision exists as a separate, active development area, but it is not currently the primary source feeding the active prototype.

## Repository structure

- `src/aisi/`: scene loading and interpretation, target structures, layout synthesis and constraints, simulation applications, and OSC integration.
- `src/aisi_sensing/`: the earlier sensing-oriented pipeline, including FrameEvent contracts, record/replay, tracking, inference, and debug rendering.
- `src/vision/`: current computer-vision and tracking utilities, including OpenCV, ArUco, and optional YOLO/SAM-related paths.
- `scripts/`: workflow launchers, currently including the preferred simulation launcher.
- `td_builders/`: partial TouchDesigner graph builders and development snapshots. They do not define the authoritative physical project.
- `touchdesigner/`: checked-in `.toe` development snapshots, not the active master project.
- `configs/`: example camera, lab, and classification configuration.
- `data/`: live simulation state, scenes, recordings, and development outputs.

## Setup

The current workflow is Windows/PowerShell-oriented. Example installation:

```powershell
git clone https://github.com/jopoint/aisi-dev AISI
cd AISI

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pip install python-osc
pip install opencv-contrib-python
```

`python-osc` is required by the simulation-to-OSC sender but is not currently declared in the base `pyproject.toml`. OpenCV with ArUco support is needed for sensing and calibration utilities. The YOLO/vision workflow uses additional dependencies and may use the separate `.venv_yolo` environment; those dependencies are not required for the base simulation workflow.

The established local repository path is:

```text
C:\dev\Promotion_Prototypen\AISI
```

## Running the current simulation pipeline

The repository-verified preferred launcher is:

```powershell
cd C:\dev\Promotion_Prototypen\AISI
.\scripts\run_sim_pipeline.ps1
```

The launcher sets `PYTHONPATH=src`, activates `.venv` when available, and opens three PowerShell processes:

- `aisi.app.sim_room_editor`: interactive top-down room editor.
- `aisi.app.learning_format_server`: browser UI at `http://127.0.0.1:8080` for learning format, visibility settings, and transformation strength.
- `aisi.app.sim_scene_to_osc`: layout generation and OSC transmission to `127.0.0.1:9000`.

The launcher currently contains the established absolute repository path shown above. Update the launcher deliberately if the checkout lives elsewhere.

For focused debugging after completing the editable installation, use two terminals:

Terminal 1:

```powershell
python .\src\aisi\app\sim_room_editor.py
```

Terminal 2:

```powershell
python .\src\aisi\app\sim_scene_to_osc.py
```

The editor writes the current scene atomically to:

```text
data/aisi/scenes/simulated/live_scene.json
```

The OSC sender reads that file, generates target poses, and sends the current scene to TouchDesigner. The learning-format server writes its state to `data/aisi/state/learning_format.json`.

## OSC contract

The default OSC destination is `127.0.0.1:9000`. Numeric lifecycle channels are sent on every normal update:

```text
/table/count
/person/count
/chair/count
```

Table channels:

```text
/table/{i}/source_x
/table/{i}/source_y
/table/{i}/source_rot
/table/{i}/target_x
/table/{i}/target_y
/table/{i}/target_rot
/table/{i}/x
/table/{i}/y
/table/{i}/rot
/table/{i}/width
/table/{i}/height
/table/{i}/type
/table/{i}/type_id
```

Person channels:

```text
/person/{i}/x
/person/{i}/y
/person/{i}/radius
```

Chair channels:

```text
/chair/{i}/x
/chair/{i}/y
/chair/{i}/radius
```

Source and target tables remain paired by index. `/x`, `/y`, and `/rot` are compatibility aliases for the source pose. A zero radius currently hides a person or chair.

The string `/type` channel is emitted for general OSC consumers. `/type_id` is its numeric form for TouchDesigner OSC In CHOP compatibility:

| `type_id` | Type |
| ---: | --- |
| 0 | `summit` |
| 1 | `sprint` |
| 2 | `rect` |

## Coordinate system

- Scene/ROI extent: `500 × 500 cm`, spanning `0–500 cm` on each axis.
- ROI center: `(250, 250) cm`.
- TouchDesigner scale: `1 cm = 0.0052 TD units`.

Conversion into TouchDesigner coordinates:

```text
tx = (x_cm - 250) * 0.0052
ty = -(y_cm - 250) * 0.0052
```

The simulation-to-OSC sender negates both source and target rotations before transmission. Do not apply the position conversion or rotation negation twice in TouchDesigner.

## Table types and geometry

The current physical/manual geometry is:

| Type | Physical table | Manually maintained TD contour | Shape |
| --- | --- | --- | --- |
| `summit` | Scout Summit, approximately `157 × 70 × 74 cm` | approximately `160 cm` top, `102 cm` bottom, `70 cm` depth | trapezoidal |
| `sprint` | Scout Sprint, approximately `82 × 60 × 74 cm` | approximately `88 cm` top, `38 cm` bottom, `60 cm` depth | trapezoidal |
| `rect` | `160 × 80 × 74 cm` | rectangular | rectangular |

Current limitation: the simulator emits the `summit`, `sprint`, and `rect` type names, but currently serializes every simulated table with the same `133 × 67 cm` rectangular footprint. The layout and constraint pipeline consumes this serialized width and height and does **not** yet model the real trapezoidal footprints. Updating the domain geometry and layout constraints is an important current development task.

## Layout generation

The repository-verified pipeline is:

```text
scene loading
→ scene interpretation
→ target profile and target structure
→ layout synthesis
→ hard-constraint repair
→ optional source/target blending
→ static fallback when generation fails
```

The selected learning format is `input`, `groupwork`, or `discussion`. `transformation_strength`, stored in `learning_format.json`, influences generation and then blends generated targets with the source scene on a `0.0–1.0` scale.

Key integration code lives in `src/aisi/app/sim_layout_rules.py`; the underlying generators and constraints live in `src/aisi/generation/`.

## TouchDesigner

The repository contains partial builders under `td_builders/` and `.toe` development snapshots under `touchdesigner/`. These are useful references and reconstruction tools, but they are not authoritative for the active physical graph.

The authoritative manually maintained project is external to the repository:

```text
C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.toe
```

The following state is manually confirmed rather than constructed by the repository builders: dynamic table/person/chair replication, OSC input through `comp_io` / `null_osc_raw`, floor and tabletop rendering, and the dual-projector calibration pipeline.

> **Warning:** Do not overwrite, regenerate, move, or rename `AISI_v2.toe` using the repository builders. Work on a dated copy only when changes to the master are explicitly requested.

## Calibration

Physical floor/tabletop calibration is considered complete and protected. Do not change homographies, local corrections, projector rotation, edge blending, masks or mask ordering, physical scale, or projector footprints unless calibration work is explicitly requested.

Projection alignment and physical output quality must be validated in the running manual TouchDesigner project and room; repository checks cannot establish them.

## Computer vision

Computer vision remains a separate development area rather than the active prototype's primary input. `src/vision/` contains the current vision/tracking utilities, while `src/aisi_sensing/` contains the earlier sensing, ArUco, record/replay, and inference architecture. OpenCV/ArUco support is available, and an optional YOLO pipeline uses additional dependencies and setup.

Do not assume that live vision currently drives `AISI_v2.toe`. Reconnecting and updating vision for the changed room and physical furniture is planned after the table/domain geometry and layout constraints are updated.

## Current development priorities

1. Update the Python/domain representation of Summit, Sprint, and Rect table geometry.
2. Update layout generation and constraints to use the new table geometry consistently.
3. Validate generated layouts with mixed table types.
4. Reconnect and update live computer vision for the changed room and furniture.
5. Continue study-oriented visual and interface refinement.

## Testing and status

There is no single canonical repository-wide test, lint, format, or type-check command. Use the narrowest relevant `pytest` target or executable check for the area being changed.

Existing tests primarily cover `aisi_sensing` and a vision tracking utility. They do not imply broad automated coverage of layout generation or the OSC contract. Physical projection, visual quality, tracking, and calibration require manual validation in TouchDesigner and the room.

## Development rules

Contributors and Codex must read [`AGENTS.md`](AGENTS.md) before modifying the project.
