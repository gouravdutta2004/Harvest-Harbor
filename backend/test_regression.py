import unittest
import asyncio
import io
from unittest.mock import patch, MagicMock
from fastapi import UploadFile

# Set testing environment before importing
import os
os.environ["ENVIRONMENT"] = "testing"

from app import predict, startup_event

class TestCropInferencePipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need to run startup_event manually to load models
        # But we don't want to fail if keras is restricted
        import tempfile
        os.environ["KERAS_HOME"] = tempfile.mkdtemp()
        try:
            startup_event()
        except Exception as e:
            print("Startup exception (ignored):", e)
            
        image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_images", "sample_leaf.jpg")
        with open(image_path, "rb") as f:
            cls.test_image = f.read()

        cls.crops = [
            "Apple", "Blueberry", "Cherry", "Corn", "Grape", "Orange", "Peach",
            "Pepper", "Potato", "Raspberry", "Soybean", "Squash", "Strawberry", "Tomato"
        ]

    def setUp(self):
        try:
            self.loop = asyncio.get_event_loop()
            if self.loop.is_closed():
                raise RuntimeError("Closed")
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def test_pipeline_for_all_crops(self):
        # Patch predictors to avoid real inference and force pipeline continuation
        with patch("crop_classifier.CropPredictor.predict_image") as mock_crop_predict, \
             patch("health_predictor.HealthPredictor.predict_image") as mock_health_predict:
            
            mock_health_predict.return_value = {"prediction": "diseased", "confidence": 98.0}

            for crop in self.crops:
                with self.subTest(crop=crop):
                    mock_crop_predict.return_value = {
                        "prediction": crop,
                        "confidence": 95.0,
                        "uncertain": False
                    }
                    
                    # Create mock UploadFile
                    mock_file = MagicMock(spec=UploadFile)
                    mock_file.filename = "sample_leaf.jpg"
                    mock_file.content_type = "image/jpeg"
                    mock_file.read = MagicMock(return_value=asyncio.Future())
                    mock_file.read.return_value.set_result(self.test_image)
                    
                    mock_user = {
                        "role": "agronomist",
                        "auth_type": "apikey",
                        "authenticated": "true",
                        "identity": "AGRO-7402"
                    }
                    
                    # Run the async predict function manually
                    loop = asyncio.get_event_loop()
                    response = loop.run_until_complete(predict(file=mock_file, user=mock_user))
                    
                    self.assertTrue(response.get("success"), f"Success flag false for {crop}")
                    self.assertIn("traceability", response, f"No traceability for {crop}")
                    self.assertEqual(response["traceability"]["crop_model"]["prediction"], crop)


class TestReviewQueueUniquenessRegression(unittest.TestCase):
    """Regression test: Review Queue IDs must be globally unique even across multiple reviews of the same report."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        self.temp_dir = tempfile.TemporaryDirectory()
        self.queue_path = Path(self.temp_dir.name) / "test_review_queue.json"
        from review_queue import ReviewQueue
        self.queue = ReviewQueue(self.queue_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_review_id_uniqueness_across_multiple_reviews_for_same_report(self):
        report_id = "CR-TEST-REGRESSION-101"

        # 1. A report can create a review
        item1 = self.queue.enqueue(
            report_id=report_id,
            reasons=["low_confidence"],
            priority="high",
            summary={"score": 0.42}
        )
        self.assertIsNotNone(item1)
        self.assertEqual(item1["report_id"], report_id)

        # 2. The first review receives a unique review_id
        review_id_1 = item1["review_id"]
        self.assertTrue(review_id_1.startswith("REV-"))
        self.assertNotEqual(review_id_1, f"REV-{report_id}")  # Must not be hardcoded to REV-{report_id}

        # 3. Resolve the first review
        res1 = self.queue.resolve(
            review_id=review_id_1,
            reviewer="dr_elena",
            decision="confirmed",
            notes="Initial resolution confirmed"
        )
        self.assertEqual(res1["status"], "resolved")
        self.assertEqual(res1["decision"], "confirmed")

        # 4. Create another review for the same report
        item2 = self.queue.enqueue(
            report_id=report_id,
            reasons=["new_symptoms_reported"],
            priority="medium",
            summary={"score": 0.38}
        )

        # 5. The second review receives a DIFFERENT review_id
        review_id_2 = item2["review_id"]
        self.assertNotEqual(review_id_1, review_id_2)
        self.assertTrue(review_id_2.startswith("REV-"))

        # 6. Both records retain the same report_id
        self.assertEqual(item1["report_id"], report_id)
        self.assertEqual(item2["report_id"], report_id)

        # 7. Resolving the second review does not modify the first resolved record
        res2 = self.queue.resolve(
            review_id=review_id_2,
            reviewer="dr_marcus",
            decision="rejected",
            notes="Secondary resolution rejected"
        )
        self.assertEqual(res2["status"], "resolved")
        self.assertEqual(res2["decision"], "rejected")

        record1_after = self.queue.get(review_id_1)
        record2_after = self.queue.get(review_id_2)

        self.assertIsNotNone(record1_after)
        self.assertIsNotNone(record2_after)
        self.assertEqual(record1_after["review_id"], review_id_1)
        self.assertEqual(record1_after["decision"], "confirmed")
        self.assertEqual(record1_after["reviewer"], "dr_elena")
        self.assertEqual(record1_after["review_notes"], "Initial resolution confirmed")

        self.assertEqual(record2_after["review_id"], review_id_2)
        self.assertEqual(record2_after["decision"], "rejected")
        self.assertEqual(record2_after["reviewer"], "dr_marcus")
        self.assertEqual(record2_after["review_notes"], "Secondary resolution rejected")


class TestUploadInferenceRegression(unittest.TestCase):
    """
    Regression test verifying image upload isolation:
    - Dedicated image uploads produce unique report IDs
    - Returned image filename matches uploaded filename exactly
    - No report ID collision or reuse across consecutive analyses
    - Distinct specimen uploads remain strictly isolated
    """

    def setUp(self):
        try:
            self.loop = asyncio.get_event_loop()
            if self.loop.is_closed():
                raise RuntimeError("Closed")
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        # Load real test leaf image from test_images/
        test_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "test_images", "sample_leaf.jpg"
        )
        with open(test_path, "rb") as f:
            self.leaf_bytes = f.read()

        self.mock_user = {
            "role": "agronomist",
            "auth_type": "apikey",
            "authenticated": "true",
            "identity": "AGRO-7402"
        }

    def _create_mock_upload_file(self, filename: str, content: bytes) -> MagicMock:
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = "image/jpeg"
        mock_file.read = MagicMock(return_value=asyncio.Future())
        mock_file.read.return_value.set_result(content)
        return mock_file

    def test_upload_produces_unique_report_and_matching_filename(self):
        mock_file_1 = self._create_mock_upload_file("leaf_specimen_a.jpg", self.leaf_bytes)
        resp1 = self.loop.run_until_complete(predict(file=mock_file_1, user=self.mock_user))

        self.assertTrue(resp1.get("success"))
        report_id_1 = resp1.get("report_id")
        self.assertTrue(report_id_1.startswith("CR-"))
        self.assertEqual(resp1.get("image", {}).get("filename"), "leaf_specimen_a.jpg")
        self.assertIn("leaf_specimen_a", resp1.get("image", {}).get("url", ""))
        self.assertIn(report_id_1, resp1.get("image", {}).get("url", ""))

        # Second consecutive call with the same filename
        mock_file_2 = self._create_mock_upload_file("leaf_specimen_a.jpg", self.leaf_bytes)
        resp2 = self.loop.run_until_complete(predict(file=mock_file_2, user=self.mock_user))

        self.assertTrue(resp2.get("success"))
        report_id_2 = resp2.get("report_id")
        self.assertTrue(report_id_2.startswith("CR-"))
        self.assertEqual(resp2.get("image", {}).get("filename"), "leaf_specimen_a.jpg")

        # Crucial check: Report IDs must NEVER be reused across runs
        self.assertNotEqual(report_id_1, report_id_2)

    def test_consecutive_uploads_remain_strictly_isolated(self):
        specimen_a = self._create_mock_upload_file("leaf_specimen_a.jpg", self.leaf_bytes)
        resp_a = self.loop.run_until_complete(predict(file=specimen_a, user=self.mock_user))

        specimen_b = self._create_mock_upload_file("leaf_specimen_b.jpg", self.leaf_bytes)
        resp_b = self.loop.run_until_complete(predict(file=specimen_b, user=self.mock_user))

        self.assertNotEqual(resp_a.get("report_id"), resp_b.get("report_id"))
        self.assertEqual(resp_a.get("image", {}).get("filename"), "leaf_specimen_a.jpg")
        self.assertEqual(resp_b.get("image", {}).get("filename"), "leaf_specimen_b.jpg")
        self.assertNotIn("leaf_specimen_b", resp_a.get("image", {}).get("url", ""))
        self.assertNotIn("leaf_specimen_a", resp_b.get("image", {}).get("url", ""))


if __name__ == "__main__":
    unittest.main()

