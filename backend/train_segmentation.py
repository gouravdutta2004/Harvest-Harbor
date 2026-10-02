import os
import json
import random
import argparse

import cv2
import numpy as np
import tensorflow as tf

from tensorflow.keras import layers, Model
from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau
)


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_DIR = os.path.join(
    BASE_DIR,
    "datasets",
    "plantseg"
)

TRAIN_IMAGE_DIR = os.path.join(
    DATASET_DIR,
    "images",
    "train"
)

TRAIN_MASK_DIR = os.path.join(
    DATASET_DIR,
    "annotations",
    "train"
)

TEST_IMAGE_DIR = os.path.join(
    DATASET_DIR,
    "images",
    "test"
)

TEST_MASK_DIR = os.path.join(
    DATASET_DIR,
    "annotations",
    "test"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "backend",
    "segmentation_model"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "unet_plantseg.keras"
)

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# IMAGE SETTINGS
# ============================================================

IMG_SIZE = 256

CHANNELS = 3

BATCH_SIZE = 4

INITIAL_LEARNING_RATE = 1e-4

VALIDATION_SPLIT = 0.10


# ============================================================
# GPU CONFIGURATION
# ============================================================

gpus = tf.config.list_physical_devices("GPU")

if gpus:
    print(f"GPUs detected: {len(gpus)}")

    for gpu in gpus:
        try:
            tf.config.experimental.set_memory_growth(
                gpu,
                True
            )
        except Exception:
            pass
else:
    print("Num GPUs: 0")


# ============================================================
# FILE UTILITIES
# ============================================================

VALID_IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff"
)


def get_image_files(directory):
    """
    Return all image files recursively.
    """

    files = []

    if not os.path.exists(directory):
        return files

    for root, _, filenames in os.walk(directory):

        for filename in filenames:

            if filename.lower().endswith(
                VALID_IMAGE_EXTENSIONS
            ):

                files.append(
                    os.path.join(root, filename)
                )

    return sorted(files)


def find_matching_mask(image_path, mask_dir):
    """
    Find corresponding PlantSeg mask.

    Supports:
        image.jpg -> image.png
        image.jpeg -> image.png
        image.png -> image.png

    Also checks recursively.
    """

    filename = os.path.basename(image_path)

    stem = os.path.splitext(filename)[0]

    possible_names = [
        stem + ".png",
        stem + ".jpg",
        stem + ".jpeg",
        stem + ".bmp",
        stem + ".tif",
        stem + ".tiff"
    ]

    # Direct paths first
    for name in possible_names:

        candidate = os.path.join(
            mask_dir,
            name
        )

        if os.path.exists(candidate):
            return candidate

    # Recursive fallback
    for root, _, filenames in os.walk(mask_dir):

        for filename in filenames:

            if os.path.splitext(filename)[0] == stem:

                return os.path.join(
                    root,
                    filename
                )

    return None


def build_image_mask_pairs(image_dir, mask_dir):
    """
    Match images with masks.
    """

    image_files = get_image_files(image_dir)

    pairs = []

    missing_masks = []

    for image_path in image_files:

        mask_path = find_matching_mask(
            image_path,
            mask_dir
        )

        if mask_path is not None:

            pairs.append(
                (
                    image_path,
                    mask_path
                )
            )

        else:

            missing_masks.append(
                image_path
            )

    print(
        f"Images found: {len(image_files)}"
    )

    print(
        f"Matched image-mask pairs: {len(pairs)}"
    )

    print(
        f"Missing masks: {len(missing_masks)}"
    )

    if missing_masks:

        print("\nFirst missing masks:")

        for path in missing_masks[:5]:
            print(path)

    return pairs


# ============================================================
# DATA LOADING
# ============================================================

def load_image_mask(image_path, mask_path):
    """
    Load image and PlantSeg mask.

    IMPORTANT:
    tf.numpy_function passes Python bytes objects here.
    Therefore we must NOT blindly call .numpy().
    """

    # --------------------------------------------------------
    # Convert image path
    # --------------------------------------------------------

    if isinstance(image_path, bytes):

        image_path = image_path.decode("utf-8")

    elif isinstance(image_path, np.ndarray):

        image_path = image_path.item()

        if isinstance(image_path, bytes):

            image_path = image_path.decode("utf-8")

        else:

            image_path = str(image_path)

    else:

        image_path = str(image_path)


    # --------------------------------------------------------
    # Convert mask path
    # --------------------------------------------------------

    if isinstance(mask_path, bytes):

        mask_path = mask_path.decode("utf-8")

    elif isinstance(mask_path, np.ndarray):

        mask_path = mask_path.item()

        if isinstance(mask_path, bytes):

            mask_path = mask_path.decode("utf-8")

        else:

            mask_path = str(mask_path)

    else:

        mask_path = str(mask_path)


    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    image = cv2.imread(
        image_path,
        cv2.IMREAD_COLOR
    )

    if image is None:

        raise ValueError(
            f"Could not read image:\n{image_path}"
        )


    # BGR -> RGB
    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )


    # Resize image
    image = cv2.resize(
        image,
        (IMG_SIZE, IMG_SIZE),
        interpolation=cv2.INTER_AREA
    )


    # Normalize image
    image = image.astype(
        np.float32
    ) / 255.0


    # --------------------------------------------------------
    # Read mask
    # --------------------------------------------------------

    mask = cv2.imread(
        mask_path,
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:

        raise ValueError(
            f"Could not read mask:\n{mask_path}"
        )


    # Resize mask using nearest-neighbor
    mask = cv2.resize(
        mask,
        (IMG_SIZE, IMG_SIZE),
        interpolation=cv2.INTER_NEAREST
    )


    # --------------------------------------------------------
    # Convert PlantSeg mask to binary
    # --------------------------------------------------------
    #
    # 0       = background
    # > 0     = disease/segmented region
    #

    mask = (
        mask > 0
    ).astype(
        np.float32
    )


    # Add channel dimension
    mask = np.expand_dims(
        mask,
        axis=-1
    )


    return image, mask


# ============================================================
# TENSORFLOW DATASET PARSER
# ============================================================

def parse_function(image_path, mask_path):

    image, mask = tf.numpy_function(
        func=load_image_mask,
        inp=[
            image_path,
            mask_path
        ],
        Tout=[
            tf.float32,
            tf.float32
        ]
    )

    # IMPORTANT:
    # numpy_function loses shape information.
    # Restore it explicitly.

    image.set_shape(
        [
            IMG_SIZE,
            IMG_SIZE,
            CHANNELS
        ]
    )

    mask.set_shape(
        [
            IMG_SIZE,
            IMG_SIZE,
            1
        ]
    )

    return image, mask


# ============================================================
# AUGMENTATION
# ============================================================

def augment(image, mask):

    # Random horizontal flip
    flip_lr = tf.random.uniform([]) > 0.5

    image = tf.cond(
        flip_lr,
        lambda: tf.image.flip_left_right(image),
        lambda: image
    )

    mask = tf.cond(
        flip_lr,
        lambda: tf.image.flip_left_right(mask),
        lambda: mask
    )


    # Random vertical flip
    flip_ud = tf.random.uniform([]) > 0.5

    image = tf.cond(
        flip_ud,
        lambda: tf.image.flip_up_down(image),
        lambda: image
    )

    mask = tf.cond(
        flip_ud,
        lambda: tf.image.flip_up_down(mask),
        lambda: mask
    )


    # Random 90-degree rotation
    k = tf.random.uniform(
        shape=[],
        minval=0,
        maxval=4,
        dtype=tf.int32
    )

    image = tf.image.rot90(
        image,
        k
    )

    mask = tf.image.rot90(
        mask,
        k
    )


    # Image-only brightness augmentation
    image = tf.image.random_brightness(
        image,
        max_delta=0.10
    )

    image = tf.clip_by_value(
        image,
        0.0,
        1.0
    )


    # Image-only contrast augmentation
    image = tf.image.random_contrast(
        image,
        lower=0.9,
        upper=1.1
    )

    image = tf.clip_by_value(
        image,
        0.0,
        1.0
    )


    return image, mask


# ============================================================
# DATASET CREATION
# ============================================================

def create_dataset(
    pairs,
    batch_size,
    training=False
):

    image_paths = [
        pair[0]
        for pair in pairs
    ]

    mask_paths = [
        pair[1]
        for pair in pairs
    ]


    dataset = tf.data.Dataset.from_tensor_slices(
        (
            image_paths,
            mask_paths
        )
    )


    if training:

        dataset = dataset.shuffle(
            buffer_size=max(
                len(pairs),
                100
            ),
            seed=SEED,
            reshuffle_each_iteration=True
        )


    dataset = dataset.map(
        parse_function,
        num_parallel_calls=tf.data.AUTOTUNE
    )


    if training:

        dataset = dataset.map(
            augment,
            num_parallel_calls=tf.data.AUTOTUNE
        )


    dataset = dataset.batch(
        batch_size,
        drop_remainder=False
    )


    dataset = dataset.prefetch(
        tf.data.AUTOTUNE
    )


    return dataset


# ============================================================
# SANITY CHECK
# ============================================================

def dataset_sanity_check(dataset):

    print("\n" + "=" * 70)
    print("DATASET SANITY CHECK")
    print("=" * 70)

    try:

        images, masks = next(
            iter(dataset)
        )

        print(
            f"Image batch shape: {images.shape}"
        )

        print(
            f"Mask batch shape: {masks.shape}"
        )

        print(
            f"Image min: {tf.reduce_min(images).numpy():.4f}"
        )

        print(
            f"Image max: {tf.reduce_max(images).numpy():.4f}"
        )

        print(
            f"Mask min: {tf.reduce_min(masks).numpy():.4f}"
        )

        print(
            f"Mask max: {tf.reduce_max(masks).numpy():.4f}"
        )


        foreground_pixels = tf.reduce_sum(
            masks
        ).numpy()

        total_pixels = tf.size(
            masks
        ).numpy()

        foreground_percentage = (
            foreground_pixels /
            total_pixels
        ) * 100.0


        print(
            f"Mask foreground: "
            f"{foreground_percentage:.2f}%"
        )


        if foreground_percentage <= 0:

            raise ValueError(
                "SANITY CHECK FAILED: "
                "mask contains no foreground pixels."
            )


        print(
            "Dataset sanity check: PASSED"
        )


    except Exception as e:

        print(
            "\nDATASET SANITY CHECK FAILED:"
        )

        print(e)

        raise


# ============================================================
# DICE METRIC
# ============================================================

def dice_coefficient(
    y_true,
    y_pred,
    smooth=1e-6
):

    y_true = tf.cast(
        y_true,
        tf.float32
    )

    y_pred = tf.cast(
        y_pred,
        tf.float32
    )


    # Flatten
    y_true = tf.reshape(
        y_true,
        [-1]
    )

    y_pred = tf.reshape(
        y_pred,
        [-1]
    )


    intersection = tf.reduce_sum(
        y_true * y_pred
    )


    denominator = (
        tf.reduce_sum(y_true)
        +
        tf.reduce_sum(y_pred)
    )


    dice = (
        2.0 * intersection
        +
        smooth
    ) / (
        denominator
        +
        smooth
    )


    return dice


# ============================================================
# IOU METRIC
# ============================================================

def iou_coefficient(
    y_true,
    y_pred,
    smooth=1e-6
):

    y_true = tf.cast(
        y_true,
        tf.float32
    )

    y_pred = tf.cast(
        y_pred,
        tf.float32
    )


    y_true = tf.reshape(
        y_true,
        [-1]
    )

    y_pred = tf.reshape(
        y_pred,
        [-1]
    )


    intersection = tf.reduce_sum(
        y_true * y_pred
    )


    union = (
        tf.reduce_sum(y_true)
        +
        tf.reduce_sum(y_pred)
        -
        intersection
    )


    iou = (
        intersection
        +
        smooth
    ) / (
        union
        +
        smooth
    )


    return iou


# ============================================================
# PRECISION
# ============================================================

def precision_metric(
    y_true,
    y_pred
):

    y_pred_binary = tf.cast(
        y_pred > 0.5,
        tf.float32
    )

    y_true = tf.cast(
        y_true,
        tf.float32
    )


    true_positive = tf.reduce_sum(
        y_true * y_pred_binary
    )

    false_positive = tf.reduce_sum(
        (1.0 - y_true) * y_pred_binary
    )


    precision = (
        true_positive + 1e-6
    ) / (
        true_positive
        +
        false_positive
        +
        1e-6
    )


    return precision


# ============================================================
# RECALL
# ============================================================

def recall_metric(
    y_true,
    y_pred
):

    y_pred_binary = tf.cast(
        y_pred > 0.5,
        tf.float32
    )

    y_true = tf.cast(
        y_true,
        tf.float32
    )


    true_positive = tf.reduce_sum(
        y_true * y_pred_binary
    )

    false_negative = tf.reduce_sum(
        y_true * (1.0 - y_pred_binary)
    )


    recall = (
        true_positive + 1e-6
    ) / (
        true_positive
        +
        false_negative
        +
        1e-6
    )


    return recall


# ============================================================
# DICE LOSS
# ============================================================

def dice_loss(
    y_true,
    y_pred
):

    return 1.0 - dice_coefficient(
        y_true,
        y_pred
    )


# ============================================================
# COMBINED LOSS
# ============================================================

def combined_loss(
    y_true,
    y_pred
):

    # Binary cross entropy
    bce = tf.keras.losses.binary_crossentropy(
        y_true,
        y_pred
    )

    bce = tf.reduce_mean(
        bce
    )


    # Dice loss
    d_loss = dice_loss(
        y_true,
        y_pred
    )


    # Combined
    return (
        0.5 * bce
        +
        0.5 * d_loss
    )


# ============================================================
# U-NET BLOCK
# ============================================================

def conv_block(
    x,
    filters,
    dropout_rate=0.0
):

    x = layers.Conv2D(
        filters,
        3,
        padding="same",
        kernel_initializer="he_normal"
    )(x)

    x = layers.BatchNormalization()(x)

    x = layers.Activation(
        "relu"
    )(x)


    x = layers.Conv2D(
        filters,
        3,
        padding="same",
        kernel_initializer="he_normal"
    )(x)

    x = layers.BatchNormalization()(x)

    x = layers.Activation(
        "relu"
    )(x)


    if dropout_rate > 0:

        x = layers.Dropout(
            dropout_rate
        )(x)


    return x


# ============================================================
# U-NET MODEL
# ============================================================

def build_unet():

    inputs = layers.Input(
        shape=(
            IMG_SIZE,
            IMG_SIZE,
            CHANNELS
        ),
        name="input_layer"
    )


    # --------------------------------------------------------
    # Encoder 1
    # --------------------------------------------------------

    c1 = conv_block(
        inputs,
        32
    )

    p1 = layers.MaxPooling2D(
        2
    )(c1)


    # --------------------------------------------------------
    # Encoder 2
    # --------------------------------------------------------

    c2 = conv_block(
        p1,
        64
    )

    p2 = layers.MaxPooling2D(
        2
    )(c2)


    # --------------------------------------------------------
    # Encoder 3
    # --------------------------------------------------------

    c3 = conv_block(
        p2,
        128
    )

    p3 = layers.MaxPooling2D(
        2
    )(c3)


    # --------------------------------------------------------
    # Bottleneck
    # --------------------------------------------------------

    c4 = conv_block(
        p3,
        256,
        dropout_rate=0.20
    )


    # --------------------------------------------------------
    # Decoder 1
    # --------------------------------------------------------

    u3 = layers.Conv2DTranspose(
        128,
        2,
        strides=2,
        padding="same"
    )(c4)

    u3 = layers.Concatenate()(
        [
            u3,
            c3
        ]
    )

    c5 = conv_block(
        u3,
        128
    )


    # --------------------------------------------------------
    # Decoder 2
    # --------------------------------------------------------

    u2 = layers.Conv2DTranspose(
        64,
        2,
        strides=2,
        padding="same"
    )(c5)

    u2 = layers.Concatenate()(
        [
            u2,
            c2
        ]
    )

    c6 = conv_block(
        u2,
        64
    )


    # --------------------------------------------------------
    # Decoder 3
    # --------------------------------------------------------

    u1 = layers.Conv2DTranspose(
        32,
        2,
        strides=2,
        padding="same"
    )(c6)

    u1 = layers.Concatenate()(
        [
            u1,
            c1
        ]
    )

    c7 = conv_block(
        u1,
        32
    )


    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    outputs = layers.Conv2D(
        1,
        1,
        activation="sigmoid",
        name="disease_mask"
    )(c7)


    model = Model(
        inputs=inputs,
        outputs=outputs,
        name="PlantSeg_U-Net"
    )


    return model


# ============================================================
# COMMAND LINE
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Train PlantSeg U-Net disease segmentation model"
    )


    parser.add_argument(
        "--epochs",
        type=int,
        default=20
    )


    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE
    )


    parser.add_argument(
        "--quick-train",
        action="store_true"
    )


    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_arguments()


    print("=" * 70)
    print("PLANTSEG U-NET TRAINING")
    print("=" * 70)

    print(
        f"TensorFlow: {tf.__version__}"
    )

    print(
        f"Num GPUs: {len(tf.config.list_physical_devices('GPU'))}"
    )


    # --------------------------------------------------------
    # Check directories
    # --------------------------------------------------------

    required_directories = [
        TRAIN_IMAGE_DIR,
        TRAIN_MASK_DIR,
        TEST_IMAGE_DIR,
        TEST_MASK_DIR
    ]


    for directory in required_directories:

        if not os.path.exists(directory):

            raise FileNotFoundError(
                f"Directory not found:\n{directory}"
            )


    # --------------------------------------------------------
    # Build training pairs
    # --------------------------------------------------------

    train_pairs = build_image_mask_pairs(
        TRAIN_IMAGE_DIR,
        TRAIN_MASK_DIR
    )


    # --------------------------------------------------------
    # Build test pairs
    # --------------------------------------------------------

    test_pairs = build_image_mask_pairs(
        TEST_IMAGE_DIR,
        TEST_MASK_DIR
    )


    print(
        f"\nTraining pairs: {len(train_pairs)}"
    )

    print(
        f"Testing pairs: {len(test_pairs)}"
    )


    if len(train_pairs) == 0:

        raise ValueError(
            "No training image-mask pairs found."
        )


    if len(test_pairs) == 0:

        raise ValueError(
            "No testing image-mask pairs found."
        )


    # --------------------------------------------------------
    # Shuffle training pairs
    # --------------------------------------------------------

    random.Random(
        SEED
    ).shuffle(
        train_pairs
    )


    # --------------------------------------------------------
    # Train / validation split
    # --------------------------------------------------------

    validation_count = max(
        1,
        int(
            len(train_pairs)
            * VALIDATION_SPLIT
        )
    )


    validation_pairs = train_pairs[
        :validation_count
    ]

    actual_train_pairs = train_pairs[
        validation_count:
    ]


    # --------------------------------------------------------
    # Quick training mode
    # --------------------------------------------------------

    if args.quick_train:

        print("\nQUICK TRAINING MODE")

        QUICK_TRAIN_SIZE = min(
            160,
            len(actual_train_pairs)
        )

        QUICK_VAL_SIZE = min(
            40,
            len(validation_pairs)
        )

        QUICK_TEST_SIZE = min(
            40,
            len(test_pairs)
        )


        actual_train_pairs = actual_train_pairs[
            :QUICK_TRAIN_SIZE
        ]

        validation_pairs = validation_pairs[
            :QUICK_VAL_SIZE
        ]

        evaluation_test_pairs = test_pairs[
            :QUICK_TEST_SIZE
        ]


        print(
            f"Train: {len(actual_train_pairs)}"
        )

        print(
            f"Validation: {len(validation_pairs)}"
        )

        print(
            f"Test: {len(evaluation_test_pairs)}"
        )

    else:

        evaluation_test_pairs = test_pairs


    print("\nFinal split:")

    print(
        f"Train: {len(actual_train_pairs)}"
    )

    print(
        f"Validation: {len(validation_pairs)}"
    )

    print(
        f"Test: {len(evaluation_test_pairs)}"
    )


    # --------------------------------------------------------
    # Create datasets
    # --------------------------------------------------------

    train_dataset = create_dataset(
        actual_train_pairs,
        args.batch_size,
        training=True
    )


    validation_dataset = create_dataset(
        validation_pairs,
        args.batch_size,
        training=False
    )


    test_dataset = create_dataset(
        evaluation_test_pairs,
        args.batch_size,
        training=False
    )


    # --------------------------------------------------------
    # Dataset sanity check
    # --------------------------------------------------------

    dataset_sanity_check(
        validation_dataset
    )


    # --------------------------------------------------------
    # Build model
    # --------------------------------------------------------

    model = build_unet()


    model.summary()


    # --------------------------------------------------------
    # Compile model
    # --------------------------------------------------------

    optimizer = tf.keras.optimizers.Adam(
        learning_rate=INITIAL_LEARNING_RATE
    )


    model.compile(
        optimizer=optimizer,
        loss=combined_loss,
        metrics=[
            dice_coefficient,
            iou_coefficient,
            precision_metric,
            recall_metric
        ]
    )


    # --------------------------------------------------------
    # Callbacks
    # --------------------------------------------------------

    callbacks = [

        ModelCheckpoint(
            MODEL_PATH,
            monitor="val_dice_coefficient",
            mode="max",
            save_best_only=True,
            verbose=1
        ),

        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        ),

        EarlyStopping(
            monitor="val_dice_coefficient",
            mode="max",
            patience=6,
            restore_best_weights=True,
            verbose=1
        )
    ]


    # --------------------------------------------------------
    # Training
    # --------------------------------------------------------

    print("\nStarting training...\n")


    history = model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=args.epochs,
        callbacks=callbacks
    )


    # --------------------------------------------------------
    # Save final model
    # --------------------------------------------------------

    model.save(
        MODEL_PATH
    )


    print("\n" + "=" * 70)
    print("MODEL SAVED")
    print("=" * 70)

    print(
        MODEL_PATH
    )


    # --------------------------------------------------------
    # Test evaluation
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL TEST EVALUATION")
    print("=" * 70)


    results = model.evaluate(
        test_dataset,
        verbose=1,
        return_dict=True
    )


    print("\nTest results:")

    for name, value in results.items():

        print(
            f"{name}: {value:.6f}"
        )


    # --------------------------------------------------------
    # Save training history
    # --------------------------------------------------------

    history_path = os.path.join(
        MODEL_DIR,
        "training_history.json"
    )


    history_data = {
        key: [
            float(v)
            for v in values
        ]
        for key, values
        in history.history.items()
    }


    with open(
        history_path,
        "w"
    ) as f:

        json.dump(
            history_data,
            f,
            indent=2
        )


    print(
        f"\nTraining history saved to:"
    )

    print(
        history_path
    )


    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()