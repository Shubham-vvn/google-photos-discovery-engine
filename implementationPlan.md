# 🚀 Google Photos AI Discovery Engine — Implementation Plan

> **Transforming the discovery engine from fashion e-commerce to Google Photos Cognitive Memory Retrieval.**

---

## Phases Overview

- [x] **Phase 0: Workspace Cleanup & Database Reset**
  - [x] Purge Myntra database and raw/processed artifacts
  - [x] Configure `data/photos_discovery.db`
  - [x] Update Git repository and Render service name

- [ ] **Phase 1: Configuration & Taxonomy Alignment**
  - [ ] Rewrite `config/taxonomy.yaml` with cognitive memory taxonomy (clues, forgotten elements, failure points, photo categories, user personas)
  - [ ] Update `config/settings.py` with Google Photos Play Store package, iOS App ID, and Reddit subreddits

- [ ] **Phase 2: Ingestion Layer Modernization**
  - [ ] Update `ingestion/scrapers/google_play_scraper.py` to target `com.google.android.apps.photos`
  - [ ] Update `ingestion/scrapers/app_store_scraper.py` to target Google Photos iOS ID `962194608`
  - [ ] Update `ingestion/scrapers/reddit_scraper.py` and Apify scrapers with photo search retrieval queries
  - [ ] Update `ingestion/orchestrator.py`

- [ ] **Phase 3: Cognitive Memory AI Extraction & Confidence Scoring**
  - [ ] Re-engineer `analysis/prompts/extraction_prompt.txt` to extract episodic clues, forgotten items, search queries, and failure points
  - [ ] Update `analysis/preprocessor.py` keyword filter for photo retrieval vocabulary
  - [ ] Update `analysis/llm_extractor.py`, `analysis/classifier.py`, and `analysis/confidence_scorer.py`
  - [ ] Update `analysis/aggregator.py`

- [ ] **Phase 4: SQLite Database Schema & Multi-Source Seed Dataset**
  - [ ] Update `storage/database.py` schema to store cognitive memory dimensions
  - [ ] Create `scripts/seed_db.py` with realistic, rich multi-source customer reviews (Play Store, App Store, Reddit) reflecting real retrieval struggles so the engine is immediately populated with high-signal evidence

- [ ] **Phase 5: Interactive Discovery Dashboard & PM Copilot**
  - [ ] Update `dashboard/api.py` with Google Photos discovery endpoints
  - [ ] Redesign `dashboard/templates/index.html` with Google Photos brand identity, cognitive charts, and search query analysis
  - [ ] Update `dashboard/static/css/style.css` and `dashboard/static/js/app.js`
  - [ ] Update `dashboard/discovery_engine.py` PM query copilot

- [ ] **Phase 6: Part 5 AI-Native Retrieval MVP Prototype**
  - [ ] Add interactive Retrieval MVP playground endpoint & UI where users can test finding photos with vague memory clues

- [ ] **Phase 7: Testing, Documentation & Cloud Sync**
  - [ ] Update unit tests in `tests/`
  - [ ] Update `README.md`
  - [ ] Commit and push to GitHub repository
