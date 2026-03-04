"""
YOLO-based object detection for furniture and people.

Uses ultralytics YOLOv8 for detecting chairs, tables, and people.
"""

from typing import List, Dict, Optional
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
