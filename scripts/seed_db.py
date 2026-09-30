#!/usr/bin/env python3
"""
Seeds the database with realistic sample Google Photos user feedback data
across diverse photo retrieval scenarios, cognitive memory breakdowns,
and search formulation struggles.

Usage:
    python scripts/seed_db.py
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
from analysis.aggregator import Aggregator

CORE_SCENARIOS = [
    # 1. Visual Utility / Medicine / Receipts / Documents
    {
        "text": "I was desperately trying to find a picture of the white medicine tablet strip I took when I had severe food poisoning last monsoon. I searched 'medicine', 'pills', 'prescription' — 0 results because Google Photos OCR couldn't read the shiny blister foil packaging. Had to manually scroll for 45 minutes through 7,000 photos to find it!",
        "source": "reddit",
        "category": "visual_utility_document",
        "target": "white blister foil medicine strip for food poisoning",
        "clues": ["visual_anchor", "emotional_context", "temporal_approximation"],
        "details": "white pills in foil, taken during food poisoning illness last monsoon season",
        "forgotten": ["exact_date", "exact_text_content", "gps_geotag"],
        "query": "medicine pills prescription",
        "behavior": "synonym_churning",
        "failure": "ocr_text_mismatch",
        "frustration": "0 results returned because OCR missed reflective blister pack text, forced into 45-minute scroll",
        "persona": "visual_note_taker",
        "request": "Enhanced OCR recognizing blurry foil packaging and handwriting"
    },
    {
        "text": "Took a photo of my car tire replacement bill and warranty slip about 18 months ago. I don't remember the shop name or exact date. Searching 'Apollo tire receipt' gives zero results because the photo was backed up without geotag and the receipt ink had faded slightly. Useless search for documents.",
        "source": "google_play",
        "category": "visual_utility_document",
        "target": "car tire replacement warranty invoice and receipt",
        "clues": ["visual_anchor", "temporal_approximation", "activity_context"],
        "details": "tire replacement receipt from around 18 months ago",
        "forgotten": ["exact_date", "exact_text_content", "gps_geotag"],
        "query": "Apollo tire receipt warranty",
        "behavior": "keyword_stacking",
        "failure": "zero_results",
        "frustration": "Zero search results for document; faded text wasn't indexed",
        "persona": "visual_note_taker",
        "request": "Auto-categorize warranty cards and paper receipts with fuzzy text search"
    },
    {
        "text": "I snap pictures of serial numbers on home appliances (refrigerator, washing machine). When the repair technician came, I searched 'refrigerator serial number'. It showed me 50 pictures of food inside my fridge from 2022 instead of the barcode sticker on the back!",
        "source": "google_support",
        "category": "visual_utility_document",
        "target": "appliance barcode and serial number sticker",
        "clues": ["visual_anchor", "activity_context"],
        "details": "white barcode sticker on metallic frame of appliance",
        "forgotten": ["exact_date", "album_folder_name"],
        "query": "refrigerator serial number",
        "behavior": "keyword_stacking",
        "failure": "semantic_misunderstanding",
        "frustration": "Returned pictures of food inside fridge rather than the barcode sticker",
        "persona": "visual_note_taker",
        "request": "Separate utility document filter from casual food and lifestyle photos"
    },

    # 2. Episodic Life Events / Vacations / Meals / Outings
    {
        "text": "We went to this quaint little beachside cafe in North Goa two winters ago where we had pancakes by the sea. I can't remember the date or the cafe name, only that it had blue wooden chairs and Priya was with us. I searched 'Goa cafe' and it dumped 850 photos of every beach, shack, and coconut tree from our trip. Gave up after 15 minutes of scrolling.",
        "source": "reddit",
        "category": "episodic_life_event",
        "target": "breakfast at beachside cafe with blue chairs in Goa",
        "clues": ["visual_anchor", "social_companion", "location_vibe", "temporal_approximation"],
        "details": "blue chairs, beach view, eating pancakes with Priya during Goa trip 2 winters ago",
        "forgotten": ["exact_date", "gps_geotag", "album_folder_name"],
        "query": "Goa cafe breakfast",
        "behavior": "keyword_stacking",
        "failure": "overwhelming_results",
        "frustration": "Dumped 850 unranked vacation photos; impossible to pinpoint the specific breakfast spot",
        "persona": "life_documenter",
        "request": "Filter search results by companion present and time of day (breakfast/morning)"
    },
    {
        "text": "Trying to find a sunset photo from our Manali trek where there was a yellow tent pitched on the ridge. I searched 'Manali sunset yellow tent'. Google Photos returned 0 results! It recognized 'Manali' and 'sunset' separately, but couldn't combine them with the yellow tent clue. Why is multi-clue retrieval so broken?",
        "source": "app_store",
        "category": "episodic_life_event",
        "target": "yellow camping tent at mountain ridge sunset",
        "clues": ["visual_anchor", "location_vibe", "activity_context"],
        "details": "yellow tent pitched on mountain ridge during sunset hiking trip",
        "forgotten": ["exact_date", "gps_geotag"],
        "query": "Manali sunset yellow tent",
        "behavior": "keyword_stacking",
        "failure": "zero_results",
        "frustration": "Multi-attribute search collapsed to 0 hits even though all objects were clearly visible",
        "persona": "life_documenter",
        "request": "Support complex multi-object queries without falling back to zero results"
    },
    {
        "text": "Remember that amazing seafood dinner we had at an open-air rooftop during my brother's wedding celebrations in Udaipur? I wanted to show my coworker the dessert platter. Searched 'Udaipur wedding food' and got 400 photos of stage decorations and flower garlands. The food photos were buried 300 rows down.",
        "source": "google_play",
        "category": "episodic_life_event",
        "target": "dessert platter at rooftop wedding dinner in Udaipur",
        "clues": ["visual_anchor", "social_companion", "location_vibe", "activity_context"],
        "details": "dessert platter, rooftop dining, brother's wedding celebrations in Udaipur",
        "forgotten": ["exact_date", "album_folder_name"],
        "query": "Udaipur wedding food dinner",
        "behavior": "keyword_stacking",
        "failure": "overwhelming_results",
        "frustration": "Specific dessert and dining photos drowned out by generic wedding stage decor",
        "persona": "life_documenter",
        "request": "Disambiguate sub-events within large events (e.g. food vs ceremony)"
    },

    # 3. Screenshots / Saved Media / Recommendations
    {
        "text": "I saved a Twitter screenshot of a book recommendation with a bright orange cover about behavioral economics about 6 months ago. I searched 'book orange' and 'book recommendation' — Google Photos showed me pictures of fruit oranges and my college textbooks! It completely ignores the visual design of screenshots.",
        "source": "reddit",
        "category": "screenshot_saved_media",
        "target": "Twitter screenshot of book with bright orange cover",
        "clues": ["visual_anchor", "temporal_approximation"],
        "details": "orange cover book recommended on a Twitter screenshot ~6 months back",
        "forgotten": ["exact_text_content", "exact_date"],
        "query": "book orange recommendation",
        "behavior": "synonym_churning",
        "failure": "semantic_misunderstanding",
        "frustration": "Returned fruit oranges and textbook photos instead of the Twitter screenshot",
        "persona": "screenshot_curator",
        "request": "Semantic screenshot search that reads app UI context and visual book covers"
    },
    {
        "text": "Captured a screenshot of an authentic Thai green curry recipe from Instagram reels. Forgot to save the bookmark. Searched 'curry recipe' in Google Photos, but since the text was stylized cursive font over a video preview, the OCR failed completely. My screenshot folder has 4,200 images, impossible to find.",
        "source": "app_store",
        "category": "screenshot_saved_media",
        "target": "Instagram screenshot of Thai green curry ingredients and recipe",
        "clues": ["visual_anchor", "activity_context"],
        "details": "Thai green curry recipe with cursive ingredient list from Instagram",
        "forgotten": ["exact_text_content", "exact_date", "album_folder_name"],
        "query": "curry recipe green thai",
        "behavior": "keyword_stacking",
        "failure": "ocr_text_mismatch",
        "frustration": "Stylized script font wasn't indexed by OCR; screenshot lost in 4,200 screenshots",
        "persona": "screenshot_curator",
        "request": "Screenshot visual clustering by source app and visual theme"
    },

    # 4. People & Portraits / Emotional Nostalgia
    {
        "text": "Looking for an old picture of my late grandfather sitting in his wooden rocking chair in our old verandah. It was taken maybe 8 or 9 years ago on an old phone before facial recognition was good. I searched 'grandfather rocking chair' and got nothing. When I tried to scroll back to 2015, the app stuttered and crashed. Heartbreaking experience.",
        "source": "reddit",
        "category": "people_and_portraits",
        "target": "grandfather sitting in wooden rocking chair on verandah",
        "clues": ["visual_anchor", "social_companion", "location_vibe", "emotional_context"],
        "details": "grandfather in rocking chair on old house verandah ~8-9 years ago",
        "forgotten": ["exact_date", "camera_device_metadata"],
        "query": "grandfather rocking chair verandah",
        "behavior": "natural_language_story",
        "failure": "temporal_disconnect",
        "frustration": "Old archive photos from previous phones not indexed by modern face clusters; scrolling crashes",
        "persona": "nostalgia_seeker",
        "request": "Retroactive face tag alignment and smooth decade archive jump"
    },
    {
        "text": "I wanted to find a funny photo of my daughter with spaghetti sauce all over her face when she was around 2 years old. I don't remember the exact month. Searched 'spaghetti baby' and got zero results. Then searched her face group with 'eating' and got 600 meal pictures. Couldn't find the messy sauce picture without 30 mins of scrolling.",
        "source": "google_play",
        "category": "people_and_portraits",
        "target": "toddler with red spaghetti sauce all over face",
        "clues": ["visual_anchor", "social_companion", "emotional_context", "temporal_approximation"],
        "details": "daughter at age 2 with messy red spaghetti sauce on face and bib",
        "forgotten": ["exact_date", "album_folder_name"],
        "query": "spaghetti baby messy food",
        "behavior": "synonym_churning",
        "failure": "scroll_fatigue_abandonment",
        "frustration": "Face group + eating returned 600 generic food photos; couldn't filter for messy/funny moments",
        "persona": "family_archivist",
        "request": "Emotion and expression filters (e.g. 'messy', 'laughing', 'crying', 'first times')"
    },
    {
        "text": "My sister was wearing this gorgeous bottle green lehenga at our cousin's sangeet in Jaipur around 3 years ago. I searched 'Jaipur green dress' — Google Photos showed green lawns, green trees, green shirts, but not her lehenga in the banquet hall. The semantic understanding of Indian traditional clothing is so weak.",
        "source": "reddit",
        "category": "episodic_life_event",
        "target": "sister wearing bottle green lehenga in banquet hall in Jaipur",
        "clues": ["visual_anchor", "social_companion", "location_vibe", "temporal_approximation"],
        "details": "sister in bottle green traditional outfit at night celebration in Jaipur ~3 years back",
        "forgotten": ["exact_date", "gps_geotag"],
        "query": "Jaipur green dress lehenga sangeet",
        "behavior": "keyword_stacking",
        "failure": "synonym_blindness",
        "frustration": "Search confused green ethnic wear with outdoor trees and casual clothing",
        "persona": "life_documenter",
        "request": "Cultural attire recognition and color-context binding"
    },
    {
        "text": "Every time I search with a natural sentence like 'the cafe we went to during our Goa trip', Google Photos acts like a dumb keyword search and matches every photo tagged Goa or cafe separately. It lacks any contextual conversational ability. If you don't remember the date, you're doomed to scroll.",
        "source": "google_support",
        "category": "episodic_life_event",
        "target": "casual vacation cafe visit",
        "clues": ["location_vibe", "activity_context"],
        "details": "cafe visited during Goa trip",
        "forgotten": ["exact_date", "gps_geotag"],
        "query": "the cafe we went to during our Goa trip",
        "behavior": "natural_language_story",
        "failure": "semantic_misunderstanding",
        "frustration": "App treats natural sentences as disjointed keywords instead of conversational memory intent",
        "persona": "life_documenter",
        "request": "Full natural language memory queries (Ask Photos style conversational agent)"
    }
]

AUTHORS = [
    "vikram_travels", "neha_delhi", "rohit_pixels", "ananya_clicks", "aditya_g",
    "priya_mumbai", "sneha_photo", "karthik_tech", "arjun_lens", "meera_memories",
    "rahul_dev", "pooja_sharma", "dev_capture", "tanvi_nostalgia", "amit_clicks"
]


def generate_dataset(target_count: int = 250):
    """Generate rich, realistic multi-source dataset expanding on core retrieval patterns."""
    documents = []
    extractions = []
    tags_list = []

    base_time = datetime(2026, 9, 20)

    for i in range(target_count):
        template = random.choice(CORE_SCENARIOS)
        doc_id = f"doc_gp_{i+1:04d}"
        extraction_id = f"ext_gp_{i+1:04d}"

        # Variations in wording and dates
        timestamp = (base_time - timedelta(days=random.randint(1, 180), hours=random.randint(1, 23))).isoformat()
        author = random.choice(AUTHORS) + f"_{random.randint(10, 99)}"
        author_hash = hashlib.sha256(f"{template['source']}_{author}".encode()).hexdigest()[:16]

        confidence = round(random.uniform(0.68, 0.95), 3)

        doc = {
            "doc_id": doc_id,
            "source": template["source"],
            "source_id": f"src_{template['source']}_{i+1000}",
            "author_hash": author_hash,
            "text": template["text"],
            "timestamp": timestamp,
            "metadata": {
                "author": author,
                "rating": random.choice([1, 2, 3]) if template["source"] in ["google_play", "app_store"] else None,
                "upvotes": random.randint(5, 85) if template["source"] == "reddit" else None,
                "category": template["category"]
            },
            "ingested_at": timestamp
        }
        documents.append(doc)

        ext = {
            "extraction_id": extraction_id,
            "doc_id": doc_id,
            "segment_index": 0,
            "segment_text": template["text"][:350],
            "photo_category": template["category"],
            "target_photo_description": template["target"],
            "remembered_clues": template["clues"],
            "remembered_details": template["details"],
            "forgotten_elements": template["forgotten"],
            "search_query_attempted": template["query"],
            "search_behavior": template["behavior"],
            "retrieval_failure_point": template["failure"],
            "user_frustration_detail": template["frustration"],
            "user_persona": template["persona"],
            "evidence_type": "direct_statement",
            "confidence_score": confidence,
            "feature_request": template["request"],
            "llm_model": "gemini-3.5-flash",
            "raw_response": json.dumps({"status": "parsed"}),
            "analyzed_at": timestamp,
            "tags": {
                "failure_point_tag": template["failure"],
                "photo_category_tag": template["category"],
                "persona_tag": template["persona"],
                "remembered_clue_tags": template["clues"],
                "forgotten_element_tags": template["forgotten"],
            }
        }
        extractions.append(ext)

    return documents, extractions


def main():
    parser = argparse.ArgumentParser(description="Seed Google Photos Discovery DB")
    parser.add_argument("--count", type=int, default=300, help="Number of records to generate")
    args = parser.parse_args()

    print(f"🚀 Seeding Google Photos Discovery Database with {args.count} cognitive retrieval scenarios...")
    db = Database()

    docs, extractions = generate_dataset(target_count=args.count)

    print(f"   📥 Inserting {len(docs)} multi-source documents into SQLite...")
    db.insert_raw_documents(docs)

    print(f"   🧠 Inserting {len(extractions)} cognitive retrieval extractions...")
    for ext in extractions:
        db.insert_extraction(ext)
        db.insert_tags(ext["extraction_id"], ext["tags"])

    print("   📊 Running Aggregator to compute pattern rollups...")
    aggregator = Aggregator()
    rollups = aggregator.aggregate(extractions)
    db.save_aggregated_patterns(rollups["retrieval_failures"])

    stats = db.get_overview_stats()
    top_failures = db.get_top_failure_points(limit=5)
    clues_stats = db.get_remembered_clues_stats()

    print("\n✅ Database Seeding Complete!")
    print(f"   • Total Documents:   {stats['total_documents']}")
    print(f"   • Total Extractions: {stats['total_extractions']}")
    print(f"   • Avg Confidence:    {stats['avg_confidence']}")
    print(f"   • Top Failure Modes: {[f['failure_tag'] for f in top_failures]}")
    print(f"   • Top Clues:         {list(clues_stats.keys())[:4]}")


if __name__ == "__main__":
    main()
