"""
YOLO-based object detection for furniture and people.

Uses ultralytics YOLOv8 for detecting chairs, tables, and people.
"""

from typing import List, Dict, Optional
import math
import numpy as np
import cv2


class YOLODetector:
    """
    YOLO-based object detector using ultralytics.
    
    Detects and returns furniture (chairs, tables) and people with bounding boxes.
    Applies label mapping to normalize YOLO class names.
    """
    
    # Label mapping: YOLO class name -> normalized name
    LABEL_MAPPING = {
        "dining table": "table",
        "chair": "chair",
        "person": "person"
    }
    
    def __init__(
        self,
        model: str = "yolov8s.pt",
        device: str = "cuda",
        conf: float = 0.25,
        iou: float = 0.5,
        classes: Optional[List[str]] = None
    ):
        """
        Initialize YOLO detector.
        
        Args:
            model: Path to YOLO model or model name (e.g., "yolov8s.pt", "yolov8m.pt")
            device: Device to run inference on ("cuda" or "cpu")
            conf: Confidence threshold (0.0-1.0)
            iou: IoU threshold for NMS (0.0-1.0)
            classes: Optional list of class labels to filter (after mapping).
                If None, no class filter is applied.
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics not found. Install with: pip install ultralytics"
            )
        
        self.model = YOLO(model)
        self.device = device
        self.conf = conf
        self.iou = iou
        
        self.classes = classes
        self._allowed_labels = None
        if classes is not None:
            self._allowed_labels = {self.LABEL_MAPPING.get(label, label) for label in classes}
        
        print(f"\n=== YOLODetector Initialized ===")
        print(f"Model: {model}")
        print(f"Device: {device}")
        print(f"Confidence threshold: {conf}")
        print(f"IoU threshold: {iou}")
        print(f"Filtering classes: {self.classes if self.classes is not None else 'None (no filter)'}")
        print(f"===================================\n")
    
    def detect(self, frame_bgr: np.ndarray) -> List[Dict]:
        """
        Detect objects in a BGR frame.
        
        Args:
            frame_bgr: Input frame in BGR format (OpenCV default)
        
        Returns:
            List of detections, each dict containing:
                - "label": str (normalized label: "chair", "table", or "person")
                - "bbox_px": [x1, y1, x2, y2] (int coordinates)
                - "score": float (confidence score)
        """
        # Convert BGR to RGB for YOLO
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Run inference
        results = self.model.predict(
            frame_rgb,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False
        )
        
        # Parse results
        detections = []
        
        if len(results) > 0:
            result = results[0]  # Single image inference
            
            # Extract boxes, classes, and confidences
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
                confidences = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy().astype(int)
                
                # Get class names from model
                class_names = result.names  # Dict: {class_id: class_name}
                
                for i in range(len(boxes)):
                    class_id = class_ids[i]
                    class_name = class_names[class_id]
                    confidence = float(confidences[i])
                    
                    # Apply label mapping
                    mapped_label = self.LABEL_MAPPING.get(class_name, class_name)
                    
                    # Filter by classes (if configured)
                    if self._allowed_labels is not None and mapped_label not in self._allowed_labels:
                        continue
                    
                    # Extract bbox as integers
                    x1, y1, x2, y2 = boxes[i]
                    bbox_px = [int(x1), int(y1), int(x2), int(y2)]
                    
                    detections.append({
                        "label": mapped_label,
                        "bbox_px": bbox_px,
                        "score": confidence
                    })
        
        return detections
    
    def detect_and_visualize(
        self,
        frame_bgr: np.ndarray,
        output_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Detect objects and create visualization overlay.
        
        Args:
            frame_bgr: Input frame in BGR format
            output_path: Optional path to save visualization
        
        Returns:
            Annotated frame with bounding boxes and labels
        """
        detections = self.detect(frame_bgr)
        
        # Create copy for drawing
        overlay = frame_bgr.copy()
        
        # Color mapping
        color_map = {
            "chair": (255, 0, 255),    # Magenta
            "table": (0, 255, 255),    # Cyan
            "person": (0, 255, 0)      # Green
        }
        
        for det in detections:
            label = det["label"]
            bbox = det["bbox_px"]
            score = det["score"]
            
            x1, y1, x2, y2 = bbox
            color = color_map.get(label, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with background
            text = f"{label}: {score:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            
            (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            
            # Background rectangle
            bg_x1, bg_y1 = x1, y1 - text_h - baseline - 5
            bg_x2, bg_y2 = x1 + text_w + 5, y1
            
            # Ensure background is within frame
            bg_y1 = max(0, bg_y1)
            
            cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
            cv2.putText(overlay, text, (x1 + 2, y1 - 5), font, font_scale, color, thickness)
        
        # Save if output path provided
        if output_path:
            cv2.imwrite(output_path, overlay)
            print(f"Saved visualization to {output_path}")
        
        return overlay


class YOLOTableOBBDetector:
    """Table-only OBB detector using an Ultralytics OBB model."""

    def __init__(
        self,
        model: str,
        device: str = "cuda",
        conf: float = 0.25,
        iou: float = 0.45,
        max_det: int = 80,
        raw_max_det: int = 0,
        raw_min_conf: Optional[float] = None,
    ):
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError("ultralytics not found. Install with: pip install ultralytics")

        self.model = YOLO(model)
        self.device = device
        self.conf = float(conf)
        self.iou = float(iou)
        self.max_det = int(max_det)
        self.raw_max_det = int(raw_max_det)
        self.raw_min_conf = None if raw_min_conf is None else float(raw_min_conf)

        print("\n=== YOLOTableOBBDetector Initialized ===")
        print(f"Model: {model}")
        print(f"Device: {device}")
        print(f"Confidence threshold: {self.conf}")
        print(f"IoU threshold: {self.iou}")
        print(f"Max det: {self.max_det}")
        print(f"Raw table top-k filter: {self.raw_max_det if self.raw_max_det > 0 else 'disabled'}")
        print(f"Raw table min-conf filter: {self.raw_min_conf if self.raw_min_conf is not None else 'disabled'}")
        print("========================================\n")

    @staticmethod
    def _normalize_theta_half_pi(theta_rad: float) -> float:
        theta = float(theta_rad)
        while theta <= -0.5 * math.pi:
            theta += math.pi
        while theta > 0.5 * math.pi:
            theta -= math.pi
        return theta

    @staticmethod
    def _yaw_from_poly(poly_xy: np.ndarray) -> Optional[float]:
        if poly_xy.shape != (4, 2):
            return None
        e01 = poly_xy[1] - poly_xy[0]
        e12 = poly_xy[2] - poly_xy[1]
        len01 = float(np.hypot(e01[0], e01[1]))
        len12 = float(np.hypot(e12[0], e12[1]))
        long_edge = e01 if len01 >= len12 else e12
        if float(np.hypot(long_edge[0], long_edge[1])) < 1e-6:
            return None
        return YOLOTableOBBDetector._normalize_theta_half_pi(math.atan2(float(long_edge[1]), float(long_edge[0])))

    def detect_tables(self, frame_bgr: np.ndarray) -> List[Dict]:
        """Return table detections with bbox + OBB polygon + yaw."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        infer_conf = self.conf if self.raw_min_conf is None else float(self.raw_min_conf)
        results = self.model.predict(
            frame_rgb,
            conf=infer_conf,
            iou=self.iou,
            device=self.device,
            verbose=False,
            max_det=self.max_det,
        )

        detections: List[Dict] = []
        if len(results) == 0:
            return detections

        result = results[0]
        obb = getattr(result, "obb", None)
        if obb is None or len(obb) == 0:
            return detections

        class_names = getattr(result, "names", {}) or {}
        confs = obb.conf.cpu().numpy() if getattr(obb, "conf", None) is not None else np.ones((len(obb),), dtype=np.float32)
        cls_ids = obb.cls.cpu().numpy().astype(int) if getattr(obb, "cls", None) is not None else np.zeros((len(obb),), dtype=np.int32)

        polys = None
        if getattr(obb, "xyxyxyxy", None) is not None:
            polys = obb.xyxyxyxy.cpu().numpy()

        for idx in range(len(obb)):
            cls_id = int(cls_ids[idx])
            class_name = class_names.get(cls_id, str(cls_id))
            mapped_label = YOLODetector.LABEL_MAPPING.get(class_name, class_name)
            # Allow table-only models without explicit class name.
            if mapped_label != "table" and len(class_names) > 1:
                continue

            if polys is None:
                continue
            poly_xy = np.asarray(polys[idx], dtype=np.float32)
            if poly_xy.shape != (4, 2):
                continue

            x_coords = poly_xy[:, 0]
            y_coords = poly_xy[:, 1]
            x1 = int(np.floor(np.min(x_coords)))
            y1 = int(np.floor(np.min(y_coords)))
            x2 = int(np.ceil(np.max(x_coords)))
            y2 = int(np.ceil(np.max(y_coords)))

            center_xy = [float(np.mean(x_coords)), float(np.mean(y_coords))]
            yaw_rad = self._yaw_from_poly(poly_xy)

            detections.append(
                {
                    "label": "table",
                    "bbox_px": [x1, y1, x2, y2],
                    "score": float(confs[idx]),
                    "obb_poly_px": np.round(poly_xy).astype(np.int32).tolist(),
                    "obb_center_px": center_xy,
                    "obb_yaw_rad": float(yaw_rad) if yaw_rad is not None else None,
                }
            )

        if self.raw_min_conf is not None:
            # Keep only raw OBB detections that satisfy the optional table-specific threshold.
            detections = [d for d in detections if float(d.get("score", 0.0)) >= float(self.raw_min_conf)]

        detections.sort(key=lambda d: float(d.get("score", 0.0)), reverse=True)
        if self.raw_max_det > 0:
            # Top-K filter is applied on raw OBB detections before merge/tracking.
            detections = detections[: self.raw_max_det]
        return detections


def main():
    """
    Simple test/demo for YOLODetector.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python yolo_detector.py <image_path> [output_path]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "yolo_detection_output.jpg"
    
    # Load image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Could not load image from {image_path}")
        sys.exit(1)
    
    # Initialize detector
    detector = YOLODetector(
        model="yolov8s.pt",
        device="cuda",
        conf=0.25,
        iou=0.5
    )
    
    # Run detection
    print("Running detection...")
    detections = detector.detect(frame)
    
    print(f"\nFound {len(detections)} objects:")
    for det in detections:
        print(f"  {det['label']}: bbox={det['bbox_px']}, score={det['score']:.3f}")
    
    # Create visualization
    overlay = detector.detect_and_visualize(frame, output_path=output_path)
    
    print(f"\nVisualization saved to {output_path}")


if __name__ == "__main__":
    main()
