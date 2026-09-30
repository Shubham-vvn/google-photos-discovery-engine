"""
Apify Reddit Scraper
Scrapes Myntra fashion discussions from Reddit (r/IndianFashionAddicts, r/indianfashionadvice, r/india)
using Apify Actor API with strict credit-saving item caps.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests

from config.settings import PROJECT_ROOT
from ingestion.scrapers.base_scraper import BaseScraper


class ApifyRedditScraper(BaseScraper):
    """Scrapes Reddit discussions via Apify actor with credit conservation."""

    SUBREDDITS = ["googlephotos", "google", "Android", "techsupport", "GooglePixel"]
    SEARCH_QUERIES = [
        "google photos search photo",
        "google photos can't find picture",
        "google photos search broken",
        "google photos remember photo",
        "google photos find receipt",
        "google photos find screenshot",
        "google photos search not working",
        "google photos scroll through thousands",
        "ask photos google",
    ]

    def __init__(self, token: Optional[str] = None):
        super().__init__(source_name="reddit_apify")
        self.token = token or os.getenv("APIFY_API_TOKEN")
        if not self.token:
            raise ValueError("APIFY_API_TOKEN not found in environment or .env file.")

    def scrape(self, max_items: int = 5, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Runs Apify scrapes one query at a time to avoid actor timeouts.
        Loops through up to 6 queries for broad coverage.
        """
        if query:
            queries = [query]
        else:
            queries = self.SEARCH_QUERIES[:6]

        all_documents = []
        items_per_query = max(max_items // len(queries), 3)

        for q in queries:
            print(f"   🔍 Querying Apify: '{q}' (max {items_per_query} items)...")
            actor_input = {
                "searches": [q],
                "maxItems": items_per_query,
                "maxPostCount": items_per_query,
                "maxComments": 0,
                "proxy": {"useApifyProxy": True}
            }

            url = f"https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items?token={self.token}&timeout=300"
            headers = {"Content-Type": "application/json"}

            try:
                resp = requests.post(url, json=actor_input, headers=headers, timeout=310)
                if resp.status_code not in [200, 201]:
                    print(f"      ⚠️ Query '{q}' failed: HTTP {resp.status_code}")
                    continue

                items = resp.json()
                if not isinstance(items, list):
                    continue

                for item in items:
                    doc = self._to_document(item)
                    if doc:
                        all_documents.append(doc)
                print(f"      ✅ Got {len(items)} results for '{q}'")

            except Exception as e:
                print(f"      ❌ Query '{q}' error: {e}")
                continue

        print(f"   ✅ Total: {len(all_documents)} Reddit posts across {len(queries)} queries.")
        return all_documents

    def _to_document(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert Apify raw Reddit item to standard RawDocument."""
        title = item.get("title", "")
        body = item.get("body", item.get("text", item.get("selftext", "")))
        full_text = f"{title}\n\n{body}".strip() if body else title.strip()

        if not full_text:
            return None

        source_id = item.get("id") or item.get("postId") or item.get("url") or ""
        created_at = item.get("createdAt") or datetime.utcnow().isoformat()

        return self.create_raw_document(
            raw_item=item,
            text=full_text,
            source_id=str(source_id),
            metadata={
                "subreddit": item.get("communityName", item.get("subreddit", "reddit")),
                "upvotes": item.get("upVotes", item.get("score", 0)),
                "num_comments": item.get("numberOfComments", item.get("numComments", 0)),
                "url": item.get("url", ""),
                "timestamp": str(created_at),
                "source_scraper": "apify_reddit_lite"
            }
        )

    def get_source_id(self, raw_item: Dict[str, Any]) -> str:
        return str(raw_item.get("id", raw_item.get("postId", "")))
