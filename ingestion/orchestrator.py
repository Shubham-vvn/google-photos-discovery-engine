"""
Ingestion Orchestrator

Coordinates scraping, cleaning, deduplication, normalization, and persistence in SQLite.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from tqdm import tqdm

from config.settings import RAW_DIR, PROCESSED_DIR
from .cleaners.deduplicator import Deduplicator
from .cleaners.text_cleaner import TextCleaner
from .normalizer import Normalizer
from .scrapers.google_play_scraper import GooglePlayScraper
from .scrapers.app_store_scraper import AppStoreScraper
from .scrapers.apify_app_store_scraper import ApifyAppStoreScraper
from .scrapers.reddit_scraper import RedditScraper
from .scrapers.apify_scraper import ApifyRedditScraper
from storage.database import Database


class IngestionOrchestrator:
    """Orchestrates the full data ingestion pipeline."""

    def __init__(self, db: Optional[Database] = None):
        self.cleaner = TextCleaner()
        self.deduplicator = Deduplicator()
        self.normalizer = Normalizer()
        self.db = db or Database()

    def run(
        self,
        skip_google_play: bool = False,
        skip_app_store: bool = False,
        skip_reddit: bool = True,
        use_apify_reddit: bool = False,
        use_apify_app_store: bool = False,
        gp_count: int = 5000,
        app_store_count: int = 500,
        apify_app_store_count: int = 500,
        reddit_limit: int = 100,
        apify_count: int = 5,
    ) -> List[Dict[str, Any]]:
        """Run the complete ingestion pipeline."""
        print("=" * 60)
        print("MYNTRA DISCOVERY ENGINE — INGESTION PIPELINE")
        print("=" * 60)

        all_raw = []

        # Step 1: Scrape Google Play
        if not skip_google_play:
            print("\n[1/6] Scraping Google Play Store reviews for Myntra...")
            gp = GooglePlayScraper()
            gp_docs = gp.scrape(count=gp_count)
            print(f"      → Fetched {len(gp_docs)} reviews")
            all_raw.extend(gp_docs)
            self._save_raw(gp_docs, "google_play")

        # Step 2: Scrape Apple App Store (RSS)
        if not skip_app_store:
            print("\n[2/6] Scraping Apple App Store reviews for Myntra (RSS)...")
            try:
                app_store = AppStoreScraper()
                as_docs = app_store.scrape(count=app_store_count)
                print(f"      → Fetched {len(as_docs)} reviews")
                all_raw.extend(as_docs)
                self._save_raw(as_docs, "app_store")
            except Exception as e:
                print(f"      ⚠️ Apple App Store scraping failed: {e}")

        # Step 2b: Scrape Apple App Store via Apify Actor (Deep Historical + Wishlist focus)
        if use_apify_app_store:
            print(f"\n[2b/6] Scraping Apple App Store via Apify Actor (target: {apify_app_store_count} reviews)...")
            try:
                apify_as = ApifyAppStoreScraper()
                apify_as_docs = apify_as.scrape(max_items=apify_app_store_count, filter_wishlist=True)
                print(f"      → Fetched {len(apify_as_docs)} Apple App Store wishlisting reviews via Apify")
                all_raw.extend(apify_as_docs)
                self._save_raw(apify_as_docs, "app_store_apify")
            except Exception as e:
                print(f"      ⚠️ Apify App Store scraping failed: {e}")

        # Step 3: Scrape Reddit (via PRAW)
        if not skip_reddit:
            print("\n[3/6] Scraping Reddit discussions & comments (PRAW)...")
            try:
                reddit = RedditScraper()
                reddit_docs = reddit.scrape(limit_per_query=reddit_limit)
                print(f"      → Fetched {len(reddit_docs)} posts/comments")
                all_raw.extend(reddit_docs)
                self._save_raw(reddit_docs, "reddit")
            except Exception as e:
                print(f"      ⚠️ Reddit PRAW scraping skipped: {e}")

        # Step 3b: Scrape Reddit (via Apify)
        if use_apify_reddit:
            print(f"\n[3b/6] Scraping Reddit via Apify Actor (credit-safe cap: {apify_count} items)...")
            try:
                apify_scraper = ApifyRedditScraper()
                apify_docs = apify_scraper.scrape(max_items=apify_count)
                print(f"      → Fetched {len(apify_docs)} Reddit posts via Apify")
                all_raw.extend(apify_docs)
                self._save_raw(apify_docs, "reddit_apify")
            except Exception as e:
                print(f"      ⚠️ Apify scraping failed: {e}")

        if not all_raw:
            print("\n⚠️ No data collected. Please verify scraper settings or internet access.")
            return []

        # Step 4: Clean
        print(f"\n[4/6] Cleaning {len(all_raw)} documents...")
        cleaned = []
        for doc in tqdm(all_raw, desc="Cleaning text"):
            cleaned_text = self.cleaner.clean(doc["text"])
            if self.cleaner.is_usable(cleaned_text):
                doc["text"] = cleaned_text
                cleaned.append(doc)
        print(f"      → {len(cleaned)} usable documents after cleaning")

        # Step 5: Deduplicate
        print(f"\n[5/6] Deduplicating...")
        unique = self.deduplicator.deduplicate(cleaned)
        print(f"      → {len(unique)} unique documents after MinHash deduplication")

        # Step 6: Normalize & store in DB
        print(f"\n[6/6] Normalizing & storing in SQLite database...")
        normalized = self.normalizer.normalize_batch(unique)
        self.db.insert_raw_documents(normalized)
        self._save_processed(normalized)
        print(f"      → {len(normalized)} documents successfully stored in database")

        print("\n" + "=" * 60)
        print(f"INGESTION COMPLETE — {len(normalized)} documents ready for AI analysis")
        print("=" * 60)
        return normalized

    def _save_raw(self, docs: List[Dict[str, Any]], source: str):
        path = RAW_DIR / f"{source}_raw.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(docs, f, indent=2, default=str)

    def _save_processed(self, docs: List[Dict[str, Any]]):
        path = PROCESSED_DIR / "normalized_documents.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(docs, f, indent=2, default=str)
