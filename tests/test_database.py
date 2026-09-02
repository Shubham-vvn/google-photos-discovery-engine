"""Tests for SQLite database interface."""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import Database


def test_database_crud():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = Database(db_path=db_path)

        # 1. Test inserting raw documents
        docs = [
            {
                "doc_id": "test-doc-1",
                "source": "google_play",
                "source_id": "gp-101",
                "author_hash": "a1b2c3d4",
                "text": "The size chart is confusing so I left it in my wishlist.",
                "timestamp": "2026-08-20T10:00:00Z",
                "metadata": {"rating": 3},
                "ingested_at": "2026-08-29T10:00:00Z",
            }
        ]
        db.insert_raw_documents(docs)

        raw = db.get_raw_documents()
        assert len(raw) == 1
        assert raw[0]["source_id"] == "gp-101"

        # 2. Test inserting extraction and tags
        extraction = {
            "extraction_id": "ext-101",
            "doc_id": "test-doc-1",
            "segment_index": 0,
            "segment_text": "The size chart is confusing so I left it in my wishlist.",
            "wishlist_motivation": "Interested in buying",
            "purchase_blocker": "Confusing size chart",
            "uncertainty_types": ["fit", "size"],
            "shopper_persona": "budget_conscious",
            "evidence_type": "direct_statement",
            "confidence_score": 0.85,
            "llm_model": "gemini-2.0-flash",
            "raw_response": "{}",
            "analyzed_at": "2026-08-29T11:00:00Z",
        }
        db.insert_extraction(extraction)
        db.insert_tags(
            "ext-101",
            {
                "purchase_blocker_tag": "size_uncertainty",
                "uncertainty_tags": ["fit"],
                "persona_tag": "budget_conscious",
            },
        )

        stats = db.get_overview_stats()
        assert stats["total_documents"] == 1
        assert stats["total_extractions"] == 1
        assert stats["avg_confidence"] == 0.85

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
