import argparse
from pathlib import Path
import cv2
import time

def main():
    parser = argparse.ArgumentParser(description="Capture frame from USB camera and save as JPG.")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0).")
    parser.add_argument("--width", type=int, default=1920, help="Requested frame width.")
    parser.add_argument("--height", type=int, default=1080, help="Requested frame height.")
    parser.add_argument("--out", required=True, help="Output JPG file path.")
    parser.add_argument("--backend", choices=["msmf", "dshow"], default="msmf", help="Capture backend (default: msmf).")
    args = parser.parse_args()

    # Map backend names to cv2 constants
    backend_map = {
        "msmf": cv2.CAP_MSMF,
        "dshow": cv2.CAP_DSHOW,
    }
    backend_flag = backend_map[args.backend]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Open camera with backend
    print(f"Backend: {args.backend}, Camera: {args.camera}")
    cap = cv2.VideoCapture(args.camera, backend_flag)
    if not cap.isOpened():
        print(f"ERROR: Could not open camera {args.camera} with backend {args.backend}")
        return 1

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    print(f"Requested: {args.width}x{args.height}")

    # Read frames to stabilize auto-exposure
    print("Reading 30 frames to stabilize auto-exposure...")
    frame = None
    for i in range(30):
        ret, frame = cap.read()
        if not ret:
            print(f"ERROR: Failed to read frame {i}")
            cap.release()
            return 1
        if (i + 1) % 10 == 0:
            print(f"  Frame {i+1}/30")

    # Get actual frame size
    if frame is not None:
        h, w = frame.shape[:2]
        print(f"Actual: {w}x{h}")
        print(f"Saving to: {out_path}")
        # Save frame
        success = cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if success:
            print(f"✓ Frame saved successfully")
        else:
            print(f"ERROR: Failed to save frame to {out_path}")
            cap.release()
            return 1
    else:
        print("ERROR: No frame captured after 30 warmup frames")
        cap.release()
        return 1

    cap.release()
    return 0

if __name__ == "__main__":
    exit(main())
