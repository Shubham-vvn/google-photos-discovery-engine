"""
Aggregator

Rolls up individual extractions into pattern-level summaries
for the Google Photos Discovery Dashboard: ranked retrieval failure points,
cognitive memory clues distribution, forgotten elements, photo categories,
and persona cross-tabulation.
"""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List


class Aggregator:
    """Aggregates individual cognitive retrieval extractions into pattern summaries."""

    def aggregate(self, extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Produce aggregate statistics from all extractions."""
        return {
            "total_extractions": len(extractions),
            "retrieval_failures": self._aggregate_failures(extractions),
            "remembered_clues": self._aggregate_clues(extractions),
            "forgotten_elements": self._aggregate_forgotten(extractions),
            "photo_categories": self._aggregate_categories(extractions),
            "persona_distribution": self._aggregate_personas(extractions),
            "persona_failure_crosstab": self._crosstab(extractions),
            "confidence_distribution": self._confidence_dist(extractions),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _aggregate_failures(self, extractions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank retrieval failure modes by weighted occurrence."""
        failure_data = defaultdict(lambda: {
            "count": 0, "weighted_count": 0.0,
            "total_confidence": 0.0, "sample_texts": [],
            "personas": Counter()
        })

        for ext in extractions:
            tag = ext.get("tags", {}).get("failure_point_tag") or ext.get("retrieval_failure_point")
            if not tag:
                continue
            data = failure_data[tag]
            conf = ext.get("confidence_score", 0.5)
            data["count"] += 1
            data["weighted_count"] += conf
            data["total_confidence"] += conf
            if len(data["sample_texts"]) < 5:
                sample = ext.get("user_frustration_detail") or ext.get("segment_text", "")
                if sample:
                    data["sample_texts"].append(sample)
            persona = ext.get("tags", {}).get("persona_tag") or ext.get("user_persona")
            if persona:
                data["personas"][persona] += 1

        ranked = []
        for tag, data in sorted(
            failure_data.items(),
            key=lambda x: x[1]["weighted_count"],
            reverse=True
        ):
            ranked.append({
                "failure_tag": tag,
                "occurrence_count": data["count"],
                "weighted_count": round(data["weighted_count"], 2),
                "avg_confidence": round(
                    data["total_confidence"] / data["count"], 3
                ) if data["count"] > 0 else 0.0,
                "sample_texts": data["sample_texts"],
                "persona_distribution": dict(data["personas"]),
                "last_updated": datetime.utcnow().isoformat(),
            })
        return ranked

    def _aggregate_clues(self, extractions: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = Counter()
        for ext in extractions:
            tags = ext.get("tags", {}).get("remembered_clue_tags") or ext.get("remembered_clues", [])
            if isinstance(tags, str):
                tags = [tags]
            for tag in tags:
                counts[tag] += 1
        return dict(counts.most_common())

    def _aggregate_forgotten(self, extractions: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = Counter()
        for ext in extractions:
            tags = ext.get("tags", {}).get("forgotten_element_tags") or ext.get("forgotten_elements", [])
            if isinstance(tags, str):
                tags = [tags]
            for tag in tags:
                counts[tag] += 1
        return dict(counts.most_common())

    def _aggregate_categories(self, extractions: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = Counter()
        for ext in extractions:
            cat = ext.get("tags", {}).get("photo_category_tag") or ext.get("photo_category")
            if cat:
                counts[cat] += 1
        return dict(counts.most_common())

    def _aggregate_personas(self, extractions: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = Counter()
        for ext in extractions:
            persona = ext.get("tags", {}).get("persona_tag") or ext.get("user_persona")
            if persona:
                counts[persona] += 1
        return dict(counts.most_common())

    def _crosstab(self, extractions: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Cross-tabulate persona × failure mode."""
        table = defaultdict(Counter)
        for ext in extractions:
            persona = ext.get("tags", {}).get("persona_tag") or ext.get("user_persona")
            failure = ext.get("tags", {}).get("failure_point_tag") or ext.get("retrieval_failure_point")
            if persona and failure:
                table[persona][failure] += 1
        return {k: dict(v) for k, v in table.items()}

    def _confidence_dist(self, extractions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Distribution of confidence scores in buckets."""
        buckets = {
            "high (0.7-1.0)": 0,
            "medium (0.4-0.7)": 0,
            "low (0.0-0.4)": 0,
        }
        for ext in extractions:
            conf = ext.get("confidence_score", 0)
            if conf >= 0.7:
                buckets["high (0.7-1.0)"] += 1
            elif conf >= 0.4:
                buckets["medium (0.4-0.7)"] += 1
            else:
                buckets["low (0.0-0.4)"] += 1
        return buckets
