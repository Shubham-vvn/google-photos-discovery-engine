"""
Aggregator

Rolls up individual extractions into pattern-level summaries
for the dashboard: ranked blockers, uncertainty distribution,
persona breakdown, and persona × blocker cross-tabulation.
"""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List


class Aggregator:
    """Aggregates individual extractions into pattern-level summaries."""

    def aggregate(self, extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Produce aggregate statistics from all extractions."""
        return {
            "total_extractions": len(extractions),
            "purchase_blockers": self._aggregate_blockers(extractions),
            "uncertainty_distribution": self._aggregate_uncertainties(extractions),
            "persona_distribution": self._aggregate_personas(extractions),
            "persona_blocker_crosstab": self._crosstab(extractions),
            "confidence_distribution": self._confidence_dist(extractions),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _aggregate_blockers(self, extractions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank purchase blockers by weighted occurrence."""
        blocker_data = defaultdict(lambda: {
            "count": 0, "weighted_count": 0.0,
            "total_confidence": 0.0, "sample_texts": [],
            "personas": Counter()
        })

        for ext in extractions:
            tag = ext.get("tags", {}).get("purchase_blocker_tag")
            if not tag:
                continue
            data = blocker_data[tag]
            conf = ext.get("confidence_score", 0.5)
            data["count"] += 1
            data["weighted_count"] += conf
            data["total_confidence"] += conf
            if len(data["sample_texts"]) < 5:
                data["sample_texts"].append(ext.get("segment_text", ""))
            persona = ext.get("tags", {}).get("persona_tag")
            if persona:
                data["personas"][persona] += 1

        # Sort by weighted count (descending)
        ranked = []
        for tag, data in sorted(
            blocker_data.items(),
            key=lambda x: x[1]["weighted_count"],
            reverse=True
        ):
            ranked.append({
                "blocker_tag": tag,
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

    def _aggregate_uncertainties(self, extractions: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = Counter()
        for ext in extractions:
            tags = ext.get("tags", {}).get("uncertainty_tags", [])
            for tag in tags:
                counts[tag] += 1
        return dict(counts.most_common())

    def _aggregate_personas(self, extractions: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = Counter()
        for ext in extractions:
            persona = ext.get("tags", {}).get("persona_tag")
            if persona:
                counts[persona] += 1
        return dict(counts.most_common())

    def _crosstab(self, extractions: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Cross-tabulate persona × blocker."""
        table = defaultdict(Counter)
        for ext in extractions:
            persona = ext.get("tags", {}).get("persona_tag")
            blocker = ext.get("tags", {}).get("purchase_blocker_tag")
            if persona and blocker:
                table[persona][blocker] += 1
        return {k: dict(v) for k, v in table.items()}

    def _confidence_dist(self, extractions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Distribution of confidence scores in buckets."""
        buckets = {"high (0.7-1.0)": 0, "medium (0.4-0.7)": 0,
                   "low (0.0-0.4)": 0}
        for ext in extractions:
            conf = ext.get("confidence_score", 0)
            if conf >= 0.7:
                buckets["high (0.7-1.0)"] += 1
            elif conf >= 0.4:
                buckets["medium (0.4-0.7)"] += 1
            else:
                buckets["low (0.0-0.4)"] += 1
        return buckets
