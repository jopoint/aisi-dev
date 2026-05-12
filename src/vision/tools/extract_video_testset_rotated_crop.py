"""Extract a rotated/cropped numbered JPG testset from a video.

Example:
  python -m src.vision.tools.extract_video_testset_rotated_crop \
    --video "C:\\path\\to\\video.mp4" \
    --out data\\vision\\testset_rotated \
    --fps 5 \
    --start-sec 0 \
    --end-sec 10 \
    --rotate 90 \
    --crop 64 282 1000 1291
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def _rotate_frame(frame, rotate: int):
    if rotate == 0:
        return frame
    if rotate == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if rotate == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if rotate == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    raise ValueError(f"Unsupported rotation: {rotate}")


def _validate_crop(crop: tuple[int, int, int, int], frame_w: int, frame_h: int) -> tuple[int, int, int, int]:
    x, y, w, h = crop
    if x < 0 or y < 0 or w <= 0 or h <= 0:
        raise ValueError("--crop requires x>=0 y>=0 w>0 h>0")

    if x + w > frame_w or y + h > frame_h:
        raise ValueError(
            f"Crop {crop} exceeds rotated frame bounds {frame_w}x{frame_h}. "
            f"Max allowed x+w <= {frame_w}, y+h <= {frame_h}."
        )

    return crop


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a numbered JPG sequence from a video with rotation and crop applied."
    )
    parser.add_argument("--video", required=True, help="Input video path.")
    parser.add_argument("--out", required=True, help="Output folder for JPG sequence.")
    parser.add_argument("--fps", type=float, required=True, help="Target extraction FPS (>0).")
    parser.add_argument("--start-sec", type=float, default=None, help="Optional start time in seconds.")
    parser.add_argument("--end-sec", type=float, default=None, help="Optional end time in seconds.")
    parser.add_argument("--rotate", type=int, choices=[0, 90, 180, 270], default=0, help="Rotate each frame before cropping.")
    parser.add_argument(
        "--crop",
        nargs=4,
        type=int,
        metavar=("X", "Y", "W", "H"),
        required=True,
        help="Crop ROI x y w h (applied after rotation).",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=95,
        help="JPEG quality 1..100 (default: 95).",
    )
    return parser.parse_args()


def _extract(
    video_path: Path,
    out_dir: Path,
    fps_target: float,
    start_sec: float | None,
    end_sec: float | None,
    rotate: int,
    crop: tuple[int, int, int, int],
    jpeg_quality: int,
) -> int:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    src_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    if src_fps <= 0:
        cap.release()
        raise RuntimeError("Video has invalid FPS metadata")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if frame_count <= 0:
        cap.release()
        raise RuntimeError("Video has invalid frame count")

    duration_sec = frame_count / src_fps

    start_sec = 0.0 if start_sec is None else float(start_sec)
    if start_sec < 0:
        cap.release()
        raise ValueError("--start-sec must be >= 0")

    end_sec = duration_sec if end_sec is None else float(end_sec)
    if end_sec < start_sec:
        cap.release()
        raise ValueError("--end-sec must be >= --start-sec")
    if end_sec > duration_sec:
        end_sec = duration_sec

    start_frame_idx = int(round(start_sec * src_fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, start_frame_idx))

    out_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    next_sample_sec = start_sec
    cur_frame_idx = max(0, start_frame_idx)
    crop_validated = False
    x, y, w, h = crop

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        t_sec = cur_frame_idx / src_fps
        if t_sec > end_sec:
            break

        if t_sec + (0.5 / src_fps) >= next_sample_sec:
            rotated = _rotate_frame(frame, rotate)

            if not crop_validated:
                rotated_h, rotated_w = rotated.shape[:2]
                _validate_crop(crop, rotated_w, rotated_h)
                crop_validated = True

            cropped = rotated[y : y + h, x : x + w]
            out_path = out_dir / f"frame_{saved:06d}.jpg"
            ok_write = cv2.imwrite(
                str(out_path),
                cropped,
                [cv2.IMWRITE_JPEG_QUALITY, int(jpeg_quality)],
            )
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


def main() -> None:
    args = _parse_args()

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

    crop = tuple(int(v) for v in args.crop)

    print("=== Extract Video Testset Rotated Crop ===")
    print(f"input video: {video_path}")
    print(f"rotate: {args.rotate}")
    print(f"crop: {crop}")
    print(f"fps: {args.fps}")
    print(f"start_sec: {args.start_sec if args.start_sec is not None else 0.0}")
    print(f"end_sec: {args.end_sec if args.end_sec is not None else 'video_end'}")
    print(f"output dir: {out_dir}")

    saved = _extract(
        video_path=video_path,
        out_dir=out_dir,
        fps_target=float(args.fps),
        start_sec=args.start_sec,
        end_sec=args.end_sec,
        rotate=int(args.rotate),
        crop=crop,
        jpeg_quality=int(args.jpeg_quality),
    )

    print(f"saved frames: {saved}")
    print(f"Done. Saved {saved} frame(s) to {out_dir}")


if __name__ == "__main__":
    main()