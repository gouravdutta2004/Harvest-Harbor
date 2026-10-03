"""
Healthy vs Diseased classifier.

Model:
    EfficientNetB0

Classes:
    0 -> healthy
    1 -> diseased
"""

import json
import os
from pathlib import Path

# Set KERAS_HOME before any TensorFlow import to avoid PermissionError on
# sandboxed / restricted systems that cannot read ~/.keras/keras.json.
_HP_DIR = Path(__file__).resolve().parent
if "KERAS_HOME" not in os.environ:
    os.environ["KERAS_HOME"] = str(_HP_DIR / ".keras")

import numpy as np
import tensorflow as tf
from PIL import Image

try:
    from calibration import TemperatureScaler
except Exception:
    TemperatureScaler = None


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR
    / "health_model"
    / "health_disease_efficientnetb0.keras"
)

H5_MODEL_PATH = (
    BASE_DIR
    / "health_model"
    / "health_disease_efficientnetb0.h5"
)

CALIBRATION_PATH = (
    BASE_DIR
    / "health_model"
    / "calibration.json"
)

CLASS_NAMES_PATH = (
    BASE_DIR
    / "health_model"
    / "health_disease_class_names.json"
)


class HealthPredictor:

    def __init__(self):

        if not MODEL_PATH.exists() and not H5_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Health model not found: {MODEL_PATH}"
            )

        if not CLASS_NAMES_PATH.exists():
            raise FileNotFoundError(
                f"Class names not found: {CLASS_NAMES_PATH}"
            )

        tf_version = getattr(tf, "__version__", "")
        load_path = H5_MODEL_PATH if (H5_MODEL_PATH.exists() and tf_version.startswith("2.15")) else MODEL_PATH

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
            fallback = H5_MODEL_PATH if load_path != H5_MODEL_PATH else MODEL_PATH
            if fallback.exists():
                self.model = _safe_load(fallback)
            else:
                raise

        with open(
            CLASS_NAMES_PATH,
            "r",
            encoding="utf-8",
        ) as f:

            raw_classes = json.load(f)

        self.class_names = {
            int(k): str(v).lower()
            for k, v in raw_classes.items()
        }

        self.calibrator = None
        self.calibration_status = "not_calibrated"
        if TemperatureScaler is not None and CALIBRATION_PATH.exists():
            try:
                self.calibrator = TemperatureScaler.load(CALIBRATION_PATH)
                self.calibration_status = "temperature_scaled"
            except Exception:
                self.calibrator = None
                self.calibration_status = "invalid_artifact"

        self.input_size = (
            int(self.model.input_shape[1]),
            int(self.model.input_shape[2]),
        )

    def preprocess_image(
        self,
        image: Image.Image,
    ):

        image = image.convert("RGB")

        image = image.resize(
            self.input_size,
            Image.Resampling.BILINEAR,
        )

        image_array = np.asarray(
            image,
            dtype=np.float32,
        )

        image_array = np.expand_dims(
            image_array,
            axis=0,
        )

        return image_array

    def predict_image(
        self,
        image: Image.Image,
    ) -> dict:

        image_array = self.preprocess_image(
            image
        )

        output = self.model.predict(
            image_array,
            verbose=0,
        )

        raw_probability_diseased = float(
            np.asarray(output).reshape(-1)[0]
        )
        probability_diseased = (
            self.calibrator.transform(raw_probability_diseased)
            if self.calibrator is not None
            else raw_probability_diseased
        )

        probability_healthy = (
            1.0 - probability_diseased
        )

        probabilities = {
            "healthy": probability_healthy,
            "diseased": probability_diseased,
        }

        predicted_index = int(
            probability_diseased >= 0.5
        )

        predicted_class = self.class_names.get(
            predicted_index,
            "diseased"
            if predicted_index == 1
            else "healthy",
        )

        confidence = (
            max(probability_healthy, probability_diseased)
            * 100.0
        )

        uncertainty_threshold = 60.0
        uncertain = confidence < uncertainty_threshold

        return {

            "prediction": predicted_class,

            "predicted_class_idx":
                predicted_index,

            "confidence":
                round(confidence, 4),

            "probability_healthy":
                round(
                    probability_healthy * 100.0,
                    4,
                ),

            "probability_diseased":
                round(
                    probability_diseased * 100.0,
                    4,
                ),

            "threshold":
                50.0,

            "uncertainty_threshold":
                uncertainty_threshold,

            "uncertain":
                uncertain,

            "model":
                "health_disease_efficientnetb0",

            "model_input_size":
                list(self.input_size),

            "class_names":
                self.class_names,

            "calibration": {
                "status": self.calibration_status,
                "method": "temperature_scaling" if self.calibrator is not None else None,
                "temperature": getattr(self.calibrator, "temperature", None),
                "raw_probability_diseased": round(raw_probability_diseased * 100.0, 4),
            },
        }


_health_predictor = None


def get_health_predictor():

    global _health_predictor

    if _health_predictor is None:

        _health_predictor = HealthPredictor()

    return _health_predictor
