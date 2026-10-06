"""Crop identification and crop-aware disease compatibility helpers."""

from typing import Any, Dict, List, Optional


CROP_ALIASES = [
    ("bell pepper", "Bell Pepper"),
    ("cherry", "Cherry"),
    ("corn", "Corn"),
    ("grapevine", "Grape"),
    ("grape", "Grape"),
    ("peach", "Peach"),
    ("pepper", "Pepper"),
    ("potato", "Potato"),
    ("raspberry", "Raspberry"),
    ("soybean", "Soybean"),
    ("squash", "Squash"),
    ("strawberry", "Strawberry"),
    ("tomato", "Tomato"),
    ("apple", "Apple"),
    ("banana", "Banana"),
    ("basil", "Basil"),
    ("bean", "Bean"),
    ("blueberry", "Blueberry"),
    ("cassava", "Cassava"),
    ("cucumber", "Cucumber"),
    ("cotton", "Cotton"),
    ("ginger", "Ginger"),
    ("guava", "Guava"),
    ("lemon", "Lemon"),
    ("mango", "Mango"),
    ("orange", "Orange"),
    ("citrus", "Orange"),
    ("papaya", "Papaya"),
    ("rice", "Rice"),
    ("sugarcane", "Sugarcane"),
    ("wheat", "Wheat"),
]


def normalize_crop_name(crop: Optional[str]) -> Optional[str]:
    if not crop:
        return None

    text = str(crop).strip().lower()

    aliases = {
        "pepper, bell": "Bell Pepper",
        "bell pepper": "Bell Pepper",
        "pepper": "Pepper",
        "corn (maize)": "Corn",
        "cherry (including sour)": "Cherry",
        "grapevine": "Grape",
        "grape": "Grape",
    }

    if text in aliases:
        return aliases[text]

    for alias, label in CROP_ALIASES:
        if text == alias:
            return label

    return str(crop).strip()


def identify_crop_from_disease_class(
    class_name: Optional[str],
) -> Optional[str]:

    if not class_name:
        return None

    text = str(class_name).strip().lower()

    for alias, label in CROP_ALIASES:

        if text == alias or text.startswith(alias + " ") or text.startswith(alias + "_"):
            return label

    return None


def enrich_top3_with_crop(top3: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    result = []

    for item in top3 or []:

        if not isinstance(item, dict):
            continue

        item_copy = dict(item)

        item_copy["crop"] = identify_crop_from_disease_class(
            item_copy.get("class")
        )

        result.append(item_copy)

    return result


def rank_diseases_for_crop(
    class_names: List[str],
    probabilities: Any,
    detected_crop: Optional[str],
    k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Rank disease candidates belonging strictly to the detected crop
    across all available class probabilities (e.g. 115 categories).

    This prevents missing relevant crop diseases that fell outside the global top-3.
    """
    if not detected_crop or probabilities is None or not class_names:
        return []

    target_crop = normalize_crop_name(detected_crop)
    if not target_crop:
        return []

    probs = list(probabilities)
    crop_candidates = []

    for idx, name in enumerate(class_names):
        if idx >= len(probs):
            break
        candidate_crop = identify_crop_from_disease_class(name)
        if candidate_crop and normalize_crop_name(candidate_crop) == target_crop:
            prob = float(probs[idx])
            crop_candidates.append({
                "class": name,
                "class_idx": idx,
                "raw_prob": prob,
                "crop": candidate_crop,
            })

    # Renormalize/report crop-conditioned disease probabilities
    total_crop_prob = sum(c["raw_prob"] for c in crop_candidates)
    
    for c in crop_candidates:
        if total_crop_prob > 0:
            renormalized_prob = c["raw_prob"] / total_crop_prob
        else:
            renormalized_prob = 0.0
            
        c["score"] = round(renormalized_prob * 100.0, 2)
        c["confidence"] = round(renormalized_prob * 100.0, 2)
        c["raw_score"] = round(c["raw_prob"] * 100.0, 2) # preserve raw score
        del c["raw_prob"]

    # Sort descending by probability score
    crop_candidates.sort(key=lambda x: x["confidence"], reverse=True)

    # Assign ranks to top-k
    result = []
    for rank, item in enumerate(crop_candidates[:k], start=1):
        item_copy = dict(item)
        item_copy["rank"] = rank
        result.append(item_copy)

    return result


def filter_top3_by_crop(
    top3: List[Dict[str, Any]],
    detected_crop: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Filter given top3 list by detected crop.
    """
    if not detected_crop:
        return []

    target_crop = normalize_crop_name(detected_crop)
    compatible = []

    for item in top3 or []:
        if not isinstance(item, dict):
            continue

        item_crop = normalize_crop_name(item.get("crop"))
        if item_crop == target_crop:
            compatible.append(dict(item))

    return compatible