# Study Mode Slice 5 — Source-to-Target motion

The active `AISI_v2.toe` remains protected manual state. This repository
helper only prepares isolated operators under `comp_study_visualization`; it
does not alter the tracking component, original AISI geometry, masks,
calibration, projector pipeline, or blend.

## Motion geometry

The helper uses the transform parameters of the existing Study Geometry COMPs:

- source: `rect_floor_outer_geo` — the established live tracking pose;
- target: `rect_target_floor_geo` — the existing target OSC pose.

For the centre-to-centre direction, it transforms that direction into each
rotated 160 × 80 cm Rect's local coordinates. The nearest rectangle boundary
is the minimum positive local-X/local-Y ray intersection. Thus the floor line
starts at the source boundary and ends at the target boundary, not at either
centre. The floor line uses those outer boundaries. The tabletop line instead
uses the existing inner contour's 150 x 70 cm support (0.780 x 0.364 TD). Its
length is the smaller of the target-centre distance and the inner-contour
support distance: it ends at the target centre when that centre is already
inside the inner contour, otherwise at the inner contour. In DUAL_SURFACE, two
restrained arrowheads are shown for a normal move: one at that tabletop end and
one at the floor segment's target-boundary end. Both point Source-to-Target.
If the floor segment is hidden by contact/overlap, the tabletop line uses the
same clamped endpoint along the Target-centre direction. Neither is a rotation
arrow.

The Tabletop Geometry COMP is attached to the source centre and source
rotation. The nested `source_local_direction` (Transform SOP) consumes
`tabletop_local_angle_deg`, calculated by rotating the normalized
`target_center - source_center` direction by `-source_rotation`. It rotates
the shaft and both arrowhead bars in source-local space; the Geometry COMP then
applies source rotation exactly once. The floor Geometry COMP remains a
world-oriented cue.

When the footprints meet or overlap, the floor segment is hidden. For a short
but nonzero translation, the tabletop segment remains visible in DUAL_SURFACE.
At zero translation both are hidden.

## Arrival tolerance

Motion is hidden when both of these conservative live-tracking tolerances are
met:

- translation: 8 cm;
- Rect orientation: 5 degrees, measured modulo 180 degrees.

The values are explicit in `study_motion_lines.py` as
`ARRIVAL_TRANSLATION_TOLERANCE_CM` and `ARRIVAL_ROTATION_TOLERANCE_DEG`. A
translation or rotation outside either tolerance keeps the translation cue
visible when the two centres have a usable direction. No rotation-only arrow
is introduced.

## Minimal manual TouchDesigner change

1. Save a user-managed backup of the active manual project.
2. Put [study_motion_lines.py](../td_builders/study_motion_lines.py) in a Text
   DAT or import/paste it in the TouchDesigner Python console, then run:

   ```python
   create_study_motion_line_geos('/project1/comp_study_visualization')
   ```

   It creates only these operators under the Study component:

   - `study_motion_math` (Text DAT)
   - `rect_motion_line_floor_geo` (Geometry COMP)
   - `rect_motion_line_tabletop_geo` (Geometry COMP)

   The function fails rather than replacing an existing operator. To reuse the
   original AISI motion styling, set each new Geometry COMP's Material to that
   existing material, or pass its path as `material_path=`.

   For an already-created Slice-5 setup, first delete only the three helper
   operators listed above from `comp_study_visualization` (after saving the
   backup), then run the updated helper once. No Render TOP, mask, or shared
   pipeline operator needs replacement.
3. In `render_floor` (Render TOP), retain the complete existing TRACKING and
   AISI branches. Replace only its `study_mode == 1` result with this exact
   Geometry list:

   ```python
   '/project1/comp_study_visualization/rect_floor_outer_geo /project1/comp_study_visualization/rect_target_floor_geo /project1/comp_study_visualization/rect_motion_line_floor_geo'
   ```

4. In `render_tabletop` (Render TOP), retain the complete existing TRACKING
   and AISI branches. Its `study_mode == 1` result must be condition-dependent:

   ```python
   '/project1/comp_study_visualization/rect_tabletop_inner_geo /project1/comp_study_visualization/rect_motion_line_tabletop_geo' if op('/project1/comp_io/null_osc_raw')['study_condition'].eval() == 1 else ''
   ```

   This returns no Study tabletop geometry for FLOOR_ONLY and both source plus
   motion for DUAL_SURFACE. Do not add target geometry to this Render TOP.
5. Do not alter `render_table_mask`.

The complete render expressions cannot be reconstructed safely because the
manual original-AISI branches are not stored in the repository. The exact
replacement values above are intentionally limited to their STUDY branches so
the manual AISI geometry lists remain verbatim.

## Physical verification

1. TRACKING: all previous source contours remain unchanged.
2. STUDY + FLOOR_ONLY: floor has source outer contour, dashed target, and an
   edge-to-edge motion segment with its floor arrow; tabletop is blank.
3. STUDY + DUAL_SURFACE: same floor output; tabletop has source inner contour,
   a centre-to-target-or-inner-contour motion segment, and its own forward
   arrow.
4. Move the live source table and change the target. Both motion endpoints
   should update from their existing poses.
5. AISI: original source/target/motion output remains unchanged.
