#!/usr/bin/env python3
"""
Seeds the database with realistic sample Myntra review data across diverse fashion categories:
ethnic wear, western wear, footwear, sizing, fabric quality, wedding/festive occasions,
delivery experience, and return policies.

Usage:
    python scripts/seed_db.py
    python scripts/seed_db.py --analyze   # Automatically run AI analysis on seeded data
"""

import argparse
import hashlib
import json
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import Database

SAMPLE_REVIEWS = [
    {
        "text": "I wishlisted 4 Anouk and Libas ethnic kurtas for my sister's wedding next month. The embroidery looks gorgeous in pictures, but I am scared the real fabric will be cheap polyester instead of georgette. Wish there was customer photo reviews with fabric closeups.",
        "source": "reddit",
        "rating": 4,
        "upvotes": 42,
        "author": "delhi_fashionista"
    },
    {
        "text": "Saved these Puma running shoes in my wishlist during Big Fashion Festival. I am confused between UK 8 and UK 9 because Puma runs narrow and I have wide feet. Don't want to go through the hassle of exchange if it doesn't fit.",
        "source": "reddit",
        "rating": 3,
        "upvotes": 18,
        "author": "runner_guy_99"
    },
    {
        "text": "Added a Zara blazer and formal trousers to cart for an upcoming job interview. But the price of 4500 feels steep unless I know it won't crease easily during travel. Still in my wishlist while I look for alternatives.",
        "source": "google_play",
        "rating": 3,
        "author": "ananya_s"
    },
    {
        "text": "App has started charging a non-refundable convenience/platform fee on every order. If I order 3 items to check size and return 2, I lose money on platform fee! So I just keep items saved in wishlist and buy from local stores instead.",
        "source": "google_play",
        "rating": 1,
        "author": "rohit_mumbai"
    },
    {
        "text": "Loved the party wear gown design by Tokyo Talkies. Saved it 2 weeks back. Hesitant to purchase because delivery date says 8 days and my event is in 6 days. Express delivery option is missing for my pincode.",
        "source": "google_play",
        "rating": 2,
        "author": "priya_k"
    },
    {
        "text": "I browse Myntra daily for streetwear inspiration and add oversized graphic tees to my wishlist. I wait to see how creators style them on Instagram before actually buying.",
        "source": "reddit",
        "rating": 5,
        "upvotes": 65,
        "author": "streetwear_india"
    },
    {
        "text": "Wishlisted a silk blend saree for Diwali gifting for my mother. The color looks emerald green in primary photo but teal in the model video. Unsure of the true shade.",
        "source": "reddit",
        "rating": 4,
        "upvotes": 29,
        "author": "festive_shopper"
    },
    {
        "text": "The return policy is getting stricter and pickup agents often dispute tag condition. I used to buy 5 items and keep 2, now I keep 10 items in wishlist and buy nothing.",
        "source": "google_play",
        "rating": 2,
        "author": "vikram_bengaluru"
    },
    {
        "text": "Saved Roadster denim jacket in wishlist. Price fluctuated from 1299 to 1899 to 1499 within 3 days. Not sure what the genuine fair price is so I am waiting indefinitely.",
        "source": "reddit",
        "rating": 3,
        "upvotes": 34,
        "author": "deal_hunter_in"
    },
    {
        "text": "Looking for cotton maternity dresses. Saved several options on Myntra, but none of the product descriptions clarify if there is feeding zipper access or pure 100% breathable cotton.",
        "source": "google_play",
        "rating": 3,
        "author": "sneha_r"
    },
    {
        "text": "Wishlisted Levi's 511 jeans. Reluctant to checkout because different washes under the same model name have completely different stretch percentages and fabric thickness.",
        "source": "reddit",
        "rating": 4,
        "upvotes": 22,
        "author": "denim_head"
    },
    {
        "text": "Added ethnic mojris and leather loafers to wishlist for festive season. Worried about shoe bite and stiffness of sole. Sizing chart has no foot circumference guide.",
        "source": "google_play",
        "rating": 3,
        "author": "manish_jaipur"
    }
]


def generate_mock_documents(count: int = 50):
    docs = []
    base_time = datetime.utcnow()

    for i in range(count):
        sample = random.choice(SAMPLE_REVIEWS)
        doc_id = str(uuid.uuid4())
        source = sample["source"]
        author = f"{sample.get('author', 'user')}_{i+1}"
        author_hash = hashlib.sha256(author.encode()).hexdigest()[:16]
        
        # Slight variation in text
        text = sample["text"]
        timestamp = (base_time - timedelta(days=random.randint(1, 45))).isoformat()
        
        metadata = {
            "rating": sample.get("rating", random.randint(1, 5)),
            "upvotes": sample.get("upvotes", random.randint(0, 50)),
            "source_type": source
        }

        docs.append({
            "doc_id": doc_id,
            "source": source,
            "source_id": f"seed_{source}_{i+1}_{uuid.uuid4().hex[:6]}",
            "author_hash": author_hash,
            "text": text,
            "timestamp": timestamp,
            "metadata": metadata,
            "ingested_at": datetime.utcnow().isoformat()
        })

    return docs


def main():
    parser = argparse.ArgumentParser(description="Seed Myntra Discovery Engine Database")
    parser.add_argument("--count", type=int, default=30, help="Number of sample documents to seed (default: 30)")
    args = parser.parse_args()

    print("=" * 60)
    print("MYNTRA DISCOVERY ENGINE — DATABASE SEEDER")
    print("=" * 60)
    print(f"🌱 Generating {args.count} realistic fashion review documents...")

    docs = generate_mock_documents(args.count)
    db = Database()
    db.insert_raw_documents(docs)

    print(f"✅ Successfully seeded {len(docs)} documents into database!")
    stats = db.get_overview_stats()
    print(f"📊 Total documents now in DB: {stats['total_documents']}")
    print(f"💡 Run 'python scripts/run_analysis.py --limit {args.count}' to analyze seeded records.")
    print("=" * 60)


if __name__ == "__main__":
    main()
