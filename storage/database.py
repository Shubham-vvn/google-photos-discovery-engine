"""
Storage Layer — Database Interface for Google Photos Discovery Engine

SQLite database interface with schema management, indexing,
and CRUD operations for raw documents, cognitive extractions, tags, and aggregated retrieval patterns.
"""

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.settings import DB_PATH


class Database:
    """SQLite database interface for the Google Photos discovery engine."""

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
                photo_category TEXT,
                target_photo_description TEXT,
                remembered_clues TEXT,       -- JSON array
                remembered_details TEXT,
                forgotten_elements TEXT,     -- JSON array
                search_query_attempted TEXT,
                search_behavior TEXT,
                retrieval_failure_point TEXT,
                user_frustration_detail TEXT,
                user_persona TEXT,
                evidence_type TEXT,
                confidence_score REAL,
                feature_request TEXT,
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
                failure_tag TEXT NOT NULL,
                occurrence_count INTEGER,
                weighted_count REAL,
                avg_confidence REAL,
                persona_distribution TEXT,  -- JSON
                sample_doc_ids TEXT,        -- JSON array
                last_updated TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_extractions_doc_id ON extractions(doc_id);
            CREATE INDEX IF NOT EXISTS idx_tags_extraction_id ON tags(extraction_id);
            CREATE INDEX IF NOT EXISTS idx_extractions_failure ON extractions(retrieval_failure_point);
            CREATE INDEX IF NOT EXISTS idx_extractions_persona ON extractions(user_persona);
            CREATE INDEX IF NOT EXISTS idx_extractions_category ON extractions(photo_category);
        """)
        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────
    # Raw Documents
    # ──────────────────────────────────────────────
    def insert_raw_documents(self, documents: List[Dict[str, Any]]):
        """Insert normalized raw documents into SQLite, ignoring duplicates."""
        conn = self._get_conn()
        for doc in documents:
            text = doc.get("text_content") or doc.get("text", "")
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
                text,
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
        """Get documents that have not been processed by the extraction pipeline."""
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
        rem_clues = extraction.get("remembered_clues", [])
        if isinstance(rem_clues, list):
            rem_clues_json = json.dumps(rem_clues)
        else:
            rem_clues_json = json.dumps([rem_clues] if rem_clues else [])

        forg_elem = extraction.get("forgotten_elements", [])
        if isinstance(forg_elem, list):
            forg_elem_json = json.dumps(forg_elem)
        else:
            forg_elem_json = json.dumps([forg_elem] if forg_elem else [])

        conn.execute("""
            INSERT OR REPLACE INTO extractions
            (extraction_id, doc_id, segment_index, segment_text,
             photo_category, target_photo_description,
             remembered_clues, remembered_details,
             forgotten_elements, search_query_attempted,
             search_behavior, retrieval_failure_point,
             user_frustration_detail, user_persona,
             evidence_type, confidence_score, feature_request,
             llm_model, raw_response, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            extraction["extraction_id"],
            extraction["doc_id"],
            extraction.get("segment_index", 0),
            extraction.get("segment_text"),
            extraction.get("photo_category"),
            extraction.get("target_photo_description"),
            rem_clues_json,
            extraction.get("remembered_details"),
            forg_elem_json,
            extraction.get("search_query_attempted"),
            extraction.get("search_behavior"),
            extraction.get("retrieval_failure_point"),
            extraction.get("user_frustration_detail"),
            extraction.get("user_persona"),
            extraction.get("evidence_type"),
            extraction.get("confidence_score"),
            extraction.get("feature_request"),
            extraction.get("llm_model"),
            extraction.get("raw_response"),
            extraction["analyzed_at"],
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
                    """, (str(uuid.uuid4()), extraction_id, category, str(v)))
            elif value:
                conn.execute("""
                    INSERT OR IGNORE INTO tags
                    (tag_id, extraction_id, tag_category, tag_value)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), extraction_id, category, str(value)))
        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────
    # Aggregated Patterns
    # ──────────────────────────────────────────────
    def save_aggregated_patterns(self, patterns: List[Dict[str, Any]]):
        conn = self._get_conn()
        conn.execute("DELETE FROM aggregated_patterns")
        for p in patterns:
            tag = p.get("failure_tag") or p.get("blocker_tag", "unknown")
            conn.execute("""
                INSERT INTO aggregated_patterns
                (pattern_id, failure_tag, occurrence_count, weighted_count,
                 avg_confidence, persona_distribution, sample_doc_ids,
                 last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                tag,
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
    # Query Helpers for Dashboard API & Reporting
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

    def get_top_failure_points(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT failure_tag, occurrence_count, weighted_count,
                   avg_confidence, persona_distribution, sample_doc_ids
            FROM aggregated_patterns
            ORDER BY weighted_count DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        if not rows:
            # Fallback directly to extractions table if aggregated_patterns hasn't been run
            conn = self._get_conn()
            fallback_rows = conn.execute("""
                SELECT retrieval_failure_point as failure_tag, COUNT(*) as occurrence_count,
                       ROUND(SUM(confidence_score), 2) as weighted_count,
                       ROUND(AVG(confidence_score), 3) as avg_confidence
                FROM extractions
                WHERE retrieval_failure_point IS NOT NULL
                GROUP BY retrieval_failure_point
                ORDER BY weighted_count DESC
                LIMIT ?
            """, (limit,)).fetchall()
            conn.close()
            return [dict(r) for r in fallback_rows]
        return [dict(r) for r in rows]

    # Backward compatibility alias
    def get_top_blockers(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.get_top_failure_points(limit=limit)

    def get_remembered_clues_stats(self) -> Dict[str, int]:
        conn = self._get_conn()
        rows = conn.execute("SELECT remembered_clues FROM extractions WHERE remembered_clues IS NOT NULL").fetchall()
        conn.close()
        counts: Dict[str, int] = {}
        for r in rows:
            try:
                clues = json.loads(r[0])
                for c in clues:
                    counts[c] = counts.get(c, 0) + 1
            except Exception:
                pass
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def get_forgotten_elements_stats(self) -> Dict[str, int]:
        conn = self._get_conn()
        rows = conn.execute("SELECT forgotten_elements FROM extractions WHERE forgotten_elements IS NOT NULL").fetchall()
        conn.close()
        counts: Dict[str, int] = {}
        for r in rows:
            try:
                elem = json.loads(r[0])
                for e in elem:
                    counts[e] = counts.get(e, 0) + 1
            except Exception:
                pass
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def get_photo_categories_stats(self) -> Dict[str, int]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT photo_category, COUNT(*) as count
            FROM extractions
            WHERE photo_category IS NOT NULL
            GROUP BY photo_category
            ORDER BY count DESC
        """).fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}

    def get_search_behavior_stats(self) -> Dict[str, int]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT search_behavior, COUNT(*) as count
            FROM extractions
            WHERE search_behavior IS NOT NULL
            GROUP BY search_behavior
            ORDER BY count DESC
        """).fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}

    def get_persona_stats(self) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT user_persona, COUNT(*) as count,
                   ROUND(AVG(confidence_score), 3) as avg_conf
            FROM extractions
            WHERE user_persona IS NOT NULL AND user_persona != 'Unknown'
            GROUP BY user_persona
            ORDER BY count DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

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
        failure_point: Optional[str] = None,
        persona: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        # backward compatibility
        blocker: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        query = """
            SELECT e.*, rd.source, rd.metadata, rd.timestamp as doc_timestamp
            FROM extractions e
            JOIN raw_documents rd ON e.doc_id = rd.doc_id
            WHERE 1=1
        """
        params = []
        target_failure = failure_point or blocker
        if target_failure:
            query += " AND e.retrieval_failure_point LIKE ?"
            params.append(f"%{target_failure}%")
        if persona:
            query += " AND e.user_persona = ?"
            params.append(persona)
        if category:
            query += " AND e.photo_category = ?"
            params.append(category)
        if search:
            query += " AND (e.segment_text LIKE ? OR e.target_photo_description LIKE ? OR e.user_frustration_detail LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY e.confidence_score DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["remembered_clues"] = json.loads(d.get("remembered_clues") or "[]")
            except Exception:
                d["remembered_clues"] = []
            try:
                d["forgotten_elements"] = json.loads(d.get("forgotten_elements") or "[]")
            except Exception:
                d["forgotten_elements"] = []
            try:
                d["metadata"] = json.loads(d.get("metadata") or "{}")
            except Exception:
                d["metadata"] = {}
            results.append(d)
        return results
