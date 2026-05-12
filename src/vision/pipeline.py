"""
Vision pipeline for furniture detection using SAM3 segmentation.

Integrates SAM3Segmenter, geometric post-processing, homography projection,
and outputs FrameEvent in JSONL format.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import json
import os
import time

from src.vision.detection.sam3_segmenter import SAM3Segmenter
from src.vision.detection.furniture_postprocess import postprocess_furniture_masks
from src.aisi_sensing.sensing.calibration.homography import apply_homography
from src.aisi_sensing.core.types import FrameEvent, DetectedEntity, Pose2D
from src.aisi_sensing.core.timebase import now_iso


class VisionPipeline:
    """
    Vision pipeline for furniture detection and tracking.
    
    Pipeline stages:
    1. SAM3 segmentation for tables and chairs
    2. Geometric post-processing (min-area rect for tables, circle for chairs)
    3. Homography projection to floor coordinates
    4. Output as FrameEvent
    """
    
    def __init__(
        self,
        sam3_config_path: Optional[str] = None,
        sam3_checkpoint_path: Optional[str] = None,
        homography_matrix: Optional[np.ndarray] = None,
        device: str = "cuda",
        table_min_area: float = 5000.0,
        table_max_area: float = 50000.0,
        chair_min_area: float = 2000.0,
        chair_max_area: float = 20000.0,
        debug_dir: Optional[str] = None,
        proposals_mode: Optional[str] = None,
        yolo_model: str = "runs/detect/train/weights/best_fixed.pt",
        yolo_conf: float = 0.25,
        yolo_iou: float = 0.45,
        table_obb_model: Optional[str] = None,
        table_obb_conf: Optional[float] = None,
        table_obb_iou: Optional[float] = None,
        table_obb_max_det: int = 0,
        table_obb_raw_min_conf: Optional[float] = None,
        yolo_max_det: int = 80,
        track_ttl_frames: int = 15,
        conf_create: Optional[float] = None,
        conf_keep: float = 0.15,
        reacquire_max_age: Optional[int] = None,
        reacquire_max_dist: float = 150.0,
        reacquire_min_iou: float = 0.05,
        chairs_no_ghost: bool = True,
        no_ghosting: bool = False,
        overlay_style: str = "debug",
        table_dark_thresh: int = 80,
        table_min_contour_area: float = 1500.0,
        table_min_area_frac: float = 0.015,
        table_min_w_frac: float = 0.08,
        table_min_h_frac: float = 0.08,
        person_min_conf: float = 0.60,
        person_min_iou: float = 0.10,
        person_max_dist: float = 180.0,
        person_ttl: int = 60,
        person_min_area: int = 1200,
        person_max_area: int = 120000,
        person_max_ar: float = 4.0,
        person_min_height: int = 60,
        person_min_ar_wh: float = 0.18,
        person_max_ar_wh: float = 1.25,
        person_excl_right_frac: float = 0.0,
        person_excl_rb_right_frac: float = 0.0,
        person_excl_rb_bottom_frac: float = 0.0,
        person_conf_override: Optional[float] = None,
        person_static_window: int = 30,
        person_static_max_delta: float = 20.0,
        person_filter_mode: str = "geom+static",
        table_refine_every: int = 0,
        table_refine_max: int = 4,
        table_refine_margin: int = 12,
        table_motion_shift_px: float = 18.0,
        table_motion_iou_min: float = 0.78,
        table_motion_area_change: float = 0.18,
        table_stable_frames: int = 4,
        table_min_bbox_area: int = 30000,
        table_min_bbox_minside: int = 120,
        table_new_conf_create: Optional[float] = None,
        table_new_min_bbox_area: Optional[int] = None,
        table_new_min_bbox_minside: Optional[int] = None,
        table_new_confirm_frames: int = 1,
        table_new_suppress_iou: float = 0.0,
        table_new_suppress_center_dist_px: float = 0.0,
        table_protect_existing_tracks: bool = False,
        table_recover_lost_tracks: bool = False,
        table_lost_track_ttl: int = 15,
        table_birth_block_near_lost_dist: float = 0.0,
        table_birth_block_near_lost_frames: int = 0,
        table_angle_deadband_deg: float = 0.0,
        table_render_grace_frames: int = 0,
        table_static_hold_frames: int = 0,
        table_static_hold_center_px: float = 0.0,
        table_static_hold_angle_deg: float = 0.0,
        table_static_hold_area_frac: float = 0.0,
        table_obb_debug_raw_overlay: bool = False,
        table_obb_debug_jsonl: Optional[str] = None,
        crop_x: Optional[int] = None,
        crop_y: Optional[int] = None,
        crop_w: Optional[int] = None,
        crop_h: Optional[int] = None,
        camera_rotate: int = 0,
        display_rotate: int = 0,
        camera_width: Optional[int] = None,
        camera_height: Optional[int] = None,
        save_live_frame_path: Optional[str] = None,
        exit_after_saving_live_frame: bool = False,
        show_table_ids: bool = False,
    ):
        """
        Initialize vision pipeline.

        Args:
            sam3_config_path: Path to SAM2.1 model config (defaults to configs/sam2/sam2.1_hiera_l.yaml)
            sam3_checkpoint_path: Path to SAM2.1 checkpoint (defaults to checkpoints/sam2.1_hiera_large.pt)
            homography_matrix: 3x3 homography matrix (pixel -> floor coords), or None
            device: "cuda" or "cpu"
            table_min_area: Minimum table mask area in pixels
            table_max_area: Maximum table mask area in pixels
            chair_min_area: Minimum chair mask area in pixels
            chair_max_area: Maximum chair mask area in pixels
            debug_dir: Optional directory for debug overlays
            proposals_mode: Auto-proposals mode ("bgsub", "dark", "yolo", or None).
                When "yolo", SAM2 is NOT loaded and YOLODetector is used instead.
            yolo_model: Path to YOLO weights (used when proposals_mode=="yolo").
            yolo_conf: YOLO confidence threshold.
            yolo_iou: YOLO IoU threshold for NMS.
            table_obb_model: Optional OBB model path for table-only detections.
            table_obb_conf: Confidence threshold for table OBB model (defaults to yolo_conf).
            table_obb_iou: IoU threshold for table OBB model (defaults to yolo_iou).
            table_obb_max_det: Optional cap for raw table OBB detections before merge/tracking (0=off).
            table_obb_raw_min_conf: Optional min confidence for raw table OBB detections before merge/tracking.
            yolo_max_det: Max detections kept per class per frame (top-k by confidence).
            track_ttl_frames: Keep unmatched tracks alive for this many frames.
            conf_create: Minimum confidence to create NEW tracks (defaults to yolo_conf).
            conf_keep: Minimum confidence to update/reacquire EXISTING tracks.
            reacquire_max_age: Max ghost age eligible for reacquire (defaults to track_ttl_frames).
            reacquire_max_dist: Max center distance in px for active/reacquire matching.
            reacquire_min_iou: Min IoU for active/reacquire matching.
            chairs_no_ghost: Disable chair ghosting/reacquire and use conf_create-only for chairs.
            no_ghosting: Disable ghosting/reacquire globally.
            overlay_style: Overlay rendering style for saved overlays
                ("debug", "projector", or "projector_on_frame").
            table_dark_thresh: Grayscale threshold for dark-pixel extraction in table ROI.
            table_min_contour_area: Minimum contour area (in ROI px) to accept rotated table fit.
            table_min_area_frac: Minimum table bbox area fraction of full frame.
            table_min_w_frac: Minimum table bbox width fraction of frame width.
            table_min_h_frac: Minimum table bbox height fraction of frame height.
            person_min_conf: Minimum confidence for person detections before tracking.
            person_min_iou: Minimum IoU for person track-detection matching.
            person_max_dist: Maximum center distance (px) for person matching.
            person_ttl: TTL in frames for person tracks.
            person_min_area: Min person bbox area in pixels.
            person_max_area: Max person bbox area in pixels.
            person_max_ar: Max person bbox aspect ratio max(w/h, h/w).
            person_min_height: Min person bbox height in pixels.
            person_min_ar_wh: Min allowed person bbox aspect ratio w/h.
            person_max_ar_wh: Max allowed person bbox aspect ratio w/h.
            person_excl_right_frac: Right-edge exclusion strip width fraction.
            person_excl_rb_right_frac: Right-bottom exclusion zone width fraction.
            person_excl_rb_bottom_frac: Right-bottom exclusion zone height fraction.
            person_conf_override: Optional stricter confidence threshold for person only.
            person_static_window: Window length for static person suppression.
            person_static_max_delta: Max center delta over full window for static suppression.
            person_filter_mode: Person filtering mode (none, geom, geom+static).
            table_refine_every: Run SAM geometry refinement every N frames for tables (0 = disabled).
            table_refine_max: Maximum number of tables to SAM-refine per refine frame.
            table_refine_margin: Margin in pixels to expand YOLO bbox before SAM box prompt.
            table_motion_shift_px: Center shift (px) above which table is considered moving.
            table_motion_iou_min: Min IoU to previous bbox required to stay stable.
            table_motion_area_change: Max relative bbox area change allowed to stay stable.
            table_stable_frames: Consecutive non-moving frames required before table is stable.
            table_min_bbox_area: Reject table detections with bbox area below this value (pixels²).
            table_min_bbox_minside: Reject table detections with min(w,h) below this value (pixels).
            table_new_conf_create: Optional stricter min confidence for creating new table tracks.
            table_new_min_bbox_area: Optional stricter min bbox area for creating new table tracks.
            table_new_min_bbox_minside: Optional stricter min short-side for creating new table tracks.
            table_new_confirm_frames: Frames required before a new table track becomes visible (1=off).
            table_new_suppress_iou: Suppress creating new table tracks if IoU with existing table is above this value.
            table_new_suppress_center_dist_px: Suppress creating new table tracks if center too close to existing table.
            table_protect_existing_tracks: Prefer table continuity by suppressing new births while recoverable lost tracks remain.
            table_recover_lost_tracks: Enable table-specific lost-track recovery before allowing new births.
            table_lost_track_ttl: Max miss_count for table tracks to remain recoverable when recovery mode is enabled.
            table_birth_block_near_lost_dist: Suppress new table birth near recoverable lost table tracks within this center distance (px, 0=off).
            table_birth_block_near_lost_frames: Optional max miss_count age for near-lost suppression (0=all recoverable).
            table_angle_deadband_deg: Table-only angle hysteresis deadband in degrees for final rendered yaw (0=off).
            table_render_grace_frames: Keep rendering last final table geometry for this many missing frames (0=off).
            table_static_hold_frames: Consecutive static candidate frames required before hold activates (0=off).
            table_static_hold_center_px: Static hold center threshold in px (0=off).
            table_static_hold_angle_deg: Static hold angle threshold in degrees (0=off).
            table_static_hold_area_frac: Static hold relative area threshold (0=off).
            table_obb_debug_raw_overlay: Show raw OBB table detections as debug overlay items.
            table_obb_debug_jsonl: Optional JSONL path for per-frame raw OBB vs final table track debug output.
            crop_x: Optional input crop X offset in pixels.
            crop_y: Optional input crop Y offset in pixels.
            crop_w: Optional input crop width in pixels.
            crop_h: Optional input crop height in pixels.
            camera_rotate: Optional camera frame rotation in degrees (0, 90, 180, 270).
            display_rotate: Optional output/display frame rotation in degrees (0, 90, 180, 270).
            camera_width: Optional requested camera capture width in pixels.
            camera_height: Optional requested camera capture height in pixels.
            save_live_frame_path: Optional path to save first rotated live frame before crop/detection.
            exit_after_saving_live_frame: Exit camera loop after saving first frame.
            show_table_ids: Show table track IDs near final table overlays (rendering only).
        """
        self.H = homography_matrix
        self.table_min_area = table_min_area
        self.table_max_area = table_max_area
        self.chair_min_area = chair_min_area
        self.chair_max_area = chair_max_area
        self.debug_dir = debug_dir
        self._proposals_mode = proposals_mode
        self.table_obb_model = str(table_obb_model).strip() if table_obb_model else None
        self.table_obb_conf = float(yolo_conf if table_obb_conf is None else table_obb_conf)
        self.table_obb_iou = float(yolo_iou if table_obb_iou is None else table_obb_iou)
        self.table_obb_max_det = int(table_obb_max_det)
        self.table_obb_raw_min_conf = None if table_obb_raw_min_conf is None else float(table_obb_raw_min_conf)
        self._yolo_max_det = yolo_max_det
        self.track_ttl_frames = int(track_ttl_frames)
        self.conf_create = float(yolo_conf if conf_create is None else conf_create)
        self.conf_keep = float(conf_keep)
        self.reacquire_max_age = int(self.track_ttl_frames if reacquire_max_age is None else reacquire_max_age)
        self.reacquire_max_dist = float(reacquire_max_dist)
        self.reacquire_min_iou = float(reacquire_min_iou)
        self.chairs_no_ghost = bool(chairs_no_ghost)
        self.no_ghosting = bool(no_ghosting)
        self.table_dark_thresh = int(table_dark_thresh)
        self.table_min_contour_area = float(table_min_contour_area)
        self.table_min_area_frac = float(table_min_area_frac)
        self.table_min_w_frac = float(table_min_w_frac)
        self.table_min_h_frac = float(table_min_h_frac)
        self.person_min_conf = float(person_min_conf)
        self.person_min_iou = float(person_min_iou)
        self.person_max_dist = float(person_max_dist)
        self.person_ttl = int(person_ttl)
        self.person_min_area = int(person_min_area)
        self.person_max_area = int(person_max_area)
        self.person_max_ar = float(person_max_ar)
        self.person_min_height = int(person_min_height)
        self.person_min_ar_wh = float(person_min_ar_wh)
        self.person_max_ar_wh = float(person_max_ar_wh)
        self.person_excl_right_frac = float(person_excl_right_frac)
        self.person_excl_rb_right_frac = float(person_excl_rb_right_frac)
        self.person_excl_rb_bottom_frac = float(person_excl_rb_bottom_frac)
        self.person_conf_override = None if person_conf_override is None else float(person_conf_override)
        self.person_static_window = int(person_static_window)
        self.person_static_max_delta = float(person_static_max_delta)
        self.person_filter_mode = str(person_filter_mode)
        self.table_refine_every = int(table_refine_every)
        self.table_refine_max = int(table_refine_max)
        self.table_refine_margin = int(table_refine_margin)
        self.table_motion_shift_px = float(table_motion_shift_px)
        self.table_motion_iou_min = float(table_motion_iou_min)
        self.table_motion_area_change = float(table_motion_area_change)
        self.table_stable_frames = int(max(1, table_stable_frames))
        self.table_min_bbox_area = int(table_min_bbox_area)
        self.table_min_bbox_minside = int(table_min_bbox_minside)
        self.table_new_conf_create = (
            float(table_new_conf_create) if table_new_conf_create is not None else float(self.conf_create)
        )
        self.table_new_min_bbox_area = int(
            self.table_min_bbox_area if table_new_min_bbox_area is None else table_new_min_bbox_area
        )
        self.table_new_min_bbox_minside = int(
            self.table_min_bbox_minside if table_new_min_bbox_minside is None else table_new_min_bbox_minside
        )
        self.table_new_confirm_frames = int(max(1, table_new_confirm_frames))
        self.table_new_suppress_iou = float(max(0.0, table_new_suppress_iou))
        self.table_new_suppress_center_dist_px = float(max(0.0, table_new_suppress_center_dist_px))
        self.table_protect_existing_tracks = bool(table_protect_existing_tracks)
        self.table_recover_lost_tracks = bool(table_recover_lost_tracks)
        self.table_lost_track_ttl = int(max(1, table_lost_track_ttl))
        self.table_birth_block_near_lost_dist = float(max(0.0, table_birth_block_near_lost_dist))
        self.table_birth_block_near_lost_frames = int(max(0, table_birth_block_near_lost_frames))
        self.table_angle_deadband_deg = float(max(0.0, table_angle_deadband_deg))
        self.table_angle_deadband_rad = float(np.deg2rad(self.table_angle_deadband_deg))
        self.table_render_grace_frames = int(max(0, table_render_grace_frames))
        self.table_static_hold_frames = int(max(0, table_static_hold_frames))
        self.table_static_hold_center_px = float(max(0.0, table_static_hold_center_px))
        self.table_static_hold_angle_deg = float(max(0.0, table_static_hold_angle_deg))
        self.table_static_hold_area_frac = float(max(0.0, table_static_hold_area_frac))
        self.table_static_hold_angle_rad = float(np.deg2rad(self.table_static_hold_angle_deg))
        self.table_static_hold_enabled = bool(
            self.table_static_hold_frames > 0
            and self.table_static_hold_center_px > 0.0
            and self.table_static_hold_angle_deg > 0.0
            and self.table_static_hold_area_frac > 0.0
        )
        self.table_obb_debug_raw_overlay = bool(table_obb_debug_raw_overlay)
        self.table_obb_debug_jsonl = str(table_obb_debug_jsonl).strip() if table_obb_debug_jsonl else None
        if crop_x is None and crop_y is None and crop_w is None and crop_h is None:
            self._input_crop = None
        else:
            self._input_crop = (
                int(crop_x or 0),
                int(crop_y or 0),
                int(crop_w or 0),
                int(crop_h or 0),
            )
        self._input_crop_warned = False
        self.camera_rotate = int(camera_rotate) if camera_rotate in (0, 90, 180, 270) else 0
        self.display_rotate = int(display_rotate) if display_rotate in (0, 90, 180, 270) else 0
        self.camera_width = None if camera_width is None else int(camera_width)
        self.camera_height = None if camera_height is None else int(camera_height)
        self.save_live_frame_path = str(save_live_frame_path).strip() if save_live_frame_path else None
        self.exit_after_saving_live_frame = bool(exit_after_saving_live_frame)
        self.show_table_ids = bool(show_table_ids)
        if self.table_obb_model and self.table_refine_every > 0:
            # Keep table geometry source consistent when OBB table mode is enabled.
            print("Table OBB model enabled: disabling SAM table refinement (--table-refine-every forced to 0).")
            self.table_refine_every = 0
        self.overlay_style = (
            overlay_style
            if overlay_style in ("debug", "projector", "projector_on_frame")
            else "debug"
        )
        self._track_ttl_frames = int(self.track_ttl_frames)
        self._track_ttl_frames_by_class = {
            "chair": int(min(4, self.track_ttl_frames)),
            "table": int(max(12, self.track_ttl_frames)),
            "person": int(max(8, min(12, self.track_ttl_frames))),
        }
        self._track_debug_every = 10
        self._emit_ghost_overlays = False
        self._class_reacquire_max_age = {
            "table": int(max(4, self.reacquire_max_age)),
            "person": int(max(3, min(self.reacquire_max_age, self._track_ttl_frames_by_class["person"]))),
            "chair": 0,
        }
        self._class_match_dist_px = {
            "table": float(max(70.0, self.reacquire_max_dist * 0.80)),
            "person": float(max(80.0, self.reacquire_max_dist * 0.95)),
            "chair": float(max(55.0, self.reacquire_max_dist * 0.75)),
        }
        self._class_match_iou_min = {
            "table": float(max(0.12, self.reacquire_min_iou)),
            "person": float(max(0.08, self.reacquire_min_iou)),
            "chair": float(max(0.05, self.reacquire_min_iou)),
        }
        self._track_match_threshold_px = {
            "chair": float(self.reacquire_max_dist),
            "table": float(self.reacquire_max_dist),
            "person": float(self.reacquire_max_dist),
        }
        self._yolo_conf_min = {
            "chair": float(self.conf_keep),
            "table": float(self.conf_keep),
            "person": float(self.conf_keep),
        }
        self._match_gate_cfg = {
            "chair": {"iou_min": float(self.reacquire_min_iou), "area_ratio_min": 0.3, "area_ratio_max": 3.5},
            "person": {"iou_min": float(self.reacquire_min_iou), "area_ratio_min": 0.3, "area_ratio_max": 3.5},
            "table": {"iou_min": float(self.reacquire_min_iou), "area_ratio_min": 0.3, "area_ratio_max": 3.5},
        }
        self._bbox_ema_alpha = {
            "chair": 0.30,
            "person": 0.30,
            "table": 0.20,
        }
        self._hard_jump_px = {
            "chair": 90.0,
            "person": 90.0,
            "table": 130.0,
        }
        self._center_smooth_alpha = 0.20
        self._tracks: Dict[str, Dict[str, Dict]] = {
            "chair": {},
            "table": {},
            "person": {},
        }
        self._next_id: Dict[str, int] = {
            "chair": 0,
            "table": 0,
            "person": 0,
        }
        self._person_new_ids_since_log = 0
        self._table_obb_detector = None

        self.frame_id = 0
        self._last_render_frame_id = -1
        self._last_overlay_items = []  # Storage for visualization items
        self.state_by_id = {}  # State management: {id: {"label":..., "bbox_px":..., "center_px":..., "shape":...}}

        if proposals_mode == "yolo":
            # YOLO mode: init detector; optionally load SAM for table geometry refinement
            self._yolo_detector = None  # lazily set below to allow lazy import
            from src.vision.detection.yolo_detector import YOLODetector, YOLOTableOBBDetector
            self._yolo_detector = YOLODetector(
                model=yolo_model,
                device=device,
                conf=yolo_conf,
                iou=yolo_iou,
            )
            if self.table_obb_model:
                self._table_obb_detector = YOLOTableOBBDetector(
                    model=self.table_obb_model,
                    device=device,
                    conf=self.table_obb_conf,
                    iou=self.table_obb_iou,
                    max_det=yolo_max_det,
                    raw_max_det=self.table_obb_max_det,
                    raw_min_conf=self.table_obb_raw_min_conf,
                )
            if self.table_refine_every > 0:
                _refine_cfg = sam3_config_path or "configs/sam2/sam2.1_hiera_l.yaml"
                _refine_ckpt = sam3_checkpoint_path or "checkpoints/sam2.1_hiera_large.pt"
                try:
                    self.segmenter = SAM3Segmenter(
                        config_path=_refine_cfg,
                        checkpoint_path=_refine_ckpt,
                        device=device,
                    )
                except Exception as exc:
                    raise RuntimeError(
                        "Table refinement requested (--table-refine-every > 0), but SAM2/SAM3Segmenter could not be initialised. "
                        "Install SAM2 or disable refinement with --table-refine-every 0."
                    ) from exc
                print(f"SAM table refine: every={self.table_refine_every} frames, max={table_refine_max} tables")
            else:
                self.segmenter = None
            print(f"\n=== VisionPipeline Initialized (YOLO mode) ===")
            print(f"YOLO model:  {yolo_model}")
            print(f"YOLO conf: {yolo_conf}  iou: {yolo_iou}  max_det: {yolo_max_det}")
            if self.table_obb_model:
                print(
                    f"Table OBB model: {self.table_obb_model} "
                    f"(conf={self.table_obb_conf}, iou={self.table_obb_iou})"
                )
                if self.table_obb_max_det > 0 or self.table_obb_raw_min_conf is not None:
                    print(
                        f"Table OBB raw filter: top_k={self.table_obb_max_det} "
                        f"min_conf={self.table_obb_raw_min_conf}"
                    )
                print(
                    f"Table anti-phantom: new_conf>={self.table_new_conf_create} "
                    f"new_min_area={self.table_new_min_bbox_area} "
                    f"new_min_minside={self.table_new_min_bbox_minside} "
                    f"confirm_frames={self.table_new_confirm_frames} "
                    f"suppress_iou>={self.table_new_suppress_iou} "
                    f"suppress_center_dist<={self.table_new_suppress_center_dist_px}px"
                )
                if self.table_protect_existing_tracks or self.table_recover_lost_tracks:
                    print(
                        f"Table continuity: protect_existing={self.table_protect_existing_tracks} "
                        f"recover_lost={self.table_recover_lost_tracks} "
                        f"lost_ttl={self.table_lost_track_ttl}"
                    )
                if self.table_recover_lost_tracks and self.table_birth_block_near_lost_dist > 0.0:
                    _lost_age_gate = self.table_birth_block_near_lost_frames if self.table_birth_block_near_lost_frames > 0 else "recoverable_ttl"
                    print(
                        f"Table birth suppression near lost: dist<={self.table_birth_block_near_lost_dist}px "
                        f"lost_age<={_lost_age_gate}"
                    )
                if self.table_angle_deadband_deg > 0.0:
                    print(
                        f"Table angle hysteresis: deadband={self.table_angle_deadband_deg}deg"
                    )
                if self.table_static_hold_enabled:
                    print(
                        f"Table static hold: frames>={self.table_static_hold_frames} "
                        f"center<{self.table_static_hold_center_px}px "
                        f"angle<{self.table_static_hold_angle_deg}deg "
                        f"area<{self.table_static_hold_area_frac}"
                    )
                if self.table_obb_debug_raw_overlay or self.table_obb_debug_jsonl:
                    print(
                        f"Table OBB debug: raw_overlay={self.table_obb_debug_raw_overlay} "
                        f"jsonl={self.table_obb_debug_jsonl}"
                    )
            print(
                f"Tracking: ttl={self.track_ttl_frames} conf_create={self.conf_create} conf_keep={self.conf_keep} "
                f"reacquire_age={self.reacquire_max_age} reacquire_dist={self.reacquire_max_dist} "
                f"reacquire_iou={self.reacquire_min_iou} chairs_no_ghost={self.chairs_no_ghost}"
            )
            print(
                f"Table motion gate: shift_px>{self.table_motion_shift_px} iou<{self.table_motion_iou_min} "
                f"area_change>{self.table_motion_area_change} stable_frames={self.table_stable_frames}"
            )
            print("Overlay ghosting: disabled (internal short-term reacquire only)")
            if self.no_ghosting:
                print("Ghosting: disabled")
            print(f"Device: {device}")
            print(f"Homography: {'enabled' if self.H is not None else 'disabled'}")
            print(f"Table refine: {'every ' + str(self.table_refine_every) + ' frames' if self.table_refine_every > 0 else 'disabled'}")
            print(f"===================================\n")
        else:
            # SAM2 mode: load segmenter
            self._yolo_detector = None
            self._table_obb_detector = None
            if sam3_config_path is None:
                sam3_config_path = "configs/sam2/sam2.1_hiera_l.yaml"
            if sam3_checkpoint_path is None:
                sam3_checkpoint_path = "checkpoints/sam2.1_hiera_large.pt"
            self.segmenter = SAM3Segmenter(
                config_path=sam3_config_path,
                checkpoint_path=sam3_checkpoint_path,
                device=device
            )
            print(f"\n=== VisionPipeline Initialized ===")
            print(f"SAM2.1 Config: {sam3_config_path}")
            print(f"SAM2.1 Checkpoint: {sam3_checkpoint_path}")
            print(f"Device: {device}")
            print(f"Homography: {'enabled' if self.H is not None else 'disabled'}")
            print(f"Table area filter: [{table_min_area}, {table_max_area}] px")
            print(f"Chair area filter: [{chair_min_area}, {chair_max_area}] px")
            print(f"===================================\n")

    def reset_tracks(self):
        """Reset YOLO tracking state (tracks and id counters)."""
        self._tracks = {
            "chair": {},
            "table": {},
            "person": {},
        }
        self._next_id = {
            "chair": 0,
            "table": 0,
            "person": 0,
        }
        self._person_new_ids_since_log = 0

    def _apply_input_crop(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Apply optional fixed input crop, clamped to frame bounds."""
        if self._input_crop is None:
            return frame_bgr

        fh, fw = frame_bgr.shape[:2]
        if fw <= 1 or fh <= 1:
            return frame_bgr

        crop_x, crop_y, crop_w, crop_h = self._input_crop
        x1 = max(0, min(fw - 1, int(crop_x)))
        y1 = max(0, min(fh - 1, int(crop_y)))
        x2 = max(0, min(fw, int(crop_x + crop_w)))
        y2 = max(0, min(fh, int(crop_y + crop_h)))

        if x2 <= x1 or y2 <= y1:
            if not self._input_crop_warned:
                print(
                    f"WARNING: invalid input crop ({crop_x},{crop_y},{crop_w},{crop_h}) "
                    f"for frame size {fw}x{fh}; using full frame."
                )
                self._input_crop_warned = True
            return frame_bgr

        cropped = frame_bgr[y1:y2, x1:x2]
        if cropped.size == 0:
            if not self._input_crop_warned:
                print(
                    f"WARNING: empty input crop ({crop_x},{crop_y},{crop_w},{crop_h}) "
                    f"for frame size {fw}x{fh}; using full frame."
                )
                self._input_crop_warned = True
            return frame_bgr

        return cropped

    def _apply_camera_rotation(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Apply optional camera frame rotation (0/90/180/270)."""
        if self.camera_rotate == 90:
            return cv2.rotate(frame_bgr, cv2.ROTATE_90_CLOCKWISE)
        if self.camera_rotate == 180:
            return cv2.rotate(frame_bgr, cv2.ROTATE_180)
        if self.camera_rotate == 270:
            return cv2.rotate(frame_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame_bgr

    def _apply_display_rotation(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Apply optional display rotation for live output windows only."""
        if self.display_rotate == 90:
            return cv2.rotate(frame_bgr, cv2.ROTATE_90_CLOCKWISE)
        if self.display_rotate == 180:
            return cv2.rotate(frame_bgr, cv2.ROTATE_180)
        if self.display_rotate == 270:
            return cv2.rotate(frame_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame_bgr

    @staticmethod
    def _bbox_area(bbox: List[int]) -> float:
        """Compute bbox area in pixels (clamped to non-negative extents)."""
        x1, y1, x2, y2 = [int(v) for v in bbox]
        w = max(0, x2 - x1)
        h = max(0, y2 - y1)
        return float(w * h)

    @staticmethod
    def _bbox_iou(box_a: List[int], box_b: List[int]) -> float:
        """Compute IoU between two [x1,y1,x2,y2] boxes."""
        ax1, ay1, ax2, ay2 = [int(v) for v in box_a]
        bx1, by1, bx2, by2 = [int(v) for v in box_b]

        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        iw = max(0, ix2 - ix1)
        ih = max(0, iy2 - iy1)
        inter = float(iw * ih)
        if inter <= 0:
            return 0.0

        area_a = VisionPipeline._bbox_area(box_a)
        area_b = VisionPipeline._bbox_area(box_b)
        union = area_a + area_b - inter
        if union <= 0:
            return 0.0
        return inter / union

    @staticmethod
    def _bbox_center(bbox: List[int]) -> Tuple[float, float]:
        """Compute bbox center for [x1,y1,x2,y2]."""
        x1, y1, x2, y2 = [float(v) for v in bbox]
        return (0.5 * (x1 + x2), 0.5 * (y1 + y2))

    @staticmethod
    def _center_dist(c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
        """Euclidean distance between two 2D points."""
        return float(np.hypot(float(c1[0]) - float(c2[0]), float(c1[1]) - float(c2[1])))

    def _greedy_track_match(
        self,
        detections: List[Dict],
        class_tracks: Dict[str, Dict],
        track_ids: List[str],
        available_det_indices: set,
        label: str,
    ) -> Dict[str, int]:
        """Greedy one-to-one match: 0.7*IoU + 0.3*(1 - normalized center distance)."""
        if not detections or not track_ids or not available_det_indices:
            return {}

        candidates: List[Tuple[float, float, float, str, int]] = []
        max_dist = max(1e-6, float(self._class_match_dist_px.get(label, self.reacquire_max_dist)))
        min_iou = float(self._class_match_iou_min.get(label, self.reacquire_min_iou))

        for tid in track_ids:
            track = class_tracks.get(tid)
            if not track:
                continue
            tbbox = track.get("bbox")
            if not tbbox or len(tbbox) != 4:
                continue
            tcenter = self._bbox_center(tbbox)
            for det_idx in list(available_det_indices):
                det = detections[det_idx]
                dbbox = det.get("bbox_px", [0, 0, 0, 0])
                if len(dbbox) != 4:
                    continue
                iou_val = self._bbox_iou(tbbox, dbbox)
                if iou_val < min_iou:
                    continue
                dcenter = self._bbox_center(dbbox)
                dist = self._center_dist(tcenter, dcenter)
                if dist > max_dist:
                    continue
                norm_dist = min(1.0, dist / max_dist)
                match_score = (0.7 * float(iou_val)) + (0.3 * (1.0 - norm_dist))
                candidates.append((match_score, float(iou_val), -dist, tid, det_idx))

        candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        matches: Dict[str, int] = {}
        used_tracks = set()
        used_dets = set()
        for _, _, _, tid, det_idx in candidates:
            if tid in used_tracks or det_idx in used_dets:
                continue
            matches[tid] = det_idx
            used_tracks.add(tid)
            used_dets.add(det_idx)

        return matches

    @staticmethod
    def _ema_bbox(old_bbox: List[int], det_bbox: List[int], alpha_new: float) -> List[int]:
        """Exponential moving average update for bbox coordinates."""
        return [
            int(round((1.0 - alpha_new) * float(old_bbox[i]) + alpha_new * float(det_bbox[i])))
            for i in range(4)
        ]

    def _update_table_motion_state(self, track: Dict, old_bbox: List[int], det_bbox: List[int]) -> None:
        """Update per-table moving/stable state from bbox dynamics."""
        old_center = self._bbox_center(old_bbox)
        det_center = self._bbox_center(det_bbox)
        center_shift_px = self._center_dist(old_center, det_center)
        iou_prev = self._bbox_iou(old_bbox, det_bbox)
        old_area = max(1.0, self._bbox_area(old_bbox))
        det_area = self._bbox_area(det_bbox)
        area_change = abs(det_area - old_area) / old_area

        moving_now = (
            center_shift_px > float(self.table_motion_shift_px)
            or iou_prev < float(self.table_motion_iou_min)
            or area_change > float(self.table_motion_area_change)
        )
        stable_count = int(track.get("table_stable_count", 0))
        if moving_now:
            stable_count = 0
            track["table_motion_state"] = "moving"
            # Prevent stale SAM geometry from being reused while object moves.
            track["last_corners_px"] = None
        else:
            stable_count += 1
            if stable_count >= int(self.table_stable_frames):
                track["table_motion_state"] = "stable"
            else:
                track["table_motion_state"] = "moving"

        track["table_stable_count"] = stable_count
        track["table_center_shift_px"] = float(center_shift_px)
        track["table_prev_iou"] = float(iou_prev)
        track["table_area_change"] = float(area_change)

    @staticmethod
    def _get_monitor_layout_windows() -> List[Tuple[int, int, int, int]]:
        """Return monitor rectangles as (x, y, w, h) on Windows; fallback to primary origin."""
        try:
            import ctypes
            from ctypes import wintypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG),
                ]

            monitors: List[Tuple[int, int, int, int]] = []

            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                wintypes.HMONITOR,
                wintypes.HDC,
                ctypes.POINTER(RECT),
                wintypes.LPARAM,
            )

            def _callback(hmonitor, hdc, lprc_monitor, lparam):  # noqa: ANN001
                rc = lprc_monitor.contents
                monitors.append((int(rc.left), int(rc.top), int(rc.right - rc.left), int(rc.bottom - rc.top)))
                return 1

            cb = MONITORENUMPROC(_callback)
            ctypes.windll.user32.EnumDisplayMonitors(0, 0, cb, 0)
            return monitors if monitors else [(0, 0, 0, 0)]
        except Exception:
            return [(0, 0, 0, 0)]
    
    def process_frame(self, frame_bgr: np.ndarray, timestamp_iso: Optional[str] = None) -> FrameEvent:
        """
        Process a single frame through the vision pipeline.
        
        Args:
            frame_bgr: Input frame in BGR format (OpenCV)
            timestamp_iso: Optional ISO timestamp, defaults to now_iso()
        
        Returns:
            FrameEvent with detected furniture entities
        """
        if timestamp_iso is None:
            timestamp_iso = now_iso()
        
        # 1. Segment with SAM3
        seg_results = self.segmenter.segment_image(
            frame_bgr,
            prompts=["table", "chair"],
            debug_dir=self.debug_dir
        )
        
        # 2. Post-process tables (min-area rect)
        table_masks = seg_results.get("table", [])
        table_results = postprocess_furniture_masks(
            table_masks,
            class_name="table",
            min_area_px=self.table_min_area,
            max_area_px=self.table_max_area,
            fit_shape="rect"
        )
        
        # 3. Post-process chairs (circle)
        chair_masks = seg_results.get("chair", [])
        chair_results = postprocess_furniture_masks(
            chair_masks,
            class_name="chair",
            min_area_px=self.chair_min_area,
            max_area_px=self.chair_max_area,
            fit_shape="circle"
        )
        
        # 4. Convert to DetectedEntity with homography projection
        furniture_entities = []
        
        # Tables
        for i, table in enumerate(table_results):
            center_px = table["center_px"]
            yaw_rad = table["yaw_rad"]
            
            # Project to floor coordinates
            if self.H is not None:
                center_floor = apply_homography(center_px, self.H)
            else:
                center_floor = center_px
            
            pose = Pose2D(x=center_floor[0], y=center_floor[1], theta=yaw_rad)
            
            entity = DetectedEntity(
                id=f"table_{i}",
                kind="table",
                pose=pose,
                confidence=table.get("score", 1.0)
            )
            furniture_entities.append(entity)
        
        # Chairs
        for i, chair in enumerate(chair_results):
            center_px = chair["center_px"]
            
            # Project to floor coordinates
            if self.H is not None:
                center_floor = apply_homography(center_px, self.H)
            else:
                center_floor = center_px
            
            pose = Pose2D(x=center_floor[0], y=center_floor[1], theta=None)
            
            entity = DetectedEntity(
                id=f"chair_{i}",
                kind="chair",
                pose=pose,
                confidence=chair.get("score", 1.0)
            )
            furniture_entities.append(entity)
        
        # 5. Build FrameEvent
        frame_event = FrameEvent(
            timestamp_iso=timestamp_iso,
            frame_id=self.frame_id,
            furniture=furniture_entities,
            people=[],  # No person detection in this pipeline
            world={"homography_applied": self.H is not None}
        )
        
        self.frame_id += 1
        
        return frame_event
    
    def process_video_to_jsonl(
        self,
        video_path: str,
        output_jsonl: str,
        max_frames: Optional[int] = None,
        flush_every: int = 10,
    ):
        """
        Process a video file and write FrameEvents to JSONL.
        
        Args:
            video_path: Path to input video file
            output_jsonl: Path to output JSONL file
            max_frames: Maximum number of frames to process (None = all)
            flush_every: Flush/fsync every N frames (based on frame_id)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
        
        output_path = Path(output_jsonl)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        frame_count = 0
        
        with open(output_path, "w") as f:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = self._apply_input_crop(frame)
                
                frame_event = self.process_frame(frame)
                f.write(json.dumps(frame_event.to_dict()) + "\n")
                if flush_every > 0 and (frame_event.frame_id % flush_every == 0):
                    f.flush()
                    os.fsync(f.fileno())
                
                frame_count += 1
                if max_frames is not None and frame_count >= max_frames:
                    break
                
                if frame_count % 10 == 0:
                    print(f"Processed {frame_count} frames...")
        
        cap.release()
        print(f"Wrote {frame_count} FrameEvents to {output_path}")
    
    def process_camera_stream(
        self,
        camera_index: int = 0,
        output_jsonl: Optional[str] = None,
        display: bool = True,
        projector_display: bool = False,
        projector_monitor: int = 1,
        flush_every: int = 10,
    ):
        """
        Process live camera stream.
        
        Args:
            camera_index: Camera device index
            output_jsonl: Optional path to write JSONL output
            display: Whether to show live display window
            projector_display: Whether to show a fullscreen projector overlay window
            projector_monitor: Monitor index for projector window (0=primary, 1=second, ...)
            flush_every: Flush/fsync every N frames (based on frame_id)
        """
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera {camera_index}")

        if self.camera_width is not None:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.camera_width))
        if self.camera_height is not None:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.camera_height))

        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(
            f"Camera capture setup: requested={self.camera_width}x{self.camera_height} "
            f"actual={actual_width}x{actual_height} rotate={self.camera_rotate} "
            f"display_rotate={self.display_rotate} crop={'on' if self._input_crop is not None else 'off'}"
        )
        
        jsonl_file = None
        if output_jsonl is not None:
            output_path = Path(output_jsonl)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            jsonl_file = open(output_path, "w")

        projector_window_name = "Projector"
        if projector_display:
            cv2.namedWindow(projector_window_name, cv2.WINDOW_NORMAL)
            monitor_layout = self._get_monitor_layout_windows()
            if projector_monitor < 0:
                projector_monitor = 0
            if projector_monitor >= len(monitor_layout):
                projector_monitor = max(0, len(monitor_layout) - 1)
            mon_x, mon_y, mon_w, mon_h = monitor_layout[projector_monitor]
            cv2.moveWindow(projector_window_name, mon_x, mon_y)
            cv2.setWindowProperty(projector_window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            print(f"Projector window on monitor {projector_monitor} at ({mon_x}, {mon_y}) size {mon_w}x{mon_h}")

        live_frame_id = 0
        _logged_first_frame = False
        _saved_live_frame = False
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame from camera")
                    break

                raw_h, raw_w = frame.shape[:2]
                frame = self._apply_camera_rotation(frame)
                rot_h, rot_w = frame.shape[:2]

                if self.save_live_frame_path and not _saved_live_frame:
                    _save_path = Path(self.save_live_frame_path)
                    _save_path.parent.mkdir(parents=True, exist_ok=True)
                    _ok = cv2.imwrite(str(_save_path), frame)
                    if _ok:
                        print(f"Saved rotated live frame (pre-crop) to {_save_path}")
                    else:
                        print(f"WARNING: failed to save rotated live frame to {_save_path}")
                    _saved_live_frame = True
                    if self.exit_after_saving_live_frame:
                        print("Exiting after saving first live frame (--exit-after-saving-live-frame).")
                        break

                frame = self._apply_input_crop(frame)

                if not _logged_first_frame:
                    print(
                        f"Camera first frame: raw={raw_w}x{raw_h} rotate={self.camera_rotate} "
                        f"after_rotate={rot_w}x{rot_h} crop={'on' if self._input_crop is not None else 'off'}"
                    )
                    _logged_first_frame = True

                timestamp_iso = now_iso()
                if self._proposals_mode == "yolo":
                    frame_event = self._process_frame_yolo(
                        frame_bgr=frame,
                        frame_id=live_frame_id,
                        timestamp_iso=timestamp_iso,
                    )
                else:
                    frame_event = self.process_frame(frame, timestamp_iso=timestamp_iso)
                live_frame_id += 1
                
                if jsonl_file is not None:
                    jsonl_file.write(json.dumps(frame_event.to_dict()) + "\n")
                    if flush_every > 0 and (frame_event.frame_id % flush_every == 0):
                        jsonl_file.flush()
                        os.fsync(jsonl_file.fileno())
                
                if display:
                    if self._last_overlay_items:
                        display_frame = self.render_overlay(frame, self._last_overlay_items)
                    else:
                        # Fallback if no overlay items are available.
                        display_frame = self._draw_detections(frame, frame_event)
                    display_frame = self._apply_display_rotation(display_frame)
                    cv2.imshow("Vision Pipeline", display_frame)

                if projector_display:
                    # Render using configured overlay style (projector/projector_on_frame/debug).
                    projector_items = self._last_overlay_items if self._last_overlay_items else []
                    projector_frame = self.render_overlay(frame, projector_items)
                    projector_frame = self._apply_display_rotation(projector_frame)
                    cv2.imshow(projector_window_name, projector_frame)

                if display or projector_display:
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('r'):
                        self.reset_tracks()
                        print("tracks reset")
                    if key == ord('q') or key == 27:  # q or ESC
                        break
        
        finally:
            cap.release()
            if jsonl_file is not None:
                jsonl_file.close()
            if display or projector_display:
                cv2.destroyAllWindows()
    
    def _draw_detections(self, frame: np.ndarray, frame_event: FrameEvent) -> np.ndarray:
        """Draw detected entities on frame for visualization."""
        display = frame.copy()
        
        for entity in frame_event.furniture:
            # Draw circle at center (pixel coords, not floor coords)
            # Note: pose is in floor coords if homography is applied
            # For display, we'd need inverse homography or store pixel coords
            # For now, just show entity count
            pass
        
        # Draw info text
        info = f"Frame {frame_event.frame_id}: {len(frame_event.furniture)} furniture"
        cv2.putText(display, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        return display
    
    def _draw_detections_with_boxes(self, frame: np.ndarray, frame_event: FrameEvent) -> np.ndarray:
        """Draw detected entities on frame with detailed information."""
        display = frame.copy()
        h, w = frame.shape[:2]
        
        # Create semi-transparent overlay for text background
        overlay = display.copy()
        
        # Draw frame info at top
        frame_info = f"Frame {frame_event.frame_id}"
        cv2.putText(display, frame_info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # Draw detections summary
        tables = [e for e in frame_event.furniture if e.kind == "table"]
        chairs = [e for e in frame_event.furniture if e.kind == "chair"]
        
        summary = f"Tables: {len(tables)}, Chairs: {len(chairs)}"
        cv2.putText(display, summary, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 200), 2)
        
        # Draw entity list
        y_offset = 110
        for i, entity in enumerate(frame_event.furniture):
            color = (0, 255, 0) if entity.kind == "table" else (255, 0, 0)
            text = f"  {entity.kind.upper()}: {entity.id} (conf: {entity.confidence:.2f})"
            cv2.putText(display, text, (10, y_offset + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
        
        return display
    
    def render_overlay(self, frame_bgr: np.ndarray, overlay_items: List[Dict]) -> np.ndarray:
        """
        Render segmentation masks and detections on frame.
        
        Args:
            frame_bgr: Input frame in BGR format
            overlay_items: List of dicts with keys:
                - id: object ID string
                - label: 'table' or 'chair'
                - mask: boolean mask array
                - score: confidence score
                - shape: dict with geometry (rect or circle)
        
        Returns:
            Overlay frame with visualized masks and geometries
        """
        frame_id = getattr(self, "_dbg_frame_id", None)
        if frame_id in (0, 11):
            for _item in overlay_items:
                if _item.get("label") != "table":
                    continue
                _shape = _item.get("shape", {})
                _has_bbox = _shape.get("bbox_px") is not None
                _has_corners = _shape.get("corners_px") is not None
                print(
                    f"[render_overlay dbg] frame={frame_id} table_id={_item.get('id')} "
                    f"has_bbox_px={_has_bbox} has_corners_px={_has_corners}"
                )

        if self.overlay_style == "projector":
            return self._render_overlay_projector(frame_bgr, overlay_items)
        if self.overlay_style == "projector_on_frame":
            return self._render_overlay_projector_on_frame(frame_bgr, overlay_items)

        overlay = frame_bgr.copy()
        h, w = overlay.shape[:2]
        
        # Color map for labels
        label_colors = {
            "table": (0, 255, 255),    # Cyan
            "chair": (255, 0, 255),    # Magenta
            "person": (0, 255, 0),     # Green
            "table_reject": (0, 165, 255),  # Orange
            "table_obb_raw": (255, 200, 0),  # Light blue/orange mix for raw OBB debug
        }
        
        for item in overlay_items:
            label = item.get("label", "unknown")
            mask = item.get("mask")
            obj_id = item.get("id", "")
            score = item.get("score", 0.0)
            is_ghost = bool(item.get("ghost", False))
            shape = item.get("shape", {})
            
            # Get color for this label
            color = label_colors.get(label, (128, 128, 128))

            # Draw mask and contour if available
            has_mask = mask is not None and mask.any()
            if has_mask:
                mask_uint8 = (mask.astype(np.uint8) * 255)

                alpha = 0.18 if is_ghost else 0.35
                mask_indices = mask > 0
                overlay[mask_indices] = (
                    overlay[mask_indices] * (1 - alpha) +
                    np.array(color) * alpha
                ).astype(np.uint8)

                contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    cv2.drawContours(overlay, contours, -1, color, 1 if is_ghost else 2)

            # tables: prefer corners, then poly, and use bbox only as last fallback.
            bbox = shape.get("bbox_px")
            if label == "table":
                table_poly_like = shape.get("corners_px")
                if not table_poly_like:
                    table_poly_like = shape.get("poly_px")

                if table_poly_like and len(table_poly_like) >= 3:
                    pts = np.array(table_poly_like, dtype=np.int32)
                    cv2.polylines(overlay, [pts], True, color, 1 if is_ghost else 2)
                elif bbox and len(bbox) == 4:
                    x1, y1, x2, y2 = [int(v) for v in bbox]
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 1 if is_ghost else 2)

            if label == "table" and "center_px" in shape:
                center = shape["center_px"]
                if center:
                    cx, cy = int(center[0]), int(center[1])
                    cv2.circle(overlay, (cx, cy), 4, color, -1)
            
            if label == "chair" and "center_px" in shape and "radius_px" in shape:
                center = shape["center_px"]
                radius = shape["radius_px"]
                if center and radius:
                    cx, cy = int(center[0]), int(center[1])
                    r = int(radius)
                    cv2.circle(overlay, (cx, cy), r, color, 2)
                    cv2.circle(overlay, (cx, cy), 4, color, -1)

            if label == "person" and "bbox_px" in shape:
                bbox = shape["bbox_px"]
                if bbox:
                    x1, y1, x2, y2 = [int(v) for v in bbox]
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 1 if is_ghost else 2)
                    if "center_px" in shape:
                        cx, cy = int(shape["center_px"][0]), int(shape["center_px"][1])
                        cv2.circle(overlay, (cx, cy), 4, color, -1)

            if label == "table_reject" and "bbox_px" in shape:
                bbox = shape["bbox_px"]
                if bbox:
                    x1, y1, x2, y2 = [int(v) for v in bbox]
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
                    reject_reason = str(shape.get("reject_reason", "table_reject_small"))
                    cv2.putText(overlay, reject_reason, (x1, max(16, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

            if label == "table_obb_raw":
                poly_px = shape.get("poly_px")
                if poly_px is not None and len(poly_px) == 4:
                    pts = np.array(poly_px, dtype=np.int32)
                    cv2.polylines(overlay, [pts], True, color, 1)
                elif bbox and len(bbox) == 4:
                    x1, y1, x2, y2 = [int(v) for v in bbox]
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 1)
                center = shape.get("center_px")
                if center and len(center) >= 2:
                    cx, cy = int(center[0]), int(center[1])
                    cv2.circle(overlay, (cx, cy), 3, color, -1)
            
            # Draw ID/score text. With show_table_ids, constrain text overlays to final table tracks.
            if self.show_table_ids:
                if label != "table" or not obj_id:
                    continue
                text = f"T{obj_id}"
                if bbox and len(bbox) == 4:
                    text_x = max(2, int(bbox[0]) + 6)
                    text_y = max(16, int(bbox[1]) - 6)
                else:
                    text_x, text_y = 10, 30
            else:
                text = f"{obj_id} ({score:.2f})"

                # Find text position near centroid
                if has_mask:
                    y_coords, x_coords = np.where(mask)
                    text_x = int(np.mean(x_coords))
                    text_y = int(np.mean(y_coords))
                elif "center_px" in shape and shape.get("center_px") is not None:
                    text_x = int(shape["center_px"][0])
                    text_y = int(shape["center_px"][1])
                elif bbox and len(bbox) == 4:
                    text_x = int(bbox[0])
                    text_y = max(20, int(bbox[1]))
                else:
                    text_x, text_y = 10, 30
            
            # Draw background rectangle for text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
            
            bg_x1, bg_y1 = max(0, text_x - 5), max(0, text_y - text_h - 5)
            bg_x2, bg_y2 = min(w, text_x + text_w + 5), min(h, text_y + 5)
            
            cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
            cv2.putText(overlay, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
        
        return overlay

    def _render_overlay_projector(self, frame_bgr: np.ndarray, overlay_items: List[Dict]) -> np.ndarray:
        """Render high-contrast projector overlay: white geometry on black background."""
        h, w = frame_bgr.shape[:2]
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        chair_target_radius = int(np.clip(round(min(w, h) * 0.042), 30, 54))

        def _inset_polygon_pts(poly_pts: np.ndarray, inset_ratio: float = 0.08) -> np.ndarray:
            if poly_pts.shape[0] < 3:
                return poly_pts
            center = np.mean(poly_pts.astype(np.float32), axis=0)
            shifted = center + (poly_pts.astype(np.float32) - center) * float(max(0.0, 1.0 - inset_ratio))
            return np.round(shifted).astype(np.int32)

        for item in overlay_items:
            label = item.get("label", "unknown")
            shape = item.get("shape", {})
            obj_id = item.get("id", "")
            bbox = shape.get("bbox_px")
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = [int(v) for v in bbox]
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(0, min(w - 1, x2))
            y2 = max(0, min(h - 1, y2))
            if x2 <= x1 or y2 <= y1:
                continue

            if label == "table":
                poly_px = shape.get("corners_px")
                if poly_px is None:
                    poly_px = shape.get("poly_px")
                table_poly = None
                if poly_px is not None and len(poly_px) == 4:
                    table_poly = np.array(poly_px, dtype=np.int32)
                if table_poly is not None:
                    inset_poly = _inset_polygon_pts(table_poly, inset_ratio=0.12)
                    cv2.polylines(overlay, [inset_poly.reshape(-1, 1, 2)], True, (255, 255, 255), 2)
                else:
                    inset_px = max(1, int(round(0.08 * min(x2 - x1, y2 - y1))))
                    ix1 = min(x2 - 1, x1 + inset_px)
                    iy1 = min(y2 - 1, y1 + inset_px)
                    ix2 = max(ix1 + 1, x2 - inset_px)
                    iy2 = max(iy1 + 1, y2 - inset_px)
                    cv2.rectangle(overlay, (ix1, iy1), (ix2, iy2), (255, 255, 255), 2)

                if self.show_table_ids and obj_id:
                    text = f"T{obj_id}"
                    tx = max(2, min(w - 2, x1 + 6))
                    ty = max(16, min(h - 2, y1 - 6))
                    cv2.putText(overlay, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            elif label == "table_reject":
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 165, 255), 2)
                reject_reason = str(shape.get("reject_reason", "table_reject_small"))
                cv2.putText(overlay, reject_reason, (x1, max(16, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1, cv2.LINE_AA)
            elif label == "table_obb_raw":
                # Keep projector overlays focused on final tracks only.
                continue
            elif label in ("chair", "person"):
                center = shape.get("center_px")
                if center and len(center) >= 2:
                    cx = int(round(float(center[0])))
                    cy = int(round(float(center[1])))
                else:
                    cx = int(round((x1 + x2) / 2.0))
                    cy = int(round((y1 + y2) / 2.0))
                radius = int(round(0.5 * min(x2 - x1, y2 - y1)))
                if radius > 0:
                    color = (255, 0, 0) if label == "chair" else (0, 200, 0)
                    if label == "chair":
                        radius = int(np.clip(radius, int(chair_target_radius * 0.8), int(chair_target_radius * 1.2)))
                        thickness = 2
                    else:
                        radius = max(8, radius)
                        thickness = 4
                    cv2.circle(overlay, (cx, cy), radius, color, thickness)
                    if label == "chair":
                        cv2.circle(overlay, (cx, cy), 2, color, -1)

        return overlay

    def _render_overlay_projector_on_frame(self, frame_bgr: np.ndarray, overlay_items: List[Dict]) -> np.ndarray:
        """Render projector alignment overlay: white geometry alpha-blended onto source frame."""
        h, w = frame_bgr.shape[:2]
        alpha = 0.6

        table_layer = frame_bgr.copy()
        circle_draw_ops: List[Tuple[int, int, int, Tuple[int, int, int], int, str]] = []
        chair_target_radius = int(np.clip(round(min(w, h) * 0.042), 30, 54))

        def _inset_polygon_pts(poly_pts: np.ndarray, inset_ratio: float = 0.08) -> np.ndarray:
            if poly_pts.shape[0] < 3:
                return poly_pts
            center = np.mean(poly_pts.astype(np.float32), axis=0)
            shifted = center + (poly_pts.astype(np.float32) - center) * float(max(0.0, 1.0 - inset_ratio))
            return np.round(shifted).astype(np.int32)

        for item in overlay_items:
            label = item.get("label", "unknown")
            shape = item.get("shape", {})
            obj_id = item.get("id", "")
            bbox = shape.get("bbox_px")
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = [int(v) for v in bbox]
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(0, min(w - 1, x2))
            y2 = max(0, min(h - 1, y2))
            if x2 <= x1 or y2 <= y1:
                continue

            if label == "table_reject":
                continue
            elif label == "table_obb_raw":
                # Keep projector overlays focused on final tracks only.
                continue
            elif label == "table":
                poly_px = shape.get("corners_px")
                if poly_px is None:
                    poly_px = shape.get("poly_px")
                table_poly = None
                if poly_px is not None and len(poly_px) == 4:
                    table_poly = np.array(poly_px, dtype=np.int32)
                if table_poly is not None:
                    inset_poly = _inset_polygon_pts(table_poly, inset_ratio=0.12)
                    cv2.polylines(table_layer, [inset_poly.reshape(-1, 1, 2)], True, (255, 255, 255), 2)
                else:
                    inset_px = max(1, int(round(0.08 * min(x2 - x1, y2 - y1))))
                    ix1 = min(x2 - 1, x1 + inset_px)
                    iy1 = min(y2 - 1, y1 + inset_px)
                    ix2 = max(ix1 + 1, x2 - inset_px)
                    iy2 = max(iy1 + 1, y2 - inset_px)
                    cv2.rectangle(table_layer, (ix1, iy1), (ix2, iy2), (255, 255, 255), 2)

                if self.show_table_ids and obj_id:
                    text = f"T{obj_id}"
                    tx = max(2, min(w - 2, x1 + 6))
                    ty = max(16, min(h - 2, y1 - 6))
                    cv2.putText(table_layer, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            elif label in ("chair", "person"):
                center = shape.get("center_px")
                if center and len(center) >= 2:
                    cx = int(round(float(center[0])))
                    cy = int(round(float(center[1])))
                else:
                    cx = int(round((x1 + x2) / 2.0))
                    cy = int(round((y1 + y2) / 2.0))
                radius = int(round(0.5 * min(x2 - x1, y2 - y1)))
                if radius > 0:
                    color = (255, 0, 0) if label == "chair" else (0, 200, 0)
                    if label == "chair":
                        radius = int(np.clip(radius, int(chair_target_radius * 0.8), int(chair_target_radius * 1.2)))
                        thickness = 2
                    else:
                        radius = max(10, radius)
                        thickness = 4
                    circle_draw_ops.append((cx, cy, radius, color, thickness, label))

        blended = cv2.addWeighted(table_layer, alpha, frame_bgr, 1.0 - alpha, 0.0)

        # Draw class-colored circles directly on blended frame (no extra alpha).
        for cx, cy, radius, color, thickness, kind in circle_draw_ops:
            cv2.circle(blended, (cx, cy), radius, color, thickness)
            if kind == "chair":
                cv2.circle(blended, (cx, cy), 2, color, -1)

        return blended

    def _extract_table_orientation_debug(self, frame_bgr: np.ndarray, bbox_px: List[int], frame_id: int = 0, track_id: object = None) -> Dict:
        """
        Estimate a table yaw from Hough line segments inside an expanded ROI.

        Returns dict with keys:
          - poly: Optional 4-point int32 polygon in image coordinates
          - used_fallback: bool
          - fallback_reason: str
          - n_contours: Number of Hough line segments retained for voting
          - best_area: Dominant angle support length in pixels
          - rect_w: Rotated rectangle width in pixels
          - rect_h: Rotated rectangle height in pixels
          - rect_angle: Dominant angle in degrees
          - mask: Optional[np.ndarray] (edge debug image)
          - yaw_rad: Dominant angle in radians
        """
        result = {
            "poly": None,
            "used_fallback": True,
            "fallback_reason": "no_lines",
            "n_contours": 0,
            "best_area": 0.0,
            "rect_w": 0.0,
            "rect_h": 0.0,
            "rect_angle": 0.0,
            "mask": None,
            "yaw_rad": None,
        }

        try:
            h, w = frame_bgr.shape[:2]
            x1, y1, x2, y2 = [int(v) for v in bbox_px]
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(0, min(w - 1, x2))
            y2 = max(0, min(h - 1, y2))
            if x2 <= x1 or y2 <= y1:
                result["fallback_reason"] = "invalid_bbox"
                return result

            bbox_w = float(x2 - x1)
            bbox_h = float(y2 - y1)
            if bbox_w <= 1.0 or bbox_h <= 1.0:
                result["fallback_reason"] = "invalid_bbox"
                return result

            margin = 20
            rx1 = max(0, x1 - margin)
            ry1 = max(0, y1 - margin)
            rx2 = min(w, x2 + margin)
            ry2 = min(h, y2 + margin)
            if rx2 <= rx1 or ry2 <= ry1:
                result["fallback_reason"] = "invalid_roi"
                return result

            roi = frame_bgr[ry1:ry2, rx1:rx2]
            if roi.size == 0:
                result["fallback_reason"] = "invalid_roi"
                return result

            roi_h, roi_w = roi.shape[:2]
            inner_trim = 20
            ix1 = inner_trim
            iy1 = inner_trim
            ix2 = roi_w - inner_trim
            iy2 = roi_h - inner_trim
            if ix2 <= ix1 or iy2 <= iy1:
                result["fallback_reason"] = "invalid_inner_roi"
                return result

            inner_roi = roi[iy1:iy2, ix1:ix2]
            if inner_roi.size == 0:
                result["fallback_reason"] = "invalid_inner_roi"
                return result

            gray = cv2.cvtColor(inner_roi, cv2.COLOR_BGR2GRAY)
            gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges_inner = cv2.Canny(gray_blur, 50, 150)
            edges = np.zeros((roi_h, roi_w), dtype=np.uint8)
            edges[iy1:iy2, ix1:ix2] = edges_inner
            result["mask"] = edges

            debug_path = None
            debug_tag = f"f{frame_id:05d}_tid{track_id}"
            if self.debug_dir:
                debug_path = Path(self.debug_dir)
                debug_path.mkdir(parents=True, exist_ok=True)
                roi_rgb = roi.copy()
                edge_overlay = roi_rgb.copy()
                edge_pixels = edges > 0
                if np.any(edge_pixels):
                    green_overlay = np.zeros_like(edge_overlay)
                    green_overlay[:, :] = (0, 255, 0)
                    blended = cv2.addWeighted(edge_overlay, 0.5, green_overlay, 0.5, 0.0)
                    edge_overlay[edge_pixels] = blended[edge_pixels]
                cv2.imwrite(str(debug_path / f"table_roi_rgb_{debug_tag}.png"), roi_rgb)
                cv2.imwrite(str(debug_path / f"table_roi_overlay_{debug_tag}.png"), edge_overlay)
                cv2.imwrite(str(debug_path / f"table_mask_bin_{debug_tag}.png"), edges)

            # Tight Hough input for table yaw stability.
            hough_min_line_length = 100
            hough_max_line_gap = 10
            hough_threshold = 80

            lines = cv2.HoughLinesP(
                edges_inner,
                rho=1,
                theta=np.pi / 180.0,
                threshold=hough_threshold,
                minLineLength=hough_min_line_length,
                maxLineGap=hough_max_line_gap,
            )

            if lines is None or len(lines) == 0:
                result["fallback_reason"] = "no_lines"
                if debug_path is not None:
                    hough_vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                    cv2.putText(hough_vis, "kept=0 dropped=0 chosen_angle=n/a", (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(hough_vis, "top_bin_weight=0.0", (8, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.imwrite(str(debug_path / f"table_roi_hough_{debug_tag}.png"), hough_vis)
                return result

            kept_segments: List[Tuple[float, float, float, Tuple[int, int, int, int]]] = []
            dropped_segments: List[Tuple[int, int, int, int]] = []
            for line in lines.reshape(-1, 4):
                x_ai, y_ai, x_bi, y_bi = [int(v) for v in line]
                x_a = x_ai + ix1
                y_a = y_ai + iy1
                x_b = x_bi + ix1
                y_b = y_bi + iy1

                dx = float(x_b - x_a)
                dy = float(y_b - y_a)
                seg_len = float(np.hypot(dx, dy))
                if seg_len < float(hough_min_line_length):
                    dropped_segments.append((x_a, y_a, x_b, y_b))
                    continue

                angle_deg = float(np.degrees(np.arctan2(dy, dx)))
                while angle_deg <= -90.0:
                    angle_deg += 180.0
                while angle_deg > 90.0:
                    angle_deg -= 180.0

                vote_weight = seg_len
                kept_segments.append((angle_deg, seg_len, vote_weight, (x_a, y_a, x_b, y_b)))

            result["n_contours"] = len(kept_segments)
            if not kept_segments:
                result["fallback_reason"] = "no_valid_lines"
                if debug_path is not None:
                    hough_vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                    for x_a, y_a, x_b, y_b in dropped_segments:
                        cv2.line(hough_vis, (x_a, y_a), (x_b, y_b), (60, 60, 60), 1, cv2.LINE_AA)
                    cv2.putText(hough_vis, f"kept=0 dropped={len(dropped_segments)} chosen_angle=n/a", (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(hough_vis, "top_bin_weight=0.0", (8, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.imwrite(str(debug_path / f"table_roi_hough_{debug_tag}.png"), hough_vis)
                return result

            bin_centers = np.arange(-90.0, 95.0, 5.0, dtype=np.float32)
            weights = np.zeros_like(bin_centers, dtype=np.float32)
            for angle_deg, _seg_len, vote_weight, _segment in kept_segments:
                bin_idx = int(np.clip(np.round((angle_deg + 90.0) / 5.0), 0, len(bin_centers) - 1))
                weights[bin_idx] += float(vote_weight)

            best_idx = int(np.argmax(weights))
            dominant_angle_deg = float(bin_centers[best_idx])
            top_bin_weight = float(weights[best_idx])
            result["best_area"] = top_bin_weight

            # Resolve 90-degree ambiguity using bbox aspect preference.
            def _norm_half_pi(theta_rad: float) -> float:
                t = float(theta_rad)
                while t <= -0.5 * np.pi:
                    t += np.pi
                while t > 0.5 * np.pi:
                    t -= np.pi
                return t

            theta = _norm_half_pi(float(np.deg2rad(dominant_angle_deg)))
            theta2 = _norm_half_pi(theta + (0.5 * np.pi))
            if bbox_w >= bbox_h:
                score_theta = abs(theta)
                score_theta2 = abs(theta2)
            else:
                score_theta = abs(abs(theta) - (0.5 * np.pi))
                score_theta2 = abs(abs(theta2) - (0.5 * np.pi))

            theta_final = theta if score_theta <= score_theta2 else theta2
            chosen_label = "theta" if score_theta <= score_theta2 else "theta2"
            chosen_angle_deg = float(np.degrees(theta_final))

            result["rect_w"] = bbox_w
            result["rect_h"] = bbox_h
            result["rect_angle"] = chosen_angle_deg
            result["yaw_rad"] = float(theta_final)

            rect_center = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
            rect = (rect_center, (bbox_w, bbox_h), chosen_angle_deg)
            box = cv2.boxPoints(rect)
            if np.any(box[:, 0] < 0) or np.any(box[:, 0] > (w - 1)) or np.any(box[:, 1] < 0) or np.any(box[:, 1] > (h - 1)):
                result["fallback_reason"] = "polygon_out_of_bounds"
                if debug_path is not None:
                    hough_vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                    for x_a, y_a, x_b, y_b in dropped_segments:
                        cv2.line(hough_vis, (x_a, y_a), (x_b, y_b), (60, 60, 60), 1, cv2.LINE_AA)
                    for _angle_deg, _seg_len, _vote_weight, (x_a, y_a, x_b, y_b) in kept_segments:
                        cv2.line(hough_vis, (x_a, y_a), (x_b, y_b), (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(hough_vis, f"kept={len(kept_segments)} dropped={len(dropped_segments)} chosen_angle={chosen_angle_deg:.1f}", (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(hough_vis, f"top_bin_weight={top_bin_weight:.1f} OOB", (8, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.putText(hough_vis, f"cands: th={np.degrees(theta):.1f} th2={np.degrees(theta2):.1f} pick={chosen_label}", (8, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.imwrite(str(debug_path / f"table_roi_hough_{debug_tag}.png"), hough_vis)
                return result

            result["poly"] = np.round(box).astype(np.int32)
            result["used_fallback"] = False
            result["fallback_reason"] = ""

            if debug_path is not None:
                hough_vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                for x_a, y_a, x_b, y_b in dropped_segments:
                    cv2.line(hough_vis, (x_a, y_a), (x_b, y_b), (60, 60, 60), 1, cv2.LINE_AA)
                for _angle_deg, _seg_len, _vote_weight, (x_a, y_a, x_b, y_b) in kept_segments:
                    cv2.line(hough_vis, (x_a, y_a), (x_b, y_b), (0, 255, 0), 2, cv2.LINE_AA)
                roi_box = np.round(box - np.array([[rx1, ry1]], dtype=np.float32)).astype(np.int32)
                cv2.polylines(hough_vis, [roi_box.reshape(-1, 1, 2)], True, (0, 255, 255), 2)
                cv2.putText(hough_vis, f"kept={len(kept_segments)} dropped={len(dropped_segments)} chosen_angle={chosen_angle_deg:.1f}", (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(hough_vis, f"top_bin_weight={top_bin_weight:.1f}", (8, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(hough_vis, f"cands: th={np.degrees(theta):.1f} th2={np.degrees(theta2):.1f} pick={chosen_label}", (8, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.imwrite(str(debug_path / f"table_roi_hough_{debug_tag}.png"), hough_vis)

            return result

        except Exception as exc:
            result["fallback_reason"] = f"exception:{str(exc)}"
            return result
    
    def _select_boxes_interactive(self, frame_bgr: np.ndarray) -> List[List[int]]:
        """
        Interactive box selection using cv2.selectROI.
        
        Args:
            frame_bgr: Input frame in BGR format
        
        Returns:
            List of boxes in format [[x1, y1, x2, y2], ...]
        """
        boxes = []
        print("Select bounding boxes. Press ENTER to add box, ESC to finish.")
        
        clone = frame_bgr.copy()
        while True:
            roi = cv2.selectROI("Select Box (press ENTER to add, ESC to finish)", clone, showCrosshair=True, fromCenter=False)
            
            # roi format: (x, y, w, h)
            x, y, w, h = roi
            
            if w == 0 or h == 0:
                # User pressed ESC without selecting
                break
            
            # Convert to [x1, y1, x2, y2]
            box = [int(x), int(y), int(x + w), int(y + h)]
            boxes.append(box)
            
            # Draw box on clone for feedback
            cv2.rectangle(clone, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
            cv2.putText(clone, f"Box {len(boxes)}", (box[0], box[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.destroyAllWindows()
        print(f"Selected {len(boxes)} boxes.")
        return boxes
    
    def _validate_geom_dict(self, geom_dict: Optional[Dict], expected_keys: List[str], 
                            geom_type: str = "geometry") -> Dict:
        """
        Validate that a geometry dictionary has the expected structure.
        
        Args:
            geom_dict: The dictionary to validate (can be None)
            expected_keys: List of required keys
            geom_type: Name of geometry type for error messages (e.g., "rect", "circle")
        
        Returns:
            The validated dictionary
        
        Raises:
            ValueError: If validation fails, with debugging information
        """
        if geom_dict is None:
            raise ValueError(f"Invalid {geom_type}: received None instead of dict")
        
        if not isinstance(geom_dict, dict):
            raise ValueError(
                f"Invalid {geom_type}: expected dict, got {type(geom_dict).__name__}. "
                f"Value: {repr(geom_dict)}"
            )
        
        missing_keys = [k for k in expected_keys if k not in geom_dict]
        if missing_keys:
            raise ValueError(
                f"Invalid {geom_type}: missing keys {missing_keys}. "
                f"Available keys: {list(geom_dict.keys())}. "
                f"Dict: {repr(geom_dict)}"
            )
        
        return geom_dict
    
    def _select_best_mask_for_box(self, box_results: List[Dict], box_index: int, 
                                    box_label: str = "") -> Optional[Dict]:
        """
        Select the best mask for a given box from segment_with_boxes results.
        
        If multiple masks are returned for the same box (edge case), keep only
        the one with highest score (or largest area if score is missing).
        
        Args:
            box_results: Full list of results from segment_with_boxes
            box_index: Original box index in the input boxes list
            box_label: Label of the box (table/chair) for logging
        
        Returns:
            Single best result dict, or None if box produced no valid masks
        """
        # For now, segment_with_boxes returns one result per box due to multimask_output=False
        # But we implement this defensively in case that changes
        if not box_results or box_index >= len(box_results):
            return None
        
        # In the normal case, there's exactly one result per box
        result = box_results[box_index]
        
        if self.debug_dir:
            mask = result["mask"]
            area = np.sum(mask)
            score = result.get("score", 0.0)
            print(f"[Box {box_index}] label={box_label} score={score:.3f} area={area} -> kept 1")
        
        return result
    
    def process_frame_with_boxes(self, frame_bgr: np.ndarray, boxes: List[List[int]], 
                                 timestamp_iso: Optional[str] = None,
                                 box_labels: Optional[List[str]] = None,
                                 frame_id: int = 0,
                                 refine_every: int = 0,
                                 box_margin_px: int = 0) -> FrameEvent:
        """
        Process a single frame with box prompts and state management for stable tracking.
        
        Three modes:
        1. frame_id == 0: Initialize state from boxes_init + SAM2 segmentation
        2. frame_id % refine_every == 0 (if refine_every > 0): Re-segment with expanded boxes
        3. Otherwise: Tracking mode (keep state, optionally apply Kalman prediction)
        
        Args:
            frame_bgr: Input frame in BGR format
            boxes: List of bounding boxes [[x1, y1, x2, y2], ...] (used only for frame_id==0)
            timestamp_iso: Optional ISO timestamp
            box_labels: Optional list of box labels (e.g., ["table", "table", "chair"])
            frame_id: Current frame index (0 = first frame)
            refine_every: Re-segment every N frames (0 = tracking only after initialization)
            box_margin_px: Margin in pixels to expand boxes during refinement
        
        Returns:
            FrameEvent with stable entity IDs from self.state_by_id
        """
        if timestamp_iso is None:
            timestamp_iso = now_iso()
        
        # If no labels provided, prepare to infer them from area (only for frame 0)
        if box_labels is None:
            box_labels = [None] * len(boxes)
        
        from src.vision.detection.furniture_postprocess import mask_to_min_area_rect, mask_to_circle
        
        # === MODE 1: Initialization (frame_id == 0) ===
        if frame_id == 0:
            if self.debug_dir:
                print(f"[Frame {frame_id}] Initialization mode: setting up state from {len(boxes)} boxes")
            
            # Segment all boxes at once
            box_results = self.segmenter.segment_with_boxes(frame_bgr, boxes=boxes)
            
            # Initialize state for each box (max 1 entity per input box)
            overlay_items = []
            for box_idx, box in enumerate(boxes):
                label_hint = box_labels[box_idx] if box_idx < len(box_labels) else None
                entity_id = f"{(label_hint or 'obj')}_{box_idx:02d}"

                # Person: use YOLO bbox directly, no SAM2 postprocessing for now
                if label_hint == "person":
                    x1, y1, x2, y2 = [int(v) for v in box]
                    center_px = [(x1 + x2) / 2.0, (y1 + y2) / 2.0]
                    self.state_by_id[entity_id] = {
                        "label": "person",
                        "bbox_px": [x1, y1, x2, y2],
                        "center_px": center_px,
                        "shape": {"type": "bbox"},
                        "confidence": 1.0,
                    }
                    overlay_items.append({
                        "id": entity_id,
                        "label": "person",
                        "mask": np.zeros(frame_bgr.shape[:2], dtype=np.uint8),
                        "score": 1.0,
                        "shape": {"center_px": center_px, "bbox_px": [x1, y1, x2, y2]},
                    })
                    continue

                result = self._select_best_mask_for_box(box_results, box_idx, box_label=label_hint or "")
                if result is None:
                    continue

                mask = result["mask"]
                area = np.sum(mask)
                label = label_hint
                if label is None:
                    if area >= self.table_min_area:
                        label = "table"
                    elif area >= self.chair_min_area:
                        label = "chair"
                    else:
                        continue

                entity_id = f"{label}_{box_idx:02d}"

                if label == "table":
                    geom_dict = mask_to_min_area_rect(mask)
                    if geom_dict is None:
                        continue
                    try:
                        geom_dict = self._validate_geom_dict(
                            geom_dict,
                            expected_keys=["center_px", "yaw_rad", "corners_px", "area_px", "bbox_px"],
                            geom_type=f"{entity_id}_rect",
                        )
                    except ValueError as e:
                        if self.debug_dir:
                            print(f"[{entity_id}] invalid geometry - {e}")
                        continue

                    self.state_by_id[entity_id] = {
                        "label": label,
                        "bbox_px": geom_dict["bbox_px"],
                        "center_px": geom_dict["center_px"],
                        "shape": {
                            "type": "rect",
                            "corners_px": geom_dict["corners_px"],
                            "yaw_rad": geom_dict["yaw_rad"],
                            "area_px": geom_dict["area_px"],
                        },
                        "confidence": result.get("score", 1.0),
                    }
                    overlay_items.append({
                        "id": entity_id,
                        "label": label,
                        "mask": mask,
                        "score": result.get("score", 1.0),
                        "shape": {
                            "corners_px": geom_dict["corners_px"],
                            "center_px": geom_dict["center_px"],
                            "bbox_px": geom_dict["bbox_px"],
                        },
                    })

                elif label == "chair":
                    geom_dict = mask_to_circle(mask)
                    if geom_dict is None:
                        continue
                    try:
                        geom_dict = self._validate_geom_dict(
                            geom_dict,
                            expected_keys=["center_px", "radius_px", "area_px", "bbox_px"],
                            geom_type=f"{entity_id}_circle",
                        )
                    except ValueError as e:
                        if self.debug_dir:
                            print(f"[{entity_id}] invalid geometry - {e}")
                        continue

                    self.state_by_id[entity_id] = {
                        "label": label,
                        "bbox_px": geom_dict["bbox_px"],
                        "center_px": geom_dict["center_px"],
                        "shape": {
                            "type": "circle",
                            "radius_px": geom_dict["radius_px"],
                            "area_px": geom_dict["area_px"],
                        },
                        "confidence": result.get("score", 1.0),
                    }
                    overlay_items.append({
                        "id": entity_id,
                        "label": label,
                        "mask": mask,
                        "score": result.get("score", 1.0),
                        "shape": {
                            "center_px": geom_dict["center_px"],
                            "radius_px": geom_dict["radius_px"],
                            "bbox_px": geom_dict["bbox_px"],
                        },
                    })

            self._last_overlay_items = overlay_items
            
            if self.debug_dir:
                print(f"[Frame {frame_id}] Initialized {len(self.state_by_id)} entities")
        
        # === MODE 2: Refinement (refine_every > 0 and frame_id % refine_every == 0) ===
        elif refine_every > 0 and frame_id % refine_every == 0:
            if self.debug_dir:
                print(f"[Frame {frame_id}] Refinement mode: expanding boxes by {box_margin_px}px")
            
            # Build refined boxes from state
            refined_boxes = []
            entity_ids_for_refinement = []
            h, w = frame_bgr.shape[:2]
            
            for entity_id, state in self.state_by_id.items():
                bbox = state["bbox_px"]
                x1, y1, x2, y2 = bbox
                
                # Expand by margin
                x1_exp = max(0, x1 - box_margin_px)
                y1_exp = max(0, y1 - box_margin_px)
                x2_exp = min(w - 1, x2 + box_margin_px)
                y2_exp = min(h - 1, y2 + box_margin_px)
                
                refined_boxes.append([x1_exp, y1_exp, x2_exp, y2_exp])
                entity_ids_for_refinement.append(entity_id)
            
            # Segment with refined boxes
            if refined_boxes:
                box_results = self.segmenter.segment_with_boxes(frame_bgr, boxes=refined_boxes)

                overlay_items = []
                for idx, entity_id in enumerate(entity_ids_for_refinement):
                    label = self.state_by_id[entity_id]["label"]

                    if label == "person":
                        x1, y1, x2, y2 = refined_boxes[idx]
                        center_px = [(x1 + x2) / 2.0, (y1 + y2) / 2.0]
                        self.state_by_id[entity_id]["bbox_px"] = [x1, y1, x2, y2]
                        self.state_by_id[entity_id]["center_px"] = center_px
                        self.state_by_id[entity_id]["shape"] = {"type": "bbox"}
                        self.state_by_id[entity_id]["confidence"] = 1.0
                        overlay_items.append({
                            "id": entity_id,
                            "label": label,
                            "mask": np.zeros(frame_bgr.shape[:2], dtype=np.uint8),
                            "score": 1.0,
                            "shape": {"center_px": center_px, "bbox_px": [x1, y1, x2, y2]},
                        })
                        continue

                    result = self._select_best_mask_for_box(box_results, idx, box_label=label)
                    if result is None:
                        if self.debug_dir:
                            print(f"[{entity_id}] Refinement failed, keeping old state")
                        continue

                    mask = result["mask"]

                    if label == "table":
                        geom_dict = mask_to_min_area_rect(mask)
                        if geom_dict is None:
                            continue
                        try:
                            geom_dict = self._validate_geom_dict(
                                geom_dict,
                                expected_keys=["center_px", "yaw_rad", "corners_px", "area_px", "bbox_px"],
                                geom_type=f"{entity_id}_rect",
                            )
                        except ValueError:
                            continue

                        self.state_by_id[entity_id]["bbox_px"] = geom_dict["bbox_px"]
                        self.state_by_id[entity_id]["center_px"] = geom_dict["center_px"]
                        self.state_by_id[entity_id]["shape"] = {
                            "type": "rect",
                            "corners_px": geom_dict["corners_px"],
                            "yaw_rad": geom_dict["yaw_rad"],
                            "area_px": geom_dict["area_px"],
                        }
                        self.state_by_id[entity_id]["confidence"] = result.get("score", 1.0)
                        overlay_items.append({
                            "id": entity_id,
                            "label": label,
                            "mask": mask,
                            "score": result.get("score", 1.0),
                            "shape": {
                                "corners_px": geom_dict["corners_px"],
                                "center_px": geom_dict["center_px"],
                                "bbox_px": geom_dict["bbox_px"],
                            },
                        })

                    elif label == "chair":
                        geom_dict = mask_to_circle(mask)
                        if geom_dict is None:
                            continue
                        try:
                            geom_dict = self._validate_geom_dict(
                                geom_dict,
                                expected_keys=["center_px", "radius_px", "area_px", "bbox_px"],
                                geom_type=f"{entity_id}_circle",
                            )
                        except ValueError:
                            continue

                        self.state_by_id[entity_id]["bbox_px"] = geom_dict["bbox_px"]
                        self.state_by_id[entity_id]["center_px"] = geom_dict["center_px"]
                        self.state_by_id[entity_id]["shape"] = {
                            "type": "circle",
                            "radius_px": geom_dict["radius_px"],
                            "area_px": geom_dict["area_px"],
                        }
                        self.state_by_id[entity_id]["confidence"] = result.get("score", 1.0)
                        overlay_items.append({
                            "id": entity_id,
                            "label": label,
                            "mask": mask,
                            "score": result.get("score", 1.0),
                            "shape": {
                                "center_px": geom_dict["center_px"],
                                "radius_px": geom_dict["radius_px"],
                                "bbox_px": geom_dict["bbox_px"],
                            },
                        })

                self._last_overlay_items = overlay_items
            
            if self.debug_dir:
                print(f"[Frame {frame_id}] Updated {len(overlay_items)} entities")
        
        # === MODE 3: Tracking (keep state as-is) ===
        else:
            # Tracking mode: keep state, no SAM2 call
            # Optional: Apply Kalman prediction here
            if self.debug_dir and frame_id > 0:
                print(f"[Frame {frame_id}] Tracking mode: keeping state")
            pass
        
        # === Generate output from state ===
        furniture_entities = []
        people_entities = []
        for entity_id, state in self.state_by_id.items():
            label = state["label"]
            center_px = state["center_px"]
            shape = state["shape"]
            
            # Project to floor coordinates
            if self.H is not None:
                center_floor = apply_homography(center_px, self.H)
            else:
                center_floor = center_px
            
            # Build entity
            if label == "table":
                yaw_rad = shape.get("yaw_rad", 0.0)
                pose = Pose2D(x=center_floor[0], y=center_floor[1], theta=yaw_rad)
            elif label == "chair":
                pose = Pose2D(x=center_floor[0], y=center_floor[1], theta=None)
            elif label == "person":
                pose = Pose2D(x=center_floor[0], y=center_floor[1], theta=None)
            else:
                continue
            
            entity = DetectedEntity(
                id=entity_id,
                kind=label,
                pose=pose,
                confidence=state.get("confidence", 1.0)
            )
            
            if label == "person":
                people_entities.append(entity)
            else:
                furniture_entities.append(entity)
        
        # Build FrameEvent
        frame_event = FrameEvent(
            timestamp_iso=timestamp_iso,
            frame_id=self.frame_id,
            furniture=furniture_entities,
            people=people_entities,
            world={"homography_applied": self.H is not None, "used_box_prompts": True, "state_tracking": True}
        )
        
        self.frame_id += 1
        return frame_event

    def process_frame_with_proposals(
        self,
        frame_bgr: np.ndarray,
        proposer,
        proposal_mode: str = "bgsub",
        timestamp_iso: Optional[str] = None,
        frame_id: int = 0,
        max_proposals_per_frame: int = 50,
        table_area_threshold: float = 8000.0,
        rectangularity_threshold: float = 0.65,
        max_tracking_distance: float = 150.0,
        debug: bool = False,
    ) -> FrameEvent:
        """
        Process frame with automatic furniture proposals.
        
        Workflow:
        1. BGSubProposer.propose() -> candidate boxes
        2. For each box: SAM2 segment -> best mask -> postprocess (minAreaRect+circle)
        3. Classify: large+rectangular -> table, else -> chair
        4. Track entities frame-to-frame with stable IDs
        
        Args:
            frame_bgr: Input frame in BGR format
            proposer: Proposer instance (BGSubProposer or DarkObjectProposer)
            proposal_mode: Active proposal mode (bgsub or dark)
            timestamp_iso: Optional ISO timestamp
            frame_id: Current frame index (0 = first frame)
            max_proposals_per_frame: Max candidate boxes passed to SAM per frame
            table_area_threshold: Min area for table classification
            rectangularity_threshold: Min ratio mask_area/bbox_area for table
            max_tracking_distance: Max center distance for entity matching
            debug: Enable debug output
            
        Returns:
            FrameEvent with tracked furniture entities
        """
        if timestamp_iso is None:
            timestamp_iso = now_iso()
        
        from src.vision.detection.furniture_postprocess import mask_to_min_area_rect, mask_to_circle
        
        # 1. Get proposals from selected proposer mode
        if proposal_mode == "dark":
            raw_boxes = proposer.propose(frame_bgr=frame_bgr, frame_id=frame_id)
            proposals = [{"bbox_px": box, "score": 1.0} for box in raw_boxes]
        else:
            proposals = proposer.propose(frame_bgr, debug=debug)

        if max_proposals_per_frame > 0:
            proposals = proposals[:max_proposals_per_frame]
        
        if debug:
            print(f"[Frame {frame_id}] {proposal_mode} found {len(proposals)} proposals")
        
        if not proposals:
            # No proposals, return empty event but maintain frame_id
            self._last_overlay_items = []
            frame_event = FrameEvent(
                timestamp_iso=timestamp_iso,
                frame_id=frame_id,
                furniture=[],
                people=[],
                world={"homography_applied": self.H is not None, "auto_proposals": True}
            )
            return frame_event
        
        # 2. Segment all candidate boxes with SAM2
        candidate_boxes = [p["bbox_px"] for p in proposals]
        
        box_results = self.segmenter.segment_with_boxes(frame_bgr, boxes=candidate_boxes)
        
        # 3. Process each mask and classify
        detected_entities = []  # List of dicts with label, center_px, shape, confidence
        
        for box_idx, (proposal, box_result) in enumerate(zip(proposals, box_results)):
            mask = box_result["mask"]
            area = np.sum(mask)
            sam_score = box_result.get("score", 0.0)
            
            # Filter by area
            if area < self.chair_min_area:
                continue
            
            # Calculate rectangularity
            y_coords, x_coords = np.where(mask)
            if len(x_coords) == 0:
                continue
            
            bbox_x1, bbox_y1 = x_coords.min(), y_coords.min()
            bbox_x2, bbox_y2 = x_coords.max(), y_coords.max()
            bbox_area = (bbox_x2 - bbox_x1 + 1) * (bbox_y2 - bbox_y1 + 1)
            rectangularity = area / bbox_area if bbox_area > 0 else 0.0
            
            # Classify as table or chair
            if area >= table_area_threshold and rectangularity >= rectangularity_threshold:
                label = "table"
                geom_dict = mask_to_min_area_rect(mask)
                if geom_dict is None:
                    continue
                
                detected_entities.append({
                    "label": label,
                    "center_px": geom_dict["center_px"],
                    "bbox_px": geom_dict["bbox_px"],
                    "shape": {
                        "type": "rect",
                        "corners_px": geom_dict["corners_px"],
                        "yaw_rad": geom_dict["yaw_rad"],
                        "area_px": geom_dict["area_px"],
                    },
                    "confidence": sam_score,
                    "mask": mask,
                })
            else:
                label = "chair"
                geom_dict = mask_to_circle(mask)
                if geom_dict is None:
                    continue
                
                detected_entities.append({
                    "label": label,
                    "center_px": geom_dict["center_px"],
                    "bbox_px": geom_dict["bbox_px"],
                    "shape": {
                        "type": "circle",
                        "radius_px": geom_dict["radius_px"],
                        "area_px": geom_dict["area_px"],
                    },
                    "confidence": sam_score,
                    "mask": mask,
                })
        
        # 4. Track entities frame-to-frame
        if frame_id == 0:
            # First frame: initialize state
            self.state_by_id = {}
            for idx, entity_data in enumerate(detected_entities):
                entity_id = f"{entity_data['label']}_{idx:02d}"
                self.state_by_id[entity_id] = {
                    "label": entity_data["label"],
                    "center_px": entity_data["center_px"],
                    "bbox_px": entity_data["bbox_px"],
                    "shape": entity_data["shape"],
                    "confidence": entity_data["confidence"],
                    "mask": entity_data.get("mask"),
                }
        else:
            # Match current detections to existing state using center distance
            updated_state = {}
            used_detections = set()
            
            # Match existing entities to new detections
            for entity_id, old_state in self.state_by_id.items():
                old_center = np.array(old_state["center_px"])
                best_match_idx = None
                best_distance = float("inf")
                
                for idx, entity_data in enumerate(detected_entities):
                    if idx in used_detections:
                        continue
                    
                    new_center = np.array(entity_data["center_px"])
                    distance = np.linalg.norm(old_center - new_center)
                    
                    # Must match same label
                    if entity_data["label"] != old_state["label"]:
                        continue
                    
                    if distance < best_distance and distance < max_tracking_distance:
                        best_distance = distance
                        best_match_idx = idx
                
                if best_match_idx is not None:
                    # Update existing entity
                    matched_entity = detected_entities[best_match_idx]
                    updated_state[entity_id] = {
                        "label": matched_entity["label"],
                        "center_px": matched_entity["center_px"],
                        "bbox_px": matched_entity["bbox_px"],
                        "shape": matched_entity["shape"],
                        "confidence": matched_entity["confidence"],
                        "mask": matched_entity.get("mask"),
                    }
                    used_detections.add(best_match_idx)
                # else: entity lost, don't add to updated_state
            
            # Add new entities for unmatched detections
            for idx, entity_data in enumerate(detected_entities):
                if idx not in used_detections:
                    # New entity
                    new_id = f"{entity_data['label']}_{len(updated_state):02d}"
                    updated_state[new_id] = {
                        "label": entity_data["label"],
                        "center_px": entity_data["center_px"],
                        "bbox_px": entity_data["bbox_px"],
                        "shape": entity_data["shape"],
                        "confidence": entity_data["confidence"],
                        "mask": entity_data.get("mask"),
                    }
            
            self.state_by_id = updated_state
        
        # 5. Build entities from state
        furniture_entities = []
        overlay_items = []
        
        for entity_id, state in self.state_by_id.items():
            label = state["label"]
            center_px = state["center_px"]
            shape = state["shape"]
            
            # Project to floor coordinates
            if self.H is not None:
                center_floor = apply_homography(center_px, self.H)
            else:
                center_floor = center_px
            
            # Build entity
            if label == "table":
                yaw_rad = shape.get("yaw_rad", 0.0)
                pose = Pose2D(x=center_floor[0], y=center_floor[1], theta=yaw_rad)
            else:  # chair
                pose = Pose2D(x=center_floor[0], y=center_floor[1], theta=None)
            
            entity = DetectedEntity(
                id=entity_id,
                kind=label,
                pose=pose,
                confidence=state.get("confidence", 1.0)
            )
            furniture_entities.append(entity)
            
            # Store overlay items for visualization
            overlay_items.append({
                "id": entity_id,
                "label": label,
                "mask": state.get("mask", np.zeros(frame_bgr.shape[:2], dtype=bool)),
                "score": state.get("confidence", 1.0),
                "shape": {
                    "center_px": center_px,
                    "bbox_px": state["bbox_px"],
                    **({"corners_px": shape.get("corners_px"), "yaw_rad": shape.get("yaw_rad")} if label == "table" else {}),
                    **({"radius_px": shape.get("radius_px")} if label == "chair" else {}),
                },
            })
        
        self._last_overlay_items = overlay_items
        
        # Build FrameEvent
        frame_event = FrameEvent(
            timestamp_iso=timestamp_iso,
            frame_id=frame_id,
            furniture=furniture_entities,
            people=[],
            world={"homography_applied": self.H is not None, "auto_proposals": True}
        )
        
        return frame_event
    
    def process_image_dir_to_jsonl(
        self,
        image_dir: str,
        output_jsonl: str,
        fps_sim: float = 10.0,
        boxes_init: Optional[List[List[int]]] = None,
        box_labels: Optional[List[str]] = None,
        init_boxes: bool = False,
        overlay_out_dir: Optional[str] = None,
        overlay_every: int = 10,
        debug_dump: bool = False,
        max_frames: Optional[int] = None,
        refine_every: int = 0,
        box_margin_px: int = 0,
        flush_every: int = 10,
    ):
        """
        Process image directory and write FrameEvents to JSONL.
        
        When boxes_init is provided, uses box-based segmentation for all frames with stable IDs.
        When boxes_init is not provided, falls back to text-based prompts (requires implementation).
        
        Args:
            image_dir: Path to directory containing images
            output_jsonl: Path to output JSONL file
            fps_sim: Simulated FPS for timestamp calculation
            boxes_init: Initial boxes for first frame [[x1, y1, x2, y2], ...]
            box_labels: Optional list of labels for each box (e.g., ["table", "table", "chair"])
                       If not provided, labels will be inferred from mask area
            init_boxes: If True, interactively select boxes on first image
            overlay_out_dir: Optional directory to save overlay frames
            overlay_every: Save overlay every N frames (default 10)
            debug_dump: If True, save segmentation masks as individual PNGs in data/vision/debug/masks/
            max_frames: Maximum number of frames to process (None = all)
            refine_every: Re-segmentation interval (0 = use same boxes for all frames, 
                         N > 0 = re-segment every N frames)
            box_margin_px: Margin in pixels to expand boxes during refinement (default 0)
            flush_every: Flush/fsync every N frames (based on frame_id)
        """
        img_dir = Path(image_dir)
        if not img_dir.exists():
            raise RuntimeError(f"Image directory not found: {image_dir}")
        
        # Load all jpg and png files, sorted by name
        image_files = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")))
        
        if len(image_files) == 0:
            raise RuntimeError(f"No .jpg or .png files found in {image_dir}")
        
        print(f"Found {len(image_files)} images in {image_dir}")
        
        output_path = Path(output_jsonl)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create overlay directory if needed
        overlay_path = None
        if overlay_out_dir:
            overlay_path = Path(overlay_out_dir)
            overlay_path.mkdir(parents=True, exist_ok=True)
            print(f"Will save overlays every {overlay_every} frames to {overlay_path}")
        
        # Determine initial boxes for first frame
        first_frame_boxes = None
        if init_boxes:
            # Load first image and select boxes interactively
            first_img = cv2.imread(str(image_files[0]))
            if first_img is None:
                raise RuntimeError(f"Could not load first image: {image_files[0]}")
            first_img = self._apply_input_crop(first_img)
            first_frame_boxes = self._select_boxes_interactive(first_img)
        elif boxes_init is not None:
            first_frame_boxes = boxes_init
        
        # Create debug masks directory if needed
        debug_masks_path = None
        if debug_dump:
            debug_masks_path = Path("data/vision/debug/masks")
            debug_masks_path.mkdir(parents=True, exist_ok=True)
            print(f"Debug mask dump enabled: {debug_masks_path}")
        
        # Initialize tracking structure if using box-based segmentation
        self._active_tracks = None
        if first_frame_boxes:
            self._active_tracks = {
                "first_frame_boxes": first_frame_boxes,
                "box_labels": box_labels if box_labels else [None] * len(first_frame_boxes),
                "detected_objects": [],
                "refine_every": refine_every,
                "box_margin_px": box_margin_px
            }
            print(f"Using box-based segmentation with {len(first_frame_boxes)} boxes")
            if box_labels:
                label_counts = {}
                for label in box_labels:
                    label_counts[label] = label_counts.get(label, 0) + 1
                print(f"  Box labels: {label_counts}")
            if refine_every > 0:
                print(f"  Re-segmenting every {refine_every} frames")
                if box_margin_px > 0:
                    print(f"  Box margin: {box_margin_px}px")
            else:
                print(f"  Using same boxes for all frames")
        else:
            print("No boxes provided; will use text-based prompts for segmentation")
        
        # Process images
        base_time = time.time()
        frame_duration = 1.0 / fps_sim
        
        frame_count = 0
        
        with open(output_path, "w") as f:
            for img_path in image_files:
                if max_frames is not None and frame_count >= max_frames:
                    break
                
                # Load image
                frame = cv2.imread(str(img_path))
                if frame is None:
                    print(f"Warning: Could not load {img_path}, skipping.")
                    continue
                frame = self._apply_input_crop(frame)
                
                # Calculate timestamp
                timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", 
                                             time.gmtime(base_time + frame_count * frame_duration))
                
                # Process frame based on available prompts
                if first_frame_boxes:
                    # Get labels from tracking structure (if available)
                    labels_to_use = None
                    if self._active_tracks is not None:
                        labels_to_use = self._active_tracks.get("box_labels")
                    
                    # Process with boxes and labels (box routing logic is inside process_frame_with_boxes)
                    frame_event = self.process_frame_with_boxes(
                        frame, 
                        first_frame_boxes,  # Only used for frame_id == 0
                        timestamp_iso, 
                        box_labels=labels_to_use,
                        frame_id=frame_count,
                        refine_every=refine_every,
                        box_margin_px=box_margin_px
                    )
                    
                    # Update internal tracking
                    if self._active_tracks is not None:
                        self._active_tracks["detected_objects"] = frame_event.furniture
                else:
                    # No boxes: use text-based prompts (requires process_frame implementation)
                    frame_event = self.process_frame(frame, timestamp_iso)
                
                f.write(json.dumps(frame_event.to_dict()) + "\n")
                if flush_every > 0 and (frame_event.frame_id % flush_every == 0):
                    f.flush()
                    os.fsync(f.fileno())
                
                # Save overlay if requested and at the right interval
                if overlay_path and (frame_count % overlay_every == 0):
                    self._last_render_frame_id = frame_count
                    # Use render_overlay if we have overlay items (box-based mode)
                    if hasattr(self, '_last_overlay_items') and self._last_overlay_items:
                        overlay = self.render_overlay(frame, self._last_overlay_items)
                    else:
                        # Fallback to text-based overlay
                        overlay = self._draw_detections_with_boxes(frame, frame_event)
                    
                    out_name = f"frame_{frame_count:05d}_{img_path.stem}.png"
                    cv2.imwrite(str(overlay_path / out_name), overlay)
                
                # Save debug masks if requested
                if debug_dump and debug_masks_path and hasattr(self, '_last_overlay_items'):
                    for item in self._last_overlay_items:
                        mask = item.get("mask")
                        obj_id = item.get("id", "")
                        
                        if mask is not None and mask.any():
                            # Convert to uint8 (0-255)
                            mask_uint8 = (mask.astype(np.uint8) * 255)
                            
                            # Save as PNG
                            mask_filename = f"frame_{frame_count:04d}_{obj_id}.png"
                            cv2.imwrite(str(debug_masks_path / mask_filename), mask_uint8)
                
                # Save debug overlay if requested (legacy)
                if self.debug_dir:
                    debug_path = Path(self.debug_dir)
                    debug_path.mkdir(parents=True, exist_ok=True)
                    
                    # Draw detections on frame
                    overlay = frame.copy()
                    for i, entity in enumerate(frame_event.furniture):
                        # For now, just add text
                        cv2.putText(overlay, f"{entity.kind} {entity.id}", (20, 40 + 30 * i),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    out_name = f"frame_{frame_count:05d}_{img_path.stem}.png"
                    cv2.imwrite(str(debug_path / out_name), overlay)
                
                frame_count += 1
                
                if frame_count % 10 == 0:
                    print(f"Processed {frame_count}/{len(image_files)} images...")
        
        print(f"Wrote {frame_count} FrameEvents to {output_path}")
        if overlay_path:
            overlay_count = (frame_count + overlay_every - 1) // overlay_every
            print(f"Saved {overlay_count} overlay frames to {overlay_path}")

    def _refine_tables_with_sam(self, frame_bgr: np.ndarray, frame_id: int) -> None:
        """
        Run SAM2.1 box-prompt refinement on active table tracks.

        For each stable candidate table track (up to table_refine_max, sorted by bbox area desc):
          - Expand YOLO bbox by table_refine_margin, call SAM with box prompt
          - Find largest mask contour, compute minAreaRect -> corners + theta
          - EMA-smooth theta with previous, store in track state
        """
        table_tracks = self._tracks.get("table", {})
        if not table_tracks:
            return

        h, w = frame_bgr.shape[:2]

        # Select stable candidates active this frame, sorted by bbox area descending
        candidates = []
        for tid, track in table_tracks.items():
            if track.get("last_seen") != frame_id:
                continue
            if str(track.get("table_motion_state", "moving")) != "stable":
                continue
            bbox = track.get("bbox", [0, 0, 0, 0])
            area = self._bbox_area(bbox)
            candidates.append((tid, bbox, area))

        if not candidates:
            return

        candidates.sort(key=lambda x: x[2], reverse=True)
        candidates = candidates[: self.table_refine_max]

        margin = self.table_refine_margin
        boxes_for_sam = []
        for tid, bbox, _ in candidates:
            x1, y1, x2, y2 = [int(v) for v in bbox]
            boxes_for_sam.append([
                max(0, x1 - margin),
                max(0, y1 - margin),
                min(w, x2 + margin),
                min(h, y2 + margin),
            ])

        try:
            results = self.segmenter.segment_with_boxes(frame_bgr, boxes=boxes_for_sam)
        except Exception as exc:
            print(f"[TableRefine][frame {frame_id}] SAM call failed: {exc}")
            for tid, _, _ in candidates:
                track = table_tracks.get(tid)
                if track is None:
                    continue
                track["last_corners_px"] = None
                track["last_refined_frame"] = frame_id
                track["last_refine_failed"] = True
            return

        debug_path = Path(self.debug_dir) if self.debug_dir else None
        if debug_path is not None:
            debug_path.mkdir(parents=True, exist_ok=True)

        for i, (tid, bbox, _) in enumerate(candidates):
            res = results[i] if i < len(results) else None
            track = table_tracks[tid]
            prev_theta = track.get("last_theta") if track.get("last_theta") is not None else track.get("prev_theta")

            def _mark_refine_failed(reason: str) -> None:
                track["last_corners_px"] = None
                track["last_refined_frame"] = frame_id
                track["last_refine_failed"] = True
                if self.debug_dir:
                    print(f"[TableRefine][frame {frame_id}] id={tid} {reason} (fallback_yolo)")

            if res is None:
                _mark_refine_failed("no result")
                continue

            mask = res.get("mask")
            sam_score = float(res.get("score", 0.0))

            if mask is None or not mask.any():
                _mark_refine_failed(f"empty mask sam_score={sam_score:.3f}")
                continue

            mask_u8 = mask.astype(np.uint8) * 255

            # --- mask cleaning: erode to detach thin protrusions, keep largest CC, light re-dilation ---
            px_raw = int(np.count_nonzero(mask_u8))
            _clean_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            mask_eroded = cv2.erode(mask_u8, _clean_kernel, iterations=2)
            # keep only the largest connected component
            _n_labels, _labels, _stats, _ = cv2.connectedComponentsWithStats(mask_eroded, connectivity=8)
            if _n_labels > 1:
                # label 0 = background; find largest foreground label
                _fg_sizes = _stats[1:, cv2.CC_STAT_AREA]
                _best_label = int(np.argmax(_fg_sizes)) + 1
                mask_clean = np.where(_labels == _best_label, np.uint8(255), np.uint8(0))
            else:
                mask_clean = mask_eroded
            # light re-dilation to partially restore original size after erosion
            mask_clean = cv2.dilate(mask_clean, _clean_kernel, iterations=1)
            px_clean = int(np.count_nonzero(mask_clean))
            if px_raw > 0 and (px_raw - px_clean) / px_raw > 0.10:
                print(
                    f"[TableRefine][frame {frame_id}] id={tid} "
                    f"mask cleaned: {px_raw}px -> {px_clean}px "
                    f"(-{100.0*(px_raw-px_clean)/px_raw:.1f}%)"
                )

            if debug_path is not None:
                cv2.imwrite(str(debug_path / f"table_f{frame_id:05d}_{tid}_mask_raw.png"), mask_u8)
                cv2.imwrite(str(debug_path / f"table_f{frame_id:05d}_{tid}_mask_clean.png"), mask_clean)
                _vis_contours = cv2.cvtColor(mask_clean, cv2.COLOR_GRAY2BGR)
                _dbg_contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(_vis_contours, _dbg_contours, -1, (0, 255, 0), 2)
                cv2.imwrite(str(debug_path / f"table_f{frame_id:05d}_{tid}_contours_clean.png"), _vis_contours)

            contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                _mark_refine_failed("no contours after cleaning")
                continue

            best_contour = max(contours, key=cv2.contourArea)
            contour_area = float(cv2.contourArea(best_contour))
            if contour_area < 1000.0:
                _mark_refine_failed(f"contour_area={contour_area:.0f} too small")
                continue

            rect = cv2.minAreaRect(best_contour)
            rect_center, rect_size, rect_angle_deg = rect
            rw, rh = rect_size

            # Derive long-edge theta; OpenCV rect angle is for the width side
            if rw < rh:
                angle_deg = rect_angle_deg + 90.0
            else:
                angle_deg = float(rect_angle_deg)

            theta_new = float(angle_deg * np.pi / 180.0)
            while theta_new <= -0.5 * np.pi:
                theta_new += np.pi
            while theta_new > 0.5 * np.pi:
                theta_new -= np.pi

            # EMA smoothing with previous theta (smallest-angle-diff)
            if prev_theta is not None:
                diff = theta_new - float(prev_theta)
                while diff <= -0.5 * np.pi:
                    diff += np.pi
                while diff > 0.5 * np.pi:
                    diff -= np.pi
                theta_used = float(prev_theta) + 0.2 * diff
                while theta_used <= -0.5 * np.pi:
                    theta_used += np.pi
                while theta_used > 0.5 * np.pi:
                    theta_used -= np.pi
            else:
                theta_used = theta_new

            corners_float = cv2.boxPoints(rect)
            corners_int = np.round(corners_float).astype(np.int32)

            track["last_corners_px"] = corners_int
            track["last_theta"] = theta_used
            track["last_refined_frame"] = frame_id
            track["last_bbox_px"] = [int(v) for v in bbox]
            track["last_refine_failed"] = False

            print(
                f"[TableRefine][frame {frame_id}] id={tid} "
                f"bbox_area={self._bbox_area(bbox):.0f} "
                f"sam_score={sam_score:.3f} "
                f"contour_area={contour_area:.0f} "
                f"theta_new={float(np.degrees(theta_new)):.2f}deg "
                f"theta_used={float(np.degrees(theta_used)):.2f}deg ok"
            )

            if debug_path is not None:
                # mask_raw/mask_clean/contours_clean already saved above; here save the minAreaRect viz
                x1, y1, x2, y2 = [int(v) for v in bbox]
                rx1 = max(0, x1 - margin)
                ry1 = max(0, y1 - margin)
                rx2 = min(w, x2 + margin)
                ry2 = min(h, y2 + margin)
                roi_vis = frame_bgr[ry1:ry2, rx1:rx2].copy()
                mask_roi = mask_clean[ry1:ry2, rx1:rx2]
                if mask_roi.shape[:2] == roi_vis.shape[:2]:
                    mask_color = np.zeros_like(roi_vis)
                    mask_color[:, :, 1] = mask_roi
                    roi_vis = cv2.addWeighted(roi_vis, 0.7, mask_color, 0.3, 0.0)
                corners_roi = corners_int.copy()
                corners_roi[:, 0] -= rx1
                corners_roi[:, 1] -= ry1
                cv2.drawContours(roi_vis, [corners_roi.reshape(-1, 1, 2)], 0, (0, 255, 0), 2)
                cv2.imwrite(str(debug_path / f"table_minarearect_f{frame_id:05d}_{tid}.png"), roi_vis)

    def _process_frame_yolo(
        self,
        frame_bgr: np.ndarray,
        frame_id: int,
        timestamp_iso: str,
    ) -> FrameEvent:
        """
        Process a single frame using YOLO detections directly (no SAM2).

        Uses greedy nearest-center matching per class with extra IoU/area gates,
        class-specific confidence filtering, and EMA bbox smoothing for stability.
        """
        from collections import Counter, defaultdict, deque

        raw_detections = self._yolo_detector.detect(frame_bgr)
        raw_table_obb_detections: List[Dict] = []
        if self._table_obb_detector is not None:
            table_obb_detections = self._table_obb_detector.detect_tables(frame_bgr)
            raw_table_obb_detections = list(table_obb_detections)
            raw_detections = [det for det in raw_detections if det.get("label") != "table"]
            raw_detections.extend(table_obb_detections)
        frame_h, frame_w = frame_bgr.shape[:2]
        frame_area = float(frame_w * frame_h) if frame_w > 0 and frame_h > 0 else 1.0
        raw_table_dets = sum(1 for det in raw_detections if det.get("label") == "table")
        rejected_small_table_dets = 0
        rejected_geom_person_dets = 0
        min_table_area_px = float(self.table_min_bbox_area)
        min_table_dim_px = self.table_min_bbox_minside
        use_min_table_dim_filter = True
        rejected_table_overlay_items: List[Dict] = []

        # Group by label and apply class-specific confidence filtering
        by_label: Dict[str, List[Dict]] = defaultdict(list)
        for det in raw_detections:
            label = det.get("label")
            if label not in ("chair", "table", "person"):
                continue
            score = float(det.get("score", 0.0))
            if self.no_ghosting:
                conf_thresh = float(self.conf_create)
            else:
                conf_thresh = float(self.conf_create) if (label == "chair" and self.chairs_no_ghost) else float(self._yolo_conf_min[label])
            if label == "person" and self.person_conf_override is not None:
                conf_thresh = max(conf_thresh, float(self.person_conf_override))
            if score < conf_thresh:
                continue

            if label == "person" and self.person_filter_mode in ("geom", "geom+static"):
                bbox = det.get("bbox_px", [0, 0, 0, 0])
                if len(bbox) != 4:
                    rejected_geom_person_dets += 1
                    continue
                x1, y1, x2, y2 = [int(v) for v in bbox]
                bw = max(0, x2 - x1)
                bh = max(0, y2 - y1)
                area = float(bw * bh)
                if bw <= 0 or bh <= 0:
                    rejected_geom_person_dets += 1
                    continue
                cx_det = 0.5 * float(x1 + x2)
                cy_det = 0.5 * float(y1 + y2)
                ar = max(float(bw) / float(max(1, bh)), float(bh) / float(max(1, bw)))
                ar_wh = float(bw) / float(max(1, bh))

                # Exclusion zones (right strip and right-bottom box) are person-only.
                in_right_strip = False
                if self.person_excl_right_frac > 0.0:
                    right_strip_x = float(frame_w) * (1.0 - float(self.person_excl_right_frac))
                    in_right_strip = cx_det >= right_strip_x

                in_right_bottom_zone = False
                if self.person_excl_rb_right_frac > 0.0 and self.person_excl_rb_bottom_frac > 0.0:
                    rb_x = float(frame_w) * (1.0 - float(self.person_excl_rb_right_frac))
                    rb_y = float(frame_h) * (1.0 - float(self.person_excl_rb_bottom_frac))
                    in_right_bottom_zone = (cx_det >= rb_x) and (cy_det >= rb_y)

                if (
                    area < float(self.person_min_area)
                    or area > float(self.person_max_area)
                    or bh < int(self.person_min_height)
                    or ar > float(self.person_max_ar)
                    or ar_wh < float(self.person_min_ar_wh)
                    or ar_wh > float(self.person_max_ar_wh)
                    or in_right_strip
                    or in_right_bottom_zone
                ):
                    rejected_geom_person_dets += 1
                    if self.debug_dir:
                        print(
                            f"[PersonFilter] drop geom area={area:.1f} h={bh} ar_sym={ar:.2f} ar_wh={ar_wh:.2f} "
                            f"right={in_right_strip} rb={in_right_bottom_zone}"
                        )
                    continue

            # Size-based table filter to avoid chair-sized false positives.
            if label == "table":
                bbox = det.get("bbox_px", [0, 0, 0, 0])
                if len(bbox) != 4:
                    rejected_small_table_dets += 1
                    continue
                x1, y1, x2, y2 = [int(v) for v in bbox]
                bw = max(0, x2 - x1)
                bh = max(0, y2 - y1)
                bbox_area = float(bw * bh)

                too_small_area = bbox_area < (self.table_min_area_frac * frame_area)
                too_small_w = self.table_min_w_frac > 0 and bw < (self.table_min_w_frac * frame_w)
                too_small_h = self.table_min_h_frac > 0 and bh < (self.table_min_h_frac * frame_h)
                too_small_abs = bbox_area < min_table_area_px
                too_small_dim = use_min_table_dim_filter and min(bw, bh) < min_table_dim_px

                reject_reason = ""
                if too_small_dim:
                    reject_reason = "table_reject_dims"
                elif too_small_abs or too_small_area or too_small_w or too_small_h:
                    reject_reason = "table_reject_small"

                if reject_reason:
                    rejected_small_table_dets += 1
                    if self.debug_dir:
                        rejected_table_overlay_items.append({
                            "id": f"table_reject_{rejected_small_table_dets:03d}",
                            "label": "table_reject",
                            "mask": None,
                            "score": score,
                            "shape": {
                                "bbox_px": [x1, y1, x2, y2],
                                "reject_reason": reject_reason,
                            },
                        })
                    continue

            by_label[label].append(det)

        # Keep top-k by confidence per class
        per_class_cap = int(self._yolo_max_det)
        for lbl in by_label:
            ranked = sorted(by_label[lbl], key=lambda d: d["score"], reverse=True)
            by_label[lbl] = ranked if per_class_cap <= 0 else ranked[:per_class_cap]

        kept_counts = {label: len(by_label.get(label, [])) for label in ("chair", "table", "person")}
        kept_table_dets = kept_counts["table"]
        dbg_raw_table_obb_count = len(raw_table_obb_detections)
        dbg_matched_active_table_tracks = 0
        dbg_matched_lost_table_tracks = 0
        dbg_new_table_tracks_created = 0
        dbg_recoverable_lost_table_track_count = 0
        dbg_blocked_new_table_births_near_lost = 0

        furniture_entities: List[DetectedEntity] = []
        people_entities: List[DetectedEntity] = []
        overlay_items: List[Dict] = []
        theta_gate_rad = float(np.deg2rad(20.0))

        def _normalize_theta_half_pi(theta_rad: float) -> float:
            theta = float(theta_rad)
            while theta <= -0.5 * np.pi:
                theta += np.pi
            while theta > 0.5 * np.pi:
                theta -= np.pi
            return theta

        def _smallest_theta_diff(theta_a: float, theta_b: float) -> float:
            diff = float(theta_a - theta_b)
            while diff <= -0.5 * np.pi:
                diff += np.pi
            while diff > 0.5 * np.pi:
                diff -= np.pi
            return diff

        def _table_shape_area_px(bbox_px: List[int], poly_px: Optional[List]) -> float:
            if poly_px is not None and len(poly_px) == 4:
                try:
                    _pts = np.asarray(poly_px, dtype=np.float32)
                    _area = float(abs(cv2.contourArea(_pts)))
                    if _area > 0.0:
                        return _area
                except Exception:
                    pass
            _bw = max(1, int(bbox_px[2]) - int(bbox_px[0]))
            _bh = max(1, int(bbox_px[3]) - int(bbox_px[1]))
            return float(_bw * _bh)

        for label in ("chair", "table", "person"):
            class_tracks = self._tracks[label]
            alpha_new = float(self._bbox_ema_alpha[label])
            if self.no_ghosting:
                ttl_frames = 0
                reacquire_max_age_label = 0
            elif label == "chair" and self.chairs_no_ghost:
                ttl_frames = 0
                reacquire_max_age_label = 0
            else:
                ttl_frames = int(self._track_ttl_frames_by_class.get(label, self._track_ttl_frames))
                reacquire_max_age_label = int(self._class_reacquire_max_age.get(label, self.reacquire_max_age))

            # Table continuity/recovery can override lost-track TTL without affecting other classes.
            if label == "table" and self.table_recover_lost_tracks and not self.no_ghosting:
                reacquire_max_age_label = int(self.table_lost_track_ttl)

            # Detections are already filtered with conf_keep and class rules above.
            detections = sorted(by_label.get(label, []), key=lambda d: float(d["score"]), reverse=True)
            available_det_idxs = set(range(len(detections)))

            active_track_ids = [tid for tid, t in class_tracks.items() if int(t.get("miss_count", 0)) == 0]
            ghost_track_ids = [
                tid
                for tid, t in class_tracks.items()
                if 0 < int(t.get("miss_count", 0)) <= reacquire_max_age_label
            ]
            if label == "table":
                dbg_recoverable_lost_table_track_count = len(ghost_track_ids)

            # Phase 1: active tracks
            matches = self._greedy_track_match(detections, class_tracks, active_track_ids, available_det_idxs, label)
            if label == "table":
                dbg_matched_active_table_tracks += len(matches)
            for _tid, _didx in matches.items():
                available_det_idxs.discard(_didx)

            # Phase 2: recently missed ghost tracks (ID reacquire)
            if not self.no_ghosting and reacquire_max_age_label > 0:
                reacquire_matches = self._greedy_track_match(detections, class_tracks, ghost_track_ids, available_det_idxs, label)
                if label == "table":
                    dbg_matched_lost_table_tracks += len(reacquire_matches)
                for _tid, _didx in reacquire_matches.items():
                    available_det_idxs.discard(_didx)
                matches.update(reacquire_matches)

            # Update matched tracks
            matched_track_ids = set(matches.keys())
            for track_id, det_idx in matches.items():
                det = detections[det_idx]
                bbox = [int(v) for v in det["bbox_px"]]
                score = float(det["score"])
                old_track = class_tracks[track_id]
                old_bbox = old_track.get("bbox", bbox)
                old_center = old_track.get("center", self._bbox_center(old_bbox))
                old_center_smoothed = old_track.get("center_smoothed", old_center)

                updated_bbox = self._ema_bbox(old_bbox, bbox, alpha_new)
                ucx, ucy = self._bbox_center(updated_bbox)
                det_center = self._bbox_center(bbox)
                center_smoothed = (
                    (1.0 - self._center_smooth_alpha) * float(old_center_smoothed[0]) + self._center_smooth_alpha * float(det_center[0]),
                    (1.0 - self._center_smooth_alpha) * float(old_center_smoothed[1]) + self._center_smooth_alpha * float(det_center[1]),
                )

                class_tracks[track_id]["bbox"] = updated_bbox
                class_tracks[track_id]["center"] = (ucx, ucy)
                class_tracks[track_id]["center_smoothed"] = center_smoothed
                class_tracks[track_id]["score"] = score
                class_tracks[track_id]["last_seen"] = frame_id
                class_tracks[track_id]["last_seen_frame"] = frame_id
                class_tracks[track_id]["miss_count"] = 0
                class_tracks[track_id]["age"] = int(class_tracks[track_id].get("age", 0)) + 1
                class_tracks[track_id]["kind"] = label
                class_tracks[track_id]["id"] = track_id
                if label == "table":
                    self._update_table_motion_state(class_tracks[track_id], old_bbox, bbox)
                    class_tracks[track_id]["obb_poly_px"] = det.get("obb_poly_px")
                    class_tracks[track_id]["obb_center_px"] = det.get("obb_center_px")
                    class_tracks[track_id]["obb_yaw_rad"] = det.get("obb_yaw_rad")
                    _confirm_count = int(class_tracks[track_id].get("table_confirm_count", 1))
                    _confirm_count += 1
                    class_tracks[track_id]["table_confirm_count"] = _confirm_count
                    if _confirm_count >= self.table_new_confirm_frames:
                        class_tracks[track_id]["table_confirmed"] = True
                if label == "person":
                    _hist = class_tracks[track_id].get("person_center_hist")
                    if _hist is None:
                        _hist = deque(maxlen=max(1, int(self.person_static_window)))
                    _hist.append((float(center_smoothed[0]), float(center_smoothed[1])))
                    class_tracks[track_id]["person_center_hist"] = _hist

            # Unmatched tracks become ghosts or expire
            stale_ids = []
            for tid, track in class_tracks.items():
                if tid in matched_track_ids:
                    continue
                if self.no_ghosting:
                    stale_ids.append(tid)
                    continue
                miss_count = int(track.get("miss_count", 0)) + 1
                track["miss_count"] = miss_count
                track["age"] = int(track.get("age", 0)) + 1
                if label == "table" and not bool(track.get("table_confirmed", True)) and miss_count > 0:
                    stale_ids.append(tid)
                    continue
                if miss_count > ttl_frames:
                    stale_ids.append(tid)
            for tid in stale_ids:
                del class_tracks[tid]

            # New track creation from unmatched detections uses conf_create.
            for det_idx in sorted(list(available_det_idxs)):
                det = detections[det_idx]
                score = float(det["score"])
                bbox = [int(v) for v in det["bbox_px"]]
                ucx, ucy = self._bbox_center(bbox)

                if label == "table":
                    # Continuity-first mode: do not spawn a new table while recoverable lost IDs still exist.
                    if self.table_protect_existing_tracks and dbg_recoverable_lost_table_track_count > 0:
                        continue

                    # Optional: suppress new table births close to recoverable lost table tracks.
                    if self.table_recover_lost_tracks and self.table_birth_block_near_lost_dist > 0.0:
                        suppress_near_lost = False
                        for _lost_id in ghost_track_ids:
                            _lost_track = class_tracks.get(_lost_id)
                            if not _lost_track:
                                continue
                            _lost_miss_count = int(_lost_track.get("miss_count", 0))
                            if _lost_miss_count <= 0 or _lost_miss_count > int(reacquire_max_age_label):
                                continue
                            if self.table_birth_block_near_lost_frames > 0 and _lost_miss_count > int(self.table_birth_block_near_lost_frames):
                                continue
                            _lost_bbox = [int(v) for v in _lost_track.get("bbox", [0, 0, 0, 0])]
                            _lost_center = self._bbox_center(_lost_bbox)
                            _lost_dist = self._center_dist((float(ucx), float(ucy)), _lost_center)
                            if _lost_dist <= float(self.table_birth_block_near_lost_dist):
                                suppress_near_lost = True
                                break
                        if suppress_near_lost:
                            dbg_blocked_new_table_births_near_lost += 1
                            continue

                    if score < float(self.table_new_conf_create):
                        continue
                    bw = max(0, bbox[2] - bbox[0])
                    bh = max(0, bbox[3] - bbox[1])
                    if float(bw * bh) < float(self.table_new_min_bbox_area):
                        continue
                    if min(bw, bh) < int(self.table_new_min_bbox_minside):
                        continue

                    suppress_new_table = False
                    for _existing_id, _existing in class_tracks.items():
                        if int(_existing.get("miss_count", 0)) > 0:
                            continue
                        if not bool(_existing.get("table_confirmed", True)):
                            continue
                        _existing_bbox = [int(v) for v in _existing.get("bbox", [0, 0, 0, 0])]

                        if self.table_new_suppress_iou > 0.0:
                            _iou = self._bbox_iou(bbox, _existing_bbox)
                            if _iou >= float(self.table_new_suppress_iou):
                                suppress_new_table = True
                                break

                        if self.table_new_suppress_center_dist_px > 0.0:
                            _existing_center = self._bbox_center(_existing_bbox)
                            _dist = self._center_dist((float(ucx), float(ucy)), _existing_center)
                            if _dist <= float(self.table_new_suppress_center_dist_px):
                                suppress_new_table = True
                                break

                    if suppress_new_table:
                        continue
                else:
                    if score < float(self.conf_create):
                        continue

                track_id = f"{label}_{self._next_id[label]:02d}"
                self._next_id[label] += 1
                class_tracks[track_id] = {
                    "id": track_id,
                    "kind": label,
                    "bbox": bbox,
                    "center": (ucx, ucy),
                    "center_smoothed": (ucx, ucy),
                    "score": score,
                    "last_seen": frame_id,
                    "last_seen_frame": frame_id,
                    "miss_count": 0,
                    "age": 1,
                    "prev_theta": class_tracks.get(track_id, {}).get("prev_theta"),
                }
                if label == "table":
                    class_tracks[track_id]["table_motion_state"] = "moving"
                    class_tracks[track_id]["table_stable_count"] = 0
                    class_tracks[track_id]["table_center_shift_px"] = 0.0
                    class_tracks[track_id]["table_prev_iou"] = 1.0
                    class_tracks[track_id]["table_area_change"] = 0.0
                    class_tracks[track_id]["obb_poly_px"] = det.get("obb_poly_px")
                    class_tracks[track_id]["obb_center_px"] = det.get("obb_center_px")
                    class_tracks[track_id]["obb_yaw_rad"] = det.get("obb_yaw_rad")
                    class_tracks[track_id]["table_confirm_count"] = 1
                    class_tracks[track_id]["table_confirmed"] = self.table_new_confirm_frames <= 1
                    dbg_new_table_tracks_created += 1
                if label == "person":
                    _hist = deque(maxlen=max(1, int(self.person_static_window)))
                    _hist.append((float(ucx), float(ucy)))
                    class_tracks[track_id]["person_center_hist"] = _hist
                if label == "person":
                    self._person_new_ids_since_log += 1

            # Build outputs for both active and ghost tracks.
            for track_id, track in class_tracks.items():
                updated_bbox = [int(v) for v in track.get("bbox", [0, 0, 0, 0])]
                center_smoothed = track.get("center_smoothed", self._bbox_center(updated_bbox))
                prev_theta_track = track.get("prev_theta")
                _miss_count = int(track.get("miss_count", 0))
                is_ghost = _miss_count > 0
                score = float(track.get("score", 0.0))

                # Keep ghost tracks only internally for short-term re-association.
                if is_ghost and not self._emit_ghost_overlays:
                    if (
                        label == "table"
                        and self.table_render_grace_frames > 0
                        and bool(track.get("table_confirmed", True))
                        and _miss_count <= int(self.table_render_grace_frames)
                    ):
                        # Table-only visual grace: reuse last final geometry directly for very short drop-outs.
                        _last_geom = track.get("table_last_final_render_geom")
                        _last_frame = int(track.get("table_last_final_render_frame_id", -1))
                        _grace_age = frame_id - _last_frame if _last_frame >= 0 else None
                        if (
                            isinstance(_last_geom, dict)
                            and _grace_age is not None
                            and 0 <= int(_grace_age) <= int(self.table_render_grace_frames)
                        ):
                            _grace_bbox = [int(v) for v in _last_geom.get("bbox_px", updated_bbox)]
                            _grace_center_raw = _last_geom.get(
                                "center_px",
                                [float(center_smoothed[0]), float(center_smoothed[1])],
                            )
                            _grace_center = (float(_grace_center_raw[0]), float(_grace_center_raw[1]))
                            _grace_yaw_raw = _last_geom.get("yaw_rad")
                            _grace_yaw = None if _grace_yaw_raw is None else float(_grace_yaw_raw)
                            _grace_poly = _last_geom.get("poly_px")
                            _grace_rect_angle = _last_geom.get("rect_angle")
                            if _grace_rect_angle is None and _grace_yaw is not None:
                                _grace_rect_angle = float(np.degrees(_grace_yaw))

                            if self.H is not None:
                                _cx_f, _cy_f = apply_homography([_grace_center[0], _grace_center[1]], self.H)
                            else:
                                _cx_f, _cy_f = _grace_center

                            furniture_entities.append(
                                DetectedEntity(
                                    id=track_id,
                                    kind="table",
                                    pose=Pose2D(
                                        x=float(_cx_f),
                                        y=float(_cy_f),
                                        theta=_grace_yaw,
                                    ),
                                    confidence=score,
                                )
                            )
                            overlay_items.append({
                                "id": track_id,
                                "label": "table",
                                "mask": None,
                                "score": score,
                                "ghost": False,
                                "shape": {
                                    "bbox_px": _grace_bbox,
                                    "center_px": [float(_grace_center[0]), float(_grace_center[1])],
                                    "poly_px": None if _grace_poly is None else [list(p) for p in _grace_poly],
                                    "used_fallback": False,
                                    "fallback_reason": "render_grace",
                                    "motion_state": str(track.get("table_motion_state", "moving")),
                                    "n_contours": 0,
                                    "best_area": 0.0,
                                    "rect_w": float(max(1, _grace_bbox[2] - _grace_bbox[0])),
                                    "rect_h": float(max(1, _grace_bbox[3] - _grace_bbox[1])),
                                    "rect_angle": _grace_rect_angle,
                                    "yaw_rad": _grace_yaw,
                                    "theta_rejected": False,
                                    "roi_mask": None,
                                },
                            })
                    continue
                if label == "table" and not bool(track.get("table_confirmed", True)):
                    continue

                table_shape_extras: Dict = {}
                table_yaw_rad = None
                if label == "table":
                    poly = None
                    theta_rejected = False
                    table_motion_state = str(track.get("table_motion_state", "moving"))
                    table_obb_poly = track.get("obb_poly_px")
                    if not is_ghost:
                        if table_obb_poly is not None and len(table_obb_poly) == 4:
                            poly = np.asarray(table_obb_poly, dtype=np.int32)
                            raw_theta = track.get("obb_yaw_rad")
                            if raw_theta is not None:
                                theta_now = _normalize_theta_half_pi(float(raw_theta))
                                if prev_theta_track is None:
                                    table_yaw_rad = theta_now
                                else:
                                    prev_theta_norm = _normalize_theta_half_pi(float(prev_theta_track))
                                    d_theta = _smallest_theta_diff(theta_now, prev_theta_norm)
                                    if abs(d_theta) > theta_gate_rad:
                                        table_yaw_rad = prev_theta_norm
                                        theta_rejected = True
                                    else:
                                        table_yaw_rad = _normalize_theta_half_pi((0.8 * prev_theta_norm) + (0.2 * theta_now))
                            elif prev_theta_track is not None:
                                table_yaw_rad = _normalize_theta_half_pi(float(prev_theta_track))

                            table_shape_extras = {
                                "poly_px": poly.tolist(),
                                "used_fallback": False,
                                "fallback_reason": "table_obb",
                                "motion_state": table_motion_state,
                                "n_contours": 0,
                                "best_area": 0.0,
                                "rect_w": float(max(1, updated_bbox[2] - updated_bbox[0])),
                                "rect_h": float(max(1, updated_bbox[3] - updated_bbox[1])),
                                "rect_angle": float(np.degrees(table_yaw_rad)) if table_yaw_rad is not None else 0.0,
                                "yaw_rad": float(table_yaw_rad) if table_yaw_rad is not None else None,
                                "theta_rejected": bool(theta_rejected),
                                "roi_mask": None,
                            }
                        else:
                            orient_dbg = self._extract_table_orientation_debug(frame_bgr, updated_bbox, frame_id=frame_id, track_id=track_id)
                            poly = orient_dbg.get("poly")
                            raw_theta = orient_dbg.get("yaw_rad")
                            if raw_theta is not None:
                                theta_now = _normalize_theta_half_pi(float(raw_theta))
                                if prev_theta_track is None:
                                    table_yaw_rad = theta_now
                                else:
                                    prev_theta_norm = _normalize_theta_half_pi(float(prev_theta_track))
                                    d_theta = _smallest_theta_diff(theta_now, prev_theta_norm)
                                    if abs(d_theta) > theta_gate_rad:
                                        table_yaw_rad = prev_theta_norm
                                        theta_rejected = True
                                    else:
                                        table_yaw_rad = _normalize_theta_half_pi((0.8 * prev_theta_norm) + (0.2 * theta_now))
                            elif prev_theta_track is not None:
                                table_yaw_rad = _normalize_theta_half_pi(float(prev_theta_track))

                            if table_yaw_rad is not None:
                                bx1, by1, bx2, by2 = [float(v) for v in updated_bbox]
                                bw = max(1.0, bx2 - bx1)
                                bh = max(1.0, by2 - by1)
                                bcx = 0.5 * (bx1 + bx2)
                                bcy = 0.5 * (by1 + by2)
                                gated_rect = ((bcx, bcy), (bw, bh), float(np.degrees(table_yaw_rad)))
                                poly = np.round(cv2.boxPoints(gated_rect)).astype(np.int32)

                            table_shape_extras = {
                                "poly_px": poly.tolist() if poly is not None else None,
                                "used_fallback": poly is None,
                                "fallback_reason": "" if poly is not None else "no_orientation",
                                "motion_state": table_motion_state,
                                "n_contours": int(orient_dbg.get("n_contours", 0)),
                                "best_area": float(orient_dbg.get("best_area", 0.0)),
                                "rect_w": float(orient_dbg.get("rect_w", 0.0)),
                                "rect_h": float(orient_dbg.get("rect_h", 0.0)),
                                "rect_angle": float(np.degrees(table_yaw_rad)) if table_yaw_rad is not None else float(orient_dbg.get("rect_angle", 0.0)),
                                "yaw_rad": float(table_yaw_rad) if table_yaw_rad is not None else None,
                                "theta_rejected": bool(theta_rejected),
                                "roi_mask": orient_dbg.get("mask"),
                            }
                    else:
                        if prev_theta_track is not None:
                            table_yaw_rad = _normalize_theta_half_pi(float(prev_theta_track))
                            bx1, by1, bx2, by2 = [float(v) for v in updated_bbox]
                            bw = max(1.0, bx2 - bx1)
                            bh = max(1.0, by2 - by1)
                            bcx = 0.5 * (bx1 + bx2)
                            bcy = 0.5 * (by1 + by2)
                            gated_rect = ((bcx, bcy), (bw, bh), float(np.degrees(table_yaw_rad)))
                            poly = np.round(cv2.boxPoints(gated_rect)).astype(np.int32)
                        else:
                            poly = None
                        table_shape_extras = {
                            "poly_px": poly.tolist() if poly is not None else None,
                            "used_fallback": poly is None,
                            "fallback_reason": "ghost_hold",
                            "motion_state": table_motion_state,
                            "n_contours": 0,
                            "best_area": 0.0,
                            "rect_w": float(max(1, updated_bbox[2] - updated_bbox[0])),
                            "rect_h": float(max(1, updated_bbox[3] - updated_bbox[1])),
                            "rect_angle": float(np.degrees(table_yaw_rad)) if table_yaw_rad is not None else 0.0,
                            "yaw_rad": float(table_yaw_rad) if table_yaw_rad is not None else None,
                            "theta_rejected": False,
                            "roi_mask": None,
                        }

                    track["prev_theta"] = float(table_yaw_rad) if table_yaw_rad is not None else prev_theta_track
                    table_render_yaw = table_yaw_rad
                    # Table-only render hysteresis: choose a stable final yaw for overlay/output.
                    # This does not modify detection/tracking/matching state.
                    if table_render_yaw is not None and self.table_angle_deadband_rad > 0.0:
                        _curr_theta_norm = _normalize_theta_half_pi(float(table_render_yaw))
                        _prev_render_theta = track.get("table_last_rendered_yaw_rad")
                        if _prev_render_theta is not None:
                            _prev_theta_norm = _normalize_theta_half_pi(float(_prev_render_theta))
                            _delta_theta = _smallest_theta_diff(_curr_theta_norm, _prev_theta_norm)
                            if abs(_delta_theta) < float(self.table_angle_deadband_rad):
                                table_render_yaw = _prev_theta_norm
                            else:
                                table_render_yaw = _curr_theta_norm
                        else:
                            table_render_yaw = _curr_theta_norm

                    if table_render_yaw is not None:
                        track["table_last_rendered_yaw_rad"] = float(table_render_yaw)
                        table_shape_extras["yaw_rad"] = float(table_render_yaw)
                        table_shape_extras["rect_angle"] = float(np.degrees(table_render_yaw))

                    # Table-only static hold: reuse previously accepted final table geometry as-is
                    # while the table remains effectively static (visual stabilization only).
                    if self.table_static_hold_enabled:
                        _curr_bbox = [int(v) for v in updated_bbox]
                        _curr_center = (float(center_smoothed[0]), float(center_smoothed[1]))
                        _curr_poly = table_shape_extras.get("poly_px")
                        _curr_yaw = table_render_yaw
                        _curr_area = _table_shape_area_px(_curr_bbox, _curr_poly)

                        _ref_geom = track.get("table_static_ref_geom")
                        _hold_geom = track.get("table_static_hold_geom")
                        _hold_active = bool(track.get("table_static_hold_active", False))
                        _cand_count = int(track.get("table_static_candidate_count", 0))

                        if _ref_geom is None:
                            _ref_geom = {
                                "bbox_px": list(_curr_bbox),
                                "center_px": [float(_curr_center[0]), float(_curr_center[1])],
                                "poly_px": None if _curr_poly is None else [list(p) for p in _curr_poly],
                                "yaw_rad": None if _curr_yaw is None else float(_curr_yaw),
                                "rect_angle": None if _curr_yaw is None else float(np.degrees(_curr_yaw)),
                                "area_px": float(_curr_area),
                            }
                            track["table_static_ref_geom"] = _ref_geom

                        def _geom_delta_ok(_a: Dict, _b: Dict) -> bool:
                            _ac = _a.get("center_px", [0.0, 0.0])
                            _bc = _b.get("center_px", [0.0, 0.0])
                            _center_dist = self._center_dist((float(_ac[0]), float(_ac[1])), (float(_bc[0]), float(_bc[1])))

                            _yaw_a = _a.get("yaw_rad")
                            _yaw_b = _b.get("yaw_rad")
                            if _yaw_a is None and _yaw_b is None:
                                _angle_diff = 0.0
                            elif _yaw_a is None or _yaw_b is None:
                                _angle_diff = float("inf")
                            else:
                                _angle_diff = abs(_smallest_theta_diff(float(_yaw_a), float(_yaw_b)))

                            _area_a = float(max(1e-6, float(_a.get("area_px", 1.0))))
                            _area_b = float(max(1e-6, float(_b.get("area_px", 1.0))))
                            _area_diff = abs(_area_a - _area_b) / max(_area_b, 1e-6)

                            return (
                                _center_dist < float(self.table_static_hold_center_px)
                                and _angle_diff < float(self.table_static_hold_angle_rad)
                                and _area_diff < float(self.table_static_hold_area_frac)
                            )

                        _curr_geom = {
                            "bbox_px": list(_curr_bbox),
                            "center_px": [float(_curr_center[0]), float(_curr_center[1])],
                            "poly_px": None if _curr_poly is None else [list(p) for p in _curr_poly],
                            "yaw_rad": None if _curr_yaw is None else float(_curr_yaw),
                            "rect_angle": None if _curr_yaw is None else float(np.degrees(_curr_yaw)),
                            "area_px": float(_curr_area),
                        }

                        if _hold_active and _hold_geom is not None:
                            if _geom_delta_ok(_curr_geom, _hold_geom):
                                # Keep held final geometry unchanged: no re-fit/reconstruction.
                                updated_bbox = [int(v) for v in _hold_geom.get("bbox_px", _curr_bbox)]
                                _hc = _hold_geom.get("center_px", [float(_curr_center[0]), float(_curr_center[1])])
                                center_smoothed = (float(_hc[0]), float(_hc[1]))
                                _hy = _hold_geom.get("yaw_rad")
                                table_yaw_rad = None if _hy is None else float(_hy)
                                _hpoly = _hold_geom.get("poly_px")
                                table_shape_extras["poly_px"] = None if _hpoly is None else [list(p) for p in _hpoly]
                                table_shape_extras["yaw_rad"] = table_yaw_rad
                                table_shape_extras["rect_angle"] = _hold_geom.get("rect_angle")
                            else:
                                track["table_static_hold_active"] = False
                                track["table_static_candidate_count"] = 0
                                track["table_static_hold_geom"] = None
                                track["table_static_ref_geom"] = _curr_geom
                        else:
                            if _geom_delta_ok(_curr_geom, _ref_geom):
                                _cand_count += 1
                                track["table_static_candidate_count"] = _cand_count
                            else:
                                track["table_static_candidate_count"] = 0
                                track["table_static_ref_geom"] = _curr_geom

                            if int(track.get("table_static_candidate_count", 0)) >= int(self.table_static_hold_frames):
                                _base_geom = track.get("table_static_ref_geom", _curr_geom)
                                track["table_static_hold_active"] = True
                                track["table_static_hold_geom"] = {
                                    "bbox_px": [int(v) for v in _base_geom.get("bbox_px", _curr_bbox)],
                                    "center_px": [
                                        float(_base_geom.get("center_px", [float(_curr_center[0]), float(_curr_center[1])])[0]),
                                        float(_base_geom.get("center_px", [float(_curr_center[0]), float(_curr_center[1])])[1]),
                                    ],
                                    "poly_px": None if _base_geom.get("poly_px") is None else [list(p) for p in _base_geom.get("poly_px")],
                                    "yaw_rad": _base_geom.get("yaw_rad"),
                                    "rect_angle": _base_geom.get("rect_angle"),
                                    "area_px": float(_base_geom.get("area_px", _curr_area)),
                                }
                                _hold_geom = track["table_static_hold_geom"]
                                updated_bbox = [int(v) for v in _hold_geom.get("bbox_px", _curr_bbox)]
                                _hc = _hold_geom.get("center_px", [float(_curr_center[0]), float(_curr_center[1])])
                                center_smoothed = (float(_hc[0]), float(_hc[1]))
                                _hy = _hold_geom.get("yaw_rad")
                                table_yaw_rad = None if _hy is None else float(_hy)
                                _hpoly = _hold_geom.get("poly_px")
                                table_shape_extras["poly_px"] = None if _hpoly is None else [list(p) for p in _hpoly]
                                table_shape_extras["yaw_rad"] = table_yaw_rad
                                table_shape_extras["rect_angle"] = _hold_geom.get("rect_angle")
                    else:
                        track["table_static_hold_active"] = False
                        track["table_static_candidate_count"] = 0
                        track["table_static_hold_geom"] = None
                        track["table_static_ref_geom"] = None

                    if table_yaw_rad is not None:
                        track["table_last_rendered_yaw_rad"] = float(table_yaw_rad)

                if self.H is not None:
                    cx_f, cy_f = apply_homography([center_smoothed[0], center_smoothed[1]], self.H)
                else:
                    cx_f, cy_f = float(center_smoothed[0]), float(center_smoothed[1])

                pose = Pose2D(
                    x=float(cx_f),
                    y=float(cy_f),
                    theta=float(table_yaw_rad) if label == "table" and table_yaw_rad is not None else None,
                )
                entity = DetectedEntity(id=track_id, kind=label, pose=pose, confidence=score)
                if label == "person" and self.person_filter_mode == "geom+static" and not is_ghost:
                    _hist = track.get("person_center_hist")
                    if _hist is not None and len(_hist) >= max(1, int(self.person_static_window)):
                        _old = _hist[0]
                        _new = _hist[-1]
                        _delta = self._center_dist(_old, _new)
                        if _delta < float(self.person_static_max_delta):
                            if self.debug_dir:
                                print(f"[PersonFilter] drop static id={track_id} delta={_delta:.1f}")
                            continue
                if label == "person":
                    people_entities.append(entity)
                else:
                    furniture_entities.append(entity)

                if label == "table" and not is_ghost:
                    # Persist final rendered table geometry for optional short drop-out grace rendering.
                    track["table_last_final_render_geom"] = {
                        "bbox_px": [int(v) for v in updated_bbox],
                        "center_px": [float(center_smoothed[0]), float(center_smoothed[1])],
                        "poly_px": None
                        if table_shape_extras.get("poly_px") is None
                        else [list(p) for p in table_shape_extras.get("poly_px")],
                        "yaw_rad": table_shape_extras.get("yaw_rad"),
                        "rect_angle": table_shape_extras.get("rect_angle"),
                    }
                    track["table_last_final_render_frame_id"] = int(frame_id)

                overlay_items.append({
                    "id": track_id,
                    "label": label,
                    "mask": None,
                    "score": score,
                    "ghost": bool(is_ghost),
                    "shape": {
                        "bbox_px": updated_bbox,
                        "center_px": [float(center_smoothed[0]), float(center_smoothed[1])],
                        **table_shape_extras,
                    },
                })

        # SAM table geometry refinement (only on refine frames)
        if self.table_refine_every > 0 and self.segmenter is not None and (frame_id % self.table_refine_every == 0):
            self._refine_tables_with_sam(frame_bgr, frame_id)

        # Patch overlay_items with SAM-refined corners where available
        if self.table_refine_every > 0 and self.segmenter is not None:
            _table_tracks = self._tracks.get("table", {})
            for _oi in overlay_items:
                if _oi.get("label") != "table":
                    continue
                _tid = _oi.get("id")
                if not _tid or _tid not in _table_tracks:
                    continue
                _track = _table_tracks[_tid]
                _motion_state = str(_track.get("table_motion_state", "moving"))
                _oi["shape"]["motion_state"] = _motion_state
                if _motion_state != "stable":
                    _oi["shape"]["used_fallback"] = True
                    _oi["shape"]["fallback_reason"] = "moving_use_yolo"
                    continue
                _last_corners = _track.get("last_corners_px")
                if _last_corners is None:
                    if bool(_track.get("last_refine_failed", False)):
                        _oi["shape"]["used_fallback"] = True
                        _oi["shape"]["fallback_reason"] = "sam_failed_use_yolo"
                    continue
                _corners_list = _last_corners.tolist() if isinstance(_last_corners, np.ndarray) else list(_last_corners)
                _oi["shape"]["poly_px"] = _corners_list
                _oi["shape"]["corners_px"] = _corners_list
                _oi["shape"]["used_fallback"] = False
                _oi["shape"]["fallback_reason"] = ""
                _refined_theta = _track.get("last_theta")
                if _refined_theta is not None:
                    _oi["shape"]["yaw_rad"] = float(_refined_theta)
                    _oi["shape"]["rect_angle"] = float(np.degrees(_refined_theta))

        if self._track_debug_every > 0 and (frame_id % self._track_debug_every == 0):
            ghost_counts = {
                _lbl: sum(1 for _t in self._tracks[_lbl].values() if int(_t.get("miss_count", 0)) > 0)
                for _lbl in ("chair", "table", "person")
            }
            table_motion_counts = {
                "moving": sum(1 for _t in self._tracks["table"].values() if str(_t.get("table_motion_state", "moving")) == "moving"),
                "stable": sum(1 for _t in self._tracks["table"].values() if str(_t.get("table_motion_state", "moving")) == "stable"),
            }
            print(
                f"[YOLO track] frame={frame_id} "
                f"det(chair={kept_counts['chair']},table={kept_counts['table']},person={kept_counts['person']}) "
                f"tracks(chair={len(self._tracks['chair'])},table={len(self._tracks['table'])},person={len(self._tracks['person'])}) "
                f"ghosts(chair={ghost_counts['chair']},table={ghost_counts['table']},person={ghost_counts['person']})"
            )
            print(
                f"[YOLO table motion] frame={frame_id} "
                f"moving={table_motion_counts['moving']} stable={table_motion_counts['stable']}"
            )
            print(
                f"[YOLO table size] frame={frame_id} "
                f"raw_table_dets={raw_table_dets} "
                f"kept_table_dets={kept_table_dets} "
                f"rejected_small_table_dets={rejected_small_table_dets}"
            )
            print(
                f"[YOLO person] frame={frame_id} "
                f"active_person_tracks={len(self._tracks['person'])} "
                f"new_person_ids_created={self._person_new_ids_since_log} "
                f"geom_filtered_person_dets={rejected_geom_person_dets}"
            )
            self._person_new_ids_since_log = 0

        if self.debug_dir and rejected_table_overlay_items:
            overlay_items.extend(rejected_table_overlay_items)

        if self.table_obb_debug_raw_overlay and raw_table_obb_detections:
            for _idx, _det in enumerate(raw_table_obb_detections):
                _bbox = [int(v) for v in _det.get("bbox_px", [0, 0, 0, 0])]
                _poly = _det.get("obb_poly_px")
                _center = _det.get("obb_center_px")
                if _center is None and len(_bbox) == 4:
                    _center = [0.5 * float(_bbox[0] + _bbox[2]), 0.5 * float(_bbox[1] + _bbox[3])]
                overlay_items.append({
                    "id": f"table_obb_raw_{_idx:03d}",
                    "label": "table_obb_raw",
                    "mask": None,
                    "score": float(_det.get("score", 0.0)),
                    "ghost": False,
                    "shape": {
                        "bbox_px": _bbox,
                        "center_px": _center,
                        "poly_px": _poly,
                        "yaw_rad": _det.get("obb_yaw_rad"),
                    },
                })

        if self.table_obb_debug_jsonl and self._table_obb_detector is not None:
            _final_tables = []
            for _item in overlay_items:
                if _item.get("label") != "table":
                    continue
                _shape = _item.get("shape", {})
                _final_tables.append({
                    "id": _item.get("id"),
                    "score": float(_item.get("score", 0.0)),
                    "bbox_px": _shape.get("bbox_px"),
                    "center_px": _shape.get("center_px"),
                    "poly_px": _shape.get("poly_px"),
                    "motion_state": _shape.get("motion_state"),
                    "fallback_reason": _shape.get("fallback_reason"),
                })
            _raw_tables = []
            for _det in raw_table_obb_detections:
                _raw_tables.append({
                    "score": float(_det.get("score", 0.0)),
                    "bbox_px": _det.get("bbox_px"),
                    "center_px": _det.get("obb_center_px"),
                    "poly_px": _det.get("obb_poly_px"),
                    "yaw_rad": _det.get("obb_yaw_rad"),
                })
            _dbg_payload = {
                "frame_id": int(frame_id),
                "timestamp": timestamp_iso,
                "raw_table_obb": _raw_tables,
                "final_table_tracks": _final_tables,
                "raw_table_obb_count": int(dbg_raw_table_obb_count),
                "matched_active_table_tracks": int(dbg_matched_active_table_tracks),
                "matched_lost_table_tracks": int(dbg_matched_lost_table_tracks),
                "new_table_tracks_created": int(dbg_new_table_tracks_created),
                "blocked_new_table_births_near_lost": int(dbg_blocked_new_table_births_near_lost),
                "recoverable_lost_table_track_count": int(dbg_recoverable_lost_table_track_count),
            }
            _dbg_path = Path(self.table_obb_debug_jsonl)
            _dbg_path.parent.mkdir(parents=True, exist_ok=True)
            with open(_dbg_path, "a", encoding="utf-8") as _dbg_f:
                _dbg_f.write(json.dumps(_dbg_payload) + "\n")

        self._dbg_frame_id = frame_id

        if frame_id in (0, 11):
            kind_counts = Counter(str(_item.get("label", "unknown")) for _item in overlay_items)
            table_items = [_item for _item in overlay_items if _item.get("label") == "table"]
            print(f"[YOLO overlay dbg] frame={frame_id} total_overlay_items={len(overlay_items)}")
            print(f"[YOLO overlay dbg] frame={frame_id} counts_by_kind={dict(kind_counts)}")
            print(f"[YOLO overlay dbg] frame={frame_id} table_items={len(table_items)}")

            for _item in table_items:
                _shape = _item.get("shape", {})
                _bbox = _shape.get("bbox_px")
                _corners = _shape.get("corners_px")
                if _corners is None:
                    _corners = _shape.get("poly_px")
                _theta = _shape.get("yaw_rad")
                print(
                    f"[YOLO overlay dbg] frame={frame_id} table_id={_item.get('id')} "
                    f"item_keys={list(_item.keys())} bbox_px={_bbox} corners_px={_corners} theta={_theta}"
                )

        self._last_overlay_items = overlay_items

        return FrameEvent(
            timestamp_iso=timestamp_iso,
            frame_id=frame_id,
            furniture=furniture_entities,
            people=people_entities,
            world={"homography_applied": self.H is not None, "auto_proposals": "yolo"},
        )

    def process_image_dir_with_proposals(
        self,
        image_dir: str,
        output_jsonl: str,
        proposal_mode: str = "bgsub",
        proposal_config: Optional[Dict] = None,
        fps_sim: float = 10.0,
        table_area_threshold: float = 8000.0,
        rectangularity_threshold: float = 0.65,
        max_tracking_distance: float = 150.0,
        overlay_out_dir: Optional[str] = None,
        overlay_every: int = 10,
        max_frames: Optional[int] = None,
        flush_every: int = 10,
        debug: bool = False,
    ):
        """
        Process image directory with automatic region proposals (BGSub + classification).
        
        Args:
            image_dir: Path to directory containing images
            output_jsonl: Path to output JSONL file
            proposal_mode: Proposer mode (bgsub, dark, furniture alias)
            proposal_config: Optional proposer config dict (e.g., {"bgsub": {...}})
            fps_sim: Simulated FPS for timestamp calculation
            table_area_threshold: Min area for table classification
            rectangularity_threshold: Min ratio mask_area/bbox_area for table
            max_tracking_distance: Max center distance for entity matching
            overlay_out_dir: Optional directory to save overlay frames
            overlay_every: Save overlay every N frames (default 10)
            max_frames: Maximum number of frames to process (None = all)
            flush_every: Flush/fsync every N frames (based on frame_id)
            debug: Enable debug output
        """
        img_dir = Path(image_dir)
        if not img_dir.exists():
            raise RuntimeError(f"Image directory not found: {image_dir}")
        
        # Load all jpg and png files, sorted by name
        image_files = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")))
        
        if len(image_files) == 0:
            raise RuntimeError(f"No .jpg or .png files found in {image_dir}")

        # Select proposer from mode
        normalized_mode = "bgsub" if proposal_mode == "furniture" else proposal_mode
        if normalized_mode not in ["bgsub", "dark", "yolo"]:
            raise ValueError(f"Unsupported auto-proposals mode: {proposal_mode}")

        cfg = proposal_config or {}
        bgsub_cfg = cfg.get("bgsub", {})
        dark_cfg = cfg.get("dark", {})

        proposer = None  # used by bgsub/dark paths only
        mode_max_proposals = 0

        if normalized_mode == "yolo":
            if self._yolo_detector is None:
                raise RuntimeError("YOLO detector not initialised. Pass proposals_mode='yolo' to VisionPipeline.__init__.")
            print(f"Found {len(image_files)} images in {image_dir}")
            print(f"Using auto-proposals mode: yolo")
            print(f"  Max det per class: {self._yolo_max_det}")
        elif normalized_mode == "dark":
            from src.vision.detection.proposals_dark import DarkObjectProposer

            proposer = DarkObjectProposer(
                fixed_thresh=dark_cfg.get("fixed_thresh", 85),
                invert=dark_cfg.get("invert", False),
                drop_border_touching=dark_cfg.get("drop_border_touching", True),
                blur_ksize=dark_cfg.get("blur_ksize", 5),
                close_ksize=dark_cfg.get("close_ksize", 7),
                close_iters=dark_cfg.get("close_iters", 1),
                open_ksize=dark_cfg.get("open_ksize", 3),
                open_iters=dark_cfg.get("open_iters", 1),
                min_area=dark_cfg.get("min_area", 500),
                max_area=dark_cfg.get("max_area", None),
                max_area_frac=dark_cfg.get("max_area_frac", dark_cfg.get("max_area_ratio", 0.15)),
                max_proposals_per_frame=dark_cfg.get("max_proposals_per_frame", 10),
                roi_bbox_px=dark_cfg.get("roi_bbox_px", None),
                debug_dir=self.debug_dir,
                debug_every=dark_cfg.get("debug_every", 5),
            )
            mode_max_proposals = int(dark_cfg.get("max_proposals_per_frame", 10))
            print(f"Found {len(image_files)} images in {image_dir}")
            print(f"Using auto-proposals mode:")
            print(f"  Proposer mode: {normalized_mode}")
            print(f"  Max proposals per frame: {mode_max_proposals}")
            print(f"  Table area threshold: {table_area_threshold} px")
            print(f"  Rectangularity threshold: {rectangularity_threshold}")
            print(f"  Max tracking distance: {max_tracking_distance} px")
        else:
            from src.vision.detection.proposals_bgsub import BGSubProposer

            proposer = BGSubProposer(
                history=bgsub_cfg.get("history", 200),
                var_threshold=bgsub_cfg.get("var_threshold", 16),
                detect_shadows=bgsub_cfg.get("detect_shadows", False),
                min_area=bgsub_cfg.get("min_area", 1500),
                max_area=bgsub_cfg.get("max_area", 200000),
            )
            mode_max_proposals = int(bgsub_cfg.get("max_proposals_per_frame", 50))
            print(f"Found {len(image_files)} images in {image_dir}")
            print(f"Using auto-proposals mode:")
            print(f"  Proposer mode: {normalized_mode}")
            print(f"  Max proposals per frame: {mode_max_proposals}")
            print(f"  Table area threshold: {table_area_threshold} px")
            print(f"  Rectangularity threshold: {rectangularity_threshold}")
            print(f"  Max tracking distance: {max_tracking_distance} px")
        
        output_path = Path(output_jsonl)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create overlay directory if needed
        overlay_path = None
        if overlay_out_dir:
            overlay_path = Path(overlay_out_dir)
            overlay_path.mkdir(parents=True, exist_ok=True)
            print(f"Will save overlays every {overlay_every} frames to {overlay_path}")
        
        # Reset state
        self.state_by_id = {}
        self.reset_tracks()
        
        # Process images
        base_time = time.time()
        frame_duration = 1.0 / fps_sim
        
        frame_count = 0
        
        with open(output_path, "w") as f:
            for img_path in image_files:
                if max_frames is not None and frame_count >= max_frames:
                    break
                
                # Load image
                frame = cv2.imread(str(img_path))
                if frame is None:
                    print(f"Warning: Could not load {img_path}, skipping.")
                    continue
                frame = self._apply_input_crop(frame)
                
                # Calculate timestamp
                timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", 
                                             time.gmtime(base_time + frame_count * frame_duration))
                
                # Process frame with proposals
                if normalized_mode == "yolo":
                    frame_event = self._process_frame_yolo(
                        frame_bgr=frame,
                        frame_id=frame_count,
                        timestamp_iso=timestamp_iso,
                    )
                else:
                    frame_event = self.process_frame_with_proposals(
                        frame_bgr=frame,
                        proposer=proposer,
                        proposal_mode=normalized_mode,
                        timestamp_iso=timestamp_iso,
                        frame_id=frame_count,
                        max_proposals_per_frame=mode_max_proposals,
                        table_area_threshold=table_area_threshold,
                        rectangularity_threshold=rectangularity_threshold,
                        max_tracking_distance=max_tracking_distance,
                        debug=debug,
                    )

                f.write(json.dumps(frame_event.to_dict()) + "\n")
                if flush_every > 0 and (frame_event.frame_id % flush_every == 0):
                    f.flush()
                    os.fsync(f.fileno())

                # Save overlay if requested and at the right interval
                if overlay_path and (frame_count % overlay_every == 0):
                    self._last_render_frame_id = frame_count
                    if self._last_overlay_items:
                        overlay = self.render_overlay(frame, self._last_overlay_items)
                    else:
                        overlay = self._draw_detections_with_boxes(frame, frame_event)

                    out_name = f"frame_{frame_count:05d}_{img_path.stem}.png"
                    cv2.imwrite(str(overlay_path / out_name), overlay)

                frame_count += 1

                if frame_count % 10 == 0:
                    entities_count = len(frame_event.furniture)
                    people_count = len(frame_event.people)
                    print(f"Processed {frame_count}/{len(image_files)} images... (furniture: {entities_count}, people: {people_count})")
        
        print(f"Wrote {frame_count} FrameEvents to {output_path}")
        if overlay_path:
            overlay_count = (frame_count + overlay_every - 1) // overlay_every
            print(f"Saved {overlay_count} overlay frames to {overlay_path}")

