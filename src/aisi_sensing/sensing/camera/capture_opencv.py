from __future__ import annotations

from typing import Iterator, Tuple
from ..calibration.homography import map_pose_with_h
from ...core.timebase import now_iso
from ...core.types import Pose2D


def open_camera(index: int = 0, width: int | None = None, height: int | None = None, fps: int | None = None):
    try:
        import cv2  # type: ignore
    except Exception as e:
        raise RuntimeError("OpenCV not available. Install opencv-python.") from e
    cap = cv2.VideoCapture(index)
    if width is not None:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height is not None:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if fps is not None:
        cap.set(cv2.CAP_PROP_FPS, fps)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {index}")
    return cap


def frames(cap) -> Iterator[Tuple[str, int, "cv2.Mat"]]:  # type: ignore[name-defined]
    """Yield (timestamp_iso, frame_id, frame) from an opened VideoCapture."""
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
