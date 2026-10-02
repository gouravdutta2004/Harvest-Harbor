"""
Harvest Harbor — Comprehensive 12-Scenario End-to-End Test Suite
=================================================================
Validates all 12 core platform requirements:
  Scenario 01: Healthy leaf detection & disease suppression
  Scenario 02: Clear diseased leaf diagnostic, explainability & severity pipeline
  Scenario 03: Low crop confidence handling (unvalidated candidates preserved, no confirmed match)
  Scenario 04: Crop-disease mismatch rejection (sanitized top-3, raw candidates preserved)
  Scenario 05: Corrupted / invalid image input handling (400 Bad Request)
  Scenario 06: Oversized image payload & decoded pixel bomb protection (413/400)
  Scenario 07: Directory traversal protection on protected asset paths (403 Forbidden)
  Scenario 08: Unauthenticated protected asset request (401 Unauthorized)
  Scenario 09: Role-based access control violation (403 Forbidden for insufficient role)
  Scenario 10: Authenticated asset download with binary streaming & headers (200 OK)
  Scenario 11: Tamper-evident evidence chain cryptographic verification (100% valid)
  Scenario 12: Human review resolution audit block aggregation & report reconstruction
"""

import asyncio
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

# Ensure testing environment and sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ["ENVIRONMENT"] = "testing"
os.environ.setdefault("KERAS_HOME", tempfile.mkdtemp())

from app import (
    app,
    predict,
    startup_event,
    evidence_blockchain,
    review_queue,
    MAX_DECODED_PIXELS,
    MAX_FILE_SIZE_BYTES,
    UPLOADS_DIR,
    GENERATED_DIR,
)
from fastapi import UploadFile, HTTPException


class ASGITestClient:
    """Zero-dependency ASGI Test Client for executing real HTTP requests against FastAPI app."""

    def __init__(self, asgi_app):
        self.app = asgi_app

    def request(self, method: str, path: str, headers: dict = None, body: bytes = b"", query_string: str = ""):
        response_start = {}
        body_parts = []

        headers_list = []
        if headers:
            for k, v in headers.items():
                headers_list.append((k.lower().encode("utf-8"), str(v).encode("utf-8")))

        raw_path = path.encode("utf-8")
        encoded_query = query_string.encode("utf-8") if isinstance(query_string, str) else query_string

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method.upper(),
            "path": path,
            "raw_path": raw_path,
            "query_string": encoded_query,
            "headers": headers_list,
        }

        request_sent = False
        disconnect_event = asyncio.Event()

        async def receive():
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            await disconnect_event.wait()
            return {"type": "http.disconnect"}

        async def send(message):
            if message["type"] == "http.response.start":
                response_start.update(message)
            elif message["type"] == "http.response.body":
                body_parts.append(message.get("body", b""))

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.app(scope, receive, send))
        finally:
            loop.close()

        status_code = response_start.get("status", 500)
        resp_headers = dict(
            (k.decode("utf-8").lower(), v.decode("utf-8"))
            for k, v in response_start.get("headers", [])
        )
        response_body = b"".join(body_parts)
        return status_code, resp_headers, response_body

    def get(self, path: str, headers: dict = None, query_string: str = ""):
        return self.request("GET", path, headers=headers, query_string=query_string)

    def post(self, path: str, headers: dict = None, body: bytes = b""):
        return self.request("POST", path, headers=headers, body=body)


class TestHarvestHarborAll12Scenarios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            startup_event()
        except Exception:
            pass
        cls.client = ASGITestClient(app)

        # Create a valid test image
        img = Image.new("RGB", (100, 100), color=(34, 139, 34))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        cls.valid_image_bytes = buf.getvalue()

        # Place a test asset in UPLOADS_DIR for asset retrieval tests
        cls.test_asset_name = "scenario_test_asset.jpg"
        cls.test_asset_path = Path(UPLOADS_DIR) / cls.test_asset_name
        with open(cls.test_asset_path, "wb") as f:
            f.write(cls.valid_image_bytes)

        cls.agro_user = {
            "role": "agronomist",
            "auth_type": "apikey",
            "authenticated": "true",
            "identity": "authenticated:agronomist",
            "inspector_label": "AGRO-E2E",
        }

    @classmethod
    def tearDownClass(cls):
        if cls.test_asset_path.exists():
            try:
                cls.test_asset_path.unlink()
            except Exception:
                pass

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        if not self.loop.is_closed():
            self.loop.close()

    def _create_mock_upload(self, data: bytes, filename: str = "leaf.jpg"):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = "image/jpeg"
        future = self.loop.create_future()
        future.set_result(data)
        mock_file.read = MagicMock(return_value=future)
        return mock_file

    # =========================================================================
    # SCENARIO 01: Healthy Leaf
    # =========================================================================
    def test_01_healthy_leaf(self):
        """Scenario 01: Healthy leaf input results in healthy status and suppressed disease."""
        mock_file = self._create_mock_upload(self.valid_image_bytes)

        with patch("health_predictor.HealthPredictor.predict_image") as mh, \
             patch("crop_classifier.CropPredictor.predict_image") as mc:
            mh.return_value = {"prediction": "healthy", "confidence": 99.8, "probability_healthy": 99.8}
            mc.return_value = {"prediction": "Apple", "confidence": 95.0, "uncertain": False}

            resp = self.loop.run_until_complete(
                predict(file=mock_file, user=self.agro_user)
            )

            self.assertTrue(resp.get("success"))
            self.assertEqual(resp["health_prediction"]["prediction"], "healthy")
            self.assertEqual(resp["status"], "healthy_prediction")
            # Disease analysis must not report an active disease
            self.assertIsNone(resp["disease_analysis"])

    # =========================================================================
    # SCENARIO 02: Clear Diseased Leaf Pipeline
    # =========================================================================
    def test_02_clear_diseased_leaf(self):
        """Scenario 02: Clear diseased leaf produces crop, validated disease, severity and explainability."""
        mock_file = self._create_mock_upload(self.valid_image_bytes)

        with patch("health_predictor.HealthPredictor.predict_image") as mh, \
             patch("crop_classifier.CropPredictor.predict_image") as mc, \
             patch("predictor.PlantPredictor.predict_image") as md:

            mh.return_value = {"prediction": "diseased", "confidence": 99.5, "probability_healthy": 0.5}
            mc.return_value = {"prediction": "Apple", "confidence": 94.0, "uncertain": False}
            md.return_value = {
                "prediction": "Apple___Apple_scab",
                "confidence": 96.0,
                "probabilities": [0.96] + [0.0] * 114,
                "class_names": ["Apple___Apple_scab"] * 115,
                "top3": [{"class": "Apple___Apple_scab", "confidence": 96.0}],
            }

            resp = self.loop.run_until_complete(
                predict(file=mock_file, user=self.agro_user)
            )

            self.assertTrue(resp.get("success"))
            self.assertEqual(resp["crop_prediction"]["prediction"], "Apple")
            self.assertEqual(resp["disease_analysis"]["prediction"], "Apple___Apple_scab")
            self.assertIn(resp["disease_analysis"]["validation"]["status"], ["validated", "validated_by_crop"])
            self.assertIsNotNone(resp.get("severity"))
            self.assertIsNotNone(resp.get("explainability"))
            self.assertEqual(resp["status"], "disease_prediction")

    # =========================================================================
    # SCENARIO 03: Skipped Low Crop Confidence
    # =========================================================================
    def test_03_skipped_low_crop_confidence(self):
        """Scenario 03: Low crop confidence skips disease validation, preserving raw candidate."""
        mock_file = self._create_mock_upload(self.valid_image_bytes)

        with patch("health_predictor.HealthPredictor.predict_image") as mh, \
             patch("crop_classifier.CropPredictor.predict_image") as mc, \
             patch("predictor.PlantPredictor.predict_image") as md:

            mh.return_value = {"prediction": "diseased", "confidence": 99.0}
            mc.return_value = {"prediction": "Apple", "confidence": 35.0, "uncertain": True}
            md.return_value = {
                "prediction": "Grape___Black_rot",
                "confidence": 90.0,
                "probabilities": [0.9] + [0.0] * 114,
                "class_names": ["Grape___Black_rot"] * 115,
                "top3": [{"class": "Grape___Black_rot", "confidence": 90.0}],
            }

            resp = self.loop.run_until_complete(
                predict(file=mock_file, user=self.agro_user)
            )

            da = resp["disease_analysis"]
            self.assertIsNone(da["prediction"])
            self.assertEqual(da["top_3"], [])
            self.assertEqual(da["validation"]["status"], "skipped_low_crop_confidence")
            self.assertEqual(da["raw_prediction"], "Grape___Black_rot")
            self.assertEqual(resp["status"], "uncertain_prediction")

    # =========================================================================
    # SCENARIO 04: Mismatch / Rejected Disease Prediction
    # =========================================================================
    def test_04_mismatch_rejected_disease(self):
        """Scenario 04: Incompatible disease candidate rejected; top_3 cleared, raw preserved."""
        mock_file = self._create_mock_upload(self.valid_image_bytes)

        with patch("health_predictor.HealthPredictor.predict_image") as mh, \
             patch("crop_classifier.CropPredictor.predict_image") as mc, \
             patch("predictor.PlantPredictor.predict_image") as md:

            mh.return_value = {"prediction": "diseased", "confidence": 99.0}
            mc.return_value = {"prediction": "Tomato", "confidence": 92.0, "uncertain": False}
            md.return_value = {
                "prediction": "Apple___Apple_scab",
                "confidence": 95.0,
                "probabilities": [0.95] + [0.0] * 114,
                "class_names": ["Apple___Apple_scab"] * 115,
                "top3": [{"class": "Apple___Apple_scab", "confidence": 95.0}],
            }

            resp = self.loop.run_until_complete(
                predict(file=mock_file, user=self.agro_user)
            )

            da = resp["disease_analysis"]
            self.assertEqual(da["validation"]["status"], "rejected")
            self.assertIsNone(da["prediction"])
            self.assertEqual(da["top_3"], [])
            self.assertEqual(da["raw_prediction"], "Apple___Apple_scab")
            self.assertEqual(resp["status"], "uncertain_prediction")

    # =========================================================================
    # SCENARIO 05: Corrupted Image Handling
    # =========================================================================
    def test_05_corrupted_image(self):
        """Scenario 05: Non-image bytes raise 400 Bad Request."""
        mock_file = self._create_mock_upload(b"GARBAGE_PAYLOAD_NOT_AN_IMAGE")

        with self.assertRaises(HTTPException) as ctx:
            self.loop.run_until_complete(
                predict(file=mock_file, user=self.agro_user)
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Invalid or corrupted image file", ctx.exception.detail)

    # =========================================================================
    # SCENARIO 06: Oversized Image Protection
    # =========================================================================
    def test_06_oversized_image(self):
        """Scenario 06: Payload exceeding byte limit or 50 MP pixel bomb is rejected."""
        # 1. Byte limit check
        fake_huge_bytes = b"0" * (MAX_FILE_SIZE_BYTES + 1024)
        mock_file = self._create_mock_upload(fake_huge_bytes)
        with self.assertRaises(HTTPException) as ctx:
            self.loop.run_until_complete(
                predict(file=mock_file, user=self.agro_user)
            )
        self.assertEqual(ctx.exception.status_code, 413)

        # 2. Pixel limit check
        huge_img = Image.new("RGB", (8000, 7000), color=(10, 10, 10))  # 56 MP > 50 MP
        buf = io.BytesIO()
        huge_img.save(buf, format="JPEG")
        mock_file2 = self._create_mock_upload(buf.getvalue())
        with self.assertRaises(HTTPException) as ctx2:
            self.loop.run_until_complete(
                predict(file=mock_file2, user=self.agro_user)
            )
        self.assertEqual(ctx2.exception.status_code, 400)
        self.assertIn("exceeds the safety limit", ctx2.exception.detail)

    # =========================================================================
    # SCENARIO 07: Directory Traversal Protection
    # =========================================================================
    def test_07_directory_traversal(self):
        """Scenario 07: Attempting directory traversal on asset endpoints returns 403 Forbidden."""
        auth_headers = {
            "Authorization": "Bearer dev-agronomist-key",
            "X-User-Role": "agronomist",
        }
        status, _, _ = self.client.get("/uploads/../../etc/passwd", headers=auth_headers)
        self.assertEqual(status, 403)

        status2, _, _ = self.client.get("/generated/../config.py", headers=auth_headers)
        self.assertEqual(status2, 403)

    # =========================================================================
    # SCENARIO 08: Unauthenticated Asset Access
    # =========================================================================
    def test_08_unauthenticated_asset_access(self):
        """Scenario 08: Requesting protected assets without credentials returns 401 Unauthorized."""
        status, _, _ = self.client.get(f"/uploads/{self.test_asset_name}")
        self.assertEqual(status, 401)

    # =========================================================================
    # SCENARIO 09: Wrong-Role Access Control
    # =========================================================================
    def test_09_wrong_role_asset_access(self):
        """Scenario 09: Role without required permission returns 403 Forbidden."""
        farmer_headers = {
            "Authorization": "Bearer dev-farmer-key",
            "X-User-Role": "farmer",
        }
        status, _, _ = self.client.get("/review-queue", headers=farmer_headers)
        self.assertEqual(status, 403)

    # =========================================================================
    # SCENARIO 10: Authenticated Asset Download
    # =========================================================================
    def test_10_authenticated_asset_download(self):
        """Scenario 10: Authenticated request returns 200 binary image stream with correct headers."""
        agro_headers = {
            "Authorization": "Bearer dev-agronomist-key",
            "X-User-Role": "agronomist",
        }
        status, headers, body = self.client.get(f"/uploads/{self.test_asset_name}", headers=agro_headers)
        self.assertEqual(status, 200)
        self.assertEqual(body, self.valid_image_bytes)
        self.assertEqual(headers.get("x-content-type-options"), "nosniff")

    # =========================================================================
    # SCENARIO 11: Evidence Chain Cryptographic Verification
    # =========================================================================
    def test_11_evidence_chain_cryptographic_verification(self):
        """Scenario 11: Tamper-evident evidence chain passes cryptographic verification across all blocks."""
        verification = evidence_blockchain.verify_chain()
        self.assertTrue(verification["valid"], f"Blockchain verification failed: {verification}")
        self.assertGreater(verification["checked_blocks"], 0)
        self.assertIsNone(verification.get("invalid_block"))

    # =========================================================================
    # SCENARIO 12: Human Review Resolution & Report Reconstruction
    # =========================================================================
    def test_12_human_review_resolution_and_reconstruction(self):
        """Scenario 12: Review resolution block is cryptographically appended and reconstructed into report."""
        import uuid
        report_id = f"CR-TEST-{uuid.uuid4().hex[:8].upper()}"
        initial_data = {
            "image": {"filename": "leaf.jpg"},
            "disease_prediction": "Apple___Apple_scab",
            "severity": {"severity_level": "low"},
        }
        evidence_blockchain.add_block(report_id=report_id, evidence_data=initial_data)

        # Append resolution block
        resolution_data = {
            "decision": "confirmed",
            "reviewer": "authenticated:agronomist",
            "review_notes": "Expert agronomist confirmed early apple scab lesions.",
        }
        evidence_blockchain.add_block(
            report_id=report_id,
            evidence_data=resolution_data,
            block_type="human_review_resolution",
        )

        # Retrieve reconstructed report via endpoint
        agro_headers = {
            "Authorization": "Bearer dev-agronomist-key",
            "X-User-Role": "agronomist",
        }
        status, _, body = self.client.get(f"/traceability/report/{report_id}", headers=agro_headers)
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))

        self.assertTrue(data.get("success"))
        report_data = data["report"].get("evidence_data") or data["report"].get("data")
        self.assertIsNotNone(report_data)
        human_review = report_data.get("human_review", {})
        self.assertTrue(human_review.get("resolved"))
        self.assertEqual(human_review.get("resolution_status"), "confirmed")
        self.assertEqual(human_review.get("reviewer"), "authenticated:agronomist")
        self.assertIn("review_history", report_data)
        self.assertEqual(len(report_data["review_history"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
