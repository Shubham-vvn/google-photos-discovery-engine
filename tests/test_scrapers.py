"""
Task 7.1 — tests/test_scrapers.py
Tests that Google Play and Reddit/Apify scrapers return valid documents
conforming to the RawDocument contract.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.scrapers.base_scraper import BaseScraper
from ingestion.scrapers.google_play_scraper import GooglePlayScraper
from ingestion.scrapers.app_store_scraper import AppStoreScraper
from ingestion.scrapers.apify_app_store_scraper import ApifyAppStoreScraper
from ingestion.scrapers.apify_scraper import ApifyRedditScraper


# ─── Google Play Scraper ───────────────────────────────────────────

class TestGooglePlayScraper:

    def test_scraper_inherits_base(self):
        gp = GooglePlayScraper()
        assert isinstance(gp, BaseScraper)
        assert gp.source_name == "google_play"
        assert gp.APP_ID == "com.google.android.apps.photos"

    def test_to_document_creates_valid_schema(self):
        gp = GooglePlayScraper()
        from datetime import datetime
        mock_review = {
            "reviewId": "abc-123",
            "content": "Size chart was inaccurate, returned the item.",
            "score": 2,
            "thumbsUpCount": 15,
            "userName": "TestUser",
            "at": datetime(2026, 8, 1),
            "reviewCreatedVersion": "4.2.1",
        }
        doc = gp._to_document(mock_review)

        # Required fields exist
        assert doc["source"] == "google_play"
        assert doc["source_id"] == "abc-123"
        assert doc["text"] == "Size chart was inaccurate, returned the item."
        assert doc["author"] == "TestUser"
        assert "metadata" in doc
        assert doc["metadata"]["rating"] == 2
        assert doc["metadata"]["thumbs_up"] == 15
        assert "scraped_at" in doc

    @patch("ingestion.scrapers.google_play_scraper.reviews")
    def test_scrape_returns_list(self, mock_reviews):
        """Scrape returns parsed list of RawDocuments."""
        from datetime import datetime
        mock_reviews.return_value = ([
            {
                "reviewId": "gp-test-1",
                "content": "Cannot find my photos from last summer trip.",
                "score": 2,
                "thumbsUpCount": 4,
                "userName": "PhotoUser",
                "at": datetime(2026, 8, 1),
                "reviewCreatedVersion": "6.80.0",
            }
        ], None)
        gp = GooglePlayScraper()
        docs = gp.scrape(count=3)

        assert isinstance(docs, list)
        assert len(docs) > 0

        for doc in docs:
            assert "source" in doc
            assert "text" in doc
            assert doc["source"] == "google_play"
            assert len(doc["text"]) > 0
            assert "metadata" in doc

    def test_get_source_id(self):
        gp = GooglePlayScraper()
        assert gp.get_source_id({"reviewId": "xyz-789"}) == "xyz-789"
        assert gp.get_source_id({}) == ""


# ─── Apple App Store Scraper ───────────────────────────────────────

class TestAppStoreScraper:

    def test_scraper_inherits_base(self):
        app_store = AppStoreScraper()
        assert isinstance(app_store, BaseScraper)
        assert app_store.source_name == "app_store"
        assert app_store.APP_ID == "962194608"

    def test_to_document_creates_valid_schema(self):
        app_store = AppStoreScraper()
        mock_entry = {
            "id": {"label": "ios-rev-101"},
            "title": {"label": "Great UI but delivery delayed"},
            "content": {"label": "The clothes quality is top notch, but delivery took 5 days.", "attributes": {"type": "text"}},
            "im:rating": {"label": "4"},
            "im:version": {"label": "5.12.0"},
            "im:voteCount": {"label": "12"},
            "author": {"name": {"label": "iOSShopper"}},
            "updated": {"label": "2026-08-20T14:30:00-07:00"},
        }
        doc = app_store._to_document(mock_entry, country="in")

        assert doc is not None
        assert doc["source"] == "app_store"
        assert doc["source_id"] == "ios-rev-101"
        assert "Great UI" in doc["text"]
        assert "delivery took 5 days" in doc["text"]
        assert doc["author"] == "iOSShopper"
        assert doc["metadata"]["rating"] == 4
        assert doc["metadata"]["app_version"] == "5.12.0"
        assert doc["metadata"]["vote_count"] == 12
        assert doc["metadata"]["country"] == "in"
        assert "scraped_at" in doc

    def test_to_document_skips_empty(self):
        app_store = AppStoreScraper()
        empty_entry = {
            "id": {"label": "empty-1"},
            "title": {"label": ""},
            "content": {"label": ""},
            "im:rating": {"label": "3"},
        }
        doc = app_store._to_document(empty_entry)
        assert doc is None

    def test_get_source_id(self):
        app_store = AppStoreScraper()
        assert app_store.get_source_id({"id": {"label": "entry-999"}}) == "entry-999"
        assert app_store.get_source_id({"id": "simple-id"}) == "simple-id"
        assert app_store.get_source_id({}) == ""

    def test_scrape_live_sample(self):
        """Live scrape of a small batch of reviews to verify iTunes RSS connectivity."""
        app_store = AppStoreScraper()
        docs = app_store.scrape(count=3, country="in")
        assert isinstance(docs, list)
        if docs:
            assert docs[0]["source"] == "app_store"
            assert "text" in docs[0]
            assert "metadata" in docs[0]


# ─── Apify Reddit Scraper ─────────────────────────────────────────

class TestApifyRedditScraper:

    def test_scraper_inherits_base(self):
        scraper = ApifyRedditScraper()
        assert isinstance(scraper, BaseScraper)
        assert scraper.source_name == "reddit_apify"

    def test_to_document_creates_valid_schema(self):
        scraper = ApifyRedditScraper()
        mock_item = {
            "id": "post-456",
            "title": "Why I stopped ordering from Myntra",
            "body": "Fabric was nothing like the photos. Quality is terrible.",
            "communityName": "r/IndianFashionAddicts",
            "upVotes": 42,
            "numberOfComments": 8,
            "url": "https://reddit.com/r/IndianFashionAddicts/post-456",
            "createdAt": "2026-08-15T10:30:00Z",
        }
        doc = scraper._to_document(mock_item)

        assert doc is not None
        assert doc["source"] == "reddit_apify"
        assert "Myntra" in doc["text"]
        assert "Fabric" in doc["text"]
        assert doc["metadata"]["subreddit"] == "r/IndianFashionAddicts"
        assert doc["metadata"]["upvotes"] == 42

    def test_to_document_skips_empty_text(self):
        scraper = ApifyRedditScraper()
        empty_item = {"id": "empty-1", "title": "", "body": ""}
        doc = scraper._to_document(empty_item)
        assert doc is None

    def test_to_document_title_only(self):
        """Posts with title but no body should still return a document."""
        scraper = ApifyRedditScraper()
        title_only = {"id": "title-1", "title": "Myntra sizing is terrible"}
        doc = scraper._to_document(title_only)
        assert doc is not None
        assert "sizing" in doc["text"]

    def test_get_source_id(self):
        scraper = ApifyRedditScraper()
        assert scraper.get_source_id({"id": "abc"}) == "abc"
        assert scraper.get_source_id({"postId": "xyz"}) == "xyz"


# ─── Apify Apple App Store Scraper ─────────────────────────────────

class TestApifyAppStoreScraper:

    def test_scraper_inherits_base(self):
        scraper = ApifyAppStoreScraper()
        assert isinstance(scraper, BaseScraper)
        assert scraper.source_name == "app_store_apify"
        assert scraper.APP_ID == "962194608"

    def test_to_document_creates_valid_schema(self):
        scraper = ApifyAppStoreScraper()
        mock_item = {
            "review_id": "14476779843",
            "review_title": "Wishlist price drop glitch",
            "review_text": "I saved several kurtas in my wishlist but price increased upon checkout.",
            "rating": 2,
            "reviewed_version": "Version 4.2608.30",
            "author_name": "FashionLoverIndia",
            "app_country": "in",
            "review_date_iso": "2026-08-27",
        }
        full_text = f"{mock_item['review_title']}\n\n{mock_item['review_text']}"
        doc = scraper._to_document(mock_item, full_text=full_text, source_id="14476779843")

        assert doc is not None
        assert doc["source"] == "app_store_apify"
        assert doc["source_id"] == "14476779843"
        assert "Wishlist price drop" in doc["text"]
        assert doc["author"] == "FashionLoverIndia"
        assert doc["metadata"]["rating"] == 2
        assert doc["metadata"]["app_version"] == "Version 4.2608.30"
        assert doc["metadata"]["country"] == "in"
        assert doc["metadata"]["source_scraper"] == "apify_apple_app_store"
        assert "scraped_at" in doc

    def test_get_source_id(self):
        scraper = ApifyAppStoreScraper()
        assert scraper.get_source_id({"review_id": "rev-999"}) == "rev-999"
        assert scraper.get_source_id({"id": "id-888"}) == "id-888"
        assert scraper.get_source_id({}) == ""

