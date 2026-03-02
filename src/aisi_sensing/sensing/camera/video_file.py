from __future__ import annotations

from typing import Iterator, Tuple
from ...core.timebase import now_iso


def open_video(path: str):
    try:
        import cv2  # type: ignore
    except Exception as e:
        raise RuntimeError("OpenCV not available. Install opencv-python.") from e
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video file {path}")
    return cap


def frames(cap) -> Iterator[Tuple[str, int, "cv2.Mat"]]:  # type: ignore[name-defined]
    try:
        import cv2  # type: ignore
    except Exception as e:
        raise RuntimeError("OpenCV not available. Install opencv-python.") from e
    frame_id = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        yield now_iso(), frame_id, frame
        frame_id += 1
    cap.release()
