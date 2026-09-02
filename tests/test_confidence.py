"""
Task 7.1 — tests/test_confidence.py
Tests that the ConfidenceScorer returns scores in [0, 1] range
and weights evidence correctly across different input scenarios.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.confidence_scorer import ConfidenceScorer


class TestConfidenceScorer:

    def setup_method(self):
        self.scorer = ConfidenceScorer()

    def test_score_returns_float_in_range(self):
        extraction = {
            "wishlist_motivation": "party wear",
            "purchase_blocker": "delivery delay concern",
            "uncertainty_type": ["trust"],
            "shopper_persona": "budget_conscious",
            "evidence_type": "direct_statement",
        }
        doc = {
            "source": "google_play",
            "text": "I ordered a dress but delivery took ten days and I had to cancel.",
            "metadata": {"rating": 2},
        }
        score = self.scorer.score(extraction, doc)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_direct_statement_scores_higher_than_inference(self):
        base_extraction = {
            "wishlist_motivation": "ethnic wear",
            "purchase_blocker": "fabric quality issue",
            "uncertainty_type": ["quality"],
            "shopper_persona": "occasion_shopper",
        }
        doc = {
            "source": "google_play",
            "text": "The fabric quality was cheap polyester instead of the georgette shown in photos. Very disappointed.",
            "metadata": {"rating": 1},
        }

        direct = {**base_extraction, "evidence_type": "direct_statement"}
        inference = {**base_extraction, "evidence_type": "inference"}

        score_direct = self.scorer.score(direct, doc)
        score_inference = self.scorer.score(inference, doc)

        assert score_direct > score_inference

    def test_longer_text_scores_higher(self):
        extraction = {
            "wishlist_motivation": "casual wear",
            "purchase_blocker": "size fit concern",
            "uncertainty_type": ["fit"],
            "shopper_persona": "budget_conscious",
            "evidence_type": "direct_statement",
        }

        short_doc = {
            "source": "google_play",
            "text": "Bad size.",
            "metadata": {"rating": 3},
        }
        long_doc = {
            "source": "google_play",
            "text": "I ordered the kurta in size M expecting a relaxed fit based on the chart. When it arrived, the chest measurement was two inches smaller than listed, the sleeves were too short, and the overall length was way off. The size chart is misleading.",
            "metadata": {"rating": 2},
        }

        score_short = self.scorer.score(extraction, short_doc)
        score_long = self.scorer.score(extraction, long_doc)

        assert score_long > score_short

    def test_complete_extraction_scores_higher(self):
        """An extraction with all fields filled should score higher than one with gaps."""
        doc = {
            "source": "reddit",
            "text": "Detailed review about quality and sizing for a wedding outfit.",
            "metadata": {},
        }

        complete = {
            "wishlist_motivation": "wedding outfit",
            "purchase_blocker": "fabric quality concern",
            "uncertainty_type": ["quality", "fit"],
            "shopper_persona": "occasion_shopper",
            "evidence_type": "direct_statement",
        }
        sparse = {
            "purchase_blocker": "quality concern",
            "evidence_type": "weak_signal",
        }

        score_complete = self.scorer.score(complete, doc)
        score_sparse = self.scorer.score(sparse, doc)

        assert score_complete > score_sparse

    def test_handles_missing_fields_gracefully(self):
        extraction = {}
        doc = {"source": "google_play", "text": "Short.", "metadata": {}}
        score = self.scorer.score(extraction, doc)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_score_never_exceeds_one(self):
        """Even with perfect input, score should never exceed 1.0."""
        extraction = {
            "wishlist_motivation": "wedding lehenga",
            "purchase_blocker": "fabric quality and sizing both bad",
            "uncertainty_type": ["quality", "fit", "trust"],
            "shopper_persona": "occasion_shopper",
            "evidence_type": "direct_statement",
        }
        doc = {
            "source": "reddit",
            "text": " ".join(["This is a very detailed review about quality issues."] * 20),
            "metadata": {"rating": 1, "upvotes": 500},
        }
        score = self.scorer.score(extraction, doc)
        assert score <= 1.0
