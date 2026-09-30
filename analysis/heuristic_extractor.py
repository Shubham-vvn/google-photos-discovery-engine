"""
Cognitive Heuristic Extractor

Provides zero-cost, offline semantic extraction fallback when LLM API quota is exhausted
or offline. Uses regex patterns and taxonomy matching to extract structured insights
on cognitive photo retrieval struggles for Google Photos.
"""

import re
from typing import Any, Dict, List, Optional


class HeuristicExtractor:
    """Extracts structured cognitive retrieval insights using rule-based NLP and taxonomy matching."""

    # 1. Failure Points Patterns
    FAILURE_PATTERNS = [
        (r"(zero\s+results?|no\s+results?|nothing\s+shows?|can't\s+find\s+anything|empty\s+results?)", "zero_results"),
        (r"(too\s+many|thousands?\s+of\s+photos?|scroll\s+forever|hundreds\s+of\s+pictures|overwhelm|drowning)", "overwhelming_results"),
        (r"(doesn't\s+understand|wrong\s+results?|unrelated|literal|semantic|not\s+what\s+i\s+asked)", "semantic_misunderstanding"),
        (r"(receipt|text\s+in\s+photo|ocr|blurry|prescription|label|screenshot\s+text)", "ocr_text_mismatch"),
        (r"(last\s+year|months?\s+ago|date\s+wrong|years?\s+ago|timeline\s+lost|season|monsoon|winter)", "temporal_disconnect"),
        (r"(synonym|medicine|pills?|cafe|coffee|dress|different\s+word|keyword)", "synonym_blindness"),
        (r"(gave\s+up|scrolling\s+for\s+hours|abandon|tired\s+of\s+scrolling|impossible\s+to\s+find)", "scroll_fatigue_abandonment"),
        (r"(memes?|whatsapp|junk|clutter|duplicates?|flood)", "false_positive_clutter"),
    ]

    # 2. Remembered Clues
    CLUE_PATTERNS = {
        "visual_anchor": [r"\bwhite\b", r"\bblue\b", r"\bred\b", r"\bgreen\b", r"\bblack\b", r"\byellow\b", r"\bcolor\b", r"\bstrip\b", r"\bcar\b", r"\bdoor\b", r"\bshirt\b", r"\bdress\b"],
        "social_companion": [r"\bmom\b", r"\bdad\b", r"\bfriend\b", r"\bfriends\b", r"\bwife\b", r"\bhusband\b", r"\bkids?\b", r"\bbaby\b", r"\bfamily\b", r"\bwith\s+[a-z]+\b", r"\btogether\b"],
        "location_vibe": [r"\bbeach\b", r"\bcafe\b", r"\brestaurant\b", r"\bsea\b", r"\bhotel\b", r"\bairport\b", r"\bmountains?\b", r"\bgoa\b", r"\bpark\b", r"\boutdoor\b"],
        "emotional_context": [r"\bsick\b", r"\bfood\s+poisoning\b", r"\bbirthday\b", r"\bwedding\b", r"\bcelebration\b", r"\bfun\b", r"\bhospital\b", r"\bvacation\b", r"\btrip\b"],
        "temporal_approximation": [r"\blast\s+year\b", r"\blast\s+month\b", r"\bcouple\s+years\b", r"\baround\s+diwali\b", r"\bsummer\b", r"\bmonsoon\b", r"\bwinter\b", r"\bcollege\s+days\b"],
        "activity_context": [r"\bbreakfast\b", r"\bdinner\b", r"\bhiking\b", r"\bcooking\b", r"\bshopping\b", r"\bparty\b", r"\bdriving\b", r"\bmeeting\b"],
    }

    # 3. Forgotten Elements
    FORGOTTEN_PATTERNS = {
        "exact_date": [r"\bdon't\s+remember\s+(the\s+)?date\b", r"\bforgot\s+(which\s+)?day\b", r"\bexact\s+date\b", r"\bwhat\s+month\b"],
        "gps_geotag": [r"\bdon't\s+remember\s+(where|the\s+city|location)\b", r"\bno\s+geotag\b", r"\bunknown\s+place\b"],
        "album_folder_name": [r"\bwhich\s+album\b", r"\bnot\s+in\s+album\b", r"\bunorganized\b", r"\bforgot\s+folder\b"],
        "exact_text_content": [r"\bdon't\s+remember\s+the\s+exact\s+name\b", r"\bexact\s+spelling\b", r"\bmedicine\s+name\b"],
        "camera_device_metadata": [r"\bold\s+phone\b", r"\bbackup\b", r"\btransferred\b", r"\bwhatsapp\b", r"\bdownloaded\b"],
    }

    # 4. Photo Categories
    CATEGORY_PATTERNS = {
        "episodic_life_event": [r"\btrip\b", r"\bgoa\b", r"\bvacation\b", r"\bcafe\b", r"\bdinner\b", r"\bwedding\b", r"\bholiday\b", r"\btravel\b"],
        "visual_utility_document": [r"\breceipt\b", r"\bmedicine\b", r"\bpills?\b", r"\bprescription\b", r"\bdrug\b", r"\bbill\b", r"\bdocument\b", r"\bserial\b", r"\bcontract\b", r"\bwarranty\b"],
        "screenshot_saved_media": [r"\bscreenshot\b", r"\btwitter\b", r"\binstagram\b", r"\bbook\b", r"\brecipe\b", r"\bquote\b", r"\barticle\b"],
        "people_and_portraits": [r"\bselfie\b", r"\bportrait\b", r"\bkid\b", r"\bchild\b", r"\bgrandma\b", r"\bdad\b", r"\bmom\b", r"\bfather\b", r"\bmother\b"],
        "aesthetic_and_inspiration": [r"\bsunset\b", r"\barchitecture\b", r"\bdecor\b", r"\boutfit\b", r"\bwallpaper\b", r"\bdesign\b"],
    }

    # 5. User Personas
    PERSONA_PATTERNS = {
        "life_documenter": [r"\bthousand", r"\bphotos\b", r"\btimeline\b", r"\beveryday\b", r"\bevery\s+trip\b", r"\bhuge\s+library\b"],
        "visual_note_taker": [r"\breceipt\b", r"\bmedicine\b", r"\bnote\b", r"\bwhiteboard\b", r"\bdocument\b", r"\bbill\b", r"\bpill\b"],
        "nostalgia_seeker": [r"\byears\s+ago\b", r"\bold\s+memory\b", r"\bchildhood\b", r"\bcollege\b", r"\bremember\s+when\b", r"\breminisce\b"],
        "screenshot_curator": [r"\bscreenshot\b", r"\bsaved\s+image\b", r"\btwitter\b", r"\binstagram\b", r"\bweb\b"],
        "family_archivist": [r"\bchildren\b", r"\bkids?\b", r"\bfamily\b", r"\bgrowing\s+up\b", r"\bparents\b", r"\balbum\b"],
    }

    def extract(self, text: str) -> Dict[str, Any]:
        """Extract structured insights from text using cognitive NLP matching."""
        lower_text = text.lower()

        # 1. Failure Point
        failure_point = "zero_results"
        for pattern, fp in self.FAILURE_PATTERNS:
            if re.search(pattern, lower_text):
                failure_point = fp
                break

        # 2. Remembered Clues
        remembered_clues = []
        for clue, patterns in self.CLUE_PATTERNS.items():
            for p in patterns:
                if re.search(p, lower_text):
                    remembered_clues.append(clue)
                    break
        if not remembered_clues:
            remembered_clues = ["visual_anchor", "location_vibe"]

        # 3. Forgotten Elements
        forgotten_elements = []
        for fe, patterns in self.FORGOTTEN_PATTERNS.items():
            for p in patterns:
                if re.search(p, lower_text):
                    forgotten_elements.append(fe)
                    break
        if not forgotten_elements:
            forgotten_elements = ["exact_date", "gps_geotag"]

        # 4. Photo Category
        detected_category = "episodic_life_event"
        category_scores = {}
        for cat, patterns in self.CATEGORY_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, lower_text))
            if score > 0:
                category_scores[cat] = score
        if category_scores:
            detected_category = max(category_scores, key=category_scores.get)

        # 5. User Persona
        detected_persona = "life_documenter"
        persona_scores = {}
        for persona, patterns in self.PERSONA_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, lower_text))
            if score > 0:
                persona_scores[persona] = score
        if persona_scores:
            detected_persona = max(persona_scores, key=persona_scores.get)

        # 6. Search Query / Behavior
        search_behavior = "keyword_stacking"
        if len(text.split()) > 25:
            search_behavior = "natural_language_story"
        elif "scroll" in lower_text:
            search_behavior = "immediate_scroll_fallback"
        elif "synonym" in lower_text or "tried" in lower_text:
            search_behavior = "synonym_churning"

        # 7. Feature Request
        feature_request = None
        if re.search(r"(ask\s+photos|conversational|ai\s+search|chat|talk)", lower_text):
            feature_request = "Conversational multi-turn retrieval (Ask Photos)"
        elif re.search(r"(filter|color|season|vibe|companion)", lower_text):
            feature_request = "Associative filters for mood, companion, and weather"
        elif re.search(r"(ocr|read\s+text|handwriting)", lower_text):
            feature_request = "Enhanced OCR indexing for receipts and handwritten notes"
        elif re.search(r"(date\s+range|slider|approximate)", lower_text):
            feature_request = "Fuzzy relative time range search"

        # Target description
        target_description = f"Seeking vaguely remembered {detected_category.replace('_', ' ')}"
        if "medicine" in lower_text or "pill" in lower_text:
            target_description = "Medicine or pharmacy tablet strip taken while unwell"
        elif "cafe" in lower_text or "goa" in lower_text:
            target_description = "Small cafe breakfast during holiday/vacation trip"
        elif "receipt" in lower_text or "bill" in lower_text:
            target_description = "Store receipt or utility document for proof/warranty"
        elif "screenshot" in lower_text:
            target_description = "Screenshot of saved book recommendation or article"

        evidence_type = "direct_statement" if len(text) > 80 else "inference"

        return {
            "photo_category": detected_category,
            "target_photo_description": target_description,
            "remembered_clues": remembered_clues,
            "remembered_details": f"Recalls contextual clues: {', '.join(remembered_clues)}",
            "forgotten_elements": forgotten_elements,
            "search_query_attempted": "vague keyword attempt",
            "search_behavior": search_behavior,
            "retrieval_failure_point": failure_point,
            "user_frustration_detail": f"Retrieval failed due to {failure_point.replace('_', ' ')}",
            "user_persona": detected_persona,
            "evidence_type": evidence_type,
            "feature_request": feature_request,
        }
