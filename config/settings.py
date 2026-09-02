"""
Myntra Discovery Engine — Central Configuration

Loads environment variables from .env and provides typed settings
for all modules across the project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_PATH = PROJECT_ROOT / os.getenv("DB_PATH", "data/myntra_discovery.db")

# ──────────────────────────────────────────────
# Google Gemini (Free Tier)
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")
LLM_RPM_LIMIT = int(os.getenv("LLM_RPM_LIMIT", "15"))
LLM_DAILY_TOKEN_LIMIT = int(os.getenv("LLM_DAILY_TOKEN_LIMIT", "1000000"))

# ──────────────────────────────────────────────
# Reddit API (Free Tier)
# ──────────────────────────────────────────────
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "MyntraDiscoveryEngine/1.0")

# ──────────────────────────────────────────────
# Taxonomy
# ──────────────────────────────────────────────
TAXONOMY_PATH = PROJECT_ROOT / "config" / "taxonomy.yaml"

# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────
def validate_config(require_reddit: bool = False):
    """Validate that required configuration is present."""
    errors = []
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
        errors.append("GEMINI_API_KEY is not set in .env")
    if require_reddit:
        if not REDDIT_CLIENT_ID or REDDIT_CLIENT_ID.startswith("your_"):
            errors.append("REDDIT_CLIENT_ID is not set in .env")
        if not REDDIT_CLIENT_SECRET or REDDIT_CLIENT_SECRET.startswith("your_"):
            errors.append("REDDIT_CLIENT_SECRET is not set in .env")
    if not TAXONOMY_PATH.exists():
        errors.append(f"Taxonomy file not found: {TAXONOMY_PATH}")
    return errors
