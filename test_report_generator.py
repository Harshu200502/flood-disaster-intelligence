
import unittest
from unittest.mock import patch

import report_generator


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        self.scenario = {
            "location": "Chennai",
            "source": "SIMULATED DEMO DATA",
        }
        self.risk = {
            "risk_level": "High",
            "basis": "Illustrative demo classification",
        }
        self.guidance = [
            {
                "source": "flood_guidance.txt",
                "text": (
                    "During flooding, avoid walking or driving "
                    "through floodwater."
                ),
                "score": 0.339,
            }
        ]

    def test_fallback_when_api_key_is_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            result = report_generator.generate_flood_report(
                self.scenario,
                self.risk,
                self.guidance,
            )

        self.assertEqual(result["status"], "fallback")
        self.assertIn("not an AI-generated report", result["warning"])
        self.assertEqual(
            result["evidence"][0]["source"],
            "flood_guidance.txt",
        )

    def test_successful_gemini_response(self):
        class FakeResponse:
            text = "Situation overview: Demo report."

        class FakeModels:
            def generate_content(self, **kwargs):
                return FakeResponse()

        class FakeClient:
            def __init__(self, api_key):
                self.models = FakeModels()

        with patch.dict(
            "os.environ",
            {
                "GEMINI_API_KEY": "test-key",
                "GEMINI_MODEL": "test-model",
            },
        ), patch.object(
            report_generator.genai,
            "Client",
            FakeClient,
        ):
            result = report_generator.generate_flood_report(
                self.scenario,
                self.risk,
                self.guidance,
            )

        self.assertEqual(result["status"], "llm_generated")
        self.assertIn("Demo report", result["report"])
        self.assertEqual(
            result["evidence"][0]["source"],
            "flood_guidance.txt",
        )

    def test_api_failure_returns_safe_fallback(self):
        class FakeClient:
            def __init__(self, api_key):
                self.models = self

            def generate_content(self, **kwargs):
                raise RuntimeError("private test error detail")

        with patch.dict(
            "os.environ",
            {
                "GEMINI_API_KEY": "test-key",
                "GEMINI_MODEL": "test-model",
            },
        ), patch.object(
            report_generator.genai,
            "Client",
            FakeClient,
        ):
            result = report_generator.generate_flood_report(
                self.scenario,
                self.risk,
                self.guidance,
            )

        self.assertEqual(result["status"], "fallback")
        self.assertIn("report generation failed", result["warning"])
        self.assertNotIn("private test error detail", result["warning"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
