from __future__ import annotations

from typing import List, Tuple


def detect_markers(frame) -> List[Tuple[int, list]]:  # type: ignore[no-untyped-def]
    """Detect ArUco markers in a frame.

    Returns a list of (id, corners) where corners is a list of 4 (x,y) pixel points.
    Requires opencv-contrib-python installed. Falls back to empty list if unavailable.
    """
    try:
        import cv2  # type: ignore
        aruco = cv2.aruco  # type: ignore[attr-defined]
    except Exception:
        return []

    # Use a common dictionary; adjust as needed.
    try:
        dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)  # type: ignore[attr-defined]
    except Exception:
        return []
    parameters = aruco.DetectorParameters()  # type: ignore[call-arg,attr-defined]
    detector = aruco.ArucoDetector(dictionary, parameters)  # type: ignore[attr-defined]
    corners, ids, _ = detector.detectMarkers(frame)
    detections: List[Tuple[int, list]] = []
    if ids is None:
        return detections
    for i, c in zip(ids.flatten().tolist(), corners):
        pts = [(float(pt[0]), float(pt[1])) for pt in c.reshape(-1, 2)]
        detections.append((int(i), pts))
    return detections
