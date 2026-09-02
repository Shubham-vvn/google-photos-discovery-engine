"""
Preprocessor

Filters irrelevant reviews (app bugs, crash reports) and segments
long text into LLM-friendly chunks for extraction.
"""

import re
from typing import Any, Dict, List


class Preprocessor:
    """Filters irrelevant content and segments text for analysis."""

    # Keywords indicating shopping/purchase behavior
    RELEVANCE_KEYWORDS = [
        "wishlist", "wish list", "saved", "save for later", "cart",
        "buy", "bought", "purchase", "order", "didn't order",
        "waiting", "confused", "not sure", "thinking about",
        "size", "fit", "quality", "worth", "expensive", "cheap",
        "return", "exchange", "review", "rating", "trust",
        "wedding", "occasion", "festival", "party",
        "compare", "similar", "alternative", "option",
        "like", "love", "want", "need", "browse",
        "app", "myntra", "fashion", "clothes", "dress", "shoe",
        "delivery", "refund", "color", "fabric", "material",
        "price", "discount", "sale", "offer", "coupon",
    ]

    # Keywords for clearly irrelevant content (app tech issues)
    IRRELEVANT_KEYWORDS = [
        "crash", "bug", "error", "loading", "slow app",
        "update", "install", "uninstall", "permission",
        "notification spam", "ads", "otp", "login fail",
    ]

    def filter_relevant(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep only documents related to shopping behavior."""
        return [
            doc for doc in documents
            if self._is_relevant(doc.get("text_content", doc.get("text", "")))
        ]

    def _is_relevant(self, text: str) -> bool:
        text_lower = text.lower()
        # Exclude clearly irrelevant (2+ irrelevant keywords = skip)
        irrelevant_count = sum(
            1 for kw in self.IRRELEVANT_KEYWORDS if kw in text_lower
        )
        if irrelevant_count >= 2:
            return False
        # Include if has shopping-related keywords
        relevant_count = sum(
            1 for kw in self.RELEVANCE_KEYWORDS if kw in text_lower
        )
        return relevant_count >= 1

    def segment(self, text: str, max_chars: int = 1000) -> List[str]:
        """Split long text into sentence-level segments."""
        if len(text) <= max_chars:
            return [text]

        sentences = re.split(r'(?<=[.!?])\s+', text)
        segments = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) < max_chars:
                current += (" " if current else "") + sentence
            else:
                if current:
                    segments.append(current)
                current = sentence

        if current:
            segments.append(current)

        return segments if segments else [text[:max_chars]]
