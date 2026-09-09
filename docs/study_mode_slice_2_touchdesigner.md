# Study Mode Slice 2 — TouchDesigner integration

The authoritative physical TouchDesigner project is manual state and is not
represented by the repository builders. This slice therefore does not edit a
`.toe` file, calibration, masks, or the projector pipeline.

## Preconditions

- `study_control` is running and has published a Study State at least once.
- `comp_io/null_osc_raw` (Null CHOP) exposes `study_mode` (and the other
  `study_*` channels).
- `toggle_content_mode` already receives/exports `study_mode`, with value `0`
  selecting the existing `comp_tracking_only` route.

## Minimal manual graph edit

Perform these edits in the active manual project, saving a user-managed backup
first. Do not replace the existing `comp_tracking_only` component.

1. At the same parent level as `comp_tracking_only`, duplicate that component
   in the TouchDesigner UI and name the copy `comp_study_visualization`.
   The copy is intentionally source-only at this point: retain its existing
   source inner/tabletop contour and outer/floor contour exactly as inherited.
   Do not add target, motion, or overlap operators.
2. Preserve `comp_tracking_only` and its current connection as content input
   `0` (TRACKING) of the existing `toggle_content_mode` switch.
3. Connect the matching output(s) of `comp_study_visualization` as content
   input `1` (STUDY) of that same switch. The output ordering must match the
   existing tracking component's floor/tabletop/mask interface exactly.
4. Leave the output of `toggle_content_mode` connected to the existing shared
   downstream floor, tabletop, table-mask, projector, and blend pipeline.
   Do not duplicate or edit those downstream components.
5. Keep the `study_mode` export on `toggle_content_mode`'s existing manually
   controlled selection/value parameter. Verify `0` selects input `0` and `1`
   selects input `1`.

No `study_condition` behavior is connected in this slice. It remains available
in `null_osc_raw` for later work; both FLOOR_ONLY and DUAL_SURFACE initially
show the duplicated source-only renderer.

## Required source data

The duplicated component must retain the same expressions/data path as
`comp_tracking_only`: source pose only from `null_osc_raw` (Null CHOP), using
`table/0/source_x`, `table/0/source_y`, and `table/0/source_rot`. It must not
introduce a second tracking client, use target channels, or apply a new
coordinate conversion.

## Physical verification

1. Start the known working tracking-only path.
2. In Study Control, select TRACKING (`/study/mode = 0`): the output must be
   unchanged from the pre-Slice-2 tracking renderer.
3. Select STUDY (`/study/mode = 1`): the floor shows the continuous outer
   source contour and the tabletop shows the continuous inner source contour.
4. Move and rotate the physical Rect table. Both contours must follow the same
   live source pose synchronously, and tabletop masking must still prevent the
   floor layer from projecting on the tabletop.
5. Toggle back to TRACKING and confirm no visible behavior change.

If any output interface differs between the duplicated component and the
tracking component, stop before reconnecting downstream components; that
interface is manual graph state not represented in this repository.
