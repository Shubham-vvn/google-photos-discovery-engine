"""
FastAPI Dashboard & Discovery Engine API
Serves all REST API endpoints and the interactive discovery dashboard.
"""

import json
from pathlib import Path
from typing import Optional
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
    title="Myntra Wishlist-to-Purchase Discovery Engine",
    description="AI-powered customer hesitation discovery engine and dashboard",
    version="1.0.0"
)


class AskRequest(BaseModel):
    question: str

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
    """GET /api/overview — High level stats, top blockers, and distributions."""
    stats = db.get_overview_stats()
    top_blockers = db.get_top_blockers(limit=5)
    confidence_dist = db.get_confidence_distribution()
    uncertainty_dist = db.get_uncertainty_stats()
    persona_stats = db.get_persona_stats()

    return JSONResponse({
        "status": "success",
        "data": {
            "stats": stats,
            "topBlockers": top_blockers,
            "confidenceDistribution": confidence_dist,
            "uncertaintyDistribution": uncertainty_dist,
            "personaStats": persona_stats,
        }
    })


@app.get("/api/blockers")
async def get_blockers(limit: int = Query(20, ge=1, le=100)):
    """GET /api/blockers — Ranked purchase blockers with weights, confidence, and quotes."""
    blockers = db.get_top_blockers(limit=limit)
    for b in blockers:
        if isinstance(b.get("sample_doc_ids"), str):
            try:
                b["sample_texts"] = json.loads(b["sample_doc_ids"])
            except Exception:
                b["sample_texts"] = []
        else:
            b["sample_texts"] = b.get("sample_doc_ids") or []

        if isinstance(b.get("persona_distribution"), str):
            try:
                b["persona_distribution"] = json.loads(b["persona_distribution"])
            except Exception:
                b["persona_distribution"] = {}

    return JSONResponse({
        "status": "success",
        "data": blockers
    })


@app.get("/api/uncertainties")
async def get_uncertainties():
    """GET /api/uncertainties — Uncertainty type distribution and breakdown."""
    dist = db.get_uncertainty_stats()
    conn = db._get_conn()
    rows = conn.execute("""
        SELECT rd.source, e.uncertainty_types, COUNT(*) as count
        FROM extractions e
        JOIN raw_documents rd ON e.doc_id = rd.doc_id
        WHERE e.uncertainty_types IS NOT NULL
        GROUP BY rd.source, e.uncertainty_types
    """).fetchall()
    conn.close()

    source_breakdown = {}
    for r in rows:
        source = r[0]
        if source not in source_breakdown:
            source_breakdown[source] = {}
        try:
            utypes = json.loads(r[1])
            for u in utypes:
                source_breakdown[source][u] = source_breakdown[source].get(u, 0) + r[2]
        except Exception:
            pass

    return JSONResponse({
        "status": "success",
        "data": {
            "distribution": dist,
            "bySource": source_breakdown
        }
    })


@app.get("/api/personas")
async def get_personas():
    """GET /api/personas — Persona breakdown and persona x blocker cross-tabulation."""
    persona_stats = db.get_persona_stats()

    conn = db._get_conn()
    rows = conn.execute("""
        SELECT e.shopper_persona, t.tag_value as blocker, COUNT(*) as count, AVG(e.confidence_score) as avg_conf
        FROM extractions e
        JOIN tags t ON e.extraction_id = t.extraction_id
        WHERE t.tag_category = 'purchase_blocker_tag'
          AND e.shopper_persona IS NOT NULL
          AND e.shopper_persona != 'Unknown'
        GROUP BY e.shopper_persona, t.tag_value
        ORDER BY count DESC
    """).fetchall()
    conn.close()

    crosstab = {}
    for r in rows:
        persona, blocker, count, avg_conf = r[0], r[1], r[2], r[3]
        if persona not in crosstab:
            crosstab[persona] = []
        crosstab[persona].append({
            "blocker": blocker,
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
    blocker: Optional[str] = None,
    persona: Optional[str] = None,
    search: Optional[str] = None
):
    """GET /api/evidence / GET /api/extractions — Detailed evidence cards with filters."""
    items = db.get_all_extractions(
        limit=limit,
        offset=offset,
        blocker=blocker,
        persona=persona,
        search=search
    )
    return JSONResponse({
        "status": "success",
        "count": len(items),
        "data": items
    })


# ──────────────────────────────────────────────
# AI Discovery Engine Q&A
# ──────────────────────────────────────────────
_discovery_engine = None


def _get_discovery_engine():
    """Lazy-initialize the discovery engine (loads Gemini model once)."""
    global _discovery_engine
    if _discovery_engine is None:
        from dashboard.discovery_engine import DiscoveryEngine
        _discovery_engine = DiscoveryEngine()
    return _discovery_engine


@app.post("/api/ask")
async def ask_discovery_engine(req: AskRequest):
    """POST /api/ask — Ask a question to the AI Discovery Engine."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    engine = _get_discovery_engine()
    result = engine.ask(req.question)

    return JSONResponse({
        "status": "success",
        "data": result
    })


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

