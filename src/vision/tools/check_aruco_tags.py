import argparse
from pathlib import Path
import cv2
import numpy as np

ARUCO_DICTS = {
    'DICT_4X4_50': cv2.aruco.DICT_4X4_50,
    'DICT_4X4_100': cv2.aruco.DICT_4X4_100,
    'DICT_5X5_50': cv2.aruco.DICT_5X5_50,
    'DICT_6X6_50': cv2.aruco.DICT_6X6_50,
    # Add more if needed
}

def mean_edge_length(corners):
    # corners: (4,2) array
    edges = [
        np.linalg.norm(corners[i] - corners[(i+1)%4])
        for i in range(4)
    ]
    return float(np.mean(edges))

def main():
    parser = argparse.ArgumentParser(description="Detect ArUco markers in an image and output debug visualization.")
    parser.add_argument("--image", required=True, help="Input image path.")
    parser.add_argument("--dict", required=True, choices=list(ARUCO_DICTS.keys()), help="ArUco dictionary name.")
    parser.add_argument("--out", required=True, help="Output debug image path.")
    args = parser.parse_args()

    img_path = Path(args.image)
    out_path = Path(args.out)
    dict_name = args.dict

    img = cv2.imread(str(img_path))
    if img is None:
        print(f"ERROR: Could not load image: {img_path}")
        return 1
    h, w = img.shape[:2]
    print(f"Loaded image: {img_path} (resolution: {w}x{h})")

    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[dict_name])
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    corners, ids, _ = detector.detectMarkers(img)

    if ids is None or len(ids) == 0:
        print("No ArUco markers found!")
        print("- Prüfe Beleuchtung, Fokus und Druckqualität.")
        print("- Stelle sicher, dass das richtige Dictionary gewählt wurde.")
        print("- Marker muss mindestens 50x50 Pixel groß sein.")
        cv2.imwrite(str(out_path), img)
        print(f"Debug image saved (unchanged): {out_path}")
        return 0

    ids = ids.flatten()
    for i, (c, marker_id) in enumerate(zip(corners, ids)):
        c = c.reshape(4,2)
        mean_len = mean_edge_length(c)
        print(f"Marker ID {marker_id}: mean edge length = {mean_len:.1f} px")
        # Draw polygon
        pts = c.astype(int)
        cv2.polylines(img, [pts], isClosed=True, color=(0,255,0), thickness=2)
        # Draw ID text
        cx, cy = np.mean(pts, axis=0).astype(int)
        cv2.putText(img, f"ID {marker_id}", (cx-20, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2, cv2.LINE_AA)

    cv2.imwrite(str(out_path), img)
    print(f"Debug image saved: {out_path}")
    return 0

if __name__ == "__main__":
    main()
