"""
Disease Segmentation Module
----------------------------

Pipeline:
1. Load trained U-Net model.
2. Detect leaf foreground using HSV + Lab.
3. Predict disease/lesion pixels using U-Net.
4. Restrict disease prediction to the leaf region.
5. Calculate affected-area ratio.
6. Generate:
   - disease mask
   - leaf mask
   - disease overlay
   - composite visualization

The trained U-Net is a DISEASE/LESION segmentation model.
It is NOT a leaf-segmentation model.

Production runtime:
- TensorFlow 2.15
- TensorFlow SavedModel exported from the original
  Keras 3 U-Net model.
"""

from pathlib import Path
from typing import Dict, Any
import logging
import uuid

import cv2
import numpy as np
from PIL import Image


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# Production TensorFlow SavedModel runtime.
#
# This artifact was exported from:
#   unet_plantseg.keras
#
# and verified under:
#   TensorFlow 2.15.0
#
# Input:
#   (None, 256, 256, 3)
#
# Output:
#   (None, 256, 256, 1)
SEGMENTATION_SAVEDMODEL_PATH = (
    BASE_DIR
    / "segmentation_model"
    / "unet_plantseg_savedmodel"
)

# Authoritative production segmentation runtime path
SEGMENTATION_MODEL_PATH = SEGMENTATION_SAVEDMODEL_PATH

# Original Keras model kept as the source/conversion lineage artifact.
SEGMENTATION_SOURCE_KERAS_PATH = (
    BASE_DIR
    / "segmentation_model"
    / "unet_plantseg.keras"
)

# Legacy H5 artifact.
# Kept for archival purposes but NOT used by the production
# runtime because it is incompatible with the current runtime.
SEGMENTATION_MODEL_H5_PATH = (
    BASE_DIR
    / "segmentation_model"
    / "unet_plantseg.h5"
)

SEGMENTATION_DIR = (
    BASE_DIR
    / "generated"
    / "segmentation"
)

SEGMENTATION_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# LEAF SEGMENTER
# ============================================================

class LeafSegmenter:
    """
    Handles:

    - leaf foreground estimation
    - disease/lesion segmentation
    - U-Net inference
    - visualization generation

    The U-Net is a disease/lesion segmentation model.
    Leaf foreground detection is performed separately using
    HSV + Lab heuristics.
    """

    def __init__(self):
        # TensorFlow SavedModel object.
        self.unet_model = None

        # Callable SavedModel signature.
        self.unet_infer = None

        self.architecture_name = (
            "HSV/Lab Adaptive Segmenter"
        )

        # Verified production U-Net input dimensions.
        self.model_input_height = 256
        self.model_input_width = 256

        self._try_load_unet()

    # ========================================================
    # LOAD U-NET
    # ========================================================

    def _try_load_unet(self) -> None:
        """
        Load the production U-Net TensorFlow SavedModel.

        The original U-Net was saved in Keras 3 format.
        The production environment uses TensorFlow 2.15,
        therefore the verified SavedModel export is used here.

        Expected signature:

        Input:
            input_layer
            shape = (None, 256, 256, 3)
            dtype = float32

        Output:
            output_0
            shape = (None, 256, 256, 1)
            dtype = float32
        """

        # ----------------------------------------------------
        # Require production SavedModel
        # ----------------------------------------------------

        if not SEGMENTATION_SAVEDMODEL_PATH.exists():
            logger.warning(
                "U-Net SavedModel not found at: "
                f"{SEGMENTATION_SAVEDMODEL_PATH}"
            )

            logger.warning(
                "Falling back to HSV/Lab segmentation."
            )

            self.unet_model = None
            self.unet_infer = None

            return

        try:
            import tensorflow as tf

            logger.info(
                "Loading U-Net SavedModel from: "
                f"{SEGMENTATION_SAVEDMODEL_PATH}"
            )

            # ------------------------------------------------
            # Load SavedModel
            # ------------------------------------------------

            self.unet_model = tf.saved_model.load(
                str(SEGMENTATION_SAVEDMODEL_PATH)
            )

            # ------------------------------------------------
            # Validate required signature
            # ------------------------------------------------

            if "serve" not in self.unet_model.signatures:
                raise RuntimeError(
                    "U-Net SavedModel does not contain "
                    "the required 'serve' signature."
                )

            self.unet_infer = (
                self.unet_model.signatures["serve"]
            )

            # ------------------------------------------------
            # Validate input signature
            # ------------------------------------------------

            input_signature = (
                self.unet_infer
                .structured_input_signature
            )

            input_kwargs = input_signature[1]

            if "input_layer" not in input_kwargs:
                raise RuntimeError(
                    "U-Net SavedModel does not expose "
                    "the expected 'input_layer' input."
                )

            input_spec = input_kwargs["input_layer"]

            if input_spec.shape.rank != 4:
                raise RuntimeError(
                    "Unexpected U-Net input rank: "
                    f"{input_spec.shape}"
                )

            if input_spec.shape[1] is None:
                raise RuntimeError(
                    "U-Net input height is undefined."
                )

            if input_spec.shape[2] is None:
                raise RuntimeError(
                    "U-Net input width is undefined."
                )

            if input_spec.shape[3] != 3:
                raise RuntimeError(
                    "Expected U-Net RGB input with 3 channels, "
                    f"got: {input_spec.shape}"
                )

            self.model_input_height = int(
                input_spec.shape[1]
            )

            self.model_input_width = int(
                input_spec.shape[2]
            )

            # ------------------------------------------------
            # Validate output signature
            # ------------------------------------------------

            output_signature = (
                self.unet_infer
                .structured_outputs
            )

            if "output_0" not in output_signature:
                raise RuntimeError(
                    "U-Net SavedModel does not expose "
                    "the expected 'output_0' output."
                )

            output_spec = output_signature["output_0"]

            if output_spec.shape.rank != 4:
                raise RuntimeError(
                    "Unexpected U-Net output rank: "
                    f"{output_spec.shape}"
                )

            if output_spec.shape[-1] != 1:
                raise RuntimeError(
                    "Expected one-channel U-Net output, "
                    f"got: {output_spec.shape}"
                )

            # ------------------------------------------------
            # Production architecture
            # ------------------------------------------------

            self.architecture_name = (
                "U-Net (Deep Learning Segmentation)"
            )

            logger.info(
                "U-Net SavedModel loaded successfully."
            )

            logger.info(
                "Model input size: "
                f"{self.model_input_width}x"
                f"{self.model_input_height}"
            )

            logger.info(
                "Model output shape: "
                f"{output_spec.shape}"
            )

            logger.info(
                "Available SavedModel signatures: "
                f"{list(self.unet_model.signatures.keys())}"
            )

        except Exception as err:

            logger.warning(
                "Failed to load U-Net SavedModel: "
                f"{err}"
            )

            logger.warning(
                "Falling back to HSV/Lab segmentation."
            )

            self.unet_model = None
            self.unet_infer = None

    # ========================================================
    # MAIN SEGMENTATION FUNCTION
    # ========================================================

    def segment_image(
        self,
        original_img: Image.Image
    ) -> Dict[str, Any]:
        """
        Run complete segmentation pipeline.

        Returns:
            Dictionary containing:

            - architecture
            - total pixels
            - leaf pixels
            - diseased pixels
            - affected ratio
            - affected percentage
            - mask path
            - leaf mask path
            - overlay path
            - composite path
        """

        # ----------------------------------------------------
        # Validate input
        # ----------------------------------------------------

        if not isinstance(
            original_img,
            Image.Image
        ):
            raise TypeError(
                "segment_image() expects a PIL.Image.Image."
            )

        # ----------------------------------------------------
        # Convert PIL -> RGB NumPy
        # ----------------------------------------------------

        img_rgb = np.array(
            original_img.convert("RGB")
        )

        if img_rgb.ndim != 3:
            raise ValueError(
                "Input image must have 3 dimensions "
                "(height, width, channels)."
            )

        if img_rgb.shape[2] != 3:
            raise ValueError(
                "Input image must contain exactly "
                "3 RGB channels."
            )

        height, width, _ = img_rgb.shape

        total_pixels = height * width

        logger.info(
            f"Processing image: "
            f"{width}x{height}"
        )

        # ====================================================
        # STEP 1 — LEAF FOREGROUND
        # ====================================================

        leaf_mask = self._extract_leaf_mask(
            img_rgb
        )

        leaf_pixels = int(
            np.count_nonzero(leaf_mask)
        )

        # ----------------------------------------------------
        # Fallback if leaf detection fails
        # ----------------------------------------------------

        if leaf_pixels == 0:

            logger.warning(
                "No leaf foreground detected. "
                "Using complete image as foreground."
            )

            leaf_mask = (
                np.ones(
                    (height, width),
                    dtype=np.uint8
                ) * 255
            )

            leaf_pixels = total_pixels

        # ====================================================
        # STEP 2 — DISEASE SEGMENTATION
        # ====================================================

        diseased_mask = (
            self._extract_diseased_mask(
                img_rgb,
                leaf_mask
            )
        )

        diseased_pixels = int(
            np.count_nonzero(diseased_mask)
        )

        # ====================================================
        # STEP 3 — AFFECTED AREA
        # ====================================================

        affected_ratio = (
            diseased_pixels /
            max(leaf_pixels, 1)
        )

        affected_percentage = (
            affected_ratio * 100.0
        )

        affected_ratio = round(
            float(affected_ratio),
            4
        )

        affected_percentage = round(
            float(affected_percentage),
            2
        )

        logger.info(
            f"Leaf pixels: {leaf_pixels}"
        )

        logger.info(
            f"Diseased pixels: {diseased_pixels}"
        )

        logger.info(
            f"Affected area: "
            f"{affected_percentage:.2f}%"
        )

        # ====================================================
        # STEP 4 — GENERATE FILE NAMES
        # ====================================================

        unique_id = uuid.uuid4().hex[:8]

        leaf_mask_filename = (
            f"segmentation_{unique_id}_leaf_mask.png"
        )

        disease_mask_filename = (
            f"segmentation_{unique_id}_disease_mask.png"
        )

        overlay_filename = (
            f"segmentation_{unique_id}_overlay.jpg"
        )

        composite_filename = (
            f"segmentation_{unique_id}_composite.jpg"
        )

        # ====================================================
        # STEP 5 — FILE PATHS
        # ====================================================

        leaf_mask_path = (
            SEGMENTATION_DIR /
            leaf_mask_filename
        )

        disease_mask_path = (
            SEGMENTATION_DIR /
            disease_mask_filename
        )

        overlay_path = (
            SEGMENTATION_DIR /
            overlay_filename
        )

        composite_path = (
            SEGMENTATION_DIR /
            composite_filename
        )

        # ====================================================
        # STEP 6 — SAVE LEAF MASK
        # ====================================================

        cv2.imwrite(
            str(leaf_mask_path),
            leaf_mask
        )

        # ====================================================
        # STEP 7 — SAVE DISEASE MASK
        # ====================================================

        cv2.imwrite(
            str(disease_mask_path),
            diseased_mask
        )

        # ====================================================
        # STEP 8 — CREATE OVERLAY
        # ====================================================

        overlay_rgb = (
            self._create_overlay_image(
                img_rgb,
                leaf_mask,
                diseased_mask
            )
        )

        Image.fromarray(
            overlay_rgb
        ).save(
            overlay_path,
            quality=95
        )

        # ====================================================
        # STEP 9 — CREATE COMPOSITE
        # ====================================================

        composite_rgb = (
            self._create_composite_image(
                img_rgb,
                leaf_mask,
                diseased_mask,
                overlay_rgb
            )
        )

        Image.fromarray(
            composite_rgb
        ).save(
            composite_path,
            quality=95
        )

        # ====================================================
        # RELATIVE PATHS
        # ====================================================

        relative_leaf_mask = (
            f"generated/segmentation/"
            f"{leaf_mask_filename}"
        )

        relative_disease_mask = (
            f"generated/segmentation/"
            f"{disease_mask_filename}"
        )

        relative_overlay = (
            f"generated/segmentation/"
            f"{overlay_filename}"
        )

        relative_composite = (
            f"generated/segmentation/"
            f"{composite_filename}"
        )

        # ====================================================
        # RETURN RESULT
        # ====================================================

        return {

            "available": True,

            "architecture": (
                self.architecture_name
            ),

            "model_input_size": (
                f"{self.model_input_width}x"
                f"{self.model_input_height}"
            ),

            "total_pixels": total_pixels,

            "leaf_pixels": leaf_pixels,

            "diseased_pixels": diseased_pixels,

            "affected_ratio": affected_ratio,

            "affected_percentage": (
                affected_percentage
            ),

            "leaf_mask_path": (
                relative_leaf_mask
            ),

            "mask_path": (
                relative_disease_mask
            ),

            "disease_mask_path": (
                relative_disease_mask
            ),

            "overlay_path": (
                relative_overlay
            ),

            "composite_path": (
                relative_composite
            ),

            "absolute_leaf_mask_path": (
                str(leaf_mask_path)
            ),

            "absolute_mask_path": (
                str(disease_mask_path)
            ),

            "absolute_disease_mask_path": (
                str(disease_mask_path)
            ),

            "absolute_overlay_path": (
                str(overlay_path)
            ),

            "absolute_composite_path": (
                str(composite_path)
            ),
        }

    # ========================================================
    # LEAF MASK
    # ========================================================

    def _extract_leaf_mask(
        self,
        img_rgb: np.ndarray
    ) -> np.ndarray:
        """
        Estimate leaf foreground using HSV + Lab.

        This is a heuristic foreground mask.
        It is NOT a trained leaf segmentation model.
        """

        # ----------------------------------------------------
        # RGB -> BGR
        # ----------------------------------------------------

        img_bgr = cv2.cvtColor(
            img_rgb,
            cv2.COLOR_RGB2BGR
        )

        # ----------------------------------------------------
        # BGR -> HSV
        # ----------------------------------------------------

        hsv = cv2.cvtColor(
            img_bgr,
            cv2.COLOR_BGR2HSV
        )

        # ----------------------------------------------------
        # BGR -> Lab
        # ----------------------------------------------------

        lab = cv2.cvtColor(
            img_bgr,
            cv2.COLOR_BGR2Lab
        )

        # ====================================================
        # GREEN / YELLOW VEGETATION
        # ====================================================

        lower_green = np.array(
            [20, 30, 20]
        )

        upper_green = np.array(
            [95, 255, 255]
        )

        mask_hsv = cv2.inRange(
            hsv,
            lower_green,
            upper_green
        )

        # ====================================================
        # LAB GREENNESS
        # ====================================================

        a_channel = lab[:, :, 1]

        _, mask_lab = cv2.threshold(
            a_channel,
            124,
            255,
            cv2.THRESH_BINARY_INV
        )

        # ====================================================
        # COMBINE
        # ====================================================

        combined = cv2.bitwise_or(
            mask_hsv,
            mask_lab
        )

        # ====================================================
        # MORPHOLOGICAL CLEANING
        # ====================================================

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (5, 5)
        )

        morph = cv2.morphologyEx(
            combined,
            cv2.MORPH_CLOSE,
            kernel,
            iterations=2
        )

        morph = cv2.morphologyEx(
            morph,
            cv2.MORPH_OPEN,
            kernel,
            iterations=1
        )

        # ====================================================
        # FIND CONTOURS
        # ====================================================

        contours, _ = cv2.findContours(
            morph,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        mask_clean = np.zeros_like(
            morph
        )

        if contours:

            image_area = (
                img_rgb.shape[0] *
                img_rgb.shape[1]
            )

            # ------------------------------------------------
            # Ignore extremely small regions
            # ------------------------------------------------

            valid_contours = [
                contour
                for contour in contours
                if cv2.contourArea(contour)
                > image_area * 0.01
            ]

            if valid_contours:

                cv2.drawContours(
                    mask_clean,
                    valid_contours,
                    -1,
                    255,
                    thickness=cv2.FILLED
                )

            else:

                largest = max(
                    contours,
                    key=cv2.contourArea
                )

                cv2.drawContours(
                    mask_clean,
                    [largest],
                    -1,
                    255,
                    thickness=cv2.FILLED
                )

        else:

            mask_clean = morph

        return mask_clean

    # ========================================================
    # DISEASE MASK
    # ========================================================

    def _extract_diseased_mask(
        self,
        img_rgb: np.ndarray,
        leaf_mask: np.ndarray
    ) -> np.ndarray:
        """
        Predict disease/lesion pixels using trained U-Net.

        Production inference uses the TensorFlow SavedModel.

        The current trained model uses:

            256 x 256 x 3

        This function reads the dimensions from the
        SavedModel signature.
        """

        height, width, _ = img_rgb.shape

        # ====================================================
        # U-NET INFERENCE
        # ====================================================

        if (
            self.unet_model is not None
            and self.unet_infer is not None
        ):

            try:

                # ------------------------------------------------
                # Read model input dimensions
                # ------------------------------------------------

                model_height = (
                    self.model_input_height
                )

                model_width = (
                    self.model_input_width
                )

                logger.info(
                    f"U-Net inference input size: "
                    f"{model_width}x{model_height}"
                )

                # ------------------------------------------------
                # Resize image
                # ------------------------------------------------

                img_resized = cv2.resize(
                    img_rgb,
                    (
                        model_width,
                        model_height
                    ),
                    interpolation=cv2.INTER_AREA
                )

                # ------------------------------------------------
                # Normalize 0-255 -> 0-1
                # ------------------------------------------------

                img_input = (
                    img_resized.astype(
                        np.float32
                    ) / 255.0
                )

                # ------------------------------------------------
                # Add batch dimension
                # ------------------------------------------------

                img_batch = np.expand_dims(
                    img_input,
                    axis=0
                )

                # ------------------------------------------------
                # U-Net SavedModel prediction
                # ------------------------------------------------

                import tensorflow as tf

                prediction = self.unet_infer(
                    input_layer=tf.constant(
                        img_batch,
                        dtype=tf.float32
                    )
                )

                # ------------------------------------------------
                # Validate prediction output
                # ------------------------------------------------

                if "output_0" not in prediction:
                    raise RuntimeError(
                        "U-Net inference did not return "
                        "the expected 'output_0' tensor."
                    )

                # ------------------------------------------------
                # Tensor -> NumPy
                # ------------------------------------------------

                pred_prob = (
                    prediction["output_0"]
                    .numpy()
                    [0, :, :, 0]
                )

                # ------------------------------------------------
                # Validate prediction
                # ------------------------------------------------

                if not np.isfinite(
                    pred_prob
                ).all():
                    raise RuntimeError(
                        "U-Net prediction contains "
                        "NaN or infinite values."
                    )

                # ------------------------------------------------
                # Probability -> binary mask
                #
                # 0.5 = existing threshold
                # ------------------------------------------------

                pred_binary = (
                    pred_prob > 0.5
                ).astype(
                    np.uint8
                ) * 255

                # ------------------------------------------------
                # Resize to original image
                # ------------------------------------------------

                disease_mask = cv2.resize(
                    pred_binary,
                    (
                        width,
                        height
                    ),
                    interpolation=cv2.INTER_NEAREST
                )

                # ------------------------------------------------
                # Keep disease only inside leaf
                # ------------------------------------------------

                disease_mask = (
                    cv2.bitwise_and(
                        leaf_mask,
                        disease_mask
                    )
                )

                # ------------------------------------------------
                # Remove tiny noise
                # ------------------------------------------------

                kernel = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE,
                    (3, 3)
                )

                disease_mask = (
                    cv2.morphologyEx(
                        disease_mask,
                        cv2.MORPH_OPEN,
                        kernel,
                        iterations=1
                    )
                )

                return disease_mask

            except Exception as error:

                logger.warning(
                    f"U-Net inference error: "
                    f"{error}"
                )

                logger.warning(
                    "Falling back to HSV/Lab "
                    "disease segmentation."
                )

        # ====================================================
        # FALLBACK COLOR SEGMENTATION
        # ====================================================

        img_bgr = cv2.cvtColor(
            img_rgb,
            cv2.COLOR_RGB2BGR
        )

        hsv = cv2.cvtColor(
            img_bgr,
            cv2.COLOR_BGR2HSV
        )

        # ====================================================
        # YELLOW / CHLOROTIC REGIONS
        # ====================================================

        lower_yellow = np.array(
            [15, 40, 40]
        )

        upper_yellow = np.array(
            [40, 255, 255]
        )

        mask_yellow = cv2.inRange(
            hsv,
            lower_yellow,
            upper_yellow
        )

        # ====================================================
        # BROWN / NECROTIC REGIONS
        # ====================================================

        lower_brown = np.array(
            [0, 30, 20]
        )

        upper_brown = np.array(
            [34, 255, 220]
        )

        mask_brown = cv2.inRange(
            hsv,
            lower_brown,
            upper_brown
        )

        # ====================================================
        # COMBINE DISEASE COLORS
        # ====================================================

        disease_combined = (
            cv2.bitwise_or(
                mask_yellow,
                mask_brown
            )
        )

        # ====================================================
        # KEEP INSIDE LEAF
        # ====================================================

        disease_combined = (
            cv2.bitwise_and(
                leaf_mask,
                disease_combined
            )
        )

        # ====================================================
        # REMOVE NOISE
        # ====================================================

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (3, 3)
        )

        disease_clean = (
            cv2.morphologyEx(
                disease_combined,
                cv2.MORPH_OPEN,
                kernel,
                iterations=1
            )
        )

        return disease_clean

    # ========================================================
    # OVERLAY
    # ========================================================

    def _create_overlay_image(
        self,
        img_rgb: np.ndarray,
        leaf_mask: np.ndarray,
        diseased_mask: np.ndarray
    ) -> np.ndarray:
        """
        Create visualization:

        - disease pixels = red
        - leaf boundary = green
        """

        overlay = img_rgb.copy()

        # ----------------------------------------------------
        # Highlight disease pixels
        # ----------------------------------------------------

        overlay[
            diseased_mask > 0
        ] = [255, 0, 0]

        # ----------------------------------------------------
        # Blend with original
        # ----------------------------------------------------

        blended = cv2.addWeighted(
            img_rgb,
            0.4,
            overlay,
            0.6,
            0
        )

        # ----------------------------------------------------
        # Leaf boundary
        # ----------------------------------------------------

        contours, _ = cv2.findContours(
            leaf_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:

            cv2.drawContours(
                blended,
                contours,
                -1,
                (0, 255, 0),
                2
            )

        return blended

    # ========================================================
    # COMPOSITE
    # ========================================================

    def _create_composite_image(
        self,
        img_rgb: np.ndarray,
        leaf_mask: np.ndarray,
        diseased_mask: np.ndarray,
        overlay_rgb: np.ndarray
    ) -> np.ndarray:
        """
        Create a 2x2 composite visualization:

        Top-left:
            Original image

        Top-right:
            Leaf mask

        Bottom-left:
            Disease mask

        Bottom-right:
            Disease overlay
        """

        # ----------------------------------------------------
        # Original
        # ----------------------------------------------------

        original = img_rgb.copy()

        height, width = original.shape[:2]

        # ----------------------------------------------------
        # Leaf mask visualization
        # ----------------------------------------------------

        leaf_visual = cv2.cvtColor(
            leaf_mask,
            cv2.COLOR_GRAY2RGB
        )

        # ----------------------------------------------------
        # Disease mask visualization
        # ----------------------------------------------------

        disease_visual = cv2.cvtColor(
            diseased_mask,
            cv2.COLOR_GRAY2RGB
        )

        # ----------------------------------------------------
        # Ensure dimensions match
        # ----------------------------------------------------

        leaf_visual = cv2.resize(
            leaf_visual,
            (width, height),
            interpolation=cv2.INTER_NEAREST
        )

        disease_visual = cv2.resize(
            disease_visual,
            (width, height),
            interpolation=cv2.INTER_NEAREST
        )

        overlay_visual = cv2.resize(
            overlay_rgb,
            (width, height),
            interpolation=cv2.INTER_AREA
        )

        # ----------------------------------------------------
        # Build 2x2 layout
        # ----------------------------------------------------

        top = np.hstack(
            (
                original,
                leaf_visual
            )
        )

        bottom = np.hstack(
            (
                disease_visual,
                overlay_visual
            )
        )

        composite = np.vstack(
            (
                top,
                bottom
            )
        )

        return composite