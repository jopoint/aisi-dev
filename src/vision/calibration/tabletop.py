"""Tabletop-plane camera calibration for AISI world coordinates (centimetres)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import math

import cv2
import numpy as np


PROFILE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class TabletopCalibration:
    homography: np.ndarray
    calibration_id: str | None = None
    plane_height_cm: float | None = None
    processed_size: tuple[int, int] | None = None
    camera_rotate: int | None = None
    crop: tuple[int, int, int, int] | None = None
    profile_backed: bool = False

    def validate_processed_frame(self, width: int, height: int) -> None:
        if self.processed_size is not None and self.processed_size != (width, height):
            raise ValueError(
                f"Calibration expects processed frame {self.processed_size[0]}x{self.processed_size[1]}, "
                f"got {width}x{height}."
            )

    def world_metadata(self) -> dict[str, Any]:
        if not self.profile_backed:
            return {}
        return {
            "calibration_id": self.calibration_id,
            "calibration_plane": "rect_tabletop",
            "plane_height_cm": self.plane_height_cm,
            "non_table_projection": "tabletop_plane_approximation",
        }


def _as_homography(value: Any) -> np.ndarray:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all():
        raise ValueError("homography must be a finite 3x3 matrix")
    if abs(float(np.linalg.det(matrix))) < 1e-12:
        raise ValueError("homography must be non-singular")
    return matrix


def load_tabletop_calibration(path: str | Path) -> TabletopCalibration:
    """Load a versioned tabletop profile or legacy bare homography JSON."""
    source = Path(path)
    with source.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Calibration JSON must be an object")
    matrix = _as_homography(data.get("homography"))
    if "schema_version" not in data:
        return TabletopCalibration(homography=matrix)
    if data.get("coordinate_system") != "aisi_world_cm":
        raise ValueError("Calibration profile coordinate_system must be 'aisi_world_cm'")
    if data.get("calibration_plane") != "rect_tabletop":
        raise ValueError("Calibration profile calibration_plane must be 'rect_tabletop'")
    geometry = data.get("processed_image")
    if not isinstance(geometry, dict):
        raise ValueError("Calibration profile requires processed_image")
    width, height = int(geometry.get("width", 0)), int(geometry.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("Calibration profile processed_image width/height must be positive")
    preprocessing = data.get("preprocessing", {})
    crop_value = preprocessing.get("crop")
    crop = None if crop_value is None else tuple(int(item) for item in crop_value)
    if crop is not None and len(crop) != 4:
        raise ValueError("Calibration profile crop must be null or [x,y,w,h]")
    return TabletopCalibration(
        homography=matrix,
        calibration_id=str(data.get("calibration_id", source.stem)),
        plane_height_cm=float(data["plane_height_cm"]),
        processed_size=(width, height),
        camera_rotate=int(preprocessing.get("camera_rotate", 0)),
        crop=crop,
        profile_backed=True,
    )


def project_point(point_px: tuple[float, float], calibration: TabletopCalibration) -> tuple[float, float]:
    point = np.array([point_px[0], point_px[1], 1.0], dtype=np.float64)
    projected = calibration.homography @ point
    if abs(float(projected[2])) < 1e-12:
        raise ValueError("Homography projected point at infinity")
    return float(projected[0] / projected[2]), float(projected[1] / projected[2])


def project_axis_angle(
    center_px: tuple[float, float], yaw_rad: float, calibration: TabletopCalibration, axis_length_px: float = 100.0
) -> float:
    """Map an unoriented OBB long-axis from image angle to AISI world angle."""
    endpoint_px = (
        center_px[0] + math.cos(yaw_rad) * axis_length_px,
        center_px[1] + math.sin(yaw_rad) * axis_length_px,
    )
    cx, cy = project_point(center_px, calibration)
    ex, ey = project_point(endpoint_px, calibration)
    return math.atan2(ey - cy, ex - cx)


def fit_homography(image_points: list[tuple[float, float]], world_points: list[tuple[float, float]]) -> np.ndarray:
    if len(image_points) < 4 or len(image_points) != len(world_points):
        raise ValueError("At least four matching image/world points are required")
    matrix, _mask = cv2.findHomography(
        np.asarray(image_points, dtype=np.float64),
        np.asarray(world_points, dtype=np.float64),
        method=0,
    )
    if matrix is None:
        raise ValueError("OpenCV could not compute a homography")
    return _as_homography(matrix)


def residual_report(image_points: list[tuple[float, float]], world_points: list[tuple[float, float]], matrix: np.ndarray) -> dict[str, Any]:
    calibration = TabletopCalibration(matrix)
    errors = []
    for image_point, world_point in zip(image_points, world_points):
        mapped = project_point(image_point, calibration)
        errors.append(math.dist(mapped, world_point))
    return {
        "point_count": len(errors),
        "rmse_cm": math.sqrt(sum(error * error for error in errors) / max(1, len(errors))),
        "max_error_cm": max(errors, default=0.0),
        "errors_cm": errors,
    }


def leave_one_out_report(image_points: list[tuple[float, float]], world_points: list[tuple[float, float]]) -> list[float | None]:
    results: list[float | None] = []
    for index in range(len(image_points)):
        remaining_image = image_points[:index] + image_points[index + 1 :]
        remaining_world = world_points[:index] + world_points[index + 1 :]
        if len(remaining_image) < 4:
            results.append(None)
            continue
        matrix = fit_homography(remaining_image, remaining_world)
        results.append(math.dist(project_point(image_points[index], TabletopCalibration(matrix)), world_points[index]))
    return results
