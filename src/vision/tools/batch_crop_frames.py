import argparse
from pathlib import Path
import cv2

def parse_args():
    p = argparse.ArgumentParser(description="Batch crop all images in a folder.")
    p.add_argument("--in-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--roi", nargs=4, type=int, required=True, metavar=("X1","Y1","X2","Y2"))
    p.add_argument("--ext", default="jpg", choices=["jpg", "png"])
    return p.parse_args()

def main():
    args = parse_args()
    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    x1, y1, x2, y2 = args.roi
    if x2 <= x1 or y2 <= y1:
        raise SystemExit(f"Invalid ROI: {args.roi}")

    files = sorted(list(in_dir.glob("*.jpg")) + list(in_dir.glob("*.jpeg")) + list(in_dir.glob("*.png")))
    if not files:
        raise SystemExit(f"No images found in {in_dir}")

    n_ok = 0
    for fp in files:
        img = cv2.imread(str(fp), cv2.IMREAD_COLOR)
        if img is None:
            continue
        h, w = img.shape[:2]
        xx1 = max(0, min(w - 1, x1))
        yy1 = max(0, min(h - 1, y1))
        xx2 = max(0, min(w, x2))
        yy2 = max(0, min(h, y2))
        crop = img[yy1:yy2, xx1:xx2]
        out_path = out_dir / f"{fp.stem}.{args.ext}"
        if cv2.imwrite(str(out_path), crop):
            n_ok += 1

    print(f"Cropped {n_ok}/{len(files)} images -> {out_dir}  ROI={args.roi}")

if __name__ == "__main__":
    main()
