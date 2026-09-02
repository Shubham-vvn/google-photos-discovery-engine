"""
Storage Layer — Database Interface for Myntra Discovery Engine

SQLite database interface with schema management, indexing,
and CRUD operations for raw documents, extractions, tags, and aggregated patterns.
"""

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.settings import DB_PATH


class Database:
    """SQLite database interface for the discovery engine."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(DB_PATH)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS raw_documents (
                doc_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_id TEXT NOT NULL,
                author_hash TEXT,
                text_content TEXT NOT NULL,
                timestamp TEXT,
                metadata TEXT,  -- JSON
                ingested_at TEXT NOT NULL,
                UNIQUE(source, source_id)
            );

            CREATE TABLE IF NOT EXISTS extractions (
                extraction_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                segment_index INTEGER DEFAULT 0,
                segment_text TEXT,
                wishlist_motivation TEXT,
                purchase_blocker TEXT,
                uncertainty_types TEXT,  -- JSON array
                shopper_persona TEXT,
                evidence_type TEXT,
                confidence_score REAL,
                llm_model TEXT,
                raw_response TEXT,
                analyzed_at TEXT NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES raw_documents(doc_id)
            );

            CREATE TABLE IF NOT EXISTS tags (
                tag_id TEXT PRIMARY KEY,
                extraction_id TEXT NOT NULL,
                tag_category TEXT NOT NULL,
                tag_value TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES extractions(extraction_id)
            );

            CREATE TABLE IF NOT EXISTS aggregated_patterns (
                pattern_id TEXT PRIMARY KEY,
                blocker_tag TEXT NOT NULL,
                occurrence_count INTEGER,
                weighted_count REAL,
                avg_confidence REAL,
                persona_distribution TEXT,  -- JSON
                sample_doc_ids TEXT,        -- JSON array
                last_updated TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_extractions_doc_id
                ON extractions(doc_id);
            CREATE INDEX IF NOT EXISTS idx_tags_extraction_id
                ON tags(extraction_id);
            CREATE INDEX IF NOT EXISTS idx_extractions_blocker
                ON extractions(purchase_blocker);
            CREATE INDEX IF NOT EXISTS idx_extractions_persona
                ON extractions(shopper_persona);
        """)
        conn.commit()

        # Migrate: add new wishlist-research columns if they don't exist
        for col in ["wishlist_pain_point", "price_behavior", "feature_request", "competitor_mention"]:
            try:
                conn.execute(f"ALTER TABLE extractions ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────
    # Raw Documents
    # ──────────────────────────────────────────────
    def insert_raw_documents(self, documents: List[Dict[str, Any]]):
        """Insert normalized raw documents into SQLite, ignoring duplicates."""
        conn = self._get_conn()
        for doc in documents:
            conn.execute("""
                INSERT OR IGNORE INTO raw_documents
                (doc_id, source, source_id, author_hash,
                 text_content, timestamp, metadata, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["doc_id"],
                doc["source"],
                doc["source_id"],
                doc.get("author_hash"),
                doc["text"],
                doc.get("timestamp"),
                json.dumps(doc.get("metadata", {})),
                doc["ingested_at"],
            ))
        conn.commit()
        conn.close()

    def get_raw_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM raw_documents LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_unanalyzed_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get documents that have not been processed by the LLM extraction pipeline."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT rd.* FROM raw_documents rd
            LEFT JOIN extractions e ON rd.doc_id = e.doc_id
            WHERE e.extraction_id IS NULL
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ──────────────────────────────────────────────
    # Extractions
    # ──────────────────────────────────────────────
    def insert_extraction(self, extraction: Dict[str, Any]):
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO extractions
            (extraction_id, doc_id, segment_index, segment_text,
             wishlist_motivation, purchase_blocker, uncertainty_types,
             shopper_persona, evidence_type, confidence_score,
             llm_model, raw_response, analyzed_at,
             wishlist_pain_point, price_behavior, feature_request, competitor_mention)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            extraction["extraction_id"],
            extraction["doc_id"],
            extraction.get("segment_index", 0),
            extraction.get("segment_text"),
            extraction.get("wishlist_motivation"),
            extraction.get("purchase_blocker"),
            json.dumps(extraction.get("uncertainty_types", [])),
            extraction.get("shopper_persona"),
            extraction.get("evidence_type"),
            extraction.get("confidence_score"),
            extraction.get("llm_model"),
            extraction.get("raw_response"),
            extraction["analyzed_at"],
            extraction.get("wishlist_pain_point"),
            extraction.get("price_behavior"),
            extraction.get("feature_request"),
            extraction.get("competitor_mention"),
        ))
        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────
    # Tags
    # ──────────────────────────────────────────────
    def insert_tags(self, extraction_id: str, tags: Dict[str, Any]):
        conn = self._get_conn()
        for category, value in tags.items():
            if isinstance(value, list):
                for v in value:
                    conn.execute("""
                        INSERT OR IGNORE INTO tags
                        (tag_id, extraction_id, tag_category, tag_value)
                        VALUES (?, ?, ?, ?)
                    """, (str(uuid.uuid4()), extraction_id, category, v))
            elif value:
                conn.execute("""
                    INSERT OR IGNORE INTO tags
                    (tag_id, extraction_id, tag_category, tag_value)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), extraction_id, category, value))
        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────
    # Aggregated Patterns
    # ──────────────────────────────────────────────
    def save_aggregated_patterns(self, patterns: List[Dict[str, Any]]):
        conn = self._get_conn()
        conn.execute("DELETE FROM aggregated_patterns")  # Replace all
        for p in patterns:
            conn.execute("""
                INSERT INTO aggregated_patterns
                (pattern_id, blocker_tag, occurrence_count, weighted_count,
                 avg_confidence, persona_distribution, sample_doc_ids,
                 last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                p["blocker_tag"],
                p["occurrence_count"],
                p["weighted_count"],
                p["avg_confidence"],
                json.dumps(p.get("persona_distribution", {})),
                json.dumps(p.get("sample_texts", [])),
                p.get("last_updated", ""),
            ))
        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────
    # Query Helpers (for Dashboard API & Analysis)
    # ──────────────────────────────────────────────
    def get_overview_stats(self) -> Dict[str, Any]:
        conn = self._get_conn()
        total_docs = conn.execute("SELECT COUNT(*) FROM raw_documents").fetchone()[0]
        total_extractions = conn.execute("SELECT COUNT(*) FROM extractions").fetchone()[0]
        avg_conf = conn.execute("SELECT AVG(confidence_score) FROM extractions").fetchone()[0] or 0.0
        sources_rows = conn.execute("SELECT source, COUNT(*) FROM raw_documents GROUP BY source").fetchall()
        sources = {row[0]: row[1] for row in sources_rows}
        conn.close()
        return {
            "total_documents": total_docs,
            "total_extractions": total_extractions,
            "avg_confidence": round(avg_conf, 3),
            "sources": sources,
        }

    def get_top_blockers(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT blocker_tag, occurrence_count, weighted_count,
                   avg_confidence, persona_distribution, sample_doc_ids
            FROM aggregated_patterns
            ORDER BY weighted_count DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_extractions_by_blocker(self, blocker_tag: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT e.*, rd.source, rd.metadata
            FROM extractions e
            JOIN raw_documents rd ON e.doc_id = rd.doc_id
            JOIN tags t ON e.extraction_id = t.extraction_id
            WHERE t.tag_category = 'purchase_blocker_tag'
              AND t.tag_value = ?
            ORDER BY e.confidence_score DESC
        """, (blocker_tag,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_persona_stats(self) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT shopper_persona, COUNT(*) as count,
                   AVG(confidence_score) as avg_conf
            FROM extractions
            WHERE shopper_persona IS NOT NULL AND shopper_persona != 'Unknown'
            GROUP BY shopper_persona
            ORDER BY count DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_uncertainty_stats(self) -> Dict[str, int]:
        conn = self._get_conn()
        rows = conn.execute("SELECT uncertainty_types FROM extractions WHERE uncertainty_types IS NOT NULL").fetchall()
        conn.close()
        counts = {}
        for r in rows:
            try:
                utypes = json.loads(r[0])
                for u in utypes:
                    counts[u] = counts.get(u, 0) + 1
            except Exception:
                pass
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def get_confidence_distribution(self) -> Dict[str, int]:
        conn = self._get_conn()
        rows = conn.execute("SELECT confidence_score FROM extractions").fetchall()
        conn.close()
        buckets = {"high (0.7-1.0)": 0, "medium (0.4-0.7)": 0, "low (0.0-0.4)": 0}
        for r in rows:
            score = r[0] or 0.0
            if score >= 0.7:
                buckets["high (0.7-1.0)"] += 1
            elif score >= 0.4:
                buckets["medium (0.4-0.7)"] += 1
            else:
                buckets["low (0.0-0.4)"] += 1
        return buckets

    def get_all_extractions(
        self,
        limit: int = 50,
        offset: int = 0,
        blocker: Optional[str] = None,
        persona: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        query = """
            SELECT e.*, rd.source, rd.metadata, rd.timestamp as doc_timestamp
            FROM extractions e
            JOIN raw_documents rd ON e.doc_id = rd.doc_id
            WHERE 1=1
        """
        params = []
        if blocker:
            query += " AND e.purchase_blocker LIKE ?"
            params.append(f"%{blocker}%")
        if persona:
            query += " AND e.shopper_persona = ?"
            params.append(persona)
        if search:
            query += " AND (e.segment_text LIKE ? OR e.purchase_blocker LIKE ? OR e.wishlist_motivation LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY e.confidence_score DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["uncertainty_types"] = json.loads(d.get("uncertainty_types") or "[]")
            except Exception:
                d["uncertainty_types"] = []
            try:
                d["metadata"] = json.loads(d.get("metadata") or "{}")
            except Exception:
                d["metadata"] = {}
            results.append(d)
        return results
