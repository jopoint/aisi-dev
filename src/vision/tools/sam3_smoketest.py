"""
SAM3 segmentation smoke test.

Standalone validation script that segmentation works with visual overlay output.

Usage:
    python src/vision/tools/sam3_smoketest.py \
      --image data/vision/test_frames/usb_1080_tagtest.jpg \
      --out data/vision/debug/sam3_smoketest.png
"""

import os
import argparse
import traceback
import cv2
import numpy as np
from pathlib import Path


def _parse_box(box_str: str) -> list[int]:
    parts = [p.strip() for p in box_str.split(",")]
    if len(parts) != 4:
        raise ValueError(f"Invalid --box '{box_str}', expected format x1,y1,x2,y2")
    try:
        x1, y1, x2, y2 = [int(p) for p in parts]
    except ValueError as exc:
        raise ValueError(f"Invalid --box '{box_str}', coordinates must be integers") from exc
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid --box '{box_str}', require x2>x1 and y2>y1")
    return [x1, y1, x2, y2]


def main():
    """Main smoke test logic."""
    parser = argparse.ArgumentParser(description="SAM3 segmentation smoke test.")
    parser.add_argument("--image", required=True, help="Input image path.")
    parser.add_argument("--out", required=True, help="Output debug image path.")
    parser.add_argument("--config", default=None, help="Path to SAM3 model config (optional).")
    parser.add_argument("--checkpoint", default=None, help="Path to SAM3 checkpoint (optional).")
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None, help="Device (default: auto).")
    parser.add_argument("--box", action="append", default=[], help="Box prompt in format x1,y1,x2,y2 (can be set multiple times).")
    
    args = parser.parse_args()
    
    # Determine device
    if args.device is None:
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
        print(f"Device: auto-detected {device}")
    else:
        device = args.device
        print(f"Device: {device}")
    
    # Load image
    print(f"Loading image: {args.image}")
    frame_bgr = cv2.imread(args.image)
    if frame_bgr is None:
        raise ValueError(f"Could not load image: {args.image}")
    
    h, w = frame_bgr.shape[:2]
    print(f"  Size: {w}x{h}")
    
    # Import SAM3Segmenter
    print("Importing SAM3Segmenter...")
    from src.vision.detection.sam3_segmenter import SAM3Segmenter
    
    # Set default paths if not provided
    config_path = args.config or "configs/sam2/sam2.1_hiera_l.yaml"
    checkpoint_path = args.checkpoint or "checkpoints/sam2.1_hiera_large.pt"

    config_path = str(Path(config_path).resolve())
    checkpoint_path = str(Path(checkpoint_path).resolve())
    
    print(f"Initializing SAM3Segmenter:")
    print(f"  Config: {config_path}")
    print(f"  Checkpoint: {checkpoint_path}")
    
    seg = SAM3Segmenter(
        config_path=config_path,
        checkpoint_path=checkpoint_path,
        device=device
    )
    
    # Segment
    box_prompts = [_parse_box(b) for b in args.box] if args.box else []
    use_box_mode = len(box_prompts) > 0

    if use_box_mode:
        print(f"Running box-prompt segmentation with {len(box_prompts)} box(es)...")
        box_results = seg.segment_with_boxes(frame_bgr, boxes=box_prompts)
        result = {"boxes": box_results}
        top_score = max([m.get("score", 0.0) for m in box_results], default=0.0)
        print("\nSegmentation Results:")
        print(f"  boxes: {len(box_results)} masks, best score: {top_score:.3f}")
    else:
        print(f"Running segmentation for ['table', 'chair']...")
        result = seg.segment_image(frame_bgr, prompts=["table", "chair"])

        # Print results
        print("\nSegmentation Results:")
        for prompt in ["table", "chair"]:
            masks = result.get(prompt, [])
            count = len(masks)
            if count > 0:
                scores = [m.get("score", 0.0) for m in masks]
                best_score = max(scores)
                print(f"  {prompt}: {count} masks, best score: {best_score:.3f}")
            else:
                print(f"  {prompt}: 0 masks")
    
    # Create debug overlay
    print("\nCreating overlay...")
    overlay = frame_bgr.copy()
    
    color_map = {
        "table": (0, 255, 0),    # green
        "chair": (0, 0, 255),    # red (BGR)
        "boxes": (255, 255, 0),  # cyan
    }

    if use_box_mode:
        for i, mask_dict in enumerate(result.get("boxes", [])[:5]):
            mask = mask_dict["mask"]
            score = mask_dict.get("score", 0.0)
            bbox = mask_dict.get("bbox_px", [0, 0, 0, 0])
            color = color_map["boxes"]

            overlay[mask] = color
            x1, y1, x2, y2 = [int(v) for v in bbox]
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                overlay,
                f"box{i} {score:.2f}",
                (x1, max(0, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )
    else:
        mask_count = 0
        for prompt in ["table", "chair"]:
            masks = result.get(prompt, [])
            color = color_map.get(prompt, (128, 128, 128))

            for i, mask_dict in enumerate(masks):
                if mask_count >= 5 * 2:  # max 5 per prompt
                    break

                mask = mask_dict["mask"]
                score = mask_dict.get("score", 0.0)

                # Draw colored mask with alpha blend
                overlay[mask] = color

                # Draw label
                label = f"{prompt} {score:.2f}"
                rows = np.where(mask.any(axis=1))[0]
                if len(rows) > 0:
                    y = int(rows[0])
                    cols = np.where(mask.any(axis=0))[0]
                    if len(cols) > 0:
                        x = int(cols[0])
                        cv2.putText(
                            overlay, label, (x, max(0, y - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
                        )

                mask_count += 1
    
    # Blend overlay with original
    alpha = 0.4
    out_frame = cv2.addWeighted(overlay, alpha, frame_bgr, 1.0 - alpha, 0)
    
    # Add title
    cv2.putText(
        out_frame, f"SAM3 Smoke Test ({device})",
        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2
    )
    
    # Save output
    print(f"Saving to: {args.out}")
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    success = cv2.imwrite(args.out, out_frame)
    if not success:
        raise RuntimeError(f"Failed to write image to {args.out}")
    
    print(f"Saved: {args.out}")
    print("\n✓ SAM3 smoke test passed!")
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTraceback:")
        print(traceback.format_exc())
        exit(1)
