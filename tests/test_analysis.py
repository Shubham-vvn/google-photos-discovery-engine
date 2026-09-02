"""
Tests for Phase 3 — AI Analysis Engine components.
Tests Preprocessor, Classifier, ConfidenceScorer, and Aggregator.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.preprocessor import Preprocessor
from analysis.classifier import Classifier
from analysis.confidence_scorer import ConfidenceScorer
from analysis.aggregator import Aggregator


def test_preprocessor_relevance_filter():
    p = Preprocessor()
    # Relevant shopping text
    relevant = [{"doc_id": "1", "text": "I saved a dress in my wishlist but hesitated due to fabric quality and size fit."}]
    # Irrelevant crash / bug text
    irrelevant = [{"doc_id": "2", "text": "App crash error bug when loading update."}]

    filtered = p.filter_relevant(relevant + irrelevant)
    assert len(filtered) == 1
    assert filtered[0]["doc_id"] == "1"


def test_preprocessor_segmentation():
    p = Preprocessor()
    short_text = "Short text."
    segments = p.segment(short_text)
    assert len(segments) == 1
    assert segments[0] == short_text

    long_text = "Sentence one. " * 50
    segments = p.segment(long_text, max_chars=100)
    assert len(segments) > 1


def test_classifier_tag_mapping():
    c = Classifier()
    extraction = {
        "purchase_blocker": "worried about delivery delay and missing package",
        "uncertainty_type": ["trust", "delivery"],
        "shopper_persona": "budget_conscious",
    }
    tags = c.classify(extraction)
    assert "purchase_blocker_tag" in tags
    assert tags["purchase_blocker_tag"] in c.taxonomy["purchase_blockers"]
    assert tags.get("persona_tag") == "budget_conscious"


def test_confidence_scorer():
    scorer = ConfidenceScorer()
    extraction = {
        "wishlist_motivation": "ethnic party wear",
        "purchase_blocker": "fabric quality might differ from photo",
        "uncertainty_type": ["quality"],
        "shopper_persona": "occasion_shopper",
        "evidence_type": "direct_statement",
    }
    doc = {
        "source": "google_play",
        "text": "Detailed review with over twenty words describing the exact product fabric issue and why I didn't buy it.",
        "metadata": {"rating": 2},
    }
    score = scorer.score(extraction, doc)
    assert 0.0 <= score <= 1.0
    assert score > 0.7  # High confidence due to direct statement, high word count, all fields present


def test_aggregator_rollup():
    aggregator = Aggregator()
    extractions = [
        {
            "segment_text": "sample text 1",
            "confidence_score": 0.85,
            "tags": {
                "purchase_blocker_tag": "quality_uncertainty",
                "uncertainty_tags": ["quality"],
                "persona_tag": "occasion_shopper",
            },
        },
        {
            "segment_text": "sample text 2",
            "confidence_score": 0.75,
            "tags": {
                "purchase_blocker_tag": "quality_uncertainty",
                "uncertainty_tags": ["quality", "fit"],
                "persona_tag": "budget_conscious",
            },
        },
    ]
    summary = aggregator.aggregate(extractions)
    assert summary["total_extractions"] == 2
    assert len(summary["purchase_blockers"]) == 1
    assert summary["purchase_blockers"][0]["blocker_tag"] == "quality_uncertainty"
    assert summary["purchase_blockers"][0]["occurrence_count"] == 2
    assert summary["uncertainty_distribution"]["quality"] == 2
    assert summary["persona_distribution"]["occasion_shopper"] == 1
