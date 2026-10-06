"""
Utility functions for Crop Disease AI backend.
Includes crop extraction, uncertainty assessment, and directory helpers.
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import Tuple, Optional

# Ensure both backend and root directories are in sys.path
_BASE_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _BASE_DIR.parent
for directory in (str(_ROOT_DIR), str(_BASE_DIR)):
    if directory not in sys.path:
        sys.path.insert(0, directory)

try:
    from backend.config import (
        UPLOADS_DIR,
        GRADCAM_DIR,
        SEGMENTATION_DIR,
        SEGMENTATION_MODEL_DIR,
        MAX_GENERATED_FILE_AGE_HOURS,
    )
except ImportError:
    from config import (
        UPLOADS_DIR,
        GRADCAM_DIR,
        SEGMENTATION_DIR,
        SEGMENTATION_MODEL_DIR,
        MAX_GENERATED_FILE_AGE_HOURS,
    )

logger = logging.getLogger(__name__)

# Known crops present in PlantWild v2 dataset, ordered by length descending
# to ensure multi-word crop names (e.g. 'bell pepper') match first.
KNOWN_CROPS = [
    "bell pepper",
    "grapevine",
    "apple",
    "banana",
    "basil",
    "bean",
    "blueberry",
    "broccoli",
    "cabbage",
    "carrot",
    "cauliflower",
    "celery",
    "cherry",
    "citrus",
    "coffee",
    "corn",
    "cucumber",
    "eggplant",
    "garlic",
    "ginger",
    "grape",
    "lettuce",
    "maple",
    "peach",
    "plum",
    "potato",
    "raspberry",
    "rice",
    "soybean",
    "squash",
    "strawberry",
    "tobacco",
    "tomato",
    "wheat",
    "zucchini",
]


def extract_crop_and_disease(raw_prediction: str) -> Tuple[Optional[str], str]:
    """
    Extract crop and disease components from a raw PlantWild class label.
    Preserves exact label string while attempting logical crop extraction.

    Returns:
        (crop, disease) tuple. If ambiguous, crop is None and disease is raw_prediction.
    """
    raw_clean = raw_prediction.strip()
    # Normalize underscores and extra spaces for matching
    raw_normalized = " ".join(raw_clean.lower().replace("_", " ").split())

    for crop in KNOWN_CROPS:
        if raw_normalized == crop or raw_normalized.startswith(crop + " "):
            disease = raw_clean[len(crop):].strip(" _-")
            if not disease:
                disease = "Healthy" if "healthy" in raw_normalized else "disease"
            return crop, disease

    return None, raw_clean



def calculate_uncertainty(score: float) -> str:
    """
    Determine uncertainty level based on model softmax score (percentage).

    >= 85.0% -> Low
    60.0% - 84.99% -> Medium
    < 60.0% -> High
    """
    if score >= 85.0:
        return "Low"
    elif score >= 60.0:
        return "Medium"
    else:
        return "High"


def ensure_directories_exist() -> None:
    """Ensure runtime upload, segmentation model, and generated output directories exist."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(GRADCAM_DIR, exist_ok=True)
    os.makedirs(SEGMENTATION_DIR, exist_ok=True)
    os.makedirs(SEGMENTATION_MODEL_DIR, exist_ok=True)


def cleanup_expired_files(max_age_hours: int = MAX_GENERATED_FILE_AGE_HOURS) -> int:
    """
    Delete files in GRADCAM_DIR, SEGMENTATION_DIR, and UPLOADS_DIR older than max_age_hours.
    Returns the total number of deleted files.
    """
    ensure_directories_exist()
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0

    for target_dir in (GRADCAM_DIR, SEGMENTATION_DIR, UPLOADS_DIR):
        if not target_dir.exists():
            continue
        for file_path in target_dir.iterdir():
            if file_path.is_file():
                try:
                    file_age = now - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                except Exception as err:
                    logger.warning(f"Failed to remove expired file {file_path}: {err}")

    # Also clean up stale .lock files from all scanned directories (only if expired)
    for target_dir in (GRADCAM_DIR, SEGMENTATION_DIR, UPLOADS_DIR):
        if not target_dir.exists():
            continue
        for file_path in target_dir.glob("*.lock"):
            if file_path.is_file():
                try:
                    file_age = now - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                except Exception as err:
                    logger.warning(f"Failed to remove stale lock file {file_path}: {err}")


    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired output/upload files.")

    return deleted_count


def compute_file_sha256(file_path: str) -> Optional[str]:
    import hashlib
    try:
        path = Path(file_path)
        if not path.is_file():
            return None
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

