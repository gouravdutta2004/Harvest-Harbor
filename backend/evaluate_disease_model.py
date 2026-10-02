#!/usr/bin/env python3
"""
Harvest Harbor — PlantWild v2 Disease Model Evaluation

Disease classifier:
    PlantWild v2 EfficientNet-B0

Model:
    115 disease classes

Evaluation modes:

1. Full 115-class evaluation
   Use:
       python evaluate_disease_model.py \
           --dataset /path/to/plantwild_test \
           --num-samples 0

   The supplied dataset MUST contain all 115 model classes.

2. Local PlantVillage benchmark
   If no external dataset is supplied, the script evaluates only
   the valid disease classes available in the local PlantVillage
   dataset.

Scientific integrity:
- No fabricated metrics.
- No synthetic samples.
- No invalid class mappings.
- Missing classes are reported.
- --num-samples 0 means ALL available samples.
- Full 115-class evaluation requires all 115 classes.
- "COMPLETED" means the evaluation ran successfully.
  It does NOT mean the model passed a scientific threshold.
"""

import os
import sys
import json
import argparse
import random
from pathlib import Path
from collections import defaultdict

import numpy as np


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault(
    "KERAS_HOME",
    str(BASE_DIR / ".keras")
)


# ============================================================
# MODEL IMPORT
# ============================================================

from predictor import (
    PlantPredictor,
    MODEL_PATH,
    CLASS_NAMES_PATH,
)


# ============================================================
# DATASET PATHS
# ============================================================

DEFAULT_PLANTWILD_DIR = (
    BASE_DIR.parent /
    "datasets" /
    "plantwild"
)

PLANTVILLAGE_ROOT = (
    BASE_DIR.parent /
    "datasets" /
    "plantvillage" /
    "raw" /
    "color"
)


# ============================================================
# VALID IMAGE EXTENSIONS
# ============================================================

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".JPG",
    ".JPEG",
    ".PNG",
    ".BMP",
    ".WEBP",
}


# ============================================================
# VALID PLANTVILLAGE -> MODEL MAPPINGS
# ============================================================
#
# IMPORTANT:
# Only mappings that actually exist in the 115-class model
# are included here.
#
# Removed invalid mappings:
#   Grape___Esca_(Black_Measles) -> grape esca
#   Peach___Bacterial_spot -> peach bacterial spot
#
# Those labels do NOT exist in the supplied 115-class metadata.
# ============================================================

PV_TO_PLANTWILD = {
    "Apple___Apple_scab":
        "apple scab",

    "Apple___Black_rot":
        "apple black rot",

    "Apple___Cedar_apple_rust":
        "apple rust",

    "Cherry_(including_sour)___Powdery_mildew":
        "cherry powdery mildew",

    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot":
        "corn gray leaf spot",

    "Corn_(maize)___Common_rust_":
        "corn rust",

    "Corn_(maize)___Northern_Leaf_Blight":
        "corn northern leaf blight",

    "Grape___Black_rot":
        "grape black rot",

    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)":
        "grape leaf spot",

    "Potato___Early_blight":
        "potato early blight",

    "Potato___Late_blight":
        "potato late blight",

    "Pepper,_bell___Bacterial_spot":
        "bell pepper bacterial spot",

    "Strawberry___Leaf_scorch":
        "strawberry leaf scorch",

    "Tomato___Bacterial_spot":
        "tomato bacterial leaf spot",

    "Tomato___Early_blight":
        "tomato early blight",

    "Tomato___Late_blight":
        "tomato late blight",

    "Tomato___Leaf_Mold":
        "tomato leaf mold",

    "Tomato___Tomato_mosaic_virus":
        "tomato mosaic virus",
}


# ============================================================
# LABEL NORMALIZATION
# ============================================================

def normalize_label(value):
    """
    Normalize class labels for safe comparison.

    Example:

        "Tomato___Early_blight"
        ->
        "tomato early blight"
    """

    value = str(value).strip().lower()

    replacements = {
        "_": " ",
        "-": " ",
        "/": " ",
        "\\": " ",
        "(": " ",
        ")": " ",
        ",": " ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return " ".join(value.split())


# ============================================================
# LOAD MODEL CLASS NAMES
# ============================================================

def load_class_names():
    """
    Load and validate the authoritative model class metadata.
    """

    if not CLASS_NAMES_PATH.exists():
        raise FileNotFoundError(
            f"Class names file not found:\n"
            f"{CLASS_NAMES_PATH}"
        )

    with open(
        CLASS_NAMES_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Class names JSON must contain a list."
        )

    class_names = [
        str(item).strip()
        for item in data
        if str(item).strip()
    ]

    if len(class_names) != 115:
        raise ValueError(
            "Invalid model class metadata.\n"
            f"Expected: 115 classes\n"
            f"Found:    {len(class_names)}"
        )

    if len(set(class_names)) != len(class_names):
        raise ValueError(
            "Duplicate disease class names detected."
        )

    return class_names


# ============================================================
# BUILD NORMALIZED MODEL MAP
# ============================================================

def build_model_class_map(class_names):
    """
    Create:

        normalized label -> official model label
    """

    mapping = {}

    for class_name in class_names:

        normalized = normalize_label(
            class_name
        )

        if normalized in mapping:

            raise ValueError(
                "Class-name normalization collision:\n"
                f"Existing: {mapping[normalized]}\n"
                f"New:      {class_name}\n"
                f"Normalized: {normalized}"
            )

        mapping[normalized] = class_name

    return mapping


# ============================================================
# RESOLVE DATASET CLASS
# ============================================================

def resolve_dataset_class(
    folder_name,
    model_class_map
):
    """
    Resolve a dataset folder name to an official
    model disease class.
    """

    normalized = normalize_label(
        folder_name
    )

    return model_class_map.get(
        normalized
    )


# ============================================================
# COLLECT FOLDER DATASET
# ============================================================

def collect_folder_dataset(
    dataset_root,
    class_names,
    require_all_classes=False
):
    """
    Expected dataset structure:

        dataset/
        ├── apple black rot/
        │   ├── image1.jpg
        │   └── image2.jpg
        ├── apple mosaic virus/
        ├── ...
        └── zucchini yellow mosaic virus/

    Dataset folder names may use common separators such
    as _, -, commas and parentheses.

    Returns:

        samples
        matched_classes
        unmatched_folders
        missing_classes
    """

    dataset_root = Path(
        dataset_root
    ).expanduser().resolve()

    if not dataset_root.exists():
        raise FileNotFoundError(
            f"Dataset directory does not exist:\n"
            f"{dataset_root}"
        )

    if not dataset_root.is_dir():
        raise NotADirectoryError(
            f"Dataset path is not a directory:\n"
            f"{dataset_root}"
        )

    model_class_map = (
        build_model_class_map(
            class_names
        )
    )

    samples = []

    matched_classes = set()

    unmatched_folders = []

    folders = sorted(
        [
            item
            for item in dataset_root.iterdir()
            if item.is_dir()
        ],
        key=lambda x: x.name.lower()
    )

    for folder in folders:

        official_class = resolve_dataset_class(
            folder.name,
            model_class_map
        )

        if official_class is None:

            unmatched_folders.append(
                folder.name
            )

            continue

        matched_classes.add(
            official_class
        )

        for image_path in folder.rglob("*"):

            if not image_path.is_file():
                continue

            if image_path.suffix not in VALID_EXTENSIONS:
                continue

            samples.append(
                (
                    image_path,
                    official_class
                )
            )

    missing_classes = [
        class_name
        for class_name in class_names
        if class_name not in matched_classes
    ]

    if require_all_classes:

        if missing_classes:

            print()
            print("=" * 70)
            print(
                "ERROR — FULL 115-CLASS DATASET INCOMPLETE"
            )
            print("=" * 70)

            print(
                f"Matched classes: "
                f"{len(matched_classes)} / 115"
            )

            print(
                f"Missing classes: "
                f"{len(missing_classes)}"
            )

            print()
            print("Missing model classes:")

            for class_name in missing_classes:
                print(
                    f"  - {class_name}"
                )

            if unmatched_folders:

                print()
                print(
                    "Unmatched dataset folders:"
                )

                for folder_name in unmatched_folders:
                    print(
                        f"  - {folder_name}"
                    )

            print()
            print(
                "Full 115-class evaluation has NOT been run."
            )

            print("=" * 70)

            raise RuntimeError(
                "The supplied dataset does not contain "
                "all 115 model classes."
            )

    return (
        samples,
        matched_classes,
        unmatched_folders,
        missing_classes,
    )


# ============================================================
# BALANCED SAMPLE SELECTION
# ============================================================

def select_balanced_samples(
    samples,
    num_samples=0,
    seed=42
):
    """
    Select samples approximately equally across classes.

    IMPORTANT:

        num_samples <= 0
        means ALL available samples.

    If num_samples is greater than or equal to the number
    of available samples, all samples are returned.

    The function never duplicates an image.
    """

    if not samples:
        return []

    if (
        num_samples is None
        or num_samples <= 0
        or num_samples >= len(samples)
    ):
        return list(samples)

    grouped = defaultdict(list)

    for image_path, class_name in samples:

        grouped[class_name].append(
            (
                image_path,
                class_name
            )
        )

    rng = random.Random(seed)

    classes = sorted(
        grouped.keys()
    )

    # First distribute the requested samples
    # approximately equally.
    base_per_class = (
        num_samples // len(classes)
    )

    remainder = (
        num_samples % len(classes)
    )

    selected = []

    for index, class_name in enumerate(classes):

        class_items = grouped[
            class_name
        ].copy()

        rng.shuffle(
            class_items
        )

        take = base_per_class

        if index < remainder:
            take += 1

        take = min(
            take,
            len(class_items)
        )

        selected.extend(
            class_items[:take]
        )

    # In unusual cases where some classes contain too few
    # samples, fill remaining capacity from unused samples.
    if len(selected) < num_samples:

        selected_ids = {
            str(path.resolve())
            for path, _ in selected
        }

        remaining = []

        for item in samples:

            path = item[0]

            if str(path.resolve()) not in selected_ids:
                remaining.append(item)

        rng.shuffle(
            remaining
        )

        needed = (
            num_samples -
            len(selected)
        )

        selected.extend(
            remaining[:needed]
        )

    rng.shuffle(
        selected
    )

    return selected[:num_samples]


# ============================================================
# MODEL PREDICTION
# ============================================================

def predict_one(
    predictor,
    image_path
):
    """
    Predict one image.

    Returns:

        prediction
        top3
    """

    result = predictor.predict_image(
        image_path
    )

    prediction = (
        result.get("prediction")
        or ""
    ).strip().lower()

    top3 = []

    for item in result.get(
        "top_3",
        []
    ):

        if not isinstance(
            item,
            dict
        ):
            continue

        class_name = (
            item.get("class")
            or ""
        ).strip().lower()

        if class_name:
            top3.append(
                class_name
            )

    return (
        prediction,
        top3
    )


# ============================================================
# METRIC CALCULATION
# ============================================================

def calculate_metrics(
    y_true,
    y_pred,
    evaluated_classes
):
    """
    Calculate macro precision, recall and F1.

    Only classes actually represented in y_true are included.
    """

    labels = [
        class_name.lower().strip()
        for class_name in evaluated_classes
    ]

    precision_values = []
    recall_values = []
    f1_values = []

    per_class = {}

    for class_name in labels:

        true_positive = 0
        false_positive = 0
        false_negative = 0

        for actual, predicted in zip(
            y_true,
            y_pred
        ):

            if (
                actual == class_name
                and predicted == class_name
            ):
                true_positive += 1

            elif (
                actual != class_name
                and predicted == class_name
            ):
                false_positive += 1

            elif (
                actual == class_name
                and predicted != class_name
            ):
                false_negative += 1

        precision_denominator = (
            true_positive +
            false_positive
        )

        recall_denominator = (
            true_positive +
            false_negative
        )

        precision = (
            true_positive /
            precision_denominator
            if precision_denominator
            else 0.0
        )

        recall = (
            true_positive /
            recall_denominator
            if recall_denominator
            else 0.0
        )

        if (
            precision + recall
        ) > 0:

            f1 = (
                2 *
                precision *
                recall /
                (
                    precision +
                    recall
                )
            )

        else:
            f1 = 0.0

        support = sum(
            1
            for actual in y_true
            if actual == class_name
        )

        precision_values.append(
            precision
        )

        recall_values.append(
            recall
        )

        f1_values.append(
            f1
        )

        per_class[class_name] = {
            "precision": precision * 100.0,
            "recall": recall * 100.0,
            "f1": f1 * 100.0,
            "support": support,
        }

    macro_precision = (
        np.mean(
            precision_values
        ) * 100.0
        if precision_values
        else 0.0
    )

    macro_recall = (
        np.mean(
            recall_values
        ) * 100.0
        if recall_values
        else 0.0
    )

    macro_f1 = (
        np.mean(
            f1_values
        ) * 100.0
        if f1_values
        else 0.0
    )

    return (
        macro_precision,
        macro_recall,
        macro_f1,
        per_class,
    )


# ============================================================
# PRINT PER-CLASS METRICS
# ============================================================

def print_per_class_metrics(
    per_class
):
    """
    Print per-class precision, recall and F1.
    """

    print()
    print("-" * 90)
    print(
        "PER-CLASS METRICS"
    )
    print("-" * 90)

    print(
        f"{'Class':45s}"
        f"{'Precision':>12s}"
        f"{'Recall':>12s}"
        f"{'F1':>12s}"
        f"{'Samples':>9s}"
    )

    print("-" * 90)

    for class_name in sorted(
        per_class.keys()
    ):

        metrics = per_class[
            class_name
        ]

        print(
            f"{class_name[:45]:45s}"
            f"{metrics['precision']:11.2f}%"
            f"{metrics['recall']:11.2f}%"
            f"{metrics['f1']:11.2f}%"
            f"{metrics['support']:9d}"
        )

    print("-" * 90)


# ============================================================
# FULL 115-CLASS EVALUATION
# ============================================================

def evaluate_external_plantwild(
    dataset_path,
    num_samples
):
    """
    Perform true 115-class evaluation.

    This function refuses to run if any model class is missing.
    """

    print()
    print("=" * 70)
    print(
        "FULL PLANTWILD V2 — 115 CLASS EVALUATION"
    )
    print("=" * 70)

    class_names = load_class_names()

    print(
        f"Model classes:     {len(class_names)}"
    )

    print(
        f"Dataset:           {dataset_path}"
    )

    (
        samples,
        matched_classes,
        unmatched_folders,
        missing_classes,
    ) = collect_folder_dataset(
        dataset_path,
        class_names,
        require_all_classes=True
    )

    print(
        f"Matched classes:   "
        f"{len(matched_classes)} / 115"
    )

    print(
        f"Available images:  "
        f"{len(samples)}"
    )

    selected = select_balanced_samples(
        samples,
        num_samples=num_samples,
        seed=42
    )

    print(
        f"Selected images:   "
        f"{len(selected)}"
    )

    if not selected:

        print()
        print(
            "Status: NOT VALIDATED"
        )

        print(
            "Reason: No valid images were found."
        )

        return

    print()
    print(
        "[INFO] Loading PlantWild disease predictor..."
    )

    predictor = PlantPredictor()

    y_true = []
    y_pred = []

    top1_correct = 0
    top3_correct = 0

    failed_samples = 0

    for index, (
        image_path,
        ground_truth
    ) in enumerate(
        selected,
        start=1
    ):

        try:

            prediction, top3 = predict_one(
                predictor,
                image_path
            )

            ground_truth_normalized = (
                ground_truth.lower().strip()
            )

            y_true.append(
                ground_truth_normalized
            )

            y_pred.append(
                prediction
            )

            if prediction == ground_truth_normalized:
                top1_correct += 1

            if (
                ground_truth_normalized
                in top3
            ):
                top3_correct += 1

        except Exception as exc:

            failed_samples += 1

            print(
                f"[WARN] "
                f"{image_path.name}: "
                f"{exc}"
            )

        if (
            index % 100 == 0
            or index == len(selected)
        ):

            print(
                f"[INFO] Processed "
                f"{index}/{len(selected)}"
            )

    evaluated_samples = len(
        y_true
    )

    if evaluated_samples == 0:

        print()
        print(
            "Status: NOT VALIDATED"
        )

        print(
            "Reason: No images were successfully evaluated."
        )

        return

    top1_accuracy = (
        top1_correct /
        evaluated_samples *
        100.0
    )

    top3_accuracy = (
        top3_correct /
        evaluated_samples *
        100.0
    )

    evaluated_classes = sorted(
        set(y_true)
    )

    (
        macro_precision,
        macro_recall,
        macro_f1,
        per_class,
    ) = calculate_metrics(
        y_true,
        y_pred,
        evaluated_classes
    )

    print()
    print("=" * 70)
    print(
        "PLANTWILD V2 — 115 CLASS RESULTS"
    )
    print("=" * 70)

    print(
        f"Model Classes:          {len(class_names)}"
    )

    print(
        f"Represented Classes:    "
        f"{len(evaluated_classes)} / 115"
    )

    print(
        f"Evaluation Samples:     "
        f"{evaluated_samples}"
    )

    print(
        f"Failed Samples:         "
        f"{failed_samples}"
    )

    print(
        f"Top-1 Accuracy:         "
        f"{top1_accuracy:.2f}%"
    )

    print(
        f"Top-3 Accuracy:         "
        f"{top3_accuracy:.2f}%"
    )

    print(
        f"Macro Precision:        "
        f"{macro_precision:.2f}%"
    )

    print(
        f"Macro Recall:           "
        f"{macro_recall:.2f}%"
    )

    print(
        f"Macro F1-Score:         "
        f"{macro_f1:.2f}%"
    )

    print("=" * 70)

    print_per_class_metrics(
        per_class
    )

    print()
    print(
        "Scientific interpretation:"
    )

    print(
        "1. These metrics describe performance on the "
        "supplied 115-class test dataset."
    )

    print(
        "2. They should not automatically be interpreted "
        "as field performance."
    )

    print(
        "3. No automatic scientific PASS/FAIL threshold "
        "is assigned."
    )

    print()
    print(
        "Status: COMPLETED"
    )

    print("=" * 70)


# ============================================================
# LOCAL PLANTVILLAGE BENCHMARK
# ============================================================

def evaluate_local_plantvillage(
    num_samples
):
    """
    Evaluate the valid PlantVillage disease mappings.

    Current valid mapping count:
        18 classes

    This is NOT a 115-class evaluation.
    """

    print()
    print("=" * 70)
    print(
        "LOCAL PLANTVILLAGE — "
        "VALID 18 CLASS DISEASE BENCHMARK"
    )
    print("=" * 70)

    class_names = load_class_names()

    model_class_map = (
        build_model_class_map(
            class_names
        )
    )

    samples = []

    skipped_mappings = []

    missing_folders = []

    for (
        folder_name,
        target_disease
    ) in PV_TO_PLANTWILD.items():

        target_normalized = (
            normalize_label(
                target_disease
            )
        )

        if (
            target_normalized
            not in model_class_map
        ):

            skipped_mappings.append(
                (
                    folder_name,
                    target_disease
                )
            )

            continue

        folder_path = (
            PLANTVILLAGE_ROOT /
            folder_name
        )

        if not folder_path.exists():

            missing_folders.append(
                folder_name
            )

            continue

        official_target = (
            model_class_map[
                target_normalized
            ]
        )

        image_paths = [
            path
            for path in folder_path.rglob("*")
            if (
                path.is_file()
                and path.suffix
                in VALID_EXTENSIONS
            )
        ]

        for image_path in image_paths:

            samples.append(
                (
                    image_path,
                    official_target
                )
            )

    valid_classes = sorted(
        set(
            target
            for _, target in samples
        )
    )

    print(
        f"Valid benchmark classes: "
        f"{len(valid_classes)} / 18"
    )

    print(
        f"Available samples: "
        f"{len(samples)}"
    )

    if skipped_mappings:

        print()
        print(
            "[INFO] Invalid mappings skipped:"
        )

        for folder_name, disease in (
            skipped_mappings
        ):

            print(
                f"  {folder_name}"
                f" -> {disease}"
            )

    if missing_folders:

        print()
        print(
            "[INFO] Missing PlantVillage folders:"
        )

        for folder_name in missing_folders:

            print(
                f"  - {folder_name}"
            )

    if not samples:

        print()
        print(
            "Status: NOT VALIDATED"
        )

        print(
            "Reason: No valid PlantVillage samples found."
        )

        return

    selected = select_balanced_samples(
        samples,
        num_samples=num_samples,
        seed=42
    )

    print(
        f"Selected samples: "
        f"{len(selected)}"
    )

    predictor = PlantPredictor()

    y_true = []
    y_pred = []

    top1_correct = 0
    top3_correct = 0

    failed_samples = 0

    for index, (
        image_path,
        ground_truth
    ) in enumerate(
        selected,
        start=1
    ):

        try:

            prediction, top3 = predict_one(
                predictor,
                image_path
            )

            gt = (
                ground_truth.lower().strip()
            )

            y_true.append(gt)
            y_pred.append(prediction)

            if prediction == gt:
                top1_correct += 1

            if gt in top3:
                top3_correct += 1

        except Exception as exc:

            failed_samples += 1

            print(
                f"[WARN] "
                f"{image_path.name}: "
                f"{exc}"
            )

        if (
            index % 100 == 0
            or index == len(selected)
        ):

            print(
                f"[INFO] Processed "
                f"{index}/{len(selected)}"
            )

    evaluated_samples = len(
        y_true
    )

    if evaluated_samples == 0:

        print()
        print(
            "Status: NOT VALIDATED"
        )

        return

    top1_accuracy = (
        top1_correct /
        evaluated_samples *
        100.0
    )

    top3_accuracy = (
        top3_correct /
        evaluated_samples *
        100.0
    )

    evaluated_classes = sorted(
        set(y_true)
    )

    (
        macro_precision,
        macro_recall,
        macro_f1,
        per_class,
    ) = calculate_metrics(
        y_true,
        y_pred,
        evaluated_classes
    )

    print()
    print("=" * 70)
    print(
        "LOCAL PLANTVILLAGE RESULTS"
    )
    print("=" * 70)

    print(
        f"Evaluation Samples:     "
        f"{evaluated_samples}"
    )

    print(
        f"Failed Samples:         "
        f"{failed_samples}"
    )

    print(
        f"Evaluated Classes:      "
        f"{len(evaluated_classes)} / 18"
    )

    print(
        f"Top-1 Accuracy:         "
        f"{top1_accuracy:.2f}%"
    )

    print(
        f"Top-3 Accuracy:         "
        f"{top3_accuracy:.2f}%"
    )

    print(
        f"Macro Precision:        "
        f"{macro_precision:.2f}%"
    )

    print(
        f"Macro Recall:           "
        f"{macro_recall:.2f}%"
    )

    print(
        f"Macro F1-Score:         "
        f"{macro_f1:.2f}%"
    )

    print("=" * 70)

    print_per_class_metrics(
        per_class
    )

    print()
    print(
        "Scientific Note:"
    )

    print(
        "This benchmark evaluates only the valid "
        "PlantVillage-to-model class mappings."
    )

    print(
        "It must NOT be presented as validation of "
        "the complete 115-class disease classifier."
    )

    print()
    print(
        "Status: COMPLETED"
    )

    print("=" * 70)


# ============================================================
# MAIN DISPATCHER
# ============================================================

def evaluate_disease_model(
    num_samples=0,
    dataset_path=None
):

    print("=" * 70)
    print(
        "HARVEST HARBOR — "
        "PLANTWILD V2 DISEASE CLASSIFIER EVALUATION"
    )
    print("=" * 70)

    print(
        f"Model: "
        f"{MODEL_PATH}"
    )

    print(
        f"Class metadata: "
        f"{CLASS_NAMES_PATH}"
    )

    # --------------------------------------------------------
    # Validate model class metadata
    # --------------------------------------------------------

    try:

        class_names = load_class_names()

    except Exception as exc:

        print()
        print(
            "Status: NOT VALIDATED"
        )

        print(
            f"Reason: {exc}"
        )

        return

    print(
        f"Verified model classes: "
        f"{len(class_names)}"
    )

    # --------------------------------------------------------
    # Validate model file
    # --------------------------------------------------------

    if not MODEL_PATH.exists():

        print()
        print(
            "Status: NOT VALIDATED"
        )

        print(
            "Reason: Disease model weights "
            "were not found."
        )

        print(
            f"Expected path: "
            f"{MODEL_PATH}"
        )

        return

    # --------------------------------------------------------
    # Explicit --dataset has highest priority
    # --------------------------------------------------------

    if dataset_path:

        dataset_path = Path(
            dataset_path
        ).expanduser().resolve()

        print()
        print(
            f"[INFO] Requested dataset:"
            f" {dataset_path}"
        )

        if not dataset_path.exists():

            print()
            print(
                "Status: NOT VALIDATED"
            )

            print(
                "Reason: Dataset path does not exist."
            )

            print(
                f"Path: {dataset_path}"
            )

            return

        if not dataset_path.is_dir():

            print()
            print(
                "Status: NOT VALIDATED"
            )

            print(
                "Reason: Dataset path is not a directory."
            )

            return

        try:

            evaluate_external_plantwild(
                dataset_path,
                num_samples
            )

        except RuntimeError:

            # The detailed error was already printed.
            return

        except Exception as exc:

            print()
            print(
                "Status: NOT VALIDATED"
            )

            print(
                f"Reason: {exc}"
            )

        return

    # --------------------------------------------------------
    # Environment variable
    # --------------------------------------------------------

    environment_dataset = os.getenv(
        "PLANTWILD_DATASET_DIR"
    )

    if environment_dataset:

        environment_dataset = Path(
            environment_dataset
        ).expanduser().resolve()

        print()
        print(
            "[INFO] PLANTWILD_DATASET_DIR detected:"
        )

        print(
            f"       {environment_dataset}"
        )

        if environment_dataset.exists():

            try:

                evaluate_external_plantwild(
                    environment_dataset,
                    num_samples
                )

            except RuntimeError:

                return

            except Exception as exc:

                print()
                print(
                    "Status: NOT VALIDATED"
                )

                print(
                    f"Reason: {exc}"
                )

            return

        print(
            "[WARN] "
            "PLANTWILD_DATASET_DIR does not exist."
        )

    # --------------------------------------------------------
    # Default local PlantWild directory
    # --------------------------------------------------------

    if (
        DEFAULT_PLANTWILD_DIR.exists()
        and DEFAULT_PLANTWILD_DIR.is_dir()
    ):

        print()
        print(
            "[INFO] Local PlantWild dataset detected."
        )

        try:

            evaluate_external_plantwild(
                DEFAULT_PLANTWILD_DIR,
                num_samples
            )

        except RuntimeError:

            return

        except Exception as exc:

            print()
            print(
                "Status: NOT VALIDATED"
            )

            print(
                f"Reason: {exc}"
            )

        return

    # --------------------------------------------------------
    # Local PlantVillage fallback
    # --------------------------------------------------------

    if (
        PLANTVILLAGE_ROOT.exists()
        and PLANTVILLAGE_ROOT.is_dir()
    ):

        print()
        print(
            "[INFO] No 115-class PlantWild dataset "
            "was supplied."
        )

        print(
            "[INFO] Running valid local "
            "PlantVillage benchmark."
        )

        evaluate_local_plantvillage(
            num_samples
        )

        print()
        print(
            "[INFO] Full 115-class validation "
            "has NOT been performed."
        )

        return

    # --------------------------------------------------------
    # No dataset
    # --------------------------------------------------------

    print()
    print(
        "Status: NOT VALIDATED"
    )

    print(
        "Reason: No compatible disease "
        "evaluation dataset was found."
    )

    print()
    print(
        "For full 115-class evaluation use:"
    )

    print(
        "python evaluate_disease_model.py "
        "--dataset /actual/path/to/plantwild_test "
        "--num-samples 0"
    )


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the Harvest Harbor "
            "115-class PlantWild disease model."
        )
    )

    parser.add_argument(
        "--num-samples",
        type=int,
        default=0,
        help=(
            "Maximum number of samples to evaluate. "
            "0 means all available samples."
        )
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help=(
            "Path to a PlantWild-style folder dataset. "
            "For full validation it must contain "
            "all 115 model classes."
        )
    )

    args = parser.parse_args()

    if args.num_samples < 0:

        parser.error(
            "--num-samples cannot be negative."
        )

    evaluate_disease_model(
        num_samples=args.num_samples,
        dataset_path=args.dataset
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()