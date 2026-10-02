#!/usr/bin/env python3
"""
Crop Model Evaluation Script
Harvest Harbor — AI Crop Disease Detection & Traceability Platform

Evaluates the dedicated EfficientNet-B0 crop classifier against the held-out test split
from crop_training_split.json using datasets/plantvillage/raw/color.
Computes Top-1 Accuracy, Top-3 Accuracy, Per-Class Precision, Recall, and F1.
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

from crop_classifier import CropPredictor, MODEL_PATH, CLASS_NAMES_PATH

SPLIT_PATH = BASE_DIR / "crop_model" / "crop_training_split.json"
DATASET_ROOT = BASE_DIR.parent / "datasets" / "plantvillage" / "raw" / "color"


def folder_to_crop(folder_name: str) -> str:
    part = folder_name.split("___")[0]
    if "Cherry" in part:
        return "Cherry (including sour)"
    if "Corn" in part:
        return "Corn (maize)"
    if "Pepper" in part:
        return "Pepper, bell"
    return part.replace("_", " ")


def evaluate_crop_model(num_samples: int = 100):
    print("=" * 65)
    print("HARVEST HARBOR — CROP MODEL TEST EVALUATION")
    print("=" * 65)

    if not MODEL_PATH.exists():
        print("Status: NOT IMPLEMENTED")
        print(f"Error: Crop model weights not found at {MODEL_PATH}")
        sys.exit(1)

    if not SPLIT_PATH.exists():
        print("Status: NOT IMPLEMENTED")
        print(f"Error: Crop dataset split not found at {SPLIT_PATH}")
        sys.exit(1)

    if not DATASET_ROOT.exists():
        print("Status: NOT IMPLEMENTED")
        print(f"Error: PlantVillage dataset not found at {DATASET_ROOT}")
        sys.exit(1)

    with open(SPLIT_PATH, "r", encoding="utf-8") as f:
        split_data = json.load(f)

    test_files = split_data.get("test_files", [])
    classes = split_data.get("classes", [])

    if not test_files:
        print("Status: NOT IMPLEMENTED")
        print("Error: Test split contains 0 files.")
        sys.exit(1)

    print(f"[INFO] Total test files in split: {len(test_files)}")
    print(f"[INFO] Crop classes ({len(classes)}): {classes}")

    if 0 < num_samples < len(test_files):
        import random
        random.seed(42)
        eval_files = random.sample(test_files, num_samples)
        print(f"[INFO] Evaluating on reproducible sample of {len(eval_files)} images")
    else:
        eval_files = test_files
        print(f"[INFO] Evaluating on all {len(eval_files)} images")

    predictor = CropPredictor(model_path=MODEL_PATH, class_names_path=CLASS_NAMES_PATH)

    correct_top1 = 0
    correct_top3 = 0
    total = 0

    class_to_idx = {c: i for i, c in enumerate(classes)}
    y_true = []
    y_pred = []

    for rel_path in eval_files:
        full_path = DATASET_ROOT / rel_path
        if not full_path.exists():
            continue

        folder = rel_path.split("/")[0]
        gt_crop = folder_to_crop(folder)
        if gt_crop not in class_to_idx:
            continue

        try:
            pil_img = Image.open(full_path)
            res = predictor.predict_image(pil_img)
            pred_crop = res.get("prediction")
            top_3_crops = [item["class"] for item in res.get("top_3", [])]

            total += 1
            y_true.append(class_to_idx[gt_crop])
            y_pred.append(class_to_idx.get(pred_crop, -1))

            if pred_crop == gt_crop:
                correct_top1 += 1
            if gt_crop in top_3_crops:
                correct_top3 += 1

        except Exception as e:
            print(f"[WARN] Error evaluating {rel_path}: {e}")

    if total == 0:
        print("Status: NOT IMPLEMENTED")
        print("Error: No images were successfully evaluated.")
        sys.exit(1)

    top1_acc = (correct_top1 / total) * 100.0
    top3_acc = (correct_top3 / total) * 100.0

    # Compute per-class precision, recall, F1
    num_classes = len(classes)
    tp = np.zeros(num_classes)
    fp = np.zeros(num_classes)
    fn = np.zeros(num_classes)

    for yt, yp in zip(y_true, y_pred):
        if yp == yt:
            tp[yt] += 1
        else:
            if yp >= 0:
                fp[yp] += 1
            fn[yt] += 1

    precisions = []
    recalls = []
    f1s = []

    for c in range(num_classes):
        p = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) > 0 else 0.0
        r = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) > 0 else 0.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)

    macro_p = np.mean(precisions) * 100.0
    macro_r = np.mean(recalls) * 100.0
    macro_f1 = np.mean(f1s) * 100.0

    print("=" * 65)
    print("CROP CLASSIFIER EVALUATION RESULTS")
    print("=" * 65)
    print(f"Evaluated Test Samples: {total}")
    print(f"Top-1 Accuracy:         {top1_acc:.2f}%")
    print(f"Top-3 Accuracy:         {top3_acc:.2f}%")
    print(f"Macro Precision:        {macro_p:.2f}%")
    print(f"Macro Recall:           {macro_r:.2f}%")
    print(f"Macro F1-Score:         {macro_f1:.2f}%")
    print("=" * 65)
    print("Status: PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate crop model on test split")
    parser.add_argument("--samples", type=int, default=100, help="Number of test samples to evaluate (default: 100, 0 for all)")
    args = parser.parse_args()
    evaluate_crop_model(num_samples=args.samples)
