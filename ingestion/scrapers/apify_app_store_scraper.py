"""
Apify Apple App Store Reviews Scraper

Scrapes deep historical iOS customer reviews for Myntra (App ID: 907394059)
using Apify Actor (johnvc~apple-app-store-reviews-api) with credit conservation
and wishlisting keyword filtering.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests

from .base_scraper import BaseScraper


class ApifyAppStoreScraper(BaseScraper):
    """Scrapes historical iOS reviews via Apify Actor."""

    APP_ID = "907394059"
    DEFAULT_COUNTRIES = ["in", "us", "gb", "ae", "ca", "sg", "au", "sa", "kw", "qa", "my", "nz"]

    WISHLIST_KEYWORDS = [
        "wishlist", "wish list", "wish-list", "wishlisted",
        "save for later", "saved for later", "save", "saved",
        "cart", "bag", "buy later", "buying later",
        "price drop", "out of stock", "price increase", "price hike",
        "heart", "bookmark", "collection", "discount", "coupon",
        "platform fee", "expensive", "not buying", "abandoned",
        "size confusion", "outfit", "recommendation"
    ]

    def __init__(self, token: Optional[str] = None, app_id: Optional[str] = None):
        super().__init__(source_name="app_store_apify")
        self.token = token or os.getenv("APIFY_API_TOKEN")
        self.app_id = app_id or self.APP_ID
        if not self.token:
            raise ValueError("APIFY_API_TOKEN not found in environment or .env file.")

    def scrape(
        self,
        max_items: int = 500,
        filter_wishlist: bool = True,
        countries: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Runs Apify Apple App Store reviews actor and returns standardized RawDocument items.
        
        Args:
            max_items: Target number of matching reviews to return.
            filter_wishlist: If True, filters for wishlisting/cart/buying signals.
            countries: Storefront country codes.
        """
        storefronts = countries or self.DEFAULT_COUNTRIES
        print(f"   🔍 Initiating Apify App Store Scraper (target: {max_items} reviews across {len(storefronts)} storefronts)...")

        # Fetch enough raw reviews to guarantee meeting the wishlisting target
        raw_limit = max_items * 4 if filter_wishlist else max_items

        actor_input = {
            "product_ids": [str(self.app_id)],
            "countries": storefronts,
            "sort_orders": ["mostrecent", "mosthelpful"],
            "limit": raw_limit,
        }

        url = f"https://api.apify.com/v2/acts/johnvc~apple-app-store-reviews-api/run-sync-get-dataset-items?token={self.token}&timeout=300"
        headers = {"Content-Type": "application/json"}

        all_documents = []
        seen_ids = set()

        for country in storefronts:
            if len(all_documents) >= max_items:
                break

            print(f"   🔍 Scraping Apify App Store reviews for country '{country}'...")
            actor_input = {
                "product_ids": [str(self.app_id)],
                "countries": [country],
                "sort_orders": ["mostrecent", "mosthelpful"],
                "limit": 300,
            }

            url = f"https://api.apify.com/v2/acts/johnvc~apple-app-store-reviews-api/run-sync-get-dataset-items?token={self.token}&timeout=180"
            headers = {"Content-Type": "application/json"}

            try:
                resp = requests.post(url, json=actor_input, headers=headers, timeout=190)
                if resp.status_code not in [200, 201]:
                    print(f"      ⚠️ Storefront '{country}' failed: HTTP {resp.status_code}")
                    continue

                items = resp.json()
                if not isinstance(items, list):
                    continue

                country_docs = 0
                for item in items:
                    if item.get("error"):
                        continue

                    source_id = self.get_source_id(item)
                    if not source_id or source_id in seen_ids:
                        continue

                    title = item.get("review_title") or item.get("title") or ""
                    body = item.get("review_text") or item.get("body") or item.get("content") or ""
                    full_text = f"{title}\n\n{body}".strip() if body else title.strip()

                    if not full_text:
                        continue

                    if filter_wishlist:
                        text_lower = full_text.lower()
                        if not any(kw in text_lower for kw in self.WISHLIST_KEYWORDS):
                            continue

                    seen_ids.add(source_id)
                    doc = self._to_document(item, full_text=full_text, source_id=source_id)
                    if doc:
                        all_documents.append(doc)
                        country_docs += 1

                    if len(all_documents) >= max_items:
                        break

                print(f"      📥 Got {country_docs} matching reviews from '{country}' (total so far: {len(all_documents)})")

            except Exception as e:
                print(f"      ❌ Country '{country}' error: {e}")
                continue

        print(f"   ✅ Collected {len(all_documents)} wishlisting-focused Apple App Store reviews")
        return all_documents

    def _to_document(
        self, item: Dict[str, Any], full_text: str, source_id: str
    ) -> Optional[Dict[str, Any]]:
        """Convert Apify raw Apple App Store item to standard RawDocument."""
        author = item.get("author_name") or item.get("author") or "Apple User"
        rating = item.get("rating")
        try:
            rating = int(rating) if rating is not None else None
        except (ValueError, TypeError):
            rating = None

        created_at = item.get("review_date_iso") or item.get("fetch_timestamp") or datetime.utcnow().isoformat()
        app_version = item.get("reviewed_version") or item.get("app_version") or ""
        country = item.get("app_country") or item.get("country") or "in"

        return self.create_raw_document(
            raw_item=item,
            text=full_text,
            source_id=str(source_id),
            author=author,
            metadata={
                "rating": rating,
                "app_version": app_version,
                "country": country,
                "source_scraper": "apify_apple_app_store",
                "timestamp": str(created_at),
            },
        )

    def get_source_id(self, raw_item: Dict[str, Any]) -> str:
        return str(raw_item.get("review_id") or raw_item.get("id") or "")
