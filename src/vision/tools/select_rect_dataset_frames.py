from pathlib import Path
import shutil


SRC_DIR = Path(
    r"C:\dev\Promotion_Prototypen\AISI\data\vision\training\rect_v1\frames"
)

OUT_DIR = Path(
    r"C:\dev\Promotion_Prototypen\AISI\data\vision\training\rect_v1\frames_selected"
)

# Every N-th frame per clip.
DEFAULT_STEP = 3

# Keep difficult scenes denser.
SPECIAL_STEPS = {
    "rect_09_occlusion": 2,
    "rect_09_occlusion_2": 2,
    "rect_11_border_cases": 2,
    "rect_11_border_cases_2": 2,
    "rect_12_messy": 2,
}


def main():
    if not SRC_DIR.exists():
        raise RuntimeError(f"Source directory does not exist: {SRC_DIR}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    clip_dirs = sorted(
        p for p in SRC_DIR.iterdir()
        if p.is_dir()
    )

    total_source = 0
    total_selected = 0

    for clip_dir in clip_dirs:
        images = sorted(clip_dir.glob("*.jpg"))

        if not images:
            continue

        step = SPECIAL_STEPS.get(
            clip_dir.name,
            DEFAULT_STEP,
        )

        clip_out = OUT_DIR / clip_dir.name
        clip_out.mkdir(parents=True, exist_ok=True)

        selected = images[::step]

        for image_path in selected:
            shutil.copy2(
                image_path,
                clip_out / image_path.name,
            )

        total_source += len(images)
        total_selected += len(selected)

        print(
            f"{clip_dir.name}: "
            f"{len(images)} -> {len(selected)} "
            f"(step={step})"
        )

    print("")
    print("==============================")
    print(f"Source images:   {total_source}")
    print(f"Selected images: {total_selected}")
    print(f"Output: {OUT_DIR}")
    print("==============================")


if __name__ == "__main__":
    main()