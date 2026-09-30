"""
Classifier

Maps free-text LLM extraction outputs to canonical taxonomy tags
using local sentence-transformer embeddings (all-MiniLM-L6-v2).
Runs 100% locally — no API calls, no cost.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config.settings import TAXONOMY_PATH

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class Classifier:
    """Maps LLM extraction outputs to canonical taxonomy tags."""

    def __init__(self):
        self.taxonomy = self._load_taxonomy()
        self.model = None
        self.mode = "tfidf"

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                print("   📦 Loading embedding model (all-MiniLM-L6-v2)...")
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self.mode = "embedding"
            except Exception:
                self.mode = "tfidf"

        self.tag_embeddings = self._precompute_embeddings()
        print(f"   ✅ Classifier ready (mode: {self.mode})")

    def _load_taxonomy(self) -> Dict[str, List[str]]:
        with open(TAXONOMY_PATH, "r") as f:
            raw = yaml.safe_load(f)
        # Strip inline comments from tag values
        taxonomy = {}
        for category, tags in raw.items():
            taxonomy[category] = [str(t).split("#")[0].strip() for t in tags]
        return taxonomy

    def _precompute_embeddings(self) -> Dict[str, Any]:
        """Pre-compute embeddings/vectors for all taxonomy tags."""
        embeddings = {}
        for category, tags in self.taxonomy.items():
            tag_texts = [tag.replace("_", " ") for tag in tags]
            if self.mode == "embedding" and self.model:
                embs = self.model.encode(tag_texts)
                vectorizer = None
            else:
                vectorizer = TfidfVectorizer(ngram_range=(1, 2))
                embs = vectorizer.fit_transform(tag_texts).toarray()

            embeddings[category] = {
                "tags": tags,
                "embeddings": embs,
                "vectorizer": vectorizer,
            }
        return embeddings

    def classify(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Add canonical tags to an extraction result."""
        tags = {}

        # Map retrieval failure point to canonical tag
        if extraction.get("retrieval_failure_point"):
            tags["failure_point_tag"] = self._find_closest_tag(
                extraction["retrieval_failure_point"], "retrieval_failure_points"
            )

        # Map photo category
        if extraction.get("photo_category"):
            tags["photo_category_tag"] = self._find_closest_tag(
                extraction["photo_category"], "photo_categories"
            )

        # Map remembered clues
        if extraction.get("remembered_clues"):
            valid_clues = self.taxonomy.get("remembered_clues", [])
            raw_clues = extraction["remembered_clues"]
            if isinstance(raw_clues, str):
                raw_clues = [raw_clues]
            validated = [c for c in raw_clues if c in valid_clues]
            for c in raw_clues:
                if c not in valid_clues:
                    matched = self._find_closest_tag(c, "remembered_clues")
                    if matched and matched not in validated:
                        validated.append(matched)
            tags["remembered_clue_tags"] = validated

        # Map forgotten elements
        if extraction.get("forgotten_elements"):
            valid_forgotten = self.taxonomy.get("forgotten_elements", [])
            raw_forgotten = extraction["forgotten_elements"]
            if isinstance(raw_forgotten, str):
                raw_forgotten = [raw_forgotten]
            validated = [f for f in raw_forgotten if f in valid_forgotten]
            for f in raw_forgotten:
                if f not in valid_forgotten:
                    matched = self._find_closest_tag(f, "forgotten_elements")
                    if matched and matched not in validated:
                        validated.append(matched)
            tags["forgotten_element_tags"] = validated

        # Map user persona
        if extraction.get("user_persona"):
            valid_personas = self.taxonomy.get("user_personas", [])
            if extraction["user_persona"] in valid_personas:
                tags["persona_tag"] = extraction["user_persona"]
            else:
                tags["persona_tag"] = self._find_closest_tag(
                    extraction["user_persona"], "user_personas"
                )

        return tags

    def _find_closest_tag(
        self, text: str, category: str, threshold: float = 0.15
    ) -> Optional[str]:
        """Find the closest canonical tag using embedding or TF-IDF similarity."""
        if category not in self.tag_embeddings:
            return None

        cat_info = self.tag_embeddings[category]
        cat_embs = cat_info["embeddings"]

        if len(cat_embs) == 0:
            return None

        clean_text = str(text).replace("_", " ")
        if self.mode == "embedding" and self.model:
            text_emb = self.model.encode([clean_text])
        else:
            vectorizer = cat_info.get("vectorizer")
            if vectorizer is None:
                return None
            text_emb = vectorizer.transform([clean_text]).toarray()

        similarities = cosine_similarity(text_emb, cat_embs)[0]

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= threshold:
            return cat_info["tags"][best_idx]
        return None  # No close match — potential "emerging pattern"
