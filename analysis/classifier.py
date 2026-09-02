"""
Classifier

Maps free-text LLM extraction outputs to canonical taxonomy tags
using local sentence-transformer embeddings (all-MiniLM-L6-v2).
Runs 100% locally — no API calls, no cost.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import yaml
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from config.settings import TAXONOMY_PATH


class Classifier:
    """Maps LLM extraction outputs to canonical taxonomy tags."""

    def __init__(self):
        # Load local embedding model (free, runs on CPU, ~80MB)
        print("   📦 Loading embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.taxonomy = self._load_taxonomy()
        self.tag_embeddings = self._precompute_embeddings()
        print("   ✅ Classifier ready")

    def _load_taxonomy(self) -> Dict[str, List[str]]:
        with open(TAXONOMY_PATH, "r") as f:
            raw = yaml.safe_load(f)
        # Strip inline comments from tag values
        taxonomy = {}
        for category, tags in raw.items():
            taxonomy[category] = [str(t).split("#")[0].strip() for t in tags]
        return taxonomy

    def _precompute_embeddings(self) -> Dict[str, Any]:
        """Pre-compute embeddings for all taxonomy tags (done once at startup)."""
        embeddings = {}
        for category, tags in self.taxonomy.items():
            tag_texts = [tag.replace("_", " ") for tag in tags]
            embs = self.model.encode(tag_texts)
            embeddings[category] = {
                "tags": tags,
                "embeddings": embs,
            }
        return embeddings

    def classify(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Add canonical tags to an extraction result."""
        tags = {}

        # Map purchase_blocker to canonical tag
        if extraction.get("purchase_blocker"):
            tags["purchase_blocker_tag"] = self._find_closest_tag(
                extraction["purchase_blocker"], "purchase_blockers"
            )

        # Map uncertainty_type (already categorical, just validate)
        if extraction.get("uncertainty_type"):
            valid_types = self.taxonomy.get("uncertainty_types", [])
            validated = [
                t for t in extraction["uncertainty_type"]
                if t in valid_types
            ]
            # For unrecognized types, try semantic matching
            for t in extraction["uncertainty_type"]:
                if t not in valid_types:
                    matched = self._find_closest_tag(t, "uncertainty_types")
                    if matched and matched not in validated:
                        validated.append(matched)
            tags["uncertainty_tags"] = validated

        # Map shopper_persona (already categorical, just validate)
        if extraction.get("shopper_persona"):
            valid_personas = self.taxonomy.get("shopper_personas", [])
            if extraction["shopper_persona"] in valid_personas:
                tags["persona_tag"] = extraction["shopper_persona"]
            else:
                tags["persona_tag"] = self._find_closest_tag(
                    extraction["shopper_persona"], "shopper_personas"
                )

        return tags

    def _find_closest_tag(
        self, text: str, category: str, threshold: float = 0.3
    ) -> Optional[str]:
        """Find the closest canonical tag using embedding similarity."""
        if category not in self.tag_embeddings:
            return None

        text_emb = self.model.encode([text])
        cat_embs = self.tag_embeddings[category]["embeddings"]

        # Guard against empty embeddings
        if len(cat_embs) == 0:
            return None

        similarities = cosine_similarity(text_emb, cat_embs)[0]

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= threshold:
            return self.tag_embeddings[category]["tags"][best_idx]
        return None  # No close match — potential "emerging pattern"
