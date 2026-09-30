#!/usr/bin/env python3
"""
CLI script to run the full analysis pipeline.
Takes ingested documents, runs LLM extraction, classification,
confidence scoring, and aggregation.

Usage:
    python scripts/run_analysis.py
    python scripts/run_analysis.py --limit 100    # Analyze only 100 docs
    python scripts/run_analysis.py --skip-llm     # Re-run classification only
"""

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(
        description="Myntra Discovery Engine — Analysis Pipeline"
    )
    parser.add_argument(
        "--limit", type=int, default=500,
        help="Max documents to analyze per run (default: 500)"
    )
    parser.add_argument(
        "--skip-llm", action="store_true",
        help="Skip LLM extraction (re-run classification/aggregation only)"
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Use high-speed local semantic heuristic extraction (bypasses LLM rate limits)"
    )
    args = parser.parse_args()

    # Validate config
    from config import GEMINI_API_KEY
    if not args.skip_llm and not args.fast:
        if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
            print("❌ GEMINI_API_KEY is required for LLM extraction.", flush=True)
            print("💡 Get a free key at https://aistudio.google.com", flush=True)
            sys.exit(1)

    print("=" * 60, flush=True)
    print("MYNTRA DISCOVERY ENGINE — ANALYSIS PIPELINE", flush=True)
    print("=" * 60, flush=True)
    print(f"  Limit: {args.limit} documents", flush=True)
    print(f"  Skip LLM: {args.skip_llm}", flush=True)
    print(f"  Fast Mode: {args.fast}", flush=True)
    print("=" * 60, flush=True)

    from storage.database import Database
    from analysis.preprocessor import Preprocessor
    from analysis.llm_extractor import LLMExtractor
    from analysis.heuristic_extractor import HeuristicExtractor

    db = Database()

    # Step 1: Get unanalyzed documents
    print("\n[1/6] Fetching unanalyzed documents from database...", flush=True)
    documents = db.get_unanalyzed_documents(limit=args.limit)
    if not documents:
        print("      → No unanalyzed documents found. Run ingestion first.", flush=True)
        sys.exit(0)
    print(f"      → Found {len(documents)} unanalyzed documents", flush=True)

    # Step 2: Relevance filtering
    print("\n[2/6] Filtering for relevance (shopping behavior keywords)...", flush=True)
    preprocessor = Preprocessor()
    relevant_docs = preprocessor.filter_relevant(documents)
    print(f"      → {len(relevant_docs)} relevant documents (filtered out {len(documents) - len(relevant_docs)} irrelevant)", flush=True)

    # Step 3: Extraction, Classification & Progressive Storage
    all_extractions = []
    enriched = []
    if not args.skip_llm:
        print(f"\n[3/6] Running extraction on {len(relevant_docs)} documents...", flush=True)
        extractor = HeuristicExtractor() if args.fast else LLMExtractor()
        from analysis.classifier import Classifier
        from analysis.confidence_scorer import ConfidenceScorer
        classifier = Classifier()
        scorer = ConfidenceScorer()

        for idx, doc in enumerate(relevant_docs, 1):
            text = doc.get("text_content", doc.get("text", ""))
            segments = preprocessor.segment(text)
            if idx % 100 == 0 or idx == 1 or idx == len(relevant_docs):
                print(f"   [{idx}/{len(relevant_docs)}] Analyzing doc {doc['doc_id'][:8]} ({len(segments)} segment(s))...", flush=True)

            for seg_idx, segment in enumerate(segments):
                if args.fast:
                    ext_res = extractor.extract(segment)
                    result = {
                        "extraction": ext_res,
                        "llm_model": "heuristic_semantic_v1",
                        "raw_response": json.dumps(ext_res),
                        "status": "success"
                    }
                else:
                    result = extractor.extract(segment)

                if result["status"] != "success" or not result["extraction"]:
                    print(f"      ↳ Segment {seg_idx+1}: {result['status']}", flush=True)
                    continue

                extraction_data = {
                    "doc_id": doc["doc_id"],
                    "segment_index": seg_idx,
                    "segment_text": segment,
                    "extraction": result["extraction"],
                    "llm_model": result["llm_model"],
                    "raw_response": result["raw_response"],
                }
                
                # Classify & score immediately
                tags = classifier.classify(result["extraction"])
                extraction_data["tags"] = tags
                score = scorer.score(result["extraction"], doc)
                extraction_data["confidence_score"] = score

                # Save immediately to SQLite
                extraction_record = {
                    "extraction_id": str(uuid.uuid4()),
                    "doc_id": doc["doc_id"],
                    "segment_index": seg_idx,
                    "segment_text": segment,
                    "photo_category": result["extraction"].get("photo_category"),
                    "target_photo_description": result["extraction"].get("target_photo_description"),
                    "remembered_clues": result["extraction"].get("remembered_clues", []),
                    "remembered_details": result["extraction"].get("remembered_details"),
                    "forgotten_elements": result["extraction"].get("forgotten_elements", []),
                    "search_query_attempted": result["extraction"].get("search_query_attempted"),
                    "search_behavior": result["extraction"].get("search_behavior"),
                    "retrieval_failure_point": result["extraction"].get("retrieval_failure_point"),
                    "user_frustration_detail": result["extraction"].get("user_frustration_detail"),
                    "user_persona": result["extraction"].get("user_persona"),
                    "evidence_type": result["extraction"].get("evidence_type"),
                    "confidence_score": score,
                    "feature_request": result["extraction"].get("feature_request"),
                    "llm_model": result["llm_model"],
                    "raw_response": result["raw_response"],
                    "analyzed_at": datetime.utcnow().isoformat(),
                }
                db.insert_extraction(extraction_record)
                db.insert_tags(extraction_record["extraction_id"], tags)

                all_extractions.append(extraction_data)
                enriched.append(extraction_data)

                failure = result['extraction'].get('retrieval_failure_point') or 'None'
                persona = result['extraction'].get('user_persona') or 'Unknown'
                print(f"      ↳ Extracted & Saved: failure='{failure}', persona='{persona}', score={score:.2f}", flush=True)

        print(f"      → {len(all_extractions)} successful extractions from {len(relevant_docs)} documents", flush=True)
    else:
        print("\n[3/6] Skipping LLM extraction (--skip-llm flag)", flush=True)
        # Load all extractions and precomputed tags from DB for instant aggregation
        conn = db._get_conn()
        rows = conn.execute("SELECT * FROM extractions").fetchall()
        tag_rows = conn.execute("SELECT extraction_id, tag_category, tag_value FROM tags").fetchall()
        conn.close()

        # Build tag lookup
        tags_by_ext = {}
        for tr in tag_rows:
            eid = tr["extraction_id"]
            cat = tr["tag_category"]
            val = tr["tag_value"]
            if eid not in tags_by_ext:
                tags_by_ext[eid] = {}
            if cat == "uncertainty_tags":
                if "uncertainty_tags" not in tags_by_ext[eid]:
                    tags_by_ext[eid]["uncertainty_tags"] = []
                tags_by_ext[eid]["uncertainty_tags"].append(val)
            else:
                tags_by_ext[eid][cat] = val

        for r in rows:
            row_dict = dict(r)
            eid = row_dict["extraction_id"]
            try:
                utypes = json.loads(row_dict.get("uncertainty_types") or "[]")
            except Exception:
                utypes = []
            ext_obj = {
                "wishlist_motivation": row_dict.get("wishlist_motivation"),
                "purchase_blocker": row_dict.get("purchase_blocker"),
                "uncertainty_type": utypes,
                "shopper_persona": row_dict.get("shopper_persona"),
                "evidence_type": row_dict.get("evidence_type"),
            }
            tags = tags_by_ext.get(eid, {})
            enriched.append({
                "doc_id": row_dict["doc_id"],
                "segment_index": row_dict.get("segment_index", 0),
                "segment_text": row_dict.get("segment_text") or "",
                "extraction": ext_obj,
                "tags": tags,
                "confidence_score": row_dict.get("confidence_score") or 0.7,
            })
        print(f"      → Loaded {len(enriched)} extractions and {len(tag_rows)} tags from database for aggregation", flush=True)

    if not enriched:
        print("\n⚠️ No extractions to process. Exiting.", flush=True)
        sys.exit(0)

    # Step 6: Aggregation
    print(f"\n[6/6] Aggregating patterns across all extractions...", flush=True)
    from analysis.aggregator import Aggregator
    aggregator = Aggregator()
    summary = aggregator.aggregate(enriched)

    # Save aggregated patterns to database
    if summary["purchase_blockers"]:
        db.save_aggregated_patterns(summary["purchase_blockers"])

    # Save full summary to JSON
    summary_path = Path("data/processed/analysis_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    # Print results
    print("\n" + "=" * 60, flush=True)
    print("ANALYSIS COMPLETE", flush=True)
    scores = [e.get("confidence_score", 0.0) for e in enriched]
    avg_conf = sum(scores) / len(scores) if scores else 0.0
    print(f"  Total extractions: {summary['total_extractions']}", flush=True)
    print(f"  Average confidence: {avg_conf:.3f}", flush=True)
    print(f"\n📊 Top Purchase Blockers:", flush=True)
    for i, blocker in enumerate(summary["purchase_blockers"][:5], 1):
        print(f"  {i}. {blocker['blocker_tag']} "
              f"(count={blocker['occurrence_count']}, "
              f"conf={blocker['avg_confidence']:.2f})", flush=True)
    print(f"\n🔍 Uncertainty Distribution:", flush=True)
    for utype, count in summary["uncertainty_distribution"].items():
        print(f"  • {utype}: {count}", flush=True)
    print(f"\n👤 Persona Distribution:", flush=True)
    for persona, count in summary["persona_distribution"].items():
        print(f"  • {persona}: {count}", flush=True)
    print(f"\n📁 Full summary saved to: {summary_path}", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
