import json
import os
import tempfile
import unittest

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.gettempdir(), "sentinel_test.db")

from backend.app import create_app
from backend.predictor import ModelNotReadyError


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_index_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SentinelGuard", response.data)

    def test_analyze_rejects_empty(self):
        response = self.client.post("/api/analyze", json={"text": "  "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn(payload["status"], {"ok", "training"})

    def test_history_is_list(self):
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_analyze_batch_rejects_empty(self):
        response = self.client.post("/api/analyze-batch", json={"texts": []})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
