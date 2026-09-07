import cv2
import time
from pathlib import Path


def fourcc_to_str(value: float) -> str:
    value = int(value)
    return "".join(chr((value >> (8 * i)) & 0xFF) for i in range(4))


def main():
    camera = 0
    duration_s = 30
    requested_width = 1920
    requested_height = 1080
    requested_fps = 30.0

    out_path = Path(r"data\vision\debug\new_room_baseline.avi")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(camera, cv2.CAP_DSHOW)

    if not cap.isOpened():
        raise RuntimeError("Could not open camera")

    # Explicitly request MJPEG capture to reduce USB bandwidth.
    cap.set(
        cv2.CAP_PROP_FOURCC,
        cv2.VideoWriter_fourcc(*"MJPG"),
    )
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, requested_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, requested_height)
    cap.set(cv2.CAP_PROP_FPS, requested_fps)

    print("Requested capture:")
    print(f"  Resolution: {requested_width}x{requested_height}")
    print(f"  FPS: {requested_fps}")
    print("")

    # Warm up camera / auto exposure.
    print("Warming up camera...")
    frame = None

    for i in range(30):
        ok, frame = cap.read()

        if not ok:
            cap.release()
            raise RuntimeError(
                f"Could not read camera frame during warmup ({i + 1}/30)"
            )

    if frame is None:
        cap.release()
        raise RuntimeError("No frame received from camera")

    h, w = frame.shape[:2]

    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    actual_fourcc = fourcc_to_str(cap.get(cv2.CAP_PROP_FOURCC))

    print("Actual capture:")
    print(f"  Resolution: {w}x{h}")
    print(f"  Reported FPS: {actual_fps}")
    print(f"  FOURCC: {actual_fourcc}")
    print("")

    # Use the actual camera frame dimensions for the writer.
    writer_fourcc = cv2.VideoWriter_fourcc(*"MJPG")

    writer = cv2.VideoWriter(
        str(out_path),
        writer_fourcc,
        requested_fps,
        (w, h),
    )

    if not writer.isOpened():
        cap.release()
        raise RuntimeError("Could not open VideoWriter")

    print(f"Recording for {duration_s} seconds...")
    print(f"Output: {out_path}")
    print("")

    start = time.perf_counter()
    frames_written = 0
    read_failures = 0

    while True:
        elapsed = time.perf_counter() - start

        if elapsed >= duration_s:
            break

        ok, frame = cap.read()

        if not ok:
            read_failures += 1
            continue

        # Basic sanity check.
        if frame is None or frame.size == 0:
            read_failures += 1
            continue

        writer.write(frame)
        frames_written += 1

    total_time = time.perf_counter() - start

    writer.release()
    cap.release()

    measured_capture_fps = (
        frames_written / total_time
        if total_time > 0
        else 0.0
    )

    nominal_video_duration = (
        frames_written / requested_fps
        if requested_fps > 0
        else 0.0
    )

    print("")
    print("Recording finished.")
    print(f"Frames written: {frames_written}")
    print(f"Read failures: {read_failures}")
    print(f"Wall-clock duration: {total_time:.2f} s")
    print(f"Measured capture FPS: {measured_capture_fps:.2f}")
    print(
        f"Nominal AVI duration at {requested_fps:.1f} fps: "
        f"{nominal_video_duration:.2f} s"
    )
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()