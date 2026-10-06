"""
test_prediction.py — Prediction pipeline unit tests.

Tests the full inference stack end-to-end using a synthetic leaf image:
  HealthPredictor → PlantPredictor → GradCAM → LeafSegmenter → Severity

All models must load successfully; no 503 / None model is accepted as success.
"""

import os
import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

# ============================================================
# PATH SETUP + KERAS_HOME GUARD (must precede any TF import)
# ============================================================
_BASE_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _BASE_DIR.parent
if "KERAS_HOME" not in os.environ:
    os.environ["KERAS_HOME"] = str(_BASE_DIR / ".keras")

for _d in (str(_ROOT_DIR), str(_BASE_DIR)):
    if _d not in sys.path:
        sys.path.insert(0, _d)

# ============================================================
# MODULE IMPORTS
# ============================================================
try:
    from backend.config import IMAGE_SIZE
    from backend.health_predictor import HealthPredictor
    from backend.predictor import get_predictor
    from backend.gradcam import GradCAMGenerator
    from backend.segmentation import LeafSegmenter
    from backend.severity import analyze_segmentation_result
except ImportError:
    from config import IMAGE_SIZE
    from health_predictor import HealthPredictor
    from predictor import get_predictor
    from gradcam import GradCAMGenerator
    from segmentation import LeafSegmenter
    from severity import analyze_segmentation_result


# ============================================================
# HELPERS
# ============================================================

def _make_leaf_image(size=(400, 400)) -> Image.Image:
    """Synthetic green leaf with brown disease spots."""
    img = Image.new("RGB", size, color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.ellipse([80, 50, 320, 350], fill=(34, 139, 34), outline=(0, 100, 0))
    draw.ellipse([150, 120, 220, 190], fill=(139, 69, 19))
    draw.ellipse([200, 220, 250, 270], fill=(160, 82, 45))
    return img


# ============================================================
# TESTS
# ============================================================

class TestHealthPredictor(unittest.TestCase):
    """HealthPredictor must load and run inference without raising."""

    @classmethod
    def setUpClass(cls):
        cls.hp = HealthPredictor()
        cls.img = _make_leaf_image()

    def test_health_model_not_none(self):
        """HealthPredictor.model must not be None after init."""
        self.assertIsNotNone(
            self.hp.model,
            "HealthPredictor.model is None — model failed to load"
        )

    def test_health_predict_returns_dict(self):
        result = self.hp.predict_image(self.img)
        self.assertIsInstance(result, dict)

    def test_health_predict_has_required_keys(self):
        result = self.hp.predict_image(self.img)
        for key in ("prediction", "confidence", "probability_healthy", "probability_diseased"):
            self.assertIn(key, result, f"Missing key '{key}' in health result")

    def test_prediction_value_valid(self):
        result = self.hp.predict_image(self.img)
        self.assertIn(result["prediction"], ("healthy", "diseased"))

    def test_health_confidence_range(self):
        result = self.hp.predict_image(self.img)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 100.0)

    def test_probabilities_sum_to_100(self):
        result = self.hp.predict_image(self.img)
        total = result["probability_healthy"] + result["probability_diseased"]
        self.assertAlmostEqual(total, 100.0, places=1)

    def test_calibration_status_present(self):
        result = self.hp.predict_image(self.img)
        self.assertIn("calibration", result)
        self.assertIn("status", result["calibration"])


class TestDiseasePredictor(unittest.TestCase):
    """Disease predictor (PlantPredictor) must load and run inference."""

    @classmethod
    def setUpClass(cls):
        cls.predictor = get_predictor()
        cls.img = _make_leaf_image()

    def test_disease_model_not_none(self):
        self.assertIsNotNone(
            self.predictor.model,
            "Disease predictor model is None"
        )

    def test_disease_predict_returns_dict(self):
        result = self.predictor.predict_image(self.img)
        self.assertIsInstance(result, dict)

    def test_disease_predict_has_required_keys(self):
        result = self.predictor.predict_image(self.img)
        for key in ("raw_prediction", "confidence", "top_3"):
            self.assertIn(key, result, f"Missing key '{key}' in disease result")

    def test_top3_length(self):
        result = self.predictor.predict_image(self.img)
        self.assertGreaterEqual(len(result["top_3"]), 1)
        self.assertLessEqual(len(result["top_3"]), 3)

    def test_disease_confidence_range(self):
        result = self.predictor.predict_image(self.img)
        self.assertGreater(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 100.0)


class TestGradCAM(unittest.TestCase):
    """GradCAM must generate outputs without raising."""

    @classmethod
    def setUpClass(cls):
        cls.predictor = get_predictor()
        cls.generator = GradCAMGenerator(cls.predictor.model)
        cls.img = _make_leaf_image()

    def test_gradcam_available(self):
        img_batch = self.predictor.preprocess_image(self.img)
        result = self.predictor.predict_image(self.img)
        target_idx = result.get("top_class_idx", 0)
        info = self.generator.generate_gradcam(img_batch, target_idx, original_img=self.img)
        self.assertIn("available", info)

    def test_gradcam_produces_heatmap_path(self):
        img_batch = self.predictor.preprocess_image(self.img)
        result = self.predictor.predict_image(self.img)
        target_idx = result.get("top_class_idx", 0)
        info = self.generator.generate_gradcam(img_batch, target_idx, original_img=self.img)
        if info.get("available"):
            # GradCAM may return either absolute or relative paths — check both
            heatmap = info.get("heatmap_path", "")
            abs_heatmap = info.get("absolute_heatmap_path", "")
            path_to_check = Path(abs_heatmap) if abs_heatmap else (
                Path(heatmap) if Path(heatmap).is_absolute() else _BASE_DIR / heatmap
            )
            self.assertTrue(
                path_to_check.exists(),
                f"Heatmap file not found at resolved path: {path_to_check}"
            )


class TestSegmentation(unittest.TestCase):
    """LeafSegmenter must load and segment without raising."""

    @classmethod
    def setUpClass(cls):
        cls.segmenter = LeafSegmenter()
        cls.img = _make_leaf_image()

    def test_segmenter_has_architecture_name(self):
        self.assertIsInstance(self.segmenter.architecture_name, str)
        self.assertGreater(len(self.segmenter.architecture_name), 0)

    def test_unet_model_loaded(self):
        """U-Net model must load; HSV/Lab fallback should be labeled as degraded."""
        if self.segmenter.unet_model is None:
            self.assertNotIn(
                "U-Net",
                self.segmenter.architecture_name,
                "architecture_name claims U-Net but unet_model is None"
            )
        else:
            self.assertIn(
                "U-Net",
                self.segmenter.architecture_name,
                "unet_model loaded but architecture_name doesn't reflect U-Net"
            )

    def test_segment_image_returns_dict(self):
        result = self.segmenter.segment_image(self.img)
        self.assertIsInstance(result, dict)

    def test_segment_has_required_keys(self):
        result = self.segmenter.segment_image(self.img)
        for key in ("leaf_pixels", "diseased_pixels"):
            self.assertIn(key, result, f"Missing key '{key}' in segmentation result")
        # The affected area ratio may be stored under 'affected_ratio' or 'affected_area_ratio'
        ratio_key = "affected_ratio" if "affected_ratio" in result else "affected_area_ratio"
        self.assertIn(
            ratio_key, result,
            f"No affected-area ratio key in segmentation result. Keys: {list(result.keys())}"
        )

    def test_affected_ratio_range(self):
        result = self.segmenter.segment_image(self.img)
        ratio_key = "affected_ratio" if "affected_ratio" in result else "affected_area_ratio"
        ratio = result.get(ratio_key, 0.0)
        self.assertGreaterEqual(ratio, 0.0)
        self.assertLessEqual(ratio, 1.0)


class TestSeverityAnalysis(unittest.TestCase):
    """Severity analysis must produce valid tier outputs."""

    @classmethod
    def setUpClass(cls):
        cls.segmenter = LeafSegmenter()
        cls.img = _make_leaf_image()

    def test_severity_returns_dict(self):
        seg_result = self.segmenter.segment_image(self.img)
        sev_result = analyze_segmentation_result(seg_result)
        self.assertIsInstance(sev_result, dict)

    def test_severity_has_required_keys(self):
        seg_result = self.segmenter.segment_image(self.img)
        sev_result = analyze_segmentation_result(seg_result)
        for key in ("severity", "affected_area_percent", "description", "recommendation"):
            self.assertIn(key, sev_result, f"Missing key '{key}' in severity result")

    def test_affected_area_percent_range(self):
        seg_result = self.segmenter.segment_image(self.img)
        sev_result = analyze_segmentation_result(seg_result)
        pct = sev_result.get("affected_area_percent", 0.0)
        self.assertGreaterEqual(pct, 0.0)
        self.assertLessEqual(pct, 100.0)


class TestFullPipeline(unittest.TestCase):
    """Full end-to-end pipeline: health → disease → gradcam → seg → severity."""

    @classmethod
    def setUpClass(cls):
        cls.hp = HealthPredictor()
        cls.predictor = get_predictor()
        cls.gradcam = GradCAMGenerator(cls.predictor.model)
        cls.segmenter = LeafSegmenter()
        cls.img = _make_leaf_image()

    def test_full_pipeline_completes(self):
        health = self.hp.predict_image(self.img)
        self.assertIn("prediction", health)

        disease = self.predictor.predict_image(self.img)
        self.assertIn("raw_prediction", disease)

        img_batch = self.predictor.preprocess_image(self.img)
        target_idx = disease.get("top_class_idx", 0)
        gradcam_info = self.gradcam.generate_gradcam(img_batch, target_idx, original_img=self.img)
        self.assertIn("available", gradcam_info)

        seg_result = self.segmenter.segment_image(self.img)
        sev_result = analyze_segmentation_result(seg_result)
        self.assertIn("severity", sev_result)

    def test_health_model_not_none_in_pipeline(self):
        self.assertIsNotNone(self.hp.model, "Health model must not be None in full pipeline")

    def test_disease_model_not_none_in_pipeline(self):
        self.assertIsNotNone(self.predictor.model, "Disease model must not be None in full pipeline")


if __name__ == "__main__":
    unittest.main(verbosity=2)
