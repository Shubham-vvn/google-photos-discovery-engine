# Implementation Plan — Myntra Wishlist-to-Purchase AI Discovery Engine

> Based on [problemStatement.md](file:///Users/shubhamthakur/Downloads/nextleap%20antigravity%20projects/Myntra-discovery-engine/problemStatement.md) & [architecture.md](file:///Users/shubhamthakur/Downloads/nextleap%20antigravity%20projects/Myntra-discovery-engine/architecture.md)

---

## Table of Contents

1. [Prerequisites & Environment Setup](#1-prerequisites--environment-setup)
2. [Phase 1 — Project Foundation](#2-phase-1--project-foundation)
3. [Phase 2 — Data Ingestion Layer](#3-phase-2--data-ingestion-layer)
4. [Phase 3 — AI Analysis Engine](#4-phase-3--ai-analysis-engine)
5. [Phase 4 — Storage Layer](#5-phase-4--storage-layer)
6. [Phase 5 — Dashboard](#6-phase-5--dashboard)
7. [Phase 6 — Integration & End-to-End Pipeline](#7-phase-6--integration--end-to-end-pipeline)
8. [Phase 7 — Testing & Validation](#8-phase-7--testing--validation)
9. [Phase 8 — Documentation & Deployment](#9-phase-8--documentation--deployment)
10. [Appendix — Free Tier Limits & Workarounds](#10-appendix--free-tier-limits--workarounds)

---

## 1. Prerequisites & Environment Setup

### 1.1 Required Accounts (All Free, No Credit Card)

| Account | URL | What You Get |
|---|---|---|
| **Google AI Studio** | [aistudio.google.com](https://aistudio.google.com) | Free Gemini API key (15 RPM, 1M tokens/day) |
| **Reddit** | [reddit.com](https://reddit.com) | Account needed for PRAW API access |
| **Reddit Developer App** | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) | Create a "script" type app → get `client_id` & `client_secret` |
| **Vercel** *(optional)* | [vercel.com](https://vercel.com) | Free hobby tier for dashboard hosting |
| **GitHub** *(optional)* | [github.com](https://github.com) | Version control + Vercel integration |

### 1.2 Local Development Requirements

| Tool | Version | Install Command |
|---|---|---|
| **Python** | 3.11+ | `brew install python@3.11` or [python.org](https://python.org) |
| **Node.js** | 18+ | `brew install node` or [nodejs.org](https://nodejs.org) |
| **npm** | 9+ | Comes with Node.js |
| **pip** | Latest | `python -m pip install --upgrade pip` |
| **venv** | Built-in | `python -m venv venv` |
| **Git** | Latest | `brew install git` |

### 1.3 Environment Setup Steps

```bash
# 1. Clone / navigate to project directory
cd Myntra-discovery-engine

# 2. Create Python virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 3. Create .env file from template
cp .env.example .env
# Then edit .env with your keys:
#   GEMINI_API_KEY=your_key_here
#   REDDIT_CLIENT_ID=your_client_id
#   REDDIT_CLIENT_SECRET=your_client_secret
#   REDDIT_USER_AGENT=MyntraDiscoveryEngine/1.0

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Set up the dashboard
cd dashboard
npm install
cd ..
```

---

## 2. Phase 1 — Project Foundation

**Goal:** Create the complete directory structure, configuration files, and shared utilities.

**Duration:** ~1 day

---

### Task 1.1 — Create Directory Structure

Create the full project skeleton as defined in the architecture:

```
Myntra-discovery-engine/
├── ingestion/
│   ├── __init__.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── google_play_scraper.py
│   │   └── reddit_scraper.py
│   ├── cleaners/
│   │   ├── __init__.py
│   │   ├── text_cleaner.py
│   │   └── deduplicator.py
│   ├── normalizer.py
│   └── orchestrator.py
│
├── analysis/
│   ├── __init__.py
│   ├── preprocessor.py
│   ├── llm_extractor.py
│   ├── classifier.py
│   ├── confidence_scorer.py
│   ├── aggregator.py
│   └── prompts/
│       └── extraction_prompt.txt
│
├── storage/
│   ├── __init__.py
│   ├── database.py
│   └── migrations/
│
├── dashboard/
│   └── (Next.js app — created in Phase 5)
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── .gitkeep
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── taxonomy.yaml
│
├── scripts/
│   ├── run_ingestion.py
│   ├── run_analysis.py
│   └── seed_db.py
│
├── tests/
│   ├── __init__.py
│   ├── test_scrapers.py
│   ├── test_cleaner.py
│   ├── test_extractor.py
│   └── test_api.py
│
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── problemStatement.md
├── architecture.md
└── implementationPlan.md
```

---

### Task 1.2 — Create `requirements.txt`

```txt
# Scraping
google-play-scraper==1.2.7
praw==7.7.1

# Text processing
beautifulsoup4==4.12.3
ftfy==6.2.3
emoji==2.12.1
datasketch==1.6.4          # MinHash for deduplication

# AI / LLM
google-generativeai==0.8.3  # Gemini free tier
sentence-transformers==3.0.1  # Local embeddings (all-MiniLM-L6-v2)
chromadb==0.5.5

# Database
# SQLite is built-in — no extra dependency needed

# Utilities
python-dotenv==1.0.1
pyyaml==6.0.2
tqdm==4.66.5
uuid6==2024.7.10

# Testing
pytest==8.3.2
pytest-asyncio==0.23.8
```

---

### Task 1.3 — Create `.env.example`

```env
# Google Gemini (free tier — get key at https://aistudio.google.com)
GEMINI_API_KEY=your_gemini_api_key_here

# Reddit API (free — create app at https://reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=MyntraDiscoveryEngine/1.0 by /u/your_username

# Database
DB_PATH=data/myntra_discovery.db

# LLM Config
LLM_MODEL=gemini-2.0-flash
LLM_RPM_LIMIT=15
LLM_DAILY_TOKEN_LIMIT=1000000
```

---

### Task 1.4 — Create `config/settings.py`

Central configuration loader using `python-dotenv`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_PATH = PROJECT_ROOT / os.getenv("DB_PATH", "data/myntra_discovery.db")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
LLM_RPM_LIMIT = int(os.getenv("LLM_RPM_LIMIT", "15"))

# Reddit
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "MyntraDiscoveryEngine/1.0")

# Taxonomy
TAXONOMY_PATH = PROJECT_ROOT / "config" / "taxonomy.yaml"
```

---

### Task 1.5 — Create `config/taxonomy.yaml`

The starter taxonomy (expected to grow as patterns emerge):

```yaml
purchase_blockers:
  - fit_uncertainty
  - size_uncertainty
  - quality_doubt
  - color_mismatch_fear
  - price_not_justified
  - occasion_mismatch
  - waiting_for_sale
  - need_external_opinion
  - forgotten_wishlist
  - mood_board_usage
  - trust_in_reviews
  - stock_availability
  - delivery_uncertainty
  - return_policy_concern

uncertainty_types:
  - fit
  - quality
  - price
  - occasion
  - trust
  - availability
  - durability
  - styling

shopper_personas:
  - budget_conscious
  - occasion_shopper
  - inspiration_browser
  - brand_loyal
  - trend_follower
  - gifter
  - impulse_saver
```

---

### Task 1.6 — Create `.gitignore`

```gitignore
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# Environment
.env

# Data (large files, not committed)
data/raw/
data/processed/
data/*.db

# Node
dashboard/node_modules/
dashboard/.next/
dashboard/out/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## 3. Phase 2 — Data Ingestion Layer

**Goal:** Build scrapers for Google Play Store and Reddit, plus text cleaning and normalization.

**Duration:** ~3 days

---

### Task 2.1 — `ingestion/scrapers/base_scraper.py`

Abstract base class that all scrapers inherit from:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class BaseScraper(ABC):
    """Base class for all data source scrapers."""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.scraped_at = None

    @abstractmethod
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape data from the source.
        Returns a list of raw documents (dicts).
        """
        pass

    @abstractmethod
    def get_source_id(self, raw_item: Dict) -> str:
        """Extract the platform-specific unique ID."""
        pass

    def create_raw_document(self, raw_item: Dict, text: str,
                            source_id: str, metadata: Dict) -> Dict:
        """Create a standardized raw document dict."""
        return {
            "source": self.source_name,
            "source_id": source_id,
            "text": text,
            "timestamp": metadata.get("timestamp"),
            "metadata": metadata,
            "scraped_at": datetime.utcnow().isoformat()
        }
```

**Key design decisions:**
- Returns plain dicts (not ORM objects) — separation of concerns
- Each scraper only knows how to talk to its platform
- `create_raw_document` enforces the unified schema

---

### Task 2.2 — `ingestion/scrapers/google_play_scraper.py`

Scrapes Myntra app reviews from Google Play Store:

```python
from google_play_scraper import reviews, Sort
from .base_scraper import BaseScraper

class GooglePlayScraper(BaseScraper):
    APP_ID = "com.myntra.android"

    def __init__(self):
        super().__init__(source_name="google_play")

    def scrape(self, count=5000, lang="en", country="in") -> list:
        all_reviews = []
        result, continuation_token = reviews(
            self.APP_ID,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=min(count, 200),  # API returns max 200 per batch
        )
        all_reviews.extend(result)

        while len(all_reviews) < count and continuation_token:
            result, continuation_token = reviews(
                self.APP_ID,
                continuation_token=continuation_token
            )
            all_reviews.extend(result)

        return [self._to_document(r) for r in all_reviews]

    def _to_document(self, review: dict) -> dict:
        return self.create_raw_document(
            raw_item=review,
            text=review.get("content", ""),
            source_id=review.get("reviewId", ""),
            metadata={
                "rating": review.get("score"),
                "thumbs_up": review.get("thumbsUpCount", 0),
                "timestamp": review.get("at", "").isoformat()
                             if review.get("at") else None,
                "app_version": review.get("reviewCreatedVersion"),
            }
        )

    def get_source_id(self, raw_item: dict) -> str:
        return raw_item.get("reviewId", "")
```

**Implementation notes:**
- `google-play-scraper` is fully free, no API key needed
- Pagination via `continuation_token` — can fetch thousands of reviews
- Rate-limit friendly: the library handles pacing internally
- Filter by `lang="en"` and `country="in"` to get Indian English reviews

---

### Task 2.3 — `ingestion/scrapers/reddit_scraper.py`

Scrapes Myntra-related posts and comments from Reddit:

```python
import praw
from config.settings import (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
                              REDDIT_USER_AGENT)
from .base_scraper import BaseScraper

class RedditScraper(BaseScraper):
    SUBREDDITS = ["india", "indianfashionadvice", "IndianFashionAddicts",
                  "fashionadvice", "Myntra"]
    SEARCH_QUERIES = [
        "myntra wishlist", "myntra cart", "myntra buy",
        "myntra quality", "myntra size", "myntra review",
        "online shopping india fashion", "myntra return",
        "myntra worth buying"
    ]

    def __init__(self):
        super().__init__(source_name="reddit")
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

    def scrape(self, limit_per_query=100) -> list:
        documents = []
        seen_ids = set()

        for subreddit_name in self.SUBREDDITS:
            subreddit = self.reddit.subreddit(subreddit_name)
            for query in self.SEARCH_QUERIES:
                try:
                    for post in subreddit.search(query, limit=limit_per_query):
                        if post.id not in seen_ids:
                            seen_ids.add(post.id)
                            documents.append(self._post_to_document(post))
                            # Also get top-level comments
                            post.comments.replace_more(limit=0)
                            for comment in post.comments.list()[:20]:
                                if comment.id not in seen_ids:
                                    seen_ids.add(comment.id)
                                    documents.append(
                                        self._comment_to_document(comment, post.id)
                                    )
                except Exception as e:
                    print(f"Error scraping r/{subreddit_name} "
                          f"for '{query}': {e}")
        return documents

    def _post_to_document(self, post) -> dict:
        text = f"{post.title}\n\n{post.selftext}" if post.selftext else post.title
        return self.create_raw_document(
            raw_item=post,
            text=text,
            source_id=post.id,
            metadata={
                "subreddit": str(post.subreddit),
                "upvotes": post.score,
                "num_comments": post.num_comments,
                "timestamp": datetime.utcfromtimestamp(
                    post.created_utc).isoformat(),
                "post_type": "submission",
            }
        )

    def _comment_to_document(self, comment, parent_post_id: str) -> dict:
        return self.create_raw_document(
            raw_item=comment,
            text=comment.body,
            source_id=comment.id,
            metadata={
                "subreddit": str(comment.subreddit),
                "upvotes": comment.score,
                "timestamp": datetime.utcfromtimestamp(
                    comment.created_utc).isoformat(),
                "post_type": "comment",
                "reply_to": parent_post_id,
            }
        )

    def get_source_id(self, raw_item: dict) -> str:
        return raw_item.id
```

**Implementation notes:**
- PRAW free tier: 100 requests/minute — more than enough
- Search across multiple subreddits and multiple queries
- Collects both posts AND comments (comments often have the real insights)
- Deduplication via `seen_ids` within a single scrape run
- `replace_more(limit=0)` avoids extra API calls for deeply nested comments

---

### Task 2.4 — `ingestion/cleaners/text_cleaner.py`

Cleans raw text for analysis:

```python
import re
import ftfy
import emoji

class TextCleaner:
    """Cleans raw user text for downstream NLP/LLM analysis."""

    def clean(self, text: str) -> str:
        if not text or not text.strip():
            return ""

        text = ftfy.fix_text(text)                    # Fix encoding issues
        text = self._strip_html(text)                  # Remove HTML tags
        text = self._normalize_whitespace(text)        # Collapse whitespace
        text = self._handle_emojis(text)               # Convert emojis to text
        text = self._remove_urls(text)                 # Strip URLs
        text = text.strip()
        return text

    def _strip_html(self, text: str) -> str:
        return re.sub(r"<[^>]+>", " ", text)

    def _normalize_whitespace(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _handle_emojis(self, text: str) -> str:
        return emoji.demojize(text, delimiters=(" [", "] "))

    def _remove_urls(self, text: str) -> str:
        return re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|"
            r"[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "", text
        )

    def is_usable(self, text: str, min_words: int = 5) -> bool:
        """Check if cleaned text is long enough to be useful."""
        return len(text.split()) >= min_words
```

---

### Task 2.5 — `ingestion/cleaners/deduplicator.py`

Near-duplicate detection using MinHash:

```python
from datasketch import MinHash, MinHashLSH

class Deduplicator:
    """Detects near-duplicate texts using MinHash LSH."""

    def __init__(self, threshold: float = 0.7, num_perm: int = 128):
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self.seen = {}

    def _get_minhash(self, text: str) -> MinHash:
        m = MinHash(num_perm=self.num_perm)
        for word in text.lower().split():
            m.update(word.encode("utf8"))
        return m

    def is_duplicate(self, doc_id: str, text: str) -> bool:
        mh = self._get_minhash(text)
        duplicates = self.lsh.query(mh)
        if duplicates:
            return True
        self.lsh.insert(doc_id, mh)
        self.seen[doc_id] = mh
        return False

    def deduplicate(self, documents: list) -> list:
        """Filter out near-duplicate documents."""
        unique = []
        for doc in documents:
            if not self.is_duplicate(doc["source_id"], doc["text"]):
                unique.append(doc)
        return unique
```

---

### Task 2.6 — `ingestion/normalizer.py`

Maps raw documents to the unified schema with UUID generation:

```python
import uuid
import hashlib
from datetime import datetime

class Normalizer:
    """Normalizes raw scraped documents into a unified schema."""

    def normalize(self, document: dict) -> dict:
        return {
            "doc_id": str(uuid.uuid4()),
            "source": document["source"],
            "source_id": document["source_id"],
            "author_hash": self._hash_author(
                document.get("author", document["source_id"])
            ),
            "text": document["text"],
            "timestamp": document.get("metadata", {}).get("timestamp"),
            "metadata": document.get("metadata", {}),
            "ingested_at": datetime.utcnow().isoformat(),
        }

    def normalize_batch(self, documents: list) -> list:
        return [self.normalize(doc) for doc in documents]

    def _hash_author(self, author: str) -> str:
        return hashlib.sha256(author.encode()).hexdigest()[:16]
```

---

### Task 2.7 — `ingestion/orchestrator.py`

Ties the entire ingestion pipeline together:

```python
import json
from pathlib import Path
from tqdm import tqdm

from config.settings import RAW_DIR, PROCESSED_DIR
from .scrapers.google_play_scraper import GooglePlayScraper
from .scrapers.reddit_scraper import RedditScraper
from .cleaners.text_cleaner import TextCleaner
from .cleaners.deduplicator import Deduplicator
from .normalizer import Normalizer
from storage.database import Database

class IngestionOrchestrator:
    """Orchestrates the full ingestion pipeline."""

    def __init__(self):
        self.cleaner = TextCleaner()
        self.deduplicator = Deduplicator()
        self.normalizer = Normalizer()
        self.db = Database()

    def run(self, skip_google_play=False, skip_reddit=False,
            gp_count=5000, reddit_limit=100):
        """Run the complete ingestion pipeline."""
        print("=" * 60)
        print("MYNTRA DISCOVERY ENGINE — INGESTION PIPELINE")
        print("=" * 60)

        all_raw = []

        # Step 1: Scrape
        if not skip_google_play:
            print("\n[1/5] Scraping Google Play Store reviews...")
            gp = GooglePlayScraper()
            gp_docs = gp.scrape(count=gp_count)
            print(f"      → Fetched {len(gp_docs)} reviews")
            all_raw.extend(gp_docs)
            self._save_raw(gp_docs, "google_play")

        if not skip_reddit:
            print("\n[2/5] Scraping Reddit posts & comments...")
            reddit = RedditScraper()
            reddit_docs = reddit.scrape(limit_per_query=reddit_limit)
            print(f"      → Fetched {len(reddit_docs)} posts/comments")
            all_raw.extend(reddit_docs)
            self._save_raw(reddit_docs, "reddit")

        # Step 2: Clean
        print(f"\n[3/5] Cleaning {len(all_raw)} documents...")
        for doc in tqdm(all_raw, desc="Cleaning"):
            doc["text"] = self.cleaner.clean(doc["text"])
        cleaned = [d for d in all_raw if self.cleaner.is_usable(d["text"])]
        print(f"      → {len(cleaned)} usable documents after cleaning")

        # Step 3: Deduplicate
        print(f"\n[4/5] Deduplicating...")
        unique = self.deduplicator.deduplicate(cleaned)
        print(f"      → {len(unique)} unique documents")

        # Step 4: Normalize & store
        print(f"\n[5/5] Normalizing & storing...")
        normalized = self.normalizer.normalize_batch(unique)
        self.db.insert_raw_documents(normalized)
        self._save_processed(normalized)
        print(f"      → {len(normalized)} documents stored in database")

        print("\n" + "=" * 60)
        print(f"INGESTION COMPLETE — {len(normalized)} documents ready")
        print("=" * 60)
        return normalized

    def _save_raw(self, docs: list, source: str):
        path = RAW_DIR / f"{source}_raw.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(docs, f, indent=2, default=str)

    def _save_processed(self, docs: list):
        path = PROCESSED_DIR / "normalized_documents.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(docs, f, indent=2, default=str)
```

---

## 4. Phase 3 — AI Analysis Engine

**Goal:** Build the LLM extraction pipeline, classifier, confidence scorer, and aggregator.

**Duration:** ~5 days

> [!IMPORTANT]
> This is the most critical phase. Every component here directly produces the insights that the dashboard will display.

---

### Task 3.1 — `analysis/prompts/extraction_prompt.txt`

The core prompt for structured extraction:

```text
You are analyzing a real user's public review or comment about Myntra
(one of India's largest online fashion and lifestyle platforms).

Your task: Extract structured insights about WHY users save items to their
wishlist but DON'T complete the purchase. Be precise — only extract what
the text explicitly states or strongly implies. If you cannot determine
a field, set it to null.

Extract the following fields as valid JSON:

1. "wishlist_motivation" (string | null)
   Why did the user save/wishlist this product?
   Example: "liked the design", "planning for wedding", "comparing options"

2. "purchase_blocker" (string | null)
   What is stopping them from buying? Be specific.
   Example: "unsure if size will fit", "quality looks questionable in photos"

3. "uncertainty_type" (array of strings | null)
   What kind of doubt do they express? Pick from:
   [fit, quality, price, occasion, trust, availability, durability, styling]
   Can be multiple. Only include what the text supports.

4. "shopper_persona" (string | null)
   What type of shopper does this person seem to be? Pick from:
   [budget_conscious, occasion_shopper, inspiration_browser, brand_loyal,
    trend_follower, gifter, impulse_saver]

5. "evidence_type" (string)
   How confident is this extraction? Pick one:
   - "direct_statement" → user explicitly says this
   - "inference" → strongly implied but not directly said
   - "weak_signal" → vague or tangential hint

Return ONLY valid JSON. No explanation, no markdown. Example format:
{
  "wishlist_motivation": "liked the ethnic design for festive season",
  "purchase_blocker": "worried the fabric quality won't match the photos",
  "uncertainty_type": ["quality", "trust"],
  "shopper_persona": "occasion_shopper",
  "evidence_type": "direct_statement"
}

User text to analyze:
"""
{user_text}
"""
```

---

### Task 3.2 — `analysis/preprocessor.py`

Filters irrelevant reviews and segments long text:

```python
import re

class Preprocessor:
    """Filters irrelevant content and segments text for analysis."""

    # Keywords indicating shopping/purchase behavior
    RELEVANCE_KEYWORDS = [
        "wishlist", "wish list", "saved", "save for later", "cart",
        "buy", "bought", "purchase", "order", "didn't order",
        "waiting", "confused", "not sure", "thinking about",
        "size", "fit", "quality", "worth", "expensive", "cheap",
        "return", "exchange", "review", "rating", "trust",
        "wedding", "occasion", "festival", "party",
        "compare", "similar", "alternative", "option",
        "like", "love", "want", "need", "browse", "browse",
        "app", "myntra", "fashion", "clothes", "dress", "shoe",
    ]

    # Keywords for clearly irrelevant content
    IRRELEVANT_KEYWORDS = [
        "crash", "bug", "error", "loading", "slow app",
        "update", "install", "uninstall", "permission",
        "notification spam", "ads",
    ]

    def filter_relevant(self, documents: list) -> list:
        """Keep only documents related to shopping behavior."""
        return [
            doc for doc in documents
            if self._is_relevant(doc["text"])
        ]

    def _is_relevant(self, text: str) -> bool:
        text_lower = text.lower()
        # Exclude clearly irrelevant
        irrelevant_count = sum(
            1 for kw in self.IRRELEVANT_KEYWORDS if kw in text_lower
        )
        if irrelevant_count >= 2:
            return False
        # Include if has shopping-related keywords
        relevant_count = sum(
            1 for kw in self.RELEVANCE_KEYWORDS if kw in text_lower
        )
        return relevant_count >= 1

    def segment(self, text: str, max_chars: int = 1000) -> list:
        """Split long text into sentence-level segments."""
        if len(text) <= max_chars:
            return [text]

        sentences = re.split(r'(?<=[.!?])\s+', text)
        segments = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) < max_chars:
                current += (" " if current else "") + sentence
            else:
                if current:
                    segments.append(current)
                current = sentence

        if current:
            segments.append(current)

        return segments if segments else [text[:max_chars]]
```

---

### Task 3.3 — `analysis/llm_extractor.py`

The core LLM extraction logic using Gemini free tier:

```python
import json
import time
import google.generativeai as genai
from pathlib import Path

from config.settings import GEMINI_API_KEY, LLM_MODEL, LLM_RPM_LIMIT

class LLMExtractor:
    """Extracts structured insights from text using Gemini free tier."""

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)
        self.prompt_template = self._load_prompt()
        self.request_count = 0
        self.last_request_time = 0
        self.rpm_limit = LLM_RPM_LIMIT

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).parent / "prompts" / "extraction_prompt.txt"
        return prompt_path.read_text()

    def _rate_limit(self):
        """Enforce free tier rate limits (15 RPM)."""
        self.request_count += 1
        elapsed = time.time() - self.last_request_time
        if elapsed < 60 / self.rpm_limit:
            sleep_time = (60 / self.rpm_limit) - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def extract(self, text: str) -> dict:
        """Extract structured insights from a single text segment."""
        self._rate_limit()
        prompt = self.prompt_template.replace("{user_text}", text)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,        # Low temp for consistency
                    response_mime_type="application/json",
                )
            )
            result = json.loads(response.text)
            return {
                "extraction": result,
                "llm_model": LLM_MODEL,
                "raw_response": response.text,
                "status": "success",
            }
        except json.JSONDecodeError:
            return {
                "extraction": None,
                "llm_model": LLM_MODEL,
                "raw_response": response.text if response else None,
                "status": "json_parse_error",
            }
        except Exception as e:
            return {
                "extraction": None,
                "llm_model": LLM_MODEL,
                "raw_response": None,
                "status": f"error: {str(e)}",
            }

    def extract_batch(self, texts: list, show_progress: bool = True) -> list:
        """Extract from multiple texts with progress tracking."""
        from tqdm import tqdm
        results = []
        iterator = tqdm(texts, desc="LLM Extraction") if show_progress else texts

        for text in iterator:
            result = self.extract(text)
            results.append(result)

        return results
```

**Critical implementation details:**
- `response_mime_type="application/json"` — forces Gemini to return valid JSON
- `temperature=0.1` — low temperature for consistent, deterministic output
- Built-in rate limiter respects the 15 RPM free tier cap
- Graceful error handling — never crashes on a single failed extraction

---

### Task 3.4 — `analysis/classifier.py`

Maps free-text LLM outputs to canonical taxonomy tags:

```python
import yaml
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from config.settings import TAXONOMY_PATH

class Classifier:
    """Maps LLM extraction outputs to canonical taxonomy tags."""

    def __init__(self):
        # Load local embedding model (free, runs on CPU)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.taxonomy = self._load_taxonomy()
        self.tag_embeddings = self._precompute_embeddings()

    def _load_taxonomy(self) -> dict:
        with open(TAXONOMY_PATH, "r") as f:
            return yaml.safe_load(f)

    def _precompute_embeddings(self) -> dict:
        """Pre-compute embeddings for all taxonomy tags."""
        embeddings = {}
        for category, tags in self.taxonomy.items():
            tag_texts = [tag.replace("_", " ") for tag in tags]
            embs = self.model.encode(tag_texts)
            embeddings[category] = {
                "tags": tags,
                "embeddings": embs,
            }
        return embeddings

    def classify(self, extraction: dict) -> dict:
        """Add canonical tags to an extraction result."""
        tags = {}

        # Map purchase_blocker to canonical tag
        if extraction.get("purchase_blocker"):
            tags["purchase_blocker_tag"] = self._find_closest_tag(
                extraction["purchase_blocker"], "purchase_blockers"
            )

        # Map uncertainty_type (already categorical, just validate)
        if extraction.get("uncertainty_type"):
            valid_types = self.taxonomy.get("uncertainty_types", [])
            tags["uncertainty_tags"] = [
                t for t in extraction["uncertainty_type"]
                if t in valid_types
            ]

        # Map shopper_persona (already categorical, just validate)
        if extraction.get("shopper_persona"):
            valid_personas = self.taxonomy.get("shopper_personas", [])
            if extraction["shopper_persona"] in valid_personas:
                tags["persona_tag"] = extraction["shopper_persona"]
            else:
                tags["persona_tag"] = self._find_closest_tag(
                    extraction["shopper_persona"], "shopper_personas"
                )

        return tags

    def _find_closest_tag(self, text: str, category: str,
                          threshold: float = 0.3) -> str | None:
        """Find the closest canonical tag using embedding similarity."""
        if category not in self.tag_embeddings:
            return None

        text_emb = self.model.encode([text])
        similarities = cosine_similarity(
            text_emb,
            self.tag_embeddings[category]["embeddings"]
        )[0]

        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]

        if best_score >= threshold:
            return self.tag_embeddings[category]["tags"][best_idx]
        return None  # No close match — potential "emerging pattern"
```

**Implementation notes:**
- `all-MiniLM-L6-v2` runs 100% locally — no API calls, no cost
- Pre-computes taxonomy embeddings once at startup (fast)
- Similarity threshold of 0.3 — below this, it's flagged as a potential new pattern
- The model is ~80MB — small enough to run on any machine

---

### Task 3.5 — `analysis/confidence_scorer.py`

Composite confidence scoring (4 weighted factors):

```python
class ConfidenceScorer:
    """Scores the confidence of each extraction on a 0.0–1.0 scale."""

    WEIGHTS = {
        "evidence_type": 0.40,
        "text_specificity": 0.25,
        "extraction_completeness": 0.20,
        "source_reliability": 0.15,
    }

    EVIDENCE_SCORES = {
        "direct_statement": 1.0,
        "inference": 0.6,
        "weak_signal": 0.3,
    }

    def score(self, extraction: dict, document: dict) -> float:
        """Compute composite confidence score."""
        scores = {
            "evidence_type": self._score_evidence_type(extraction),
            "text_specificity": self._score_specificity(
                document.get("text", "")
            ),
            "extraction_completeness": self._score_completeness(extraction),
            "source_reliability": self._score_source(document),
        }

        total = sum(
            scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )
        return round(min(max(total, 0.0), 1.0), 3)

    def _score_evidence_type(self, extraction: dict) -> float:
        evidence = extraction.get("evidence_type", "weak_signal")
        return self.EVIDENCE_SCORES.get(evidence, 0.3)

    def _score_specificity(self, text: str) -> float:
        """Longer, more detailed text = higher specificity."""
        word_count = len(text.split())
        if word_count >= 50:
            return 1.0
        elif word_count >= 20:
            return 0.7
        elif word_count >= 10:
            return 0.4
        return 0.2

    def _score_completeness(self, extraction: dict) -> float:
        """More fields extracted = more confident overall."""
        fields = ["wishlist_motivation", "purchase_blocker",
                  "uncertainty_type", "shopper_persona"]
        filled = sum(1 for f in fields if extraction.get(f))
        return filled / len(fields)

    def _score_source(self, document: dict) -> float:
        """Score based on source type and metadata."""
        source = document.get("source", "")
        metadata = document.get("metadata", {})

        base_score = 0.5
        if source == "google_play":
            base_score = 0.7  # Reviews tend to be more specific
            if metadata.get("rating"):
                base_score += 0.1
        elif source == "reddit":
            base_score = 0.6
            upvotes = metadata.get("upvotes", 0)
            if upvotes > 10:
                base_score += 0.2
            elif upvotes > 3:
                base_score += 0.1

        return min(base_score, 1.0)
```

---

### Task 3.6 — `analysis/aggregator.py`

Rolls up individual extractions into pattern-level summaries:

```python
from collections import defaultdict, Counter
from datetime import datetime

class Aggregator:
    """Aggregates individual extractions into pattern-level summaries."""

    def aggregate(self, extractions: list) -> dict:
        """Produce aggregate statistics from all extractions."""
        return {
            "total_extractions": len(extractions),
            "purchase_blockers": self._aggregate_blockers(extractions),
            "uncertainty_distribution": self._aggregate_uncertainties(
                extractions
            ),
            "persona_distribution": self._aggregate_personas(extractions),
            "persona_blocker_crosstab": self._crosstab(extractions),
            "confidence_distribution": self._confidence_dist(extractions),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _aggregate_blockers(self, extractions: list) -> list:
        """Rank purchase blockers by weighted occurrence."""
        blocker_data = defaultdict(lambda: {
            "count": 0, "weighted_count": 0.0,
            "total_confidence": 0.0, "sample_texts": [],
            "personas": Counter()
        })

        for ext in extractions:
            tag = ext.get("tags", {}).get("purchase_blocker_tag")
            if not tag:
                continue
            data = blocker_data[tag]
            conf = ext.get("confidence_score", 0.5)
            data["count"] += 1
            data["weighted_count"] += conf
            data["total_confidence"] += conf
            if len(data["sample_texts"]) < 5:
                data["sample_texts"].append(ext.get("segment_text", ""))
            persona = ext.get("tags", {}).get("persona_tag")
            if persona:
                data["personas"][persona] += 1

        # Sort by weighted count (descending)
        ranked = []
        for tag, data in sorted(
            blocker_data.items(),
            key=lambda x: x[1]["weighted_count"],
            reverse=True
        ):
            ranked.append({
                "blocker_tag": tag,
                "occurrence_count": data["count"],
                "weighted_count": round(data["weighted_count"], 2),
                "avg_confidence": round(
                    data["total_confidence"] / data["count"], 3
                ),
                "sample_texts": data["sample_texts"],
                "persona_distribution": dict(data["personas"]),
            })
        return ranked

    def _aggregate_uncertainties(self, extractions: list) -> dict:
        counts = Counter()
        for ext in extractions:
            tags = ext.get("tags", {}).get("uncertainty_tags", [])
            for tag in tags:
                counts[tag] += 1
        return dict(counts.most_common())

    def _aggregate_personas(self, extractions: list) -> dict:
        counts = Counter()
        for ext in extractions:
            persona = ext.get("tags", {}).get("persona_tag")
            if persona:
                counts[persona] += 1
        return dict(counts.most_common())

    def _crosstab(self, extractions: list) -> dict:
        """Cross-tabulate persona × blocker."""
        table = defaultdict(Counter)
        for ext in extractions:
            persona = ext.get("tags", {}).get("persona_tag")
            blocker = ext.get("tags", {}).get("purchase_blocker_tag")
            if persona and blocker:
                table[persona][blocker] += 1
        return {k: dict(v) for k, v in table.items()}

    def _confidence_dist(self, extractions: list) -> dict:
        """Distribution of confidence scores in buckets."""
        buckets = {"high (0.7-1.0)": 0, "medium (0.4-0.7)": 0,
                   "low (0.0-0.4)": 0}
        for ext in extractions:
            conf = ext.get("confidence_score", 0)
            if conf >= 0.7:
                buckets["high (0.7-1.0)"] += 1
            elif conf >= 0.4:
                buckets["medium (0.4-0.7)"] += 1
            else:
                buckets["low (0.0-0.4)"] += 1
        return buckets
```

---

## 5. Phase 4 — Storage Layer

**Goal:** Set up SQLite database with schema, ORM models, and CRUD operations.

**Duration:** ~2 days

---

### Task 4.1 — `storage/database.py`

Complete database layer with schema creation and CRUD:

```python
import sqlite3
import json
from pathlib import Path
from config.settings import DB_PATH

class Database:
    """SQLite database interface for the discovery engine."""

    def __init__(self, db_path: str = None):
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
                ingested_at TEXT NOT NULL
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
        conn.close()

    # --- Raw Documents ---
    def insert_raw_documents(self, documents: list):
        conn = self._get_conn()
        for doc in documents:
            conn.execute("""
                INSERT OR IGNORE INTO raw_documents
                (doc_id, source, source_id, author_hash,
                 text_content, timestamp, metadata, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["doc_id"], doc["source"], doc["source_id"],
                doc.get("author_hash"), doc["text"],
                doc.get("timestamp"),
                json.dumps(doc.get("metadata", {})),
                doc["ingested_at"],
            ))
        conn.commit()
        conn.close()

    def get_raw_documents(self, limit=100, offset=0) -> list:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM raw_documents LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_unanalyzed_documents(self, limit=100) -> list:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT rd.* FROM raw_documents rd
            LEFT JOIN extractions e ON rd.doc_id = e.doc_id
            WHERE e.extraction_id IS NULL
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Extractions ---
    def insert_extraction(self, extraction: dict):
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO extractions
            (extraction_id, doc_id, segment_index, segment_text,
             wishlist_motivation, purchase_blocker, uncertainty_types,
             shopper_persona, evidence_type, confidence_score,
             llm_model, raw_response, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ))
        conn.commit()
        conn.close()

    # --- Tags ---
    def insert_tags(self, extraction_id: str, tags: dict):
        conn = self._get_conn()
        import uuid
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

    # --- Aggregated Patterns ---
    def save_aggregated_patterns(self, patterns: list):
        conn = self._get_conn()
        conn.execute("DELETE FROM aggregated_patterns")  # Replace all
        for p in patterns:
            import uuid
            conn.execute("""
                INSERT INTO aggregated_patterns
                (pattern_id, blocker_tag, occurrence_count, weighted_count,
                 avg_confidence, persona_distribution, sample_doc_ids,
                 last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), p["blocker_tag"],
                p["occurrence_count"], p["weighted_count"],
                p["avg_confidence"],
                json.dumps(p.get("persona_distribution", {})),
                json.dumps(p.get("sample_texts", [])),
                p.get("last_updated", ""),
            ))
        conn.commit()
        conn.close()

    # --- Query Helpers (for Dashboard API) ---
    def get_overview_stats(self) -> dict:
        conn = self._get_conn()
        stats = {
            "total_documents": conn.execute(
                "SELECT COUNT(*) FROM raw_documents"
            ).fetchone()[0],
            "total_extractions": conn.execute(
                "SELECT COUNT(*) FROM extractions"
            ).fetchone()[0],
            "avg_confidence": conn.execute(
                "SELECT AVG(confidence_score) FROM extractions"
            ).fetchone()[0] or 0,
            "sources": dict(conn.execute(
                "SELECT source, COUNT(*) FROM raw_documents GROUP BY source"
            ).fetchall()),
        }
        conn.close()
        return stats

    def get_top_blockers(self, limit=10) -> list:
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

    def get_extractions_by_blocker(self, blocker_tag: str) -> list:
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

    def get_persona_stats(self) -> list:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT shopper_persona, COUNT(*) as count,
                   AVG(confidence_score) as avg_conf
            FROM extractions
            WHERE shopper_persona IS NOT NULL
            GROUP BY shopper_persona
            ORDER BY count DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
```

---

## 6. Phase 5 — Dashboard

**Goal:** Build a Next.js web dashboard with API routes reading from SQLite.

**Duration:** ~5 days

---

### Task 5.1 — Initialize Next.js Project

```bash
cd Myntra-discovery-engine
npx -y create-next-app@latest dashboard --js --no-tailwind --no-eslint \
    --no-turbopack --app --src-dir --no-import-alias
cd dashboard
npm install recharts better-sqlite3
```

---

### Task 5.2 — Dashboard File Structure

```
dashboard/
├── src/
│   ├── app/
│   │   ├── layout.js                 # Root layout with nav
│   │   ├── page.js                   # Overview page
│   │   ├── globals.css               # Design system
│   │   ├── blockers/
│   │   │   └── page.js               # Purchase blockers page
│   │   ├── uncertainties/
│   │   │   └── page.js               # Uncertainty explorer
│   │   ├── personas/
│   │   │   └── page.js               # Persona view
│   │   ├── evidence/
│   │   │   └── page.js               # Evidence drilldown
│   │   └── api/
│   │       ├── overview/route.js      # GET /api/overview
│   │       ├── blockers/route.js      # GET /api/blockers
│   │       ├── uncertainties/route.js # GET /api/uncertainties
│   │       ├── personas/route.js      # GET /api/personas
│   │       └── extractions/route.js   # GET /api/extractions
│   ├── components/
│   │   ├── Navbar.jsx
│   │   ├── StatCard.jsx
│   │   ├── BlockerChart.jsx
│   │   ├── ConfidenceBadge.jsx
│   │   ├── PersonaRadar.jsx
│   │   ├── EvidenceCard.jsx
│   │   └── UncertaintyHeatmap.jsx
│   └── lib/
│       └── db.js                      # SQLite connection for API routes
├── package.json
└── next.config.js
```

---

### Task 5.3 — Dashboard Pages (Detailed)

#### Overview Page (`/`)
- **Hero stats row:** Total documents, total extractions, avg confidence, sources breakdown
- **Top 5 purchase blockers:** Horizontal bar chart (Recharts)
- **Confidence distribution:** Donut chart showing high/medium/low
- **Uncertainty type distribution:** Radar chart
- **Recent extractions feed:** Last 10 extractions with confidence badges

#### Purchase Blockers Page (`/blockers`)
- **Ranked blocker list:** Cards showing each blocker with:
  - Occurrence count + weighted count
  - Avg confidence score with color-coded badge
  - Top 3 sample quotes from real users
  - Persona breakdown (mini horizontal bar)
- **Click any blocker** → expands to show all evidence

#### Uncertainty Explorer (`/uncertainties`)
- **Heatmap:** Uncertainty type × source type matrix
- **Filter panel:** Filter by uncertainty type, confidence level, source
- **Evidence list:** Actual user text behind each uncertainty tag

#### Persona View (`/personas`)
- **Persona cards:** One per persona type showing:
  - Total users matched to this persona
  - Top blockers for this persona specifically
  - Avg confidence
- **Cross-tabulation table:** Persona × Blocker pivot table

#### Evidence Drilldown (`/evidence`)
- **Search & filter:** By blocker, persona, confidence, source
- **Full evidence cards:** Each showing:
  - Original user text (highlighted relevant parts)
  - Extraction JSON
  - Confidence score breakdown (4 factors)
  - Source info and timestamp

---

### Task 5.4 — API Routes Implementation

Each API route reads from the SQLite database using `better-sqlite3`:

```javascript
// dashboard/src/lib/db.js
import Database from "better-sqlite3";
import path from "path";

let db = null;

export function getDb() {
  if (!db) {
    const dbPath = path.join(
      process.cwd(), "..", "data", "myntra_discovery.db"
    );
    db = new Database(dbPath, { readonly: true });
    db.pragma("journal_mode = WAL");
  }
  return db;
}
```

```javascript
// dashboard/src/app/api/overview/route.js
import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";

export async function GET() {
  const db = getDb();

  const totalDocs = db.prepare(
    "SELECT COUNT(*) as count FROM raw_documents"
  ).get().count;

  const totalExtractions = db.prepare(
    "SELECT COUNT(*) as count FROM extractions"
  ).get().count;

  const avgConfidence = db.prepare(
    "SELECT AVG(confidence_score) as avg FROM extractions"
  ).get().avg || 0;

  const topBlockers = db.prepare(`
    SELECT blocker_tag, occurrence_count, weighted_count, avg_confidence
    FROM aggregated_patterns
    ORDER BY weighted_count DESC
    LIMIT 5
  `).all();

  const sources = db.prepare(
    "SELECT source, COUNT(*) as count FROM raw_documents GROUP BY source"
  ).all();

  return NextResponse.json({
    totalDocuments: totalDocs,
    totalExtractions,
    avgConfidence: Math.round(avgConfidence * 1000) / 1000,
    topBlockers,
    sources,
  });
}
```

---

### Task 5.5 — Design System (`globals.css`)

Premium dark theme with glassmorphism, gradients, and micro-animations:

```css
/* Key design tokens */
:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #12121a;
  --bg-card: rgba(255, 255, 255, 0.04);
  --bg-card-hover: rgba(255, 255, 255, 0.08);
  --border: rgba(255, 255, 255, 0.08);
  --text-primary: #e8e8ed;
  --text-secondary: #8b8b9e;
  --accent-blue: #6366f1;
  --accent-purple: #a78bfa;
  --accent-pink: #f472b6;
  --accent-green: #34d399;
  --accent-amber: #fbbf24;
  --confidence-high: #34d399;
  --confidence-medium: #fbbf24;
  --confidence-low: #f87171;
  --font-sans: 'Inter', -apple-system, sans-serif;
  --radius: 12px;
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}
```

---

## 7. Phase 6 — Integration & End-to-End Pipeline

**Goal:** Wire all layers together into runnable CLI scripts.

**Duration:** ~2 days

---

### Task 6.1 — `scripts/run_ingestion.py`

```python
#!/usr/bin/env python3
"""CLI script to run the full ingestion pipeline."""

import argparse
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.orchestrator import IngestionOrchestrator

def main():
    parser = argparse.ArgumentParser(
        description="Myntra Discovery Engine — Data Ingestion"
    )
    parser.add_argument("--gp-count", type=int, default=5000,
                        help="Number of Google Play reviews to fetch")
    parser.add_argument("--reddit-limit", type=int, default=100,
                        help="Posts per query from Reddit")
    parser.add_argument("--skip-gp", action="store_true",
                        help="Skip Google Play scraping")
    parser.add_argument("--skip-reddit", action="store_true",
                        help="Skip Reddit scraping")
    args = parser.parse_args()

    orchestrator = IngestionOrchestrator()
    orchestrator.run(
        skip_google_play=args.skip_gp,
        skip_reddit=args.skip_reddit,
        gp_count=args.gp_count,
        reddit_limit=args.reddit_limit,
    )

if __name__ == "__main__":
    main()
```

---

### Task 6.2 — `scripts/run_analysis.py`

```python
#!/usr/bin/env python3
"""CLI script to run the full analysis pipeline."""

import uuid
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import Database
from analysis.preprocessor import Preprocessor
from analysis.llm_extractor import LLMExtractor
from analysis.classifier import Classifier
from analysis.confidence_scorer import ConfidenceScorer
from analysis.aggregator import Aggregator

def main():
    db = Database()
    preprocessor = Preprocessor()
    extractor = LLMExtractor()
    classifier = Classifier()
    scorer = ConfidenceScorer()
    aggregator = Aggregator()

    # Step 1: Get unanalyzed documents
    print("[1/6] Fetching unanalyzed documents...")
    documents = db.get_unanalyzed_documents(limit=500)
    print(f"      → {len(documents)} documents to analyze")

    if not documents:
        print("No new documents to analyze. Run ingestion first.")
        return

    # Step 2: Filter for relevance
    print("[2/6] Filtering for relevance...")
    relevant = preprocessor.filter_relevant(documents)
    print(f"      → {len(relevant)} relevant documents")

    # Step 3: Extract with LLM
    print("[3/6] Running LLM extraction (this will take a while)...")
    print(f"      Rate limit: {extractor.rpm_limit} RPM")
    estimated_time = len(relevant) * (60 / extractor.rpm_limit)
    print(f"      Estimated time: {estimated_time / 60:.1f} minutes")

    all_extractions = []
    for doc in tqdm(relevant, desc="Extracting"):
        segments = preprocessor.segment(doc["text_content"])
        for idx, segment in enumerate(segments):
            result = extractor.extract(segment)
            if result["status"] == "success" and result["extraction"]:
                extraction = result["extraction"]

                # Step 4: Classify & tag
                tags = classifier.classify(extraction)

                # Step 5: Score confidence
                confidence = scorer.score(extraction, doc)

                # Assemble full extraction record
                record = {
                    "extraction_id": str(uuid.uuid4()),
                    "doc_id": doc["doc_id"],
                    "segment_index": idx,
                    "segment_text": segment,
                    "wishlist_motivation": extraction.get(
                        "wishlist_motivation"),
                    "purchase_blocker": extraction.get("purchase_blocker"),
                    "uncertainty_types": extraction.get(
                        "uncertainty_type", []),
                    "shopper_persona": extraction.get("shopper_persona"),
                    "evidence_type": extraction.get("evidence_type"),
                    "confidence_score": confidence,
                    "llm_model": result["llm_model"],
                    "raw_response": result["raw_response"],
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "tags": tags,
                }
                all_extractions.append(record)
                db.insert_extraction(record)
                db.insert_tags(record["extraction_id"], tags)

    print(f"\n[4/6] Stored {len(all_extractions)} extractions")

    # Step 6: Aggregate
    print("[5/6] Aggregating patterns...")
    aggregated = aggregator.aggregate(all_extractions)
    db.save_aggregated_patterns(aggregated["purchase_blockers"])
    print(f"      → {len(aggregated['purchase_blockers'])} "
          f"unique blocker patterns found")

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nTop Purchase Blockers:")
    for i, b in enumerate(aggregated["purchase_blockers"][:5], 1):
        print(f"  {i}. {b['blocker_tag']} "
              f"(count: {b['occurrence_count']}, "
              f"confidence: {b['avg_confidence']:.2f})")
    print(f"\nConfidence Distribution:")
    for bucket, count in aggregated["confidence_distribution"].items():
        print(f"  {bucket}: {count}")

if __name__ == "__main__":
    main()
```

---

### Task 6.3 — `scripts/seed_db.py`

Seeds the database with sample data for dashboard development:

```python
#!/usr/bin/env python3
"""Seeds the database with sample data for testing."""

# Creates ~50 sample documents and extractions
# so the dashboard can be developed without waiting
# for real scraping + analysis to complete.
# See implementation for sample review texts.
```

---

## 8. Phase 7 — Testing & Validation

**Goal:** Verify each component works correctly, end-to-end.

**Duration:** ~3 days

---

### Task 7.1 — Unit Tests

| Test File | What It Tests |
|---|---|
| `tests/test_scrapers.py` | Google Play and Reddit scrapers return valid documents |
| `tests/test_cleaner.py` | Text cleaner handles HTML, emojis, encoding, URLs |
| `tests/test_extractor.py` | LLM extractor returns valid JSON (mock + live test) |
| `tests/test_classifier.py` | Taxonomy mapping returns valid tags |
| `tests/test_confidence.py` | Confidence scorer returns scores in [0, 1] |
| `tests/test_database.py` | CRUD operations work on SQLite |
| `tests/test_api.py` | Dashboard API routes return correct JSON |

### Task 7.2 — Integration Tests

```bash
# Run full pipeline on a small sample
python scripts/run_ingestion.py --gp-count 50 --reddit-limit 10
python scripts/run_analysis.py

# Verify database has data
python -c "
from storage.database import Database
db = Database()
stats = db.get_overview_stats()
print(f'Documents: {stats[\"total_documents\"]}')
print(f'Extractions: {stats[\"total_extractions\"]}')
print(f'Avg confidence: {stats[\"avg_confidence\"]:.3f}')
"
```

### Task 7.3 — Dashboard Smoke Test

```bash
cd dashboard
npm run dev
# Open http://localhost:3000
# Verify:
#   ✓ Overview page loads with charts
#   ✓ Blockers page shows ranked list
#   ✓ Evidence cards display actual user text
#   ✓ Confidence badges show correct colors
#   ✓ All pages are responsive
```

---

## 9. Phase 8 — Documentation & Deployment

**Goal:** Write README, deploy dashboard, and document findings.

**Duration:** ~2 days

---

### Task 8.1 — `README.md`

```markdown
# Myntra Wishlist-to-Purchase AI Discovery Engine

An AI-powered tool that discovers why Myntra users wishlist items
but don't complete the purchase — using real public user reviews
and comments, not assumptions.

## Quick Start
1. Clone the repo
2. `cp .env.example .env` and add your (free) API keys
3. `pip install -r requirements.txt`
4. `python scripts/run_ingestion.py`
5. `python scripts/run_analysis.py`
6. `cd dashboard && npm install && npm run dev`
7. Open http://localhost:3000

## Cost: ₹0
Every tool in this stack is free. See architecture.md for details.
```

### Task 8.2 — Deploy Dashboard to Vercel (Free)

```bash
cd dashboard
npx -y vercel --prod
# Follow prompts — free hobby tier, no credit card needed
```

---

## 10. Appendix — Free Tier Limits & Workarounds

| Service | Free Tier Limit | Our Usage | Headroom |
|---|---|---|---|
| **Gemini 2.0 Flash** | 15 RPM, 1M tokens/day | ~5,000 reviews/day at ~200 tokens each | Plenty for MVP |
| **Reddit API (PRAW)** | 100 requests/min | ~10-20 requests per scrape session | Massive headroom |
| **Google Play Scraper** | No official limit (scraping) | ~5,000 reviews per run | No issue |
| **Vercel Hobby** | 100GB bandwidth/month | Dashboard with ~10 users | Way under limit |
| **SQLite** | No limits (local file) | ~50K documents | No issue up to millions |
| **Hugging Face models** | No limits (local download) | One-time 80MB download | N/A |

### Workarounds for Rate Limits

| Scenario | Solution |
|---|---|
| **Hit 15 RPM on Gemini** | Built-in rate limiter adds `time.sleep()` between calls |
| **Need to process >5K reviews/day** | Run overnight; cache LLM responses to avoid re-processing |
| **Reddit API slowdown** | Reduce `limit_per_query`; increase delay between requests |
| **Gemini free tier discontinued** | Fall back to Ollama + Llama 3 (free, local, 8GB RAM) |

---

## Summary: Full Implementation Checklist

| # | Phase | Tasks | Duration | Status |
|---|---|---|---|---|
| 1 | **Foundation** | Dir structure, config, deps, .env | 1 day | ✅ **Completed** |
| 2 | **Ingestion** | Scrapers, cleaner, dedup, normalizer, orchestrator | 3 days | ✅ **Completed** |
| 3 | **AI Analysis** | Preprocessor, LLM extractor, classifier, scorer, aggregator | 5 days | ✅ **Completed** |
| 4 | **Storage** | SQLite schema, database.py, CRUD | 2 days | ✅ **Completed** |
| 5 | **Dashboard** | FastAPI + Glassmorphic UI, API routes, Chart.js | 5 days | ✅ **Completed** |
| 6 | **Integration** | CLI scripts, end-to-end wiring, Apify Reddit | 2 days | ✅ **Completed** |
| 7 | **Testing** | 59 unit tests, integration tests, smoke tests | 3 days | ✅ **Completed** |
| 8 | **Deployment** | README, Dockerfile, Render config, documentation | 2 days | ✅ **Completed** |
| | **Total** | | **~23 days** | ✅ **ALL DONE** |

> [!IMPORTANT]
> **Total cost of this entire project: ₹0** — Every tool, API, hosting service, and library is completely free.
