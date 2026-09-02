#!/usr/bin/env python3
"""
CLI script to run the full ingestion pipeline.
Scrapes Google Play Store reviews and Reddit posts/comments,
cleans, deduplicates, normalizes, and stores them in the database.

Usage:
    python scripts/run_ingestion.py
    python scripts/run_ingestion.py --gp-count 1000 --reddit-limit 50
    python scripts/run_ingestion.py --skip-gp        # Reddit only
    python scripts/run_ingestion.py --skip-reddit     # Google Play only
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(
        description="Myntra Discovery Engine — Data Ingestion"
    )
    parser.add_argument(
        "--gp-count", type=int, default=5000,
        help="Number of Google Play reviews to fetch (default: 5000)"
    )
    parser.add_argument(
        "--reddit-limit", type=int, default=100,
        help="Max posts per query from Reddit (default: 100)"
    )
    parser.add_argument(
        "--skip-gp", action="store_true",
        help="Skip Google Play Store scraping"
    )
    parser.add_argument(
        "--app-store-count", type=int, default=500,
        help="Number of Apple App Store reviews to fetch (default: 500)"
    )
    parser.add_argument(
        "--skip-app-store", action="store_true",
        help="Skip Apple App Store scraping"
    )
    parser.add_argument(
        "--skip-reddit", action="store_true", default=True,
        help="Skip Reddit direct PRAW scraping"
    )
    parser.add_argument(
        "--apify", action="store_true",
        help="Enable Reddit scraping via Apify Actor"
    )
    parser.add_argument(
        "--apify-count", type=int, default=5,
        help="Max items to fetch via Apify to conserve credits (default: 5)"
    )
    parser.add_argument(
        "--apify-app-store", action="store_true",
        help="Enable deep Apple App Store scraping via Apify Actor"
    )
    parser.add_argument(
        "--apify-app-store-count", type=int, default=500,
        help="Target number of wishlisting/cart reviews to fetch from Apple App Store via Apify (default: 500)"
    )
    args = parser.parse_args()

    from ingestion.orchestrator import IngestionOrchestrator

    orchestrator = IngestionOrchestrator()
    orchestrator.run(
        skip_google_play=args.skip_gp,
        skip_app_store=args.skip_app_store,
        skip_reddit=args.skip_reddit,
        use_apify_reddit=args.apify,
        use_apify_app_store=args.apify_app_store,
        gp_count=args.gp_count,
        app_store_count=args.app_store_count,
        apify_app_store_count=args.apify_app_store_count,
        reddit_limit=args.reddit_limit,
        apify_count=args.apify_count,
    )


if __name__ == "__main__":
    main()
