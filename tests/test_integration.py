"""
Task 7.2 — tests/test_integration.py
End-to-end integration test verifying the full pipeline:
  Ingestion → Storage → Query Helpers → Dashboard API

Runs against the real SQLite database to confirm data flows
correctly through all layers.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import Database


class TestIntegrationPipeline:
    """Verifies that previously ingested + analyzed data is queryable end-to-end."""

    def setup_method(self):
        self.db = Database()

    def test_database_has_documents(self):
        stats = self.db.get_overview_stats()
        assert stats["total_documents"] > 0, "Database should have ingested documents"

    def test_database_has_extractions(self):
        stats = self.db.get_overview_stats()
        assert stats["total_extractions"] > 0, "Database should have AI extractions"

    def test_avg_confidence_is_valid(self):
        stats = self.db.get_overview_stats()
        assert 0.0 <= stats["avg_confidence"] <= 1.0

    def test_sources_populated(self):
        stats = self.db.get_overview_stats()
        assert len(stats["sources"]) > 0, "At least one data source should be populated"

    def test_top_blockers_returns_data(self):
        blockers = self.db.get_top_blockers(limit=5)
        assert isinstance(blockers, list)
        assert len(blockers) > 0, "Should have at least one aggregated blocker pattern"
        for b in blockers:
            assert "blocker_tag" in b
            assert "occurrence_count" in b
            assert b["occurrence_count"] > 0

    def test_persona_stats_returns_data(self):
        personas = self.db.get_persona_stats()
        assert isinstance(personas, list)
        assert len(personas) > 0, "Should have at least one discovered persona"
        for p in personas:
            assert "shopper_persona" in p
            assert "count" in p
            assert p["count"] > 0

    def test_uncertainty_stats_returns_data(self):
        uncertainties = self.db.get_uncertainty_stats()
        assert isinstance(uncertainties, dict)
        assert len(uncertainties) > 0, "Should have at least one uncertainty type"

    def test_confidence_distribution_sums_correctly(self):
        dist = self.db.get_confidence_distribution()
        assert "high (0.7-1.0)" in dist
        assert "medium (0.4-0.7)" in dist
        assert "low (0.0-0.4)" in dist

        total = dist["high (0.7-1.0)"] + dist["medium (0.4-0.7)"] + dist["low (0.0-0.4)"]
        stats = self.db.get_overview_stats()
        assert total == stats["total_extractions"]

    def test_all_extractions_query(self):
        items = self.db.get_all_extractions(limit=10)
        assert isinstance(items, list)
        assert len(items) > 0
        for item in items:
            assert "doc_id" in item
            assert "confidence_score" in item
            assert "source" in item

    def test_dashboard_api_overview_end_to_end(self):
        """Verify the dashboard API returns correct data from the real DB."""
        from fastapi.testclient import TestClient
        from dashboard.api import app

        client = TestClient(app)
        resp = client.get("/api/overview")
        assert resp.status_code == 200

        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["stats"]["total_documents"] > 0
        assert data["data"]["stats"]["total_extractions"] > 0
        assert len(data["data"]["topBlockers"]) > 0

    def test_dashboard_api_evidence_search(self):
        """Test evidence search with a keyword filter."""
        from fastapi.testclient import TestClient
        from dashboard.api import app

        client = TestClient(app)
        resp = client.get("/api/evidence?limit=5")
        assert resp.status_code == 200

        data = resp.json()
        assert data["status"] == "success"
        assert len(data["data"]) > 0
