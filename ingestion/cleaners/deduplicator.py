"""
Deduplicator

Detects near-duplicate user texts across reviews and Reddit comments using MinHash LSH.
"""

from typing import Any, Dict, List
from datasketch import MinHash, MinHashLSH


class Deduplicator:
    """Detects near-duplicate texts using MinHash LSH."""

    def __init__(self, threshold: float = 0.7, num_perm: int = 128):
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self.seen = set()

    def _get_minhash(self, text: str) -> MinHash:
        m = MinHash(num_perm=self.num_perm)
        words = text.lower().split()
        for word in words:
            m.update(word.encode("utf-8"))
        return m

    def is_duplicate(self, doc_id: str, text: str) -> bool:
        if len(text.split()) < 10:
            return False  # Short texts bypass LSH index to prevent hash collision false positives

        mh = self._get_minhash(text)
        duplicates = self.lsh.query(mh)
        if duplicates:
            return True

        if doc_id not in self.seen:
            self.lsh.insert(doc_id, mh)
            self.seen.add(doc_id)
        return False

    def deduplicate(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out near-duplicate documents."""
        unique = []
        for doc in documents:
            doc_identifier = f"{doc.get('source')}_{doc.get('source_id')}"
            if not self.is_duplicate(doc_identifier, doc["text"]):
                unique.append(doc)
        return unique
