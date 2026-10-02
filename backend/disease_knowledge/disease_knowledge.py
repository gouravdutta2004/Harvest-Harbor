import json
from pathlib import Path


# ---------------------------------------------------------
# PATH
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

KNOWLEDGE_FILE = BASE_DIR / "diseases.json"


# ---------------------------------------------------------
# LOAD KNOWLEDGE BASE
# ---------------------------------------------------------

def load_disease_knowledge():
    """
    Load disease information from diseases.json.
    """

    if not KNOWLEDGE_FILE.exists():
        print(
            f"[WARNING] Disease knowledge file not found: "
            f"{KNOWLEDGE_FILE}"
        )
        return {}

    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        print(
            f"[INFO] Disease knowledge base loaded: "
            f"{len(data)} diseases"
        )

        return data

    except json.JSONDecodeError as error:
        print(
            f"[ERROR] Invalid JSON in disease knowledge base: "
            f"{error}"
        )
        return {}

    except Exception as error:
        print(
            f"[ERROR] Failed to load disease knowledge base: "
            f"{error}"
        )
        return {}


DISEASE_KNOWLEDGE = load_disease_knowledge()


# ---------------------------------------------------------
# NORMALIZE DISEASE NAME
# ---------------------------------------------------------

def normalize_disease_name(disease_name):
    """
    Convert model disease names into knowledge-base keys.

    Example:

        potato early blight
        ->
        potato_early_blight
    """

    if not disease_name:
        return ""

    name = str(disease_name).lower().strip()

    # Common separators
    name = name.replace(" ", "_")
    name = name.replace("-", "_")
    name = name.replace("/", "_")

    # Remove duplicate underscores
    while "__" in name:
        name = name.replace("__", "_")

    return name


# ---------------------------------------------------------
# GET RAW DISEASE INFORMATION
# ---------------------------------------------------------

def get_disease_information(disease_name):
    """
    Get disease information from the knowledge base.
    """

    key = normalize_disease_name(disease_name)

    if not key:
        return None

    return DISEASE_KNOWLEDGE.get(key)


# ---------------------------------------------------------
# GET DISEASE SUMMARY
# ---------------------------------------------------------

def get_disease_summary(disease_name):
    """
    Return a clean disease information object for the API.
    """

    information = get_disease_information(disease_name)

    if information is None:
        return {
            "available": False,
            "disease_key": normalize_disease_name(disease_name),
            "message": "Detailed knowledge unavailable for this class."
        }

    return {
        "available": True,

        "crop": information.get("crop"),

        "disease": information.get("disease"),

        "symptoms": information.get(
            "symptoms",
            []
        ),

        "causes": information.get(
            "causes",
            []
        ),

        "environment": information.get(
            "environment",
            []
        ),

        "spread": information.get(
            "spread",
            []
        ),

        "immediate_actions": information.get(
            "immediate_actions",
            []
        ),

        "prevention": information.get(
            "prevention",
            []
        ),

        "treatment_note": information.get(
            "treatment_note"
        )
    }


# ---------------------------------------------------------
# CHECK AVAILABILITY
# ---------------------------------------------------------

def disease_information_available(disease_name):
    """
    Check whether disease information exists.
    """

    return (
        get_disease_information(disease_name)
        is not None
    )


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    print("\n====================================")
    print("DISEASE KNOWLEDGE BASE TEST")
    print("====================================")

    test_disease = "potato early blight"

    result = get_disease_summary(test_disease)

    print(json.dumps(
        result,
        indent=4,
        ensure_ascii=False
    ))