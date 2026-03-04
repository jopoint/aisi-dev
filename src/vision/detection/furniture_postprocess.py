"""
Post-processing utilities for furniture detection masks.

Provides geometric fitting (min-area rectangle, circle) and filtering
based on area and aspect ratio constraints.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple


def ensure_int_coords(coords: np.ndarray) -> List[List[int]]:
    """
    Convert coordinate array to list of integer coordinates.
    
    Args:
        coords: Array of coordinates (N, 2)
    
    Returns:
        List of [x, y] integer coordinate lists
    """
    return [[int(x), int(y)] for x, y in coords]


def compute_bbox_from_corners(corners: np.ndarray) -> List[int]:
    """
    Compute bounding box from corner coordinates.
    
    Args:
        corners: Array of corner coordinates (4, 2) or similar
    
    Returns:
        [x1, y1, x2, y2] format bbox
    """
    x_coords = corners[:, 0]
    y_coords = corners[:, 1]
    
    x1 = int(np.floor(np.min(x_coords)))
    y1 = int(np.floor(np.min(y_coords)))
    x2 = int(np.ceil(np.max(x_coords)))
    y2 = int(np.ceil(np.max(y_coords)))
    
    return [x1, y1, x2, y2]


def mask_to_min_area_rect(mask: np.ndarray) -> Optional[Dict]:
    """
    Fit a minimum-area rotated rectangle to a binary mask.
    
    Args:
        mask: Binary mask (H, W) as bool or uint8
    
    Returns:
        Dictionary with:
            - center_px: [cx, cy] in pixels
            - yaw_rad: Rotation angle in radians (CCW from positive x-axis)
            - corners_px: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] integer coordinates
            - area_px: Area of the fitted rectangle in pixels
            - bbox_px: [x1, y1, x2, y2] bounding box
        Or None if no contours found
    """
    mask_uint8 = mask.astype(np.uint8)
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        # No contours found
        return None
    
    # Use largest contour
    contour = max(contours, key=cv2.contourArea)
    
    # Fit minimum area rectangle
    rect = cv2.minAreaRect(contour)
    center, size, angle_deg = rect
    
    # Convert angle to radians (OpenCV angle is in degrees, CW from horizontal)
    # Convert to CCW from positive x-axis
    yaw_rad = -np.deg2rad(angle_deg)
    
    # Get corner points
    box = cv2.boxPoints(rect)
    rect_corners_px = box.astype(np.float32)
    
    # Compute area
    w, h = size
    area_px = float(w * h)
    
    # Compute bounding box
    bbox_px = compute_bbox_from_corners(rect_corners_px)
    
    # Convert corners to integer coordinates
    corners_int = ensure_int_coords(rect_corners_px)
    
    return {
        "center_px": [float(center[0]), float(center[1])],
        "yaw_rad": float(yaw_rad),
        "corners_px": corners_int,
        "area_px": area_px,
        "bbox_px": bbox_px
    }


def mask_to_circle(mask: np.ndarray) -> Optional[Dict]:
    """
    Fit a minimum enclosing circle to a binary mask.
    
    Args:
        mask: Binary mask (H, W) as bool or uint8
    
    Returns:
        Dictionary with:
            - center_px: [cx, cy] in pixels
            - radius_px: Radius in pixels
            - area_px: Area of the fitted circle in pixels
            - bbox_px: [x1, y1, x2, y2] bounding box
        Or None if no contours found
    """
    mask_uint8 = mask.astype(np.uint8)
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        return None
    
    # Use largest contour
    contour = max(contours, key=cv2.contourArea)
    
    # Fit minimum enclosing circle
    (cx, cy), radius = cv2.minEnclosingCircle(contour)
    center_px = [float(cx), float(cy)]
    radius_px = float(radius)
    area_px = float(np.pi * radius_px ** 2)
    
    # Compute bounding box
    bbox_px = [int(cx - radius), int(cy - radius), int(cx + radius), int(cy + radius)]
    
    return {
        "center_px": center_px,
        "radius_px": radius_px,
        "area_px": area_px,
        "bbox_px": bbox_px
    }


def filter_mask_by_area(
    mask: np.ndarray,
    min_area_px: Optional[float] = None,
    max_area_px: Optional[float] = None
) -> bool:
    """
    Check if mask area is within specified bounds.
    
    Args:
        mask: Binary mask (H, W)
        min_area_px: Minimum area in pixels (inclusive), or None for no min
        max_area_px: Maximum area in pixels (inclusive), or None for no max
    
    Returns:
        True if mask passes area filter, False otherwise
    """
    area = np.count_nonzero(mask)
    
    if min_area_px is not None and area < min_area_px:
        return False
    if max_area_px is not None and area > max_area_px:
        return False
    
    return True


def filter_rect_by_aspect_ratio(
    rect_corners_px: np.ndarray,
    min_aspect: float = 1.0,
    max_aspect: float = 10.0
) -> bool:
    """
    Check if fitted rectangle aspect ratio is within bounds.
    
    Aspect ratio is defined as max(width/height, height/width),
    so it's always >= 1.0.
    
    Args:
        rect_corners_px: (4, 2) array of rectangle corners
        min_aspect: Minimum aspect ratio (>= 1.0)
        max_aspect: Maximum aspect ratio
    
    Returns:
        True if aspect ratio is within bounds, False otherwise
    """
    # Compute side lengths
    p0, p1, p2, p3 = rect_corners_px
    side1 = np.linalg.norm(p1 - p0)
    side2 = np.linalg.norm(p2 - p1)
    
    if side1 == 0 or side2 == 0:
        return False
    
    # Aspect ratio (always >= 1)
    aspect = max(side1 / side2, side2 / side1)
    
    return min_aspect <= aspect <= max_aspect


def filter_furniture_mask(
    mask: np.ndarray,
    class_name: str,
    min_area_px: Optional[float] = None,
    max_area_px: Optional[float] = None,
    check_aspect: bool = False,
    min_aspect: float = 1.5,
    max_aspect: float = 5.0
) -> bool:
    """
    Apply class-specific filters to a furniture mask.
    
    Args:
        mask: Binary mask (H, W)
        class_name: "table" or "chair"
        min_area_px: Minimum area constraint
        max_area_px: Maximum area constraint
        check_aspect: Whether to check aspect ratio (typically for tables)
        min_aspect: Minimum aspect ratio for rectangles (>= 1.0)
        max_aspect: Maximum aspect ratio for rectangles
    
    Returns:
        True if mask passes all filters, False otherwise
    """
    # Area filter
    if not filter_mask_by_area(mask, min_area_px, max_area_px):
        return False
    
    # Aspect ratio filter (optional, typically for tables)
    if check_aspect:
        rect_dict = mask_to_min_area_rect(mask)
        if rect_dict is None:
            return False
        rect_corners = np.array(rect_dict["corners_px"])
        if not filter_rect_by_aspect_ratio(rect_corners, min_aspect, max_aspect):
            return False
    
    return True


def postprocess_furniture_masks(
    masks: list[dict],
    class_name: str,
    min_area_px: Optional[float] = None,
    max_area_px: Optional[float] = None,
    fit_shape: str = "rect"  # "rect" or "circle"
) -> list[dict]:
    """
    Post-process a list of furniture masks with filtering and geometric fitting.
    
    Args:
        masks: List of mask_dict from segmentation (must have "mask" key)
        class_name: "table" or "chair"
        min_area_px: Minimum area filter
        max_area_px: Maximum area filter
        fit_shape: "rect" for min-area rectangle, "circle" for enclosing circle
    
    Returns:
        List of mask_dict with added geometry fields:
            - For "rect": center_px, yaw_rad, rect_corners_px, area_px
            - For "circle": center_px, radius_px, area_px
    """
    # Class-specific defaults
    check_aspect = (class_name == "table")
    
    filtered = []
    
    for mask_dict in masks:
        mask = mask_dict["mask"]
        
        # Apply filters
        if not filter_furniture_mask(
            mask,
            class_name,
            min_area_px=min_area_px,
            max_area_px=max_area_px,
            check_aspect=check_aspect
        ):
            continue
        
        # Fit geometry
        result = mask_dict.copy()
        
        if fit_shape == "rect":
            rect_dict = mask_to_min_area_rect(mask)
            if rect_dict is None:
                continue
            result.update(rect_dict)
            result["fit_area_px"] = rect_dict["area_px"]
        elif fit_shape == "circle":
            circle_dict = mask_to_circle(mask)
            if circle_dict is None:
                continue
            result.update(circle_dict)
            result["fit_area_px"] = circle_dict["area_px"]
        else:
            raise ValueError(f"Unknown fit_shape: {fit_shape}")
        
        filtered.append(result)
    
    return filtered
