"""
CLI tool to run the vision pipeline on video files, camera streams, or image directories.

Example usage:
    # Process video file
    python -m src.vision.tools.run_vision_pipeline --video data/video.mp4 --out data/vision_output.jsonl
    
    # Live camera
    python -m src.vision.tools.run_vision_pipeline --camera 0 --out data/vision_live.jsonl
    
    # Image directory
    python -m src.vision.tools.run_vision_pipeline --image-dir data/vision/test_frames --out data/vision_output.jsonl
    
    # Image directory with interactive box selection
    python -m src.vision.tools.run_vision_pipeline --image-dir data/frames --out output.jsonl --init-boxes
    
    # Image directory with predefined boxes
    python -m src.vision.tools.run_vision_pipeline --image-dir data/frames --out output.jsonl --boxes-init "100,100,500,500;600,200,900,600"
"""

import argparse
import numpy as np
from pathlib import Path
import json
from typing import List, Tuple, Optional
import torch
import cv2

from src.vision.pipeline import VisionPipeline
from src.vision.utils import load_vision_config


def load_homography(path: str) -> np.ndarray:
    """Load homography matrix from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    H = np.array(data["homography"], dtype=np.float64)
    return H


def parse_boxes(boxes_str: str) -> List[List[int]]:
    """
    Parse box string in format "x1,y1,x2,y2;x1,y1,x2,y2;..."
    
    Args:
        boxes_str: Semicolon-separated box coordinates
    
    Returns:
        List of boxes [[x1, y1, x2, y2], ...]
    """
    boxes = []
    for box_str in boxes_str.split(";"):
        coords = [int(x.strip()) for x in box_str.split(",")]
        if len(coords) != 4:
            raise ValueError(f"Box must have 4 coordinates, got {len(coords)}: {box_str}")
        boxes.append(coords)
    return boxes


def load_boxes_from_json(json_path: str) -> List[List[int]]:
    """
    Load boxes from JSON file (from select_boxes_init.py).
    
    Args:
        json_path: Path to JSON file with boxes
    
    Returns:
        List of boxes [[x1, y1, x2, y2], ...]
    """
    with open(json_path, "r") as f:
        data = json.load(f)
    
    boxes = []
    if "boxes" in data:
        for box_info in data["boxes"]:
            bbox = box_info["bbox_px"]
            boxes.append(bbox)  # bbox is [x1, y1, x2, y2]
    
    return boxes


def load_boxes_with_labels_from_json(json_path: str) -> Tuple[List[List[int]], List[str]]:
    """
    Load boxes with labels from JSON file (from select_boxes_init.py).
    
    Args:
        json_path: Path to JSON file with boxes
    
    Returns:
        Tuple of (boxes, labels) where:
        - boxes: List of [[x1, y1, x2, y2], ...]
        - labels: List of label strings (e.g., "table", "chair")
    """
    with open(json_path, "r") as f:
        data = json.load(f)
    
    boxes = []
    labels = []
    if "boxes" in data:
        for box_info in data["boxes"]:
            bbox = box_info["bbox_px"]
            label = box_info.get("label", "unknown")
            boxes.append(bbox)
            labels.append(label)
    
    return boxes, labels


def map_detector_classes_to_coco(detector_classes_arg: Optional[str]) -> Optional[List[str]]:
    """
    Map user detector classes to COCO class names.

    Args:
        detector_classes_arg: Comma-separated class list from CLI, or None

    Returns:
        List of COCO class names, or None if no class filter is requested
    """
    if detector_classes_arg is None:
        return None

    token_map = {
        "table": ["dining table"],
        "chair": ["chair"],
        "person": ["person"],
    }

    mapped: List[str] = []
    for token in [part.strip() for part in detector_classes_arg.split(",") if part.strip()]:
        mapped.extend(token_map.get(token, [token]))

    return mapped


def load_first_frame(
    image_dir: Optional[str] = None,
    video_path: Optional[str] = None,
    camera_index: Optional[int] = None
) -> Optional[np.ndarray]:
    """
    Load the first frame from image directory, video, or camera.
    
    Args:
        image_dir: Path to image directory
        video_path: Path to video file
        camera_index: Camera device index
    
    Returns:
        First frame as BGR numpy array, or None if loading fails
    """
    if image_dir:
        img_dir = Path(image_dir)
        image_files = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")))
        if len(image_files) == 0:
            print(f"ERROR: No images found in {image_dir}")
            return None
        frame = cv2.imread(str(image_files[0]))
        if frame is None:
            print(f"ERROR: Could not load first image: {image_files[0]}")
            return None
        return frame
    
    elif video_path:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"ERROR: Could not open video: {video_path}")
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print(f"ERROR: Could not read first frame from video: {video_path}")
            return None
        return frame
    
    elif camera_index is not None:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print(f"ERROR: Could not open camera: {camera_index}")
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print(f"ERROR: Could not read frame from camera: {camera_index}")
            return None
        return frame
    
    return None


def auto_init_boxes_with_yolo(
    frame_bgr: np.ndarray,
    detector_model: str,
    detector_classes: Optional[List[str]],
    device: str,
    output_json_path: str,
    debug_overlay_path: str = "data/vision/debug/auto_init_boxes.png"
) -> Tuple[List[List[int]], List[str]]:
    """
    Automatically initialize boxes using YOLO detection.
    
    Args:
        frame_bgr: First frame in BGR format
        detector_model: YOLO model path (e.g., "yolov8s.pt")
        detector_classes: Optional class filter list (COCO names), None = no filter
        device: Device to run detector on ("cuda" or "cpu")
        output_json_path: Path to save boxes JSON
        debug_overlay_path: Path to save debug visualization
    
    Returns:
        Tuple of (boxes, labels) where:
        - boxes: List of [[x1, y1, x2, y2], ...]
        - labels: List of label strings
    """
    from src.vision.detection.yolo_detector import YOLODetector
    
    print(f"\n=== Auto-Initializing Boxes with YOLO ===")
    print(f"Detector model: {detector_model}")
    print(f"Detector classes: {detector_classes if detector_classes is not None else 'None (no filter)'}")
    print(f"Device: {device}")
    
    # Initialize detector
    detector = YOLODetector(
        model=detector_model,
        device=device,
        conf=0.25,
        iou=0.5,
        classes=detector_classes
    )
    
    # Run detection
    detections = detector.detect(frame_bgr)
    
    print(f"Found {len(detections)} objects")
    
    if len(detections) == 0:
        print("WARNING: No objects detected. Proceeding without boxes.")
        return [], []

    # Print top-10 detections by score
    print("Top-10 detections (label, score):")
    top_detections = sorted(detections, key=lambda item: float(item.get("score", 0.0)), reverse=True)[:10]
    for det in top_detections:
        print(f"  {det['label']}: {det['score']:.3f}")
    
    # Extract boxes and labels
    boxes = []
    labels = []
    for det in detections:
        boxes.append(det["bbox_px"])
        labels.append(det["label"])
        print(f"  {det['label']}: bbox={det['bbox_px']}, score={det['score']:.3f}")
    
    # Save JSON
    h, w = frame_bgr.shape[:2]
    output_data = {
        "image_size": [w, h],
        "boxes": [
            {"label": label, "bbox_px": bbox}
            for label, bbox in zip(labels, boxes)
        ]
    }
    
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Saved boxes to: {output_json_path}")
    
    # Create debug overlay
    debug_path = Path(debug_overlay_path)
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    
    overlay = frame_bgr.copy()
    color_map = {
        "chair": (255, 0, 255),    # Magenta
        "table": (0, 255, 255),    # Cyan
        "person": (0, 255, 0)      # Green
    }
    
    for label, bbox in zip(labels, boxes):
        x1, y1, x2, y2 = bbox
        color = color_map.get(label, (255, 255, 255))
        
        # Draw box
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
        
        # Draw label
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        text = f"{label}"
        
        (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        bg_x1, bg_y1 = x1, y1 - text_h - baseline - 5
        bg_x2, bg_y2 = x1 + text_w + 5, y1
        bg_y1 = max(0, bg_y1)
        
        cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
        cv2.putText(overlay, text, (x1 + 2, y1 - 5), font, font_scale, color, thickness)
    
    cv2.imwrite(str(debug_path), overlay)
    print(f"Saved debug overlay to: {debug_overlay_path}")
    print(f"========================================\n")
    
    return boxes, labels


def check_cuda_available() -> bool:
    """
    Check if CUDA is available.
    
    Returns:
        True if CUDA is available, False otherwise
    """
    try:
        return torch.cuda.is_available()
    except Exception:
        return False


def main():
    # Load vision configuration defaults from configs/vision.yaml
    try:
        vision_config = load_vision_config("configs/vision.yaml")
        sam_config = vision_config.get("sam", {})
        furniture_config = vision_config.get("furniture", {})
        print(f"\nLoaded configuration from configs/vision.yaml")
    except FileNotFoundError:
        print("WARNING: configs/vision.yaml not found. Using hardcoded defaults.")
        sam_config = {
            "config_path": "configs/sam2/sam2.1_hiera_l.yaml",
            "checkpoint_path": "checkpoints/sam2.1_hiera_large.pt",
            "device": "cuda"
        }
        furniture_config = {
            "table_min_area": 5000.0,
            "table_max_area": 50000.0,
            "chair_min_area": 2000.0,
            "chair_max_area": 20000.0
        }
    
    parser = argparse.ArgumentParser(description="Run vision pipeline for furniture detection.")
    
    # Input source (mutually exclusive)
    parser.add_argument("--video", help="Input video file path.")
    parser.add_argument("--camera", type=int, help="Camera device index.")
    parser.add_argument("--image-dir", help="Input directory with images (*.jpg, *.png).")
    parser.add_argument("--camera-rotate", type=int, choices=[0, 90, 180, 270], default=0, help="Optional camera frame rotation in degrees (default: 0).")
    parser.add_argument("--camera-width", type=int, default=None, help="Optional requested camera capture width in pixels.")
    parser.add_argument("--camera-height", type=int, default=None, help="Optional requested camera capture height in pixels.")
    parser.add_argument("--save-live-frame", default=None, help="Optional output PNG path: save first live frame after rotation, before crop/detection.")
    parser.add_argument("--exit-after-saving-live-frame", action="store_true", help="Exit camera loop immediately after saving --save-live-frame.")
    
    # Output
    parser.add_argument("--out", required=True, help="Output JSONL file path.")
    
    # SAM2.1 configuration (loaded from configs/vision.yaml, CLI overrides)
    parser.add_argument("--sam-config", default=sam_config.get("config_path"), help="SAM2.1 model config path.")
    parser.add_argument("--sam-checkpoint", default=sam_config.get("checkpoint_path"), help="SAM2.1 checkpoint path.")
    parser.add_argument("--device", choices=["cuda", "cpu"], default=sam_config.get("device"), help="Device for SAM2.1 (falls back to cpu if cuda not available).")
    
    # Homography
    parser.add_argument("--homography", help="Path to homography JSON file (optional).")
    
    # Furniture filtering (loaded from configs/vision.yaml, CLI overrides)
    parser.add_argument("--table-min-area", type=float, default=furniture_config.get("table_min_area"), help="Minimum table area in pixels.")
    parser.add_argument("--table-max-area", type=float, default=furniture_config.get("table_max_area"), help="Maximum table area in pixels.")
    parser.add_argument("--chair-min-area", type=float, default=furniture_config.get("chair_min_area"), help="Minimum chair area in pixels.")
    parser.add_argument("--chair-max-area", type=float, default=furniture_config.get("chair_max_area"), help="Maximum chair area in pixels.")
    
    # Box initialization (for image-dir mode)
    parser.add_argument("--boxes-init", help="Path to JSON file with initial boxes (from select_boxes_init.py)")
    parser.add_argument("--init-boxes", action="store_true", help="Interactively select boxes on first image (image-dir mode).")
    
    # Auto-init with YOLO detector
    parser.add_argument("--auto-init-boxes", action="store_true", help="Automatically initialize boxes using YOLO detector.")
    parser.add_argument("--auto-init-out", default="data/vision/boxes_init_auto.json", help="Output path for auto-initialized boxes JSON (default: data/vision/boxes_init_auto.json).")
    parser.add_argument("--detector", default="yolo", help="Detector type for auto-init (default: yolo).")
    parser.add_argument("--detector-model", default="yolov8s.pt", help="Detector model path (default: yolov8s.pt).")
    parser.add_argument("--detector-classes", default=None, help="Comma-separated detector classes (e.g., chair,table,person). If omitted with --auto-init-boxes: no filter.")
    
    # Auto-proposals
    parser.add_argument(
        "--auto-proposals",
        choices=["bgsub", "dark", "furniture", "yolo"],
        help=(
            "Enable automatic region proposals mode. "
            "Modes: bgsub, dark, furniture (alias for bgsub), yolo."
        ),
    )

    # YOLO proposer options (used when --auto-proposals yolo)
    parser.add_argument("--yolo-model", default="runs/detect/train/weights/best_fixed.pt", help="YOLO weights path (default: runs/detect/train/weights/best_fixed.pt).")
    parser.add_argument("--yolo-conf", type=float, default=0.25, help="YOLO confidence threshold (default: 0.25).")
    parser.add_argument("--yolo-iou", type=float, default=0.45, help="YOLO IoU threshold for NMS (default: 0.45).")
    parser.add_argument("--table-obb-model", default=None, help="Optional table-only OBB weights path for hybrid mode (table from OBB, chair/person from YOLO).")
    parser.add_argument("--table-obb-conf", type=float, default=None, help="Confidence threshold for --table-obb-model (default: --yolo-conf).")
    parser.add_argument("--table-obb-iou", type=float, default=None, help="IoU threshold for --table-obb-model (default: --yolo-iou).")
    parser.add_argument("--table-obb-max-det", type=int, default=0, help="Optional cap for raw table OBB detections before merge/tracking (0 = disabled).")
    parser.add_argument("--table-obb-raw-min-conf", type=float, default=None, help="Optional minimum confidence applied only to raw table OBB detections before merge/tracking.")
    parser.add_argument("--table-obb-debug-raw-overlay", action="store_true", help="Show raw table OBB detections as debug overlay items.")
    parser.add_argument("--table-obb-debug-jsonl", default=None, help="Optional JSONL path to write per-frame raw table OBB detections vs final table tracks.")
    parser.add_argument("--yolo-max-det", type=int, default=80, help="Max YOLO detections kept per frame (default: 80).")
    parser.add_argument("--track-ttl-frames", type=int, default=15, help="Keep unmatched tracks alive for this many frames (default: 15).")
    parser.add_argument("--conf-create", type=float, default=None, help="Min detection confidence to create a NEW track (default: --yolo-conf).")
    parser.add_argument("--conf-keep", type=float, default=0.15, help="Min detection confidence to update/reacquire EXISTING tracks (default: 0.15).")
    parser.add_argument("--reacquire-max-age", type=int, default=None, help="Max ghost age in frames eligible for ID reacquire (default: --track-ttl-frames).")
    parser.add_argument("--reacquire-max-dist", type=float, default=150.0, help="Max center distance in px for active/reacquire matching (default: 150).")
    parser.add_argument("--reacquire-min-iou", type=float, default=0.05, help="Min IoU for active/reacquire matching (default: 0.05).")
    parser.add_argument("--chairs-no-ghost", type=lambda v: str(v).lower() in ("1", "true", "yes", "y", "on"), default=True, help="If true (default), disable chair ghosting/reacquire and use conf_create-only for chairs.")
    parser.add_argument("--no-ghosting", action="store_true", help="Disable ghosting/reacquire globally (output only matched/new tracks per frame).")
    parser.add_argument("--table-min-area-frac", type=float, default=0.015, help="Reject YOLO table boxes smaller than this fraction of frame area (default: 0.015).")
    parser.add_argument("--table-min-w-frac", type=float, default=0.08, help="Reject YOLO table boxes narrower than this fraction of frame width (default: 0.08).")
    parser.add_argument("--table-min-h-frac", type=float, default=0.08, help="Reject YOLO table boxes shorter than this fraction of frame height (default: 0.08).")
    parser.add_argument("--person-min-conf", type=float, default=0.60, help="Minimum confidence for person detections before tracking (default: 0.60).")
    parser.add_argument("--person-min-iou", type=float, default=0.10, help="Minimum IoU for person track matching (default: 0.10).")
    parser.add_argument("--person-max-dist", type=float, default=180.0, help="Maximum center distance in pixels for person matching (default: 180).")
    parser.add_argument("--person-ttl", type=int, default=60, help="Person track TTL in frames (default: 60).")
    parser.add_argument("--person-min-area", type=int, default=1200, help="Min person bbox area in px (default: 1200).")
    parser.add_argument("--person-max-area", type=int, default=120000, help="Max person bbox area in px (default: 120000).")
    parser.add_argument("--person-max-ar", type=float, default=4.0, help="Max person bbox aspect ratio max(w/h, h/w) (default: 4.0).")
    parser.add_argument("--person-min-height", type=int, default=60, help="Min person bbox height in px (default: 60).")
    parser.add_argument("--person-min-ar-wh", type=float, default=0.18, help="Min allowed person bbox ratio w/h (default: 0.18).")
    parser.add_argument("--person-max-ar-wh", type=float, default=1.25, help="Max allowed person bbox ratio w/h (default: 1.25).")
    parser.add_argument("--person-excl-right-frac", type=float, default=0.0, help="Exclude person detections with center in the right edge strip (fraction of frame width, default: 0.0).")
    parser.add_argument("--person-excl-rb-right-frac", type=float, default=0.0, help="Right-bottom exclusion zone width fraction from right edge (default: 0.0).")
    parser.add_argument("--person-excl-rb-bottom-frac", type=float, default=0.0, help="Right-bottom exclusion zone height fraction from bottom edge (default: 0.0).")
    parser.add_argument("--person-conf-override", type=float, default=None, help="Optional stricter confidence threshold applied only to person detections before tracking.")
    parser.add_argument("--person-static-window", type=int, default=30, help="Window size for static person suppression (default: 30).")
    parser.add_argument("--person-static-max-delta", type=float, default=20.0, help="Max center delta (px) over full window to consider static (default: 20.0).")
    parser.add_argument("--person-filter-mode", choices=["none", "geom", "geom+static"], default="geom+static", help="Person filter mode (default: geom+static).")

    # SAM table geometry refinement (YOLO mode only)
    parser.add_argument("--table-refine-every", type=int, default=3, help="Run SAM table geometry refinement every N frames (0 = disabled, default: 3).")
    parser.add_argument("--table-refine-max", type=int, default=4, help="Max tables to SAM-refine per refine frame (default: 4).")
    parser.add_argument("--table-refine-margin", type=int, default=12, help="Margin in px to expand YOLO bbox before SAM box prompt (default: 12).")
    parser.add_argument("--table-motion-shift-px", type=float, default=18.0, help="Mark table as moving if center shift exceeds this many px (default: 18).")
    parser.add_argument("--table-motion-iou-min", type=float, default=0.78, help="Mark table as moving if IoU to previous bbox is below this value (default: 0.78).")
    parser.add_argument("--table-motion-area-change", type=float, default=0.18, help="Mark table as moving if relative bbox area change exceeds this value (default: 0.18).")
    parser.add_argument("--table-stable-frames", type=int, default=4, help="Consecutive non-moving frames required before table is stable (default: 4).")
    parser.add_argument("--table-min-bbox-area", type=int, default=30000, help="Reject table detections with bbox area < this px\u00b2 (default: 30000).")
    parser.add_argument("--table-min-bbox-minside", type=int, default=120, help="Reject table detections with min(w,h) < this px (default: 120).")
    parser.add_argument("--table-new-conf-create", type=float, default=None, help="Optional stricter confidence to create NEW table tracks (default: --conf-create).")
    parser.add_argument("--table-new-min-bbox-area", type=int, default=None, help="Optional stricter min bbox area to create NEW table tracks (default: --table-min-bbox-area).")
    parser.add_argument("--table-new-min-bbox-minside", type=int, default=None, help="Optional stricter min bbox short-side to create NEW table tracks (default: --table-min-bbox-minside).")
    parser.add_argument("--table-new-confirm-frames", type=int, default=1, help="Frames required before a NEW table track is shown (1 = disabled).")
    parser.add_argument("--table-new-suppress-iou", type=float, default=0.0, help="Suppress NEW table tracks if IoU with existing confirmed table >= value (0 = disabled).")
    parser.add_argument("--table-new-suppress-center-dist-px", type=float, default=0.0, help="Suppress NEW table tracks if center distance to existing confirmed table <= px (0 = disabled).")
    parser.add_argument("--table-protect-existing-tracks", action="store_true", help="Prefer continuity for tables: suppress new table births while recoverable lost table tracks exist.")
    parser.add_argument("--table-recover-lost-tracks", action="store_true", help="Enable table-specific lost-track recovery before new table birth.")
    parser.add_argument("--table-lost-track-ttl", type=int, default=15, help="Recoverable miss-count TTL for lost table tracks when recovery mode is enabled (default: 15).")
    parser.add_argument("--table-birth-block-near-lost-dist", type=float, default=0.0, help="Suppress NEW table birth when detection center is within this px distance to a recoverable lost table track (0 = disabled).")
    parser.add_argument("--table-birth-block-near-lost-frames", type=int, default=0, help="Optional max miss_count age for near-lost birth suppression (0 = use all recoverable lost tracks).")
    parser.add_argument("--table-angle-deadband-deg", type=float, default=0.0, help="Table-only angle hysteresis deadband in degrees for final render angle (0 = disabled).")
    parser.add_argument("--table-render-grace-frames", type=int, default=0, help="Render last final table geometry for this many missing frames (0 = disabled).")
    parser.add_argument("--table-static-hold-frames", type=int, default=0, help="Consecutive static candidate frames before table hold is activated (0 = disabled).")
    parser.add_argument("--table-static-hold-center-px", type=float, default=0.0, help="Static hold threshold for center delta in px (0 = disabled).")
    parser.add_argument("--table-static-hold-angle-deg", type=float, default=0.0, help="Static hold threshold for angle delta in degrees (0 = disabled).")
    parser.add_argument("--table-static-hold-area-frac", type=float, default=0.0, help="Static hold threshold for relative area delta (0 = disabled).")

    # Dark proposer options
    parser.add_argument("--dark-fixed-thresh", type=int, default=None, help="HSV V-channel threshold for dark objects (0-255).")
    parser.add_argument("--dark-max-area-frac", type=float, default=None, help="Max component area as fraction of frame area.")
    parser.add_argument("--dark-no-drop-border", action="store_true", help="Do NOT drop components touching image borders (default: drop them).")
    parser.add_argument("--roi-bbox", type=int, nargs=4, metavar=("X1", "Y1", "X2", "Y2"), help="ROI bounding box in pixels [x1 y1 x2 y2] (optional).")
    
    # Processing options (image-dir)
    parser.add_argument("--fps-sim", type=float, default=10.0, help="Simulated FPS for timestamps (image-dir mode).")
    parser.add_argument("--overlay-out-dir", help="Optional directory to save overlay frames (image-dir only).")
    parser.add_argument("--overlay-style", choices=["debug", "projector", "projector_on_frame"], default="debug", help="Overlay style for saved overlays (default: debug).")
    parser.add_argument("--overlay-every", type=int, default=10, help="Save overlay every N frames (default 10).")
    parser.add_argument("--debug-dump", action="store_true", help="Save segmentation masks as individual PNGs (image-dir only).")
    parser.add_argument("--refine-every", type=int, default=10, help="Re-segment every N frames (default 10, 0 = no refinement).")
    parser.add_argument("--box-margin-px", type=int, default=40, help="Margin in pixels to expand boxes during refinement (default 40).")
    
    # General options
    parser.add_argument("--debug-dir", help="Optional directory for debug overlays.")
    parser.add_argument("--max-frames", type=int, help="Maximum frames to process.")
    parser.add_argument("--flush-every", type=int, default=10, help="Flush and fsync JSONL output every N frames (default 10).")
    parser.add_argument("--no-display", action="store_true", help="Disable live display (camera only).")
    parser.add_argument("--projector-display", action="store_true", help="Show fullscreen projector overlay window (camera mode).")
    parser.add_argument("--projector-monitor", type=int, default=1, help="Monitor index for projector window (0=primary, 1=second).")
    parser.add_argument("--show-table-ids", action="store_true", help="Show table track IDs near final table overlays.")
    parser.add_argument("--display-rotate", type=int, choices=[0, 90, 180, 270], default=0, help="Rotate final display/projector feed (0/90/180/270), rendering only.")
    parser.add_argument("--crop-x", type=int, default=None, help="Optional fixed input crop X offset in pixels.")
    parser.add_argument("--crop-y", type=int, default=None, help="Optional fixed input crop Y offset in pixels.")
    parser.add_argument("--crop-w", type=int, default=None, help="Optional fixed input crop width in pixels.")
    parser.add_argument("--crop-h", type=int, default=None, help="Optional fixed input crop height in pixels.")
    
    args = parser.parse_args()
    
    # Validate input source
    input_count = sum([args.video is not None, args.camera is not None, args.image_dir is not None])
    if input_count == 0:
        parser.error("One of --video, --camera, or --image-dir must be specified.")
    if input_count > 1:
        parser.error("Only one of --video, --camera, or --image-dir can be specified.")
    
    # Validate box options
    if args.boxes_init and args.init_boxes:
        parser.error("Cannot specify both --boxes-init and --init-boxes.")
    if (args.boxes_init or args.init_boxes) and args.image_dir is None:
        parser.error("--boxes-init and --init-boxes are only supported with --image-dir.")
    if args.auto_init_boxes and args.image_dir is None:
        parser.error("--auto-init-boxes is only supported with --image-dir.")
    if args.auto_proposals and args.image_dir is None:
        # Allow live camera for YOLO-only proposal mode.
        if not (args.camera is not None and args.auto_proposals == "yolo"):
            parser.error("--auto-proposals is only supported with --image-dir (or --camera when mode is yolo).")
    if args.table_obb_model and args.auto_proposals != "yolo":
        parser.error("--table-obb-model is only supported with --auto-proposals yolo.")
    if args.auto_proposals and (args.boxes_init or args.init_boxes or args.auto_init_boxes):
        parser.error("--auto-proposals cannot be used with manual box initialization (--boxes-init, --init-boxes, --auto-init-boxes).")
    if args.overlay_out_dir and args.image_dir is None:
        parser.error("--overlay-out-dir is only supported with --image-dir.")
    if args.flush_every < 1:
        parser.error("--flush-every must be >= 1.")
    if args.table_obb_max_det is not None and int(args.table_obb_max_det) < 0:
        parser.error("--table-obb-max-det must be >= 0.")
    if args.table_obb_raw_min_conf is not None and not (0.0 <= float(args.table_obb_raw_min_conf) <= 1.0):
        parser.error("--table-obb-raw-min-conf must be in [0, 1].")
    if int(args.table_lost_track_ttl) < 1:
        parser.error("--table-lost-track-ttl must be >= 1.")
    if float(args.table_birth_block_near_lost_dist) < 0.0:
        parser.error("--table-birth-block-near-lost-dist must be >= 0.")
    if int(args.table_birth_block_near_lost_frames) < 0:
        parser.error("--table-birth-block-near-lost-frames must be >= 0.")
    if float(args.table_angle_deadband_deg) < 0.0:
        parser.error("--table-angle-deadband-deg must be >= 0.")
    if int(args.table_render_grace_frames) < 0:
        parser.error("--table-render-grace-frames must be >= 0.")
    if int(args.table_static_hold_frames) < 0:
        parser.error("--table-static-hold-frames must be >= 0.")
    if float(args.table_static_hold_center_px) < 0.0:
        parser.error("--table-static-hold-center-px must be >= 0.")
    if float(args.table_static_hold_angle_deg) < 0.0:
        parser.error("--table-static-hold-angle-deg must be >= 0.")
    if float(args.table_static_hold_area_frac) < 0.0:
        parser.error("--table-static-hold-area-frac must be >= 0.")
    crop_vals = [args.crop_x, args.crop_y, args.crop_w, args.crop_h]
    crop_set_count = sum(v is not None for v in crop_vals)
    if crop_set_count not in (0, 4):
        parser.error("Set either all crop params (--crop-x --crop-y --crop-w --crop-h) or none.")
    if args.crop_w is not None and int(args.crop_w) <= 0:
        parser.error("--crop-w must be > 0.")
    if args.crop_h is not None and int(args.crop_h) <= 0:
        parser.error("--crop-h must be > 0.")
    if args.camera_width is not None and int(args.camera_width) <= 0:
        parser.error("--camera-width must be > 0.")
    if args.camera_height is not None and int(args.camera_height) <= 0:
        parser.error("--camera-height must be > 0.")
    if args.save_live_frame and args.camera is None:
        parser.error("--save-live-frame is only supported with --camera.")
    if args.exit_after_saving_live_frame and not args.save_live_frame:
        parser.error("--exit-after-saving-live-frame requires --save-live-frame.")
    
    # Load homography if provided
    H = None
    if args.homography:
        H = load_homography(args.homography)
        print(f"Loaded homography from {args.homography}")
    
    # Check device availability and fall back if needed
    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        print("WARNING: CUDA requested but not available. Falling back to CPU.")
        device = "cpu"
    
    if args.conf_create is None:
        args.conf_create = float(args.yolo_conf)
    if args.reacquire_max_age is None:
        args.reacquire_max_age = int(args.track_ttl_frames)

    # Print startup configuration
    is_yolo_mode = getattr(args, "auto_proposals", None) == "yolo"
    print(f"\n=== Vision Pipeline Configuration ===")
    if is_yolo_mode:
        print(f"Mode: YOLO proposals")
        print(f"YOLO model: {args.yolo_model}")
        print(f"YOLO conf: {args.yolo_conf}  iou: {args.yolo_iou}  max_det: {args.yolo_max_det}")
        if args.table_obb_model:
            table_obb_conf = args.table_obb_conf if args.table_obb_conf is not None else args.yolo_conf
            table_obb_iou = args.table_obb_iou if args.table_obb_iou is not None else args.yolo_iou
            print(
                f"Table OBB hybrid: model={args.table_obb_model} "
                f"conf={table_obb_conf} iou={table_obb_iou}"
            )
            if args.table_obb_max_det and int(args.table_obb_max_det) > 0:
                print(f"Table OBB raw filter: top_k={int(args.table_obb_max_det)}")
            if args.table_obb_raw_min_conf is not None:
                print(f"Table OBB raw filter: min_conf>={float(args.table_obb_raw_min_conf)}")
            if args.table_obb_debug_raw_overlay or args.table_obb_debug_jsonl:
                print(
                    f"Table OBB debug: raw_overlay={args.table_obb_debug_raw_overlay} "
                    f"jsonl={args.table_obb_debug_jsonl}"
                )
            table_new_conf_create = args.table_new_conf_create if args.table_new_conf_create is not None else args.conf_create
            table_new_min_bbox_area = args.table_new_min_bbox_area if args.table_new_min_bbox_area is not None else args.table_min_bbox_area
            table_new_min_bbox_minside = args.table_new_min_bbox_minside if args.table_new_min_bbox_minside is not None else args.table_min_bbox_minside
            print(
                f"Table anti-phantom: new_conf>={table_new_conf_create} "
                f"new_min_area={table_new_min_bbox_area} new_min_minside={table_new_min_bbox_minside} "
                f"confirm_frames={args.table_new_confirm_frames} "
                f"suppress_iou>={args.table_new_suppress_iou} "
                f"suppress_center_dist<={args.table_new_suppress_center_dist_px}px"
            )
            if args.table_protect_existing_tracks or args.table_recover_lost_tracks:
                print(
                    f"Table continuity: protect_existing={args.table_protect_existing_tracks} "
                    f"recover_lost={args.table_recover_lost_tracks} "
                    f"lost_ttl={args.table_lost_track_ttl}"
                )
            if args.table_recover_lost_tracks and float(args.table_birth_block_near_lost_dist) > 0.0:
                print(
                    f"Table birth suppression near lost: dist<={float(args.table_birth_block_near_lost_dist)}px "
                    f"lost_age<={int(args.table_birth_block_near_lost_frames) if int(args.table_birth_block_near_lost_frames) > 0 else 'recoverable_ttl'}"
                )
            if float(args.table_angle_deadband_deg) > 0.0:
                print(
                    f"Table angle hysteresis: deadband={float(args.table_angle_deadband_deg)}deg"
                )
            if int(args.table_render_grace_frames) > 0:
                print(
                    f"Table render grace: frames={int(args.table_render_grace_frames)}"
                )
            if (
                int(args.table_static_hold_frames) > 0
                and float(args.table_static_hold_center_px) > 0.0
                and float(args.table_static_hold_angle_deg) > 0.0
                and float(args.table_static_hold_area_frac) > 0.0
            ):
                print(
                    f"Table static hold: frames>={int(args.table_static_hold_frames)} "
                    f"center<{float(args.table_static_hold_center_px)}px "
                    f"angle<{float(args.table_static_hold_angle_deg)}deg "
                    f"area<{float(args.table_static_hold_area_frac)}"
                )
        print(
            f"Tracking: ttl={args.track_ttl_frames} conf_create={args.conf_create} conf_keep={args.conf_keep} "
            f"reacquire_age={args.reacquire_max_age} reacquire_dist={args.reacquire_max_dist} reacquire_iou={args.reacquire_min_iou} "
            f"chairs_no_ghost={args.chairs_no_ghost}"
        )
        print(
            f"Person filter: mode={args.person_filter_mode} area=[{args.person_min_area},{args.person_max_area}] "
            f"h_min={args.person_min_height} ar_wh=[{args.person_min_ar_wh},{args.person_max_ar_wh}] "
            f"max_ar_sym={args.person_max_ar} excl_right={args.person_excl_right_frac} "
            f"excl_rb=({args.person_excl_rb_right_frac},{args.person_excl_rb_bottom_frac}) "
            f"person_conf_override={args.person_conf_override} static_window={args.person_static_window} "
            f"static_max_delta={args.person_static_max_delta}"
        )
        if args.table_refine_every > 0:
            print(
                f"Table SAM Refinement: ENABLED every {args.table_refine_every} frames "
                f"(max_tables={args.table_refine_max}, margin={args.table_refine_margin}px)"
            )
        else:
            print("Table SAM Refinement: DISABLED (--table-refine-every 0)")
        print(
            f"Table motion state: shift_px>{args.table_motion_shift_px} iou<{args.table_motion_iou_min} "
            f"area_change>{args.table_motion_area_change} stable_frames={args.table_stable_frames}"
        )
        if args.no_ghosting:
            print("Ghosting: disabled")
    else:
        print(f"SAM2.1 Config: {args.sam_config}")
        print(f"SAM2.1 Checkpoint: {args.sam_checkpoint}")
    print(f"Device: {device}")
    if args.camera is not None:
        print(
            f"Camera input: index={args.camera} req_width={args.camera_width} "
            f"req_height={args.camera_height} camera_rotate={args.camera_rotate} "
            f"display_rotate={args.display_rotate}"
        )
    if args.show_table_ids:
        print("Overlay debug: show_table_ids=True")
        if args.save_live_frame:
            print(
                f"Live frame capture: save_path={args.save_live_frame} "
                f"exit_after_save={args.exit_after_saving_live_frame}"
            )
    if crop_set_count == 4:
        print(f"Input crop: enabled x={args.crop_x} y={args.crop_y} w={args.crop_w} h={args.crop_h}")
    else:
        print("Input crop: disabled")
    print(f"Table area filter: [{args.table_min_area}, {args.table_max_area}] px")
    print(f"Chair area filter: [{args.chair_min_area}, {args.chair_max_area}] px")
    print(f"Output: {args.out}")
    print(f"=====================================")
    pipeline = VisionPipeline(
        sam3_config_path=args.sam_config,
        sam3_checkpoint_path=args.sam_checkpoint,
        homography_matrix=H,
        device=device,
        table_min_area=args.table_min_area,
        table_max_area=args.table_max_area,
        chair_min_area=args.chair_min_area,
        chair_max_area=args.chair_max_area,
        debug_dir=args.debug_dir,
        proposals_mode=args.auto_proposals,
        yolo_model=args.yolo_model,
        yolo_conf=args.yolo_conf,
        yolo_iou=args.yolo_iou,
        table_obb_model=args.table_obb_model,
        table_obb_conf=args.table_obb_conf,
        table_obb_iou=args.table_obb_iou,
        table_obb_max_det=args.table_obb_max_det,
        table_obb_raw_min_conf=args.table_obb_raw_min_conf,
        table_obb_debug_raw_overlay=args.table_obb_debug_raw_overlay,
        table_obb_debug_jsonl=args.table_obb_debug_jsonl,
        yolo_max_det=args.yolo_max_det,
        track_ttl_frames=args.track_ttl_frames,
        conf_create=args.conf_create,
        conf_keep=args.conf_keep,
        reacquire_max_age=args.reacquire_max_age,
        reacquire_max_dist=args.reacquire_max_dist,
        reacquire_min_iou=args.reacquire_min_iou,
        chairs_no_ghost=args.chairs_no_ghost,
        no_ghosting=args.no_ghosting,
        table_min_area_frac=args.table_min_area_frac,
        table_min_w_frac=args.table_min_w_frac,
        table_min_h_frac=args.table_min_h_frac,
        person_min_conf=args.person_min_conf,
        person_min_iou=args.person_min_iou,
        person_max_dist=args.person_max_dist,
        person_ttl=args.person_ttl,
        person_min_area=args.person_min_area,
        person_max_area=args.person_max_area,
        person_max_ar=args.person_max_ar,
        person_min_height=args.person_min_height,
        person_min_ar_wh=args.person_min_ar_wh,
        person_max_ar_wh=args.person_max_ar_wh,
        person_excl_right_frac=args.person_excl_right_frac,
        person_excl_rb_right_frac=args.person_excl_rb_right_frac,
        person_excl_rb_bottom_frac=args.person_excl_rb_bottom_frac,
        person_conf_override=args.person_conf_override,
        person_static_window=args.person_static_window,
        person_static_max_delta=args.person_static_max_delta,
        person_filter_mode=args.person_filter_mode,
        overlay_style=args.overlay_style,
        table_refine_every=args.table_refine_every,
        table_refine_max=args.table_refine_max,
        table_refine_margin=args.table_refine_margin,
        table_motion_shift_px=args.table_motion_shift_px,
        table_motion_iou_min=args.table_motion_iou_min,
        table_motion_area_change=args.table_motion_area_change,
        table_stable_frames=args.table_stable_frames,
        table_min_bbox_area=args.table_min_bbox_area,
        table_min_bbox_minside=args.table_min_bbox_minside,
        table_new_conf_create=args.table_new_conf_create,
        table_new_min_bbox_area=args.table_new_min_bbox_area,
        table_new_min_bbox_minside=args.table_new_min_bbox_minside,
        table_new_confirm_frames=args.table_new_confirm_frames,
        table_new_suppress_iou=args.table_new_suppress_iou,
        table_new_suppress_center_dist_px=args.table_new_suppress_center_dist_px,
        table_protect_existing_tracks=args.table_protect_existing_tracks,
        table_recover_lost_tracks=args.table_recover_lost_tracks,
        table_lost_track_ttl=args.table_lost_track_ttl,
        table_birth_block_near_lost_dist=args.table_birth_block_near_lost_dist,
        table_birth_block_near_lost_frames=args.table_birth_block_near_lost_frames,
        table_angle_deadband_deg=args.table_angle_deadband_deg,
        table_render_grace_frames=args.table_render_grace_frames,
        table_static_hold_frames=args.table_static_hold_frames,
        table_static_hold_center_px=args.table_static_hold_center_px,
        table_static_hold_angle_deg=args.table_static_hold_angle_deg,
        table_static_hold_area_frac=args.table_static_hold_area_frac,
        crop_x=args.crop_x,
        crop_y=args.crop_y,
        crop_w=args.crop_w,
        crop_h=args.crop_h,
        camera_rotate=args.camera_rotate,
        display_rotate=args.display_rotate,
        camera_width=args.camera_width,
        camera_height=args.camera_height,
        save_live_frame_path=args.save_live_frame,
        exit_after_saving_live_frame=args.exit_after_saving_live_frame,
        show_table_ids=args.show_table_ids,
    )
    
    # Process input
    if args.video:
        print(f"Processing video: {args.video}")
        pipeline.process_video_to_jsonl(
            video_path=args.video,
            output_jsonl=args.out,
            max_frames=args.max_frames,
            flush_every=args.flush_every,
        )
    elif args.camera is not None:
        print(f"Processing camera stream: {args.camera}")
        pipeline.process_camera_stream(
            camera_index=args.camera,
            output_jsonl=args.out,
            display=not args.no_display,
            projector_display=args.projector_display,
            projector_monitor=args.projector_monitor,
            flush_every=args.flush_every,
        )
    else:  # image-dir
        print(f"Processing image directory: {args.image_dir}")
        
        # Check for --auto-proposals mode
        if args.auto_proposals:
            proposal_mode = "bgsub" if args.auto_proposals == "furniture" else args.auto_proposals
            if args.auto_proposals == "furniture":
                print("Using auto-proposals mode 'furniture' as alias for 'bgsub'")
            else:
                print(f"Using auto-proposals mode: {proposal_mode}")

            # Load proposal/classification config
            bgsub_config = vision_config.get("bgsub", {})
            classification_config = vision_config.get("classification", {})

            # Build dark proposer config from CLI arguments
            dark_config = vision_config.get("dark", {})
            if args.dark_fixed_thresh is not None:
                dark_config["fixed_thresh"] = args.dark_fixed_thresh
            if args.dark_max_area_frac is not None:
                dark_config["max_area_frac"] = args.dark_max_area_frac
            if args.dark_no_drop_border:
                dark_config["drop_border_touching"] = False
            if args.roi_bbox:
                dark_config["roi_bbox_px"] = list(args.roi_bbox)

            # Process with auto-proposals (proposer selection happens in VisionPipeline)
            pipeline.process_image_dir_with_proposals(
                image_dir=args.image_dir,
                output_jsonl=args.out,
                proposal_mode=proposal_mode,
                proposal_config={"bgsub": bgsub_config, "dark": dark_config},
                fps_sim=args.fps_sim,
                table_area_threshold=classification_config.get("table_threshold_area", 8000.0),
                rectangularity_threshold=classification_config.get("rectangularity_threshold", 0.65),
                max_tracking_distance=classification_config.get("max_tracking_distance", 150.0),
                overlay_out_dir=args.overlay_out_dir,
                overlay_every=args.overlay_every,
                max_frames=args.max_frames,
                flush_every=args.flush_every,
                debug=args.debug_dir is not None,
            )
        else:
            # Parse initial boxes if provided
            boxes_init = None
            box_labels = None
            
            # Priority: --boxes-init > --auto-init-boxes > --init-boxes
            if args.boxes_init:
                if args.auto_init_boxes:
                    print("WARNING: Both --boxes-init and --auto-init-boxes specified. Using --boxes-init (has priority).")
                # Check if it's a JSON file or string format
                if args.boxes_init.endswith(".json"):
                    boxes_init, box_labels = load_boxes_with_labels_from_json(args.boxes_init)
                    print(f"Loaded {len(boxes_init)} initial boxes from JSON: {args.boxes_init}")
                    if box_labels:
                        from collections import Counter
                        label_counts = Counter(box_labels)
                        print(f"  Labels: {dict(label_counts)}")
                else:
                    boxes_init = parse_boxes(args.boxes_init)
                    print(f"Using {len(boxes_init)} initial boxes from --boxes-init")
            elif args.auto_init_boxes:
                # Auto-initialize boxes with YOLO detector
                first_frame = load_first_frame(
                    image_dir=args.image_dir,
                    video_path=None,  # Only image-dir mode supports auto-init in this context
                    camera_index=None
                )
                
                if first_frame is not None:
                    detector_classes = map_detector_classes_to_coco(args.detector_classes)
                    boxes_init, box_labels = auto_init_boxes_with_yolo(
                        frame_bgr=first_frame,
                        detector_model=args.detector_model,
                        detector_classes=detector_classes,
                        device=device,
                        output_json_path=args.auto_init_out,
                        debug_overlay_path="data/vision/debug/auto_init_boxes.png"
                    )
                    
                    if len(boxes_init) > 0:
                        print(f"Auto-initialized {len(boxes_init)} boxes with YOLO")
                        from collections import Counter
                        label_counts = Counter(box_labels)
                        print(f"  Labels: {dict(label_counts)}")
                else:
                    print("ERROR: Could not load first frame for auto-init")
            
            pipeline.process_image_dir_to_jsonl(
                image_dir=args.image_dir,
                output_jsonl=args.out,
                fps_sim=args.fps_sim,
                boxes_init=boxes_init,
                box_labels=box_labels,
                init_boxes=args.init_boxes,
                overlay_out_dir=args.overlay_out_dir,
                overlay_every=args.overlay_every,
                debug_dump=args.debug_dump,
                refine_every=args.refine_every,
                box_margin_px=args.box_margin_px,
                max_frames=args.max_frames,
                flush_every=args.flush_every,
            )
    
    print(f"\nDone. Output written to {args.out}")


if __name__ == "__main__":
    main()
