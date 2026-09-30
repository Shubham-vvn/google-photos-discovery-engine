"""
FastAPI Dashboard & Google Photos AI Discovery Engine API

Serves all REST API endpoints, the interactive cognitive discovery dashboard,
and the AI-Native Retrieval MVP prototype (Part 5).
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import Database
from config.settings import DB_PATH

app = FastAPI(
    title="Google Photos AI Discovery Engine & Retrieval MVP",
    description="AI-powered discovery engine uncovering why users struggle to retrieve vaguely remembered photos, plus an AI-native associative retrieval prototype.",
    version="2.0.0"
)


class AskRequest(BaseModel):
    question: str


class RetrievalSearchRequest(BaseModel):
    query: str
    companion_filter: Optional[str] = None
    category_filter: Optional[str] = None


# Static and template directories
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

db = Database()


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Serve the interactive discovery engine dashboard."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/overview")
async def get_overview():
    """GET /api/overview — High level stats, top failure points, and cognitive distributions."""
    stats = db.get_overview_stats()
    top_failures = db.get_top_failure_points(limit=6)
    confidence_dist = db.get_confidence_distribution()
    clues_dist = db.get_remembered_clues_stats()
    forgotten_dist = db.get_forgotten_elements_stats()
    persona_stats = db.get_persona_stats()
    categories_dist = db.get_photo_categories_stats()

    return JSONResponse({
        "status": "success",
        "data": {
            "stats": stats,
            "topFailures": top_failures,
            "confidenceDistribution": confidence_dist,
            "rememberedClues": clues_dist,
            "forgottenElements": forgotten_dist,
            "personaStats": persona_stats,
            "photoCategories": categories_dist,
            # Backward compatibility aliases
            "topBlockers": top_failures,
            "uncertaintyDistribution": clues_dist,
        }
    })


@app.get("/api/failures")
@app.get("/api/blockers")
async def get_failures(limit: int = Query(20, ge=1, le=100)):
    """GET /api/failures — Ranked retrieval failure modes with weights, confidence, and quotes."""
    failures = db.get_top_failure_points(limit=limit)
    for f in failures:
        if isinstance(f.get("sample_doc_ids"), str):
            try:
                f["sample_texts"] = json.loads(f["sample_doc_ids"])
            except Exception:
                f["sample_texts"] = []
        else:
            f["sample_texts"] = f.get("sample_doc_ids") or []

        if isinstance(f.get("persona_distribution"), str):
            try:
                f["persona_distribution"] = json.loads(f["persona_distribution"])
            except Exception:
                f["persona_distribution"] = {}

    return JSONResponse({
        "status": "success",
        "data": failures
    })


@app.get("/api/clues")
@app.get("/api/uncertainties")
async def get_clues():
    """GET /api/clues — What users remember vs what they forget."""
    remembered = db.get_remembered_clues_stats()
    forgotten = db.get_forgotten_elements_stats()
    categories = db.get_photo_categories_stats()

    return JSONResponse({
        "status": "success",
        "data": {
            "rememberedClues": remembered,
            "forgottenElements": forgotten,
            "photoCategories": categories,
            "distribution": remembered,  # backward compatibility
        }
    })


@app.get("/api/personas")
async def get_personas():
    """GET /api/personas — Persona breakdown and persona x failure cross-tabulation."""
    persona_stats = db.get_persona_stats()

    conn = db._get_conn()
    rows = conn.execute("""
        SELECT e.user_persona, e.retrieval_failure_point as failure, COUNT(*) as count, AVG(e.confidence_score) as avg_conf
        FROM extractions e
        WHERE e.user_persona IS NOT NULL AND e.retrieval_failure_point IS NOT NULL
        GROUP BY e.user_persona, e.retrieval_failure_point
        ORDER BY count DESC
    """).fetchall()
    conn.close()

    crosstab: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        persona, failure, count, avg_conf = r[0], r[1], r[2], r[3]
        if persona not in crosstab:
            crosstab[persona] = []
        crosstab[persona].append({
            "failure": failure,
            "count": count,
            "avg_confidence": round(avg_conf, 3)
        })

    return JSONResponse({
        "status": "success",
        "data": {
            "personas": persona_stats,
            "crosstab": crosstab
        }
    })


@app.get("/api/evidence")
@app.get("/api/extractions")
async def get_extractions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    failure_point: Optional[str] = None,
    persona: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    blocker: Optional[str] = None,
):
    """GET /api/evidence — Detailed customer evidence cards with filters."""
    items = db.get_all_extractions(
        limit=limit,
        offset=offset,
        failure_point=failure_point or blocker,
        persona=persona,
        category=category,
        search=search
    )
    return JSONResponse({
        "status": "success",
        "count": len(items),
        "data": items
    })


# ──────────────────────────────────────────────
# AI Discovery Engine Q&A Copilot
# ──────────────────────────────────────────────
_discovery_engine = None


def _get_discovery_engine():
    """Lazy-initialize the discovery engine."""
    global _discovery_engine
    if _discovery_engine is None:
        from dashboard.discovery_engine import DiscoveryEngine
        _discovery_engine = DiscoveryEngine()
    return _discovery_engine


@app.post("/api/ask")
async def ask_discovery_engine(req: AskRequest):
    """POST /api/ask — Ask a qualitative PM question to the AI Discovery Engine."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    engine = _get_discovery_engine()
    result = engine.ask(req.question)

    return JSONResponse({
        "status": "success",
        "data": result
    })


# ──────────────────────────────────────────────
# Part 5: AI-Native Retrieval MVP Endpoint
# ──────────────────────────────────────────────
SAMPLE_ALBUM_PHOTOS = [
    {
        "id": "photo_001",
        "title": "Breakfast by the Sea, Cafe Lilliput, Anjuna Beach",
        "tags": ["goa", "cafe", "breakfast", "beach", "sea", "blue chairs", "pancakes", "sunny", "vacation"],
        "companion": "Priya",
        "approx_date": "November 2024 (Morning)",
        "category": "episodic_life_event",
        "visual_anchors": ["blue wooden chairs", "sparkling blue water", "yellow table umbrella", "pancake plate"],
        "color_palette": ["blue", "yellow", "white", "sand"],
        "image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&auto=format&fit=crop&q=80",
        "ocr_text": "Cafe Lilliput Beachside Breakfast Menu"
    },
    {
        "id": "photo_002",
        "title": "Prescription Slip & Cifran Medicine Foil Strip",
        "tags": ["medicine", "pills", "prescription", "pharmacy", "sick", "white", "blister pack", "food poisoning"],
        "companion": "None",
        "approx_date": "July 2025 (Monsoon)",
        "category": "visual_utility_document",
        "visual_anchors": ["white tablet blister pack", "doctor clinic slip", "silver foil strip"],
        "color_palette": ["white", "silver", "blue ink"],
        "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&auto=format&fit=crop&q=80",
        "ocr_text": "Cifran 500mg - Take twice daily after meals"
    },
    {
        "id": "photo_003",
        "title": "Book Recommendation Screenshot: Thinking in Bets",
        "tags": ["screenshot", "book", "twitter", "reading", "orange", "recommendation", "article"],
        "companion": "None",
        "approx_date": "March 2026",
        "category": "screenshot_saved_media",
        "visual_anchors": ["bright orange book cover", "Twitter dark mode interface", "bold typography"],
        "color_palette": ["orange", "black", "white"],
        "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80",
        "ocr_text": "Must read for product strategists: Thinking in Bets by Annie Duke"
    },
    {
        "id": "photo_004",
        "title": "Yellow Mountain Tent during Sunset Trek in Manali",
        "tags": ["manali", "trek", "camping", "tent", "yellow", "sunset", "mountains", "snow peaks"],
        "companion": "Rohan, Sneha",
        "approx_date": "October 2024 (Evening)",
        "category": "episodic_life_event",
        "visual_anchors": ["bright yellow tent", "orange pink sunset sky", "snow clad mountain ridge"],
        "color_palette": ["yellow", "orange", "purple", "white"],
        "image_url": "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=600&auto=format&fit=crop&q=80",
        "ocr_text": ""
    },
    {
        "id": "photo_005",
        "title": "Toddler's First Spaghetti Dinner (Messy Face)",
        "tags": ["daughter", "baby", "spaghetti", "messy", "dinner", "funny", "red sauce", "high chair"],
        "companion": "Ananya (Daughter)",
        "approx_date": "May 2023",
        "category": "people_and_portraits",
        "visual_anchors": ["red tomato sauce on cheeks", "white baby bib", "wooden high chair"],
        "color_palette": ["red", "white", "brown"],
        "image_url": "https://images.unsplash.com/photo-1543332164-6e82f355badc?w=600&auto=format&fit=crop&q=80",
        "ocr_text": ""
    },
    {
        "id": "photo_006",
        "title": "Sister in Bottle Green Lehenga at Sangeet, Jaipur",
        "tags": ["jaipur", "wedding", "sangeet", "sister", "green", "lehenga", "traditional", "lights"],
        "companion": "Meera (Sister)",
        "approx_date": "December 2023 (Night)",
        "category": "episodic_life_event",
        "visual_anchors": ["emerald bottle green embroidered dress", "golden fairy lights", "palace courtyard"],
        "color_palette": ["emerald green", "gold", "navy"],
        "image_url": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&auto=format&fit=crop&q=80",
        "ocr_text": ""
    }
]


@app.post("/api/retrieval-mvp/search")
async def associative_retrieval_mvp(req: RetrievalSearchRequest):
    """
    POST /api/retrieval-mvp/search — Part 5 AI-Native Retrieval MVP prototype.
    Decomposes vague user memory queries into associative clues (visual anchors,
    companions, approximate seasons, emotions) and scores candidate visual assets.
    """
    query_lower = req.query.lower().strip()
    if not query_lower:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    query_tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', query_lower))

    # Match each candidate photo using multi-modal associative clue scoring
    scored_results = []
    for photo in SAMPLE_ALBUM_PHOTOS:
        score = 0.0
        matched_clues = []

        # Tag matches
        for tag in photo["tags"]:
            if tag in query_lower or any(token in tag for token in query_tokens):
                score += 0.35
                matched_clues.append(f"Tag: '{tag}'")

        # Visual anchors
        for anchor in photo["visual_anchors"]:
            if any(w in query_lower for w in anchor.lower().split()):
                score += 0.4
                matched_clues.append(f"Visual Anchor: '{anchor}'")

        # Color match
        for color in photo["color_palette"]:
            if color in query_lower:
                score += 0.35
                matched_clues.append(f"Color: '{color}'")

        # Companion match
        if photo["companion"].lower() in query_lower or (req.companion_filter and req.companion_filter.lower() in photo["companion"].lower()):
            score += 0.5
            matched_clues.append(f"Companion: '{photo['companion']}'")

        # OCR match
        if photo["ocr_text"]:
            for token in query_tokens:
                if token in photo["ocr_text"].lower():
                    score += 0.45
                    matched_clues.append(f"Indexed Text: '{token}'")

        # Filter by category if requested
        if req.category_filter and req.category_filter != "all":
            if photo["category"] != req.category_filter:
                score *= 0.2

        if score > 0.2:
            conf = min(round(0.45 + (score * 0.2), 2), 0.98)
            scored_results.append({
                "photo": photo,
                "confidence_score": conf,
                "matched_clues": list(set(matched_clues))[:4],
                "retrieval_reasoning": f"Matched via associative memory: {', '.join(list(set(matched_clues))[:3])}."
            })

    scored_results.sort(key=lambda x: x["confidence_score"], reverse=True)

    return JSONResponse({
        "status": "success",
        "query": req.query,
        "total_candidates_scanned": len(SAMPLE_ALBUM_PHOTOS),
        "matches_found": len(scored_results),
        "results": scored_results
    })


# ──────────────────────────────────────────────
# Health & LLM Diagnostics
# ──────────────────────────────────────────────
@app.get("/api/llm-status")
async def check_llm_status():
    """GET /api/llm-status — Live diagnostic to verify Gemini LLM connection on Render/local."""
    import google.generativeai as genai
    from config.settings import GEMINI_API_KEY, LLM_MODEL

    key_configured = bool(GEMINI_API_KEY and not GEMINI_API_KEY.startswith("your_"))
    masked_key = f"{GEMINI_API_KEY[:6]}...{GEMINI_API_KEY[-4:]}" if (GEMINI_API_KEY and len(GEMINI_API_KEY) > 10) else None

    if not key_configured:
        return JSONResponse({
            "status": "error",
            "connected": False,
            "message": "GEMINI_API_KEY is missing or unconfigured in environment variables.",
            "api_key_configured": False
        }, status_code=500)

    genai.configure(api_key=GEMINI_API_KEY)
    models_to_test = [LLM_MODEL, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]

    working_model = None
    test_error = None
    for model_name in models_to_test:
        if not model_name:
            continue
        try:
            m = genai.GenerativeModel(model_name)
            resp = m.generate_content("Ping")
            if resp and hasattr(resp, "text") and resp.text:
                working_model = model_name
                break
        except Exception as e:
            test_error = str(e)

    if working_model:
        return JSONResponse({
            "status": "success",
            "connected": True,
            "active_model": working_model,
            "configured_model": LLM_MODEL,
            "api_key_configured": True,
            "api_key_preview": masked_key,
            "message": f"Successfully connected to Google Gemini LLM ({working_model})"
        })
    else:
        return JSONResponse({
            "status": "error",
            "connected": False,
            "api_key_configured": True,
            "api_key_preview": masked_key,
            "error_details": test_error,
            "message": "Gemini API key is present but failed to generate test response."
        }, status_code=502)
