from pathlib import Path
import shutil


ROOT = Path(
    r"C:\dev\Promotion_Prototypen\AISI\data\vision\training\rect_v1"
)

SRC = ROOT / "frames"
DST = ROOT / "dataset_obb"


TRAIN_CLIPS = {
    "rect_01_center",
    "rect_02_top",
    "rect_03_bottom",
    "rect_04_edges",
    "rect_05_two_separate",
    "rect_06_two_close",
    "rect_07_three",
    "rect_08_multi",
    "rect_09_occlusion",
    "rect_10_motion",
}

VAL_CLIPS = {
    "rect_09_occlusion_2",
    "rect_11_border_cases",
}

TEST_CLIPS = {
    "rect_11_border_cases_2",
    "rect_12_messy",
}


def copy_clip(clip_name: str, split: str) -> int:
    src_dir = SRC / clip_name

    if not src_dir.exists():
        raise RuntimeError(f"Missing clip directory: {src_dir}")

    dst_dir = DST / "images" / split
    dst_dir.mkdir(parents=True, exist_ok=True)

    count = 0

    for image_path in sorted(src_dir.glob("*.jpg")):
        shutil.copy2(
            image_path,
            dst_dir / image_path.name,
        )
        count += 1

    return count


def main():
    if DST.exists():
        shutil.rmtree(DST)

    for split in ("train", "val", "test"):
        (DST / "images" / split).mkdir(
            parents=True,
            exist_ok=True,
        )
        (DST / "labels" / split).mkdir(
            parents=True,
            exist_ok=True,
        )

    totals = {}

    for split, clips in (
        ("train", TRAIN_CLIPS),
        ("val", VAL_CLIPS),
        ("test", TEST_CLIPS),
    ):
        total = 0

        for clip in sorted(clips):
            count = copy_clip(clip, split)
            total += count
            print(f"{split:5} {clip}: {count}")

        totals[split] = total

    yaml_text = """path: .
train: images/train
val: images/val
test: images/test

names:
  0: table
"""

    (DST / "data.yaml").write_text(
        yaml_text,
        encoding="utf-8",
    )

    print("")
    print("==============================")
    print(f"Train: {totals['train']}")
    print(f"Val:   {totals['val']}")
    print(f"Test:  {totals['test']}")
    print(f"Total: {sum(totals.values())}")
    print(f"Dataset: {DST}")
    print("==============================")


if __name__ == "__main__":
    main()