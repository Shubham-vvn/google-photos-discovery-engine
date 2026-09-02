"""Configuration package for Myntra Discovery Engine."""

from .settings import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DIR,
    PROCESSED_DIR,
    DB_PATH,
    GEMINI_API_KEY,
    LLM_MODEL,
    LLM_RPM_LIMIT,
    LLM_DAILY_TOKEN_LIMIT,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    TAXONOMY_PATH,
    validate_config,
)
