"""
Grad-CAM (Gradient-weighted Class Activation Mapping) implementation for EfficientNetB0.
Generates genuine activation heatmaps and visual overlay files.
Handles nested sub-models (e.g. Keras EfficientNet functional block) cleanly.
"""
import uuid
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Ensure both backend and root directories are in sys.path
_BASE_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _BASE_DIR.parent
for directory in (str(_ROOT_DIR), str(_BASE_DIR)):
    if directory not in sys.path:
        sys.path.insert(0, directory)

# Import config FIRST to pre-configure KERAS_HOME before tensorflow is loaded
try:
    from backend.config import GRADCAM_DIR
except ImportError:
    from config import GRADCAM_DIR

import numpy as np
import cv2
from PIL import Image, ImageOps
import tensorflow as tf

try:
    from tensorflow import keras
except (ImportError, AttributeError):
    try:
        import keras
    except ImportError:
        keras = getattr(tf, "keras", None)

logger = logging.getLogger(__name__)


class GradCAMGenerator:
    def __init__(self, model: Any):
        self.model = model
        self.submodel, self.target_layer_name = self._find_target_conv_layer()
        sub_name = self.submodel.name if self.submodel else "top_level"

        # Resolve models module safely across TensorFlow and Keras versions
        models_module = getattr(getattr(tf, "keras", None), "models", None) or getattr(keras, "models", None)
        if models_module is None:
            raise RuntimeError("Unable to locate keras.models in tensorflow or standalone keras.")

        # Pre-build sub_grad_model or grad_model once to prevent memory graph leak on every call
        if self.submodel is not None:
            sub_conv_layer = self.submodel.get_layer(self.target_layer_name)
            self.sub_grad_model = models_module.Model(
                inputs=self.submodel.inputs,
                outputs=[sub_conv_layer.output, self.submodel.output],
            )
            self.grad_model = None
        else:
            self.sub_grad_model = None
            self.grad_model = models_module.Model(
                inputs=[self.model.inputs],
                outputs=[
                    self.model.get_layer(self.target_layer_name).output,
                    self.model.output,
                ],
            )

        logger.info(
            f"Grad-CAM initialized with target layer '{self.target_layer_name}' in '{sub_name}'"
        )

    def _find_target_conv_layer(self) -> Tuple[Optional[Any], str]:
        """Find the final convolutional feature layer of the model or submodel."""
        preferred_names = ["top_conv", "top_activation", "conv2d", "block7a_project_conv"]

        # 1. Search inside submodels (e.g. efficientnetb0)
        for layer in reversed(self.model.layers):
            if hasattr(layer, "layers") and isinstance(layer.layers, list):
                for sublayer in reversed(layer.layers):
                    if sublayer.name in preferred_names:
                        return layer, sublayer.name
                for sublayer in reversed(layer.layers):
                    if "conv" in sublayer.name.lower():
                        return layer, sublayer.name

        # 2. Search top-level layers
        for layer in reversed(self.model.layers):
            if layer.name in preferred_names:
                return None, layer.name

        # Fallback
        return None, self.model.layers[-3].name

    def generate_gradcam(
        self,
        img_batch: np.ndarray,
        target_class_idx: int,
        original_img: Optional[Image.Image] = None,
        alpha: float = 0.4,
    ) -> Dict[str, Any]:
        """
        Calculates Grad-CAM heatmap for the target class index and saves heatmap & overlay images.

        Args:
            img_batch: Preprocessed image tensor of shape (1, 224, 224, 3)
            target_class_idx: Model output index for top prediction
            original_img: PIL Image of original upload for pixel-perfect overlay
            alpha: Transparency weight for overlay blending

        Returns:
            Dictionary with paths to generated heatmap and overlay files.
        """
        img_tensor = tf.cast(img_batch, tf.float32)

        with tf.GradientTape() as tape:
            if self.submodel is not None and self.sub_grad_model is not None:
                # Forward pass layer-by-layer with training=False to disable data augmentation & dropout
                x = img_tensor
                for layer in self.model.layers:
                    if layer.__class__.__name__ == "InputLayer":
                        continue
                    if layer == self.submodel:
                        conv_outputs, eff_output = self.sub_grad_model(x, training=False)
                        x = eff_output
                    else:
                        x = layer(x, training=False)

                predictions = x
            else:
                conv_outputs, predictions = self.grad_model(img_tensor, training=False)

            loss = predictions[:, target_class_idx]

        # Extract gradients of target class score w.r.t target conv layer
        grads = tape.gradient(loss, conv_outputs)

        # Global average pooling of gradients per feature map
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

        # Weight feature map channels by pooled gradients
        conv_outputs_0 = conv_outputs[0]
        heatmap = conv_outputs_0 @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap, axis=-1)

        # Apply ReLU to retain positive contributions
        heatmap = tf.maximum(heatmap, 0.0)
        max_val = tf.reduce_max(heatmap)
        if max_val > 0:
            heatmap = heatmap / max_val
        else:
            logger.warning(
                f"Grad-CAM target layer '{self.target_layer_name}' produced zero positive activation for class index {target_class_idx}."
            )

        heatmap_np = heatmap.numpy()

        # Target dimensions for output images
        if original_img is not None:
            oriented_orig = ImageOps.exif_transpose(original_img)
            target_w, target_h = oriented_orig.size
            orig_rgb = np.array(oriented_orig.convert("RGB"))
        else:
            target_w, target_h = 224, 224
            orig_rgb = np.uint8(np.clip(img_batch[0], 0, 255))

        # Resize heatmap to target dimensions
        heatmap_resized = cv2.resize(heatmap_np, (target_w, target_h))
        heatmap_uint8 = np.uint8(255 * heatmap_resized)

        # Apply JET color map for heatmap
        color_heatmap_bgr = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        color_heatmap_rgb = cv2.cvtColor(color_heatmap_bgr, cv2.COLOR_BGR2RGB)

        # Superimpose heatmap on original image
        overlay_rgb = cv2.addWeighted(orig_rgb, 1 - alpha, color_heatmap_rgb, alpha, 0)

        # Generate unique filenames
        unique_id = uuid.uuid4().hex[:8]
        heatmap_filename = f"gradcam_{unique_id}_heatmap.jpg"
        overlay_filename = f"gradcam_{unique_id}_overlay.jpg"

        heatmap_path = GRADCAM_DIR / heatmap_filename
        overlay_path = GRADCAM_DIR / overlay_filename

        # Save images
        Image.fromarray(color_heatmap_rgb).save(heatmap_path, quality=95)
        Image.fromarray(overlay_rgb).save(overlay_path, quality=95)

        relative_heatmap = f"generated/gradcam/{heatmap_filename}"
        relative_overlay = f"generated/gradcam/{overlay_filename}"

        return {
            "available": True,
            "target_layer": self.target_layer_name,
            "heatmap_path": relative_heatmap,
            "overlay_path": relative_overlay,
            "absolute_heatmap_path": str(heatmap_path),
            "absolute_overlay_path": str(overlay_path),
        }

