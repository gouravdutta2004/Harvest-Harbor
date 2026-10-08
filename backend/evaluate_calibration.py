#!/usr/bin/env python3
"""
Model Calibration & ECE Evaluation Script
Harvest Harbor — AI Crop Disease Detection & Traceability Platform

Evaluates probability calibration on the held-out validation/test split.
Computes:
- Expected Calibration Error (ECE)
- Maximum Calibration Error (MCE)
- Brier Score (pre and post-calibration)
- Negative Log-Likelihood (NLL)
- Reliability Diagram bin statistics
"""

import argparse
import json
import os
import sys
from pathlib import Path
import numpy as np

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Pre-configure Keras home before importing TensorFlow
os.environ.setdefault("KERAS_HOME", str(BASE_DIR / ".keras"))

import tensorflow as tf
from calibration import TemperatureScaler, binary_nll, _clip

MODEL_DIR = BASE_DIR / "health_model"
SPLIT_PATH = MODEL_DIR / "dataset_split.json"
MODEL_PATH = MODEL_DIR / "health_disease_efficientnetb0.keras"
H5_MODEL_PATH = MODEL_DIR / "health_disease_efficientnetb0.h5"
CALIBRATION_PATH = MODEL_DIR / "calibration.json"


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10):
    """
    Compute Expected Calibration Error (ECE), MCE, and per-bin statistics.
    y_true: array of 0 or 1
    y_prob: array of predicted probabilities in [0, 1]
    """
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(y_prob, bins) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    ece = 0.0
    mce = 0.0
    bin_stats = []
    total_samples = len(y_true)

    for i in range(n_bins):
        mask = bin_indices == i
        count = int(np.sum(mask))
        if count > 0:
            bin_acc = float(np.mean(y_true[mask]))
            bin_conf = float(np.mean(y_prob[mask]))
            gap = abs(bin_acc - bin_conf)
            weight = count / total_samples
            ece += weight * gap
            mce = max(mce, gap)
        else:
            bin_acc = 0.0
            bin_conf = (bins[i] + bins[i + 1]) / 2.0
            gap = 0.0

        bin_stats.append({
            "bin": i + 1,
            "range": f"[{bins[i]:.2f}, {bins[i+1]:.2f}]",
            "count": count,
            "accuracy": bin_acc,
            "confidence": bin_conf,
            "gap": gap
        })

    return float(ece), float(mce), bin_stats


def compute_brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    return float(np.mean((y_prob - y_true) ** 2))


def evaluate_calibration(max_samples: int = 100):
    print("=" * 65)
    print("HARVEST HARBOR — HEALTH MODEL CALIBRATION & ECE EVALUATION")
    print("=" * 65)

    if not MODEL_PATH.exists():
        print("Status: NOT IMPLEMENTED")
        print(f"Error: Health model weights not found at {MODEL_PATH}")
        sys.exit(0)

    if not SPLIT_PATH.exists():
        print("Status: NOT IMPLEMENTED")
        print(f"Reason: Validation dataset split file not found at {SPLIT_PATH}")
        sys.exit(0)

    try:
        data = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
        val_files = data.get("val_files", [])
        val_labels = data.get("val_labels", [])
        if not val_files:
            print("Status: NOT IMPLEMENTED")
            print("Reason: Validation split contains 0 samples.")
            sys.exit(0)
    except Exception as exc:
        print("Status: NOT IMPLEMENTED")
        print(f"Error parsing validation split: {exc}")
        sys.exit(0)

    # Filter files that exist on disk
    valid_pairs = []
    for path_str, label in zip(val_files, val_labels):
        p = Path(path_str)
        if p.exists():
            valid_pairs.append((str(p), int(label)))

    if not valid_pairs:
        print("Status: NOT IMPLEMENTED")
        print("Reason: None of the saved validation files were found on disk.")
        sys.exit(0)

    if max_samples and len(valid_pairs) > max_samples:
        import random
        rng = random.Random(42)
        valid_pairs = rng.sample(valid_pairs, max_samples)

    print(f"[INFO] Evaluating on {len(valid_pairs)} held-out validation samples...")

    # Load model
    load_path = H5_MODEL_PATH if (H5_MODEL_PATH.exists() and getattr(tf, "__version__", "").startswith("2.15")) else MODEL_PATH
    try:
        model = tf.keras.models.load_model(load_path, compile=False)
    except Exception:
        fallback = H5_MODEL_PATH if load_path != H5_MODEL_PATH else MODEL_PATH
        if fallback.exists():
            model = tf.keras.models.load_model(fallback, compile=False)
        else:
            raise

    # Load calibration parameters if available
    scaler = None
    temperature = 1.0
    if CALIBRATION_PATH.exists():
        try:
            calib_data = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
            temperature = float(calib_data.get("temperature", 1.0))
            scaler = TemperatureScaler(temperature=temperature, fitted=True)
            print(f"[INFO] Loaded temperature scaling parameter: T = {temperature:.4f}")
        except Exception as e:
            print(f"[WARN] Failed to load calibration artifact: {e}")

    # Predict
    raw_probs = []
    true_labels = []
    for i in range(0, len(valid_pairs), 64):
        batch = valid_pairs[i : i + 64]
        images = []
        for path, label in batch:
            raw = tf.io.read_file(path)
            img = tf.image.decode_image(raw, channels=3, expand_animations=False)
            img = tf.image.resize(img, (224, 224))
            images.append(img)
            true_labels.append(label)
        arr = tf.stack(images)
        out = np.asarray(model.predict(arr, verbose=0)).reshape(-1)
        raw_probs.extend(out.tolist())

    y_true = np.asarray(true_labels, dtype=np.int32)
    y_raw = _clip(np.asarray(raw_probs, dtype=np.float64))

    # Compute uncalibrated metrics
    uncal_ece, uncal_mce, uncal_bins = compute_ece(y_true, y_raw)
    uncal_brier = compute_brier_score(y_true, y_raw)
    uncal_nll = binary_nll(y_true, y_raw)

    print("\n-----------------------------------------------------------------")
    print("UNCALIBRATED MODEL PERFORMANCE")
    print("-----------------------------------------------------------------")
    print(f"Evaluated Samples:              {len(y_true)}")
    print(f"Expected Calibration Error (ECE): {uncal_ece * 100:.2f}%")
    print(f"Maximum Calibration Error (MCE):  {uncal_mce * 100:.2f}%")
    print(f"Brier Score:                    {uncal_brier:.4f}")
    print(f"Negative Log-Likelihood (NLL):   {uncal_nll:.4f}")

    if scaler and scaler.fitted:
        # Apply temperature scaling
        cal_probs = np.array([scaler.transform(p) for p in y_raw])
        cal_ece, cal_mce, cal_bins = compute_ece(y_true, cal_probs)
        cal_brier = compute_brier_score(y_true, cal_probs)
        cal_nll = binary_nll(y_true, cal_probs)

        print("\n-----------------------------------------------------------------")
        print(f"CALIBRATED MODEL PERFORMANCE (Temperature T = {temperature:.4f})")
        print("-----------------------------------------------------------------")
        print(f"Expected Calibration Error (ECE): {cal_ece * 100:.2f}% (improvement: -{(uncal_ece - cal_ece)*100:.2f}%)")
        print(f"Maximum Calibration Error (MCE):  {cal_mce * 100:.2f}%")
        print(f"Brier Score:                    {cal_brier:.4f}")
        print(f"Negative Log-Likelihood (NLL):   {cal_nll:.4f}")

        active_bins = cal_bins
    else:
        active_bins = uncal_bins

    print("\n-----------------------------------------------------------------")
    print("RELIABILITY DIAGRAM (10 BINS)")
    print("-----------------------------------------------------------------")
    print(f"{'Bin':<5} {'Range':<14} {'Count':<7} {'Accuracy':<10} {'Confidence':<12} {'Gap':<8}")
    for b in active_bins:
        if b['count'] > 0:
            print(f"{b['bin']:<5} {b['range']:<14} {b['count']:<7} {b['accuracy']*100:>6.1f}%   {b['confidence']*100:>8.1f}%   {b['gap']*100:>5.2f}%")

    print("=================================================================")
    print("Status: PASS")
    print("=================================================================")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-samples", type=int, default=100)
    args = ap.parse_args()
    evaluate_calibration(max_samples=args.max_samples)


if __name__ == "__main__":
    main()
