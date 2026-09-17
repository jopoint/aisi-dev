"""Offline, diagnostic-only table-OBB preprocessing comparison helpers.

This module intentionally invokes the existing :class:`YOLOTableOBBDetector`
directly.  It is not part of ``VisionPipeline`` and therefore cannot change
the frames used by live detection, association, or tracking.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import cv2
import numpy as np

from src.vision.detection.yolo_detector import YOLOTableOBBDetector
from src.vision.calibration.tabletop import TabletopCalibration, project_point


Variant = Tuple[str, Callable[[np.ndarray], np.ndarray]]


def levels_white_point(frame: np.ndarray, white_point: int) -> np.ndarray:
    """Apply the requested linear Levels white-point expansion.

    This is deliberately neither a gamma adjustment nor a local contrast
    operation: values are multiplied by ``255 / white_point`` and clipped.
    It is used only by the offline detector comparison in this module.
    """

    if not 1 <= int(white_point) <= 255:
        raise ValueError("white_point must be in [1, 255]")
    scale = 255.0 / float(white_point)
    return np.clip(frame.astype(np.float32) * scale, 0.0, 255.0).astype(np.uint8)


def table_obb_preprocess_variants(
    *, levels_white_points: Sequence[int] = (235, 225, 215)
) -> Tuple[Variant, ...]:
    """Return deterministic, deliberately conservative debug variants.

    None of these are applied in production.  The gamma/exposure variants
    darken bright projected content modestly; highlight clipping additionally
    limits the difference between projected white lines and a white tabletop.
    """

    gamma_lut = np.round(
        np.power(np.arange(256, dtype=np.float32) / 255.0, 1.15) * 255.0
    ).astype(np.uint8)

    def grayscale(frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    def gamma_115(frame: np.ndarray) -> np.ndarray:
        return cv2.LUT(frame, gamma_lut)

    def exposure_down(frame: np.ndarray) -> np.ndarray:
        return cv2.convertScaleAbs(frame, alpha=0.90, beta=-8.0)

    def highlight_clip_225(frame: np.ndarray) -> np.ndarray:
        return np.minimum(frame, 225).astype(np.uint8)

    def gaussian_blur_3(frame: np.ndarray) -> np.ndarray:
        return cv2.GaussianBlur(frame, (3, 3), 0)

    def gaussian_blur_5(frame: np.ndarray) -> np.ndarray:
        return cv2.GaussianBlur(frame, (5, 5), 0)

    def gaussian_blur_7(frame: np.ndarray) -> np.ndarray:
        return cv2.GaussianBlur(frame, (7, 7), 0)

    def exposure_down_gaussian_5(frame: np.ndarray) -> np.ndarray:
        return gaussian_blur_5(exposure_down(frame))

    level_variants = tuple(
        (
            f"levels_white_point_{int(white_point)}",
            lambda frame, white_point=int(white_point): levels_white_point(frame, white_point),
        )
        for white_point in levels_white_points
    )

    return (
        ("original", lambda frame: frame.copy()),
        ("grayscale", grayscale),
        ("gamma_1p15", gamma_115),
        ("exposure_down", exposure_down),
        ("highlight_clip_225", highlight_clip_225),
        ("gaussian_blur_3", gaussian_blur_3),
        ("gaussian_blur_5", gaussian_blur_5),
        ("gaussian_blur_7", gaussian_blur_7),
        ("exposure_down_gaussian_5", exposure_down_gaussian_5),
    ) + level_variants


def _obb_metrics(detection: Dict) -> Dict[str, float | None]:
    """Extract compact OBB metrics from the detector's existing payload."""

    poly = np.asarray(detection.get("obb_poly_px") or [], dtype=np.float32)
    if poly.shape != (4, 2):
        return {"long_side_px": None, "short_side_px": None, "area_px": None, "aspect_ratio": None}
    edge_a = float(np.linalg.norm(poly[1] - poly[0]))
    edge_b = float(np.linalg.norm(poly[2] - poly[1]))
    long_side = max(edge_a, edge_b)
    short_side = min(edge_a, edge_b)
    return {
        "long_side_px": long_side,
        "short_side_px": short_side,
        "area_px": float(abs(cv2.contourArea(poly.reshape(-1, 1, 2)))),
        "aspect_ratio": long_side / short_side if short_side > 1e-6 else None,
    }


def _world_obb_metrics(
    detection: Dict,
    calibration_profile: TabletopCalibration | None,
) -> Dict[str, float | None] | None:
    """Measure a raw OBB in calibrated centimetres when supplied by the CLI."""

    if calibration_profile is None:
        return None
    poly = detection.get("obb_poly_px") or []
    if not isinstance(poly, list) or len(poly) != 4:
        return None
    try:
        points_cm = [project_point((float(point[0]), float(point[1])), calibration_profile) for point in poly]
    except (IndexError, TypeError, ValueError, np.linalg.LinAlgError):
        return None
    edges = [
        float(np.hypot(
            points_cm[(index + 1) % 4][0] - points_cm[index][0],
            points_cm[(index + 1) % 4][1] - points_cm[index][1],
        ))
        for index in range(4)
    ]
    width = 0.5 * (edges[0] + edges[2])
    height = 0.5 * (edges[1] + edges[3])
    long_side, short_side = max(width, height), min(width, height)
    signed_area = sum(
        points_cm[index][0] * points_cm[(index + 1) % 4][1]
        - points_cm[(index + 1) % 4][0] * points_cm[index][1]
        for index in range(4)
    )
    area = abs(0.5 * signed_area)
    if short_side <= 1e-6 or area <= 0.0:
        return None
    return {
        "long_side_cm": long_side,
        "short_side_cm": short_side,
        "area_cm2": area,
        "aspect_ratio": long_side / short_side,
    }


def _json_detection(
    index: int,
    detection: Dict,
    calibration_profile: TabletopCalibration | None,
) -> Dict:
    return {
        "raw_detection_index": index,
        "score": float(detection.get("score", 0.0)),
        "bbox_px": detection.get("bbox_px"),
        "center_px": detection.get("obb_center_px"),
        "poly_px": detection.get("obb_poly_px"),
        "yaw_rad": detection.get("obb_yaw_rad"),
        "obb": _obb_metrics(detection),
        "world_obb": _world_obb_metrics(detection, calibration_profile),
    }


def _summary_row(record: Dict) -> Dict:
    """Flatten the score-selected raw OBB into one comparison CSV row."""

    selected = record["selected_raw_obb"]
    obb = selected["obb"] if selected is not None else {}
    world_obb = (selected.get("world_obb") or {}) if selected is not None else {}
    center = selected["center_px"] if selected is not None else None
    return {
        "frame_id": record["frame_id"],
        "source_frame": record["source_frame"],
        "preprocessing_variant": record["preprocessing_variant"],
        "detected_table_count": record["raw_table_obb_count"],
        "highest_confidence": None if selected is None else selected["score"],
        "center_x_px": None if center is None else center[0],
        "center_y_px": None if center is None else center[1],
        "yaw_rad": None if selected is None else selected["yaw_rad"],
        "long_side_px": obb.get("long_side_px"),
        "short_side_px": obb.get("short_side_px"),
        "obb_area_px": obb.get("area_px"),
        "aspect_ratio": obb.get("aspect_ratio"),
        "world_long_side_cm": world_obb.get("long_side_cm"),
        "world_short_side_cm": world_obb.get("short_side_cm"),
        "world_area_cm2": world_obb.get("area_cm2"),
    }


def draw_table_obb_overlay(frame_bgr: np.ndarray, detections: Sequence[Dict]) -> np.ndarray:
    """Draw raw OBB candidates, highlighting the score-selected candidate.

    This is a detector-level comparison.  It intentionally has no tracker,
    hence no final persistent ID; the first (confidence-sorted) detection is
    marked only as ``selected_raw`` for side-by-side inspection.
    """

    overlay = frame_bgr.copy()
    for index, detection in enumerate(detections):
        poly = np.asarray(detection.get("obb_poly_px") or [], dtype=np.int32)
        color = (0, 255, 255) if index == 0 else (0, 120, 255)
        thickness = 3 if index == 0 else 2
        if poly.shape == (4, 2):
            cv2.polylines(overlay, [poly.reshape(-1, 1, 2)], True, color, thickness, cv2.LINE_AA)
        center = detection.get("obb_center_px")
        if isinstance(center, (list, tuple)) and len(center) == 2:
            x, y = int(round(center[0])), int(round(center[1]))
            label = f"{'selected_raw ' if index == 0 else ''}obb_{index}: {float(detection.get('score', 0.0)):.2f}"
            cv2.putText(overlay, label, (x + 6, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 1, cv2.LINE_AA)
    return overlay


def _image_paths(input_path: Path, max_frames: int | None) -> Iterable[Path]:
    if input_path.is_file():
        paths = [input_path]
    elif input_path.is_dir():
        paths = sorted(
            path for path in input_path.iterdir()
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}
        )
    else:
        raise ValueError(f"Comparison input does not exist: {input_path}")
    if not paths:
        raise ValueError(f"No image frames found at: {input_path}")
    return paths if max_frames is None else paths[:max_frames]


def run_table_obb_preprocess_comparison(
    input_path: str | Path,
    output_dir: str | Path,
    detector: YOLOTableOBBDetector,
    *,
    max_frames: int | None = None,
    calibration_profile: TabletopCalibration | None = None,
    levels_white_points: Sequence[int] = (235, 225, 215),
) -> Path:
    """Run raw table-OBB inference on each debug variant and save artifacts.

    Returns the JSONL path.  Its ``final_track_id`` is always ``None`` because
    this purposely stops before the production tracker; ``selected_raw_obb``
    is the model's confidence-sorted first candidate instead.
    """

    source = Path(input_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    jsonl_path = output / "table_obb_preprocess_comparison.jsonl"
    summary_path = output / "table_obb_preprocess_summary.csv"
    jsonl_path.write_text("", encoding="utf-8")
    summary_columns = (
        "frame_id", "source_frame", "preprocessing_variant", "detected_table_count",
        "highest_confidence", "center_x_px", "center_y_px", "yaw_rad",
        "long_side_px", "short_side_px", "obb_area_px", "aspect_ratio",
        "world_long_side_cm", "world_short_side_cm", "world_area_cm2",
    )

    with (
        jsonl_path.open("a", encoding="utf-8") as jsonl_file,
        summary_path.open("w", encoding="utf-8", newline="") as summary_file,
    ):
        summary_writer = csv.DictWriter(summary_file, fieldnames=summary_columns)
        summary_writer.writeheader()
        for frame_id, image_path in enumerate(_image_paths(source, max_frames)):
            frame = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError(f"Could not read image frame: {image_path}")
            for variant_name, transform in table_obb_preprocess_variants(
                levels_white_points=levels_white_points
            ):
                processed = transform(frame)
                detections = detector.detect_tables(processed)
                prefix = f"frame_{frame_id:05d}_{variant_name}"
                processed_path = output / f"{prefix}_processed.png"
                overlay_path = output / f"{prefix}_raw_obb.png"
                if not cv2.imwrite(str(processed_path), processed):
                    raise IOError(f"Could not write debug image: {processed_path}")
                if not cv2.imwrite(str(overlay_path), draw_table_obb_overlay(processed, detections)):
                    raise IOError(f"Could not write debug image: {overlay_path}")
                raw = [
                    _json_detection(index, detection, calibration_profile)
                    for index, detection in enumerate(detections)
                ]
                record = {
                    "frame_id": frame_id,
                    "source_frame": str(image_path),
                    "preprocessing_variant": variant_name,
                    "raw_table_obb": raw,
                    "raw_table_obb_count": len(raw),
                    "selected_raw_obb": raw[0] if raw else None,
                    "final_selected_table_obb": None,
                    "final_track_id": None,
                    "note": "Offline detector comparison; final tracker output is intentionally not run.",
                }
                jsonl_file.write(json.dumps(record) + "\n")
                summary_writer.writerow(_summary_row(record))
    return jsonl_path
