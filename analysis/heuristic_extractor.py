"""
Semantic Heuristic Extractor

Provides zero-cost, offline semantic extraction fallback when LLM API quota is exhausted
or offline. Uses regex patterns and semantic sentence-transformer matching to extract
structured insights aligned with the PM market research study requirements.
"""

import re
from typing import Any, Dict, List, Optional


class HeuristicExtractor:
    """Extracts structured wishlist insights using rule-based NLP and taxonomy matching."""

    # Keywords / patterns for uncertainty types
    UNCERTAINTY_PATTERNS = {
        "fit": [r"\bsize\b", r"\bfit\b", r"\bfitting\b", r"\btight\b", r"\bloose\b", r"\blength\b", r"\bmeasurement\b", r"\bsmall\b", r"\blarge\b", r"\bxxl\b", r"\bmedium\b"],
        "quality": [r"\bquality\b", r"\bfabric\b", r"\bmaterial\b", r"\bcheap\b", r"\bcolor fade\b", r"\bdefect\b", r"\btorn\b", r"\bduplicate\b", r"\bfake\b", r"\btransparent\b", r"\bstitching\b"],
        "price": [r"\bprice\b", r"\bexpensive\b", r"\bcostly\b", r"\bdiscount\b", r"\bcoupon\b", r"\boffer\b", r"\bplatform fee\b", r"\bconvenience fee\b", r"\bextra charge\b", r"\bsale\b", r"\bexpensive\b"],
        "availability": [r"\bout of stock\b", r"\bunavailable\b", r"\bsold out\b", r"\bno stock\b", r"\bstock\b", r"\brestock\b"],
        "trust": [r"\breturn\b", r"\brefund\b", r"\bcustomer care\b", r"\bcustomer support\b", r"\bfraud\b", r"\bscam\b", r"\bexchange\b", r"\bdelayed\b", r"\bdelivery\b", r"\bwrong item\b", r"\bused item\b"],
        "occasion": [r"\bwedding\b", r"\bfestive\b", r"\bdiwali\b", r"\bparty\b", r"\boffice\b", r"\bcasual\b", r"\bfunction\b", r"\bbirthday\b"],
        "durability": [r"\bdurable\b", r"\blasting\b", r"\bwashed\b", r"\bwash\b", r"\bshrink\b", r"\bfaded\b", r"\bwear and tear\b"],
        "styling": [r"\bstyle\b", r"\bstyling\b", r"\bmatching\b", r"\blook\b", r"\bappearance\b", r"\bphotos\b", r"\binfluencer\b", r"\boutfit\b"],
    }

    # Personas
    PERSONA_PATTERNS = {
        "budget_conscious": [r"\bprice\b", r"\bexpensive\b", r"\bdiscount\b", r"\bcoupon\b", r"\bworth\b", r"\bvalue for money\b", r"\bcheap\b", r"\bdeal\b", r"\bfee\b", r"\bcashback\b"],
        "occasion_shopper": [r"\bwedding\b", r"\bfestive\b", r"\bevent\b", r"\bparty\b", r"\bcelebration\b", r"\bdiwali\b", r"\beid\b", r"\bfunction\b"],
        "inspiration_browser": [r"\bwishlist\b", r"\bsave\b", r"\bsaved\b", r"\bbrowse\b", r"\bcollection\b", r"\blater\b", r"\blook\b", r"\binspiration\b", r"\bbookmark\b"],
        "brand_loyal": [r"\bbrand\b", r"\bquality\b", r"\boriginal\b", r"\bgenuine\b", r"\btrusted\b", r"\blevis\b", r"\bnike\b", r"\bpuma\b", r"\bzara\b", r"\bh&m\b"],
        "trend_follower": [r"\btrend\b", r"\btrendy\b", r"\blatest\b", r"\bfashion\b", r"\binfluencer\b", r"\bviral\b", r"\bnew arrival\b"],
    }

    # Wishlist Pain Points
    WISHLIST_PAIN_PATTERNS = [
        (r"(price\s+increase|price\s+hiked|price\s+went\s+up|costlier)", "price increased after adding to wishlist"),
        (r"(out\s+of\s+stock|sold\s+out|no\s+stock|item\s+unavailable)", "wishlisted item went out of stock"),
        (r"(disappear|removed|vanished|missing\s+from\s+wishlist)", "wishlist items randomly disappear or reset"),
        (r"(limit|cannot\s+add|wishlist\s+full|maximum\s+items)", "wishlist item limit reached"),
        (r"(hard\s+to\s+find|cannot\s+organize|no\s+folder|no\s+category)", "lack of wishlist organization and categorization"),
        (r"(no\s+notification|price\s+drop\s+alert|didn't\s+notify)", "lack of timely price drop and restock notifications"),
        (r"(bookmark|save\s+for\s+later|never\s+buy|just\s+looking)", "used as inspirational bookmarking rather than direct intent"),
    ]

    # Competitor Mentions
    COMPETITOR_PATTERNS = [
        (r"\bajio\b", "AJIO"),
        (r"\bamazon\b", "Amazon Fashion"),
        (r"\bflipkart\b", "Flipkart"),
        (r"\bnykaa\b", "Nykaa Fashion"),
        (r"\bmeesho\b", "Meesho"),
        (r"\bzara\b", "Zara"),
        (r"\bh&m\b", "H&M"),
    ]

    def extract(self, text: str) -> Dict[str, Any]:
        """Extract structured insights from text using heuristic & NLP matching."""
        lower_text = text.lower()

        # 1. Uncertainty Types
        uncertainties = []
        for utype, patterns in self.UNCERTAINTY_PATTERNS.items():
            for p in patterns:
                if re.search(p, lower_text):
                    uncertainties.append(utype)
                    break

        # 2. Shopper Persona
        detected_persona = "inspiration_browser"
        persona_scores = {}
        for persona, patterns in self.PERSONA_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, lower_text))
            if score > 0:
                persona_scores[persona] = score
        if persona_scores:
            detected_persona = max(persona_scores, key=persona_scores.get)

        # 3. Wishlist Pain Point
        wishlist_pain = None
        for pattern, pain_desc in self.WISHLIST_PAIN_PATTERNS:
            if re.search(pattern, lower_text):
                wishlist_pain = pain_desc
                break

        # 4. Price Behavior
        price_behavior = None
        if re.search(r"(price\s+increase|price\s+went\s+up|costlier|rate\s+increased)", lower_text):
            price_behavior = "price increased after wishlisting"
        elif re.search(r"(wait\s+for\s+sale|wait\s+for\s+discount|price\s+drop|discount\s+wait)", lower_text):
            price_behavior = "waiting for sale or price drop"
        elif re.search(r"(coupon\s+not\s+working|convenience\s+fee|platform\s+fee)", lower_text):
            price_behavior = "hidden fees or platform charges at checkout"

        # 5. Purchase Blocker
        blocker = None
        if "fit" in uncertainties and ("size" in lower_text or "chart" in lower_text):
            blocker = "Size uncertainty and inconsistent brand fit charts"
        elif "quality" in uncertainties and ("cheap" in lower_text or "fabric" in lower_text or "color" in lower_text):
            blocker = "Fabric quality doubt and fear product won't match photos"
        elif "trust" in uncertainties and ("return" in lower_text or "refund" in lower_text or "fee" in lower_text):
            blocker = "Return friction, non-refundable platform fee, or refund delays"
        elif wishlist_pain == "wishlisted item went out of stock":
            blocker = "Product frequently goes out of stock before purchase decision"
        elif price_behavior == "price increased after wishlisting":
            blocker = "Sudden price surge after saving item to wishlist"
        elif price_behavior == "waiting for sale or price drop":
            blocker = "Waiting for festive discount or upcoming price reduction"
        elif "availability" in uncertainties:
            blocker = "Preferred size or variant unavailable"
        elif len(uncertainties) > 0:
            blocker = f"Uncertainty regarding {', '.join(uncertainties)}"

        # 6. Feature Request
        feature_request = None
        if re.search(r"(size\s+recommend|body\s+type|fit\s+finder)", lower_text):
            feature_request = "Fit predictor / accurate size recommendation tool"
        elif re.search(r"(price\s+tracker|price\s+alert|notify\s+when\s+price\s+drops)", lower_text):
            feature_request = "Price drop alert and historical price tracker"
        elif re.search(r"(organize|folder|category|sub\s*wishlist|collection)", lower_text):
            feature_request = "Wishlist categorization and custom collection boards"
        elif re.search(r"(try\s*on|ar\s*view|real\s*photo|customer\s*photo)", lower_text):
            feature_request = "Customer video reviews and virtual try-on previews"

        # 7. Competitor Mention
        competitor_mention = None
        found_comps = []
        for pat, comp_name in self.COMPETITOR_PATTERNS:
            if re.search(pat, lower_text):
                found_comps.append(comp_name)
        if found_comps:
            competitor_mention = f"Compares experience with {', '.join(found_comps)}"

        # 8. Wishlist Motivation
        motivation = None
        if "occasion" in uncertainties or detected_persona == "occasion_shopper":
            motivation = "Planning and shortlisting for an upcoming occasion or event"
        elif detected_persona == "budget_conscious":
            motivation = "Tracking product prices and saving for discounts/deals"
        elif detected_persona == "inspiration_browser":
            motivation = "Saving visual inspiration and bookmarking styles for later"
        elif "fit" in uncertainties:
            motivation = "Shortlisting items while verifying measurements and sizing"
        else:
            motivation = "Saving appealing fashion products to compare before checkout"

        # 9. Evidence Type
        evidence_type = "direct_statement" if len(text) > 80 and (blocker or wishlist_pain) else "inference"

        return {
            "wishlist_motivation": motivation,
            "purchase_blocker": blocker,
            "uncertainty_type": uncertainties if uncertainties else ["quality"],
            "shopper_persona": detected_persona,
            "evidence_type": evidence_type,
            "wishlist_pain_point": wishlist_pain,
            "price_behavior": price_behavior,
            "feature_request": feature_request,
            "competitor_mention": competitor_mention,
        }
