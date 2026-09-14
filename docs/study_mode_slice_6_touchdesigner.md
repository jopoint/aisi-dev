# Study Mode Slice 6 — overlap-gated tabletop target

This helper adds only `rect_target_tabletop_geo (Geometry COMP)` below the
manual project's `/project1/comp_study_visualization (Base COMP)`. It does
not alter the protected `.toe`, calibration, masks, projector components, or
the Tracking/AISI renderers.

## Behaviour

`rect_target_tabletop_geo` is a dashed, unfilled `150 x 70 cm` inner Rect
target (`0.780 x 0.364` TD units). It reads the Study-controller-owned
`study/target_x`, `study/target_y`, and `study/target_rot` channels.
Its transform uses the same established axes as the Study source geometry:
`tx = (250 - x_cm) * 0.0052`, `ty = (y_cm - 250) * 0.0052`; rotation is read
unchanged from the existing target channel.
Its visibility reads `study_overlap_state (Script CHOP)`. That CHOP has a
native input chain from `study_source_pose` and `study_target_pose` (Object
CHOPs), through `study_overlap_pose_inputs (Merge CHOP)`. Each Object CHOP
uses its Geometry COMP as Target and `comp_study_visualization` as Reference,
so it cooks whenever the sibling Geo transform changes and supplies the
standard `tx`, `ty`, and `rz` channels. The overlap Script CHOP delegates the
actual SAT calculation to the existing `study_motion_math (Text DAT)`
function.

The final tabletop-target visibility is not a Geometry COMP parameter
expression. `study_target_tabletop_visibility_state (Select CHOP)` reads only
`study/mode`, `study/condition`, and `study/phase` from the OSC CHOP.
`study_target_tabletop_visibility_inputs (Merge CHOP)` combines that local
state CHOP and `study_overlap_state`; its
`study_target_tabletop_visibility (Script CHOP)` outputs the single channel
`rect_target_tabletop_geo:sx`. The following
`study_target_tabletop_visibility_export (Null CHOP)` uses automatic CHOP
export rooted at `comp_study_visualization`, so that channel directly owns
`rect_target_tabletop_geo.par.sx`.

- source and target outer Rects separated: hidden;
- source and target outer Rects overlap or touch: visible;
- arrived poses remain visible when overlapping; only the motion cues hide.

The tabletop target is additionally gated by `study_mode == 1` (STUDY) and
`study_condition == 1` (DUAL_SURFACE). It is hidden in TRACKING, AISI, and
Study/FLOOR_ONLY even if the footprints overlap.

No second collision implementation or OSC data path is introduced. The
explicit CHOP dependency prevents the old, opaque Geometry-parameter
expression from remaining stale until a forced cook.

During startup, a missing pose channel/sample yields `overlap = 0.0`; the
callback does not throw until both pose CHOPs are fully available.

## Manual TouchDesigner update

1. Back up the active project. Do not replace `comp_tracking_only` or shared
   mask/projector operators.
2. Rebuild the existing Slice-5 helper operators so `study_motion_math` also
   reports overlap for arrived poses. Inside
   `comp_study_visualization (Base COMP)`, delete only these generated
   operators: `study_motion_math (Text DAT)`,
   `rect_motion_line_floor_geo (Geometry COMP)`, and
   `rect_motion_line_tabletop_geo (Geometry COMP)`. Re-run the current
   `create_study_motion_line_geos()` helper.
3. To switch to the fixed Study target, delete only its generated operators:
   `rect_target_floor_geo (Geometry COMP)`,
   `rect_target_tabletop_geo (Geometry COMP)`,
   `study_source_pose (Object CHOP)`, `study_target_pose (Object CHOP)`,
   `study_overlap_pose_inputs (Merge CHOP)`,
   `study_overlap_callbacks (Text DAT)`, and
   `study_overlap_state (Script CHOP)`,
   `study_target_tabletop_visibility_state (Select CHOP)`,
   `study_target_tabletop_visibility_inputs (Merge CHOP)`,
   `study_target_tabletop_visibility_callbacks (Text DAT)`,
   `study_target_tabletop_visibility (Script CHOP)`, and
   `study_target_tabletop_visibility_export (Null CHOP)`. Then import/paste the current
   `td_builders/study_target_floor.py` into a Text
   DAT or the TD Python console, then run:

   ```python
   create_study_target_floor_geo('/project1/comp_study_visualization')
   create_study_target_tabletop_geo('/project1/comp_study_visualization')
   ```

   This refuses to overwrite generated operators. It expects the existing
   `rect_floor_outer_geo`, the freshly recreated `rect_target_floor_geo`, and freshly rebuilt
   `study_motion_math` operators. It additionally creates
   `study_source_pose (Object CHOP)`, `study_target_pose (Object CHOP)`,
   `study_overlap_pose_inputs (Merge CHOP)`,
   `study_overlap_callbacks (Text DAT)`, and
   `study_overlap_state (Script CHOP)`,
   `study_target_tabletop_visibility_state (Select CHOP)`,
   `study_target_tabletop_visibility_inputs (Merge CHOP)`,
   `study_target_tabletop_visibility_callbacks (Text DAT)`,
   `study_target_tabletop_visibility (Script CHOP)`, and
   `study_target_tabletop_visibility_export (Null CHOP)`. Assign the same restrained
   target/motion material as the floor target if the parent does not supply
   one.
   `study_motion_math` and the two motion Geometry COMPs need no rebuild for
   the fixed Study target: they already read the source and target Geometry
   transforms, not target OSC channels directly.

### Restart-safe overlap and visibility update

To update only the stale source-pose dependency in an existing project, leave
both target Geometry COMPs and all motion Geometry COMPs in place. Inside
`comp_study_visualization (Base COMP)`, delete only:

`study_source_pose`, `study_target_pose`, `study_overlap_pose_inputs`, the
legacy `study_pose_callbacks` DAT if present, `study_overlap_callbacks`,
`study_overlap_state`, `study_target_tabletop_visibility_inputs`,
`study_target_tabletop_visibility_state`,
`study_target_tabletop_visibility_callbacks`,
`study_target_tabletop_visibility`, and
`study_target_tabletop_visibility_export`.

Reload the current `study_target_floor.py` helper in TD and run:

```python
create_study_overlap_state('/project1/comp_study_visualization')
create_study_target_tabletop_visibility_state('/project1/comp_study_visualization')
```

This recreates `study_source_pose` and `study_target_pose` as Object CHOPs,
not Script CHOPs, and recreates the direct CHOP export to the already-existing
`rect_target_tabletop_geo`. No Render TOP geometry-list update is required.
Confirm that the Object CHOPs contain `tx`, `ty`, and `rz`; then move the live
source and verify both `study_overlap_state['overlap']` and
`rect_target_tabletop_geo.par.sx` change without any `cook()` call.
4. Leave `render_floor (Render TOP)` and `render_table_mask (Render TOP)`
   unchanged. In `render_tabletop (Render TOP)`, preserve the existing
   TRACKING and AISI branches and replace only the STUDY result with:

   ```python
   '/project1/comp_study_visualization/rect_tabletop_inner_geo /project1/comp_study_visualization/rect_motion_line_tabletop_geo /project1/comp_study_visualization/rect_target_tabletop_geo' if op('/project1/comp_io/null_osc_raw')['study_condition'].eval() == 1 else ''
   ```

The expression means `FLOOR_ONLY` selects no Study tabletop geometry, while
`DUAL_SURFACE` selects source, motion, and the overlap-gated inner target.

## Physical verification

- TRACKING: unchanged floor and tabletop source contours.
- AISI: unchanged original source/target/motion output.
- STUDY / FLOOR_ONLY: floor source, floor dashed target, and floor motion as
  applicable; no tabletop source, motion, or target.
- STUDY / DUAL_SURFACE, separated footprints: tabletop source/motion only;
  no tabletop target.
- STUDY / DUAL_SURFACE, overlapping or touching footprints: dashed `150 x
  70 cm` tabletop target appears at the target pose. It remains visible when
  the table is within the arrival tolerance, while motion cues disappear.
