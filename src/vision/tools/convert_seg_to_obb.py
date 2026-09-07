from pathlib import Path
import shutil


ROOT = Path(
    r"C:\dev\Promotion_Prototypen\AISI\data\vision\training\rect_v1"
)

SRC = ROOT / "cvat_export_seg" / "labels" / "train"
DST = ROOT / "cvat_export_obb_converted" / "labels" / "train"


def main():
    if not SRC.exists():
        raise RuntimeError(f"Source not found: {SRC}")

    if DST.parent.parent.exists():
        shutil.rmtree(DST.parent.parent)

    DST.mkdir(parents=True, exist_ok=True)

    files = sorted(SRC.glob("*.txt"))

    converted = 0
    skipped = 0

    for src_file in files:
        out_lines = []

        for raw_line in src_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()

            if not line:
                continue

            parts = line.split()

            class_id = parts[0]
            coords = parts[1:]

            # YOLO segmentation:
            # class x1 y1 x2 y2 x3 y3 ...
            if len(coords) != 8:
                print(
                    f"SKIP {src_file.name}: "
                    f"expected 4-point polygon (=8 coords), "
                    f"got {len(coords)} coords"
                )
                skipped += 1
                continue

            values = [float(v) for v in coords]

            if any(v < 0.0 or v > 1.0 for v in values):
                print(
                    f"SKIP {src_file.name}: "
                    "coordinates outside normalized [0,1] range"
                )
                skipped += 1
                continue

            out_line = class_id + " " + " ".join(
                f"{v:.6f}" for v in values
            )

            out_lines.append(out_line)

        dst_file = DST / src_file.name

        if out_lines:
            dst_file.write_text(
                "\n".join(out_lines) + "\n",
                encoding="utf-8",
            )
            converted += 1

    print("")
    print("==============================")
    print(f"Source label files: {len(files)}")
    print(f"Converted files:    {converted}")
    print(f"Skipped objects:    {skipped}")
    print(f"Output: {DST}")
    print("==============================")


if __name__ == "__main__":
    main()