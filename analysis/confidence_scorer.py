"""
Confidence Scorer

Computes a composite confidence score (0.0–1.0) for each extraction
using 4 weighted factors: evidence type, text specificity,
extraction completeness, and source reliability.
"""

import json
from typing import Any, Dict


class ConfidenceScorer:
    """Scores the confidence of each extraction on a 0.0–1.0 scale."""

    WEIGHTS = {
        "evidence_type": 0.40,
        "text_specificity": 0.25,
        "extraction_completeness": 0.20,
        "source_reliability": 0.15,
    }

    EVIDENCE_SCORES = {
        "direct_statement": 1.0,
        "inference": 0.6,
        "weak_signal": 0.3,
    }

    def score(self, extraction: Dict[str, Any], document: Dict[str, Any]) -> float:
        """Compute composite confidence score."""
        scores = {
            "evidence_type": self._score_evidence_type(extraction),
            "text_specificity": self._score_specificity(
                document.get("text_content", document.get("text", ""))
            ),
            "extraction_completeness": self._score_completeness(extraction),
            "source_reliability": self._score_source(document),
        }

        total = sum(
            scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )
        return round(min(max(total, 0.0), 1.0), 3)

    def _score_evidence_type(self, extraction: Dict[str, Any]) -> float:
        evidence = extraction.get("evidence_type", "weak_signal")
        return self.EVIDENCE_SCORES.get(evidence, 0.3)

    def _score_specificity(self, text: str) -> float:
        """Longer, more detailed text = higher specificity."""
        word_count = len(text.split())
        if word_count >= 50:
            return 1.0
        elif word_count >= 20:
            return 0.7
        elif word_count >= 10:
            return 0.4
        return 0.2

    def _score_completeness(self, extraction: Dict[str, Any]) -> float:
        """More fields extracted = more confident overall."""
        fields = ["wishlist_motivation", "purchase_blocker",
                  "uncertainty_type", "shopper_persona"]
        filled = sum(1 for f in fields if extraction.get(f))
        return filled / len(fields)

    def _score_source(self, document: Dict[str, Any]) -> float:
        """Score based on source type and metadata."""
        source = document.get("source", "")
        metadata_raw = document.get("metadata", {})

        # Handle metadata stored as JSON string (from SQLite)
        if isinstance(metadata_raw, str):
            try:
                metadata = json.loads(metadata_raw)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        else:
            metadata = metadata_raw

        base_score = 0.5
        if source == "google_play":
            base_score = 0.7  # Reviews tend to be more specific
            if metadata.get("rating"):
                base_score += 0.1
        elif source == "reddit":
            base_score = 0.6
            upvotes = metadata.get("upvotes", 0)
            if isinstance(upvotes, (int, float)):
                if upvotes > 10:
                    base_score += 0.2
                elif upvotes > 3:
                    base_score += 0.1

        return min(base_score, 1.0)
