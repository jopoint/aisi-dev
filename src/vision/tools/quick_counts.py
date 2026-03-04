#!/usr/bin/env python3
"""
Quick counter script for furniture detection results in JSONL format.

Reads FrameEvents from JSONL and counts furniture kinds (tables, chairs, etc).
Supports averaging over multiple frames.

Usage:
    python src/vision/tools/quick_counts.py --jsonl data/vision/out_synth.jsonl --frames 1
    python src/vision/tools/quick_counts.py --jsonl data/vision/out.jsonl --frames 10
"""

import argparse
import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple


def count_frame_furniture(frame_event: Dict) -> Counter:
    """
    Count furniture kinds in a single FrameEvent.
    
    Args:
        frame_event: Dict with 'furniture' key containing list of entities
    
    Returns:
        Counter of kinds
    """
    furniture = frame_event.get("furniture", [])
    kinds = [item["kind"] for item in furniture]
    return Counter(kinds)


def read_jsonl_frames(jsonl_path: str, max_frames: int = None) -> List[Dict]:
    """
    Read frames from JSONL file.
    
    Args:
        jsonl_path: Path to JSONL file
        max_frames: Maximum number of frames to read (None = all)
    
    Returns:
        List of frame event dicts
    """
    frames = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_frames is not None and i >= max_frames:
                break
            try:
                frame = json.loads(line.strip())
                frames.append(frame)
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse line {i+1}: {e}")
                continue
    
    return frames


def aggregate_counts(frames: List[Dict]) -> Tuple[Counter, float]:
    """
    Aggregate furniture counts over all frames.
    
    Args:
        frames: List of frame event dicts
    
    Returns:
        Tuple of (total_counter, average_count)
    """
    total_counter = Counter()
    
    for frame in frames:
        frame_counts = count_frame_furniture(frame)
        total_counter.update(frame_counts)
    
    # Calculate average per frame
    num_frames = len(frames) if frames else 1
    avg_per_frame = sum(total_counter.values()) / num_frames if num_frames > 0 else 0
    
    return total_counter, avg_per_frame


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Count furniture kinds in JSONL detection output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Count first frame only
  python src/vision/tools/quick_counts.py --jsonl data/vision/out_synth.jsonl --frames 1
  
  # Average counts over 10 frames
  python src/vision/tools/quick_counts.py --jsonl data/vision/out.jsonl --frames 10
  
  # Count all frames
  python src/vision/tools/quick_counts.py --jsonl data/vision/out.jsonl
        """
    )
    
    parser.add_argument(
        "--jsonl",
        default="data/vision/out_synth.jsonl",
        help="Path to JSONL file with FrameEvents (default: data/vision/out_synth.jsonl)"
    )
    
    parser.add_argument(
        "--frames",
        type=int,
        default=1,
        help="Number of frames to process (default: 1, use 0 for all frames)"
    )
    
    args = parser.parse_args()
    
    # Validate path
    jsonl_path = Path(args.jsonl)
    if not jsonl_path.exists():
        print(f"Error: JSONL file not found: {args.jsonl}")
        return 1
    
    # Read frames
    max_frames = args.frames if args.frames > 0 else None
    frames = read_jsonl_frames(str(jsonl_path), max_frames=max_frames)
    
    if not frames:
        print(f"Error: No frames read from {args.jsonl}")
        return 1
    
    print(f"Read {len(frames)} frame(s) from {args.jsonl}")
    
    # Aggregate and display results
    total_counter, avg_per_frame = aggregate_counts(frames)
    
    print(f"\nFurniture counts ({len(frames)} frames):")
    print(f"  Total: {dict(total_counter)}")
    print(f"  Average per frame: {avg_per_frame:.2f}")
    
    if len(frames) > 1:
        print(f"\nPer-frame breakdown:")
        for i, frame in enumerate(frames):
            frame_counts = count_frame_furniture(frame)
            print(f"  Frame {i}: {dict(frame_counts)}")
    
    return 0


if __name__ == "__main__":
    exit(main())
