import argparse
import cv2
import os
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Probe connected cameras and optionally save snapshots.")
    parser.add_argument("--max-index", type=int, default=30, help="Maximum camera index to test.")
    parser.add_argument("--width", type=int, default=1920, help="Requested frame width.")
    parser.add_argument("--height", type=int, default=1080, help="Requested frame height.")
    parser.add_argument("--save-snapshots", action="store_true", help="Save a snapshot from each camera that produces a frame.")
    parser.add_argument("--backend", choices=["dshow", "msmf", "any"], default="any", help="Preferred capture backend.")
    args = parser.parse_args()

    snapshot_dir = Path("data/vision/test_frames")
    if args.save_snapshots:
        snapshot_dir.mkdir(parents=True, exist_ok=True)

    # map backend names to cv2 constants
    backend_map = {
        "dshow": cv2.CAP_DSHOW,
        "msmf": cv2.CAP_MSMF,
    }

    for i in range(args.max_index + 1):
        # choose backend(s) to try based on user preference
        tried = []
        cap = None
        used_backend = None
        backends_to_try = []
        if args.backend == "any":
            backends_to_try = ["msmf", "dshow"]
        else:
            backends_to_try = [args.backend]
        for b in backends_to_try:
            backend_flag = backend_map.get(b, cv2.CAP_ANY)
            cap = cv2.VideoCapture(i, backend_flag)
            tried.append(b)
            if cap.isOpened():
                used_backend = b
                break
            else:
                cap.release()
                cap = None
        if cap is None or not cap.isOpened():
            print(f"index {i}: cannot open (tried {tried})")
            continue
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        # warm up
        frame = None
        for _ in range(30):
            ret, frame = cap.read()
            if not ret:
                frame = None
            else:
                pass
        if frame is None:
            print(f"backend {used_backend}, index {i}: opened but no frames")
            cap.release()
            continue
        h, w = frame.shape[:2]
        print(f"backend {used_backend}, index {i}: requested {args.width}x{args.height}, got {w}x{h}")
        if args.save_snapshots:
            fname = snapshot_dir / f"{used_backend}_index_{i}_{w}x{h}.jpg"
            cv2.imwrite(str(fname), frame)
            print(f"   saved snapshot: {fname}")
        cap.release()
        # small delay so cameras aren't slammed
        time.sleep(0.1)

if __name__ == "__main__":
    main()
