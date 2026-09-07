from pathlib import Path
import shutil

ROOT = Path(
    r"C:\dev\Promotion_Prototypen\AISI\data\vision\training\rect_v1"
)

PRED = Path(
    r"C:\dev\Promotion_Prototypen\AISI\runs\obb\runs\obb\rect_v0_predictions\labels"
)

TRUE = ROOT / "dataset_obb" / "labels" / "train"
OUT = ROOT / "dataset_obb_v1" / "labels" / "train"

IMAGES_SRC = ROOT / "dataset_obb" / "images" / "train"
IMAGES_OUT = ROOT / "dataset_obb_v1" / "images" / "train"


def strip_confidence(line: str) -> str:
    parts = line.strip().split()

    # Expected prediction:
    # class + 8 OBB coords + confidence = 10 values
    if len(parts) == 10:
        return " ".join(parts[:9])

    # Already clean OBB label
    if len(parts) == 9:
        return line.strip()

    raise ValueError(f"Unexpected OBB label format: {line}")


def main():
    if OUT.parent.parent.exists():
        shutil.rmtree(OUT.parent.parent)

    OUT.mkdir(parents=True, exist_ok=True)
    IMAGES_OUT.mkdir(parents=True, exist_ok=True)

    true_names = {p.name for p in TRUE.glob("*.txt")}

    copied_true = 0
    copied_pseudo = 0

    for image in IMAGES_SRC.glob("*.jpg"):
        shutil.copy2(image, IMAGES_OUT / image.name)

        label_name = image.with_suffix(".txt").name

        true_label = TRUE / label_name
        pred_label = PRED / label_name
        out_label = OUT / label_name

        if true_label.exists():
            shutil.copy2(true_label, out_label)
            copied_true += 1
            continue

        if pred_label.exists():
            lines = [
                strip_confidence(x)
                for x in pred_label.read_text(
                    encoding="utf-8"
                ).splitlines()
                if x.strip()
            ]

            out_label.write_text(
                "\n".join(lines) + "\n",
                encoding="utf-8",
            )

            copied_pseudo += 1

    print("")
    print("==============================")
    print(f"True labels:   {copied_true}")
    print(f"Pseudo labels: {copied_pseudo}")
    print(f"Total labels:  {copied_true + copied_pseudo}")
    print(f"Output:        {OUT.parent.parent}")
    print("==============================")


if __name__ == "__main__":
    main()