"""
SAM3 segmentation wrapper for SAM2.1 text-prompt based object detection.

This module wraps the official SAM2 Predictor from facebookresearch/sam2
and provides a simple API for text-based segmentation.
"""

import cv2
import numpy as np
from pathlib import Path
import importlib.resources
import importlib.util
import sys


def _find_sam2_config(model_variant: str = "hiera_large") -> Path:
    """
    Find SAM2 config file within the installed sam2 package.
    
    Args:
        model_variant: Model variant name (e.g., "hiera_large", "hiera_small")
    
    Returns:
        Path to config file
    
    Raises:
        FileNotFoundError: If config cannot be found
    """
    try:
        # Try to find sam2 package and its configs directory
        import sam2
        sam2_path = Path(sam2.__file__).parent
        configs_dir = sam2_path / "configs"
        
        if not configs_dir.exists():
            raise FileNotFoundError(f"sam2 configs directory not found: {configs_dir}")
        
        # Look for config file matching the model variant
        # Try patterns like "sam2.1_hiera_large.yaml", "hiera_large.yaml"
        candidates = [
            f"sam2.1_{model_variant}.yaml",
            f"{model_variant}.yaml",
        ]
        
        for candidate in candidates:
            config_path = configs_dir / candidate
            if config_path.exists():
                return config_path
        
        # List available configs
        available = list(configs_dir.glob("*.yaml"))
        raise FileNotFoundError(
            f"Config for model variant '{model_variant}' not found in {configs_dir}.\n"
            f"Available configs: {[c.name for c in available]}"
        )
    
    except ImportError:
        raise RuntimeError(
            "sam2 package not installed. Install from facebookresearch/sam2 repo:\n"
            "  pip install git+https://github.com/facebookresearch/sam2.git"
        )


class SAM3Segmenter:
    """
    Wrapper for SAM2.1 text-prompt segmentation.
    
    Args:
        config_path: Path to model config file. If None, auto-finds from sam2 package.
        model_variant: Model variant name (e.g., "hiera_large", "hiera_small").
                      Used to find default config if config_path is None.
        checkpoint_path: Path to SAM2.1 checkpoint file. If None, uses default.
        device: "cuda" or "cpu"
    """
    
    def __init__(
        self,
        config_path: str | None = None,
        model_variant: str = "hiera_large",
        checkpoint_path: str | None = None,
        device: str = "cuda"
    ):
        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor
            self._build_sam = build_sam2
            self._predictor_class = SAM2ImagePredictor
        except ImportError as e:
            raise RuntimeError(
                "SAM2 not available. Install from facebookresearch/sam2 repo:\n"
                "  pip install git+https://github.com/facebookresearch/sam2.git"
            ) from e
        
        self.device = device
        
        # Resolve config path
        if config_path is None:
            config_path = _find_sam2_config(model_variant)
        else:
            config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        self.config_path = config_path.absolute()
        
        # Resolve checkpoint path
        if checkpoint_path is None:
            checkpoint_path = Path("checkpoints/sam2.1_hiera_large.pt")
        else:
            checkpoint_path = Path(checkpoint_path)
        
        self.checkpoint_path = checkpoint_path.absolute()
        
        # Validate checkpoint exists
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f"Checkpoint not found: {self.checkpoint_path}\n"
                f"Download SAM2.1 weights from: "
                f"https://github.com/facebookresearch/segment-anything-2"
            )
        
        # Build model
        print(f"Building SAM2.1 model...")
        print(f"  Config: {self.config_path}")
        print(f"  Checkpoint: {self.checkpoint_path}")
        print(f"  Device: {device}")
        
        model = self._build_sam(config_file=str(self.config_path), ckpt_path=str(self.checkpoint_path), device=device)
        self.predictor = self._predictor_class(model)
        
        print(f"✓ SAM2Segmenter initialized successfully")
    
    def segment_image(self, frame_bgr: np.ndarray, prompts: list[str], debug_dir: str | None = None) -> dict[str, list[dict]]:
        """
        Segment an image using text prompts.
        
        Args:
            frame_bgr: Input image in BGR format (OpenCV format)
            prompts: List of text prompts (e.g., ["table", "chair"])
            debug_dir: Optional directory to save debug overlays
        
        Returns:
            dict mapping each prompt to a list of mask_dict:
                - mask: (H, W) boolean numpy array
                - score: float confidence score
                - bbox_px: [x1, y1, x2, y2] in pixels
        """
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w = frame_bgr.shape[:2]
        
        # Set image
        self.predictor.set_image(frame_rgb)
        
        results = {}
        
        for prompt in prompts:
            # Call text-based prediction
            # Note: SAM2 doesn't natively support text prompts - it needs point/box prompts
            # For SAM3 or a CLIP+SAM2 pipeline, adjust API accordingly
            # Here we show a placeholder that would work with a text-enabled SAM variant
            try:
                # Attempt text-based prediction (adjust to actual API)
                # If SAM3 has predict_text method:
                masks, scores, logits = self._predict_with_text(prompt)
            except AttributeError:
                # Fallback: SAM2 requires point/box prompts, not text
                # For a real implementation, integrate GROUNDING-DINO or similar for text→box
                print(f"WARNING: Text prompt '{prompt}' not directly supported. Skipping.")
                results[prompt] = []
                continue
            
            mask_dicts = []
            for mask, score in zip(masks, scores):
                # Convert mask to boolean
                mask_bool = mask.astype(bool)
                
                # Compute bounding box from mask
                bbox = self._mask_to_bbox(mask_bool)
                
                mask_dicts.append({
                    "mask": mask_bool,
                    "score": float(score),
                    "bbox_px": bbox,
                })
            
            results[prompt] = mask_dicts
            
            # Save debug overlay if requested
            if debug_dir is not None and len(mask_dicts) > 0:
                self._save_debug_overlay(frame_bgr, mask_dicts, prompt, debug_dir)
        
        return results

    def segment_with_boxes(self, frame_bgr: np.ndarray, boxes_px: list[list[int]] | None = None, boxes: list[list[int]] | None = None) -> list[dict]:
        """Segment an image using box prompts with SAM2 predictor.

        Args:
            frame_bgr: Input image in BGR format.
            boxes_px: List of boxes [[x1,y1,x2,y2], ...] in pixel coordinates.
            boxes: Alias for boxes_px.

        Returns:
            List of mask_dict with keys: mask, score, bbox_px.
        """
        if boxes_px is None:
            boxes_px = boxes or []
        if not boxes_px:
            return []

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self.predictor.set_image(frame_rgb)

        results: list[dict] = []
        for box in boxes_px:
            if len(box) != 4:
                raise ValueError(f"Invalid box format {box}; expected [x1,y1,x2,y2]")

            x1, y1, x2, y2 = [int(v) for v in box]
            box_np = np.array([[x1, y1, x2, y2]], dtype=np.float32)

            masks, scores, _ = self.predictor.predict(
                point_coords=None,
                point_labels=None,
                box=box_np,
                multimask_output=False,
            )

            if masks is None or len(masks) == 0:
                continue

            mask = masks[0].astype(bool)
            score = float(scores[0]) if scores is not None and len(scores) > 0 else 0.0

            results.append({
                "mask": mask,
                "score": score,
                "bbox_px": [x1, y1, x2, y2],
            })

        return results
    
    def _predict_with_text(self, text: str):
        """
        Placeholder for text-based prediction.
        
        For SAM3 with native text support, this would call predictor.predict_text(text).
        For SAM2, you would integrate CLIP or Grounding-DINO to convert text→boxes,
        then call predictor.predict() with box prompts.
        
        Returns:
            masks: (N, H, W) array
            scores: (N,) array
            logits: (N, H, W) array
        """
        # This is a placeholder implementation
        # Replace with actual SAM3 text API when available
        raise NotImplementedError(
            "SAM2/SAM3 text-prompt API not implemented. "
            "Integrate Grounding-DINO or CLIP for text→box conversion, "
            "then use predictor.predict() with box prompts."
        )
    
    def _mask_to_bbox(self, mask: np.ndarray) -> list[int]:
        """Compute bounding box [x1, y1, x2, y2] from boolean mask."""
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        if not rows.any() or not cols.any():
            return [0, 0, 0, 0]
        y1, y2 = np.where(rows)[0][[0, -1]]
        x1, x2 = np.where(cols)[0][[0, -1]]
        return [int(x1), int(y1), int(x2), int(y2)]
    
    def _save_debug_overlay(self, frame_bgr: np.ndarray, mask_dicts: list[dict], prompt: str, debug_dir: str):
        """Save debug overlay with colored masks and bounding boxes."""
        debug_path = Path(debug_dir)
        debug_path.mkdir(parents=True, exist_ok=True)
        
        overlay = frame_bgr.copy()
        
        # Color palette for multiple masks
        colors = [
            (0, 255, 0),    # green
            (255, 0, 0),    # blue
            (0, 255, 255),  # yellow
            (255, 0, 255),  # magenta
            (255, 128, 0),  # orange
        ]
        
        for i, mask_dict in enumerate(mask_dicts):
            mask = mask_dict["mask"]
            score = mask_dict["score"]
            bbox = mask_dict["bbox_px"]
            color = colors[i % len(colors)]
            
            # Draw colored mask
            overlay[mask] = color
            
            # Draw bounding box
            x1, y1, x2, y2 = bbox
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            
            # Draw score text
            label = f"{prompt} {score:.2f}"
            cv2.putText(overlay, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Blend with original
        alpha = 0.5
        out = cv2.addWeighted(overlay, alpha, frame_bgr, 1.0 - alpha, 0)
        
        out_path = debug_path / f"sam3_{prompt}.png"
        cv2.imwrite(str(out_path), out)
        print(f"Debug overlay saved: {out_path}")
