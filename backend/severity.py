"""
Severity Estimation Module
--------------------------

Purpose:
    Estimate disease severity from the percentage of leaf area
    covered by the predicted disease/lesion mask.

Important:
    The thresholds below are project-defined initial thresholds.
    They are NOT expert-validated or agronomically standard thresholds.

Pipeline:

    Leaf Mask
        +
    Disease Mask
        ↓
    Diseased Pixels / Leaf Pixels
        ↓
    Affected Area %
        ↓
    Severity Category
"""

from typing import Dict, Any


# ============================================================
# PROJECT THRESHOLDS
# ============================================================

HEALTHY_THRESHOLD = 0.0
EARLY_MAX = 15.0
MODERATE_MAX = 35.0


# ============================================================
# SEVERITY CALCULATION
# ============================================================

def calculate_affected_area(
    diseased_pixels: int,
    leaf_pixels: int
) -> float:
    """
    Calculate percentage of the detected leaf area
    affected by disease.

    Formula:

        affected_area =
            diseased_pixels / leaf_pixels * 100

    Args:
        diseased_pixels:
            Number of pixels predicted as diseased.

        leaf_pixels:
            Number of pixels belonging to the detected leaf.

    Returns:
        Affected area percentage.
    """

    if leaf_pixels <= 0:
        return 0.0

    if diseased_pixels < 0:
        diseased_pixels = 0

    # Disease pixels cannot logically exceed leaf pixels.
    diseased_pixels = min(
        diseased_pixels,
        leaf_pixels
    )

    percentage = (
        diseased_pixels /
        leaf_pixels
    ) * 100.0

    return round(
        percentage,
        2
    )


# ============================================================
# SEVERITY CATEGORY
# ============================================================

def classify_severity(
    affected_area_percent: float
) -> str:
    """
    Convert affected-area percentage into
    the project's initial severity category.

    Thresholds:

        0%              -> Healthy
        >0% and <15%    -> Early
        15% and <35%    -> Moderate
        >=35%           -> Severe

    Returns:
        Severity category.
    """

    if affected_area_percent <= HEALTHY_THRESHOLD:

        return "Healthy"

    elif affected_area_percent < EARLY_MAX:

        return "Early"

    elif affected_area_percent < MODERATE_MAX:

        return "Moderate"

    else:

        return "Severe"


# ============================================================
# SEVERITY DESCRIPTION
# ============================================================

def get_severity_description(
    severity: str
) -> str:
    """
    Return a simple explanation for the
    severity category.
    """

    descriptions = {

        "Healthy":
            "No significant diseased area was detected "
            "by the segmentation model.",

        "Early":
            "A relatively small portion of the detected "
            "leaf area is affected. Field inspection and "
            "disease-specific management should be considered.",

        "Moderate":
            "A moderate portion of the detected leaf area "
            "is affected. Further field inspection and "
            "disease-specific management are recommended.",

        "Severe":
            "A substantial portion of the detected leaf area "
            "is affected. Prompt field inspection and "
            "disease-specific management should be considered."
    }

    return descriptions.get(
        severity,
        "Severity could not be determined."
    )


# ============================================================
# RECOMMENDATIONS
# ============================================================

def get_recommendation(
    severity: str
) -> str:
    """
    Return general project-level guidance.

    These are general recommendations and should not
    replace crop-specific agricultural advice.
    """

    recommendations = {

        "Healthy":
            "No disease area was detected. Continue routine "
            "crop monitoring and maintain appropriate crop "
            "management practices.",

        "Early":
            "Prioritize field inspection and confirm the "
            "predicted disease. Monitor affected plants and "
            "follow disease-specific management guidance.",

        "Moderate":
            "Inspect the affected area carefully and follow "
            "appropriate disease-specific management practices. "
            "Continue monitoring surrounding plants.",

        "Severe":
            "Prioritize field inspection and disease confirmation. "
            "Follow appropriate disease-specific management "
            "guidance and monitor the surrounding crop."
    }

    return recommendations.get(
        severity,
        "Consult an appropriate agricultural expert."
    )


# ============================================================
# COMPLETE SEVERITY ANALYSIS
# ============================================================

def analyze_severity(
    diseased_pixels: int,
    leaf_pixels: int
) -> Dict[str, Any]:
    """
    Complete severity analysis.

    Example:

        result = analyze_severity(
            diseased_pixels=4539,
            leaf_pixels=59581
        )

    Returns:

        {
            "diseased_pixels": 4539,
            "leaf_pixels": 59581,
            "affected_area_percent": 7.62,
            "severity": "Early",
            ...
        }
    """

    # --------------------------------------------------------
    # Validate inputs
    # --------------------------------------------------------

    if leaf_pixels <= 0:

        return {
            "available": False,
            "error": (
                "Leaf pixel count must be greater than zero."
            )
        }

    if diseased_pixels < 0:

        return {
            "available": False,
            "error": (
                "Diseased pixel count cannot be negative."
            )
        }

    # --------------------------------------------------------
    # Protect against invalid segmentation result
    # --------------------------------------------------------

    if diseased_pixels > leaf_pixels:

        diseased_pixels = leaf_pixels

    # --------------------------------------------------------
    # Calculate affected area
    # --------------------------------------------------------

    affected_area_percent = (
        calculate_affected_area(
            diseased_pixels,
            leaf_pixels
        )
    )

    # --------------------------------------------------------
    # Determine severity
    # --------------------------------------------------------

    severity = classify_severity(
        affected_area_percent
    )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description = get_severity_description(
        severity
    )

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    recommendation = get_recommendation(
        severity
    )

    # --------------------------------------------------------
    # Return complete result
    # --------------------------------------------------------

    return {

        "available": True,

        "diseased_pixels": (
            diseased_pixels
        ),

        "leaf_pixels": (
            leaf_pixels
        ),

        "affected_area_percent": (
            affected_area_percent
        ),

        "severity": severity,
        "severity_level": severity,

        "description": description,

        "recommendation": recommendation,

        "thresholds": {

            "healthy": "0%",

            "early":
                ">0% to <15%",

            "moderate":
                "15% to <35%",

            "severe":
                ">=35%"
        },

        "threshold_type":
            "project_defined_initial_thresholds",

        "calibration_required": True
    }


# ============================================================
# ANALYZE DIRECTLY FROM SEGMENTATION RESULT
# ============================================================

def analyze_segmentation_result(
    segmentation_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Accept the dictionary returned by segmentation.py.

    This allows:

        segmentation.py
                ↓
        severity.py

    without manually passing pixel counts.
    """

    if not segmentation_result:

        return {
            "available": False,
            "error": (
                "Segmentation result is empty."
            )
        }

    if not segmentation_result.get(
        "available",
        False
    ):

        return {
            "available": False,
            "error": (
                "Segmentation result is unavailable."
            )
        }

    diseased_pixels = int(
        segmentation_result.get(
            "diseased_pixels",
            0
        )
    )

    leaf_pixels = int(
        segmentation_result.get(
            "leaf_pixels",
            0
        )
    )

    result = analyze_severity(
        diseased_pixels=diseased_pixels,
        leaf_pixels=leaf_pixels
    )
    if not result.get("available"):
        return result

    affected = float(result.get("affected_area_percent", 0.0))
    boundaries = [0.0, EARLY_MAX, MODERATE_MAX]
    distance = min(abs(affected - b) for b in boundaries)
    result["threshold_margin_percent"] = round(distance, 2)
    result["severity_uncertainty"] = (
        "High" if distance < 2.0 else "Medium" if distance < 5.0 else "Low"
    )
    result["calibration_note"] = (
        "Severity thresholds are project-defined and require agronomic validation. "
        "Threshold margin indicates how close the estimated affected area is to a project threshold."
    )
    return result


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("SEVERITY ESTIMATION TEST")
    print("=" * 60)

    # Your actual segmentation result
    diseased_pixels = 4539
    leaf_pixels = 59581

    result = analyze_severity(
        diseased_pixels=diseased_pixels,
        leaf_pixels=leaf_pixels
    )

    if not result["available"]:

        print(
            f"ERROR: {result['error']}"
        )

        raise SystemExit(1)

    print()
    print(
        f"Diseased pixels    : "
        f"{result['diseased_pixels']}"
    )

    print(
        f"Leaf pixels        : "
        f"{result['leaf_pixels']}"
    )

    print(
        f"Affected area     : "
        f"{result['affected_area_percent']:.2f}%"
    )

    print(
        f"Severity           : "
        f"{result['severity']}"
    )

    print()
    print(
        "Description:"
    )

    print(
        result["description"]
    )

    print()
    print(
        "Recommendation:"
    )

    print(
        result["recommendation"]
    )

    print()
    print(
        f"Threshold type     : "
        f"{result['threshold_type']}"
    )

    print(
        f"Calibration needed : "
        f"{result['calibration_required']}"
    )

    print()
    print("=" * 60)
    print("SEVERITY TEST COMPLETED")
    print("=" * 60)