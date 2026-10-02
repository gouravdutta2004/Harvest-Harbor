"""
Harvest Harbor
Dedicated Crop Classification Training Script

Dataset:
    PlantVillage color dataset

Model:
    EfficientNetB0

Task:
    Crop/species classification

IMPORTANT:
    This model identifies the crop.
    It does NOT identify the disease.

Pipeline:

    PlantVillage
        |
        v
    Dataset validation
        |
        v
    Group-aware 80/10/10 split
        |
        v
    EfficientNetB0 transfer learning
        |
        v
    Fine tuning
        |
        v
    Best validation model
        |
        v
    Save model
        |
        v
    Reload saved model
        |
        v
    Test evaluation #1
        |
        v
    Test evaluation #2
        |
        v
    Verify identical results
        |
        v
    Save complete metadata

The script is intentionally conservative:
- It never evaluates an uncompiled model.
- It saves the model before final evaluation.
- It reloads the saved model before evaluation.
- It does not claim validation if evaluation fails.
- It saves the exact train/validation/test file lists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers


# ============================================================
# 1. CONFIGURATION
# ============================================================

SEED = 42

IMAGE_SIZE = (224, 224)

DEFAULT_BATCH_SIZE = 32

DEFAULT_INITIAL_EPOCHS = 15

DEFAULT_FINE_TUNE_EPOCHS = 10

INITIAL_LEARNING_RATE = 1e-3

FINE_TUNE_LEARNING_RATE = 1e-4

FINAL_EVALUATION_LEARNING_RATE = 1e-5

FINE_TUNE_LAST_N_LAYERS = 30

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# ============================================================
# 2. PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = SCRIPT_DIR.parent

DEFAULT_DATASET_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "plantvillage"
    / "raw"
    / "color"
)

OUTPUT_DIR = (
    SCRIPT_DIR
    / "crop_model"
)

MODEL_PATH = (
    OUTPUT_DIR
    / "crop_efficientnetb0.keras"
)

CLASS_NAMES_PATH = (
    OUTPUT_DIR
    / "crop_class_names.json"
)

SPLIT_PATH = (
    OUTPUT_DIR
    / "crop_training_split.json"
)

HISTORY_PATH = (
    OUTPUT_DIR
    / "training_history.json"
)

TRAINING_LOG_PATH = (
    OUTPUT_DIR
    / "training_summary.json"
)

INITIAL_CHECKPOINT_PATH = (
    OUTPUT_DIR
    / "crop_initial_best.keras"
)

FINE_TUNE_CHECKPOINT_PATH = (
    OUTPUT_DIR
    / "crop_finetune_best.keras"
)


# ============================================================
# 3. REPRODUCIBILITY
# ============================================================

def set_global_seed(seed: int = SEED) -> None:
    """
    Set deterministic random seeds.
    """

    os.environ["PYTHONHASHSEED"] = str(seed)

    random.seed(seed)

    np.random.seed(seed)

    tf.keras.utils.set_random_seed(seed)

    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass


# ============================================================
# 4. UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


def sha256_file(path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.

    Used for reproducibility metadata.
    """

    digest = hashlib.sha256()

    with path.open("rb") as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def write_json(
    path: Path,
    data,
) -> None:
    """
    Safely write JSON.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ============================================================
# 5. DATASET VALIDATION
# ============================================================

def validate_dataset_directory(
    dataset_dir: Path,
) -> None:
    """
    Validate dataset directory before training.
    """

    if not dataset_dir.exists():

        raise FileNotFoundError(
            "\nDataset directory does not exist:\n"
            f"{dataset_dir}\n\n"
            "Expected structure:\n"
            "datasets/plantvillage/raw/color/"
        )

    if not dataset_dir.is_dir():

        raise NotADirectoryError(
            f"Dataset path is not a directory:\n"
            f"{dataset_dir}"
        )


# ============================================================
# 6. CROP NAME EXTRACTION
# ============================================================

def crop_from_folder(
    folder_name: str,
) -> str:
    """
    Convert PlantVillage folder name to crop name.

    Example:

        Tomato___Tomato_mosaic_virus
        ->
        Tomato

        Potato___healthy
        ->
        Potato
    """

    if "___" in folder_name:

        crop_name = folder_name.split(
            "___",
            1,
        )[0]

    else:

        crop_name = folder_name

    crop_name = crop_name.strip()

    crop_name = crop_name.replace(
        "_",
        " ",
    )

    return crop_name


# ============================================================
# 7. GROUP KEY
# ============================================================

def extract_group_key(
    image_path: Path,
) -> str:
    """
    Create a deterministic group key.

    The dataset does not provide an explicit physical-plant
    identifier in this training script.

    Therefore we use:

        parent folder + filename prefix

    This reduces accidental leakage where filenames contain
    repeated source identifiers.

    IMPORTANT:
    This is a heuristic, not a guaranteed physical-plant ID.
    """

    stem = image_path.stem.strip()

    parts = stem.split("_")

    if len(parts) > 1:

        prefix = parts[0]

    else:

        prefix = stem

    return (
        f"{image_path.parent.name}::"
        f"{prefix}"
    )


# ============================================================
# 8. COLLECT IMAGES
# ============================================================

def collect_dataset(
    dataset_dir: Path,
):
    """
    Scan PlantVillage and return image records.

    Each record:

        {
            path,
            class_name,
            group_key
        }
    """

    validate_dataset_directory(
        dataset_dir
    )

    records = []

    class_directories = sorted(
        [
            path
            for path in dataset_dir.iterdir()
            if path.is_dir()
        ],
        key=lambda p: p.name.lower(),
    )

    if not class_directories:

        raise RuntimeError(
            "No class directories were found."
        )

    for class_dir in class_directories:

        class_name = crop_from_folder(
            class_dir.name
        )

        for image_path in sorted(
            class_dir.rglob("*")
        ):

            if not image_path.is_file():
                continue

            if (
                image_path.suffix.lower()
                not in SUPPORTED_EXTENSIONS
            ):
                continue

            records.append(
                {
                    "path": image_path,
                    "class_name": class_name,
                    "group_key": extract_group_key(
                        image_path
                    ),
                }
            )

    if not records:

        raise RuntimeError(
            "No supported images were found."
        )

    return records


# ============================================================
# 9. DATASET INTEGRITY CHECK
# ============================================================

def validate_records(
    records,
) -> None:
    """
    Check dataset records before splitting.
    """

    paths = [
        record["path"]
        for record in records
    ]

    duplicate_paths = (
        len(paths)
        != len(set(paths))
    )

    if duplicate_paths:

        raise RuntimeError(
            "Duplicate image paths detected."
        )

    missing = []

    for record in records:

        if not record["path"].exists():

            missing.append(
                str(record["path"])
            )

            if len(missing) >= 10:
                break

    if missing:

        raise RuntimeError(
            "Missing image files detected.\n"
            + "\n".join(missing)
        )


# ============================================================
# 10. GROUP-AWARE CLASS SPLIT
# ============================================================

def split_class_groups(
    class_records,
    seed: int = SEED,
):
    """
    Split one crop class into approximately:

        80% train
        10% validation
        10% test

    Entire groups are kept together.
    """

    rng = random.Random(
        seed
    )

    groups = {}

    for record in class_records:

        groups.setdefault(
            record["group_key"],
            [],
        ).append(record)

    group_list = list(
        groups.values()
    )

    rng.shuffle(
        group_list
    )

    total = len(
        class_records
    )

    target_train = (
        total * 0.80
    )

    target_validation = (
        total * 0.10
    )

    train = []
    validation = []
    test = []

    current_train = 0
    current_validation = 0

    for group in group_list:

        group_size = len(group)

        # Calculate how far each choice would be
        # from its desired target.
        train_error = abs(
            (
                current_train
                + group_size
            )
            - target_train
        )

        validation_error = abs(
            (
                current_validation
                + group_size
            )
            - (
                target_train
                + target_validation
            )
        )

        # Once train target is approximately reached,
        # fill validation.
        if current_train < target_train:

            train.append(group)

            current_train += group_size

        elif (
            current_validation
            < target_validation
        ):

            validation.append(group)

            current_validation += group_size

        else:

            test.append(group)

    # Flatten groups.
    train_records = [
        item
        for group in train
        for item in group
    ]

    validation_records = [
        item
        for group in validation
        for item in group
    ]

    test_records = [
        item
        for group in test
        for item in group
    ]

    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------
    #
    # This should only matter for unusual datasets with
    # extremely large groups.
    #

    if total >= 3:

        if not validation_records:

            if len(train) > 1:

                moved_group = train.pop()

                validation.append(
                    moved_group
                )

                train_records = [
                    item
                    for group in train
                    for item in group
                ]

                validation_records = [
                    item
                    for group in validation
                    for item in group
                ]

        if not test_records:

            if len(train) > 1:

                moved_group = train.pop()

                test.append(
                    moved_group
                )

                train_records = [
                    item
                    for group in train
                    for item in group
                ]

                test_records = [
                    item
                    for group in test
                    for item in group
                ]

    return (
        train_records,
        validation_records,
        test_records,
    )


# ============================================================
# 11. COMPLETE DATASET SPLIT
# ============================================================

def create_split(
    records,
    classes,
):
    """
    Create a deterministic class-balanced group-aware split.
    """

    by_class = {
        class_name: []
        for class_name in classes
    }

    for record in records:

        by_class[
            record["class_name"]
        ].append(record)

    train_records = []

    validation_records = []

    test_records = []

    class_statistics = {}

    for class_index, class_name in enumerate(
        classes
    ):

        class_records = by_class[
            class_name
        ]

        (
            class_train,
            class_validation,
            class_test,
        ) = split_class_groups(
            class_records,
            seed=SEED + class_index,
        )

        train_records.extend(
            class_train
        )

        validation_records.extend(
            class_validation
        )

        test_records.extend(
            class_test
        )

        class_statistics[
            class_name
        ] = {
            "total": len(
                class_records
            ),
            "train": len(
                class_train
            ),
            "validation": len(
                class_validation
            ),
            "test": len(
                class_test
            ),
            "unique_groups": len(
                {
                    item["group_key"]
                    for item in class_records
                }
            ),
        }

    # Deterministic shuffle.
    rng = random.Random(
        SEED
    )

    rng.shuffle(
        train_records
    )

    rng.shuffle(
        validation_records
    )

    rng.shuffle(
        test_records
    )

    # --------------------------------------------------------
    # Leakage verification
    # --------------------------------------------------------

    train_groups = {
        record["group_key"]
        for record in train_records
    }

    validation_groups = {
        record["group_key"]
        for record in validation_records
    }

    test_groups = {
        record["group_key"]
        for record in test_records
    }

    overlap_train_validation = (
        train_groups
        & validation_groups
    )

    overlap_train_test = (
        train_groups
        & test_groups
    )

    overlap_validation_test = (
        validation_groups
        & test_groups
    )

    if overlap_train_validation:

        raise RuntimeError(
            "Group leakage detected between "
            "train and validation."
        )

    if overlap_train_test:

        raise RuntimeError(
            "Group leakage detected between "
            "train and test."
        )

    if overlap_validation_test:

        raise RuntimeError(
            "Group leakage detected between "
            "validation and test."
        )

    # --------------------------------------------------------
    # Verify every record appears exactly once.
    # --------------------------------------------------------

    all_paths = {
        record["path"]
        for record in records
    }

    split_paths = (
        {
            record["path"]
            for record in train_records
        }
        |
        {
            record["path"]
            for record in validation_records
        }
        |
        {
            record["path"]
            for record in test_records
        }
    )

    if all_paths != split_paths:

        raise RuntimeError(
            "Dataset split does not contain exactly "
            "the original set of images."
        )

    if (
        len(train_records)
        + len(validation_records)
        + len(test_records)
        != len(records)
    ):

        raise RuntimeError(
            "Dataset split count mismatch."
        )

    return (
        train_records,
        validation_records,
        test_records,
        class_statistics,
        {
            "train_validation": len(
                overlap_train_validation
            ),
            "train_test": len(
                overlap_train_test
            ),
            "validation_test": len(
                overlap_validation_test
            ),
        },
    )


# ============================================================
# 12. IMAGE DECODER
# ============================================================

def decode_image(
    image_path,
):
    """
    Robust JPEG/PNG/WebP decoder.
    """

    image_bytes = tf.io.read_file(
        image_path
    )

    image = tf.image.decode_image(
        image_bytes,
        channels=3,
        expand_animations=False,
    )

    image.set_shape(
        [
            None,
            None,
            3,
        ]
    )

    image = tf.image.resize(
        image,
        IMAGE_SIZE,
        method=(
            tf.image.ResizeMethod.BILINEAR
        ),
    )

    image = tf.cast(
        image,
        tf.float32,
    )

    return image


# ============================================================
# 13. DATASET LOADER
# ============================================================

def make_dataset(
    records,
    class_to_index,
    batch_size,
    training=False,
):
    """
    Create tf.data.Dataset.
    """

    if not records:

        raise RuntimeError(
            "Attempted to create a dataset "
            "from zero images."
        )

    paths = np.asarray(
        [
            str(record["path"])
            for record in records
        ],
        dtype=str,
    )

    labels = np.asarray(
        [
            class_to_index[
                record["class_name"]
            ]
            for record in records
        ],
        dtype=np.int32,
    )

    dataset = (
        tf.data.Dataset.from_tensor_slices(
            (
                paths,
                labels,
            )
        )
    )

    if training:

        dataset = dataset.shuffle(
            buffer_size=min(
                len(records),
                4096,
            ),
            seed=SEED,
            reshuffle_each_iteration=True,
        )

    def load_example(
        path,
        label,
    ):

        image = decode_image(
            path
        )

        label = tf.cast(
            label,
            tf.int32,
        )

        return (
            image,
            label,
        )

    dataset = dataset.map(
        load_example,
        num_parallel_calls=(
            tf.data.AUTOTUNE
        ),
    )

    dataset = dataset.batch(
        batch_size,
        drop_remainder=False,
    )

    dataset = dataset.prefetch(
        tf.data.AUTOTUNE
    )

    return dataset


# ============================================================
# 14. MODEL CREATION
# ============================================================

def build_model(
    number_of_classes,
):
    """
    Build EfficientNetB0 classifier.
    """

    augmentation = (
        tf.keras.Sequential(
            [
                layers.RandomFlip(
                    "horizontal"
                ),

                layers.RandomRotation(
                    0.08
                ),

                layers.RandomZoom(
                    0.15
                ),

                layers.RandomContrast(
                    0.10
                ),
            ],
            name="data_augmentation",
        )
    )

    backbone = (
        tf.keras.applications.EfficientNetB0(
            include_top=False,
            weights="imagenet",
            input_shape=(
                IMAGE_SIZE[0],
                IMAGE_SIZE[1],
                3,
            ),
        )
    )

    # Phase 1:
    # freeze entire pretrained backbone.
    backbone.trainable = False

    inputs = tf.keras.Input(
        shape=(
            IMAGE_SIZE[0],
            IMAGE_SIZE[1],
            3,
        ),
        name="image",
    )

    x = augmentation(
        inputs
    )

    x = backbone(
        x,
        training=False,
    )

    x = layers.GlobalAveragePooling2D(
        name="global_average_pooling"
    )(x)

    x = layers.Dropout(
        0.25,
        name="dropout",
    )(x)

    outputs = layers.Dense(
        number_of_classes,
        activation="softmax",
        name="crop_probabilities",
    )(x)

    model = tf.keras.Model(
        inputs=inputs,
        outputs=outputs,
        name="crop_efficientnetb0",
    )

    return (
        model,
        backbone,
    )


# ============================================================
# 15. COMPILE MODEL
# ============================================================

def compile_model(
    model,
    learning_rate,
):
    """
    Compile model.

    IMPORTANT:
    This function is called again after loading a .keras
    model before evaluate().
    """

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=learning_rate
        ),

        loss=(
            "sparse_categorical_crossentropy"
        ),

        metrics=[
            tf.keras.metrics.SparseCategoricalAccuracy(
                name="accuracy"
            ),

            tf.keras.metrics.SparseTopKCategoricalAccuracy(
                k=3,
                name="top3_accuracy",
            ),
        ],
    )

    return model


# ============================================================
# 16. CALLBACKS
# ============================================================

def create_initial_callbacks():
    """
    Callbacks for phase 1.
    """

    return [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=(
                INITIAL_CHECKPOINT_PATH
            ),
            monitor="val_accuracy",
            mode="max",
            save_best_only=True,
            save_weights_only=False,
            verbose=1,
        ),

        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_accuracy",
            mode="max",
            factor=0.5,
            patience=2,
            min_lr=1e-6,
            verbose=1,
        ),
    ]


def create_fine_tune_callbacks():
    """
    Callbacks for phase 2.

    Separate checkpoint so the validation best is
    tracked from the beginning of fine-tuning.
    """

    return [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=(
                FINE_TUNE_CHECKPOINT_PATH
            ),
            monitor="val_accuracy",
            mode="max",
            save_best_only=True,
            save_weights_only=False,
            verbose=1,
        ),

        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_accuracy",
            mode="max",
            factor=0.5,
            patience=2,
            min_lr=1e-7,
            verbose=1,
        ),
    ]


# ============================================================
# 17. HISTORY CLEANING
# ============================================================

def clean_history(
    history,
):
    """
    Convert Keras History object to JSON-compatible data.
    """

    if history is None:

        return {}

    result = {}

    for key, values in (
        history.history.items()
    ):

        result[key] = [
            float(value)
            for value in values
        ]

    return result


# ============================================================
# 18. EVALUATE SAVED MODEL
# ============================================================

def evaluate_saved_model(
    model_path,
    test_dataset,
):
    """
    Reload and evaluate saved model.

    This deliberately compiles the model before evaluation.
    """

    if not model_path.exists():

        raise FileNotFoundError(
            "Saved model does not exist:\n"
            f"{model_path}"
        )

    print(
        "\n[INFO] Loading saved model:"
    )

    print(
        f"       {model_path}"
    )

    loaded_model = (
        tf.keras.models.load_model(
            model_path,
            compile=False,
        )
    )

    print(
        "[INFO] Compiling loaded model..."
    )

    compile_model(
        loaded_model,
        FINAL_EVALUATION_LEARNING_RATE,
    )

    print(
        "[INFO] Running test evaluation..."
    )

    metrics = loaded_model.evaluate(
        test_dataset,
        verbose=1,
        return_dict=True,
    )

    cleaned = {}

    for key, value in metrics.items():

        cleaned[key] = float(
            value
        )

    return cleaned


# ============================================================
# 19. VERIFY TEST RESULTS
# ============================================================

def verify_test_metrics(
    first,
    second,
):
    """
    Verify that two evaluations of the same deterministic
    test dataset produce the same results.
    """

    keys = set(first.keys())

    if keys != set(second.keys()):

        raise RuntimeError(
            "Test evaluation metric names differ "
            "between the two evaluation passes."
        )

    differences = {}

    for key in sorted(keys):

        difference = abs(
            first[key]
            - second[key]
        )

        differences[key] = difference

        if difference > 1e-6:

            raise RuntimeError(
                "Repeated test evaluation produced "
                f"different '{key}' values: "
                f"{first[key]} vs {second[key]}"
            )

    return differences


# ============================================================
# 20. MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Train PlantVillage crop classifier "
            "using EfficientNetB0."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_DIR,
        help=(
            "PlantVillage color dataset directory."
        ),
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=DEFAULT_INITIAL_EPOCHS,
        help=(
            "Number of initial transfer-learning epochs."
        ),
    )

    parser.add_argument(
        "--fine-tune-epochs",
        type=int,
        default=DEFAULT_FINE_TUNE_EPOCHS,
        help=(
            "Number of fine-tuning epochs."
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Batch size.",
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Validate arguments
    # --------------------------------------------------------

    if args.epochs < 1:

        raise ValueError(
            "--epochs must be at least 1."
        )

    if args.fine_tune_epochs < 1:

        raise ValueError(
            "--fine-tune-epochs must be at least 1."
        )

    if args.batch_size < 1:

        raise ValueError(
            "--batch-size must be at least 1."
        )

    # --------------------------------------------------------
    # Reproducibility
    # --------------------------------------------------------

    set_global_seed(
        SEED
    )

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("HARVEST HARBOR - CROP CLASSIFIER")
    print("=" * 75)

    print(
        f"\nTensorFlow version: "
        f"{tf.__version__}"
    )

    print(
        f"Dataset: "
        f"{args.dataset.resolve()}"
    )

    print(
        f"Image size: "
        f"{IMAGE_SIZE}"
    )

    print(
        f"Batch size: "
        f"{args.batch_size}"
    )

    print(
        f"Initial epochs: "
        f"{args.epochs}"
    )

    print(
        f"Fine-tune epochs: "
        f"{args.fine_tune_epochs}"
    )

    # --------------------------------------------------------
    # GPU information
    # --------------------------------------------------------

    gpus = tf.config.list_physical_devices(
        "GPU"
    )

    print(
        f"GPUs detected: "
        f"{len(gpus)}"
    )

    # --------------------------------------------------------
    # Dataset
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("STEP 1 — DATASET DISCOVERY")
    print("=" * 75)

    records = collect_dataset(
        args.dataset
    )

    validate_records(
        records
    )

    classes = sorted(
        {
            record["class_name"]
            for record in records
        }
    )

    if len(classes) < 2:

        raise RuntimeError(
            "At least two crop classes are required."
        )

    class_to_index = {
        class_name: index
        for index, class_name in enumerate(
            classes
        )
    }

    print(
        f"\nTotal images: "
        f"{len(records)}"
    )

    print(
        f"Number of crop classes: "
        f"{len(classes)}"
    )

    print(
        "\nCrop classes:"
    )

    for index, class_name in enumerate(
        classes
    ):

        print(
            f"  {index:02d} -> {class_name}"
        )

    # --------------------------------------------------------
    # Split
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("STEP 2 — GROUP-AWARE DATASET SPLIT")
    print("=" * 75)

    (
        train_records,
        validation_records,
        test_records,
        class_statistics,
        group_overlap,
    ) = create_split(
        records,
        classes,
    )

    print(
        f"\nTrain images: "
        f"{len(train_records)}"
    )

    print(
        f"Validation images: "
        f"{len(validation_records)}"
    )

    print(
        f"Test images: "
        f"{len(test_records)}"
    )

    # --------------------------------------------------------
    # Basic split safety
    # --------------------------------------------------------

    if not train_records:

        raise RuntimeError(
            "Training split is empty."
        )

    if not validation_records:

        raise RuntimeError(
            "Validation split is empty."
        )

    if not test_records:

        raise RuntimeError(
            "Test split is empty."
        )

    # --------------------------------------------------------
    # Save exact split metadata
    # --------------------------------------------------------

    try:

        relative_root = (
            args.dataset.resolve()
        )

        def relative_path(record):

            try:

                return str(
                    record["path"]
                    .resolve()
                    .relative_to(
                        relative_root
                    )
                )

            except ValueError:

                return str(
                    record["path"].resolve()
                )

        split_metadata = {

            "created_at_utc": utc_now(),

            "seed": SEED,

            "dataset_root": str(
                relative_root
            ),

            "dataset_type": (
                "PlantVillage color"
            ),

            "split_method": (
                "Class-wise group-aware split"
            ),

            "target_ratios": {
                "train": 0.80,
                "validation": 0.10,
                "test": 0.10,
            },

            "actual_counts": {
                "total": len(records),
                "train": len(
                    train_records
                ),
                "validation": len(
                    validation_records
                ),
                "test": len(
                    test_records
                ),
            },

            "classes": classes,

            "class_to_index": (
                class_to_index
            ),

            "class_statistics": (
                class_statistics
            ),

            "group_overlap": (
                group_overlap
            ),

            "limitations": (
                "The group key is derived from "
                "filename structure and is not an "
                "explicit physical-plant identifier. "
                "Therefore it reduces some potential "
                "leakage but cannot guarantee complete "
                "source isolation."
            ),

            "train_files": [
                relative_path(record)
                for record in train_records
            ],

            "validation_files": [
                relative_path(record)
                for record in validation_records
            ],

            "test_files": [
                relative_path(record)
                for record in test_records
            ],
        }

        write_json(
            SPLIT_PATH,
            split_metadata,
        )

    except Exception as exc:

        raise RuntimeError(
            "Could not save dataset split metadata."
        ) from exc

    print(
        f"\nSaved exact split:"
        f"\n{SPLIT_PATH}"
    )

    # --------------------------------------------------------
    # Save classes
    # --------------------------------------------------------

    class_metadata = {

        "created_at_utc": utc_now(),

        "num_classes": len(classes),

        "classes": classes,

        "class_to_index": (
            class_to_index
        ),

        "index_to_class": {
            str(index): class_name
            for class_name, index
            in class_to_index.items()
        },
    }

    write_json(
        CLASS_NAMES_PATH,
        class_metadata,
    )

    print(
        f"Saved class metadata:"
        f"\n{CLASS_NAMES_PATH}"
    )

    # --------------------------------------------------------
    # Build datasets
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("STEP 3 — BUILD TENSORFLOW DATASETS")
    print("=" * 75)

    train_ds = make_dataset(
        train_records,
        class_to_index,
        args.batch_size,
        training=True,
    )

    validation_ds = make_dataset(
        validation_records,
        class_to_index,
        args.batch_size,
        training=False,
    )

    test_ds = make_dataset(
        test_records,
        class_to_index,
        args.batch_size,
        training=False,
    )

    print(
        "\nTensorFlow datasets created successfully."
    )

    # --------------------------------------------------------
    # Build model
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("STEP 4 — BUILD EFFICIENTNETB0")
    print("=" * 75)

    model, backbone = build_model(
        len(classes)
    )

    compile_model(
        model,
        INITIAL_LEARNING_RATE,
    )

    print(
        "\nModel created and compiled successfully."
    )

    # --------------------------------------------------------
    # Phase 1
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("STEP 5 — INITIAL TRANSFER LEARNING")
    print("=" * 75)

    initial_history = model.fit(
        train_ds,
        validation_data=validation_ds,
        epochs=args.epochs,
        callbacks=create_initial_callbacks(),
        verbose=1,
    )

    print(
        "\nInitial training completed."
    )

    # --------------------------------------------------------
    # Load best initial model
    # --------------------------------------------------------

    if not INITIAL_CHECKPOINT_PATH.exists():

        raise RuntimeError(
            "Initial training completed but the "
            "best initial checkpoint was not created."
        )

    print(
        "\nLoading best initial checkpoint..."
    )

    model = tf.keras.models.load_model(
        INITIAL_CHECKPOINT_PATH,
        compile=False,
    )

    # Find EfficientNet backbone.
    try:

        backbone = model.get_layer(
            "efficientnetb0"
        )

    except ValueError as exc:

        raise RuntimeError(
            "Could not find EfficientNetB0 "
            "backbone in saved model."
        ) from exc

    # --------------------------------------------------------
    # Phase 2
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("STEP 6 — FINE-TUNING")
    print("=" * 75)

    backbone.trainable = True

    freeze_until = max(
        0,
        len(backbone.layers)
        - FINE_TUNE_LAST_N_LAYERS,
    )

    for layer_index, layer in enumerate(
        backbone.layers
    ):

        if layer_index < freeze_until:

            layer.trainable = False

        else:

            layer.trainable = True

        # Freeze BatchNorm for stable fine-tuning.
        if isinstance(
            layer,
            tf.keras.layers.BatchNormalization,
        ):

            layer.trainable = False

    trainable_backbone_layers = sum(
        1
        for layer in backbone.layers
        if layer.trainable
    )

    print(
        f"\nEfficientNetB0 total layers: "
        f"{len(backbone.layers)}"
    )

    print(
        f"Trainable backbone layers: "
        f"{trainable_backbone_layers}"
    )

    # IMPORTANT:
    # Recompile after changing trainable layers.
    compile_model(
        model,
        FINE_TUNE_LEARNING_RATE,
    )

    fine_tune_history = model.fit(
        train_ds,
        validation_data=validation_ds,
        epochs=args.fine_tune_epochs,
        callbacks=create_fine_tune_callbacks(),
        verbose=1,
    )

    print(
        "\nFine-tuning completed."
    )

    # --------------------------------------------------------
    # Checkpoint existence
    # --------------------------------------------------------

    if not FINE_TUNE_CHECKPOINT_PATH.exists():

        raise RuntimeError(
            "Fine-tuning completed but the "
            "best fine-tuning checkpoint was not created."
        )

    # --------------------------------------------------------
    # Load BEST fine-tuned model
    # --------------------------------------------------------

    print(
        "\nLoading best fine-tuned model..."
    )

    best_model = (
        tf.keras.models.load_model(
            FINE_TUNE_CHECKPOINT_PATH,
            compile=False,
        )
    )

    # --------------------------------------------------------
    # Compile before save/evaluation
    # --------------------------------------------------------

    print(
        "Compiling best fine-tuned model..."
    )

    compile_model(
        best_model,
        FINAL_EVALUATION_LEARNING_RATE,
    )

    # --------------------------------------------------------
    # Save final production model
    # --------------------------------------------------------

    print(
        "\nSaving final crop model..."
    )

    best_model.save(
        MODEL_PATH
    )

    if not MODEL_PATH.exists():

        raise RuntimeError(
            "Model save command completed but "
            "model file does not exist."
        )

    model_size = (
        MODEL_PATH.stat().st_size
    )

    if model_size <= 0:

        raise RuntimeError(
            "Saved model file is empty."
        )

    print(
        f"\nFinal model saved:"
        f"\n{MODEL_PATH}"
    )

    print(
        f"Model size: "
        f"{model_size / (1024 * 1024):.2f} MB"
    )

    # --------------------------------------------------------
    # FIRST TEST EVALUATION
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("STEP 7 — TEST EVALUATION #1")
    print("=" * 75)

    first_test_metrics = (
        evaluate_saved_model(
            MODEL_PATH,
            test_ds,
        )
    )

    print(
        "\nFirst test evaluation:"
    )

    for metric_name, metric_value in (
        first_test_metrics.items()
    ):

        print(
            f"  {metric_name}: "
            f"{metric_value:.8f}"
        )

    # --------------------------------------------------------
    # SECOND TEST EVALUATION
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("STEP 8 — TEST EVALUATION #2")
    print("=" * 75)

    second_test_metrics = (
        evaluate_saved_model(
            MODEL_PATH,
            test_ds,
        )
    )

    print(
        "\nSecond test evaluation:"
    )

    for metric_name, metric_value in (
        second_test_metrics.items()
    ):

        print(
            f"  {metric_name}: "
            f"{metric_value:.8f}"
        )

    # --------------------------------------------------------
    # Verify both evaluations
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("STEP 9 — VERIFY TEST RESULTS")
    print("=" * 75)

    metric_differences = (
        verify_test_metrics(
            first_test_metrics,
            second_test_metrics,
        )
    )

    print(
        "\nRepeated evaluation differences:"
    )

    for metric_name, difference in (
        metric_differences.items()
    ):

        print(
            f"  {metric_name}: "
            f"{difference:.12f}"
        )

    # --------------------------------------------------------
    # Save history
    # --------------------------------------------------------

    history_metadata = {

        "created_at_utc": utc_now(),

        "status": (
            "SUCCESS"
        ),

        "model": {

            "name": (
                "crop_efficientnetb0"
            ),

            "architecture": (
                "EfficientNetB0"
            ),

            "input_size": list(
                IMAGE_SIZE
            ),

            "num_classes": len(
                classes
            ),

            "classes": classes,
        },

        "dataset": {

            "name": (
                "PlantVillage color"
            ),

            "total_images": len(
                records
            ),

            "train_images": len(
                train_records
            ),

            "validation_images": len(
                validation_records
            ),

            "test_images": len(
                test_records
            ),

            "dataset_root": str(
                args.dataset.resolve()
            ),
        },

        "training": {

            "seed": SEED,

            "batch_size": (
                args.batch_size
            ),

            "initial_epochs": (
                args.epochs
            ),

            "fine_tune_epochs": (
                args.fine_tune_epochs
            ),

            "initial_learning_rate": (
                INITIAL_LEARNING_RATE
            ),

            "fine_tune_learning_rate": (
                FINE_TUNE_LEARNING_RATE
            ),

            "final_evaluation_learning_rate": (
                FINAL_EVALUATION_LEARNING_RATE
            ),

            "fine_tune_last_n_layers": (
                FINE_TUNE_LAST_N_LAYERS
            ),

            "batch_normalization_frozen": True,
        },

        "initial_training_history": (
            clean_history(
                initial_history
            )
        ),

        "fine_tuning_history": (
            clean_history(
                fine_tune_history
            )
        ),

        "test_evaluation": {

            "pass_1": (
                first_test_metrics
            ),

            "pass_2": (
                second_test_metrics
            ),

            "metric_differences": (
                metric_differences
            ),

            "consistent": True,
        },

        "artifacts": {

            "model": str(
                MODEL_PATH
            ),

            "class_names": str(
                CLASS_NAMES_PATH
            ),

            "split": str(
                SPLIT_PATH
            ),

            "initial_checkpoint": str(
                INITIAL_CHECKPOINT_PATH
            ),

            "fine_tune_checkpoint": str(
                FINE_TUNE_CHECKPOINT_PATH
            ),
        },

        "model_sha256": (
            sha256_file(
                MODEL_PATH
            )
        ),

        "validation_note": (
            "The reported test metrics are "
            "held-out PlantVillage metrics. "
            "They do not establish real-world "
            "farmer-field performance."
        ),
    }

    write_json(
        HISTORY_PATH,
        history_metadata,
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n")
    print("=" * 75)
    print("FINAL TEST EVALUATION RESULTS")
    print("=" * 75)

    print(
        f"\ntest_loss: "
        f"{second_test_metrics['loss']:.8f}"
    )

    print(
        f"test_accuracy: "
        f"{second_test_metrics['accuracy']:.8f}"
    )

    print(
        f"test_top3_accuracy: "
        f"{second_test_metrics['top3_accuracy']:.8f}"
    )

    print("\n")
    print("=" * 75)
    print("TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 75)

    print(
        "\nFinal model:"
    )

    print(
        MODEL_PATH
    )

    print(
        "\nClass metadata:"
    )

    print(
        CLASS_NAMES_PATH
    )

    print(
        "\nExact dataset split:"
    )

    print(
        SPLIT_PATH
    )

    print(
        "\nComplete training history:"
    )

    print(
        HISTORY_PATH
    )

    print(
        "\nModel SHA-256:"
    )

    print(
        history_metadata[
            "model_sha256"
        ]
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "These are PlantVillage held-out "
        "test results only."
    )

    print(
        "They should not be presented as "
        "real-world field validation."
    )


# ============================================================
# 21. ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\n\nTraining interrupted by user."
        )

        raise SystemExit(130)

    except Exception as error:

        print(
            "\n\n"
            + "=" * 75
        )

        print(
            "TRAINING FAILED"
        )

        print(
            "=" * 75
        )

        print(
            f"\nError type: "
            f"{type(error).__name__}"
        )

        print(
            f"Error message:\n"
            f"{error}"
        )

        print(
            "\nThe model is NOT marked as successfully "
            "validated."
        )

        raise