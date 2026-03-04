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
        choices=["bgsub", "dark", "furniture"],
        help=(
            "Enable automatic region proposals mode. "
            "Modes: bgsub, dark, furniture (alias for bgsub)."
        ),
    )
    
    # Dark proposer options
    parser.add_argument("--dark-fixed-thresh", type=int, default=None, help="HSV V-channel threshold for dark objects (0-255).")
    parser.add_argument("--dark-max-area-frac", type=float, default=None, help="Max component area as fraction of frame area.")
    parser.add_argument("--dark-no-drop-border", action="store_true", help="Do NOT drop components touching image borders (default: drop them).")
    parser.add_argument("--roi-bbox", type=int, nargs=4, metavar=("X1", "Y1", "X2", "Y2"), help="ROI bounding box in pixels [x1 y1 x2 y2] (optional).")
    
    # Processing options (image-dir)
    parser.add_argument("--fps-sim", type=float, default=10.0, help="Simulated FPS for timestamps (image-dir mode).")
    parser.add_argument("--overlay-out-dir", help="Optional directory to save overlay frames (image-dir only).")
    parser.add_argument("--overlay-every", type=int, default=10, help="Save overlay every N frames (default 10).")
    parser.add_argument("--debug-dump", action="store_true", help="Save segmentation masks as individual PNGs (image-dir only).")
    parser.add_argument("--refine-every", type=int, default=10, help="Re-segment every N frames (default 10, 0 = no refinement).")
    parser.add_argument("--box-margin-px", type=int, default=40, help="Margin in pixels to expand boxes during refinement (default 40).")
    
    # General options
    parser.add_argument("--debug-dir", help="Optional directory for debug overlays.")
    parser.add_argument("--max-frames", type=int, help="Maximum frames to process.")
    parser.add_argument("--flush-every", type=int, default=10, help="Flush and fsync JSONL output every N frames (default 10).")
    parser.add_argument("--no-display", action="store_true", help="Disable live display (camera only).")
    
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
        parser.error("--auto-proposals is only supported with --image-dir.")
    if args.auto_proposals and (args.boxes_init or args.init_boxes or args.auto_init_boxes):
        parser.error("--auto-proposals cannot be used with manual box initialization (--boxes-init, --init-boxes, --auto-init-boxes).")
    if args.overlay_out_dir and args.image_dir is None:
        parser.error("--overlay-out-dir is only supported with --image-dir.")
    if args.flush_every < 1:
        parser.error("--flush-every must be >= 1.")
    
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
    
    # Print startup configuration
    print(f"\n=== Vision Pipeline Configuration ===")
    print(f"SAM2.1 Config: {args.sam_config}")
    print(f"SAM2.1 Checkpoint: {args.sam_checkpoint}")
    print(f"Device: {device}")
    print(f"Table area filter: [{args.table_min_area}, {args.table_max_area}] px²")
    print(f"Chair area filter: [{args.chair_min_area}, {args.chair_max_area}] px²")
    print(f"Output: {args.out}")
    print(f"=====================================\n")
    pipeline = VisionPipeline(
        sam3_config_path=args.sam_config,
        sam3_checkpoint_path=args.sam_checkpoint,
        homography_matrix=H,
        device=device,
        table_min_area=args.table_min_area,
        table_max_area=args.table_max_area,
        chair_min_area=args.chair_min_area,
        chair_max_area=args.chair_max_area,
        debug_dir=args.debug_dir
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
