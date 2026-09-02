"""
Task 7.1 — tests/test_extractor.py
Tests LLM extractor with mock responses (no real API calls)
and validates JSON parsing, retry delay parsing, and error handling.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ─── Test helper methods without touching the API ──────────────────

class TestLLMExtractorHelpers:
    """Test internal helper methods of LLMExtractor without API calls."""

    def setup_method(self):
        """Patch genai.configure so no real API key is needed."""
        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel"):
            from analysis.llm_extractor import LLMExtractor
            self.extractor = LLMExtractor()

    def test_clean_json_response_plain(self):
        raw = '{"purchase_blocker": "size fit concern"}'
        assert self.extractor._clean_json_response(raw) == raw

    def test_clean_json_response_strips_code_fences(self):
        raw = '```json\n{"purchase_blocker": "quality"}\n```'
        cleaned = self.extractor._clean_json_response(raw)
        assert cleaned == '{"purchase_blocker": "quality"}'
        assert "```" not in cleaned

    def test_clean_json_response_strips_plain_fences(self):
        raw = '```\n{"key": "value"}\n```'
        cleaned = self.extractor._clean_json_response(raw)
        assert cleaned == '{"key": "value"}'

    def test_parse_retry_delay_from_seconds(self):
        error = "429 Resource Exhausted: retry in 4.5s"
        delay = self.extractor._parse_retry_delay(error)
        assert delay == 5.0  # 4.5 + 0.5

    def test_parse_retry_delay_from_seconds_field(self):
        error = "retry_delay { seconds: 10 }"
        delay = self.extractor._parse_retry_delay(error)
        assert delay == 10.5

    def test_parse_retry_delay_capped_at_15(self):
        error = "retry in 30.0s"
        delay = self.extractor._parse_retry_delay(error)
        assert delay == 15.0  # Capped

    def test_parse_retry_delay_default_fallback(self):
        error = "Some random error with no delay info"
        delay = self.extractor._parse_retry_delay(error)
        assert delay == 5.0  # Default


class TestLLMExtractorMocked:
    """Test the extract() method with mocked Gemini responses."""

    def setup_method(self):
        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            from analysis.llm_extractor import LLMExtractor
            self.mock_model_instance = MockModel.return_value
            self.extractor = LLMExtractor()

    def test_extract_success_returns_valid_structure(self):
        mock_json = json.dumps({
            "wishlist_motivation": "ethnic wear for wedding",
            "purchase_blocker": "unsure about fabric quality from photos",
            "uncertainty_type": ["quality"],
            "shopper_persona": "occasion_shopper",
            "evidence_type": "direct_statement"
        })
        mock_response = MagicMock()
        mock_response.text = mock_json
        self.mock_model_instance.generate_content.return_value = mock_response

        result = self.extractor.extract("I wishlisted a lehenga but unsure about fabric quality")

        assert result["status"] == "success"
        assert result["extraction"] is not None
        assert result["extraction"]["purchase_blocker"] == "unsure about fabric quality from photos"
        assert result["extraction"]["shopper_persona"] == "occasion_shopper"
        assert isinstance(result["extraction"]["uncertainty_type"], list)
        assert result["llm_model"] is not None

    def test_extract_normalizes_uncertainty_string_to_list(self):
        """If LLM returns uncertainty_type as a string, it should be wrapped in a list."""
        mock_json = json.dumps({
            "wishlist_motivation": "daily wear",
            "purchase_blocker": "size concern",
            "uncertainty_type": "fit",
            "shopper_persona": "budget_conscious",
            "evidence_type": "inference"
        })
        mock_response = MagicMock()
        mock_response.text = mock_json
        self.mock_model_instance.generate_content.return_value = mock_response

        result = self.extractor.extract("Worried about size fit")

        assert result["status"] == "success"
        assert result["extraction"]["uncertainty_type"] == ["fit"]

    def test_extract_handles_json_parse_error(self):
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON at all"
        self.mock_model_instance.generate_content.return_value = mock_response

        result = self.extractor.extract("Some text")

        assert result["status"] == "json_parse_error"
        assert result["extraction"] is None

    def test_extract_handles_safety_filter(self):
        self.mock_model_instance.generate_content.side_effect = Exception(
            "Response was blocked due to SAFETY reasons"
        )

        result = self.extractor.extract("Some text")

        assert result["status"] == "safety_filtered"
        assert result["extraction"] is None

    def test_extract_handles_code_fenced_json(self):
        mock_json = '```json\n{"purchase_blocker": "delivery delay", "uncertainty_type": ["trust"]}\n```'
        mock_response = MagicMock()
        mock_response.text = mock_json
        self.mock_model_instance.generate_content.return_value = mock_response

        result = self.extractor.extract("Delivery took 10 days")

        assert result["status"] == "success"
        assert result["extraction"]["purchase_blocker"] == "delivery delay"
