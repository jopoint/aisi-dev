"""
Background subtraction-based region proposal generator.
"""
import cv2
import numpy as np
from pathlib import Path


class BGSubProposer:
    """
    Background subtraction-based region proposer using MOG2.
    Returns bounding boxes for foreground objects.
    """
    
    def __init__(
        self,
        history: int = 200,
        var_threshold: int = 16,
        detect_shadows: bool = False,
        min_area: int = 1500,
        max_area: int = 200000,
    ):
        """
        Initialize background subtractor.
        
        Args:
            history: Number of frames for background model
            var_threshold: Threshold on the squared Mahalanobis distance
            detect_shadows: Whether to detect shadows (slower)
            min_area: Minimum contour area to accept
            max_area: Maximum contour area to accept
        """
        self.min_area = min_area
        self.max_area = max_area
        
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history,
            varThreshold=var_threshold,
            detectShadows=detect_shadows,
        )
        
        # Morphology kernel for noise reduction
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
    def propose(self, frame_bgr: np.ndarray, debug: bool = False) -> list[dict]:
        """
        Generate region proposals from foreground mask.
        
        Args:
            frame_bgr: Input frame in BGR format (H, W, 3)
            debug: If True, save debug visualization
            
        Returns:
            List of proposals: [{"bbox_px": [x1, y1, x2, y2], "score": float}, ...]
        """
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame_bgr)
        
        # Threshold to binary
        _, binary = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)
        
        # Morphology: close then open to reduce noise
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, self.kernel, iterations=2)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, self.kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        proposals = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by area
            if area < self.min_area or area > self.max_area:
                continue
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            bbox = [x, y, x + w, y + h]
            
            # Calculate score based on solidity (ratio of contour area to convex hull area)
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0.0
            
            # Alternative: normalized area score
            # score = min(1.0, area / self.max_area)
            
            proposals.append({
                "bbox_px": bbox,
                "score": solidity,
            })
        
        # Sort by score descending
        proposals.sort(key=lambda p: p["score"], reverse=True)
        
        # Debug visualization
        if debug and proposals:
            self._save_debug_image(frame_bgr, proposals, opened)
        
        return proposals
    
    def _save_debug_image(self, frame_bgr: np.ndarray, proposals: list[dict], mask: np.ndarray):
        """Save debug visualization with bounding boxes."""
        debug_dir = Path("data/vision/debug")
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Create visualization: frame + mask overlay + boxes
        vis = frame_bgr.copy()
        
        # Overlay mask in green
        mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        mask_colored[:, :, 1] = mask  # Green channel
        vis = cv2.addWeighted(vis, 0.7, mask_colored, 0.3, 0)
        
        # Draw boxes
        for proposal in proposals:
            x1, y1, x2, y2 = proposal["bbox_px"]
            score = proposal["score"]
            
            # Color by score (green = high, red = low)
            color = (0, int(255 * score), int(255 * (1 - score)))
            
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            
            # Label with score
            label = f"{score:.2f}"
            cv2.putText(
                vis, label, (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
            )
        
        # Save
        output_path = debug_dir / "bgsub_boxes.png"
        cv2.imwrite(str(output_path), vis)
        print(f"Saved BGSub debug overlay to: {output_path}")
