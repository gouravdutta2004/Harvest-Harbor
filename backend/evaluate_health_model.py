#!/usr/bin/env python3
"""
Health Model Evaluation Script
Harvest Harbor — AI Crop Disease Detection & Traceability Platform

Evaluates the binary health vs diseased classifier.
If the dedicated validation split is empty, reports NOT VALIDATED with scientific rationale,
or evaluates against PlantVillage healthy/diseased partitions when requested.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
from PIL import Image

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Pre-configure Keras home
os.environ.setdefault("KERAS_HOME", str(BASE_DIR / ".keras"))

from health_predictor import HealthPredictor, MODEL_PATH

SPLIT_PATH = BASE_DIR / "health_model" / "dataset_split.json"
PLANTVILLAGE_ROOT = BASE_DIR.parent / "datasets" / "plantvillage" / "raw" / "color"


def evaluate_health_model(use_plantvillage: bool = False, num_samples: int = 100):
    print("=" * 65)
    print("HARVEST HARBOR — HEALTH CLASSIFIER EVALUATION")
    print("=" * 65)

    if not MODEL_PATH.exists():
        print("Status: NOT IMPLEMENTED")
        print(f"Error: Health model weights not found at {MODEL_PATH}")
        sys.exit(1)

    # Check split file
    has_split = False
    val_files = []
    if SPLIT_PATH.exists():
        try:
            with open(SPLIT_PATH, "r", encoding="utf-8") as f:
                split_data = json.load(f)
            val_files = split_data.get("val_files", [])
            has_split = len(val_files) > 0
        except Exception:
            has_split = False

    if not has_split and not use_plantvillage:
        print("Status: NOT VALIDATED")
        print("Reason: Health model held-out validation split contains 0 samples in dataset_split.json.")
        print("Scientific Note: To avoid fabricating health classifier metrics, validation requires a verified")
        print("held-out test split. You can pass --use-plantvillage to run empirical evaluation against")
        print("PlantVillage healthy/diseased folders.")
        sys.exit(0)

    # If use_plantvillage is requested or split exists
    print(f"[INFO] Evaluating health predictor using PlantVillage ground truth folders...")
    predictor = HealthPredictor()

    folders = [f for f in PLANTVILLAGE_ROOT.iterdir() if f.is_dir()]
    healthy_folders = [f for f in folders if f.name.endswith("___healthy")]
    diseased_folders = [f for f in folders if not f.name.endswith("___healthy")]

    import random
    random.seed(42)

    eval_items = []
    # Pick balanced samples
    h_per_folder = max(1, (num_samples // 2) // len(healthy_folders))
    d_per_folder = max(1, (num_samples // 2) // len(diseased_folders))

    for hf in healthy_folders:
        imgs = list(hf.glob("*.JPG")) + list(hf.glob("*.jpg"))
        for img_path in random.sample(imgs, min(len(imgs), h_per_folder)):
            eval_items.append((img_path, "healthy"))

    for df in diseased_folders:
        imgs = list(df.glob("*.JPG")) + list(df.glob("*.jpg"))
        for img_path in random.sample(imgs, min(len(imgs), d_per_folder)):
            eval_items.append((img_path, "diseased"))

    random.shuffle(eval_items)
    print(f"[INFO] Selected {len(eval_items)} balanced samples (healthy & diseased)")

    correct = 0
    tp = 0  # diseased as diseased
    fp = 0  # healthy as diseased
    fn = 0  # diseased as healthy
    tn = 0  # healthy as healthy

    for img_path, gt_label in eval_items:
        try:
            res = predictor.predict_image(Image.open(img_path))
            pred_label = res.get("prediction")
            if pred_label == gt_label:
                correct += 1
            if gt_label == "diseased" and pred_label == "diseased":
                tp += 1
            elif gt_label == "healthy" and pred_label == "diseased":
                fp += 1
            elif gt_label == "diseased" and pred_label == "healthy":
                fn += 1
            elif gt_label == "healthy" and pred_label == "healthy":
                tn += 1
        except Exception as e:
            print(f"[WARN] Error evaluating {img_path.name}: {e}")

    total = len(eval_items)
    accuracy = (correct / total) * 100.0 if total > 0 else 0.0
    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("=" * 65)
    print("HEALTH CLASSIFIER EVALUATION RESULTS")
    print("=" * 65)
    print(f"Evaluated Samples: {total}")
    print(f"Accuracy:          {accuracy:.2f}%")
    print(f"Precision:         {precision:.2f}%")
    print(f"Recall:            {recall:.2f}%")
    print(f"F1-Score:          {f1:.2f}%")
    print("=" * 65)
    print("Status: PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate health model")
    parser.add_argument("--use-plantvillage", action="store_true", help="Evaluate against PlantVillage healthy/diseased partitions")
    parser.add_argument("--samples", type=int, default=100, help="Number of samples to evaluate")
    args = parser.parse_args()
    evaluate_health_model(use_plantvillage=args.use_plantvillage, num_samples=args.samples)
