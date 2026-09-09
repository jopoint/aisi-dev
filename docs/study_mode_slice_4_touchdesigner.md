# Study Mode Slice 4 — floor-only target

The authoritative `AISI_v2.toe` is manual state and is not represented by the
repository builders. This helper deliberately does not edit that file or any
shared mask, calibration, projector, or blend operator.

## Data source

`rect_target_floor_geo` reads these existing channels from
`/project1/comp_io/null_osc_raw`:

- `table/0/target_x`
- `table/0/target_y`
- `table/0/target_rot`

They are emitted by `sim_scene_to_osc.py`; `target_rot` is already negated for
TouchDesigner. The helper applies the existing 250 cm centre and 0.0052 TD
units/cm conversion for position only. It does not create a new OSC or pose
path.

In tracking-only mode the established compatibility contract mirrors target to
source, so the dashed target intentionally coincides with the source. A
visibly distinct target requires the normal AISI target-generation sender; no
change is made here to that policy.

## Minimal manual TouchDesigner change

1. Save a user-managed backup of the active manual project.
2. Put [study_target_floor.py](../td_builders/study_target_floor.py) in a Text
   DAT (or paste/import it in the TouchDesigner Python console), then run:

   ```python
   create_study_target_floor_geo('/project1/comp_study_visualization')
   ```

   This creates only `rect_target_floor_geo` (Geometry COMP) with 12 dashed
   bars for a 160 × 80 cm Rect footprint. It refuses to overwrite an operator
   of that name. Assign the existing AISI floor-target material to its Material
   parameter if the Study component does not already provide the intended
   target styling. Alternatively pass its path as the optional
   `material_path=` argument.
3. In `render_floor` (Render TOP), preserve the existing TRACKING and AISI
   branches exactly. In the existing `STUDY` branch, replace the returned
   geometry string with this exact value:

   ```python
   '/project1/comp_study_visualization/rect_floor_outer_geo /project1/comp_study_visualization/rect_target_floor_geo'
   ```

   This is the only required Render TOP Geometry change. The branch must be
   selected only for `study_mode == 1`; do not alter the `study_mode == 0`
   TRACKING branch or the `study_mode == 2` original AISI branch.
4. Do not change `render_tabletop` or `render_table_mask`.

The exact complete `render_floor` expression cannot safely be reconstructed
from this repository because the active manual AISI geometry-list branch is
not versioned. Replacing only the Study branch above preserves it verbatim.

## Physical verification

1. TRACKING (`study_mode = 0`): existing continuous source floor and tabletop
   contours remain unchanged.
2. STUDY + FLOOR_ONLY (`study_mode = 1`, `study_condition = 0`): continuous
   source outer contour plus dashed target footprint on the floor; no Study
   tabletop source contour.
3. STUDY + DUAL_SURFACE (`study_mode = 1`, `study_condition = 1`): the same
   two floor geometries plus the existing continuous Study tabletop source.
4. AISI (`study_mode = 2`): original source/target/motion geometry list is
   unchanged.
5. Confirm the real table mask remains active and unchanged in every mode.
