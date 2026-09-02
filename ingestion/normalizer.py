"""
Normalizer

Normalizes raw scraped documents into a unified schema with anonymized author hashes and UUIDs.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List


class Normalizer:
    """Normalizes raw scraped documents into a unified schema."""

    def normalize(self, document: Dict[str, Any]) -> Dict[str, Any]:
        author_raw = document.get("author") or document.get("source_id", "unknown")
        return {
            "doc_id": str(uuid.uuid4()),
            "source": document["source"],
            "source_id": str(document["source_id"]),
            "author_hash": self._hash_author(author_raw),
            "text": document["text"],
            "timestamp": document.get("metadata", {}).get("timestamp") or document.get("timestamp"),
            "metadata": document.get("metadata", {}),
            "ingested_at": datetime.utcnow().isoformat(),
        }

    def normalize_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.normalize(doc) for doc in documents]

    def _hash_author(self, author: str) -> str:
        return hashlib.sha256(author.encode("utf-8")).hexdigest()[:16]
