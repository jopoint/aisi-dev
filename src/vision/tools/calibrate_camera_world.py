"""Fit a Rect-tabletop pixel-to-AISI-world calibration from a capture manifest."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from src.vision.calibration.tabletop import TabletopCalibration, fit_homography, leave_one_out_report, project_point, residual_report


def _aruco_dictionary(name: str):
    if not hasattr(cv2, "aruco") or not hasattr(cv2.aruco, name):
        raise ValueError(f"OpenCV ArUco dictionary unavailable: {name}")
    return cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, name))


def _load_manifest(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise ValueError("Calibration manifest must be a JSON object")
    if manifest.get("coordinate_system") != "aisi_world_cm":
        raise ValueError("Manifest coordinate_system must be 'aisi_world_cm'")
    if manifest.get("calibration_plane") != "rect_tabletop":
        raise ValueError("Manifest calibration_plane must be 'rect_tabletop'")
    if float(manifest.get("plane_height_cm", 0.0)) <= 0.0:
        raise ValueError("Manifest plane_height_cm must be positive")
    if not isinstance(manifest.get("captures"), list):
        raise ValueError("Manifest captures must be a list")
    return manifest


def collect_correspondences(manifest_path: str | Path, debug_dir: str | Path | None = None):
    manifest_file = Path(manifest_path)
    manifest = _load_manifest(manifest_file)
    dictionary = _aruco_dictionary(str(manifest.get("aruco_dictionary", "DICT_4X4_50")))
    detector = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())
    image_points: list[tuple[float, float]] = []
    world_points: list[tuple[float, float]] = []
    details: list[dict[str, Any]] = []
    processed_size: tuple[int, int] | None = None
    debug_path = None if debug_dir is None else Path(debug_dir)
    if debug_path is not None:
        debug_path.mkdir(parents=True, exist_ok=True)

    for capture_index, capture in enumerate(manifest["captures"]):
        if not isinstance(capture, dict) or not isinstance(capture.get("image"), str):
            raise ValueError(f"Capture {capture_index} requires image")
        image_path = Path(capture["image"])
        if not image_path.is_absolute():
            image_path = manifest_file.parent / image_path
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Capture {capture_index}: cannot read image {image_path}")
        height, width = image.shape[:2]
        if processed_size is None:
            processed_size = (width, height)
        elif processed_size != (width, height):
            raise ValueError(f"Capture {capture_index}: image size {width}x{height} differs from {processed_size[0]}x{processed_size[1]}")
        corners, marker_ids, _rejected = detector.detectMarkers(image)
        detected: dict[int, tuple[float, float]] = {}
        if marker_ids is not None:
            for corner, marker_id in zip(corners, marker_ids.flatten()):
                center = np.mean(corner.reshape(4, 2), axis=0)
                detected[int(marker_id)] = (float(center[0]), float(center[1]))
        expected = capture.get("points")
        if not isinstance(expected, list) or not expected:
            raise ValueError(f"Capture {capture_index}: points must be a non-empty list")
        overlay = image.copy()
        capture_marker_ids: set[int] = set()
        for point_index, point in enumerate(expected):
            if not isinstance(point, dict) or "marker_id" not in point or "world_cm" not in point:
                raise ValueError(f"Capture {capture_index} point {point_index}: requires marker_id and world_cm")
            marker_id = int(point["marker_id"])
            if marker_id in capture_marker_ids:
                raise ValueError(f"Capture {capture_index}: marker {marker_id} is declared more than once")
            capture_marker_ids.add(marker_id)
            world = point["world_cm"]
            if not isinstance(world, list) or len(world) != 2:
                raise ValueError(f"Capture {capture_index} point {point_index}: world_cm must be [x,y]")
            if marker_id not in detected:
                raise ValueError(f"Capture {capture_index}: expected marker {marker_id} was not detected")
            pixel = detected[marker_id]
            world_xy = (float(world[0]), float(world[1]))
            image_points.append(pixel)
            world_points.append(world_xy)
            details.append({"capture_index": capture_index, "image": str(image_path), "marker_id": marker_id, "pixel": list(pixel), "world_cm": list(world_xy)})
            cv2.circle(overlay, (round(pixel[0]), round(pixel[1])), 6, (0, 255, 0), 2)
            cv2.putText(overlay, f"id={marker_id} world=({world_xy[0]:.1f},{world_xy[1]:.1f})", (round(pixel[0]) + 8, round(pixel[1]) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
        if debug_path is not None:
            cv2.imwrite(str(debug_path / f"capture_{capture_index:02d}.png"), overlay)
    if len(image_points) < 4:
        raise ValueError("At least four valid marker correspondences are required")
    return manifest, processed_size, image_points, world_points, details


def run(manifest_path: str | Path, output: str | Path, report: str | Path, debug_dir: str | Path | None = None) -> dict[str, Any]:
    manifest, processed_size, image_points, world_points, details = collect_correspondences(manifest_path, debug_dir)
    matrix = fit_homography(image_points, world_points)
    metrics = residual_report(image_points, world_points, matrix)
    loo = leave_one_out_report(image_points, world_points)
    for detail, error, loo_error in zip(details, metrics["errors_cm"], loo):
        detail["fit_error_cm"] = error
        detail["leave_one_out_error_cm"] = loo_error
        detail["mapped_world_cm"] = list(project_point(tuple(detail["pixel"]), TabletopCalibration(matrix)))
    preprocessing = manifest.get("preprocessing", {})
    calibration_id = str(manifest.get("calibration_id", Path(output).stem))
    profile = {
        "schema_version": 1,
        "calibration_id": calibration_id,
        "coordinate_system": "aisi_world_cm",
        "calibration_plane": "rect_tabletop",
        "plane_height_cm": float(manifest["plane_height_cm"]),
        "processed_image": {"width": processed_size[0], "height": processed_size[1]},
        "preprocessing": {"camera_rotate": int(preprocessing.get("camera_rotate", 0)), "crop": preprocessing.get("crop")},
        "homography": matrix.tolist(),
        "reference_points": details,
        "validation": {**metrics, "leave_one_out_errors_cm": loo},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    for destination, payload in ((Path(output), profile), (Path(report), profile["validation"])):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return profile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True, help="Output calibration profile JSON")
    parser.add_argument("--report", required=True, help="Output validation report JSON")
    parser.add_argument("--debug-dir", default=None)
    args = parser.parse_args()
    profile = run(args.manifest, args.output, args.report, args.debug_dir)
    validation = profile["validation"]
    print(f"Wrote tabletop calibration {args.output}")
    print(f"Points={validation['point_count']} RMSE={validation['rmse_cm']:.3f}cm max={validation['max_error_cm']:.3f}cm")


if __name__ == "__main__":
    main()
