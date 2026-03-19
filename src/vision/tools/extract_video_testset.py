"""Extract a tracking testset (numbered JPG sequence) from a video.

Example:
  python -m src.vision.tools.extract_video_testset \
    --video "C:\\Users\\Johannes\\OneDrive\\Bilder\\Eigene Aufnahmen\\WIN_20260305_12_08_44_Pro.mp4" \
    --out data\\vision\\dataset\\frames_test_dense \
    --fps 5 \
        --crop 300 0 1277 1015
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Tuple

import cv2


def _validate_crop(crop: Tuple[int, int, int, int], frame_w: int, frame_h: int) -> Tuple[int, int, int, int]:
    """Validate ROI x,y,w,h (NOT x1,y1,x2,y2) against frame bounds (strict)."""
    x, y, w, h = crop
    if x < 0 or y < 0 or w <= 0 or h <= 0:
        raise ValueError("--crop requires x>=0 y>=0 w>0 h>0")

    x2 = x + w
    y2 = y + h
    if x2 > frame_w or y2 > frame_h:
        raise ValueError(
            f"Crop {crop} exceeds frame bounds {frame_w}x{frame_h}. "
            f"Max allowed x+w <= {frame_w}, y+h <= {frame_h}."
        )

    return crop


def _extract(
    video_path: Path,
    out_dir: Path,
    fps_target: float,
    crop: Tuple[int, int, int, int],
    start_sec: Optional[float],
    end_sec: Optional[float],
    resize_wh: Optional[Tuple[int, int]],
    jpeg_quality: int,
) -> int:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    src_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    if src_fps <= 0:
        cap.release()
        raise RuntimeError("Video has invalid FPS metadata")

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    if frame_w <= 0 or frame_h <= 0:
        cap.release()
        raise RuntimeError("Video has invalid frame dimensions")

    crop = _validate_crop(crop, frame_w, frame_h)

    duration_sec = (frame_count / src_fps) if frame_count > 0 else None

    start_sec = 0.0 if start_sec is None else float(start_sec)
    end_sec = None if end_sec is None else float(end_sec)
    if start_sec < 0:
        cap.release()
        raise ValueError("--start-sec must be >= 0")
    if end_sec is not None and end_sec < start_sec:
        cap.release()
        raise ValueError("--end-sec must be >= --start-sec")

    if duration_sec is not None:
        if start_sec > duration_sec:
            cap.release()
            raise ValueError(f"--start-sec ({start_sec:.3f}) exceeds duration ({duration_sec:.3f})")
        if end_sec is not None and end_sec > duration_sec:
            end_sec = duration_sec

    start_frame_idx = int(round(start_sec * src_fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, start_frame_idx))

    out_dir.mkdir(parents=True, exist_ok=True)

    next_sample_sec = start_sec
    cur_frame_idx = max(0, start_frame_idx)
    saved = 0

    x, y, w, h = crop
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        t_sec = cur_frame_idx / src_fps
        if end_sec is not None and t_sec > end_sec:
            break

        if t_sec + (0.5 / src_fps) >= next_sample_sec:
            out = frame[y : y + h, x : x + w]
            if resize_wh is not None:
                out = cv2.resize(out, resize_wh, interpolation=cv2.INTER_AREA)

            out_name = f"frame_{saved:06d}.jpg"
            out_path = out_dir / out_name
            ok_write = cv2.imwrite(str(out_path), out, [cv2.IMWRITE_JPEG_QUALITY, int(jpeg_quality)])
            if not ok_write:
                cap.release()
                raise RuntimeError(f"Failed to write image: {out_path}")

            saved += 1
            next_sample_sec += 1.0 / fps_target

        cur_frame_idx += 1

    cap.release()

    if saved == 0:
        raise RuntimeError("No frames extracted. Check --fps and time range.")

    return saved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract numbered JPG tracking testset from a video.")
    parser.add_argument("--video", required=True, help="Input video path.")
    parser.add_argument("--out", required=True, help="Output folder for JPG sequence.")
    parser.add_argument("--fps", type=float, required=True, help="Target extraction FPS (>0).")

    parser.add_argument("--start-sec", type=float, default=None, help="Optional start time in seconds.")
    parser.add_argument("--end-sec", type=float, default=None, help="Optional end time in seconds.")

    parser.add_argument("--crop", nargs=4, type=int, metavar=("X", "Y", "W", "H"), required=True, help="Crop ROI x y w h (NOT x1 y1 x2 y2).")

    parser.add_argument("--resize-w", type=int, default=None, help="Optional output width.")
    parser.add_argument("--resize-h", type=int, default=None, help="Optional output height.")
    parser.add_argument("--jpeg-quality", type=int, default=95, help="JPEG quality 1..100 (default: 95).")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    video_path = Path(args.video)
    out_dir = Path(args.out)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not video_path.is_file():
        raise ValueError(f"--video must point to a file: {video_path}")

    if args.fps <= 0:
        raise ValueError("--fps must be > 0")

    if not (1 <= int(args.jpeg_quality) <= 100):
        raise ValueError("--jpeg-quality must be in [1, 100]")

    if (args.resize_w is None) ^ (args.resize_h is None):
        raise ValueError("--resize-w and --resize-h must be set together")

    resize_wh: Optional[Tuple[int, int]] = None
    if args.resize_w is not None and args.resize_h is not None:
        if args.resize_w <= 0 or args.resize_h <= 0:
            raise ValueError("--resize-w and --resize-h must be > 0")
        resize_wh = (int(args.resize_w), int(args.resize_h))

    crop = tuple(int(v) for v in args.crop)

    print("=== Extract Video Testset ===")
    print(f"video: {video_path}")
    print(f"out: {out_dir}")
    print(f"fps: {args.fps}")
    print(f"start_sec: {args.start_sec if args.start_sec is not None else 0.0}")
    print(f"end_sec: {args.end_sec if args.end_sec is not None else 'video_end'}")
    print(f"crop: {crop}")
    print(f"resize: {resize_wh if resize_wh is not None else 'none'}")

    saved = _extract(
        video_path=video_path,
        out_dir=out_dir,
        fps_target=float(args.fps),
        crop=crop,
        start_sec=args.start_sec,
        end_sec=args.end_sec,
        resize_wh=resize_wh,
        jpeg_quality=int(args.jpeg_quality),
    )

    print(f"Done. Saved {saved} frame(s) to {out_dir}")


if __name__ == "__main__":
    main()
