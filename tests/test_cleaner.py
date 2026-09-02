"""Tests for TextCleaner and Deduplicator."""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.cleaners.text_cleaner import TextCleaner
from ingestion.cleaners.deduplicator import Deduplicator


def test_text_cleaner():
    cleaner = TextCleaner()

    # Test HTML stripping
    dirty_html = "<p>Great kurti! <br/>Loved the <b>quality</b>.</p>"
    cleaned = cleaner.clean(dirty_html)
    assert "<" not in cleaned
    assert "Great kurti! Loved the quality." == cleaned

    # Test PII removal
    pii_text = "Call me at 9876543210 or email test@gmail.com for details on this item"
    cleaned_pii = cleaner.clean(pii_text)
    assert "9876543210" not in cleaned_pii
    assert "test@gmail.com" not in cleaned_pii
    assert "[PHONE]" in cleaned_pii
    assert "[EMAIL]" in cleaned_pii

    # Test emoji demojization
    emoji_text = "Loved the dress! ❤️👗"
    cleaned_emoji = cleaner.clean(emoji_text)
    assert "[red_heart]" in cleaned_emoji or "[dress]" in cleaned_emoji


def test_deduplicator():
    dedup = Deduplicator(threshold=0.7)

    doc1 = "The size chart on this dress was completely inaccurate and did not fit me well at all."
    doc2 = "The size chart on this dress was completely inaccurate and did not fit me well at all."
    doc3 = "I loved the color of this shirt for the wedding party next week."

    assert not dedup.is_duplicate("doc1", doc1)
    assert dedup.is_duplicate("doc2", doc2)
    assert not dedup.is_duplicate("doc3", doc3)
