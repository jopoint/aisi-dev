# Person Robustness Plan (Data-First)

## Scope
- Table path is frozen for the current milestone.
- Person robustness is treated as a small data problem first, not as additional tracking tuning.

## TODO (Small Person Eval Set)
- Collect more people (different body shapes/heights).
- Collect different clothing styles and colors.
- Cover different positions inside the ROI.
- Include ROI edge and corner cases explicitly.
- Include partial occlusions between tables.
- Add short sequences for walking, standing, and bending.

## Reuse Existing Repo Tools
- `src/vision/tools/extract_video_testset.py`
- Build a compact, numbered frame set from video (`--fps`, `--start-sec`, `--end-sec`, `--crop`).
- `src/vision/tools/video_to_frames.py`
- Quick full-frame or every-N extraction for rapid sampling.
- `src/vision/tools/batch_crop_frames.py`
- Apply a consistent ROI crop to extracted frames for comparable person eval subsets.
- `src/vision/tools/capture_frame.py`
- Capture targeted edge/occlusion stills directly from live camera.

## Note
- Deferred table-side ideas (for example tape markers on table edges) remain out of scope for this phase.
