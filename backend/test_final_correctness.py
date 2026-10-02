"""
Harvest Harbor — Final Correctness & Safety Regression Test Suite
==================================================================
Tests:
  1. skipped_low_crop_confidence:
     - Produces NO official disease prediction (disease_analysis.prediction is None)
     - Sets official disease top_3 to empty list ([])
     - Preserves raw prediction and raw_top_3 as unvalidated candidates
     - Sets status to 'uncertain_prediction'
     - Suppresses confirmed severity assignment

  2. remove_absolute_path_keys():
     - Strips absolute path keys (e.g. 'absolute_storage_path')
     - Redacts/sanitizes absolute filesystem paths embedded inside error message strings
     - Preserves relative public URLs (e.g. '/uploads/...', '/generated/...')
     - Recursively cleans nested dicts, lists, and string values

  3. Unified image pixel limit (MAX_DECODED_PIXELS):
     - Rejects images whose total decoded pixels (width * height) exceed the 50 MP safety limit
     - Accepts images within the safety limit
"""

import asyncio
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

# Set testing environment
os.environ["ENVIRONMENT"] = "testing"
os.environ.setdefault("KERAS_HOME", tempfile.mkdtemp())

from app import (
    app,
    predict,
    startup_event,
    remove_absolute_path_keys,
    MAX_DECODED_PIXELS,
    make_upload_url,
    make_generated_url,
)
from fastapi import UploadFile, HTTPException

def _ensure_event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


class TestSkippedLowCropConfidenceCorrectness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            startup_event()
        except Exception as e:
            print("Startup exception (ignored):", e)
        cls.image_path = Path(__file__).resolve().parent.parent / "test_images" / "sample_leaf.jpg"
        with open(cls.image_path, "rb") as f:
            cls.test_image_bytes = f.read()

    def test_skipped_low_crop_confidence_produces_no_official_prediction(self):
        """When crop confidence is < 50%, official prediction is None and top_3 is empty."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "leaf.jpg"
        mock_file.content_type = "image/jpeg"
        loop = _ensure_event_loop()
        future = loop.create_future()
        future.set_result(self.test_image_bytes)
        mock_file.read = MagicMock(return_value=future)

        mock_user = {
            "role": "agronomist",
            "auth_type": "apikey",
            "authenticated": "true",
            "identity": "authenticated:agronomist",
            "inspector_label": "AGRO-7402",
        }

        with patch("crop_classifier.CropPredictor.predict_image") as mc, \
             patch("health_predictor.HealthPredictor.predict_image") as mh, \
             patch("predictor.PlantPredictor.predict_image") as md:

            mh.return_value = {"prediction": "diseased", "confidence": 99.0}
            mc.return_value = {"prediction": "Apple", "confidence": 35.0, "uncertain": True}
            md.return_value = {
                "prediction": "Grape___Black_rot",
                "confidence": 92.0,
                "probabilities": [0.92] + [0.0] * 114,
                "class_names": ["Grape___Black_rot"] * 115,
                "top3": [{"class": "Grape___Black_rot", "confidence": 92.0}],
            }

            resp = loop.run_until_complete(
                predict(file=mock_file, user=mock_user)
            )

            da = resp["disease_analysis"]

            # 1. Official disease prediction MUST be None
            self.assertIsNone(da["prediction"],
                              "Official disease prediction must be None when crop confidence is too low to validate.")

            # 2. Official disease confidence MUST be None
            self.assertIsNone(da["confidence"],
                              "Official disease confidence must be None when crop confidence is too low to validate.")

            # 3. Official top_3 MUST be empty list
            self.assertEqual(da["top_3"], [],
                             "Official top_3 must be empty so UI never displays an unvalidated primary match.")

            # 4. Raw prediction MUST be preserved separately for audit
            self.assertEqual(da["raw_prediction"], "Grape___Black_rot",
                             "Raw prediction must be preserved for audit.")
            self.assertGreater(len(da["raw_top_3"]), 0,
                               "Raw top-3 must be preserved as unvalidated candidates.")
            self.assertEqual(da["raw_top_3"][0]["class"], "Grape___Black_rot")

            # 5. Validation status must be skipped_low_crop_confidence
            self.assertEqual(da["validation"]["status"], "skipped_low_crop_confidence")

            # 6. Overall response status must be uncertain_prediction
            self.assertEqual(resp["status"], "uncertain_prediction")

            # 7. Severity must NOT be presented as confirmed disease severity
            self.assertFalse(resp["severity"]["available"],
                             "Confirmed disease severity must not be assigned when disease is unvalidated.")


class TestAbsolutePathSanitization(unittest.TestCase):

    def test_strip_absolute_path_keys(self):
        """Keys starting with 'absolute_' must be removed from dict."""
        data = {
            "report_id": "CR-12345",
            "absolute_storage_path": "/home/developer/crop-disease-ai/backend/uploads/sample.jpg",
            "absolute_model_path": "/home/ubuntu/crop-disease-ai/model.keras",
            "safe_key": "safe_value",
        }
        cleaned = remove_absolute_path_keys(data)
        self.assertNotIn("absolute_storage_path", cleaned)
        self.assertNotIn("absolute_model_path", cleaned)
        self.assertIn("safe_key", cleaned)
        self.assertEqual(cleaned["safe_key"], "safe_value")

    def test_sanitize_embedded_error_message_paths(self):
        """Absolute filesystem paths embedded inside error strings must be sanitized."""
        error_msg = (
            "[Errno 2] No such file or directory: "
            "'/home/developer/crop-disease-ai/backend/uploads/CR-12345_leaf.jpg'"
        )
        cleaned = remove_absolute_path_keys(error_msg)
        self.assertNotIn("/home/developer", cleaned,
                         "Absolute user directory must be sanitized from error string.")
        # Uploads relative path should be preserved or redacted
        self.assertTrue(
            cleaned.startswith("[Errno 2] No such file or directory: '/uploads/CR-12345_leaf.jpg'")
            or "[REDACTED_PATH]" in cleaned
        )

    def test_sanitize_internal_system_paths(self):
        """Internal system paths (e.g. /home/ubuntu, /var/log, C:\\...) must be redacted."""
        test_strings = [
            "Fatal error occurred in /home/deploy/app/server.py at line 12",
            "Log file located at /var/log/syslog could not be opened",
            "C:\\Users\\Administrator\\AppData\\Local\\Temp\\crash.dump was created",
        ]
        for s in test_strings:
            cleaned = remove_absolute_path_keys(s)
            self.assertNotIn("/home/deploy", cleaned)
            self.assertNotIn("/var/log", cleaned)
            self.assertNotIn("C:\\Users\\Administrator", cleaned)
            self.assertIn("[REDACTED_PATH]", cleaned)

    def test_preserve_legitimate_relative_urls(self):
        """Relative URLs like /uploads/... and /generated/... must remain untouched."""
        data = {
            "image_url": "/uploads/CR-0025E60213CC_sample_leaf.jpg",
            "heatmap": "/generated/gradcam/gradcam_123_heatmap.jpg",
            "overlay": "/generated/segmentation/segmentation_123_overlay.jpg",
        }
        cleaned = remove_absolute_path_keys(data)
        self.assertEqual(cleaned["image_url"], "/uploads/CR-0025E60213CC_sample_leaf.jpg")
        self.assertEqual(cleaned["heatmap"], "/generated/gradcam/gradcam_123_heatmap.jpg")
        self.assertEqual(cleaned["overlay"], "/generated/segmentation/segmentation_123_overlay.jpg")


class TestImagePixelSafetyLimit(unittest.TestCase):

    def test_unified_max_decoded_pixels_constant(self):
        """Verify unified decoded pixel safety constant is 50,000,000."""
        self.assertEqual(MAX_DECODED_PIXELS, 50_000_000)
        self.assertEqual(Image.MAX_IMAGE_PIXELS, 50_000_000)

    def test_rejects_image_exceeding_pixel_limit(self):
        """An image whose width * height exceeds MAX_DECODED_PIXELS is rejected with 400 Bad Request."""
        # Create a small valid JPEG with header claiming 8000 x 7000 = 56,000,000 pixels (> 50 MP)
        # We can construct an in-memory image object and verify the dimension check
        img = Image.new("RGB", (100, 100), color="green")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        valid_jpeg_bytes = buf.getvalue()

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "huge_leaf.jpg"
        mock_file.content_type = "image/jpeg"

        # Mock Image.open to return an image of size (8000, 7000) = 56 MP
        mock_huge_img = MagicMock(spec=Image.Image)
        mock_huge_img.format = "JPEG"
        mock_huge_img.size = (8000, 7000)
        mock_huge_img.convert.return_value = mock_huge_img

        loop = _ensure_event_loop()
        future = loop.create_future()
        future.set_result(valid_jpeg_bytes)
        mock_file.read = MagicMock(return_value=future)

        mock_user = {
            "role": "agronomist",
            "auth_type": "apikey",
            "authenticated": "true",
            "identity": "authenticated:agronomist",
        }

        with patch("PIL.Image.open", return_value=mock_huge_img), \
             patch("PIL.ImageOps.exif_transpose", return_value=mock_huge_img):

            with self.assertRaises(HTTPException) as ctx:
                loop.run_until_complete(
                    predict(file=mock_file, user=mock_user)
                )

            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("exceeds the safety limit", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main(verbosity=2)
