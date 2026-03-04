
import argparse
from pathlib import Path
import cv2
import numpy as np
import json

ARUCO_DICTS = {
    'DICT_4X4_50': cv2.aruco.DICT_4X4_50,
    'DICT_4X4_100': cv2.aruco.DICT_4X4_100,
    'DICT_5X5_50': cv2.aruco.DICT_5X5_50,
    'DICT_6X6_50': cv2.aruco.DICT_6X6_50,
    # Add more if needed
}

def mean_edge_length(corners):
    edges = [
        np.linalg.norm(corners[i] - corners[(i+1)%4])
        for i in range(4)
    ]
    return float(np.mean(edges))

def resize_to_fit(img, max_width=1280, max_height=720):
    h, w = img.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale, (new_w, new_h)

def main():
    parser = argparse.ArgumentParser(description="Select ROI on preview and detect ArUco markers in original image ROI.")
    parser.add_argument("--image", required=True, help="Input image path.")
    parser.add_argument("--dict", required=True, choices=list(ARUCO_DICTS.keys()), help="ArUco dictionary name.")
    parser.add_argument("--preview-max-width", type=int, default=1280, help="Max width for preview window.")
    parser.add_argument("--preview-max-height", type=int, default=720, help="Max height for preview window.")
    args = parser.parse_args()

    img_path = Path(args.image)
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"ERROR: Could not load image: {img_path}")
        return 1
    orig_h, orig_w = img.shape[:2]
    print(f"Loaded image: {img_path} (original resolution: {orig_w}x{orig_h})")

    # Create preview
    preview_img, scale, (preview_w, preview_h) = resize_to_fit(img, args.preview_max_width, args.preview_max_height)
    scale_x = orig_w / preview_w
    scale_y = orig_h / preview_h
    print(f"Preview resolution: {preview_w}x{preview_h}")
    print(f"Scale factors: scale_x={scale_x:.4f}, scale_y={scale_y:.4f}")

    # Select ROI on preview
    print("Select ROI with mouse on preview, then press ENTER or SPACE. Press C to cancel.")
    roi = cv2.selectROI("Select ROI (Preview)", preview_img, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow("Select ROI (Preview)")
    px, py, prw, prh = map(int, roi)
    if prw == 0 or prh == 0:
        print("ROI selection cancelled.")
        return 1
    print(f"Selected ROI in preview: x={px}, y={py}, w={prw}, h={prh}")

    # Scale ROI to original image
    x = int(round(px * scale_x))
    y = int(round(py * scale_y))
    rw = int(round(prw * scale_x))
    rh = int(round(prh * scale_y))
    # Clamp to image bounds
    x = max(0, min(x, orig_w-1))
    y = max(0, min(y, orig_h-1))
    rw = max(1, min(rw, orig_w-x))
    rh = max(1, min(rh, orig_h-y))
    print(f"ROI in original image: x={x}, y={y}, w={rw}, h={rh}")

    roi_img = img[y:y+rh, x:x+rw]
    print(f"ROI resolution (original): {rw}x{rh}")

    # Save ROI as JSON
    roi_json_path = Path("data/vision/roi.json")
    roi_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(roi_json_path, "w") as f:
        json.dump({"x": x, "y": y, "w": rw, "h": rh}, f, indent=2)
    print(f"ROI coordinates saved to {roi_json_path}")

    # Detect markers in ROI (original image)
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[args.dict])
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    corners, ids, _ = detector.detectMarkers(roi_img)

    debug_img = img.copy()
    if ids is None or len(ids) == 0:
        print("No ArUco markers found in ROI!")
        print("- Prüfe Beleuchtung, Fokus und Druckqualität.")
        print("- Stelle sicher, dass das richtige Dictionary gewählt wurde.")
        print("- Marker muss mindestens 50x50 Pixel groß sein.")
        # Draw ROI rectangle
        cv2.rectangle(debug_img, (x, y), (x+rw, y+rh), (0, 0, 255), 2)
        out_path = Path("data/vision/debug/tag_check_roi.png")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), debug_img)
        print(f"Debug image saved (ROI only): {out_path}")
        return 0

    ids = ids.flatten()
    for i, (c, marker_id) in enumerate(zip(corners, ids)):
        c = c.reshape(4,2)
        mean_len = mean_edge_length(c)
        print(f"Marker ID {marker_id}: mean edge length = {mean_len:.1f} px")
        # Map corners to original image
        pts = (c + np.array([x, y])).astype(int)
        cv2.polylines(debug_img, [pts], isClosed=True, color=(0,255,0), thickness=2)
        cx, cy = np.mean(pts, axis=0).astype(int)
        cv2.putText(debug_img, f"ID {marker_id}", (cx-20, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2, cv2.LINE_AA)
    # Draw ROI rectangle
    cv2.rectangle(debug_img, (x, y), (x+rw, y+rh), (255, 0, 0), 2)
    out_path = Path("data/vision/debug/tag_check_roi.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), debug_img)
    print(f"Debug image saved: {out_path}")
    return 0

if __name__ == "__main__":
    main()
