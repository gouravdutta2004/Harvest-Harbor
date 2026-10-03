"""
PlantWild v2 EfficientNetB0 Disease Classifier

Responsibilities:
- Load PlantWild disease model once
- Preprocess PIL images or file paths
- Perform disease classification
- Return Top-3 predictions
- Return predicted class index
- Return crop and disease
- Calculate confidence
- Calculate uncertainty
- Provide field names compatible with app.py
- Remain compatible with Grad-CAM
"""

import json
import logging
import sys
import threading

from pathlib import Path
from typing import Dict, Any, Union

import numpy as np
from PIL import Image, ImageOps

# ============================================================
# PATH CONFIGURATION
# ============================================================

_BASE_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _BASE_DIR.parent

for directory in (
    str(_ROOT_DIR),
    str(_BASE_DIR)
):
    if directory not in sys.path:
        sys.path.insert(0, directory)


# ============================================================
# CONFIG IMPORT
# ============================================================

try:

    from backend.config import (
        MODEL_PATH,
        H5_MODEL_PATH,
        CLASS_NAMES_PATH,
        IMAGE_SIZE,
        MODEL_VERSION,
        HEALTH_STATUS,
        HEALTH_STATUS_NOTE,
    )

    from backend.utils import (
        extract_crop_and_disease,
        calculate_uncertainty,
    )

except ImportError:

    from config import (
        MODEL_PATH,
        H5_MODEL_PATH,
        CLASS_NAMES_PATH,
        IMAGE_SIZE,
        MODEL_VERSION,
        HEALTH_STATUS,
        HEALTH_STATUS_NOTE,
    )

    from utils import (
        extract_crop_and_disease,
        calculate_uncertainty,
    )


# ============================================================
# TENSORFLOW
# ============================================================

# Guard: ensure KERAS_HOME is set before tensorflow is imported
# (config.py sets it, but protect standalone usage too)
import os as _os
if "KERAS_HOME" not in _os.environ:
    _os.environ["KERAS_HOME"] = str(_BASE_DIR / ".keras")

import tensorflow as tf


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# PLANT PREDICTOR
# ============================================================

class PlantPredictor:

    _instance = None
    _lock = threading.Lock()

    # ========================================================
    # SINGLETON
    # ========================================================

    def __new__(cls):

        if cls._instance is None:

            with cls._lock:

                if cls._instance is None:

                    cls._instance = super(
                        PlantPredictor,
                        cls
                    ).__new__(cls)

                    cls._instance._load_model()

        return cls._instance

    # ========================================================
    # LOAD MODEL
    # ========================================================

    def _load_model(self) -> None:
        """
        Load the PlantWild Keras model and class names.

        The model is loaded only once.
        """

        model_path = Path(
            MODEL_PATH
        )

        class_names_path = Path(
            CLASS_NAMES_PATH
        )

        # ----------------------------------------------------
        # Model existence
        # ----------------------------------------------------

        if not model_path.exists() and not H5_MODEL_PATH.exists():

            raise FileNotFoundError(
                f"Model file not found at: {model_path}"
            )

        # ----------------------------------------------------
        # Class names existence
        # ----------------------------------------------------

        if not class_names_path.exists():

            raise FileNotFoundError(
                "Class names file not found at: "
                f"{class_names_path}"
            )

        # ----------------------------------------------------
        # Load Keras model
        # ----------------------------------------------------

        tf_version = getattr(tf, "__version__", "")
        load_path = H5_MODEL_PATH if (H5_MODEL_PATH.exists() and tf_version.startswith("2.15")) else model_path

        logger.info(
            "Loading PlantWild model from %s...",
            load_path
        )

        def _safe_load(filepath):
            models_mod = getattr(getattr(tf, "keras", None), "models", None)
            if models_mod is None or not hasattr(models_mod, "load_model"):
                try:
                    from tensorflow import keras
                    models_mod = keras.models
                except Exception:
                    try:
                        import keras
                        models_mod = keras.models
                    except Exception:
                        pass
            if models_mod is not None and hasattr(models_mod, "load_model"):
                return models_mod.load_model(str(filepath), compile=False)
            return tf.keras.models.load_model(str(filepath), compile=False)

        try:
            self.model = _safe_load(load_path)
        except Exception:
            fallback = H5_MODEL_PATH if load_path != H5_MODEL_PATH else model_path
            if fallback.exists():
                self.model = _safe_load(fallback)
            else:
                raise

        # ----------------------------------------------------
        # Load class names
        # ----------------------------------------------------

        with open(
            class_names_path,
            "r",
            encoding="utf-8"
        ) as f:

            loaded_class_names = json.load(f)

        # ----------------------------------------------------
        # Normalize class names
        #
        # JSON can be either:
        #
        # {
        #   "0": "class A",
        #   "1": "class B"
        # }
        #
        # OR:
        #
        # [
        #   "class A",
        #   "class B"
        # ]
        # ----------------------------------------------------

        if isinstance(
            loaded_class_names,
            dict
        ):

            class_names = []

            output_dim = int(
                self.model.output_shape[-1]
            )

            for i in range(output_dim):

                class_name = (
                    loaded_class_names.get(
                        str(i)
                    )
                )

                if class_name is None:

                    class_name = (
                        loaded_class_names.get(i)
                    )

                if class_name is None:

                    raise ValueError(
                        "Missing class name for "
                        f"class index {i}"
                    )

                class_names.append(
                    str(class_name)
                )

            self.class_names = class_names

        elif isinstance(
            loaded_class_names,
            list
        ):

            self.class_names = [
                str(x)
                for x in loaded_class_names
            ]

        else:

            raise ValueError(
                "Class names JSON must contain "
                "either a dictionary or list."
            )

        # ----------------------------------------------------
        # Validate model output
        # ----------------------------------------------------

        model_output_dim = (
            self.model.output_shape[-1]
        )

        if len(self.class_names) != model_output_dim:

            raise ValueError(
                "Class names count mismatch: "
                f"JSON contains {len(self.class_names)} "
                f"classes, but model output shape has "
                f"{model_output_dim} outputs."
            )

        # ----------------------------------------------------
        # Log success
        # ----------------------------------------------------

        logger.info(
            "Successfully loaded model '%s' "
            "with %d classes.",
            MODEL_VERSION,
            len(self.class_names)
        )

    # ========================================================
    # PREPROCESS IMAGE
    # ========================================================

    def preprocess_image(
        self,
        image_input: Union[
            str,
            Path,
            Image.Image
        ]
    ) -> np.ndarray:
        """
        Preprocess image for EfficientNetB0.

        Steps:
        1. Open image if path is supplied
        2. Apply EXIF orientation
        3. Convert to RGB
        4. Resize to IMAGE_SIZE
        5. Convert to float32
        6. Keep pixel range [0,255]
        7. Add batch dimension
        """

        # ----------------------------------------------------
        # File path input
        # ----------------------------------------------------

        if isinstance(
            image_input,
            (str, Path)
        ):

            with Image.open(
                image_input
            ) as img:

                img_oriented = (
                    ImageOps.exif_transpose(
                        img
                    )
                )

                img_rgb = (
                    img_oriented.convert(
                        "RGB"
                    )
                )

        # ----------------------------------------------------
        # PIL image input
        # ----------------------------------------------------

        elif isinstance(
            image_input,
            Image.Image
        ):

            img_oriented = (
                ImageOps.exif_transpose(
                    image_input
                )
            )

            img_rgb = (
                img_oriented.convert(
                    "RGB"
                )
            )

        # ----------------------------------------------------
        # Invalid input
        # ----------------------------------------------------

        else:

            raise ValueError(
                "Unsupported image input type. "
                "Expected file path or PIL Image."
            )

        # ----------------------------------------------------
        # Resize
        # ----------------------------------------------------

        img_resized = img_rgb.resize(
            IMAGE_SIZE,
            Image.Resampling.BILINEAR
        )

        # ----------------------------------------------------
        # NumPy conversion
        # ----------------------------------------------------

        img_array = np.asarray(
            img_resized,
            dtype=np.float32
        )

        # ----------------------------------------------------
        # Batch dimension
        # ----------------------------------------------------

        img_batch = np.expand_dims(
            img_array,
            axis=0
        )

        return img_batch

    # ========================================================
    # NORMALIZE MODEL OUTPUT
    # ========================================================

    def _get_probabilities(
        self,
        raw_outputs: np.ndarray
    ) -> np.ndarray:
        """
        Convert model output into a valid probability vector.

        Supports:
        - logits
        - probabilities
        """

        raw_outputs = np.asarray(
            raw_outputs,
            dtype=np.float32
        )

        raw_outputs = np.nan_to_num(
            raw_outputs,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

        # ----------------------------------------------------
        # If values already behave like probabilities
        # ----------------------------------------------------

        total = float(
            np.sum(raw_outputs)
        )

        if (
            np.all(raw_outputs >= 0.0)
            and np.all(raw_outputs <= 1.0)
            and np.isclose(
                total,
                1.0,
                atol=1e-2
            )
        ):

            probabilities = raw_outputs

        # ----------------------------------------------------
        # Otherwise use softmax
        # ----------------------------------------------------

        else:

            probabilities = (
                tf.nn.softmax(
                    raw_outputs
                ).numpy()
            )

        # ----------------------------------------------------
        # Final cleanup
        # ----------------------------------------------------

        probabilities = np.nan_to_num(
            probabilities,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

        # ----------------------------------------------------
        # Ensure sum = 1
        # ----------------------------------------------------

        probability_sum = float(
            np.sum(probabilities)
        )

        if probability_sum <= 0:

            probabilities = np.ones_like(
                probabilities,
                dtype=np.float32
            )

            probabilities /= (
                len(probabilities)
            )

        else:

            probabilities = (
                probabilities
                / probability_sum
            )

        return probabilities

    # ========================================================
    # PREDICT IMAGE
    # ========================================================

    def predict_image(
        self,
        image_input: Union[
            str,
            Path,
            Image.Image
        ]
    ) -> Dict[str, Any]:
        """
        Perform PlantWild disease classification.

        Returns:

        prediction
        predicted_class_idx
        confidence
        uncertainty
        crop
        disease
        top_3
        raw_prediction
        top_class_idx
        model_version
        health status
        """

        # ====================================================
        # PREPROCESS
        # ====================================================

        img_batch = (
            self.preprocess_image(
                image_input
            )
        )

        # ====================================================
        # MODEL INFERENCE
        # ====================================================

        raw_outputs = (
            self.model(
                img_batch,
                training=False
            ).numpy()[0]
        )

        # ====================================================
        # PROBABILITIES
        # ====================================================

        probabilities = (
            self._get_probabilities(
                raw_outputs
            )
        )

        # ====================================================
        # TOP-3 INDEXES
        # ====================================================

        top_indices = (
            np.argsort(
                probabilities
            )[::-1][:3]
        )

        # ====================================================
        # TOP-3 RESULTS
        # ====================================================

        top_3 = []

        for rank, idx in enumerate(
            top_indices,
            start=1
        ):

            idx = int(idx)

            class_name = (
                self.class_names[idx]
            )

            score = float(
                probabilities[idx] * 100.0
            )

            score = round(
                score,
                2
            )

            top_3.append({

                "rank": rank,

                "class": class_name,

                "score": score,

                # Compatible field
                # for app.py
                "confidence": score,

                "class_idx": idx
            })

        # ====================================================
        # TOP-1
        # ====================================================

        top_1 = top_3[0]

        top_class_idx = int(
            top_1["class_idx"]
        )

        raw_prediction = str(
            top_1["class"]
        )

        confidence = float(
            top_1["score"]
        )

        # ====================================================
        # UNCERTAINTY
        # ====================================================

        uncertainty = (
            calculate_uncertainty(
                confidence
            )
        )

        # ====================================================
        # CROP + DISEASE
        # ====================================================

        try:

            crop, disease = (
                extract_crop_and_disease(
                    raw_prediction
                )
            )

        except Exception:

            crop = None
            disease = raw_prediction

        # ====================================================
        # RESULT
        # ====================================================

        result = {

            "success": True,

            # ------------------------------------------------
            # Model
            # ------------------------------------------------

            "model_version": (
                MODEL_VERSION
            ),

            # ------------------------------------------------
            # Main prediction fields
            # ------------------------------------------------

            "prediction": raw_prediction,

            "predicted_class": raw_prediction,

            "predicted_class_idx": (
                top_class_idx
            ),

            "confidence": confidence,

            "uncertainty": uncertainty,

            # ------------------------------------------------
            # Crop / disease
            # ------------------------------------------------

            "crop": crop,

            "disease": disease,

            # ------------------------------------------------
            # Original compatibility fields
            # ------------------------------------------------

            "raw_prediction": (
                raw_prediction
            ),

            "top_class_idx": (
                top_class_idx
            ),

            # ------------------------------------------------
            # Health information
            # ------------------------------------------------

            "health_status": (
                HEALTH_STATUS
            ),

            "health_status_note": (
                HEALTH_STATUS_NOTE
            ),

            # ------------------------------------------------
            # Top-3
            # ------------------------------------------------

            "top_3": top_3,

            # ------------------------------------------------
            # Alias expected by app.py
            # ------------------------------------------------

            "top3": top_3,

            # ------------------------------------------------
            # Complete 115-class probability distribution
            # ------------------------------------------------

            "probabilities": probabilities.tolist(),

            "class_names": list(self.class_names)
        }

        # ====================================================
        # LOW CONFIDENCE MESSAGE
        # ====================================================

        if uncertainty == "High":

            result["message"] = (
                "Please upload a clearer image."
            )

        else:

            result["message"] = (
                "Disease prediction generated successfully."
            )

        # ====================================================
        # RETURN
        # ====================================================

        return result


# ============================================================
# GLOBAL PREDICTOR
# ============================================================

def get_predictor() -> PlantPredictor:

    return PlantPredictor()