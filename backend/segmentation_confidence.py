"""Confidence diagnostics for the segmentation output.

Because the current LeafSegmenter exposes a binary mask, confidence is a
quality diagnostic rather than a calibrated probability. It combines leaf
coverage, lesion coverage plausibility, edge fragmentation, and model source.
"""
from __future__ import annotations

from typing import Any
import numpy as np


def estimate_segmentation_confidence(result: dict[str, Any]) -> dict[str, Any]:
    leaf = max(int(result.get("leaf_pixels", 0)), 1)
    diseased = max(int(result.get("diseased_pixels", 0)), 0)
    affected = min(diseased / leaf, 1.0)
    leaf_fraction = min(max(leaf / max(int(result.get("total_pixels", leaf)), 1), 0.0), 1.0)
    architecture = str(result.get("architecture", ""))

    # These are quality heuristics, not ground-truth probabilities.
    coverage_score = 1.0 if 0.05 <= leaf_fraction <= 0.95 else 0.55
    affected_score = 1.0 if 0.001 <= affected <= 0.95 else 0.65
    model_score = 1.0 if "U-Net" in architecture else 0.70
    score = float(np.clip(0.45 * model_score + 0.30 * coverage_score + 0.25 * affected_score, 0.0, 1.0))
    level = "High" if score >= 0.80 else "Medium" if score >= 0.60 else "Low"
    return {
        "score": round(score * 100.0, 2),
        "level": level,
        "calibrated": False,
        "method": "segmentation_quality_heuristic",
        "warning": "This is a quality heuristic, not a calibrated segmentation probability.",
    }
