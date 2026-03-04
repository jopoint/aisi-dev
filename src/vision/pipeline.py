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
        debug_dir: Optional[str] = None
    ):
        """
        Initialize vision pipeline.
        
        Args:
            sam3_config_path: Path to SAM2.1 model config (defaults to configs/sam2/sam2.1_hiera_l.yaml)
            sam3_checkpoint_path: Path to SAM2.1 checkpoint (defaults to checkpoints/sam2.1_hiera_large.pt)
            homography_matrix: 3x3 homography matrix (pixel → floor coords), or None
            device: "cuda" or "cpu"
            table_min_area: Minimum table mask area in pixels
            table_max_area: Maximum table mask area in pixels
            chair_min_area: Minimum chair mask area in pixels
            chair_max_area: Maximum chair mask area in pixels
            debug_dir: Optional directory for debug overlays
        """
        # Use SAM2.1 defaults if not provided
        if sam3_config_path is None:
            sam3_config_path = "configs/sam2/sam2.1_hiera_l.yaml"
        if sam3_checkpoint_path is None:
            sam3_checkpoint_path = "checkpoints/sam2.1_hiera_large.pt"
        
        self.segmenter = SAM3Segmenter(
            config_path=sam3_config_path,
            checkpoint_path=sam3_checkpoint_path,
            device=device
        )
        
        self.H = homography_matrix
        self.table_min_area = table_min_area
        self.table_max_area = table_max_area
        self.chair_min_area = chair_min_area
        self.chair_max_area = chair_max_area
        self.debug_dir = debug_dir
        
        self.frame_id = 0
        self._last_overlay_items = []  # Storage for visualization items
        self.state_by_id = {}  # State management: {id: {"label":..., "bbox_px":..., "center_px":..., "shape":...}}
        
        print(f"\n=== VisionPipeline Initialized ===")
        print(f"SAM2.1 Config: {sam3_config_path}")
        print(f"SAM2.1 Checkpoint: {sam3_checkpoint_path}")
        print(f"Device: {device}")
        print(f"Homography: {'enabled' if self.H is not None else 'disabled'}")
        print(f"Table area filter: [{table_min_area}, {table_max_area}] px")
        print(f"Chair area filter: [{chair_min_area}, {chair_max_area}] px")
        print(f"===================================\n")
    
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
        flush_every: int = 10,
    ):
        """
        Process live camera stream.
        
        Args:
            camera_index: Camera device index
            output_jsonl: Optional path to write JSONL output
            display: Whether to show live display window
            flush_every: Flush/fsync every N frames (based on frame_id)
        """
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera {camera_index}")
        
        jsonl_file = None
        if output_jsonl is not None:
            output_path = Path(output_jsonl)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            jsonl_file = open(output_path, "w")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame from camera")
                    break
                
                frame_event = self.process_frame(frame)
                
                if jsonl_file is not None:
                    jsonl_file.write(json.dumps(frame_event.to_dict()) + "\n")
                    if flush_every > 0 and (frame_event.frame_id % flush_every == 0):
                        jsonl_file.flush()
                        os.fsync(jsonl_file.fileno())
                
                if display:
                    # Draw detections on frame
                    display_frame = self._draw_detections(frame, frame_event)
                    cv2.imshow("Vision Pipeline", display_frame)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:  # q or ESC
                        break
        
        finally:
            cap.release()
            if jsonl_file is not None:
                jsonl_file.close()
            if display:
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
        overlay = frame_bgr.copy()
        h, w = overlay.shape[:2]
        
        # Color map for labels
        label_colors = {
            "table": (0, 255, 255),    # Cyan
            "chair": (255, 0, 255),    # Magenta
            "person": (0, 255, 0),     # Green
        }
        
        for item in overlay_items:
            label = item.get("label", "unknown")
            mask = item.get("mask")
            obj_id = item.get("id", "")
            score = item.get("score", 0.0)
            shape = item.get("shape", {})
            
            # Get color for this label
            color = label_colors.get(label, (128, 128, 128))

            # Draw mask and contour if available
            has_mask = mask is not None and mask.any()
            if has_mask:
                mask_uint8 = (mask.astype(np.uint8) * 255)

                alpha = 0.35
                mask_indices = mask > 0
                overlay[mask_indices] = (
                    overlay[mask_indices] * (1 - alpha) +
                    np.array(color) * alpha
                ).astype(np.uint8)

                contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    cv2.drawContours(overlay, contours, -1, color, 2)

            # Draw bbox fallback if available (works even without mask)
            bbox = shape.get("bbox_px")
            if bbox and len(bbox) == 4:
                x1, y1, x2, y2 = [int(v) for v in bbox]
                cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            
            # Draw geometry shapes
            if label == "table" and "corners_px" in shape:
                corners = shape["corners_px"]
                if corners and len(corners) >= 3:
                    pts = np.array(corners, dtype=np.int32)
                    cv2.polylines(overlay, [pts], True, color, 2)
            
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
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
                    if "center_px" in shape:
                        cx, cy = int(shape["center_px"][0]), int(shape["center_px"][1])
                        cv2.circle(overlay, (cx, cy), 4, color, -1)
            
            # Draw ID and score text
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
        if normalized_mode not in ["bgsub", "dark"]:
            raise ValueError(f"Unsupported auto-proposals mode: {proposal_mode}")

        cfg = proposal_config or {}
        bgsub_cfg = cfg.get("bgsub", {})
        dark_cfg = cfg.get("dark", {})

        if normalized_mode == "dark":
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
                
                # Calculate timestamp
                timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", 
                                             time.gmtime(base_time + frame_count * frame_duration))
                
                # Process frame with proposals
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
                    if hasattr(self, '_last_overlay_items') and self._last_overlay_items:
                        overlay = self.render_overlay(frame, self._last_overlay_items)
                    else:
                        overlay = self._draw_detections_with_boxes(frame, frame_event)
                    
                    out_name = f"frame_{frame_count:05d}_{img_path.stem}.png"
                    cv2.imwrite(str(overlay_path / out_name), overlay)
                
                frame_count += 1
                
                if frame_count % 10 == 0:
                    entities_count = len(frame_event.furniture)
                    print(f"Processed {frame_count}/{len(image_files)} images... (detected: {entities_count} furniture)")
        
        print(f"Wrote {frame_count} FrameEvents to {output_path}")
        if overlay_path:
            overlay_count = (frame_count + overlay_every - 1) // overlay_every
            print(f"Saved {overlay_count} overlay frames to {overlay_path}")

