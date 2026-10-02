from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

IMAGE_DIR = ROOT / "datasets" / "plantseg" / "images" / "train"
MASK_DIR = ROOT / "datasets" / "plantseg" / "annotations" / "train"

images = sorted(IMAGE_DIR.glob("*.jpg"))

print("=" * 60)
print("PlantSeg MASK DIAGNOSTIC")
print("=" * 60)

print("Images:", len(images))
print("Masks:", len(list(MASK_DIR.glob("*.png"))))

foreground_ratios = []

checked = 0

for image_path in images[:100]:

    mask_path = MASK_DIR / f"{image_path.stem}.png"

    if not mask_path.exists():
        continue

    mask = cv2.imread(
        str(mask_path),
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:
        continue

    binary = mask > 0

    total_pixels = binary.size
    foreground_pixels = np.count_nonzero(binary)

    ratio = (
        foreground_pixels
        / total_pixels
        * 100
    )

    foreground_ratios.append(ratio)

    print(
        f"{image_path.name:55s} "
        f"mask_min={mask.min():3d} "
        f"mask_max={mask.max():3d} "
        f"foreground={ratio:7.3f}%"
    )

    checked += 1


print("=" * 60)

if foreground_ratios:

    print("Checked:", checked)
    print(
        "Minimum foreground %:",
        round(min(foreground_ratios), 4)
    )

    print(
        "Maximum foreground %:",
        round(max(foreground_ratios), 4)
    )

    print(
        "Average foreground %:",
        round(
            float(np.mean(foreground_ratios)),
            4
        )
    )

    print(
        "Median foreground %:",
        round(
            float(np.median(foreground_ratios)),
            4
        )
    )

    print(
        "Masks with >0 foreground:",
        sum(
            x > 0
            for x in foreground_ratios
        ),
        "/",
        len(foreground_ratios)
    )

else:

    print("ERROR: No valid masks found.")

print("=" * 60)