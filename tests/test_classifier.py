"""
Task 7.1 — tests/test_classifier.py
Tests that the Classifier correctly maps extracted text to canonical taxonomy tags.
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
        assert "purchase_blockers" in self.classifier.taxonomy
        assert "uncertainty_types" in self.classifier.taxonomy
        assert "shopper_personas" in self.classifier.taxonomy
        assert len(self.classifier.taxonomy["purchase_blockers"]) > 0

    def test_maps_delivery_blocker(self):
        extraction = {
            "purchase_blocker": "worried about delivery taking too long and package getting lost",
            "uncertainty_type": ["trust"],
            "shopper_persona": "budget_conscious",
        }
        tags = self.classifier.classify(extraction)
        assert "purchase_blocker_tag" in tags
        assert tags["purchase_blocker_tag"] in self.classifier.taxonomy["purchase_blockers"]

    def test_maps_quality_blocker(self):
        extraction = {
            "purchase_blocker": "fabric quality looks cheap and different from the product image",
            "uncertainty_type": ["quality"],
            "shopper_persona": "occasion_shopper",
        }
        tags = self.classifier.classify(extraction)
        assert "purchase_blocker_tag" in tags
        # Should map to quality_uncertainty or similar
        blocker_tag = tags["purchase_blocker_tag"]
        assert blocker_tag in self.classifier.taxonomy["purchase_blockers"]

    def test_preserves_known_persona(self):
        extraction = {
            "purchase_blocker": "price too high",
            "uncertainty_type": ["price"],
            "shopper_persona": "budget_conscious",
        }
        tags = self.classifier.classify(extraction)
        assert tags.get("persona_tag") == "budget_conscious"

    def test_maps_uncertainty_tags(self):
        extraction = {
            "purchase_blocker": "not sure if the size will fit",
            "uncertainty_type": ["fit", "quality"],
            "shopper_persona": "trend_follower",
        }
        tags = self.classifier.classify(extraction)
        assert "uncertainty_tags" in tags
        assert isinstance(tags["uncertainty_tags"], list)

    def test_handles_missing_blocker_gracefully(self):
        extraction = {
            "purchase_blocker": None,
            "uncertainty_type": ["trust"],
            "shopper_persona": "budget_conscious",
        }
        tags = self.classifier.classify(extraction)
        # Should not crash; may return a default or empty tag
        assert isinstance(tags, dict)

    def test_handles_empty_extraction(self):
        extraction = {}
        tags = self.classifier.classify(extraction)
        assert isinstance(tags, dict)
