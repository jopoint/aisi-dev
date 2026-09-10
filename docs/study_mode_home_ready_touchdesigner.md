# Study Mode: neutral HOME/READY setup guides

`td_builders/study_start_pose.py` creates only Study-owned HOME/READY setup
Geometry COMPs below `/project1/comp_study_visualization`. It does not edit the
protected `.toe`, tracking, calibration, masks, clipping, projector components,
or the original AISI renderer.

## Neutral visual contract

Every table in the trial setup uses exactly the same solid 160 x 80 cm outer
Rect geometry, material argument, line thickness, and visibility rule. The
historic name `rect_start_floor_geo` is only setup-list index zero; it has no
different geometry, material, label, colour, or line style from
`rect_setup_floor_geo_01` through `rect_setup_floor_geo_05`. Consequently the
HOME display does not reveal which physical table becomes the live Study source
during ACTIVE.

The optional participant markers are unlabeled neutral dashed circles. No
participant positions are supplied by the current `trials.json`; the optional
schema is ready for them when an experimenter defines the physical positions.

The Study controller publishes the variable setup state on every full-state
publish:

```text
/study/setup_table_count
/study/setup_table/<index>/x
/study/setup_table/<index>/y
/study/setup_table/<index>/rot
/study/participant_start_count
/study/participant_start/<index>/x
/study/participant_start/<index>/y
/study/participant_start/<index>/radius
```

The table and marker Geometry COMPs are individually count-gated, so unused
capacity stays hidden.

| Phase | Setup tables and participant markers | Existing live Study source/target/motion |
|---|---|---|
| HOME (0) | visible | hidden |
| READY (1) | visible | hidden |
| ACTIVE (2) | hidden | unchanged ACTIVE behaviour |
| COMPLETE (3) | hidden | hidden |

## Trial JSON optional field

Each trial may define zero or more participant setup markers:

```json
"participant_start_positions": [
  {"id": "P1", "x_cm": 190, "y_cm": 395, "radius_cm": 40},
  {"id": "P2", "x_cm": 310, "y_cm": 395, "radius_cm": 40}
]
```

`id` is validated as a unique non-empty string; `x_cm`, `y_cm`, and positive
`radius_cm` are required per marker (`radius_cm` defaults to 40 when omitted).
Omitting the field produces no marker and does not invent participant
coordinates.

## Manual TouchDesigner rebuild

1. Save a backup of the manual `.toe`.
2. In `/project1/comp_study_visualization`, delete **only** older generated
   HOME setup guides if they exist:

   - `rect_start_floor_geo`
   - `rect_setup_floor_geo_01` through `rect_setup_floor_geo_05`
   - `study_participant_start_marker_geo_00` through
     `study_participant_start_marker_geo_03`

   Do not delete the existing target, motion, overlap, source, rendering,
   calibration, or mask operators for this update.

3. Paste/import the current `study_start_pose.py` into a Text DAT or TD's
   Python editor, then run:

   ```python
   create_study_home_setup_geos(
       '/project1/comp_study_visualization',
       max_table_count=6,
       max_participant_count=4,
   )
   ```

   It creates these Geometry COMPs:

   ```text
   rect_start_floor_geo
   rect_setup_floor_geo_01 ... rect_setup_floor_geo_05
   study_participant_start_marker_geo_00 ... _03
   ```

   Give every setup-table COMP the same existing neutral floor material. The
   participant markers may use a neutral floor-marker material; they carry no
   label. The default capacity supports source plus five distractors and four
   participant markers; increase the arguments only if a future trial needs
   more.

4. Preserve the TRACKING and AISI portions of each Render TOP Geometry
   expression. In the `study/mode == 1` floor-result branch, use:

   ```python
   ('/project1/comp_study_visualization/rect_start_floor_geo '
    '/project1/comp_study_visualization/rect_setup_floor_geo_01 '
    '/project1/comp_study_visualization/rect_setup_floor_geo_02 '
    '/project1/comp_study_visualization/rect_setup_floor_geo_03 '
    '/project1/comp_study_visualization/rect_setup_floor_geo_04 '
    '/project1/comp_study_visualization/rect_setup_floor_geo_05 '
    '/project1/comp_study_visualization/study_participant_start_marker_geo_00 '
    '/project1/comp_study_visualization/study_participant_start_marker_geo_01 '
    '/project1/comp_study_visualization/study_participant_start_marker_geo_02 '
    '/project1/comp_study_visualization/study_participant_start_marker_geo_03'
    if op('/project1/comp_io/null_osc_raw')['study/phase'].eval() in (0, 1)
    else '/project1/comp_study_visualization/rect_floor_outer_geo '
         '/project1/comp_study_visualization/rect_target_floor_geo '
         '/project1/comp_study_visualization/rect_motion_line_floor_geo'
    if op('/project1/comp_io/null_osc_raw')['study/phase'].eval() == 2
    else '')
   ```

5. Keep the existing Study tabletop branch exactly as it is: only the active
   source/tabletop target/motion list belongs there during phase `2` and
   `study_condition == 1`. Do not add setup guides to that list.

6. Leave `render_table_mask`, calibration, clipping, and all original AISI
   geometry lists unchanged.
