"""
Interactive tool to select and label bounding boxes for furniture detection.

Example usage:
    python src/vision/tools/select_boxes_init.py \
        --image data/vision/test_frames/usb_1080_tagtest.jpg \
        --out data/vision/boxes_init.json \
        --preview-max-width 1280
"""

import argparse
import cv2
import numpy as np
import json
import os
from pathlib import Path


def resize_to_fit(img, max_width=1280, max_height=720):
    """
    Resize image to fit within max dimensions while preserving aspect ratio.
    
    Args:
        img: Input image
        max_width: Maximum width
        max_height: Maximum height
    
    Returns:
        (resized_img, scale, (new_width, new_height))
    """
    h, w = img.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale, (new_w, new_h)


def draw_boxes_on_image(image, boxes):
    """
    Draw labeled boxes on image for visualization.
    
    Args:
        image: Input image (BGR)
        boxes: List of dicts with 'label' and 'bbox_px' keys
    
    Returns:
        Image with boxes drawn
    """
    overlay = image.copy()
    
    # Color map
    colors = {
        "table": (0, 255, 0),    # Green
        "chair": (255, 0, 0),    # Blue
        "unknown": (0, 255, 255) # Yellow
    }
    
    for i, box_info in enumerate(boxes):
        label = box_info.get("label", "unknown")
        bbox = box_info["bbox_px"]
        x1, y1, x2, y2 = bbox
        
        color = colors.get(label, colors["unknown"])
        
        # Draw rectangle
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
        
        # Draw label with index
        text = f"{i}: {label}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        # Get text size for background
        (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # Draw background rectangle for text
        cv2.rectangle(overlay, (x1, y1 - text_h - baseline - 5), 
                     (x1 + text_w, y1), color, -1)
        
        # Draw text
        cv2.putText(overlay, text, (x1, y1 - baseline - 2), 
                   font, font_scale, (255, 255, 255), thickness)
    
    return overlay


def main():
    parser = argparse.ArgumentParser(
        description="Interactively select and label bounding boxes for furniture."
    )
    parser.add_argument("--image", required=True, help="Input image path.")
    parser.add_argument("--out", required=True, help="Output JSON file path.")
    parser.add_argument(
        "--preview-max-width", 
        type=int, 
        default=1280, 
        help="Max width for preview window."
    )
    parser.add_argument(
        "--preview-max-height",
        type=int,
        default=720,
        help="Max height for preview window."
    )
    
    args = parser.parse_args()
    
    # Load original image
    img_path = Path(args.image)
    original_img = cv2.imread(str(img_path))
    if original_img is None:
        raise RuntimeError(f"Could not load image: {img_path}")
    
    orig_h, orig_w = original_img.shape[:2]
    print(f"Loaded image: {img_path}")
    print(f"  Original resolution: {orig_w}x{orig_h}")
    
    # Create preview
    preview_img, scale, (preview_w, preview_h) = resize_to_fit(
        original_img, args.preview_max_width, args.preview_max_height
    )
    scale_x = orig_w / preview_w
    scale_y = orig_h / preview_h
    
    print(f"  Preview resolution: {preview_w}x{preview_h}")
    print(f"  Scale factors: x={scale_x:.4f}, y={scale_y:.4f}")
    print()
    print("Instructions:")
    print("  1. Drag a box on the preview image")
    print("  2. Press ENTER to confirm the box")
    print("  3. Then press:")
    print("     't' = label as TABLE")
    print("     'c' = label as CHAIR")
    print("     'u' = UNDO last box")
    print("     'q' = QUIT (finish and save)")
    print("  4. Press ESC during box selection to finish")
    print()
    
    boxes = []  # List of {"label": str, "bbox_px": [x1, y1, x2, y2]}
    
    while True:
        # Create preview with current boxes for feedback
        preview_with_boxes = preview_img.copy()
        
        # Draw existing boxes on preview (scaled down)
        for box_info in boxes:
            label = box_info["label"]
            x1, y1, x2, y2 = box_info["bbox_px"]
            
            # Scale to preview coordinates
            px1 = int(x1 / scale_x)
            py1 = int(y1 / scale_y)
            px2 = int(x2 / scale_x)
            py2 = int(y2 / scale_y)
            
            color = (0, 255, 0) if label == "table" else (255, 0, 0)
            cv2.rectangle(preview_with_boxes, (px1, py1), (px2, py2), color, 2)
        
        # Show current box count
        info_text = f"Boxes: {len(boxes)} (ESC to finish)"
        cv2.putText(preview_with_boxes, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Select ROI on preview
        roi = cv2.selectROI("Select Box (ENTER to confirm, ESC to finish)", 
                           preview_with_boxes, showCrosshair=True, fromCenter=False)
        
        px, py, pw, ph = map(int, roi)
        
        # Check if selection was cancelled (ESC pressed or zero size)
        if pw == 0 or ph == 0:
            print("\nNo box selected. Finishing...")
            cv2.destroyAllWindows()
            break
        
        # Convert preview coordinates to original coordinates
        x1 = int(px * scale_x)
        y1 = int(py * scale_y)
        x2 = int((px + pw) * scale_x)
        y2 = int((py + ph) * scale_y)
        
        # Ensure coordinates are within image bounds
        x1 = max(0, min(x1, orig_w))
        y1 = max(0, min(y1, orig_h))
        x2 = max(0, min(x2, orig_w))
        y2 = max(0, min(y2, orig_h))
        
        print(f"\nBox selected (preview): ({px}, {py}, {pw}, {ph})")
        print(f"Box in original coords: ({x1}, {y1}) -> ({x2}, {y2})")
        print("Press: 't' (table), 'c' (chair), 'u' (undo last), 'q' (quit)")
        
        # Wait for label input
        while True:
            key = cv2.waitKey(0) & 0xFF
            
            if key == ord('t'):
                boxes.append({"label": "table", "bbox_px": [x1, y1, x2, y2]})
                print(f"  -> Added as TABLE (box #{len(boxes) - 1})")
                break
            elif key == ord('c'):
                boxes.append({"label": "chair", "bbox_px": [x1, y1, x2, y2]})
                print(f"  -> Added as CHAIR (box #{len(boxes) - 1})")
                break
            elif key == ord('u'):
                if len(boxes) > 0:
                    removed = boxes.pop()
                    print(f"  -> Undid last box: {removed['label']}")
                    print(f"  -> Current box count: {len(boxes)}")
                else:
                    print("  -> No boxes to undo")
                break
            elif key == ord('q'):
                print("  -> Quitting without adding this box")
                cv2.destroyAllWindows()
                # Exit the inner and outer loop
                break
            else:
                print(f"  -> Invalid key. Press 't', 'c', 'u', or 'q'")
        
        # Check if user pressed 'q' to quit
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()
    
    print(f"\nTotal boxes selected: {len(boxes)}")
    
    if len(boxes) == 0:
        print("No boxes to save. Exiting.")
        return
    
    # Prepare output JSON
    output_data = {
        "image_path": str(img_path),
        "image_size": [orig_w, orig_h],
        "boxes": boxes
    }
    
    # Save JSON
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Saved box data to: {out_path}")
    
    # Create debug overlay on original image
    debug_dir = Path("data/vision/debug")
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    overlay = draw_boxes_on_image(original_img, boxes)
    debug_path = debug_dir / "boxes_init_overlay.png"
    cv2.imwrite(str(debug_path), overlay)
    
    print(f"Saved debug overlay to: {debug_path}")
    print("\nBox summary:")
    for i, box_info in enumerate(boxes):
        label = box_info["label"]
        bbox = box_info["bbox_px"]
        print(f"  {i}: {label:6s} -> {bbox}")


if __name__ == "__main__":
    main()
