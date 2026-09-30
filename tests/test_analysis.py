"""
Tests for AI Analysis Engine components for Google Photos Discovery Engine.
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
    # Relevant photo retrieval text
    relevant = [{"doc_id": "1", "text": "I can't find that old photo from our Goa trip with the beachside cafe and blue chairs."}]
    # Irrelevant billing text
    irrelevant = [{"doc_id": "2", "text": "Subscription charge payment failed google one bill credit card declined."}]

    filtered = p.filter_relevant(relevant + irrelevant)
    assert len(filtered) == 1
    assert filtered[0]["doc_id"] == "1"


def test_preprocessor_segmentation():
    p = Preprocessor()
    short_text = "Short photo retrieval query."
    segments = p.segment(short_text)
    assert len(segments) == 1
    assert segments[0] == short_text

    long_text = "Sentence one describing the photo. " * 50
    segments = p.segment(long_text, max_chars=100)
    assert len(segments) > 1


def test_classifier_tag_mapping():
    c = Classifier()
    extraction = {
        "retrieval_failure_point": "zero results for medicine query",
        "remembered_clues": ["visual_anchor"],
        "user_persona": "visual_note_taker",
    }
    tags = c.classify(extraction)
    assert "failure_point_tag" in tags
    assert tags["failure_point_tag"] in c.taxonomy["retrieval_failure_points"]
    assert tags.get("persona_tag") == "visual_note_taker"


def test_confidence_scorer():
    scorer = ConfidenceScorer()
    extraction = {
        "photo_category": "episodic_life_event",
        "retrieval_failure_point": "overwhelming_results",
        "remembered_clues": ["location_vibe", "visual_anchor"],
        "user_persona": "life_documenter",
        "evidence_type": "direct_statement",
    }
    doc = {
        "source": "google_play",
        "text": "Detailed review with over twenty words describing how I tried searching for our Goa cafe breakfast and got 800 photos.",
        "metadata": {"rating": 2},
    }
    score = scorer.score(extraction, doc)
    assert 0.0 <= score <= 1.0
    assert score > 0.7


def test_aggregator_rollup():
    aggregator = Aggregator()
    extractions = [
        {
            "segment_text": "sample text 1",
            "confidence_score": 0.85,
            "tags": {
                "failure_point_tag": "overwhelming_results",
                "remembered_clue_tags": ["visual_anchor"],
                "persona_tag": "life_documenter",
            },
        },
        {
            "segment_text": "sample text 2",
            "confidence_score": 0.75,
            "tags": {
                "failure_point_tag": "overwhelming_results",
                "remembered_clue_tags": ["visual_anchor", "location_vibe"],
                "persona_tag": "visual_note_taker",
            },
        },
    ]
    summary = aggregator.aggregate(extractions)
    assert summary["total_extractions"] == 2
    assert len(summary["retrieval_failures"]) == 1
    assert summary["retrieval_failures"][0]["failure_tag"] == "overwhelming_results"
    assert summary["retrieval_failures"][0]["occurrence_count"] == 2
    assert summary["remembered_clues"]["visual_anchor"] == 2
    assert summary["persona_distribution"]["life_documenter"] == 1
