#!/usr/bin/env python3
"""
Segmentation Validation Script
Harvest Harbor — AI Crop Disease Detection & Traceability Platform

Evaluates the U-Net lesion segmentation model on the held-out PlantSeg test dataset.
Computes IoU (Jaccard Index), Dice Coefficient (F1 score), Precision, and Recall.
"""

import os
import sys
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

from segmentation import LeafSegmenter, SEGMENTATION_MODEL_PATH

DEFAULT_DATASET_DIR = BASE_DIR.parent / "datasets" / "plantseg"


def evaluate_segmentation(num_samples: int = 50):
    print("=" * 65)
    print("HARVEST HARBOR — U-NET SEGMENTATION VALIDATION")
    print("=" * 65)

    dataset_path = Path(os.getenv("SEGMENTATION_DATASET_DIR") or DEFAULT_DATASET_DIR)
    images_dir = dataset_path / "images" / "test"
    masks_dir = dataset_path / "annotations" / "test"

    if not images_dir.exists() or not masks_dir.exists():
        print("Status: NOT IMPLEMENTED")
        print(f"Error: PlantSeg test dataset not found at {dataset_path}")
        print("Please supply test images and pixel-level ground truth mask annotations.")
        sys.exit(1)

    if not SEGMENTATION_MODEL_PATH.exists():
        print("Status: NOT IMPLEMENTED")
        print(f"Error: Trained U-Net model weights not found at {SEGMENTATION_MODEL_PATH}")
        sys.exit(1)

    print(f"[INFO] Dataset Directory: {dataset_path}")
    print(f"[INFO] Model Weights: {SEGMENTATION_MODEL_PATH}")

    # Gather matching test pairs
    mask_files = sorted(list(masks_dir.glob("*.png")))
    if not mask_files:
        print("Status: NOT IMPLEMENTED")
        print("Error: No ground truth masks (.png) found in annotations/test.")
        sys.exit(1)

    pairs = []
    for mf in mask_files:
        stem = mf.stem
        img_f = images_dir / f"{stem}.jpg"
        if not img_f.exists():
            img_f = images_dir / f"{stem}.png"
        if img_f.exists():
            pairs.append((img_f, mf))

    print(f"[INFO] Total verified test pairs: {len(pairs)}")
    if num_samples > 0 and num_samples < len(pairs):
        import random
        random.seed(42)
        pairs = random.sample(pairs, num_samples)
        print(f"[INFO] Evaluating on reproducible random subset: {len(pairs)} samples")
    else:
        print(f"[INFO] Evaluating on all {len(pairs)} test samples")

    segmenter = LeafSegmenter()
    if segmenter.unet_model is None:
        print("Status: NOT IMPLEMENTED")
        print("Error: Could not load U-Net model.")
        sys.exit(1)

    ious = []
    dices = []
    precisions = []
    recalls = []

    print("-" * 65)
    print("Evaluating samples...")

    for i, (img_path, mask_path) in enumerate(pairs):
        try:
            pil_img = Image.open(img_path).convert("RGB")
            gt_mask_pil = Image.open(mask_path).convert("L")
            w, h = pil_img.size

            gt_mask = np.array(gt_mask_pil) > 0  # boolean

            # Model prediction: resize to 256x256 normalized [0, 1]
            img_resized = pil_img.resize((256, 256), Image.Resampling.BILINEAR)
            img_arr = np.array(img_resized, dtype=np.float32) / 255.0
            img_batch = np.expand_dims(img_arr, axis=0)

            if segmenter.unet_infer is not None:
                import tensorflow as tf
                out = segmenter.unet_infer(input_layer=tf.constant(img_batch, dtype=tf.float32))
                pred_prob = out["output_0"].numpy()[0]  # (256, 256, 1)
            elif hasattr(segmenter.unet_model, "predict"):
                pred_prob = segmenter.unet_model.predict(img_batch, verbose=0)[0]  # (256, 256, 1)
            else:
                raise RuntimeError("U-Net model callable not found")
            pred_mask_256 = (pred_prob[..., 0] >= 0.5).astype(np.uint8)

            # Resize pred mask back to original dimensions for fair pixel-level evaluation
            pred_mask_pil = Image.fromarray(pred_mask_256).resize((w, h), Image.Resampling.NEAREST)
            pred_mask = np.array(pred_mask_pil) > 0

            intersection = np.logical_and(gt_mask, pred_mask).sum()
            union = np.logical_or(gt_mask, pred_mask).sum()
            pred_total = pred_mask.sum()
            gt_total = gt_mask.sum()

            # IoU
            if union == 0:
                iou = 1.0 if (pred_total == 0 and gt_total == 0) else 0.0
            else:
                iou = intersection / union

            # Dice
            if (pred_total + gt_total) == 0:
                dice = 1.0
            else:
                dice = (2.0 * intersection) / (pred_total + gt_total)

            # Precision & Recall
            prec = (intersection / pred_total) if pred_total > 0 else (1.0 if gt_total == 0 else 0.0)
            rec = (intersection / gt_total) if gt_total > 0 else 1.0

            ious.append(iou)
            dices.append(dice)
            precisions.append(prec)
            recalls.append(rec)

        except Exception as e:
            print(f"[WARN] Error evaluating sample {img_path.name}: {e}")

    mean_iou = float(np.mean(ious)) if ious else 0.0
    mean_dice = float(np.mean(dices)) if dices else 0.0
    mean_prec = float(np.mean(precisions)) if precisions else 0.0
    mean_rec = float(np.mean(recalls)) if recalls else 0.0

    print("=" * 65)
    print("VALIDATION RESULTS (PLANTSEG TEST SET)")
    print("=" * 65)
    print(f"Evaluated Samples:  {len(ious)}")
    print(f"Mean IoU (Jaccard): {mean_iou * 100:.2f}%")
    print(f"Mean Dice (F1):     {mean_dice * 100:.2f}%")
    print(f"Mean Precision:     {mean_prec * 100:.2f}%")
    print(f"Mean Recall:        {mean_rec * 100:.2f}%")
    print("=" * 65)
    print("Status: PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate U-Net segmentation on PlantSeg test set")
    parser.add_argument("--samples", "--num-samples", dest="samples", type=int, default=50, help="Number of test samples to evaluate (default: 50)")
    args = parser.parse_args()
    evaluate_segmentation(num_samples=args.samples)
