"""
Create synthetic image sequences with small transformations for testing.

Example usage:
    python src/vision/tools/make_synthetic_sequence.py \
        --image data/vision/test_frames/usb_1080_tagtest.jpg \
        --out-dir data/vision/synth_seq \
        --n 60
"""

import argparse
import cv2
import numpy as np
from pathlib import Path
import math


def apply_synthetic_transform(
    image: np.ndarray,
    frame_idx: int,
    n_frames: int,
    max_translation: float = 10.0,
    brightness_variation: float = 0.05
) -> np.ndarray:
    """
    Apply small synthetic transformations to an image.
    
    Args:
        image: Input image (BGR)
        frame_idx: Current frame index (0 to n_frames-1)
        n_frames: Total number of frames
        max_translation: Maximum translation in pixels
        brightness_variation: Relative brightness variation (0.0 - 1.0)
    
    Returns:
        Transformed image
    """
    h, w = image.shape[:2]
    
    # Calculate phase based on frame index
    phase = 2.0 * math.pi * frame_idx / n_frames
    
    # Calculate translation using sin/cos for smooth circular motion
    tx = max_translation * math.sin(phase)
    ty = max_translation * math.cos(phase * 0.7)  # Different frequency for y
    
    # Build affine transformation matrix for translation
    M = np.float32([
        [1, 0, tx],
        [0, 1, ty]
    ])
    
    # Apply translation
    transformed = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    # Apply brightness variation if specified
    if brightness_variation > 0:
        # Brightness oscillates with sin wave
        brightness_factor = 1.0 + brightness_variation * math.sin(phase * 2.0)
        transformed = cv2.convertScaleAbs(transformed, alpha=brightness_factor, beta=0)
    
    return transformed


def main():
    parser = argparse.ArgumentParser(
        description="Create synthetic image sequence with small transformations."
    )
    parser.add_argument("--image", required=True, help="Input image path.")
    parser.add_argument("--out-dir", required=True, help="Output directory for frames.")
    parser.add_argument("--n", type=int, default=60, help="Number of frames to generate.")
    parser.add_argument(
        "--max-translation", 
        type=float, 
        default=10.0, 
        help="Maximum translation in pixels."
    )
    parser.add_argument(
        "--brightness-var",
        type=float,
        default=0.05,
        help="Brightness variation (0.0-1.0, relative to original)."
    )
    parser.add_argument(
        "--no-brightness",
        action="store_true",
        help="Disable brightness variation."
    )
    
    args = parser.parse_args()
    
    # Load input image
    image = cv2.imread(args.image)
    if image is None:
        raise RuntimeError(f"Could not load image: {args.image}")
    
    h, w = image.shape[:2]
    print(f"Loaded image: {args.image}")
    print(f"  Resolution: {w}x{h}")
    
    # Create output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {out_dir}")
    
    # Determine brightness variation
    brightness_var = 0.0 if args.no_brightness else args.brightness_var
    
    # Generate frames
    print(f"Generating {args.n} frames...")
    for i in range(args.n):
        # Apply transformation
        frame = apply_synthetic_transform(
            image,
            frame_idx=i,
            n_frames=args.n,
            max_translation=args.max_translation,
            brightness_variation=brightness_var
        )
        
        # Save frame
        frame_name = f"frame_{i:04d}.jpg"
        frame_path = out_dir / frame_name
        cv2.imwrite(str(frame_path), frame)
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{args.n} frames...")
    
    print(f"Done. Generated {args.n} frames in {out_dir}")
    print(f"Transformations applied:")
    print(f"  - Max translation: {args.max_translation} px")
    print(f"  - Brightness variation: {'disabled' if args.no_brightness else f'{brightness_var:.2%}'}")


if __name__ == "__main__":
    main()
