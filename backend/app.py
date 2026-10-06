import os
import sys
from pathlib import Path

# ============================================================
# KERAS_HOME MUST be set before any TensorFlow import fires.
# tf.keras reads ~/.keras/keras.json at module load time, which
# fails in sandboxed / restricted environments. Point it to the
# local backend directory so no home-directory access is needed.
# ============================================================
_BACKEND_DIR = str(Path(__file__).resolve().parent)
if "KERAS_HOME" not in os.environ:
    os.environ["KERAS_HOME"] = str(Path(_BACKEND_DIR) / ".keras")

import io
import json
import uuid
import copy
import time
import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import numpy as np
from PIL import Image, ImageOps

from config import (
    MAX_FILE_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
    MAX_DECODED_PIXELS,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    MAX_IMAGE_WIDTH,
    MAX_IMAGE_HEIGHT,
)
Image.MAX_IMAGE_PIXELS = MAX_DECODED_PIXELS

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ============================================================
# LOCAL IMPORTS
# ============================================================

from predictor import PlantPredictor
from health_predictor import HealthPredictor
from gradcam import GradCAMGenerator
from segmentation import LeafSegmenter
from severity import analyze_segmentation_result
from traceability.blockchain import EvidenceBlockchain
from traceability.evidence import create_evidence_record
from auth import require_auth, authorize
from crop_identifier import (
    identify_crop_from_disease_class,
    enrich_top3_with_crop,
    filter_top3_by_crop,
    rank_diseases_for_crop,
    normalize_crop_name,
)
from crop_classifier import CropPredictor
from segmentation_confidence import estimate_segmentation_confidence
from review_queue import ReviewQueue
from utils import cleanup_expired_files, compute_file_sha256


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

GENERATED_DIR = BASE_DIR / "generated"
UPLOADS_DIR = BASE_DIR / "uploads"

DISEASE_KNOWLEDGE_DIR = os.path.join(
    BASE_DIR,
    "disease_knowledge"
)

DISEASE_KNOWLEDGE_FILE = os.path.join(
    DISEASE_KNOWLEDGE_DIR,
    "diseases.json"
)

os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

TRACEABILITY_DIR = os.path.join(BASE_DIR, "traceability")
os.makedirs(TRACEABILITY_DIR, exist_ok=True)
TRACEABILITY_CHAIN_FILE = os.path.join(TRACEABILITY_DIR, "evidence_chain.json")
evidence_blockchain = EvidenceBlockchain(storage_path=TRACEABILITY_CHAIN_FILE)
REVIEW_QUEUE_FILE = os.path.join(TRACEABILITY_DIR, "review_queue.json")
review_queue = ReviewQueue(REVIEW_QUEUE_FILE)


# ============================================================
# MODEL VERSION
# ============================================================

HEALTH_MODEL_VERSION = "health_disease_efficientnetb0"
DISEASE_MODEL_VERSION = "plantwild_v2_efficientnetb0"
SEGMENTATION_MODEL_VERSION = "unet_plantseg"
CROP_MODEL_VERSION = "crop_efficientnetb0"

HEALTH_MODEL_META = {
    "name": HEALTH_MODEL_VERSION,
    "model_hash": "bb961155086400507012b3d5202c585ee54289bcbbffcbc3baa4abed585689f5",
    "classes_hash": "3a0a1395512d4753f9fa5547a1b12561a9262620ea00d711a42f9961b4f074a1",
    "calibration_hash": "4eb30d1025624d8bc5af903bb57fbf5756590ef18e291111e6b401117373d347",
}
DISEASE_MODEL_META = {
    "name": DISEASE_MODEL_VERSION,
    "model_hash": "411611a0977eaba38ae616635ecb8e7f6c1299cb0e9f89f585896786adb6802c",
    "classes_hash": "b928d7d8c17fcf143111f4e2aa29b74a3f7e94a4cc15dfa9e4761cc5489a3da6",
}
CROP_MODEL_META = {
    "name": CROP_MODEL_VERSION,
    "model_hash": "b473ae77ca426e6910ec76d40c640732d30eb02c98cf3cee941b56b573a0d331",
    "classes_hash": "5b06e356caaf5cca3eb96457e55db60c8d88478530fd435607016e7af71d2a77",
}
SEGMENTATION_MODEL_META = {
    "name": SEGMENTATION_MODEL_VERSION,
    "model_hash": "622ac75ee8c7c12e7701384946540e1654a7073c111521f7c2cbadb433b895c8",
    "runtime_format": "SavedModel",
    "runtime_path": "segmentation_model/unet_plantseg_savedmodel",
    "source_model_hash": "11eaadaea1723edb86fca13bc4aade6a483f37e75b4d6658390cb63479221145",
    "source_format": "Keras",
    "source_model_path": "segmentation_model/unet_plantseg.keras",
}
SYSTEM_VERSION = "crop-disease-ai-v2"


# ============================================================
# FASTAPI APPLICATION
# ============================================================

from contextlib import asynccontextmanager

@asynccontextmanager
async def _lifespan(app_instance):
    """Run startup logic then yield control to FastAPI."""
    startup_event()
    yield

app = FastAPI(
    title="Crop Disease AI",
    description=(
        "AI-powered crop health, disease detection, "
        "segmentation, severity estimation and explainability API."
    ),
    version=SYSTEM_VERSION,
    lifespan=_lifespan,
)

from fastapi import Request
from fastapi.responses import JSONResponse

# 19. Add rate limiting
RATE_LIMIT_WINDOW = 60
MAX_REQUESTS_PER_WINDOW = 100
ip_request_counts = {}
ip_last_reset = {}

# 20. Add inference concurrency limits
MAX_CONCURRENT_INFERENCES = 4
inference_semaphore = asyncio.Semaphore(MAX_CONCURRENT_INFERENCES)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for static/file serving
    if request.url.path.startswith("/generated") or request.url.path.startswith("/uploads"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    if client_ip not in ip_last_reset or now - ip_last_reset[client_ip] > RATE_LIMIT_WINDOW:
        ip_request_counts[client_ip] = 0
        ip_last_reset[client_ip] = now

    ip_request_counts[client_ip] += 1
    if ip_request_counts[client_ip] > MAX_REQUESTS_PER_WINDOW:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    return await call_next(request)


# ============================================================
# CORS
# ============================================================

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Inspector-ID", "X-User-Role"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Swagger UI (/docs) and ReDoc (/redoc) require assets from jsDelivr and inline init scripts
    if request.url.path in ("/docs", "/redoc", "/openapi.json"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: blob: https://fastapi.tiangolo.com; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "connect-src 'self' http: https:; "
            "frame-ancestors 'none';"
        )
    else:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: blob:; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; font-src 'self'; connect-src 'self' http: https:; frame-ancestors 'none';"
        )
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https" or os.getenv("ENABLE_HSTS", "false").lower() in ("true", "1"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


# ============================================================
# STATIC FILES (SECURE ASSET SERVING)
# ============================================================

# 14, 15. Removed public /uploads and /generated static mounts
# app.mount("/generated", StaticFiles(directory=GENERATED_DIR, html=False), name="generated")
# app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR, html=False), name="uploads")

from fastapi.responses import FileResponse

@app.get("/uploads/{filename:path}")
def get_upload_file(filename: str, user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "view_reports")
    safe_filename = filename.lstrip("/\\")
    file_path = UPLOADS_DIR / safe_filename
    # Prevent path traversal
    if ".." in filename or not file_path.resolve().is_relative_to(UPLOADS_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Invalid path")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.get("/generated/{subpath:path}")
def get_generated_file(subpath: str, user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "view_reports")
    safe_subpath = subpath.lstrip("/\\")
    file_path = GENERATED_DIR / safe_subpath
    # Prevent path traversal
    if ".." in subpath or not file_path.resolve().is_relative_to(GENERATED_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Invalid path")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


# ============================================================
# GLOBAL MODEL OBJECTS
# ============================================================

health_predictor: Optional[HealthPredictor] = None
disease_predictor: Optional[PlantPredictor] = None
gradcam_generator: Optional[GradCAMGenerator] = None
leaf_segmenter: Optional[LeafSegmenter] = None
crop_predictor: Optional[CropPredictor] = None

disease_knowledge: Dict[str, Any] = {}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def generate_report_id() -> str:
    """
    Generate unique Crop Report ID.
    """
    return f"CR-{uuid.uuid4().hex[:12].upper()}"


def get_timestamp() -> str:
    """
    Return UTC ISO-8601 timestamp.
    """
    return datetime.now(timezone.utc).isoformat()


def calculate_sha256(data: bytes) -> str:
    """
    Calculate SHA-256 hash of uploaded image.
    """
    return hashlib.sha256(data).hexdigest()


def compute_directory_sha256(directory_path: Path) -> str:
    """
    Compute a deterministic SHA-256 hash for an entire directory.

    The hash includes every file's relative POSIX path and raw bytes,
    processed in deterministic sorted order.
    """
    root = Path(directory_path)

    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")

    if not root.is_dir():
        raise NotADirectoryError(
            f"Expected directory but received: {root}"
        )

    files = sorted(
        path for path in root.rglob("*")
        if path.is_file()
    )

    if not files:
        raise ValueError(f"Directory contains no files: {root}")

    hasher = hashlib.sha256()

    for path in files:
        relative_path = path.relative_to(root).as_posix()
        hasher.update(relative_path.encode("utf-8"))
        hasher.update(b"\0")

        with path.open("rb") as file:
            while True:
                chunk = file.read(1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)

        hasher.update(b"\0")

    return hasher.hexdigest()


def make_absolute_path(path: Optional[str]) -> Optional[str]:
    """
    Convert relative path to absolute path.
    """
    if not path:
        return None

    if os.path.isabs(path):
        return path

    return os.path.abspath(path)


def make_generated_url(path: Optional[str]) -> Optional[str]:
    """
    Convert generated file path into API URL.
    """
    if not path:
        return None

    absolute_path = make_absolute_path(path)
    if not absolute_path:
        return None

    try:
        p = Path(absolute_path).resolve()
        gen_dir = Path(GENERATED_DIR).resolve()
        if not p.is_relative_to(gen_dir):
            return None

        relative_path = p.relative_to(gen_dir).as_posix()
        return f"/generated/{relative_path}"
    except Exception:
        return None


def make_upload_url(path: Optional[str]) -> Optional[str]:
    """
    Convert uploaded file path into API URL.
    """
    if not path:
        return None

    absolute_path = make_absolute_path(path)
    if not absolute_path:
        return None

    try:
        p = Path(absolute_path).resolve()
        upl_dir = Path(UPLOADS_DIR).resolve()
        if not p.is_relative_to(upl_dir):
            return None

        relative_path = p.relative_to(upl_dir).as_posix()
        return f"/uploads/{relative_path}"
    except Exception:
        return None


def safe_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to float.
    """

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> Optional[int]:
    """
    Safely convert a value to int.
    """

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_prediction_result(result: Any) -> Dict[str, Any]:
    """
    Ensure prediction result is always returned as a dictionary.
    """

    if isinstance(result, dict):
        return result

    return {
        "prediction": result
    }



import re

PATH_REGEX = re.compile(
    r'(?:/(?:Users|home|var|tmp|private|root|opt|usr)/[^\s\'":;,<>]+|[A-Za-z]:\\[^\s\'":;,<>]+)'
)

def sanitize_embedded_paths(text: str) -> str:
    """Sanitize any absolute filesystem paths embedded within a string."""
    def _repl(match):
        raw = match.group(0)
        url = make_generated_url(raw) or make_upload_url(raw)
        return url if url else "[REDACTED_PATH]"
    return PATH_REGEX.sub(_repl, text)

def remove_absolute_path_keys(obj: Any) -> Any:
    """
    Recursively remove dictionary keys that start with 'absolute_'
    or contain absolute filesystem paths (e.g. '/Users/...').
    Sanitizes embedded absolute paths in strings/error messages.
    Preserves relative URLs like '/generated/...' and '/uploads/...'.
    """
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if str(k).startswith("absolute_"):
                continue
            cleaned[k] = remove_absolute_path_keys(v)
        return cleaned
    elif isinstance(obj, list):
        return [remove_absolute_path_keys(item) for item in obj]
    elif isinstance(obj, str):
        # Exact absolute path check
        if (obj.startswith("/Users/") or obj.startswith("/home/") or obj.startswith("/var/") or obj.startswith("/tmp/") or obj.startswith("/private/")) and os.path.isabs(obj):
            url = make_generated_url(obj) or make_upload_url(obj)
            return url if url else "[REDACTED_PATH]"
        # String with embedded absolute path (e.g. error messages)
        if ("/" in obj or "\\" in obj) and PATH_REGEX.search(obj):
            return sanitize_embedded_paths(obj)
        return obj
    return obj


def determine_human_review(response: Dict[str, Any], report_id: str) -> Dict[str, Any]:
    """
    Evaluate diagnostic results against quality/uncertainty triggers
    and enqueue for human review if necessary.
    """
    reasons = []
    if isinstance(response.get("health_prediction"), dict) and response["health_prediction"].get("uncertain"):
        reasons.append("health_prediction_uncertain")
    if isinstance(response.get("disease_analysis"), dict):
        disease_analysis = response["disease_analysis"]

        validation = disease_analysis.get("validation")
        if isinstance(validation, dict):
            if validation.get("status") == "rejected":
                reasons.append("no_compatible_disease")

        disease_confidence = safe_float(
            disease_analysis.get("confidence")
        )

        if (
            disease_confidence is not None
            and disease_confidence < 50
        ):
            reasons.append("low_disease_confidence")
    if isinstance(response.get("crop_prediction"), dict) and response["crop_prediction"].get("uncertain"):
        reasons.append("crop_prediction_uncertain")
    if isinstance(response.get("segmentation"), dict):
        level = ((response["segmentation"].get("confidence") or {}).get("level"))
        if level == "Low":
            reasons.append("low_segmentation_quality")
    if isinstance(response.get("severity"), dict) and response["severity"].get("calibration_required"):
        reasons.append("severity_thresholds_not_validated")

    if reasons:
        priority = "high" if any(r in reasons for r in ["health_prediction_uncertain", "low_disease_confidence"]) else "medium"
        raw_summary = {
            "health_prediction": response.get("health_prediction"),
            "crop_prediction": response.get("crop_prediction"),
            "disease_analysis": response.get("disease_analysis"),
            "segmentation": response.get("segmentation"),
            "severity": response.get("severity"),
        }
        sanitized_summary = remove_absolute_path_keys(raw_summary)
        review_queue.enqueue(report_id, reasons, priority, sanitized_summary)
        human_review = {"required": True, "reasons": reasons}
    else:
        human_review = {"required": False, "reasons": []}

    response["human_review"] = human_review
    return human_review


def add_traceability_block(*, response: Dict[str, Any], report_id: str, timestamp: str, image_hash: str, health_prediction: Optional[str], health_confidence: Optional[float], disease_prediction: Optional[str], disease_confidence: Optional[float], disease_uncertainty: Optional[str], disease_class_idx: Optional[int], severity: Optional[str], affected_area_percent: Optional[float], top_3: Optional[list], raw_top_3: Optional[list] = None, actor: Optional[Dict[str, Any]] = None) -> None:
    """Persist the complete diagnostic response as tamper-evident evidence."""
    try:
        # Determine human review status FIRST before assembling snapshot
        determine_human_review(response, report_id)

        # Deep copy response and clean absolute path keys & recursive traceability
        snapshot = json.loads(json.dumps(response, default=str))
        snapshot["traceability"] = None
        snapshot = remove_absolute_path_keys(snapshot)

        evidence_data = create_evidence_record(
            report_id=report_id,
            timestamp=timestamp,
            image_sha256=image_hash,
            health_prediction=health_prediction,
            health_confidence=health_confidence,
            disease_prediction=disease_prediction,
            disease_confidence=disease_confidence,
            disease_uncertainty=disease_uncertainty,
            disease_class_idx=disease_class_idx,
            severity=severity,
            affected_area_percent=affected_area_percent,
            model_versions={
                "system": {"name": SYSTEM_VERSION},
                "health": HEALTH_MODEL_META,
                "disease": DISEASE_MODEL_META,
                "segmentation": SEGMENTATION_MODEL_META,
                "crop": {
                    **CROP_MODEL_META,
                    "available": crop_predictor is not None,
                    "method": "dedicated_crop_classifier" if crop_predictor is not None else "disease_class_name_mapping",
                },
            },
            top_3=top_3 or [],
            report_snapshot=snapshot,
            actor=actor,
        )
        block = evidence_blockchain.add_block(report_id=report_id, evidence_data=evidence_data)
        verification = evidence_blockchain.verify_chain()
        if not isinstance(response.get("traceability"), dict):
            response["traceability"] = {}
        response["traceability"]["blockchain"] = {
            "enabled": True,
            "block_index": block["block_index"],
            "previous_hash": block["previous_hash"],
            "current_hash": block["current_hash"],
            "chain_valid": verification["valid"],
            "checked_blocks": verification["checked_blocks"],
            "invalid_block": verification.get("invalid_block"),
        }
    except Exception as exc:
        print("[WARNING] Traceability failed:", str(exc))
        if not isinstance(response.get("traceability"), dict):
            response["traceability"] = {}
        response["traceability"]["blockchain"] = {
            "enabled": False,
            "chain_valid": False,
            "error": str(exc),
        }

# ============================================================
# DISEASE KNOWLEDGE BASE
# ============================================================

def load_disease_knowledge() -> Dict[str, Any]:

    if not os.path.exists(DISEASE_KNOWLEDGE_FILE):
        print(
            "[WARNING] Disease knowledge file not found:",
            DISEASE_KNOWLEDGE_FILE
        )

        return {}

    try:

        with open(
            DISEASE_KNOWLEDGE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, dict):

            print(
                "[INFO] Disease knowledge base loaded:",
                len(data),
                "diseases"
            )

            return data

        print(
            "[WARNING] Disease knowledge JSON "
            "must contain an object."
        )

        return {}

    except Exception as e:

        print(
            "[ERROR] Failed to load disease knowledge:",
            str(e)
        )

        return {}


def get_disease_information(
    disease_name: Optional[str]
) -> Dict[str, Any]:

    if not disease_name:
        return {
            "available": False,
            "message": "Disease name is not available."
        }

    disease_key = (
        disease_name
        .strip()
        .lower()
        .replace("___", "_")
        .replace(" ", "_")
        .replace("-", "_")
    )

    # 1. Direct key lookup
    if disease_key in disease_knowledge:
        return {
            "available": True,
            "disease_key": disease_key,
            "information": disease_knowledge[disease_key]
        }

    # 2. Key with simplified crop prefix (e.g. apple_apple_scab -> apple_scab)
    parts = disease_key.split("_")
    if len(parts) >= 2 and parts[0] == parts[1]:
        simplified_key = "_".join(parts[1:])
        if simplified_key in disease_knowledge:
            return {
                "available": True,
                "disease_key": simplified_key,
                "information": disease_knowledge[simplified_key]
            }

    # 3. Substring matching in knowledge base
    for kb_key, kb_data in disease_knowledge.items():
        if kb_key in disease_key or disease_key in kb_key:
            return {
                "available": True,
                "disease_key": kb_key,
                "information": kb_data
            }

    # 4. Token overlap matching
    query_tokens = set(disease_key.split("_"))
    best_match = None
    max_overlap = 0
    for kb_key, kb_data in disease_knowledge.items():
        kb_tokens = set(kb_key.split("_"))
        overlap = len(query_tokens.intersection(kb_tokens))
        if overlap > max_overlap and overlap >= 2:
            max_overlap = overlap
            best_match = (kb_key, kb_data)

    if best_match:
        return {
            "available": True,
            "disease_key": best_match[0],
            "information": best_match[1]
        }

    return {
        "available": False,
        "disease_key": disease_key,
        "message": (
            "Disease information is not available "
            "in the current knowledge base."
        )
    }


# ============================================================
# STARTUP
# ============================================================

def startup_event():

    global health_predictor
    global disease_predictor
    global gradcam_generator
    global leaf_segmenter
    global crop_predictor
    global disease_knowledge

    print("\n" + "=" * 70)
    print("STARTING CROP DISEASE AI")
    print("=" * 70)

    # --------------------------------------------------------
    # HEALTH MODEL
    # --------------------------------------------------------

    try:

        health_predictor = HealthPredictor()
        try:
            from health_predictor import MODEL_PATH as HP_MODEL_PATH, CLASS_NAMES_PATH as HP_CLASS_NAMES_PATH, CALIBRATION_PATH as HP_CALIBRATION_PATH
            HEALTH_MODEL_META["model_hash"] = compute_file_sha256(str(HP_MODEL_PATH))
            HEALTH_MODEL_META["classes_hash"] = compute_file_sha256(str(HP_CLASS_NAMES_PATH))
            if HP_CALIBRATION_PATH.exists():
                HEALTH_MODEL_META["calibration_hash"] = compute_file_sha256(str(HP_CALIBRATION_PATH))
        except Exception as e:
            print("[WARNING] Could not hash health model:", str(e))

        print(
            "[INFO] Health predictor loaded successfully."
        )

    except Exception as e:

        health_predictor = None

        print(
            "[ERROR] Failed to load health predictor:",
            str(e)
        )

    # --------------------------------------------------------
    # DISEASE MODEL
    # --------------------------------------------------------

    try:

        disease_predictor = PlantPredictor()
        try:
            from config import MODEL_PATH as DP_MODEL_PATH, CLASS_NAMES_PATH as DP_CLASS_NAMES_PATH
            DISEASE_MODEL_META["model_hash"] = compute_file_sha256(str(DP_MODEL_PATH))
            DISEASE_MODEL_META["classes_hash"] = compute_file_sha256(str(DP_CLASS_NAMES_PATH))
        except Exception as e:
            print("[WARNING] Could not hash disease model:", str(e))

        print(
            "[INFO] Disease predictor loaded successfully."
        )

        try:

            print(
                "[INFO] Disease classes:",
                len(disease_predictor.class_names)
            )

        except Exception:
            pass

    except Exception as e:

        disease_predictor = None

        print(
            "[ERROR] Failed to load disease predictor:",
            str(e)
        )

    # --------------------------------------------------------
    # DEDICATED CROP MODEL
    # --------------------------------------------------------

    try:
        crop_predictor = CropPredictor()
        try:
            from crop_classifier import MODEL_PATH as CROP_MODEL_PATH, CLASS_NAMES_PATH as CROP_CLASS_NAMES_PATH
            CROP_MODEL_META["model_hash"] = compute_file_sha256(str(CROP_MODEL_PATH))
            CROP_MODEL_META["classes_hash"] = compute_file_sha256(str(CROP_CLASS_NAMES_PATH))
        except Exception as e:
            print("[WARNING] Could not hash crop model:", str(e))
        print("[INFO] Dedicated crop predictor loaded successfully.")
    except Exception as e:
        crop_predictor = None
        print("[WARNING] Dedicated crop predictor unavailable:", str(e))

    # --------------------------------------------------------
    # GRAD-CAM
    # --------------------------------------------------------

    try:

        if disease_predictor is None:
            raise RuntimeError("Disease predictor is unavailable; Grad-CAM cannot be initialized.")
        gradcam_generator = GradCAMGenerator(
            disease_predictor.model
        )

        print(
            "[INFO] Grad-CAM initialized successfully."
        )

    except Exception as e:

        gradcam_generator = None

        print(
            "[WARNING] Grad-CAM initialization failed:",
            str(e)
        )

    # --------------------------------------------------------
    # SEGMENTATION
    # --------------------------------------------------------

    try:

        leaf_segmenter = LeafSegmenter()

        try:
            from segmentation import (
                SEGMENTATION_SAVEDMODEL_PATH,
                SEGMENTATION_MODEL_PATH,
                SEGMENTATION_SOURCE_KERAS_PATH,
            )

            # Production runtime artifact: TensorFlow SavedModel.
            if not SEGMENTATION_SAVEDMODEL_PATH.exists():
                raise FileNotFoundError(
                    "Production segmentation SavedModel not found: "
                    f"{SEGMENTATION_SAVEDMODEL_PATH}"
                )

            if not SEGMENTATION_SAVEDMODEL_PATH.is_dir():
                raise NotADirectoryError(
                    "Production segmentation SavedModel path is not a directory: "
                    f"{SEGMENTATION_SAVEDMODEL_PATH}"
                )

            SEGMENTATION_MODEL_META["model_hash"] = (
                compute_directory_sha256(
                    SEGMENTATION_SAVEDMODEL_PATH
                )
            )
            SEGMENTATION_MODEL_META["runtime_format"] = "SavedModel"
            SEGMENTATION_MODEL_META["runtime_path"] = (
                "segmentation_model/unet_plantseg_savedmodel"
            )

            # Original Keras artifact retained as source/conversion lineage.
            if SEGMENTATION_SOURCE_KERAS_PATH.exists():
                SEGMENTATION_MODEL_META["source_model_hash"] = (
                    compute_file_sha256(
                        str(SEGMENTATION_SOURCE_KERAS_PATH)
                    )
                )
                SEGMENTATION_MODEL_META["source_format"] = "Keras"
                SEGMENTATION_MODEL_META["source_model_path"] = (
                    "segmentation_model/unet_plantseg.keras"
                )

            print(
                "[INFO] Segmentation runtime artifact hash:",
                SEGMENTATION_MODEL_META.get("model_hash")
            )
            print(
                "[INFO] Segmentation source model hash:",
                SEGMENTATION_MODEL_META.get("source_model_hash")
            )
            print(
                "[INFO] Segmentation runtime format:",
                SEGMENTATION_MODEL_META.get("runtime_format")
            )

        except Exception as e:
            print("[WARNING] Could not hash segmentation model:", str(e))

        print(
            "[INFO] Leaf segmentation model loaded."
        )

    except Exception as e:

        leaf_segmenter = None

        print(
            "[WARNING] Segmentation model failed:",
            str(e)
        )

    # --------------------------------------------------------
    # KNOWLEDGE BASE
    # --------------------------------------------------------

    disease_knowledge = load_disease_knowledge()

    print("=" * 70)
    print("STARTUP COMPLETE")
    print("=" * 70 + "\n")


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "application": "Crop Disease AI",
        "version": SYSTEM_VERSION,
        "status": "running",
        "models": {
            "health": health_predictor is not None,
            "disease": disease_predictor is not None,
            "gradcam": gradcam_generator is not None,
            "segmentation": leaf_segmenter is not None,
            "crop_identification": crop_predictor is not None,
            "human_review_queue": True
        }
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    health_ok = health_predictor is not None
    disease_ok = disease_predictor is not None
    crop_ok = crop_predictor is not None
    gradcam_ok = gradcam_generator is not None
    segmentation_ok = leaf_segmenter is not None

    if not health_ok or not disease_ok:
        status_str = "unhealthy"
    elif not crop_ok or not gradcam_ok or not segmentation_ok:
        status_str = "degraded"
    else:
        status_str = "healthy"

    return {
        "status": status_str,
        "models": {
            "health_model": health_ok,
            "disease_model": disease_ok,
            "crop_model": {
                "available": crop_ok,
                "method": "dedicated_crop_classifier" if crop_ok else "disease_class_name_mapping"
            },
            "gradcam": gradcam_ok,
            "segmentation": segmentation_ok,
            "traceability": True,
            "human_review_queue": True
        },
        "knowledge_base": {
            "loaded": bool(disease_knowledge),
            "disease_count": len(disease_knowledge)
        }
    }


# ============================================================
# PREDICT ENDPOINT
# ============================================================

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    user: Dict[str, str] = Depends(require_auth),
):

    authorize(user, "scan")

    # ========================================================
    # INITIAL VALIDATION
    # ========================================================

    if not file:

        raise HTTPException(
            status_code=400,
            detail="No image file uploaded."
        )

    if not file.content_type:

        raise HTTPException(
            status_code=400,
            detail="File content type is missing."
        )

    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if not ext:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have an image extension (.jpg, .jpeg, .png, .webp)."
        )

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    declared_content_type = file.content_type.lower()
    allowed_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    }

    if declared_content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image type. "
                "Please upload JPG, JPEG, PNG or WEBP."
            )
        )

    if ext in {".jpg", ".jpeg"} and declared_content_type not in {"image/jpeg", "image/jpg"}:
        raise HTTPException(
            status_code=400,
            detail=f"Extension '{ext}' does not match declared Content-Type '{declared_content_type}'."
        )
    if ext == ".png" and declared_content_type != "image/png":
        raise HTTPException(
            status_code=400,
            detail=f"Extension '{ext}' does not match declared Content-Type '{declared_content_type}'."
        )
    if ext == ".webp" and declared_content_type != "image/webp":
        raise HTTPException(
            status_code=400,
            detail=f"Extension '{ext}' does not match declared Content-Type '{declared_content_type}'."
        )

    # ========================================================
    # READ FILE
    # ========================================================

    try:

        image_bytes = await file.read()

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Could not read uploaded image: {str(e)}"
        )

    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    # ========================================================
    # IMAGE SIZE VALIDATION
    # ========================================================

    if len(image_bytes) > MAX_FILE_SIZE_BYTES:

        raise HTTPException(
            status_code=413,
            detail=f"Image size must be less than {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )

    # ========================================================
    # OPEN IMAGE & VERIFY CONTENT FORMAT
    # ========================================================

    try:

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        detected_format = getattr(image, "format", None)
        if isinstance(detected_format, str) and detected_format:
            detected_format = detected_format.upper()
            format_extension_map = {
                "JPEG": {".jpg", ".jpeg"},
                "PNG": {".png"},
                "WEBP": {".webp"},
            }
            valid_extensions = format_extension_map.get(detected_format, set())
            if ext not in valid_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Uploaded image content format ({detected_format}) does not match file extension ({ext})."
                )

        image = ImageOps.exif_transpose(image)

        image.load()

        image = image.convert("RGB")

        w, h = image.size
        if w < MIN_IMAGE_WIDTH or h < MIN_IMAGE_HEIGHT:
            raise HTTPException(
                status_code=400,
                detail=f"Image dimensions too small ({w}x{h}). Minimum {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT} pixels required."
            )
        total_pixels = w * h
        if total_pixels > MAX_DECODED_PIXELS:
            raise HTTPException(
                status_code=400,
                detail=f"Image pixel count ({total_pixels:,}) exceeds the safety limit of {MAX_DECODED_PIXELS:,} pixels ({w}x{h})."
            )
        if w > MAX_IMAGE_WIDTH or h > MAX_IMAGE_HEIGHT:
            raise HTTPException(
                status_code=400,
                detail=f"Image dimensions too large ({w}x{h}). Maximum {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT} pixels allowed."
            )

    except HTTPException:
        raise
    except Image.DecompressionBombError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds safety decompression limits: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid or corrupted image file: "
                f"{str(e)}"
            )
        )

    # ========================================================
    # BASIC METADATA
    # ========================================================

    report_id = generate_report_id()

    timestamp = get_timestamp()

    image_hash = calculate_sha256(
        image_bytes
    )

    original_filename = (
        file.filename
        if file.filename
        else "uploaded_image.jpg"
    )

    # ========================================================
    # SAVE ORIGINAL IMAGE
    # ========================================================

    clean_base = os.path.basename(original_filename).replace("/", "").replace("\\", "").replace("..", "")
    safe_chars = "".join(c for c in clean_base if c.isalnum() or c in "._- ")
    safe_stem, _ = os.path.splitext(safe_chars or "uploaded_image")
    safe_stem = safe_stem.strip("._- ")
    if not safe_stem:
        safe_stem = "uploaded_image"
    safe_filename = f"{report_id}_{safe_stem}.jpg"

    upload_path = os.path.join(
        UPLOADS_DIR,
        safe_filename
    )

    try:

        image.save(
            upload_path,
            format="JPEG",
            quality=95
        )

    except Exception as e:

        print(
            "[WARNING] Could not save uploaded image:",
            str(e)
        )

        upload_path = None

    # ========================================================
    # RESPONSE BASE
    # ========================================================

    if upload_path:
        response_image_url = make_upload_url(upload_path)
    else:
        response_image_url = None

    response: Dict[str, Any] = {

        "success": True,

        "report_id": report_id,

        "timestamp": timestamp,

        "image": {
            "filename": original_filename,
            "url": response_image_url,
            "sha256": image_hash,
            "width": image.width,
            "height": image.height,
            "format": "RGB"
        },

        "system": {
            "version": SYSTEM_VERSION,
            "health_model": HEALTH_MODEL_VERSION,
            "disease_model": DISEASE_MODEL_VERSION,
            "segmentation_model": SEGMENTATION_MODEL_VERSION,
            "crop_model": {
                "name": CROP_MODEL_VERSION,
                "available": crop_predictor is not None,
                "method": "dedicated_crop_classifier" if crop_predictor is not None else "disease_class_name_mapping",
            },
        },

        "health_prediction": None,

        "crop_prediction": None,

        "disease_analysis": None,

        "disease_information": None,

        "explainability": None,

        "segmentation": None,

        "severity": None,

        "traceability": None,

        "status": None,

        "message": None
    }

    # ========================================================
    # HEALTH MODEL CHECK
    # ========================================================

    if health_predictor is None:

        raise HTTPException(
            status_code=503,
            detail="Health prediction model is not available."
        )

    try:

        # IMPORTANT:
        # HealthPredictor expects PIL.Image
        # Inference is CPU-bound/blocking — run in thread pool to avoid blocking the event loop.
        async with inference_semaphore:
            loop = asyncio.get_event_loop()
            health_result = await loop.run_in_executor(
                None, health_predictor.predict_image, image
            )

        health_result = normalize_prediction_result(
            health_result
        )

    except Exception as e:

        print(
            "[ERROR] Health prediction failed:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Health prediction failed: "
                f"{str(e)}"
            )
        )

    # ========================================================
    # DEDICATED CROP IDENTIFICATION
    # ========================================================

    crop_result = None
    if crop_predictor is not None:
        try:
            async with inference_semaphore:
                loop = asyncio.get_event_loop()
                crop_result = await loop.run_in_executor(
                    None, crop_predictor.predict_image, image
                )
            response["crop_prediction"] = crop_result
        except Exception as e:
            print("[WARNING] Crop prediction failed:", str(e))
            response["crop_prediction"] = {"available": False, "message": str(e)}
    else:
        response["crop_prediction"] = {
            "available": False,
            "message": "Dedicated crop model is not installed. Crop identification will use disease-class mapping when possible.",
        }

    # ========================================================
    # HEALTH RESULT
    # ========================================================

    health_prediction = health_result.get(
        "prediction"
    )

    if health_prediction is None:

        health_prediction = health_result.get(
            "predicted_class"
        )

    if health_prediction is None:

        health_prediction = health_result.get(
            "class_name"
        )

    if health_prediction is not None:

        health_prediction = str(
            health_prediction
        ).lower()

    health_confidence = safe_float(
        health_result.get("confidence")
    )

    healthy_probability = safe_float(
        health_result.get("healthy_probability")
        or health_result.get("probability_healthy")
    )

    diseased_probability = safe_float(
        health_result.get("diseased_probability")
        or health_result.get("probability_diseased")
    )

    health_class_idx = safe_int(
        health_result.get("predicted_class_idx")
    )

    health_uncertain = health_result.get(
        "uncertain",
        False
    )

    health_threshold = safe_float(
        health_result.get("threshold")
    )

    # --------------------------------------------------------
    # If predictor did not provide probabilities, derive them
    # where possible from confidence + predicted class.
    # --------------------------------------------------------

    if (
        healthy_probability is None
        and diseased_probability is None
        and health_confidence is not None
    ):

        confidence_fraction = (
            health_confidence / 100.0
            if health_confidence > 1
            else health_confidence
        )

        confidence_fraction = max(
            0.0,
            min(1.0, confidence_fraction)
        )

        if health_prediction == "healthy":

            healthy_probability = (
                confidence_fraction
            )

            diseased_probability = (
                1.0 - confidence_fraction
            )

        elif health_prediction == "diseased":

            diseased_probability = (
                confidence_fraction
            )

            healthy_probability = (
                1.0 - confidence_fraction
            )

    response["health_prediction"] = {

        "prediction": health_prediction,

        "predicted_class_idx": health_class_idx,

        "confidence": health_confidence,

        "healthy_probability": (
            healthy_probability
        ),

        "diseased_probability": (
            diseased_probability
        ),

        "threshold": health_threshold,

        "uncertain": bool(
            health_uncertain
        ),

        "model": HEALTH_MODEL_VERSION,

        "class_names": (
            health_result.get("class_names")
        ),

        "calibration": health_result.get("calibration")
    }

    # ========================================================
    # HEALTH CONFIDENCE GATE
    # ========================================================

    if bool(health_uncertain):
        response["status"] = "uncertain_health_prediction"
        response["message"] = (
            "The AI could not confidently determine whether the image is healthy or diseased. "
            "Please upload a clearer image or request agronomist review."
        )
        response["traceability"] = {
            "report_id": report_id,
            "timestamp": timestamp,
            "image_sha256": image_hash,
            "pipeline": "health_classifier_only",
            "health_model": {"name": HEALTH_MODEL_VERSION, "prediction": health_prediction, "confidence": health_confidence},
            "actor": user,
        }
        add_traceability_block(
            response=response, report_id=report_id, timestamp=timestamp, image_hash=image_hash,
            health_prediction=health_prediction, health_confidence=health_confidence,
            disease_prediction=None, disease_confidence=None, disease_uncertainty="High",
            disease_class_idx=None, severity=None, affected_area_percent=None, top_3=[], actor=user,
        )
        return remove_absolute_path_keys(response)

    # ========================================================
    # HEALTHY BRANCH
    # ========================================================

    if health_prediction == "healthy":

        response["status"] = (
            "healthy_prediction"
        )

        response["message"] = (
            "The image was classified as healthy."
        )

        response["traceability"] = {

            "report_id": report_id,

            "timestamp": timestamp,

            "image_sha256": image_hash,

            "pipeline": "health_classifier_only",

            "actor": user,

            "health_model": {
                "name": HEALTH_MODEL_VERSION,
                "prediction": health_prediction,
                "confidence": health_confidence
            },

            "disease_model": None,

            "segmentation_model": None
        }

        add_traceability_block(
            response=response, report_id=report_id, timestamp=timestamp, image_hash=image_hash,
            health_prediction=health_prediction, health_confidence=health_confidence,
            disease_prediction=None, disease_confidence=None, disease_uncertainty=None,
            disease_class_idx=None, severity=None, affected_area_percent=None, top_3=[], actor=user,
        )

        return remove_absolute_path_keys(response)

    # ========================================================
    # IF HEALTH PREDICTION IS UNKNOWN
    # ========================================================

    if health_prediction not in {
        "diseased",
        "healthy"
    }:

        response["status"] = (
            "uncertain_health_prediction"
        )

        response["message"] = (
            "The AI could not confidently determine "
            "whether the image is healthy or diseased. "
            "Please upload a clearer image."
        )

        response["traceability"] = {

            "report_id": report_id,

            "timestamp": timestamp,

            "image_sha256": image_hash,

            "pipeline": "health_classifier_only",

            "actor": user,

            "health_model": {
                "name": HEALTH_MODEL_VERSION,
                "prediction": health_prediction,
                "confidence": health_confidence
            }
        }

        add_traceability_block(
            response=response, report_id=report_id, timestamp=timestamp, image_hash=image_hash,
            health_prediction=health_prediction, health_confidence=health_confidence,
            disease_prediction=None, disease_confidence=None, disease_uncertainty=None,
            disease_class_idx=None, severity=None, affected_area_percent=None, top_3=[], actor=user,
        )

        return remove_absolute_path_keys(response)

    # ========================================================
    # DISEASE MODEL CHECK
    # ========================================================

    if disease_predictor is None:

        response["status"] = (
            "health_prediction_only"
        )

        response["message"] = (
            "The image appears diseased, "
            "but the disease model is unavailable."
        )

        response["traceability"] = {
            "report_id": report_id, "timestamp": timestamp, "image_sha256": image_hash,
            "pipeline": "health_classifier_only",
            "health_model": {"name": HEALTH_MODEL_VERSION, "prediction": health_prediction, "confidence": health_confidence, "predicted_class_idx": health_class_idx},
            "disease_model": None, "segmentation_model": None,
        }
        add_traceability_block(
            response=response, report_id=report_id, timestamp=timestamp, image_hash=image_hash,
            health_prediction=health_prediction, health_confidence=health_confidence,
            disease_prediction=None, disease_confidence=None, disease_uncertainty=None,
            disease_class_idx=None, severity=None, affected_area_percent=None, top_3=[], actor=user,
        )

        return remove_absolute_path_keys(response)

    # ========================================================
    # DISEASE PREDICTION
    # ========================================================

    try:

        # IMPORTANT:
        # PlantPredictor expects PIL.Image
        # Inference is CPU-bound/blocking — run in thread pool to avoid blocking the event loop.
        async with inference_semaphore:
            loop = asyncio.get_event_loop()
            disease_result = await loop.run_in_executor(
                None, disease_predictor.predict_image, image
            )

        disease_result = normalize_prediction_result(
            disease_result
        )

    except Exception as e:

        print(
            "[ERROR] Disease prediction failed:",
            str(e)
        )

        response["status"] = (
            "disease_prediction_failed"
        )

        response["message"] = (
            "The image appears diseased, "
            "but disease identification failed."
        )

        response["traceability"] = {

            "report_id": report_id,

            "timestamp": timestamp,

            "image_sha256": image_hash,

            "pipeline": (
                "health_classifier_then_disease_classifier"
            ),

            "actor": user,

            "health_model": {
                "name": HEALTH_MODEL_VERSION,
                "prediction": health_prediction,
                "confidence": health_confidence
            },

            "disease_model": {
                "name": DISEASE_MODEL_VERSION,
                "error": str(e)
            }
        }

        add_traceability_block(
            response=response, report_id=report_id, timestamp=timestamp, image_hash=image_hash,
            health_prediction=health_prediction, health_confidence=health_confidence,
            disease_prediction=None, disease_confidence=None, disease_uncertainty=None,
            disease_class_idx=None, severity=None, affected_area_percent=None, top_3=[], actor=user,
        )

        return remove_absolute_path_keys(response)

    # ========================================================
    # DISEASE PREDICTION FIELDS
    # ========================================================

    disease_name = disease_result.get(
        "prediction"
    )

    if disease_name is None:

        disease_name = disease_result.get(
            "predicted_class"
        )

    if disease_name is None:

        disease_name = disease_result.get(
            "class_name"
        )

    if disease_name is not None:

        disease_name = str(
            disease_name
        )

    disease_confidence = safe_float(
        disease_result.get("confidence")
    )

    disease_uncertainty = (
        disease_result.get("uncertainty")
    )

    disease_class_idx = safe_int(
        disease_result.get(
            "predicted_class_idx"
        )
    )

    top3 = disease_result.get(
        "top3"
    )

    if not isinstance(top3, list):

        top3 = []

    # ========================================================
    # NORMALIZE TOP-3
    # ========================================================

    normalized_top3 = []

    for item in top3:

        if not isinstance(item, dict):
            continue

        normalized_item = dict(item)

        if "confidence" in normalized_item:

            normalized_item["confidence"] = (
                safe_float(
                    normalized_item["confidence"]
                )
            )

        if "class_idx" in normalized_item:

            normalized_item["class_idx"] = (
                safe_int(
                    normalized_item["class_idx"]
                )
            )

        normalized_top3.append(
            normalized_item
        )

    top3 = enrich_top3_with_crop(normalized_top3)

    # ========================================================
    # CROP IDENTIFICATION
    # ========================================================

    inferred_crop = identify_crop_from_disease_class(
        disease_name
    )

    crop_method = "disease_class_name_mapping"

    if (
        isinstance(crop_result, dict)
        and crop_result.get("prediction")
    ):
        inferred_crop = crop_result.get("prediction")
        crop_method = "dedicated_crop_classifier"

    # ========================================================
    # PRESERVE RAW DISEASE PREDICTION
    # ========================================================

    raw_disease_name = disease_name
    raw_disease_confidence = disease_confidence
    raw_disease_class_idx = disease_class_idx
    raw_disease_uncertainty = disease_uncertainty
    raw_top3 = list(top3)

    # ========================================================
    # CROP-AWARE DISEASE VALIDATION (ALL 115 PROBABILITIES)
    # ========================================================
    #
    # When an independent crop is detected, evaluate disease candidates
    # across the complete 115-class probability vector, rather than
    # only the global top-3.
    #
    # Raw predictions remain in response["disease_analysis"]["raw_top_3"].
    # ========================================================

    all_probabilities = disease_result.get("probabilities")
    class_names_list = disease_result.get("class_names") or (
        disease_predictor.class_names if disease_predictor else []
    )

    compatible_top3 = rank_diseases_for_crop(
        class_names=class_names_list,
        probabilities=all_probabilities,
        detected_crop=inferred_crop,
        k=3,
    )

    disease_validation_status = "not_validated"
    disease_validation_reason = None

    if crop_method == "dedicated_crop_classifier":

        crop_conf = safe_float(crop_result.get("confidence") if isinstance(crop_result, dict) else None)

        if crop_conf is not None and crop_conf < 50.0:
            # Crop model is uncertain: produce NO official disease prediction.
            # Raw disease prediction is preserved separately in raw_prediction / raw_top_3 as an unvalidated candidate.
            disease_name = None
            disease_confidence = None
            disease_class_idx = None
            disease_uncertainty = "High"
            disease_validation_status = "skipped_low_crop_confidence"
            top3 = []
            compatible_top3 = []
            disease_validation_reason = (
                "Crop prediction confidence was too low (< 50%) to safely validate disease candidates. "
                "No official disease prediction was assigned; raw prediction preserved for audit."
            )

        elif compatible_top3:

            validated_top1 = compatible_top3[0]

            disease_name = validated_top1.get("class")

            disease_confidence = safe_float(
                validated_top1.get("confidence")
            )

            disease_class_idx = safe_int(
                validated_top1.get("class_idx")
            )

            # Recalculate uncertainty from the validated
            # crop-compatible disease prediction.
            if disease_confidence is None:
                disease_uncertainty = "High"
            elif disease_confidence < 50:
                disease_uncertainty = "High"
            elif disease_confidence < 75:
                disease_uncertainty = "Medium"
            else:
                disease_uncertainty = "Low"

            disease_validation_status = "validated_by_crop"
            top3 = compatible_top3

        else:

            # The disease model produced no compatible
            # candidate across all 115 classes for this crop.
            disease_name = None
            disease_confidence = None
            disease_class_idx = None
            disease_uncertainty = "High"

            disease_validation_status = "rejected"
            top3 = [] # Fix rejected top_3

            disease_validation_reason = (
                "No disease-class prediction across all model categories is compatible with the independently "
                "detected crop."
            )

    else:

        # Legacy fallback only applies when the dedicated crop
        # classifier is unavailable.
        disease_validation_status = "legacy_mapping"

        disease_validation_reason = (
            "Dedicated crop classifier was unavailable; "
            "crop-aware disease validation could not be "
            "performed independently."
        )

    # ========================================================
    # DISEASE CLASS INDEX FALLBACK
    # ========================================================
    #
    # This fallback is only valid for a validated/legacy
    # prediction. Never use the raw incompatible prediction
    # after crop validation rejected it.
    # ========================================================

    if disease_class_idx is None and disease_name is not None:

        if compatible_top3 and disease_validation_status == "validated_by_crop":

            disease_class_idx = safe_int(
                compatible_top3[0].get("class_idx")
            )

        elif disease_validation_status == "legacy_mapping" and top3:

            disease_class_idx = safe_int(
                top3[0].get("class_idx")
            )

    # ========================================================
    # DETERMINE UNCERTAINTY
    # ========================================================

    if disease_uncertainty is None:

        if (
            disease_confidence is not None
            and disease_confidence < 50
        ):

            disease_uncertainty = "High"

        elif (
            disease_confidence is not None
            and disease_confidence < 75
        ):

            disease_uncertainty = "Medium"

        else:

            disease_uncertainty = "Low"

    disease_uncertainty = str(
        disease_uncertainty
    )

    # ========================================================
    # DISEASE ANALYSIS
    # ========================================================

    response["disease_analysis"] = {

        # Validated/final disease prediction.
        "prediction": disease_name,

        # Raw disease-model prediction is retained for
        # auditability and debugging.
        "raw_prediction": raw_disease_name,

        "raw_confidence": raw_disease_confidence,

        "raw_predicted_class_idx": raw_disease_class_idx,

        "raw_uncertainty": raw_disease_uncertainty,

        "raw_top_3": raw_top3,

        "crop": inferred_crop,

        "crop_identification_method": crop_method,

        "crop_confidence": (
            (crop_result or {}).get("confidence")
            if isinstance(crop_result, dict)
            else None
        ),

        "crop_uncertain": (
            (crop_result or {}).get("uncertain")
            if isinstance(crop_result, dict)
            else True
        ),

        "confidence": disease_confidence,

        "uncertainty": disease_uncertainty,

        "predicted_class_idx": disease_class_idx,

        # Raw model top-3 is preserved.
        "top_3": top3,

        # Crop-compatible candidates are exposed separately.
        "compatible_top_3": compatible_top3,

        "validation": {
            "status": disease_validation_status,
            "reason": disease_validation_reason,
        },

        "model": DISEASE_MODEL_VERSION
    }

    # ========================================================
    # KNOWLEDGE BASE
    # ========================================================

    response["disease_information"] = (
        get_disease_information(
            disease_name
        )
    )

    # ========================================================
    # GRAD-CAM
    # ========================================================

    explainability = {

        "available": False,

        "method": "Grad-CAM",

        "target_class_idx": disease_class_idx,

        "heatmap": None,

        "overlay": None,

        "message": None
    }

    if gradcam_generator is None:

        explainability["message"] = (
            "Grad-CAM is not available."
        )

    elif disease_class_idx is None:

        if disease_validation_status == "rejected":

            explainability["message"] = (
                "Grad-CAM was not generated because the "
                "raw disease prediction was incompatible "
                "with the independently detected crop."
            )

        elif disease_validation_status == "skipped_low_crop_confidence":

            explainability["message"] = (
                "Grad-CAM was not generated because crop "
                "prediction confidence was too low to validate "
                "a target disease candidate."
            )

        else:

            explainability["message"] = (
                "Grad-CAM could not determine "
                "the target disease class."
            )

    else:

        try:

            # ----------------------------------------------
            # Disease predictor preprocessing
            # ----------------------------------------------

            img_batch = (
                disease_predictor.preprocess_image(
                    image
                )
            )

            img_batch = np.asarray(
                img_batch
            )

            if img_batch.ndim == 3:

                img_batch = np.expand_dims(
                    img_batch,
                    axis=0
                )

            # ----------------------------------------------
            # Generate Grad-CAM
            # ----------------------------------------------

            gradcam_result = (
                gradcam_generator.generate_gradcam(
                    img_batch,
                    int(disease_class_idx),
                    original_img=image,
                    alpha=0.4
                )
            )

            if not isinstance(
                gradcam_result,
                dict
            ):

                gradcam_result = {}

            explainability["available"] = True

            explainability["target_class_idx"] = (
                disease_class_idx
            )

            explainability["target_layer"] = (
                gradcam_generator.target_layer_name
                if hasattr(
                    gradcam_generator,
                    "target_layer_name"
                )
                else None
            )

            # ----------------------------------------------
            # Copy generated paths
            # ----------------------------------------------

            heatmap_path = (
                gradcam_result.get(
                    "absolute_heatmap_path"
                ) or gradcam_result.get(
                    "heatmap_path"
                )
            )

            overlay_path = (
                gradcam_result.get(
                    "absolute_overlay_path"
                ) or gradcam_result.get(
                    "overlay_path"
                )
            )

            if heatmap_path:

                explainability["heatmap"] = (
                    make_generated_url(
                        heatmap_path
                    )
                )

            if overlay_path:

                explainability["overlay"] = (
                    make_generated_url(
                        overlay_path
                    )
                )

            # ----------------------------------------------
            # Copy any other useful Grad-CAM information
            # ----------------------------------------------

            for key in [
                "prediction",
                "confidence"
            ]:

                if (
                    key in gradcam_result
                    and gradcam_result[key] is not None
                ):

                    explainability[key] = (
                        gradcam_result[key]
                    )

        except Exception as e:

            print(
                "[WARNING] Grad-CAM failed:",
                str(e)
            )

            explainability["available"] = False

            explainability["message"] = (
                f"Grad-CAM generation failed: {str(e)}"
            )

    response["explainability"] = (
        explainability
    )

    # ========================================================
    # SEGMENTATION
    # ========================================================

    segmentation_result = None

    if leaf_segmenter is not None:

        try:

            # IMPORTANT:
            # LeafSegmenter expects PIL.Image
            # Inference is CPU-bound/blocking — run in thread pool to avoid blocking the event loop.
            loop = asyncio.get_event_loop()
            segmentation_result = await loop.run_in_executor(
                None, leaf_segmenter.segment_image, image
            )

            if not isinstance(
                segmentation_result,
                dict
            ):

                segmentation_result = None

        except Exception as e:

            print(
                "[WARNING] Segmentation failed:",
                str(e)
            )

            segmentation_result = None

    if segmentation_result is None:

        response["segmentation"] = {

            "available": False,

            "message": (
                "Segmentation could not be performed."
            )
        }

    else:

        segmentation_output = dict(
            segmentation_result
        )

        # ----------------------------------------------
        # Convert generated paths into URLs
        # ----------------------------------------------

        path_keys = [
            "leaf_mask_path",
            "disease_mask_path",
            "overlay_path",
            "composite_path"
        ]

        absolute_key_map = {
            "leaf_mask_path": "absolute_leaf_mask_path",
            "disease_mask_path": "absolute_disease_mask_path",
            "overlay_path": "absolute_overlay_path",
            "composite_path": "absolute_composite_path",
        }

        for key in path_keys:

            if key in segmentation_output:
                # Prefer absolute path to avoid double-prefix in make_generated_url
                abs_key = absolute_key_map.get(key)
                path_to_convert = (
                    segmentation_output.get(abs_key)
                    or segmentation_output.get(key)
                )
                segmentation_output[key] = (
                    make_generated_url(
                        path_to_convert
                    )
                )

        segmentation_output[
            "available"
        ] = True

        segmentation_output[
            "architecture"
        ] = segmentation_output.get(
            "architecture",
            SEGMENTATION_MODEL_VERSION
        )

        for abs_key in [
            "absolute_leaf_mask_path",
            "absolute_disease_mask_path",
            "absolute_mask_path",
            "absolute_overlay_path",
            "absolute_composite_path",
        ]:
            segmentation_output.pop(abs_key, None)

        segmentation_output["confidence"] = estimate_segmentation_confidence(segmentation_output)
        response["segmentation"] = segmentation_output

    # ========================================================
    # SEVERITY
    # ========================================================

    if segmentation_result is not None:

        try:

            severity_input = response.get("segmentation")

            if not isinstance(severity_input, dict):
                severity_input = dict(segmentation_result)

            severity_input["available"] = True

            # ------------------------------------------------
            # If no crop-compatible disease was identified,
            # do NOT present lesion percentage as confirmed
            # disease severity.
            # ------------------------------------------------

            if disease_validation_status in ("rejected", "skipped_low_crop_confidence"):

                response["severity"] = {
                    "available": False,
                    "affected_area_percent": safe_float(
                        severity_input.get(
                            "affected_percentage"
                        )
                    ),
                    "message": (
                        "Leaf/lesion segmentation was performed, "
                        "but a severity grade was not assigned because "
                        "no crop-compatible disease was validated."
                    ),
                    "diagnostic_warning": (
                        "The segmented affected area must not be "
                        "interpreted as confirmed severity for a "
                        "specific disease without a validated disease "
                        "prediction. Awaiting human review."
                    ),
                    "calibration_required": True
                }

            else:

                severity_result = (
                    analyze_segmentation_result(
                        severity_input
                    )
                )

                if not isinstance(
                    severity_result,
                    dict
                ):

                    severity_result = {
                        "available": False,
                        "message": (
                            "Severity analysis returned "
                            "an invalid result."
                        )
                    }

                # ------------------------------------------
                # Disease-confidence warning
                # ------------------------------------------

                if (
                    disease_confidence is not None
                    and disease_confidence < 50
                ):

                    severity_result[
                        "diagnostic_warning"
                    ] = (
                        "Disease confidence is low. "
                        "The affected-area estimate and "
                        "severity category should not be "
                        "treated as a confirmed disease diagnosis."
                    )

                response["severity"] = severity_result

        except Exception as e:

            print(
                "[WARNING] Severity analysis failed:",
                str(e)
            )

            response["severity"] = {
                "available": False,
                "message": (
                    f"Severity analysis failed: {str(e)}"
                )
            }

    else:

        response["severity"] = {
            "available": False,
            "message": (
                "Severity cannot be calculated "
                "because segmentation is unavailable."
            )
        }

    # ========================================================
    # FINAL RESPONSE STATUS
    # ========================================================

    disease_is_uncertain = (
        disease_confidence is None
        or disease_confidence < 50
        or str(disease_uncertainty).lower() == "high"
    )

    if disease_validation_status == "rejected":

        response["status"] = (
            "uncertain_prediction"
        )

        response["message"] = (
            "The image appears diseased, but the disease "
            "model did not produce a crop-compatible disease "
            "prediction. The result requires human review."
        )

    elif disease_validation_status == "skipped_low_crop_confidence":

        response["status"] = (
            "uncertain_prediction"
        )

        response["message"] = (
            "The image appears diseased, but crop identification confidence "
            "was too low to validate disease candidates. No official disease "
            "prediction was made and the result requires human review."
        )

    elif disease_is_uncertain:

        response["status"] = (
            "uncertain_prediction"
        )

        response["message"] = (
            "The image appears diseased, but the "
            "validated disease prediction has low confidence. "
            "Please upload a clearer image or request "
            "agronomist review."
        )

    else:

        response["status"] = (
            "disease_prediction"
        )

        response["message"] = (
            "The image appears diseased and the "
            "AI generated a disease prediction."
        )

    # ========================================================
    # TRACEABILITY
    # ========================================================

    response["traceability"] = {

        "report_id": report_id,

        "timestamp": timestamp,

        "image_sha256": image_hash,

        "pipeline": (
            "health_classifier_then_"
            "disease_classifier_then_"
            "gradcam_segmentation_severity"
        ),

        "health_model": {
            **HEALTH_MODEL_META,
            "prediction": health_prediction,
            "confidence": health_confidence,
            "predicted_class_idx": health_class_idx
        },

        "crop_model": {
            **CROP_MODEL_META,
            "prediction": inferred_crop,
            "method": crop_method,
            "confidence": (
                (crop_result or {}).get("confidence")
                if isinstance(crop_result, dict)
                else None
            ),
            "uncertain": (
                (crop_result or {}).get("uncertain")
                if isinstance(crop_result, dict)
                else True
            )
        },

        "disease_model": {

            **DISEASE_MODEL_META,

            # Final validated disease prediction.
            "prediction": disease_name,

            "confidence": disease_confidence,

            "uncertainty": disease_uncertainty,

            "predicted_class_idx": (
                disease_class_idx
            ),

            # Raw disease model output.
            "raw_prediction": raw_disease_name,

            "raw_confidence": raw_disease_confidence,

            "raw_predicted_class_idx": raw_disease_class_idx,

            "raw_uncertainty": raw_disease_uncertainty,

            "validation": {
                "status": disease_validation_status,
                "reason": disease_validation_reason,
                "compatible_top_3": compatible_top3,
            }
        },

        "segmentation_model": {

            **SEGMENTATION_MODEL_META,

            "available": (
                segmentation_result is not None
            )
        },

        "evidence": {

            "image_sha256": image_hash,

            "report_id": report_id,

            "timestamp": timestamp
        }
    }

    severity_name = None
    affected_area_percent = None
    if isinstance(response.get("severity"), dict):
        severity_name = response["severity"].get("severity")
        affected_area_percent = safe_float(response["severity"].get("affected_area_percent"))

    add_traceability_block(
        response=response, report_id=report_id, timestamp=timestamp, image_hash=image_hash,
        health_prediction=health_prediction, health_confidence=health_confidence,
        disease_prediction=disease_name, disease_confidence=disease_confidence,
        disease_uncertainty=disease_uncertainty, disease_class_idx=disease_class_idx,
        severity=severity_name, affected_area_percent=affected_area_percent, top_3=top3, actor=user,
    )

    # ========================================================
    # RETURN
    # ========================================================

    return remove_absolute_path_keys(response)



# ============================================================
# TRACEABILITY ENDPOINTS
# ============================================================

@app.get("/traceability/status")
def traceability_status(user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "view_reports")
    return evidence_blockchain.get_chain_info()

@app.get("/traceability/verify")
def verify_traceability(user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "verify_blockchain")
    return evidence_blockchain.verify_chain()

@app.get("/traceability/chain")
def get_traceability_chain(user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "view_reports")
    chain = evidence_blockchain.get_chain()
    return {
        "success": True,
        "chain": remove_absolute_path_keys(chain),
        "verification": evidence_blockchain.verify_chain(),
    }

@app.get("/traceability/report/{report_id}")
def get_traceability_report(report_id: str, user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "view_reports")
    block = evidence_blockchain.find_report(report_id)
    if block is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' was not found in the evidence chain.")

    # 8. Fix report retrieval to aggregate review-resolution blocks
    # 13. Add review history to report reconstruction
    resolutions = [
        b for b in evidence_blockchain.get_chain()
        if b.get("report_id") == report_id and b.get("block_type") == "human_review_resolution"
    ]
    
    if resolutions:
        # Create a deep copy to avoid mutating the original block cache
        block = copy.deepcopy(block)
        ev_data = block.get("data") if "data" in block else block.get("evidence_data")
        if ev_data is None:
            ev_data = {}
            block["data"] = ev_data
        block["evidence_data"] = ev_data
        ev_data["review_history"] = resolutions
        
        # Merge the latest resolution state into the human_review dict for the frontend
        latest_res = resolutions[-1].get("data") or resolutions[-1].get("evidence_data") or {}
        if "human_review" not in ev_data:
            ev_data["human_review"] = {}
            
        ev_data["human_review"]["resolved"] = True
        ev_data["human_review"]["resolution_status"] = latest_res.get("decision")
        ev_data["human_review"]["reviewer"] = latest_res.get("reviewer")
        ev_data["human_review"]["resolution_notes"] = latest_res.get("review_notes")
        ev_data["human_review"]["resolved_at"] = resolutions[-1].get("timestamp")

    return {
        "success": True,
        "report": remove_absolute_path_keys(block),
        "chain_verification": evidence_blockchain.verify_chain(),
    }

# ============================================================
# HUMAN REVIEW ENDPOINTS
# ============================================================

@app.post("/review-queue/submit")
def submit_for_review(payload: Dict[str, Any], user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "scan")
    report_id = payload.get("report_id")
    if not report_id:
        raise HTTPException(status_code=400, detail="report_id is required")
    notes = payload.get("notes", "")
    reasons = payload.get("reasons") or ["user_requested_review"]
    priority = payload.get("priority", "medium")
    summary = payload.get("summary")
    if not summary:
        block = evidence_blockchain.find_report(report_id)
        if block:
            ev_data = block.get("data") or block.get("evidence_data") or {}
            snap = ev_data.get("report_snapshot") or {}
            summary = {
                "health_prediction": snap.get("health_prediction") or ev_data.get("health"),
                "crop_prediction": snap.get("crop_prediction") or ev_data.get("crop"),
                "disease_analysis": snap.get("disease_analysis") or ev_data.get("disease"),
                "segmentation": snap.get("segmentation"),
                "severity": snap.get("severity") or ev_data.get("severity"),
                "notes": notes,
                "submitted_by": user.get("identity", "user"),
            }
        else:
            summary = {"notes": notes, "submitted_by": user.get("identity", "user")}
    sanitized_summary = remove_absolute_path_keys(summary)
    item = review_queue.enqueue(report_id, reasons, priority, sanitized_summary)
    return {"success": True, "message": "Case submitted for expert review", "item": remove_absolute_path_keys(item)}


@app.get("/review-queue")
@app.get("/reviews")
def get_review_queue(status: Optional[str] = None, user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "review_reports")
    items = review_queue.list(status=status)
    return {"success": True, "items": remove_absolute_path_keys(items)}

@app.get("/review-queue/{review_id}")
@app.get("/reviews/{review_id}")
def get_review_item(review_id: str, user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "review_reports")
    item = review_queue.get(review_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Review item not found.")
    return {"success": True, "item": remove_absolute_path_keys(item)}

@app.post("/review-queue/{review_id}/resolve")
@app.post("/reviews/{review_id}/resolve")
def resolve_review_item(review_id: str, payload: Dict[str, Any], user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "review_reports")
    try:
        # reviewer identity is ALWAYS derived from the authenticated credential, never from the client header
        trusted_reviewer_identity = user.get("identity", f"authenticated:{user.get('role', 'reviewer')}")
        item = review_queue.resolve(
            review_id,
            reviewer=trusted_reviewer_identity,
            decision=str(payload.get("decision", "")),
            notes=str(payload.get("notes", "")),
        )
        report_id = item.get("report_id") or review_id
        audit_record = {
            "review_id": review_id,
            "report_id": report_id,
            "event": "human_review_resolution",
            "decision": item.get("decision"),
            "reviewer": trusted_reviewer_identity,          # from auth token — trusted
            "reviewer_role": user.get("role"),              # from auth token — trusted
            "inspector_label": user.get("inspector_label", ""),  # from X-Inspector-ID — display only
            "review_notes": item.get("review_notes"),
            "original_reasons": item.get("reasons"),
            "resolved_at": item.get("updated_at"),
            "actor": {
                "role": user.get("role"),
                "identity": trusted_reviewer_identity,
                "auth_type": user.get("auth_type"),
            },
        }
        review_block = evidence_blockchain.add_block(
            report_id=report_id,
            evidence_data=audit_record,
            block_type="human_review_resolution",
        )
        item["blockchain_block_index"] = review_block["block_index"]
        item["blockchain_current_hash"] = review_block["current_hash"]
    except KeyError:
        raise HTTPException(status_code=404, detail="Review item not found.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "item": remove_absolute_path_keys(item)}


# ============================================================
# MAINTENANCE & CLEANUP
# ============================================================

@app.post("/admin/cleanup")
def trigger_cleanup(max_age_hours: int = 24, user: Dict[str, str] = Depends(require_auth)):
    authorize(user, "all")
    deleted = cleanup_expired_files(max_age_hours=max_age_hours)
    return {
        "success": True,
        "deleted_files_count": deleted,
        "max_age_hours": max_age_hours,
        "message": f"Cleaned up {deleted} files older than {max_age_hours} hours."
    }

# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )