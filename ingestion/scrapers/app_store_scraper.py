"""
Apple App Store Scraper

Scrapes public user reviews for the Google Photos iOS application using
Apple's iTunes Customer Reviews RSS / JSON API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import requests

from .base_scraper import BaseScraper
from config.settings import APP_STORE_ID


class AppStoreScraper(BaseScraper):
    """Scraper for Apple App Store (iOS) customer reviews."""

    # Google Photos on iOS App Store
    APP_ID = APP_STORE_ID

    def __init__(self, app_id: Optional[str] = None):
        super().__init__(source_name="app_store")
        self.app_id = app_id or self.APP_ID

    def scrape(
        self,
        count: int = 500,
        country: str = "in",
        sort_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape reviews from Apple App Store RSS feed.
        
        Args:
            count: Max number of reviews to fetch.
            country: Two-letter ISO country code (default 'in' for India).
            sort_by: 'mostRecent', 'mostHelpful', or None (both for max coverage).
        """
        all_reviews = []
        seen_ids = set()

        sort_strategies = [sort_by] if sort_by else ["mostRecent", "mostHelpful"]
        per_sort_target = count // len(sort_strategies) + 50

        for current_sort in sort_strategies:
            max_pages = min((per_sort_target + 49) // 50, 10)

            for page in range(1, max_pages + 1):
                if len(all_reviews) >= count:
                    break

                url = (
                    f"https://itunes.apple.com/{country}/rss/customerreviews/"
                    f"page={page}/id={self.app_id}/sortBy={current_sort}/json"
                )
                print(f"   🔍 Fetching Apple App Store reviews ({current_sort}, page {page}/{max_pages})...")

                try:
                    resp = requests.get(url, timeout=15)
                    if resp.status_code != 200:
                        print(f"      ⚠️ App Store returned status code {resp.status_code} on page {page}")
                        break

                    data = resp.json()
                    feed = data.get("feed", {})
                    entries = feed.get("entry", [])

                    if not entries:
                        break

                    # Sometimes entry is a single dict if only 1 item
                    if isinstance(entries, dict):
                        entries = [entries]

                    for entry in entries:
                        if len(all_reviews) >= count:
                            break

                        # Check if entry is a review (has author and rating)
                        if "author" not in entry or "im:rating" not in entry:
                            continue

                        review_id = self.get_source_id(entry)
                        if review_id and review_id not in seen_ids:
                            seen_ids.add(review_id)
                            doc = self._to_document(entry, country=country)
                            if doc:
                                all_reviews.append(doc)

                except Exception as e:
                    print(f"      ⚠️ Error scraping Apple App Store page {page}: {e}")
                    break

        print(f"   ✅ Fetched {len(all_reviews)} Apple App Store reviews across {len(sort_strategies)} sort strategies")
        return all_reviews

    def _to_document(self, entry: Dict[str, Any], country: str = "in") -> Optional[Dict[str, Any]]:
        """Convert raw iTunes JSON review entry into a standardized RawDocument dict."""
        source_id = self.get_source_id(entry)

        title = entry.get("title", {}).get("label", "").strip()
        content = entry.get("content", {}).get("label", "").strip()

        # Combine title and review body for complete context
        full_text = f"{title}\n\n{content}".strip() if title and content else (content or title)
        if not full_text:
            return None

        # Author
        author_name = entry.get("author", {}).get("name", {}).get("label", "")

        # Rating (1 to 5)
        rating_str = entry.get("im:rating", {}).get("label", "0")
        try:
            rating = int(rating_str)
        except ValueError:
            rating = None

        # App version
        app_version = entry.get("im:version", {}).get("label", "")

        # Timestamp / Updated
        updated_str = entry.get("updated", {}).get("label")
        timestamp = updated_str if updated_str else datetime.utcnow().isoformat()

        # Vote count
        vote_count_str = entry.get("im:voteCount", {}).get("label", "0")
        try:
            vote_count = int(vote_count_str)
        except ValueError:
            vote_count = 0

        return self.create_raw_document(
            raw_item=entry,
            text=full_text,
            source_id=source_id,
            author=author_name,
            metadata={
                "rating": rating,
                "title": title,
                "app_version": app_version,
                "vote_count": vote_count,
                "country": country,
                "timestamp": timestamp,
            },
        )

    def get_source_id(self, raw_item: Dict[str, Any]) -> str:
        """Extract review ID from raw iTunes entry."""
        id_entry = raw_item.get("id", {})
        if isinstance(id_entry, dict):
            return str(id_entry.get("label", ""))
        return str(id_entry or "")
