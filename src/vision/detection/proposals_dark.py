"""
Dark-object proposal generator based on HSV V-channel thresholding + morphology + connected components.
"""

from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np


class DarkObjectProposer:
    def __init__(
        self,
        fixed_thresh: int = 85,
        invert: bool = False,
        drop_border_touching: bool = True,
        blur_ksize: int = 5,
        close_ksize: int = 7,
        close_iters: int = 1,
        open_ksize: int = 3,
        open_iters: int = 1,
        min_area: int = 500,
        max_area: Optional[int] = None,
        max_area_frac: float = 0.15,
        max_proposals_per_frame: int = 10,
        roi_bbox_px: Optional[List[int]] = None,
        debug_dir: Optional[str] = None,
        debug_every: int = 1,
    ):
        """
        Args:
            fixed_thresh: Threshold on HSV V-channel (0-255). V < threshold => foreground.
            invert: If True, invert the mask logic (V >= threshold => foreground).
            drop_border_touching: If True, exclude components touching image borders.
            blur_ksize: Gaussian blur kernel size (odd int, <=1 disables blur).
            close_ksize: Morphological close kernel size.
            close_iters: Close iterations.
            open_ksize: Morphological open kernel size.
            open_iters: Open iterations.
            min_area: Minimum component area (px).
            max_area: Optional maximum component area (px). If None, uses max_area_frac.
            max_area_frac: Fraction of frame area to use as default max_area (e.g., 0.15 = 15%).
            max_proposals_per_frame: Keep at most N boxes per frame (sorted by area desc).
            roi_bbox_px: Optional ROI [x1,y1,x2,y2]; boxes must intersect ROI.
            debug_dir: Optional output directory for debug images.
            debug_every: Save debug images every Nth frame.
        """
        if fixed_thresh < 0 or fixed_thresh > 255:
            raise ValueError(f"fixed_thresh must be in [0,255], got {fixed_thresh}")
        if max_proposals_per_frame < 1:
            raise ValueError("max_proposals_per_frame must be >= 1")
        if debug_every < 1:
            raise ValueError("debug_every must be >= 1")
        if max_area_frac < 0 or max_area_frac > 1:
            raise ValueError(f"max_area_frac must be in [0,1], got {max_area_frac}")

        self.fixed_thresh = fixed_thresh
        self.invert = invert
        self.drop_border_touching = drop_border_touching

        self.blur_ksize = self._normalize_kernel_size(blur_ksize)
        self.close_ksize = self._normalize_kernel_size(close_ksize)
        self.close_iters = max(0, int(close_iters))
        self.open_ksize = self._normalize_kernel_size(open_ksize)
        self.open_iters = max(0, int(open_iters))

        self.min_area = max(0, int(min_area))
        self.max_area = None if max_area is None else max(0, int(max_area))
        self.max_area_frac = float(max_area_frac)
        self.max_proposals_per_frame = int(max_proposals_per_frame)

        self.roi_bbox_px = self._normalize_bbox(roi_bbox_px) if roi_bbox_px is not None else None

        self.debug_dir = Path(debug_dir) if debug_dir else None
        self.debug_every = int(debug_every)

        self._close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.close_ksize, self.close_ksize))
        self._open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.open_ksize, self.open_ksize))

        if self.debug_dir is not None:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

    def propose(self, frame_bgr: np.ndarray, frame_id: int) -> List[List[int]]:
        """
        Propose bounding boxes for dark objects via HSV V-channel thresholding + connected components.

        Args:
            frame_bgr: Input image in BGR format.
            frame_id: Current frame index (used for debug filenames/logging).

        Returns:
            List of bounding boxes in pixel coords: [[x1,y1,x2,y2], ...]
        """
        if frame_bgr is None or frame_bgr.size == 0:
            print(f"[DarkObjectProposer][frame {frame_id}] raw=0 after_max_area=0 after_border=0 after_extent=0 kept=0 largest_area=0")
            return []

        h, w = frame_bgr.shape[:2]
        frame_area = h * w
        max_area = self.max_area if self.max_area is not None else int(frame_area * self.max_area_frac)

        # 1. Convert to HSV and extract V-channel
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        v_channel = hsv[:, :, 2]

        # 2. Apply blur if enabled
        if self.blur_ksize > 1:
            v_channel = cv2.GaussianBlur(v_channel, (self.blur_ksize, self.blur_ksize), 0)

        # 3. Threshold: V < fixed_thresh => foreground (dark objects)
        if not self.invert:
            mask = (v_channel < self.fixed_thresh).astype(np.uint8) * 255
        else:
            mask = (v_channel >= self.fixed_thresh).astype(np.uint8) * 255

        # 4. Morphological operations
        if self.close_iters > 0 and self.close_ksize > 1:
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self._close_kernel, iterations=self.close_iters)
        if self.open_iters > 0 and self.open_ksize > 1:
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._open_kernel, iterations=self.open_iters)

        # 5. Connected components analysis
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(
            mask, connectivity=8, ltype=cv2.CV_32S
        )

        raw_boxes = []
        max_area_pass_boxes = []
        border_pass_boxes = []
        extent_pass_boxes = []
        kept_candidates = []
        largest_area = 0.0

        # Skip label 0 (background)
        for label_id in range(1, num_labels):
            x, y, box_w, box_h, area = stats[label_id]
            area = float(area)
            largest_area = max(largest_area, area)

            bbox = [int(x), int(y), int(x + box_w), int(y + box_h)]
            raw_boxes.append((bbox, area))

            if area < self.min_area:
                continue
            if area > max_area:
                continue
            max_area_pass_boxes.append((bbox, area))

            # 6. Drop components touching border
            if self.drop_border_touching:
                if x <= 0 or y <= 0 or (x + box_w) >= (w - 1) or (y + box_h) >= (h - 1):
                    continue
            border_pass_boxes.append((bbox, area))

            bbox_area = float(max(1, box_w * box_h))
            extent = area / bbox_area
            if extent < 0.30:
                continue
            extent_pass_boxes.append((bbox, area))

            # 8. Filter by ROI intersection
            if self.roi_bbox_px is not None and not self._intersects(bbox, self.roi_bbox_px):
                continue
            kept_candidates.append((bbox, area))

        # 9. Sort by area (descending) and cap
        kept_candidates.sort(key=lambda item: item[1], reverse=True)
        kept = kept_candidates[: self.max_proposals_per_frame]
        kept_boxes = [bbox for bbox, _ in kept]

        print(
            f"[DarkObjectProposer][frame {frame_id}] "
            f"raw={len(raw_boxes)} after_max_area={len(max_area_pass_boxes)} "
            f"after_border={len(border_pass_boxes)} after_extent={len(extent_pass_boxes)} "
            f"kept={len(kept_boxes)} largest_area={largest_area:.1f}"
        )

        if self._should_debug(frame_id):
            self._save_debug_images(
                frame_bgr=frame_bgr,
                mask=mask,
                frame_id=frame_id,
                raw_boxes=[bbox for bbox, _ in raw_boxes],
                kept_boxes=kept_boxes,
            )

        return kept_boxes

    def _should_debug(self, frame_id: int) -> bool:
        return self.debug_dir is not None and (frame_id % self.debug_every == 0)

    def _save_debug_images(
        self,
        frame_bgr: np.ndarray,
        mask: np.ndarray,
        frame_id: int,
        raw_boxes: List[List[int]],
        kept_boxes: List[List[int]],
    ) -> None:
        if self.debug_dir is None:
            return

        self.debug_dir.mkdir(parents=True, exist_ok=True)

        mask_path = self.debug_dir / f"binary_mask_{frame_id:05d}.png"
        raw_path = self.debug_dir / f"raw_boxes_{frame_id:05d}.png"
        kept_path = self.debug_dir / f"kept_boxes_{frame_id:05d}.png"

        cv2.imwrite(str(mask_path), mask)

        raw_vis = frame_bgr.copy()
        kept_vis = frame_bgr.copy()

        if self.roi_bbox_px is not None:
            rx1, ry1, rx2, ry2 = self.roi_bbox_px
            cv2.rectangle(raw_vis, (rx1, ry1), (rx2, ry2), (255, 255, 0), 2)
            cv2.rectangle(kept_vis, (rx1, ry1), (rx2, ry2), (255, 255, 0), 2)

        for idx, bbox in enumerate(raw_boxes):
            x1, y1, x2, y2 = bbox
            cv2.rectangle(raw_vis, (x1, y1), (x2, y2), (0, 140, 255), 2)
            cv2.putText(raw_vis, str(idx), (x1, max(20, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)

        for idx, bbox in enumerate(kept_boxes):
            x1, y1, x2, y2 = bbox
            cv2.rectangle(kept_vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(kept_vis, str(idx), (x1, max(20, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.imwrite(str(raw_path), raw_vis)
        cv2.imwrite(str(kept_path), kept_vis)

    @staticmethod
    def _normalize_kernel_size(value: int) -> int:
        value = int(value)
        if value <= 1:
            return 1
        if value % 2 == 0:
            value += 1
        return value

    @staticmethod
    def _normalize_bbox(bbox: List[int]) -> List[int]:
        if len(bbox) != 4:
            raise ValueError(f"roi_bbox_px must be [x1,y1,x2,y2], got {bbox}")
        x1, y1, x2, y2 = [int(v) for v in bbox]
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        return [x1, y1, x2, y2]

    @staticmethod
    def _intersects(box_a: List[int], box_b: List[int]) -> bool:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)
        return ix2 > ix1 and iy2 > iy1
