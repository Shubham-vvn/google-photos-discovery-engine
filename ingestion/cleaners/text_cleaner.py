"""
Text Cleaner

Cleans and normalizes noisy, colloquial user reviews and comments for downstream NLP and LLM tasks.
Handles HTML tags, emojis, bad encodings, URLs, PII patterns, and excessive whitespace.
"""

import html
import re
import emoji
import ftfy


class TextCleaner:
    """Cleans raw user text for downstream NLP/LLM analysis."""

    def clean(self, text: str) -> str:
        if not text or not text.strip():
            return ""

        text = ftfy.fix_text(text)
        text = html.unescape(text)
        text = self._strip_html(text)
        text = self._remove_urls(text)
        text = self._remove_pii(text)
        text = self._handle_emojis(text)
        text = self._collapse_punctuation(text)
        text = self._normalize_whitespace(text)
        return text.strip()

    def _strip_html(self, text: str) -> str:
        return re.sub(r"<[^>]+>", " ", text)

    def _normalize_whitespace(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        # Remove space before punctuation marks (e.g. "quality ." -> "quality.")
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        return text.strip()

    def _handle_emojis(self, text: str) -> str:
        return emoji.demojize(text, delimiters=(" [", "] "))

    def _remove_urls(self, text: str) -> str:
        return re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            " ",
            text,
        )

    def _remove_pii(self, text: str) -> str:
        # Strip phone numbers (10 digits)
        text = re.sub(r"\b[6-9]\d{9}\b", "[PHONE]", text)
        # Strip email addresses
        text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL]", text)
        return text

    def _collapse_punctuation(self, text: str) -> str:
        return re.sub(r"([!?.]){2,}", r"\1", text)

    def is_usable(self, text: str, min_words: int = 5) -> bool:
        """Check if cleaned text contains enough meaningful words."""
        cleaned = re.sub(r"\[[^\]]+\]", "", text).strip()
        return len(cleaned.split()) >= min_words
