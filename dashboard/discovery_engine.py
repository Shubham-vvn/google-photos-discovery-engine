"""
AI Discovery Engine — Interactive Q&A Module

Takes a user's natural-language question, searches the SQLite research
database for relevant evidence (RAG-style across Google Play and Reddit),
and uses Gemini to synthesize a well-formatted, PM-grade answer citing
verbatim customer quotes.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from config.settings import GEMINI_API_KEY, LLM_MODEL, LLM_RPM_LIMIT
from storage.database import Database


class DiscoveryEngine:
    """RAG-powered Q&A engine over the Myntra research database."""

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)
        self.db = Database()
        self.last_request_time = 0.0
        self.rpm_limit = LLM_RPM_LIMIT

    # ──────────────────────────────────────────────
    # Rate Limiting
    # ──────────────────────────────────────────────
    def _rate_limit(self):
        """Enforce Gemini free-tier rate limits."""
        elapsed = time.time() - self.last_request_time
        min_interval = 60.0 / self.rpm_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_request_time = time.time()

    # ──────────────────────────────────────────────
    # Database Search & Evidence Retrieval
    # ──────────────────────────────────────────────
    def _search_evidence(self, question: str) -> Dict[str, Any]:
        """Search the research database for evidence relevant to the question."""
        conn = self.db._get_conn()

        stop_words = {
            "what", "why", "how", "when", "where", "who", "which", "is", "are",
            "do", "does", "did", "the", "a", "an", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "and", "or", "but", "not", "it", "its",
            "this", "that", "these", "those", "can", "could", "would", "should",
            "will", "about", "their", "they", "them", "most", "some", "all",
            "any", "many", "much", "more", "than", "has", "have", "had", "been",
            "was", "were", "be", "being", "into", "between", "after", "before",
            "during", "up", "out", "over", "under", "you", "your", "we", "our",
            "my", "me", "i", "he", "she", "her", "his", "us", "if", "so", "then",
            "there", "here", "also", "just", "very", "really", "too", "well",
            "like", "want", "need", "get", "make", "tell", "say", "know",
            "think", "see", "look", "find", "give", "take", "come", "go",
            "myntra", "users", "customers", "people", "app",
        }
        words = re.findall(r'[a-zA-Z]+', question.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        evidence = {
            "extractions": [],
            "blockers": [],
            "personas": [],
            "total_matches": 0,
        }

        # Keyword matching across database
        if keywords:
            like_clauses = " OR ".join(
                ["e.segment_text LIKE ?", "e.purchase_blocker LIKE ?",
                 "e.wishlist_motivation LIKE ?", "e.wishlist_pain_point LIKE ?",
                 "e.feature_request LIKE ?", "e.competitor_mention LIKE ?",
                 "e.price_behavior LIKE ?", "rd.text_content LIKE ?", "rd.source LIKE ?"]
            )
            all_conditions = []
            all_params = []
            for kw in keywords[:6]:
                all_conditions.append(f"({like_clauses})")
                all_params.extend([f"%{kw}%"] * 9)

            if all_conditions:
                where_clause = " OR ".join(all_conditions)
                query = f"""
                    SELECT e.segment_text, e.purchase_blocker, e.wishlist_motivation,
                           e.shopper_persona, e.confidence_score, e.uncertainty_types,
                           e.wishlist_pain_point, e.feature_request, e.competitor_mention,
                           e.price_behavior, rd.source, rd.text_content
                    FROM extractions e
                    JOIN raw_documents rd ON e.doc_id = rd.doc_id
                    WHERE {where_clause}
                    ORDER BY e.confidence_score DESC
                    LIMIT 25
                """
                rows = conn.execute(query, all_params).fetchall()
                for r in rows:
                    evidence["extractions"].append(dict(r))
                evidence["total_matches"] = len(evidence["extractions"])

        # Fallback if empty
        if not evidence["extractions"]:
            fallback_rows = conn.execute("""
                SELECT e.segment_text, e.purchase_blocker, e.wishlist_motivation,
                       e.shopper_persona, e.confidence_score, e.uncertainty_types,
                       e.wishlist_pain_point, e.feature_request, e.competitor_mention,
                       e.price_behavior, rd.source, rd.text_content
                FROM extractions e
                JOIN raw_documents rd ON e.doc_id = rd.doc_id
                ORDER BY e.confidence_score DESC
                LIMIT 20
            """).fetchall()
            for r in fallback_rows:
                evidence["extractions"].append(dict(r))

        # Blockers from aggregated patterns
        blocker_rows = conn.execute("""
            SELECT blocker_tag, occurrence_count, weighted_count,
                   avg_confidence, sample_doc_ids
            FROM aggregated_patterns
            ORDER BY weighted_count DESC
            LIMIT 10
        """).fetchall()
        evidence["blockers"] = [dict(r) for r in blocker_rows]

        # Persona stats
        persona_rows = conn.execute("""
            SELECT shopper_persona, COUNT(*) as count,
                   AVG(confidence_score) as avg_conf
            FROM extractions
            WHERE shopper_persona IS NOT NULL AND shopper_persona != 'Unknown'
            GROUP BY shopper_persona
            ORDER BY count DESC
        """).fetchall()
        evidence["personas"] = [dict(r) for r in persona_rows]

        # Uncertainty stats
        uncertainty_rows = conn.execute(
            "SELECT uncertainty_types FROM extractions WHERE uncertainty_types IS NOT NULL"
        ).fetchall()
        uncertainty_counts = {}
        for r in uncertainty_rows:
            try:
                utypes = json.loads(r[0])
                for u in utypes:
                    uncertainty_counts[u] = uncertainty_counts.get(u, 0) + 1
            except Exception:
                pass
        evidence["uncertainties"] = uncertainty_counts
        evidence["stats"] = self.db.get_overview_stats()

        conn.close()
        return evidence

    # ──────────────────────────────────────────────
    # LLM Prompting
    # ──────────────────────────────────────────────
    def _build_research_prompt(self, question: str, evidence: Dict[str, Any]) -> str:
        """Build a context-rich prompt using database evidence."""
        quotes = []
        for ext in evidence["extractions"][:18]:
            text = ext.get("segment_text") or ext.get("text_content") or ""
            if text and len(text) > 15:
                source = ext.get("source", "Unknown").upper()
                blocker = ext.get("purchase_blocker", "N/A")
                persona = ext.get("shopper_persona", "N/A")
                quotes.append(
                    f'- [{source}] (Blocker: {blocker}, Persona: {persona}) "{text[:300]}"'
                )

        blocker_lines = []
        for b in evidence["blockers"]:
            blocker_lines.append(
                f'- {b["blocker_tag"]}: {b["occurrence_count"]} occurrences, '
                f'{(b["avg_confidence"]*100):.0f}% confidence'
            )

        persona_lines = [
            f'- {p["shopper_persona"]}: {p["count"]} reviews, {(p["avg_conf"]*100):.0f}% avg confidence'
            for p in evidence["personas"]
        ]

        uncertainty_lines = [
            f"- {k}: {v} occurrences"
            for k, v in sorted(evidence.get("uncertainties", {}).items(), key=lambda x: x[1], reverse=True)[:8]
        ]

        stats = evidence.get("stats", {})

        prompt = f"""You are a senior Product Manager AI assistant for Myntra, India's leading fashion e-commerce platform.
You have access to a real research database containing customer reviews and behavioral analysis about Myntra's wishlist-to-purchase journey.

DATABASE OVERVIEW:
- Total customer documents analyzed: {stats.get('total_documents', 0)}
- Total AI extractions performed: {stats.get('total_extractions', 0)}
- Average extraction confidence: {(stats.get('avg_confidence', 0)*100):.1f}%
- Data sources: {', '.join(stats.get('sources', {}).keys()) or 'Google Play Store, Reddit'}

TOP PURCHASE BLOCKERS (from research):
{chr(10).join(blocker_lines) if blocker_lines else 'No blockers extracted yet.'}

SHOPPER PERSONAS:
{chr(10).join(persona_lines) if persona_lines else 'No personas identified yet.'}

CUSTOMER UNCERTAINTY DIMENSIONS:
{chr(10).join(uncertainty_lines) if uncertainty_lines else 'No uncertainty data yet.'}

RELEVANT CUSTOMER QUOTES & EVIDENCE:
{chr(10).join(quotes) if quotes else 'No matching customer quotes found for this query.'}

---

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer the question using the research data and customer evidence provided above.
2. Structure your answer clearly with headers, bullet points, and bold text for key findings.
3. Cite specific customer quotes when available (use blockquote formatting with >).
4. Include relevant statistics (percentages, counts) from the data.
5. End with actionable "Product Recommendations" where appropriate.
6. Keep the tone professional and insightful — like a PM presenting findings to stakeholders.
7. Format the response in Markdown.
"""
        return prompt

    def _build_general_prompt(self, question: str) -> str:
        return f"""You are a senior Product Manager AI assistant specializing in fashion e-commerce, specifically Myntra (India's leading fashion platform).

The user is asking a question that our research database doesn't have direct evidence for, but you can provide general industry knowledge and best practices.

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer based on general e-commerce and fashion industry knowledge.
2. Be clear that this is general knowledge, NOT from our specific research data.
3. Where possible, relate your answer to Myntra's context (Indian fashion e-commerce).
4. Structure your answer with clear headers and bullet points in Markdown.
"""

    # ──────────────────────────────────────────────
    # Main Ask Method
    # ──────────────────────────────────────────────
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Answer a user question using the 3-tier strategy:
        1. Research-backed (RAG with Gemini)
        2. General LLM knowledge
        3. Not Found fallback
        """
        if not question or not question.strip():
            return {
                "answer": "Please enter a question to get started.",
                "source_type": "not_found",
                "evidence_used": [],
                "confidence": 0,
            }

        question = question.strip()

        # Step 1: Search the research database
        evidence = self._search_evidence(question)
        has_research_data = (
            len(evidence["extractions"]) > 0
            or len(evidence["blockers"]) > 0
        )

        # Format evidence items for frontend display
        evidence_used = []
        for ext in evidence["extractions"][:6]:
            text = ext.get("segment_text") or ext.get("text_content") or ""
            if text:
                evidence_used.append({
                    "text": text[:260],
                    "source": ext.get("source", "UNKNOWN").upper().replace("_", " "),
                    "blocker": ext.get("purchase_blocker"),
                    "persona": ext.get("shopper_persona"),
                    "confidence": ext.get("confidence_score", 0.9),
                })

        avg_conf = round(
            sum(e.get("confidence", 0.85) for e in evidence_used) /
            max(len(evidence_used), 1), 3
        )

        # Step 2: Try research-backed answer with Gemini
        if has_research_data:
            try:
                self._rate_limit()
                prompt = self._build_research_prompt(question, evidence)
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=2048,
                    )
                )

                return {
                    "answer": response.text,
                    "source_type": "research",
                    "evidence_used": evidence_used,
                    "confidence": avg_conf,
                    "stats": {
                        "extractions_matched": len(evidence["extractions"]),
                        "blockers_available": len(evidence["blockers"]),
                        "personas_available": len(evidence["personas"]),
                    }
                }

            except Exception as e:
                print(f"[DiscoveryEngine] Gemini error for research query: {e}")
                # Fall through to general LLM attempt

        # Step 3: Try general LLM knowledge
        try:
            self._rate_limit()
            prompt = self._build_general_prompt(question)
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=1536,
                )
            )
            return {
                "answer": response.text,
                "source_type": "llm",
                "evidence_used": [],
                "confidence": 0,
            }

        except Exception as e:
            return {
                "answer": (
                    "❌ **Answer Not Found**\n\n"
                    "The AI Discovery Engine could not find a relevant answer "
                    "for this question. Try asking about:\n\n"
                    "- Customer survey findings and drop-off discouragements\n"
                    "- Top purchase blockers and hesitation patterns\n"
                    "- Shopper personas (Deal Hunter, Style Explorer, etc.)\n"
                    "- Return policy friction and photo reality doubts"
                ),
                "source_type": "not_found",
                "evidence_used": [],
                "confidence": 0,
            }
