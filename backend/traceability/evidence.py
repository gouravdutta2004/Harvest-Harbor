from typing import Any, Dict, Optional


def create_evidence_record(
    *,
    report_id: str,
    timestamp: str,
    image_sha256: str,
    health_prediction: Optional[str],
    health_confidence: Optional[float],
    disease_prediction: Optional[str],
    disease_confidence: Optional[float],
    disease_uncertainty: Optional[str],
    disease_class_idx: Optional[int],
    severity: Optional[str],
    affected_area_percent: Optional[float],
    model_versions: Dict[str, Any],
    top_3: Optional[list] = None,
    report_snapshot: Optional[Dict[str, Any]] = None,
    actor: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create the canonical evidence payload stored in the tamper-evident chain.

    report_snapshot is the complete diagnostic response needed to reconstruct a
    historical report without rerunning the models.
    """
    snapshot = dict(report_snapshot) if isinstance(report_snapshot, dict) else None
    
    crop_model_info = model_versions.get("crop")
    if not isinstance(crop_model_info, dict) and not crop_model_info:
        crop_model_info = {"available": False, "method": "disease_class_name_mapping"}

    return {
        "report_id": report_id,
        "timestamp": timestamp,
        "image_sha256": image_sha256,
        "health": {
            "prediction": health_prediction,
            "confidence": health_confidence,
        },
        "disease": {
            "prediction": disease_prediction,
            "confidence": disease_confidence,
            "uncertainty": disease_uncertainty,
            "class_idx": disease_class_idx,
            "top_3": top_3 or [],
        },
        "severity": {
            "severity": severity,
            "affected_area_percent": affected_area_percent,
        },
        "models": {
            "system": model_versions.get("system"),
            "health": model_versions.get("health"),
            "disease": model_versions.get("disease"),
            "crop": crop_model_info,
            "segmentation": model_versions.get("segmentation"),
        },
        "actor": actor or {},
        "report_snapshot": snapshot,
    }
