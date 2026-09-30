"""
Preprocessor

Filters irrelevant reviews (billing complaints, account lockouts) and segments
long text into LLM-friendly chunks for extraction.
"""

import re
from typing import Any, Dict, List


class Preprocessor:
    """Filters irrelevant content and segments text for cognitive retrieval analysis."""

    # Keywords indicating photo search, memory retrieval, and browsing behavior
    RELEVANCE_KEYWORDS = [
        "search", "find", "can't find", "cant find", "remember", "forgot",
        "photo", "picture", "image", "video", "album", "scroll", "scrolling",
        "receipt", "screenshot", "medicine", "cafe", "vacation", "trip",
        "query", "face", "tag", "location", "date", "year", "old photo",
        "lost", "disappeared", "looking for", "retrieval", "timeline",
        "years ago", "months ago", "event", "document", "ask photos",
        "results", "zero results", "too many photos", "impossible to find"
    ]

    # Keywords for clearly irrelevant content (billing/subscription spam)
    IRRELEVANT_KEYWORDS = [
        "subscription charge", "google one bill", "payment failed",
        "refund money", "credit card declined", "storage plan price",
        "otp login", "hacked account"
    ]

    def filter_relevant(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep only documents related to photo search and retrieval behavior."""
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
        # Include if has photo search / memory retrieval keywords
        relevant_count = sum(
            1 for kw in self.RELEVANCE_KEYWORDS if kw in text_lower
        )
        return relevant_count >= 1

    def segment(self, text: str, max_chars: int = 1000) -> List[str]:
        """Split long text into sentence-level segments."""
        if len(text) <= max_chars:
            return [text]

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        segments = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= max_chars:
                current = f"{current} {sentence}".strip()
            else:
                if current:
                    segments.append(current)
                current = sentence

        if current:
            segments.append(current)

        return segments if segments else [text]
