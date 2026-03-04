"""
Extract frames from video file.

Example usage:
    python -m src.vision.tools.video_to_frames --video data/vision/videos/bgsub_test.mp4 --out-dir data/vision/bgsub_frames --max-frames 120 --every-n 1
"""

import argparse
import cv2
import sys
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Extract frames from video file.")
    parser.add_argument("--video", required=True, help="Input video file path")
    parser.add_argument("--out-dir", required=True, help="Output directory for frames")
    parser.add_argument("--max-frames", type=int, default=0, help="Maximum frames to save (0 = unlimited, default: 0)")
    parser.add_argument("--every-n", type=int, default=1, help="Save every N-th frame (default: 1)")
    parser.add_argument("--jpg-quality", type=int, default=95, help="JPEG quality 0-100 (default: 95)")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.video):
        print(f"ERROR: Video file not found: {args.video}")
        sys.exit(1)
    
    if args.every_n < 1:
        print(f"ERROR: --every-n must be >= 1, got {args.every_n}")
        sys.exit(1)
    
    if args.jpg_quality < 0 or args.jpg_quality > 100:
        print(f"ERROR: --jpg-quality must be in [0, 100], got {args.jpg_quality}")
        sys.exit(1)
    
    # Create output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Input video: {args.video}")
    print(f"Output directory: {args.out_dir}")
    
    # Open video
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"ERROR: Could not open video: {args.video}")
        sys.exit(1)
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames_video = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\nVideo properties:")
    print(f"  FPS: {fps}")
    print(f"  Resolution: {frame_width}x{frame_height}")
    print(f"  Total frames: {total_frames_video}")
    print(f"  Every N frames: {args.every_n}")
    if args.max_frames > 0:
        print(f"  Max frames to save: {args.max_frames}")
    print()
    
    # JPEG encoding parameters
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, args.jpg_quality]
    
    # Read frames
    idx = 0
    save_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Check if we should save this frame
        if idx % args.every_n == 0:
            # Save frame
            filename = f"frame_{save_idx:04d}.jpg"
            filepath = out_dir / filename
            
            cv2.imwrite(str(filepath), frame, encode_params)
            
            save_idx += 1
            
            # Check if we've reached max frames
            if args.max_frames > 0 and save_idx >= args.max_frames:
                break
        
        idx += 1
        
        # Progress indicator
        if (idx % 100 == 0) or (save_idx % 10 == 0 and idx % args.every_n == 0):
            print(f"Read {idx} frames, saved {save_idx} frames...", end='\r')
    
    cap.release()
    
    # Final report
    print(f"\n\n=== Extraction Complete ===")
    print(f"Total frames read: {idx}")
    print(f"Total frames saved: {save_idx}")
    print(f"Input FPS: {fps}")
    print(f"Input resolution: {frame_width}x{frame_height}")
    print(f"Output directory: {args.out_dir}")
    print(f"===========================")


if __name__ == "__main__":
    main()
