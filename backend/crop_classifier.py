"""Dedicated crop-identification model.

This model performs crop identification independently from the
PlantWild disease classifier.

Pipeline:
    PIL image
        -> EXIF orientation
        -> RGB
        -> 224x224
        -> EfficientNetB0
        -> crop + confidence + Top-3
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR
    / "crop_model"
    / "crop_efficientnetb0.keras"
)

H5_MODEL_PATH = (
    BASE_DIR
    / "crop_model"
    / "crop_efficientnetb0.h5"
)

CLASS_NAMES_PATH = (
    BASE_DIR
    / "crop_model"
    / "crop_class_names.json"
)

MODEL_VERSION = "crop_efficientnetb0"

UNCERTAINTY_THRESHOLD = 60.0

logger = logging.getLogger(__name__)


class CropPredictor:
    """Dedicated EfficientNetB0 crop classifier."""

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        class_names_path: Path = CLASS_NAMES_PATH,
    ):
        if not model_path.exists() and not H5_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Crop model not found: {model_path}"
            )

        if not class_names_path.exists():
            raise FileNotFoundError(
                f"Crop class names not found: {class_names_path}"
            )

        import tensorflow as tf

        load_path = H5_MODEL_PATH if (H5_MODEL_PATH.exists() and tf.__version__.startswith("2.15")) else model_path
        logger.info(
            "Loading crop model from %s",
            load_path,
        )

        try:
            self.model = tf.keras.models.load_model(
                str(load_path),
                compile=False,
            )
        except Exception:
            fallback = H5_MODEL_PATH if load_path != H5_MODEL_PATH else model_path
            if fallback.exists():
                self.model = tf.keras.models.load_model(
                    str(fallback),
                    compile=False,
                )
            else:
                raise

        raw = json.loads(
            class_names_path.read_text(
                encoding="utf-8"
            )
        )

        # ---------------------------------------------------------
        # Support the current metadata format:
        #
        # {
        #   "classes": [...],
        #   "class_to_index": {...},
        #   "index_to_class": {...}
        # }
        #
        # Also support a simple list/dict for compatibility.
        # ---------------------------------------------------------

        if isinstance(raw, dict):

            if isinstance(
                raw.get("index_to_class"),
                dict,
            ):
                self.class_names = {
                    int(index): str(name)
                    for index, name
                    in raw["index_to_class"].items()
                }

            elif isinstance(
                raw.get("classes"),
                list,
            ):
                self.class_names = {
                    index: str(name)
                    for index, name
                    in enumerate(raw["classes"])
                }

            else:
                # Legacy dictionary:
                # {"0": "Apple", "1": "Blueberry", ...}
                try:
                    self.class_names = {
                        int(index): str(name)
                        for index, name in raw.items()
                    }
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "Unsupported crop class metadata format."
                    ) from exc

        elif isinstance(raw, list):

            self.class_names = {
                index: str(name)
                for index, name
                in enumerate(raw)
            }

        else:
            raise ValueError(
                "Unsupported crop class metadata format."
            )

        # ---------------------------------------------------------
        # Validate model output against class metadata
        # ---------------------------------------------------------

        model_output_dim = (
            self.model.output_shape[-1]
        )

        if model_output_dim is None:
            raise ValueError(
                "Crop model output dimension is undefined."
            )

        model_output_dim = int(
            model_output_dim
        )

        if len(self.class_names) != model_output_dim:
            raise ValueError(
                "Crop model/class metadata mismatch: "
                f"model has {model_output_dim} outputs, "
                f"but metadata contains "
                f"{len(self.class_names)} classes."
            )

        expected_indices = set(
            range(model_output_dim)
        )

        actual_indices = set(
            self.class_names.keys()
        )

        if actual_indices != expected_indices:
            raise ValueError(
                "Crop class indices are invalid. "
                f"Expected {sorted(expected_indices)}, "
                f"got {sorted(actual_indices)}."
            )

        # ---------------------------------------------------------
        # Model input validation
        # ---------------------------------------------------------

        input_shape = self.model.input_shape

        if len(input_shape) != 4:
            raise ValueError(
                "Expected crop model input shape "
                "(None, height, width, channels), "
                f"got {input_shape}."
            )

        height = input_shape[1]
        width = input_shape[2]
        channels = input_shape[3]

        if (
            height is None
            or width is None
            or channels != 3
        ):
            raise ValueError(
                "Crop model must accept RGB images with "
                f"fixed spatial dimensions. Got {input_shape}."
            )

        self.input_size = (
            int(width),
            int(height),
        )

        logger.info(
            "Crop model '%s' loaded successfully: "
            "input=%s output=%s classes=%d",
            MODEL_VERSION,
            self.model.input_shape,
            self.model.output_shape,
            len(self.class_names),
        )

    def preprocess_image(
        self,
        image: Image.Image,
    ) -> np.ndarray:
        """Prepare a PIL image for EfficientNetB0."""

        if not isinstance(image, Image.Image):
            raise TypeError(
                "CropPredictor expects a PIL.Image.Image."
            )

        # Apply EXIF orientation before resizing.
        image = ImageOps.exif_transpose(image)

        # Ensure 3-channel RGB.
        image = image.convert("RGB")

        # Resize exactly to model input size.
        image = image.resize(
            self.input_size,
            Image.Resampling.BILINEAR,
        )

        # Keras EfficientNet preprocessing handles
        # float32 pixel values in the 0..255 range.
        array = np.asarray(
            image,
            dtype=np.float32,
        )

        if array.shape != (
            self.input_size[1],
            self.input_size[0],
            3,
        ):
            raise ValueError(
                "Unexpected preprocessed image shape: "
                f"{array.shape}"
            )

        return np.expand_dims(
            array,
            axis=0,
        )

    @staticmethod
    def _to_probabilities(
        output: np.ndarray,
    ) -> np.ndarray:
        """Convert model output to a valid probability vector."""

        output = np.asarray(
            output,
            dtype=np.float64,
        ).reshape(-1)

        if output.size == 0:
            raise ValueError(
                "Crop model returned an empty prediction."
            )

        if not np.all(np.isfinite(output)):
            raise ValueError(
                "Crop model returned NaN or infinite values."
            )

        # The trained model uses softmax, but keep this robust
        # in case the saved model is changed to output logits.
        if (
            np.any(output < 0.0)
            or not np.isclose(
                float(output.sum()),
                1.0,
                atol=1e-3,
            )
        ):
            shifted = (
                output - np.max(output)
            )

            exp_output = np.exp(
                shifted
            )

            denominator = float(
                exp_output.sum()
            )

            if denominator <= 0.0:
                raise ValueError(
                    "Unable to convert crop model output "
                    "to probabilities."
                )

            output = (
                exp_output
                / denominator
            )

        # Numerical safety.
        output = np.clip(
            output,
            0.0,
            1.0,
        )

        total = float(output.sum())

        if total <= 0.0:
            raise ValueError(
                "Crop probability vector sums to zero."
            )

        output = output / total

        return output

    def predict_image(
        self,
        image: Image.Image,
    ) -> dict[str, Any]:
        """Predict crop from a PIL image."""

        array = self.preprocess_image(
            image
        )

        raw_output = self.model.predict(
            array,
            verbose=0,
        )

        probabilities = (
            self._to_probabilities(
                raw_output
            )
        )

        if len(probabilities) != len(
            self.class_names
        ):
            raise ValueError(
                "Prediction output/class metadata "
                "length mismatch."
            )

        order = np.argsort(
            probabilities
        )[::-1]

        top1 = int(order[0])

        confidence = float(
            probabilities[top1] * 100.0
        )

        # Entropy is reported as supporting information,
        # not as a calibrated uncertainty probability.
        entropy = float(
            -np.sum(
                np.clip(
                    probabilities,
                    1e-12,
                    1.0,
                )
                * np.log(
                    np.clip(
                        probabilities,
                        1e-12,
                        1.0,
                    )
                )
            )
        )

        if len(order) > 1:
            top2_margin = float(
                (
                    probabilities[order[0]]
                    - probabilities[order[1]]
                )
                * 100.0
            )
        else:
            top2_margin = 100.0

        top_3 = []

        for rank, index in enumerate(
            order[:3],
            start=1,
        ):
            index = int(index)

            top_3.append(
                {
                    "rank": rank,
                    "class": self.class_names[index],
                    "confidence": round(
                        float(
                            probabilities[index]
                            * 100.0
                        ),
                        4,
                    ),
                    "class_idx": index,
                }
            )

        uncertain = (
            confidence
            < UNCERTAINTY_THRESHOLD
        )

        return {
            "success": True,
            "prediction": self.class_names[top1],
            "predicted_class_idx": top1,
            "confidence": round(
                confidence,
                4,
            ),
            "uncertain": bool(
                uncertain
            ),
            "uncertainty_threshold": (
                UNCERTAINTY_THRESHOLD
            ),
            "entropy": round(
                entropy,
                6,
            ),
            "top2_margin": round(
                top2_margin,
                4,
            ),
            "top_3": top_3,
            "model": MODEL_VERSION,
            "model_input_size": [
                self.input_size[0],
                self.input_size[1],
            ],
            "calibration": {
                "status": "not_calibrated"
            },
        }
