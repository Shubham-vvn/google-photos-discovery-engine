# ─────────────────────────────────────────────────────
#  Myntra Discovery Engine — Multi-stage Docker Build
#  Optimized for Render.com / Railway free tier
# ─────────────────────────────────────────────────────

FROM python:3.10-slim AS base

# System deps for building native extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install Python dependencies ──────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application code ────────────────────────────
COPY config/ config/
COPY ingestion/ ingestion/
COPY analysis/ analysis/
COPY storage/ storage/
COPY dashboard/ dashboard/
COPY scripts/ scripts/
COPY tests/ tests/

# ── Create data directory ────────────────────────────
RUN mkdir -p data

# ── Expose dashboard port ────────────────────────────
EXPOSE 8000

# ── Health check ─────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/overview')" || exit 1

# ── Default: launch the dashboard ────────────────────
CMD ["python", "scripts/run_dashboard.py", "--host", "0.0.0.0", "--port", "8000"]
