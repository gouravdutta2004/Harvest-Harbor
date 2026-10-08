from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if "KERAS_HOME" not in os.environ:
    os.environ["KERAS_HOME"] = str(Path(__file__).resolve().parent / "backend" / ".keras")

import numpy as np
import tensorflow as tf

from PIL import Image, ImageOps

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

import matplotlib.pyplot as plt


# ============================================================
# HARVEST HARBOR
# CORRECT 14 × 14 PLANT DISEASE CONFUSION MATRIX
# ============================================================


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(
    "/Users/gourav/Harvest-Harbor"
)

MODEL_H5_PATH = (
    PROJECT_ROOT
    / "backend"
    / "model"
    / "plantwild_v2_efficientnetb0.h5"
)

MODEL_KERAS_PATH = (
    PROJECT_ROOT
    / "backend"
    / "model"
    / "plantwild_v2_efficientnetb0.keras"
)

CLASS_NAMES_PATH = (
    PROJECT_ROOT
    / "backend"
    / "model"
    / "plantwild_v2_class_names.json"
)

MAPPING_PATH = (
    PROJECT_ROOT
    / "datasets"
    / "plantvillage"
    / "data_distribution_for_SVM"
    / "test_mapping.txt"
)

TEST_IMAGE_ROOT = (
    PROJECT_ROOT
    / "datasets"
    / "plantvillage"
    / "data_distribution_for_SVM"
    / "test"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "confusion_matrix_output"
)


# ============================================================
# MODEL SETTINGS
# ============================================================

IMAGE_SIZE = (
    224,
    224,
)

BATCH_SIZE = 32


# ============================================================
# 14 PLANTVILLAGE → PLANTWILD MAPPINGS
# ============================================================

PLANTVILLAGE_TO_PLANTWILD: Dict[str, str] = {

    "apple___apple_scab":
        "apple scab",

    "apple___black_rot":
        "apple black rot",

    "apple___cedar_apple_rust":
        "apple rust",

    "corn_(maize)___cercospora_leaf_spot_gray_leaf_spot":
        "corn gray leaf spot",

    "corn_(maize)___common_rust_":
        "corn rust",

    "corn_(maize)___northern_leaf_blight":
        "corn northern leaf blight",

    "grape___black_rot":
        "grape black rot",

    "potato___early_blight":
        "potato early blight",

    "potato___late_blight":
        "potato late blight",

    "squash___powdery_mildew":
        "squash powdery mildew",

    "strawberry___leaf_scorch":
        "strawberry leaf scorch",

    "tomato___bacterial_spot":
        "tomato bacterial leaf spot",

    "tomato___early_blight":
        "tomato early blight",

    "tomato___late_blight":
        "tomato late blight",
}


# ============================================================
# EXACT ORDER FOR 14 × 14 MATRIX
# ============================================================

SELECTED_CLASSES: List[str] = [

    "apple scab",

    "apple black rot",

    "apple rust",

    "corn gray leaf spot",

    "corn northern leaf blight",

    "corn rust",

    "grape black rot",

    "potato early blight",

    "potato late blight",

    "squash powdery mildew",

    "strawberry leaf scorch",

    "tomato bacterial leaf spot",

    "tomato early blight",

    "tomato late blight",
]


# ============================================================
# NORMALIZE CLASS NAMES
# ============================================================

def normalize_class_name(
    name: str,
) -> str:

    name = str(name)

    name = name.strip()

    name = name.strip(
        "\"'"
    )

    name = name.lower()

    # Normalize path separators
    name = name.replace(
        "\\",
        "/",
    )

    # Spaces → underscores
    name = re.sub(
        r"\s+",
        "_",
        name,
    )

    # Hyphens → underscores
    name = name.replace(
        "-",
        "_",
    )

    return name


# ============================================================
# NORMALIZE PATH
# ============================================================

def normalize_relative_path(
    path: str,
) -> str:

    path = str(path)

    path = path.strip()

    path = path.strip(
        "\"'"
    )

    path = path.replace(
        "\\",
        "/",
    )

    # Remove ./ from beginning
    path = re.sub(
        r"^\./+",
        "",
        path,
    )

    return path


# ============================================================
# FIND IMAGE PATH ROBUSTLY
# ============================================================

def find_test_image(
    relative_path: str,
) -> Optional[Path]:

    relative_path = normalize_relative_path(
        relative_path
    )

    # --------------------------------------------------------
    # First try the exact relative path.
    # --------------------------------------------------------

    candidate = (
        TEST_IMAGE_ROOT
        / Path(relative_path)
    )

    if candidate.exists():
        return candidate

    # --------------------------------------------------------
    # Sometimes mapping paths contain extra directories.
    #
    # Try everything after SVM/test/.
    # --------------------------------------------------------

    marker = "SVM/test/"

    lower_path = relative_path.lower()

    marker_index = lower_path.find(
        marker.lower()
    )

    if marker_index >= 0:

        shortened = relative_path[
            marker_index + len(marker):
        ]

        candidate = (
            TEST_IMAGE_ROOT
            / Path(shortened)
        )

        if candidate.exists():
            return candidate

    # --------------------------------------------------------
    # Try removing leading test/
    # --------------------------------------------------------

    if lower_path.startswith(
        "test/"
    ):

        candidate = (
            TEST_IMAGE_ROOT
            / Path(relative_path[5:])
        )

        if candidate.exists():
            return candidate

    return None


# ============================================================
# PARSE MAPPING LINE
# ============================================================

def parse_mapping_line(
    line: str,
) -> Optional[
    Tuple[str, str]
]:

    line = line.strip()

    if not line:
        return None

    # ========================================================
    # IMPORTANT
    #
    # This is the parser that previously worked with your
    # actual mapping file.
    #
    # Your file contains:
    #
    #     ... SVM/test/...
    #
    # with variable whitespace before SVM/test/.
    # ========================================================

    match = re.search(
        r"\s+SVM/test/",
        line,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    left = (
        line[
            :match.start()
        ]
        .strip()
    )

    right = (
        line[
            match.end():
        ]
        .strip()
    )

    if not left or not right:
        return None

    return (
        left,
        right,
    )


# ============================================================
# EXTRACT PLANTVILLAGE CLASS
# ============================================================

def extract_plantvillage_class(
    left_side: str,
) -> Optional[str]:

    normalized = left_side.replace("\\", "/").strip()
    marker = "raw/color/"

    if marker not in normalized:
        return None

    remainder = normalized.split(marker, 1)[1]

    if "/" not in remainder:
        return None

    return remainder.split("/", 1)[0].strip()


# ============================================================
# LOAD PLANTWILD CLASS NAMES
# ============================================================

def load_plantwild_classes() -> List[str]:

    if not CLASS_NAMES_PATH.exists():

        raise FileNotFoundError(
            "\nPlantWild class names file not found:\n"
            f"{CLASS_NAMES_PATH}"
        )

    with open(
        CLASS_NAMES_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(
            file
        )

    # --------------------------------------------------------
    # Support common JSON formats
    # --------------------------------------------------------

    if isinstance(
        data,
        list,
    ):

        classes = data

    elif isinstance(
        data,
        dict,
    ):

        if "class_names" in data:

            classes = data[
                "class_names"
            ]

        elif "classes" in data:

            classes = data[
                "classes"
            ]

        else:

            raise ValueError(
                "Could not find 'class_names' "
                "or 'classes' in JSON."
            )

    else:

        raise ValueError(
            "Invalid class names JSON format."
        )

    classes = [
        str(x).strip()
        for x in classes
    ]

    print(
        f"PlantWild classes: {len(classes)}"
    )

    if len(classes) != 115:

        raise ValueError(
            "ERROR: Expected exactly "
            f"115 PlantWild classes, "
            f"but found {len(classes)}."
        )

    print(
        "Verified: PlantWild contains 115 classes."
    )

    return classes


# ============================================================
# FIND ACTUAL PLANTWILD CLASS
# ============================================================

def resolve_plantwild_class(
    target_name: str,
    plantwild_classes: List[str],
) -> Optional[str]:

    normalized_target = (
        normalize_class_name(
            target_name
        )
    )

    for class_name in (
        plantwild_classes
    ):

        if (
            normalize_class_name(
                class_name
            )
            == normalized_target
        ):

            return class_name

    return None


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset_entries(
    plantwild_classes: List[str],
):

    print()
    print("=" * 70)
    print(
        "LOADING PLANTVILLAGE TEST MAPPING"
    )
    print("=" * 70)

    if not MAPPING_PATH.exists():

        raise FileNotFoundError(
            "\nMapping file not found:\n"
            f"{MAPPING_PATH}"
        )

    entries = []

    total_mapping_entries = 0

    invalid_lines = 0

    missing_images = 0

    ignored_classes = 0

    # --------------------------------------------------------
    # Class distribution
    # --------------------------------------------------------

    class_counts = {
        class_name: 0
        for class_name in SELECTED_CLASSES
    }

    # --------------------------------------------------------
    # Read mapping
    # --------------------------------------------------------

    with open(
        MAPPING_PATH,
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            parsed = parse_mapping_line(
                line
            )

            if parsed is None:

                invalid_lines += 1

                continue

            left_side, relative_path = parsed

            total_mapping_entries += 1

            # ------------------------------------------------
            # Extract original PlantVillage class
            # ------------------------------------------------

            plantvillage_class = (
                extract_plantvillage_class(
                    left_side
                )
            )

            if plantvillage_class is None:

                ignored_classes += 1

                continue

            normalized_pv = normalize_class_name(
                plantvillage_class
            )

            if normalized_pv not in PLANTVILLAGE_TO_PLANTWILD:

                ignored_classes += 1

                continue

            # ------------------------------------------------
            # Convert to PlantWild class
            # ------------------------------------------------

            target_name = (
                PLANTVILLAGE_TO_PLANTWILD[
                    normalized_pv
                ]
            )

            plantwild_class = (
                resolve_plantwild_class(
                    target_name,
                    plantwild_classes,
                )
            )

            if plantwild_class is None:

                print()
                print(
                    "WARNING:"
                )

                print(
                    "PlantWild class not found:"
                )

                print(
                    target_name
                )

                ignored_classes += 1

                continue

            # ------------------------------------------------
            # Confirm selected class
            # ------------------------------------------------

            if (
                plantwild_class
                not in SELECTED_CLASSES
            ):

                ignored_classes += 1

                continue

            # ------------------------------------------------
            # Find actual image
            # ------------------------------------------------

            image_path = find_test_image(
                relative_path
            )

            if image_path is None:

                missing_images += 1

                continue

            # ------------------------------------------------
            # Store
            # ------------------------------------------------

            entries.append(
                (
                    image_path,
                    plantwild_class,
                )
            )

            class_counts[
                plantwild_class
            ] += 1

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        f"Total mapping entries : "
        f"{total_mapping_entries:,}"
    )

    print(
        f"Invalid mapping lines : "
        f"{invalid_lines:,}"
    )

    print(
        f"Missing images        : "
        f"{missing_images:,}"
    )

    print(
        f"Ignored classes       : "
        f"{ignored_classes:,}"
    )

    print(
        f"14-class samples      : "
        f"{len(entries):,}"
    )

    # ========================================================
    # CLASS DISTRIBUTION
    # ========================================================

    print()
    print(
        "14-CLASS DATASET DISTRIBUTION"
    )

    print(
        "-" * 70
    )

    for number, class_name in enumerate(
        SELECTED_CLASSES,
        start=1,
    ):

        print(
            f"{number:2d}. "
            f"{class_name:<38} "
            f"{class_counts[class_name]:>5}"
        )

    # ========================================================
    # IMPORTANT VALIDATION
    # ========================================================

    missing_classes = [
        class_name
        for class_name in SELECTED_CLASSES
        if class_counts[class_name] == 0
    ]

    if missing_classes:

        print()
        print(
            "WARNING: Selected classes with "
            "zero samples:"
        )

        for class_name in missing_classes:

            print(
                f"  - {class_name}"
            )

    if len(entries) == 0:

        raise RuntimeError(
            "\nNo valid 14-class images were found."
        )

    return entries


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    print()
    print("=" * 70)
    print(
        "LOADING PLANTWILD MODEL"
    )
    print("=" * 70)

    model = None

    # --------------------------------------------------------
    # TensorFlow 2.15 → prefer H5
    # --------------------------------------------------------

    if MODEL_H5_PATH.exists():

        print(
            "Trying H5 model:"
        )

        print(
            MODEL_H5_PATH
        )

        try:

            model = (
                tf.keras.models.load_model(
                    MODEL_H5_PATH,
                    compile=False,
                )
            )

            print(
                "H5 MODEL LOADED SUCCESSFULLY"
            )

        except Exception as error:

            print()
            print(
                "H5 model loading failed."
            )

            print(
                "Error type:",
                type(error).__name__,
            )

            print(
                "Error:",
                str(error),
            )

    # --------------------------------------------------------
    # Fallback to Keras
    # --------------------------------------------------------

    if model is None:

        if not MODEL_KERAS_PATH.exists():

            raise FileNotFoundError(
                "\nNeither model file exists."
            )

        print()
        print(
            "Trying Keras model:"
        )

        print(
            MODEL_KERAS_PATH
        )

        model = (
            tf.keras.models.load_model(
                MODEL_KERAS_PATH,
                compile=False,
            )
        )

        print(
            "KERAS MODEL LOADED SUCCESSFULLY"
        )

    print()
    print(
        "Model input shape :",
        model.input_shape,
    )

    print(
        "Model output shape:",
        model.output_shape,
    )

    if (
        model.output_shape[-1]
        != 115
    ):

        raise ValueError(
            "Expected model output "
            "dimension 115."
        )

    return model


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def load_image(
    image_path: Path,
) -> np.ndarray:

    with Image.open(
        image_path
    ) as image:

        # Correct EXIF orientation
        image = ImageOps.exif_transpose(
            image
        )

        # Ensure RGB
        image = image.convert(
            "RGB"
        )

        # Resize to model input
        image = image.resize(
            IMAGE_SIZE,
            Image.Resampling.LANCZOS,
        )

        image_array = np.asarray(
            image,
            dtype=np.float32,
        )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Keep 0–255 values because this matches the existing
    # Harvest Harbor predictor preprocessing.
    # --------------------------------------------------------

    return image_array


# ============================================================
# SOFTMAX
# ============================================================

def softmax(
    values: np.ndarray,
) -> np.ndarray:

    values = (
        values
        - np.max(
            values,
            axis=1,
            keepdims=True,
        )
    )

    exponentials = np.exp(
        values
    )

    return (
        exponentials
        / np.sum(
            exponentials,
            axis=1,
            keepdims=True,
        )
    )


# ============================================================
# FIND MODEL INDICES FOR 14 CLASSES
# ============================================================

def get_selected_model_indices(
    plantwild_classes: List[str],
) -> List[int]:

    indices = []

    print()
    print(
        "SELECTED PLANTWILD MODEL OUTPUT INDICES"
    )

    print(
        "-" * 70
    )

    for class_name in SELECTED_CLASSES:

        target = normalize_class_name(
            class_name
        )

        found_index = None

        for index, model_class in enumerate(
            plantwild_classes
        ):

            if (
                normalize_class_name(
                    model_class
                )
                == target
            ):

                found_index = index

                break

        if found_index is None:

            raise ValueError(
                "Could not find model output "
                f"for class: {class_name}"
            )

        indices.append(
            found_index
        )

        print(
            f"{found_index:3d} -> "
            f"{class_name}"
        )

    if len(indices) != 14:

        raise ValueError(
            "Expected 14 selected model indices."
        )

    if len(set(indices)) != 14:

        raise ValueError(
            "Duplicate model indices detected."
        )

    return indices


# ============================================================
# PREDICT DATASET
# ============================================================

def predict_dataset(
    model,
    entries,
    plantwild_classes,
):

    print()
    print("=" * 70)
    print(
        "RUNNING 14-CLASS MODEL PREDICTIONS"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Get corresponding output neurons
    # --------------------------------------------------------

    selected_indices = (
        get_selected_model_indices(
            plantwild_classes
        )
    )

    y_true = []

    y_pred = []

    prediction_rows = []

    top3_matches = 0

    top5_matches = 0

    total = len(entries)

    # --------------------------------------------------------
    # Process batches
    # --------------------------------------------------------

    for start in range(
        0,
        total,
        BATCH_SIZE,
    ):

        batch_entries = entries[
            start:
            start + BATCH_SIZE
        ]

        batch_images = []

        valid_entries = []

        # ----------------------------------------------------
        # Load batch images
        # ----------------------------------------------------

        for image_path, true_class in (
            batch_entries
        ):

            try:

                image_array = load_image(
                    image_path
                )

                batch_images.append(
                    image_array
                )

                valid_entries.append(
                    (
                        image_path,
                        true_class,
                    )
                )

            except Exception as error:

                print()
                print(
                    "WARNING: Failed to load:"
                )

                print(
                    image_path
                )

                print(
                    "Reason:",
                    error,
                )

        if not batch_images:

            continue

        batch_array = np.stack(
            batch_images,
            axis=0,
        )

        # ----------------------------------------------------
        # Get original 115 outputs
        # ----------------------------------------------------

        raw_predictions = (
            model(
                batch_array,
                training=False,
            ).numpy()
        )

        if (
            raw_predictions.shape[1]
            != 115
        ):

            raise ValueError(
                "Unexpected model output shape: "
                f"{raw_predictions.shape}"
            )

        # ----------------------------------------------------
        # SELECT ONLY THE 14 REQUIRED OUTPUTS
        # ----------------------------------------------------

        selected_logits = (
            raw_predictions[
                :,
                selected_indices,
            ]
        )

        # ----------------------------------------------------
        # Convert selected 14 outputs into probabilities
        # ----------------------------------------------------

        selected_probabilities = softmax(
            selected_logits
        )

        # ----------------------------------------------------
        # Find highest scoring selected class
        # ----------------------------------------------------

        predicted_indices = np.argmax(
            selected_probabilities,
            axis=1,
        )

        # ----------------------------------------------------
        # Store results
        # ----------------------------------------------------

        for index, (
            image_path,
            true_class,
        ) in enumerate(
            valid_entries
        ):

            predicted_index = int(
                predicted_indices[index]
            )

            predicted_class = (
                SELECTED_CLASSES[
                    predicted_index
                ]
            )

            confidence = float(
                selected_probabilities[
                    index,
                    predicted_index,
                ]
            )

            y_true.append(
                true_class
            )

            y_pred.append(
                predicted_class
            )

            true_idx = SELECTED_CLASSES.index(true_class)
            probs = selected_probabilities[index]
            top3_idx = np.argsort(probs)[-3:]
            top5_idx = np.argsort(probs)[-5:]
            if true_idx in top3_idx:
                top3_matches += 1
            if true_idx in top5_idx:
                top5_matches += 1

            rel_path = (
                str(image_path.relative_to(PROJECT_ROOT).as_posix())
                if image_path.is_relative_to(PROJECT_ROOT)
                else str(image_path)
            )

            prediction_rows.append(
                {
                    "image_path":
                        rel_path,

                    "true_class":
                        true_class,

                    "predicted_class":
                        predicted_class,

                    "confidence":
                        confidence,
                }
            )

        processed = min(
            start + BATCH_SIZE,
            total,
        )

        print(
            f"\rProcessed "
            f"{processed:,}/{total:,} images",
            end="",
            flush=True,
        )

    print()

    top3_acc = float(top3_matches / total) if total > 0 else 0.0
    top5_acc = float(top5_matches / total) if total > 0 else 0.0

    return (
        y_true,
        y_pred,
        prediction_rows,
        top3_acc,
        top5_acc,
    )


# ============================================================
# SAVE CONFUSION MATRIX CSV
# ============================================================

def save_confusion_matrix_csv(
    matrix: np.ndarray,
) -> Path:

    output_file = (
        OUTPUT_DIR
        / "confusion_matrix_14x14.csv"
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerow(
            [
                "True / Predicted"
            ]
            + SELECTED_CLASSES
        )

        for class_name, row in zip(
            SELECTED_CLASSES,
            matrix,
        ):

            writer.writerow(
                [
                    class_name
                ]
                + row.tolist()
            )

    return output_file


# ============================================================
# SAVE PREDICTIONS
# ============================================================

def save_predictions_csv(
    prediction_rows,
) -> Path:

    output_file = (
        OUTPUT_DIR
        / "confusion_matrix_14class_predictions.csv"
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "image_path",
                "true_class",
                "predicted_class",
                "confidence",
            ],
        )

        writer.writeheader()

        writer.writerows(
            prediction_rows
        )

    return output_file


# ============================================================
# PLOT CONFUSION MATRIX
# ============================================================

def plot_confusion_matrix(
    matrix: np.ndarray,
    normalized: bool = False,
) -> Path:

    if normalized:

        row_totals = matrix.sum(
            axis=1,
            keepdims=True,
        )

        display_matrix = np.divide(
            matrix.astype(float),
            row_totals,
            out=np.zeros_like(
                matrix,
                dtype=float,
            ),
            where=row_totals != 0,
        )

        title = (
            "Harvest Harbor - "
            "Normalized 14 × 14 "
            "Confusion Matrix"
        )

        output_file = (
            OUTPUT_DIR
            / "confusion_matrix_14x14_normalized.png"
        )

    else:

        display_matrix = (
            matrix.astype(float)
        )

        title = (
            "Harvest Harbor - "
            "14 × 14 Confusion Matrix"
        )

        output_file = (
            OUTPUT_DIR
            / "confusion_matrix_14x14.png"
        )

    plt.figure(
        figsize=(18, 15)
    )

    plt.imshow(
        display_matrix,
        interpolation="nearest",
        aspect="auto",
    )

    plt.title(
        title,
        fontsize=16,
        pad=20,
    )

    plt.colorbar()

    positions = np.arange(
        len(SELECTED_CLASSES)
    )

    plt.xticks(
        positions,
        SELECTED_CLASSES,
        rotation=70,
        ha="right",
        fontsize=9,
    )

    plt.yticks(
        positions,
        SELECTED_CLASSES,
        fontsize=9,
    )

    plt.xlabel(
        "Predicted Class",
        fontsize=12,
    )

    plt.ylabel(
        "True Class",
        fontsize=12,
    )

    max_value = (
        display_matrix.max()
    )

    threshold = (
        max_value / 2
        if max_value > 0
        else 0
    )

    for i in range(
        display_matrix.shape[0]
    ):

        for j in range(
            display_matrix.shape[1]
        ):

            if normalized:

                cell_text = (
                    f"{display_matrix[i, j] * 100:.1f}%"
                )

            else:

                cell_text = str(
                    matrix[i, j]
                )

            text_color = (
                "white"
                if display_matrix[i, j]
                > threshold
                else "black"
            )

            plt.text(
                j,
                i,
                cell_text,
                ha="center",
                va="center",
                fontsize=7,
                color=text_color,
            )

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    return output_file


# ============================================================
# SAVE CLASSIFICATION REPORT
# ============================================================

def save_classification_report(
    y_true,
    y_pred,
) -> Path:

    report = classification_report(
        y_true,
        y_pred,
        labels=SELECTED_CLASSES,
        target_names=SELECTED_CLASSES,
        digits=4,
        zero_division=0,
    )

    output_file = (
        OUTPUT_DIR
        / "classification_report_14class.txt"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "HARVEST HARBOR\n"
        )

        file.write(
            "14-CLASS CLASSIFICATION REPORT\n"
        )

        file.write(
            "=" * 70
            + "\n\n"
        )

        file.write(
            report
        )

    return output_file


# ============================================================
# SAVE JSON RESULTS
# ============================================================

def save_results_json(
    matrix: np.ndarray,
    evaluated_samples: int,
    accuracy: float,
    balanced_accuracy: float,
    macro_precision: float,
    macro_recall: float,
    macro_f1: float,
    weighted_precision: float,
    weighted_recall: float,
    weighted_f1: float,
    top1_accuracy: Optional[float] = None,
    top3_accuracy: Optional[float] = None,
    top5_accuracy: Optional[float] = None,
) -> Path:

    results = {

        "project":
            "Harvest Harbor",

        "evaluation_type":
            "14-class subset evaluation",

        "base_model":
            "PlantWild EfficientNetB0",

        "base_model_class_count":
            115,

        "evaluation_class_count":
            14,

        "evaluated_samples":
            int(evaluated_samples),

        "accuracy":
            float(accuracy),

        "top1_accuracy":
            float(top1_accuracy if top1_accuracy is not None else accuracy),

        "top3_accuracy":
            float(top3_accuracy) if top3_accuracy is not None else None,

        "top5_accuracy":
            float(top5_accuracy) if top5_accuracy is not None else None,

        "balanced_accuracy":
            float(balanced_accuracy),

        "macro_precision":
            float(macro_precision),

        "macro_recall":
            float(macro_recall),

        "macro_f1":
            float(macro_f1),

        "weighted_precision":
            float(weighted_precision),

        "weighted_recall":
            float(weighted_recall),

        "weighted_f1":
            float(weighted_f1),

        "classes":
            SELECTED_CLASSES,

        "confusion_matrix":
            matrix.tolist(),
    }

    output_file = (
        OUTPUT_DIR
        / "confusion_matrix_14class_results.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
        )

    return output_file


# ============================================================
# PRINT MATRIX TO TERMINAL
# ============================================================

def print_confusion_matrix(
    matrix: np.ndarray,
):

    print()
    print(
        "=" * 70
    )

    print(
        "14 × 14 CONFUSION MATRIX"
    )

    print(
        "=" * 70
    )

    # Short names for terminal display
    short_names = [
        "Apple Scab",
        "Apple Black Rot",
        "Apple Rust",
        "Corn Gray Spot",
        "Corn Northern Blight",
        "Corn Rust",
        "Grape Black Rot",
        "Potato Early Blight",
        "Potato Late Blight",
        "Squash Powdery Mildew",
        "Strawberry Leaf Scorch",
        "Tomato Bacterial Spot",
        "Tomato Early Blight",
        "Tomato Late Blight",
    ]

    print()

    print(
        "Rows = True class"
    )

    print(
        "Columns = Predicted class"
    )

    print()

    # Header
    print(
        " " * 28
        + " ".join(
            f"{i + 1:>5}"
            for i in range(14)
        )
    )

    for i, row in enumerate(
        matrix
    ):

        print(
            f"{i + 1:2d} "
            f"{short_names[i]:<25} "
            + " ".join(
                f"{int(value):>5}"
                for value in row
            )
        )

    print()

    print(
        "Class numbers:"
    )

    for i, name in enumerate(
        short_names,
        start=1,
    ):

        print(
            f"{i:2d} = {name}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "HARVEST HARBOR"
    )

    print(
        "CORRECT 14 × 14 "
        "PLANT DISEASE CONFUSION MATRIX"
    )

    print(
        "=" * 70
    )

    print()
    print(
        "TensorFlow version:",
        tf.__version__,
    )

    # --------------------------------------------------------
    # Load classes
    # --------------------------------------------------------

    plantwild_classes = (
        load_plantwild_classes()
    )

    # --------------------------------------------------------
    # Selected classes
    # --------------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "SELECTED 14 CLASSES"
    )

    print(
        "=" * 70
    )

    for number, class_name in enumerate(
        SELECTED_CLASSES,
        start=1,
    ):

        original_name = None

        for (
            pv_name,
            pw_name,
        ) in PLANTVILLAGE_TO_PLANTWILD.items():

            if pw_name == class_name:

                original_name = pv_name

                break

        print(
            f"{number:2d}. "
            f"{original_name} "
            f"-> {class_name}"
        )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = load_model()

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    entries = (
        load_dataset_entries(
            plantwild_classes
        )
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Do not start prediction if the expected dataset
    # was not found.
    # --------------------------------------------------------

    print()

    print(
        "Dataset validation:"
    )

    print(
        f"Valid selected samples: "
        f"{len(entries):,}"
    )

    if len(entries) == 0:

        raise RuntimeError(
            "Dataset validation failed."
        )

    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    (
        y_true,
        y_pred,
        prediction_rows,
        top3_accuracy,
        top5_accuracy,
    ) = predict_dataset(
        model,
        entries,
        plantwild_classes,
    )

    # --------------------------------------------------------
    # Validate prediction count
    # --------------------------------------------------------

    print()

    print(
        "Prediction validation:"
    )

    print(
        f"Ground truth samples : "
        f"{len(y_true):,}"
    )

    print(
        f"Predicted samples    : "
        f"{len(y_pred):,}"
    )

    if len(y_true) != len(
        entries
    ):

        raise RuntimeError(
            "Not all selected samples "
            "were successfully evaluated."
        )

    if len(y_true) != len(
        y_pred
    ):

        raise RuntimeError(
            "Ground truth and prediction "
            "counts do not match."
        )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=SELECTED_CLASSES,
    )

    # --------------------------------------------------------
    # Accuracy
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    # --------------------------------------------------------
    # Balanced accuracy
    # --------------------------------------------------------

    balanced_accuracy = (
        balanced_accuracy_score(
            y_true,
            y_pred,
        )
    )

    # --------------------------------------------------------
    # Macro metrics
    # --------------------------------------------------------

    (
        macro_precision,
        macro_recall,
        macro_f1,
        _,
    ) = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=SELECTED_CLASSES,
        average="macro",
        zero_division=0,
    )

    # --------------------------------------------------------
    # Weighted metrics
    # --------------------------------------------------------

    (
        weighted_precision,
        weighted_recall,
        weighted_f1,
        _,
    ) = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=SELECTED_CLASSES,
        average="weighted",
        zero_division=0,
    )

    # --------------------------------------------------------
    # Save outputs
    # --------------------------------------------------------

    confusion_csv = (
        save_confusion_matrix_csv(
            matrix
        )
    )

    predictions_csv = (
        save_predictions_csv(
            prediction_rows
        )
    )

    confusion_png = (
        plot_confusion_matrix(
            matrix,
            normalized=False,
        )
    )

    normalized_png = (
        plot_confusion_matrix(
            matrix,
            normalized=True,
        )
    )

    report_file = (
        save_classification_report(
            y_true,
            y_pred,
        )
    )

    results_json = (
        save_results_json(
            matrix=matrix,
            evaluated_samples=len(
                y_true
            ),
            accuracy=accuracy,
            balanced_accuracy=balanced_accuracy,
            macro_precision=macro_precision,
            macro_recall=macro_recall,
            macro_f1=macro_f1,
            weighted_precision=weighted_precision,
            weighted_recall=weighted_recall,
            weighted_f1=weighted_f1,
            top1_accuracy=accuracy,
            top3_accuracy=top3_accuracy,
            top5_accuracy=top5_accuracy,
        )
    )

    # --------------------------------------------------------
    # Print matrix
    # --------------------------------------------------------

    print_confusion_matrix(
        matrix
    )

    # --------------------------------------------------------
    # FINAL METRICS
    # --------------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "FINAL 14-CLASS RESULTS"
    )

    print(
        "=" * 70
    )

    print()

    print(
        f"Evaluated samples       : "
        f"{len(y_true):,}"
    )

    print()

    print(
        f"Top-1 Accuracy          : "
        f"{accuracy:.4f} "
        f"({accuracy * 100:.2f}%)"
    )

    print(
        f"Top-3 Accuracy          : "
        f"{top3_accuracy:.4f} "
        f"({top3_accuracy * 100:.2f}%)"
    )

    print(
        f"Top-5 Accuracy          : "
        f"{top5_accuracy:.4f} "
        f"({top5_accuracy * 100:.2f}%)"
    )

    print(
        f"Balanced accuracy       : "
        f"{balanced_accuracy:.4f} "
        f"({balanced_accuracy * 100:.2f}%)"
    )

    print()

    print(
        "MACRO AVERAGE"
    )

    print(
        "-" * 40
    )

    print(
        f"Precision               : "
        f"{macro_precision:.4f} "
        f"({macro_precision * 100:.2f}%)"
    )

    print(
        f"Recall                  : "
        f"{macro_recall:.4f} "
        f"({macro_recall * 100:.2f}%)"
    )

    print(
        f"F1-score                : "
        f"{macro_f1:.4f} "
        f"({macro_f1 * 100:.2f}%)"
    )

    print()

    print(
        "WEIGHTED AVERAGE"
    )

    print(
        "-" * 40
    )

    print(
        f"Precision               : "
        f"{weighted_precision:.4f} "
        f"({weighted_precision * 100:.2f}%)"
    )

    print(
        f"Recall                  : "
        f"{weighted_recall:.4f} "
        f"({weighted_recall * 100:.2f}%)"
    )

    print(
        f"F1-score                : "
        f"{weighted_f1:.4f} "
        f"({weighted_f1 * 100:.2f}%)"
    )

    # --------------------------------------------------------
    # Output files
    # --------------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "OUTPUT FILES"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "Confusion matrix PNG:"
    )

    print(
        confusion_png
    )

    print()

    print(
        "Normalized confusion matrix PNG:"
    )

    print(
        normalized_png
    )

    print()

    print(
        "Confusion matrix CSV:"
    )

    print(
        confusion_csv
    )

    print()

    print(
        "Predictions CSV:"
    )

    print(
        predictions_csv
    )

    print()

    print(
        "Classification report:"
    )

    print(
        report_file
    )

    print()

    print(
        "Results JSON:"
    )

    print(
        results_json
    )

    print()
    print(
        "=" * 70
    )

    print(
        "EVALUATION FINISHED SUCCESSFULLY"
    )

    print(
        "=" * 70
    )

    print()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()