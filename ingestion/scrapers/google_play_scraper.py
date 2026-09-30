"""
Google Play Store Scraper

Scrapes public user reviews for the Google Photos Android application.
"""

from typing import Any, Dict, List, Optional
from google_play_scraper import reviews, Sort
from .base_scraper import BaseScraper
from config.settings import GOOGLE_PLAY_PACKAGE


class GooglePlayScraper(BaseScraper):
    APP_ID = GOOGLE_PLAY_PACKAGE

    def __init__(self):
        super().__init__(source_name="google_play")

    def scrape(self, count: int = 5000, lang: str = "en", country: str = "in") -> List[Dict[str, Any]]:
        all_reviews = []
        seen_ids = set()

        sort_strategies = [Sort.NEWEST, Sort.MOST_RELEVANT] if count > 2000 else [Sort.NEWEST]
        per_sort_target = count // len(sort_strategies) + 500

        for sort_order in sort_strategies:
            print(f"   🔍 Fetching Google Play reviews with sort={sort_order.name} (target: {per_sort_target})...")
            try:
                result, continuation_token = reviews(
                    self.APP_ID,
                    lang=lang,
                    country=country,
                    sort=sort_order,
                    count=min(per_sort_target, 200),
                )
                for r in result:
                    rid = r.get("reviewId")
                    if rid and rid not in seen_ids:
                        seen_ids.add(rid)
                        all_reviews.append(r)

                sort_fetched = len(result)
                while sort_fetched < per_sort_target and continuation_token:
                    batch_count = min(per_sort_target - sort_fetched, 200)
                    result, continuation_token = reviews(
                        self.APP_ID,
                        continuation_token=continuation_token,
                        count=batch_count,
                    )
                    if not result:
                        break
                    for r in result:
                        rid = r.get("reviewId")
                        if rid and rid not in seen_ids:
                            seen_ids.add(rid)
                            all_reviews.append(r)
                    sort_fetched += len(result)

            except Exception as e:
                print(f"   ⚠️ Error scraping with sort {sort_order.name}: {e}")

        return [self._to_document(r) for r in all_reviews if r.get("content")]

    def _to_document(self, review: Dict[str, Any]) -> Dict[str, Any]:
        dt = review.get("at")
        timestamp_str = dt.isoformat() if dt else None
        return self.create_raw_document(
            raw_item=review,
            text=review.get("content", ""),
            source_id=review.get("reviewId", ""),
            author=review.get("userName"),
            metadata={
                "rating": review.get("score"),
                "thumbs_up": review.get("thumbsUpCount", 0),
                "timestamp": timestamp_str,
                "app_version": review.get("reviewCreatedVersion"),
            },
        )

    def get_source_id(self, raw_item: Dict[str, Any]) -> str:
        return str(raw_item.get("reviewId", ""))
