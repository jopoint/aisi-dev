"""
Debug tool for visualizing BGSubProposer region proposals.

Example usage:
    python -m src.vision.tools.debug_bgsub_proposals --image-dir data/vision/synth_seq --out-dir data/vision/debug/bgsub --max-frames 30
"""

import argparse
import cv2
import numpy as np
from pathlib import Path
import sys

from src.vision.detection.proposals_bgsub import BGSubProposer


def main():
    parser = argparse.ArgumentParser(description="Debug BGSubProposer region proposals.")
    parser.add_argument("--image-dir", required=True, help="Input image directory (*.jpg, *.png)")
    parser.add_argument("--out-dir", required=True, help="Output directory for debug frames")
    parser.add_argument("--max-frames", type=int, default=30, help="Maximum frames to process (default: 30)")
    
    # BGSub parameters
    parser.add_argument("--history", type=int, default=200, help="BGSub history (default: 200)")
    parser.add_argument("--var-threshold", type=int, default=16, help="BGSub variance threshold (default: 16)")
    parser.add_argument("--min-area", type=int, default=1500, help="Minimum proposal area (default: 1500)")
    parser.add_argument("--max-area", type=int, default=200000, help="Maximum proposal area (default: 200000)")
    
    args = parser.parse_args()
    
    # Load image files
    img_dir = Path(args.image_dir)
    if not img_dir.exists():
        print(f"ERROR: Image directory not found: {args.image_dir}")
        sys.exit(1)
    
    image_files = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")))
    
    if len(image_files) == 0:
        print(f"ERROR: No .jpg or .png files found in {args.image_dir}")
        sys.exit(1)
    
    print(f"Found {len(image_files)} images in {args.image_dir}")
    
    # Create output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {args.out_dir}")
    
    # Initialize BGSubProposer
    proposer = BGSubProposer(
        history=args.history,
        var_threshold=args.var_threshold,
        detect_shadows=False,
        min_area=args.min_area,
        max_area=args.max_area,
    )
    
    print(f"\n=== BGSubProposer Configuration ===")
    print(f"History: {args.history}")
    print(f"Variance threshold: {args.var_threshold}")
    print(f"Min area: {args.min_area} px")
    print(f"Max area: {args.max_area} px")
    print(f"===================================\n")
    
    # Process frames
    max_frames = min(args.max_frames, len(image_files))
    
    for frame_idx in range(max_frames):
        img_path = image_files[frame_idx]
        
        # Load frame
        frame = cv2.imread(str(img_path))
        if frame is None:
            print(f"WARNING: Could not load {img_path}, skipping.")
            continue
        
        # Get proposals
        proposals = proposer.propose(frame, debug=False)
        
        # Log
        print(f"Frame {frame_idx}: {len(proposals)} boxes")
        
        # Draw proposals on frame
        vis = frame.copy()
        
        for idx, proposal in enumerate(proposals):
            bbox = proposal["bbox_px"]
            score = proposal["score"]
            
            x1, y1, x2, y2 = [int(v) for v in bbox]
            
            # Color by score (green = high, red = low)
            color = (0, int(255 * score), int(255 * (1 - score)))
            
            # Draw rectangle
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            
            # Draw index and score
            label = f"{idx}: {score:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # Background for text
            cv2.rectangle(vis, (x1, y1 - label_size[1] - 8), (x1 + label_size[0] + 4, y1), color, -1)
            cv2.putText(vis, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Draw frame info at top left
        info_text = f"Frame {frame_idx}, Boxes={len(proposals)}"
        cv2.rectangle(vis, (0, 0), (400, 40), (0, 0, 0), -1)
        cv2.putText(vis, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # Save frame
        out_path = out_dir / f"frame_{frame_idx:04d}.png"
        cv2.imwrite(str(out_path), vis)
    
    print(f"\nProcessed {max_frames} frames.")
    print(f"Debug frames saved to: {args.out_dir}")


if __name__ == "__main__":
    main()
