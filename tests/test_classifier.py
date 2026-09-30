"""
Tests for Classifier taxonomy mapping in Google Photos Discovery Engine.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.classifier import Classifier


class TestClassifier:

    def setup_method(self):
        self.classifier = Classifier()

    def test_classifier_has_taxonomy_loaded(self):
        assert "retrieval_failure_points" in self.classifier.taxonomy
        assert "remembered_clues" in self.classifier.taxonomy
        assert "forgotten_elements" in self.classifier.taxonomy
        assert "photo_categories" in self.classifier.taxonomy
        assert "user_personas" in self.classifier.taxonomy
        assert len(self.classifier.taxonomy["retrieval_failure_points"]) > 0

    def test_maps_failure_point(self):
        extraction = {
            "retrieval_failure_point": "zero results returned for search query",
            "photo_category": "episodic_life_event",
            "user_persona": "life_documenter",
        }
        tags = self.classifier.classify(extraction)
        assert "failure_point_tag" in tags
        assert tags["failure_point_tag"] in self.classifier.taxonomy["retrieval_failure_points"]

    def test_maps_photo_category(self):
        extraction = {
            "retrieval_failure_point": "overwhelming_results",
            "photo_category": "receipts and paper warranty cards",
            "user_persona": "visual_note_taker",
        }
        tags = self.classifier.classify(extraction)
        assert "photo_category_tag" in tags
        assert tags["photo_category_tag"] in self.classifier.taxonomy["photo_categories"]

    def test_preserves_known_persona(self):
        extraction = {
            "retrieval_failure_point": "zero_results",
            "user_persona": "life_documenter",
        }
        tags = self.classifier.classify(extraction)
        assert tags.get("persona_tag") == "life_documenter"

    def test_maps_remembered_clues(self):
        extraction = {
            "remembered_clues": ["visual_anchor", "location_vibe"],
            "user_persona": "nostalgia_seeker",
        }
        tags = self.classifier.classify(extraction)
        assert "remembered_clue_tags" in tags
        assert isinstance(tags["remembered_clue_tags"], list)

    def test_handles_missing_failure_gracefully(self):
        extraction = {
            "retrieval_failure_point": None,
            "user_persona": "visual_note_taker",
        }
        tags = self.classifier.classify(extraction)
        assert isinstance(tags, dict)

    def test_handles_empty_extraction(self):
        extraction = {}
        tags = self.classifier.classify(extraction)
        assert isinstance(tags, dict)
