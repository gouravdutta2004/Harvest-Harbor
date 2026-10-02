"""
Configuration settings for Crop Disease AI backend.
Uses environment-independent absolute path resolution based on file location.
"""
import os
import sys
from pathlib import Path

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Pre-configure Keras home directory to prevent PermissionError in sandboxed environments
os.environ.setdefault("KERAS_HOME", str(BASE_DIR / ".keras"))

# Ensure both backend and root directories are in sys.path for flexible imports
for directory in (str(ROOT_DIR), str(BASE_DIR)):
    if directory not in sys.path:
        sys.path.insert(0, directory)

# Model paths
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "plantwild_v2_efficientnetb0.keras"
H5_MODEL_PATH = MODEL_DIR / "plantwild_v2_efficientnetb0.h5"
CLASS_NAMES_PATH = MODEL_DIR / "plantwild_v2_class_names.json"

# Output directories
GENERATED_DIR = BASE_DIR / "generated"
GRADCAM_DIR = GENERATED_DIR / "gradcam"
SEGMENTATION_DIR = GENERATED_DIR / "segmentation"
UPLOADS_DIR = BASE_DIR / "uploads"
SEGMENTATION_MODEL_DIR = BASE_DIR / "segmentation_model"
# Production runtime artifact: TensorFlow SavedModel
SEGMENTATION_MODEL_PATH = SEGMENTATION_MODEL_DIR / "unet_plantseg_savedmodel"
# Source Keras artifact retained for lineage provenance
SEGMENTATION_SOURCE_KERAS_PATH = SEGMENTATION_MODEL_DIR / "unet_plantseg.keras"

# Retention policy for generated output files
MAX_GENERATED_FILE_AGE_HOURS = int(os.getenv("MAX_GENERATED_FILE_AGE_HOURS", "24"))

# Image processing config
IMAGE_SIZE = (224, 224)

# Upload and image safety limits (15 MB, 50 MP, 32x32 min, 10000x10000 max)
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", str(15 * 1024 * 1024)))
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_DECODED_PIXELS = int(os.getenv("MAX_DECODED_PIXELS", "50000000"))
MIN_IMAGE_WIDTH = int(os.getenv("MIN_IMAGE_WIDTH", "32"))
MIN_IMAGE_HEIGHT = int(os.getenv("MIN_IMAGE_HEIGHT", "32"))
MAX_IMAGE_WIDTH = int(os.getenv("MAX_IMAGE_WIDTH", "10000"))
MAX_IMAGE_HEIGHT = int(os.getenv("MAX_IMAGE_HEIGHT", "10000"))

# Model metadata & limitations
MODEL_VERSION = "PlantWild-v2-EfficientNetB0"
HEALTH_STATUS = "diseased_prediction"
HEALTH_STATUS_NOTE = (
    "The current PlantWild v2 classifier contains disease classes and is not a healthy-vs-diseased classifier."
)

# CORS settings
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
env_origins = os.getenv("CORS_ORIGINS")
if env_origins:
    ALLOWED_ORIGINS = [o.strip() for o in env_origins.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = DEFAULT_ORIGINS

