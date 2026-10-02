"""Fit health-model temperature scaling on the exact saved validation split without data leakage.

This script does NOT retrain the classifier or generate a new random split.
It reads backend/health_model/dataset_split.json (saved during training by train_health_classifier.py)
to obtain the exact held-out validation samples, and computes calibration metadata stored in
backend/health_model/calibration.json.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Pre-configure Keras home before importing TensorFlow
_BACKEND_DIR = Path(__file__).resolve().parent
os.environ.setdefault("KERAS_HOME", str(_BACKEND_DIR / ".keras"))

import numpy as np
import tensorflow as tf
from calibration import TemperatureScaler

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path(__file__).resolve().parent / "health_model"
SPLIT_PATH = MODEL_DIR / "dataset_split.json"
MODEL_PATH = MODEL_DIR / "health_disease_efficientnetb0.keras"
OUT_PATH = MODEL_DIR / "calibration.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split-file", type=Path, default=SPLIT_PATH)
    ap.add_argument("--max-samples", type=int, default=200, help="Maximum number of validation samples to evaluate")
    args = ap.parse_args()

    split_file = args.split_file
    if not split_file.exists():
        print(f"[WARNING] Dataset split file not found at {split_file}.")
        print("Calibration requires the exact validation split from train_health_classifier.py.")
        print("HealthPredictor will correctly report calibration_status: 'not_calibrated'.")
        return

    if not MODEL_PATH.exists():
        print(f"[WARNING] Health model file not found at {MODEL_PATH}. Cannot calibrate.")
        return

    try:
        split_data = json.loads(split_file.read_text(encoding="utf-8"))
        val_files = split_data.get("val_files", [])
        val_labels = split_data.get("val_labels", [])
    except Exception as exc:
        print(f"[WARNING] Failed to parse {split_file}: {exc}")
        return

    if not val_files or not val_labels:
        print("[WARNING] Validation split data is empty. Skipping calibration generation.")
        return

    # Filter files that physically exist on disk
    valid_pairs = []
    for path_str, label in zip(val_files, val_labels):
        p = Path(path_str)
        if p.exists():
            valid_pairs.append((str(p), int(label)))

    if not valid_pairs:
        print("[WARNING] None of the saved validation files were found on disk. Skipping calibration.")
        return

    if args.max_samples and len(valid_pairs) > args.max_samples:
        import random
        rng = random.Random(42)
        valid_pairs = rng.sample(valid_pairs, args.max_samples)

    print(f"Loading {len(valid_pairs)} held-out validation samples from dataset_split.json...")

    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    probs = []
    labels = []
    for i in range(0, len(valid_pairs), 64):
        batch = valid_pairs[i : i + 64]
        images = []
        for path, label in batch:
            raw = tf.io.read_file(path)
            img = tf.image.decode_image(raw, channels=3, expand_animations=False)
            img = tf.image.resize(img, (224, 224))
            images.append(img)
            labels.append(label)
        arr = tf.stack(images)
        out = np.asarray(model.predict(arr, verbose=0)).reshape(-1)
        probs.extend(out.tolist())

    scaler = TemperatureScaler()
    stats = scaler.fit(labels, probs)
    metadata = {
        "method": "temperature_scaling",
        "temperature": round(float(stats.get("temperature", 1.0)), 4),
        "calibration_dataset_description": f"Saved validation split from dataset_split.json ({len(valid_pairs)} images)",
        "number_of_samples": len(valid_pairs),
        "calibration_timestamp": datetime.now(timezone.utc).isoformat(),
        "model_version": "health_disease_efficientnetb0",
        **stats,
    }
    scaler.save(OUT_PATH, metadata)
    print(json.dumps(metadata, indent=2))
    print("Saved calibration metadata to", OUT_PATH)


if __name__ == "__main__":
    main()
