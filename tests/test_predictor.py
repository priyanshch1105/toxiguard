import json
import os
import unittest

from ml.config import MODEL_PATH, VECTORIZER_PATH


@unittest.skipUnless(
    os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH),
    "trained model artifacts are required",
)
class PredictorTests(unittest.TestCase):
    def test_sample_cases(self):
        from backend.predictor import classify_text

        cases_path = os.path.join(os.path.dirname(__file__), "sample_cases.json")
        with open(cases_path, "r") as handle:
            cases = json.load(handle)
        for case in cases:
            result = classify_text(case["text"])
            self.assertEqual(result["is_toxic"], case["expect_toxic"], case["text"])
            self.assertIn(result["moderation_result"], {"SAFE", "REVIEW", "BLOCK"})
            self.assertEqual(len(result["labels"]), 6)
