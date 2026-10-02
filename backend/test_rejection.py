import unittest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi import UploadFile

# Set testing environment before importing
import os
os.environ["ENVIRONMENT"] = "testing"

from app import predict, startup_event

class TestDiseaseRejection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        os.environ["KERAS_HOME"] = tempfile.mkdtemp()
        try:
            startup_event()
        except Exception as e:
            print("Startup exception (ignored):", e)
            
        image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_images", "sample_leaf.jpg")
        with open(image_path, "rb") as f:
            cls.test_image = f.read()

    def setUp(self):
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def test_incompatible_disease_rejection(self):
        # We patch CropPredictor to return Apple
        # We patch DiseasePredictor to return a Grape disease (e.g. Grape Black Rot)
        # This should trigger disease validation rejection
        with patch("health_predictor.HealthPredictor.predict_image") as mock_health, \
             patch("crop_classifier.CropPredictor.predict_image") as mock_crop, \
             patch("predictor.PlantPredictor.predict_image") as mock_disease:
             
            mock_health.return_value = {"prediction": "diseased", "confidence": 99.0}
            
            # Predict crop: Apple
            mock_crop.return_value = {"prediction": "Apple", "confidence": 95.0, "uncertain": False}
            
            # Predict disease: Grape Black Rot (incompatible with Apple)
            # Make sure it's something that is definitely not apple
            mock_disease.return_value = {
                "prediction": "Grape___Black_rot",
                "confidence": 99.0,
                "probabilities": [0.0]*115, # Mock probabilities
                "class_names": ["Grape___Black_rot"] * 115,
                "top3": [{"class": "Grape___Black_rot", "confidence": 99.0}]
            }
            # Put some high confidence in the probability array
            mock_disease.return_value["probabilities"][0] = 0.99
            
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = "apple_leaf.jpg"
            mock_file.content_type = "image/jpeg"
            mock_file.read = MagicMock(return_value=asyncio.Future())
            mock_file.read.return_value.set_result(self.test_image)
            
            mock_user = {
                "role": "agronomist",
                "auth_type": "apikey",
                "authenticated": "true",
                "identity": "AGRO-7402"
            }
            
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(predict(file=mock_file, user=mock_user))
            
            # Assertions
            self.assertTrue(response.get("success"))
            self.assertEqual(response["status"], "uncertain_prediction")
            
            da = response["disease_analysis"]
            
            # Verify validation status is rejected
            self.assertEqual(da["validation"]["status"], "rejected")
            
            # Verify primary match is None/cleared so we never display raw incompatible
            self.assertIsNone(da["prediction"])
            self.assertEqual(da["top_3"], [])
            
            # Verify raw_top_3 is preserved for audit
            self.assertGreater(len(da["raw_top_3"]), 0)
            self.assertEqual(da["raw_top_3"][0]["class"], "Grape___Black_rot")
            self.assertEqual(da["raw_prediction"], "Grape___Black_rot")

if __name__ == "__main__":
    unittest.main()
