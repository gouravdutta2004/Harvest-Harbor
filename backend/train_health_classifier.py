from pathlib import Path
import json
import math
import shutil

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import EfficientNetB0
from sklearn.model_selection import train_test_split


# ============================================================
# CONFIG
# ============================================================

DATASET_DIR = Path("datasets/plantvillage/raw/color")

MODEL_DIR = Path("backend/health_model")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "health_disease_efficientnetb0.keras"
CLASS_NAMES_PATH = MODEL_DIR / "health_disease_class_names.json"

IMG_SIZE = 224
BATCH_SIZE = 32

INITIAL_EPOCHS = 10
FINE_TUNE_EPOCHS = 10

SEED = 42

AUTOTUNE = tf.data.AUTOTUNE


# ============================================================
# GPU / CPU INFORMATION
# ============================================================

print("=" * 60)
print("Healthy vs Diseased Classifier Training")
print("=" * 60)

print("TensorFlow version:", tf.__version__)

gpus = tf.config.list_physical_devices("GPU")

if gpus:
    print("GPU available:", gpus)
else:
    print("GPU not available. Using CPU.")


# ============================================================
# COLLECT FILES
# ============================================================

print("\nScanning PlantVillage color dataset...")

healthy_files = []
diseased_files = []

valid_extensions = {
    ".jpg",
    ".jpeg",
    ".png",
    ".JPG",
    ".JPEG",
    ".PNG",
}


for class_dir in sorted(DATASET_DIR.iterdir()):

    if not class_dir.is_dir():
        continue

    is_healthy = "___healthy" in class_dir.name.lower()

    files = [
        p for p in class_dir.iterdir()
        if p.is_file() and p.suffix in valid_extensions
    ]

    if is_healthy:
        healthy_files.extend(files)
    else:
        diseased_files.extend(files)


print("Healthy images :", len(healthy_files))
print("Diseased images:", len(diseased_files))
print("Total images   :", len(healthy_files) + len(diseased_files))


# ============================================================
# CREATE BINARY DATASET
# ============================================================

all_files = healthy_files + diseased_files

all_labels = (
    [0] * len(healthy_files) +
    [1] * len(diseased_files)
)

print("\nBinary labels:")
print("0 = Healthy")
print("1 = Diseased")


# ============================================================
# TRAIN / VALIDATION / TEST SPLIT
# ============================================================

# First split:
# 80% train
# 20% temporary

train_files, temp_files, train_labels, temp_labels = train_test_split(
    all_files,
    all_labels,
    test_size=0.20,
    random_state=SEED,
    stratify=all_labels,
)

# Second split:
# temporary -> 10% validation + 10% test

val_files, test_files, val_labels, test_labels = train_test_split(
    temp_files,
    temp_labels,
    test_size=0.50,
    random_state=SEED,
    stratify=temp_labels,
)


print("\nDataset split:")
print("Train      :", len(train_files))
print("Validation :", len(val_files))
print("Test       :", len(test_files))

# Save exact dataset split metadata for reproducible health calibration
split_metadata_path = MODEL_DIR / "dataset_split.json"
try:
    from datetime import datetime, timezone
    split_metadata = {
        "split_date": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "train_count": len(train_files),
        "val_count": len(val_files),
        "test_count": len(test_files),
        "train_files": [str(p) for p in train_files],
        "val_files": [str(p) for p in val_files],
        "test_files": [str(p) for p in test_files],
        "train_labels": [int(l) for l in train_labels],
        "val_labels": [int(l) for l in val_labels],
        "test_labels": [int(l) for l in test_labels],
    }
    with open(split_metadata_path, "w", encoding="utf-8") as f:
        json.dump(split_metadata, f, indent=2, ensure_ascii=False)
    print("Saved dataset split metadata to:", split_metadata_path)
except Exception as exc:
    print("[WARNING] Could not save dataset split metadata:", exc)


# ============================================================
# DATASET CREATION
# ============================================================

def load_image(path, label):

    image = tf.io.read_file(path)

    image = tf.image.decode_image(
        image,
        channels=3,
        expand_animations=False
    )

    image.set_shape([None, None, 3])

    image = tf.image.resize(
        image,
        [IMG_SIZE, IMG_SIZE]
    )

    image = tf.cast(image, tf.float32)

    return image, tf.cast(label, tf.float32)


def create_dataset(files, labels, training=False):

    file_strings = [
        str(p)
        for p in files
    ]

    ds = tf.data.Dataset.from_tensor_slices(
        (file_strings, labels)
    )

    if training:
        ds = ds.shuffle(
            buffer_size=len(file_strings),
            seed=SEED,
            reshuffle_each_iteration=True
        )

    ds = ds.map(
        load_image,
        num_parallel_calls=AUTOTUNE
    )

    ds = ds.batch(BATCH_SIZE)

    ds = ds.prefetch(AUTOTUNE)

    return ds


train_ds = create_dataset(
    train_files,
    train_labels,
    training=True
)

val_ds = create_dataset(
    val_files,
    val_labels
)

test_ds = create_dataset(
    test_files,
    test_labels
)


# ============================================================
# DATA AUGMENTATION
# ============================================================

data_augmentation = keras.Sequential(
    [
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.08),
        layers.RandomZoom(0.15),
        layers.RandomContrast(0.10),
    ],
    name="data_augmentation"
)


# ============================================================
# MODEL
# ============================================================

print("\nBuilding EfficientNetB0...")


base_model = EfficientNetB0(
    include_top=False,
    weights="imagenet",
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)

base_model.trainable = False


inputs = keras.Input(
    shape=(IMG_SIZE, IMG_SIZE, 3),
    name="image"
)

x = data_augmentation(inputs)

x = base_model(
    x,
    training=False
)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dropout(0.30)(x)

outputs = layers.Dense(
    1,
    activation="sigmoid",
    name="health_probability"
)(x)


model = keras.Model(
    inputs,
    outputs,
    name="health_disease_efficientnetb0"
)


# ============================================================
# CLASS WEIGHTS
# ============================================================

healthy_count = len(healthy_files)
diseased_count = len(diseased_files)

total = healthy_count + diseased_count

class_weight = {
    0: total / (2 * healthy_count),
    1: total / (2 * diseased_count),
}

print("\nClass weights:")
print(class_weight)


# ============================================================
# COMPILE
# ============================================================

model.compile(
    optimizer=keras.optimizers.Adam(
        learning_rate=1e-3
    ),
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        keras.metrics.Precision(name="precision"),
        keras.metrics.Recall(name="recall"),
        keras.metrics.AUC(name="auc"),
    ]
)


model.summary()


# ============================================================
# CALLBACKS
# ============================================================

callbacks = [

    keras.callbacks.ModelCheckpoint(
        filepath=str(MODEL_PATH),
        monitor="val_auc",
        mode="max",
        save_best_only=True,
        verbose=1
    ),

    keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=2,
        min_lr=1e-7,
        verbose=1
    ),

    keras.callbacks.EarlyStopping(
        monitor="val_auc",
        mode="max",
        patience=4,
        restore_best_weights=True,
        verbose=1
    ),
]


# ============================================================
# INITIAL TRAINING
# ============================================================

print("\n")
print("=" * 60)
print("PHASE 1 — TRAIN CLASSIFICATION HEAD")
print("=" * 60)

history1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=INITIAL_EPOCHS,
    class_weight=class_weight,
    callbacks=callbacks
)


# ============================================================
# FINE-TUNING
# ============================================================

print("\n")
print("=" * 60)
print("PHASE 2 — FINE-TUNE EFFICIENTNETB0")
print("=" * 60)


base_model.trainable = True


# Freeze most layers.
# Only fine-tune the last ~30 layers.

for layer in base_model.layers[:-30]:
    layer.trainable = False


model.compile(
    optimizer=keras.optimizers.Adam(
        learning_rate=1e-5
    ),
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        keras.metrics.Precision(name="precision"),
        keras.metrics.Recall(name="recall"),
        keras.metrics.AUC(name="auc"),
    ]
)


history2 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=FINE_TUNE_EPOCHS,
    class_weight=class_weight,
    callbacks=callbacks
)


# ============================================================
# LOAD BEST MODEL
# ============================================================

print("\nLoading best saved model...")

best_model = keras.models.load_model(
    MODEL_PATH
)


# ============================================================
# TEST EVALUATION
# ============================================================

print("\n")
print("=" * 60)
print("FINAL TEST EVALUATION")
print("=" * 60)

results = best_model.evaluate(
    test_ds,
    return_dict=True
)

for name, value in results.items():
    print(f"{name:12}: {value:.4f}")


# ============================================================
# SAVE CLASS NAMES
# ============================================================

class_names = {
    "0": "healthy",
    "1": "diseased"
}

with open(
    CLASS_NAMES_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        class_names,
        f,
        indent=2
    )


# ============================================================
# SAVE TRAINING HISTORY
# ============================================================

history = {}

for key, values in history1.history.items():
    history.setdefault(key, []).extend(values)

for key, values in history2.history.items():
    history.setdefault(key, []).extend(values)


history_path = MODEL_DIR / "training_history.json"

with open(
    history_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        history,
        f,
        indent=2
    )


# ============================================================
# FINAL INFORMATION
# ============================================================

print("\n")
print("=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)

print("Model:")
print(MODEL_PATH)

print("\nClass names:")
print(CLASS_NAMES_PATH)

print("\nTraining history:")
print(history_path)

print("\nBinary classification:")
print("0 → Healthy")
print("1 → Diseased")

print("\nNext step:")
print("Integrate this model into backend/app.py")
print("=" * 60)

