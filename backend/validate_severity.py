"""
Harvest Harbor
Severity Validation
------------------

Purpose:
    Validate project-defined severity tiers by comparing:

        Ground-truth lesion mask
                    vs
        U-Net predicted lesion mask

Important:
    The severity thresholds used by this project are
    project-defined initial thresholds.

    They are NOT expert-validated or agronomically standard
    severity thresholds.

    Expert/agronomist visual-scale validation requires
    an external expert-annotated dataset.
"""

import os
import sys
import argparse
from pathlib import Path

# ============================================================
# PATHS & ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure Keras home points to backend/.keras so TF does not attempt to read ~/.keras/keras.json
os.environ["KERAS_HOME"] = str(BASE_DIR / ".keras")

import numpy as np
from PIL import Image

from segmentation import LeafSegmenter

from severity import (
    calculate_affected_area,
    classify_severity,
)

PLANTSEG_DIR = (
    BASE_DIR.parent /
    "datasets" /
    "plantseg"
)

IMAGE_DIR = (
    PLANTSEG_DIR /
    "images" /
    "test"
)

MASK_DIR = (
    PLANTSEG_DIR /
    "annotations" /
    "test"
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_NUM_SAMPLES = 50

RANDOM_SEED = 42


# ============================================================
# ARGUMENT PARSER
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Harvest Harbor — Quantitative "
            "Severity Threshold Validation"
        )
    )

    parser.add_argument(
        "--num-samples",
        type=int,
        default=DEFAULT_NUM_SAMPLES,
        help=(
            "Number of test pairs to evaluate. "
            "Use 0 to evaluate all verified pairs."
        ),
    )

    return parser.parse_args()


# ============================================================
# FIND IMAGE / MASK PAIRS
# ============================================================

def find_test_pairs():

    if not IMAGE_DIR.exists():

        raise FileNotFoundError(
            f"Image directory not found: "
            f"{IMAGE_DIR}"
        )

    if not MASK_DIR.exists():

        raise FileNotFoundError(
            f"Mask directory not found: "
            f"{MASK_DIR}"
        )

    # --------------------------------------------------------
    # Find test images
    # --------------------------------------------------------

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

    image_files = sorted(
        [
            p
            for p in IMAGE_DIR.iterdir()
            if (
                p.is_file()
                and
                p.suffix.lower()
                in image_extensions
            )
        ]
    )

    pairs = []

    missing_masks = []

    # --------------------------------------------------------
    # Match by filename stem
    #
    # Example:
    #
    # image:
    #     apple_black_rot_143.jpg
    #
    # mask:
    #     apple_black_rot_143.png
    # --------------------------------------------------------

    for image_path in image_files:

        mask_path = (
            MASK_DIR /
            f"{image_path.stem}.png"
        )

        if mask_path.exists():

            pairs.append(
                (
                    image_path,
                    mask_path
                )
            )

        else:

            missing_masks.append(
                image_path.name
            )

    print(
        f"[INFO] Images found: "
        f"{len(image_files)}"
    )

    print(
        f"[INFO] Matching image/mask pairs: "
        f"{len(pairs)}"
    )

    if missing_masks:

        print(
            f"[WARN] Images without masks: "
            f"{len(missing_masks)}"
        )

        for name in missing_masks[:10]:

            print(
                f"       {name}"
            )

    return pairs


# ============================================================
# SELECT SAMPLES
# ============================================================

def select_pairs(
    pairs,
    num_samples
):

    if not pairs:

        return []

    # --------------------------------------------------------
    # 0 means ALL
    # --------------------------------------------------------

    if num_samples == 0:

        return list(pairs)

    if num_samples < 0:

        raise ValueError(
            "--num-samples must be >= 0"
        )

    # --------------------------------------------------------
    # Requested samples >= available
    # --------------------------------------------------------

    if num_samples >= len(pairs):

        return list(pairs)

    # --------------------------------------------------------
    # Reproducible random selection
    # --------------------------------------------------------

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    indices = rng.choice(
        len(pairs),
        size=num_samples,
        replace=False
    )

    indices = sorted(
        indices.tolist()
    )

    return [
        pairs[index]
        for index in indices
    ]


# ============================================================
# GROUND-TRUTH AREA
# ============================================================

def calculate_ground_truth_area(
    mask_path,
    image_path=None,
    segmenter=None
):

    mask = np.array(
        Image.open(mask_path).convert("L")
    )

    # --------------------------------------------------------
    # Pixels above 10 are treated as lesion/diseased pixels
    # --------------------------------------------------------

    diseased_pixels = int(
        np.sum(
            mask > 10
        )
    )

    # --------------------------------------------------------
    # Denominator pixels:
    # If image & segmenter are provided, compute detected leaf pixels
    # to match model's prediction methodology (lesion / leaf area).
    # Otherwise fallback to complete mask area.
    # --------------------------------------------------------

    total_pixels = (
        mask.shape[0] *
        mask.shape[1]
    )
    denominator_pixels = total_pixels

    if image_path is not None and segmenter is not None:
        try:
            img_rgb = np.array(Image.open(image_path).convert("RGB"))
            leaf_mask = segmenter._extract_leaf_mask(img_rgb)
            leaf_pixels = int(np.count_nonzero(leaf_mask))
            if leaf_pixels > 0:
                denominator_pixels = leaf_pixels
        except Exception as e:
            logger.warning(f"Could not extract leaf mask for {image_path}: {e}")

    area_percent = (
        calculate_affected_area(
            diseased_pixels,
            denominator_pixels
        )
    )

    tier = classify_severity(
        area_percent
    )

    return (
        area_percent,
        tier,
        diseased_pixels,
        denominator_pixels
    )


# ============================================================
# PREDICTED AREA
# ============================================================

def get_predicted_area(
    segmentation_result
):

    if not segmentation_result:

        return None

    if not segmentation_result.get(
        "available",
        False
    ):

        return None

    # ========================================================
    # IMPORTANT FIX
    #
    # LeafSegmenter returns:
    #
    #     affected_ratio
    #     affected_percentage
    #
    # It does NOT return:
    #
    #     affected_area_percent
    # ========================================================

    if (
        "affected_percentage"
        not in segmentation_result
    ):

        return None

    value = (
        segmentation_result[
            "affected_percentage"
        ]
    )

    if value is None:

        return None

    try:

        value = float(value)

    except (
        TypeError,
        ValueError
    ):

        return None

    if not np.isfinite(value):

        return None

    # --------------------------------------------------------
    # Keep percentage inside valid range
    # --------------------------------------------------------

    value = max(
        0.0,
        min(
            100.0,
            value
        )
    )

    return value


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_args()

    print("=" * 65)

    print(
        "HARVEST HARBOR — "
        "QUANTITATIVE SEVERITY THRESHOLD VALIDATION"
    )

    print("=" * 65)

    # ========================================================
    # SCIENTIFIC NOTE
    # ========================================================

    print(
        "[INFO] Expert visual rating dataset "
        "not provided."
    )

    print(
        "[INFO] Evaluating severity agreement "
        "using verified ground-truth lesion masks "
        "from PlantSeg test split"
    )

    print(
        f"       {MASK_DIR}"
    )

    print(
        "Scientific Note: This evaluates quantitative "
        "agreement between predicted and ground-truth "
        "affected-area estimates. It does not establish "
        "expert-validated agronomic severity standards."
    )

    # ========================================================
    # FIND DATASET PAIRS
    # ========================================================

    try:

        pairs = find_test_pairs()

    except Exception as error:

        print(
            f"[ERROR] Dataset discovery failed: "
            f"{error}"
        )

        print(
            "Status: NOT IMPLEMENTED"
        )

        sys.exit(0)

    print(
        f"[INFO] Total verified test pairs: "
        f"{len(pairs)}"
    )

    # ========================================================
    # SELECT DATA
    # ========================================================

    try:

        eval_pairs = select_pairs(
            pairs,
            args.num_samples
        )

    except Exception as error:

        print(
            f"[ERROR] Sample selection failed: "
            f"{error}"
        )

        sys.exit(1)

    if args.num_samples == 0:

        print(
            f"[INFO] Evaluating on all "
            f"{len(eval_pairs)} test samples"
        )

    else:

        print(
            f"[INFO] Evaluating on "
            f"{len(eval_pairs)} samples "
            f"(random seed: {RANDOM_SEED})"
        )

    if not eval_pairs:

        print(
            "[ERROR] No valid test pairs found."
        )

        print(
            "Status: NOT IMPLEMENTED"
        )

        sys.exit(0)

    # ========================================================
    # INITIALIZE SEGMENTER
    # ========================================================

    print(
        "[INFO] Initializing LeafSegmenter "
        "for severity inference..."
    )

    try:

        segmenter = LeafSegmenter()

    except Exception as error:

        print(
            f"[ERROR] Failed to initialize "
            f"LeafSegmenter: {error}"
        )

        print(
            "Status: NOT IMPLEMENTED"
        )

        sys.exit(0)

    # ========================================================
    # METRICS
    # ========================================================

    tier_matches = 0

    total_eval = 0

    skipped_samples = 0

    area_differences = []

    gt_area_values = []

    predicted_area_values = []

    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    confusion = {

        "Healthy": {
            "Healthy": 0,
            "Early": 0,
            "Moderate": 0,
            "Severe": 0,
        },

        "Early": {
            "Healthy": 0,
            "Early": 0,
            "Moderate": 0,
            "Severe": 0,
        },

        "Moderate": {
            "Healthy": 0,
            "Early": 0,
            "Moderate": 0,
            "Severe": 0,
        },

        "Severe": {
            "Healthy": 0,
            "Early": 0,
            "Moderate": 0,
            "Severe": 0,
        },
    }

    # ========================================================
    # EVALUATION
    # ========================================================

    print("-" * 65)
    print("Evaluating samples...")
    print("-" * 65)

    for img_path, mask_path in eval_pairs:

        try:

            # ==================================================
            # GROUND TRUTH
            # ==================================================

            (
                gt_area_pct,
                gt_tier,
                gt_diseased_pixels,
                gt_total_pixels
            ) = calculate_ground_truth_area(
                mask_path,
                image_path=img_path,
                segmenter=segmenter
            )

            # ==================================================
            # LOAD IMAGE
            # ==================================================

            image = Image.open(
                img_path
            ).convert("RGB")

            # ==================================================
            # U-NET SEGMENTATION
            # ==================================================

            result = (
                segmenter.segment_image(
                    image
                )
            )

            # ==================================================
            # CHECK RESULT
            # ==================================================

            if not result:

                print(
                    f"[WARN] Empty segmentation "
                    f"result: {img_path.name}"
                )

                skipped_samples += 1

                continue

            if not result.get(
                "available",
                False
            ):

                print(
                    f"[WARN] Segmentation unavailable: "
                    f"{img_path.name}"
                )

                skipped_samples += 1

                continue

            # ==================================================
            # GET PREDICTED AREA
            # ==================================================

            predicted_area = (
                get_predicted_area(
                    result
                )
            )

            if predicted_area is None:

                print(
                    f"[WARN] Missing or invalid "
                    f"affected_percentage: "
                    f"{img_path.name}"
                )

                print(
                    f"       Available keys: "
                    f"{list(result.keys())}"
                )

                skipped_samples += 1

                continue

            # ==================================================
            # PREDICTED TIER
            # ==================================================

            predicted_tier = (
                classify_severity(
                    predicted_area
                )
            )

            # ==================================================
            # RECORD METRICS
            # ==================================================

            total_eval += 1

            difference = abs(
                predicted_area -
                gt_area_pct
            )

            area_differences.append(
                difference
            )

            gt_area_values.append(
                gt_area_pct
            )

            predicted_area_values.append(
                predicted_area
            )

            # ==================================================
            # TIER MATCH
            # ==================================================

            if predicted_tier == gt_tier:

                tier_matches += 1

            # ==================================================
            # CONFUSION MATRIX
            # ==================================================

            confusion[
                gt_tier
            ][
                predicted_tier
            ] += 1

        except Exception as error:

            print(
                f"[WARN] Error evaluating "
                f"{img_path.name}: {error}"
            )

            skipped_samples += 1

    # ========================================================
    # NO RESULTS
    # ========================================================

    if total_eval == 0:

        print()

        print(
            "Status: NOT IMPLEMENTED"
        )

        print(
            "Reason: No test samples were "
            "successfully evaluated."
        )

        sys.exit(0)

    # ========================================================
    # CALCULATE FINAL METRICS
    # ========================================================

    tier_accuracy = (
        tier_matches /
        total_eval
    ) * 100.0

    mean_absolute_error = float(
        np.mean(
            area_differences
        )
    )

    mean_gt_area = float(
        np.mean(
            gt_area_values
        )
    )

    mean_predicted_area = float(
        np.mean(
            predicted_area_values
        )
    )

    # ========================================================
    # RESULTS
    # ========================================================

    print()

    print("=" * 65)

    print(
        "SEVERITY THRESHOLD VALIDATION RESULTS"
    )

    print("=" * 65)

    print(
        f"Evaluated Test Pairs:       "
        f"{total_eval}"
    )

    print(
        f"Skipped Samples:            "
        f"{skipped_samples}"
    )

    print(
        f"Severity Tier Accuracy:     "
        f"{tier_accuracy:.2f}%"
    )

    print(
        f"Mean Absolute Error (MAE):  "
        f"{mean_absolute_error:.2f}% "
        f"affected leaf area"
    )

    print(
        f"Mean GT Affected Area:      "
        f"{mean_gt_area:.2f}%"
    )

    print(
        f"Mean Predicted Area:        "
        f"{mean_predicted_area:.2f}%"
    )

    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    print()

    print(
        "Confusion Matrix "
        "(Ground Truth Rows -> Predicted Columns):"
    )

    print(
        f"{'GT / Pred':<12}"
        f"{'Healthy':<10}"
        f"{'Early':<10}"
        f"{'Moderate':<11}"
        f"{'Severe':<10}"
    )

    for gt_tier in [
        "Healthy",
        "Early",
        "Moderate",
        "Severe",
    ]:

        row = confusion[
            gt_tier
        ]

        print(
            f"{gt_tier:<12}"
            f"{row['Healthy']:<10}"
            f"{row['Early']:<10}"
            f"{row['Moderate']:<11}"
            f"{row['Severe']:<10}"
        )

    # ========================================================
    # THRESHOLDS
    # ========================================================

    print()

    print(
        "Project-Defined Severity Thresholds:"
    )

    print(
        "Healthy  : <= 0%"
    )

    print(
        "Early    : >0% to <15%"
    )

    print(
        "Moderate : >=15% to <35%"
    )

    print(
        "Severe   : >=35%"
    )

    # ========================================================
    # SCIENTIFIC LIMITATION
    # ========================================================

    print()

    print(
        "Scientific Limitation:"
    )

    print(
        "These thresholds are project-defined "
        "initial thresholds and have not been "
        "validated against expert agronomic "
        "severity ratings."
    )

    print(
        "PlantSeg mask agreement should not be "
        "reported as expert-validated agronomic "
        "severity performance."
    )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    print("=" * 65)

    print(
        "Status: EVALUATED"
    )

    print("=" * 65)

    sys.exit(0)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()