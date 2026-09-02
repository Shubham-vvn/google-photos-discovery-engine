import os
import shutil
from PIL import Image, ImageDraw, ImageFont

W, H = 1376, 768
BG_COLOR = (17, 18, 21)       # #111215
CARD_BG = (26, 28, 34)        # #1a1c22
CARD_BORDER = (44, 47, 56)    # #2c2f38
TEXT_WHITE = (245, 245, 247)
TEXT_MUTED = (160, 165, 175)
TEXT_YELLOW = (245, 166, 35)  # #f5a623
TEXT_PINK = (255, 63, 108)    # Myntra pink #ff3f6c
TEXT_CYAN = (38, 198, 218)    # #26c6da
ACCENT_GREEN = (76, 175, 80)
ACCENT_ORANGE = (255, 152, 0)
ACCENT_RED = (239, 83, 80)

# Load fonts
def get_font(size, bold=False):
    try:
        if bold:
            return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', size)
        else:
            return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', size)
    except:
        return ImageFont.load_default()

def draw_header(draw, part_text, title_text, subtitle_text, slide_num):
    # Brand logo & Part
    draw.text((50, 35), "myntra", font=get_font(22, bold=True), fill=TEXT_PINK)
    draw.text((140, 37), part_text, font=get_font(15, bold=True), fill=TEXT_YELLOW)
    draw.text((1220, 35), "nextleap", font=get_font(18, bold=True), fill=TEXT_WHITE)
    
    # Title & Subtitle
    draw.text((50, 72), title_text, font=get_font(24, bold=True), fill=TEXT_WHITE)
    draw.text((50, 115), subtitle_text, font=get_font(15, bold=False), fill=TEXT_MUTED)
    
    # Slide number
    draw.ellipse((1315, 715, 1345, 745), fill=CARD_BG, outline=CARD_BORDER)
    draw.text((1324, 722), str(slide_num), font=get_font(14, bold=True), fill=TEXT_WHITE)

def draw_footer(draw, text):
    draw.text((50, 725), text, font=get_font(12, bold=False), fill=TEXT_MUTED)

# ----------------- SLIDE 1: Growth Strategy & Overview -----------------
def generate_slide_1():
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    draw_header(draw, 
                "GROWTH STRATEGY · OVERVIEW", 
                "Myntra leads India's fashion e-commerce — but wishlist-to-purchase conversion is its next hard problem", 
                "175M+ users, Rs. 800+ AOV, dominant market share — growth now hinges on converting wishlist hoarders into confident buyers.", 
                1)
    
    # 4 Metric Cards Top
    top_metrics = [
        ("175M+", "Monthly active users +32% YoY"),
        ("Rs. 30,000+ Cr", "Annual GMV +28% YoY"),
        ("Rs. 800+", "Average order value"),
        ("5,996", "Reviews analyzed this project")
    ]
    
    mx = 50
    for val, sub in top_metrics:
        draw.rounded_rectangle((mx, 155, mx+295, 235), radius=8, fill=CARD_BG, outline=CARD_BORDER)
        draw.text((mx+20, 168), val, font=get_font(22, bold=True), fill=TEXT_WHITE)
        draw.text((mx+20, 202), sub, font=get_font(12, bold=False), fill=ACCENT_GREEN if "+" in sub else TEXT_MUTED)
        mx += 320

    # Middle Left: Competitive Landscape (2026) Table
    draw.rounded_rectangle((50, 255, 660, 595), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((70, 275), "COMPETITIVE LANDSCAPE (2026)", font=get_font(14, bold=True), fill=TEXT_YELLOW)
    
    headers = ["Player", "Share", "Positioning"]
    draw.text((70, 310), headers[0], font=get_font(12, bold=True), fill=TEXT_CYAN)
    draw.text((220, 310), headers[1], font=get_font(12, bold=True), fill=TEXT_CYAN)
    draw.text((340, 310), headers[2], font=get_font(12, bold=True), fill=TEXT_CYAN)
    draw.line((70, 332, 640, 332), fill=CARD_BORDER, width=1)
    
    players = [
        ("Myntra", "~35%", "Fashion category leader"),
        ("Ajio", "~18%", "Reliance-backed challenger"),
        ("Flipkart Fashion", "~15%", "Marketplace crossover"),
        ("Amazon Fashion", "~12%", "Selection depth play"),
        ("Meesho", "~10%", "Value segment disruptor")
    ]
    
    py = 345
    for p_name, p_share, p_pos in players:
        is_myntra = p_name == "Myntra"
        if is_myntra:
            draw.rectangle((65, py-4, 645, py+24), fill=(35, 42, 50))
        draw.text((70, py), p_name, font=get_font(12, bold=is_myntra), fill=TEXT_YELLOW if is_myntra else TEXT_WHITE)
        draw.text((220, py), p_share, font=get_font(12, bold=False), fill=ACCENT_GREEN if is_myntra else TEXT_MUTED)
        draw.text((340, py), p_pos, font=get_font(12, bold=False), fill=TEXT_WHITE if is_myntra else TEXT_MUTED)
        py += 36

    # Middle Right Top: Project Metrics (Blockers & Confidence)
    draw.rounded_rectangle((685, 255, 990, 345), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((705, 268), "13", font=get_font(24, bold=True), fill=TEXT_WHITE)
    draw.text((705, 305), "Unique purchase blockers discovered", font=get_font(11, bold=False), fill=TEXT_MUTED)
    
    draw.rounded_rectangle((1020, 255, 1325, 345), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((1040, 268), "81.8%", font=get_font(24, bold=True), fill=TEXT_WHITE)
    draw.text((1040, 305), "AI classification confidence", font=get_font(11, bold=False), fill=TEXT_MUTED)

    # Middle Right Bottom: Supporting Evidence
    draw.rounded_rectangle((685, 360, 1325, 595), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((705, 380), "SUPPORTING EVIDENCE -- THE CORE LEVER", font=get_font(13, bold=True), fill=TEXT_YELLOW)
    
    draw.text((705, 420), "\"We see wishlists as a funnel, not a dead end -- the gap", font=get_font(13, bold=False), fill=TEXT_WHITE)
    draw.text((705, 444), "between save and buy is an information problem, not a", font=get_font(13, bold=False), fill=TEXT_WHITE)
    draw.text((705, 468), "pricing problem.\"", font=get_font(13, bold=False), fill=TEXT_WHITE)
    
    draw.text((705, 510), "Wishlist conversion rate industry-wide remains below 20% --", font=get_font(12, bold=False), fill=TEXT_MUTED)
    draw.text((705, 532), "primarily driven by fit, trust, and return policy friction.", font=get_font(12, bold=False), fill=TEXT_MUTED)

    # Bottom Banner: Growth Team's KPI (14 Days)
    draw.rounded_rectangle((50, 610, 1325, 695), radius=8, fill=(28, 32, 42), outline=TEXT_YELLOW)
    draw.text((70, 626), "GROWTH TEAM'S KPI: % of wishlist items converting to purchase within 14 days", font=get_font(14, bold=True), fill=TEXT_YELLOW)
    draw.text((70, 655), "-- Driven by information confidence, not discounts", font=get_font(12, bold=False), fill=TEXT_WHITE)

    draw_footer(draw, "Sources: Myntra App Reviews · Google Play Store · Apple App Store · Reddit · Primary Research · nextleap Analysis")
    return img
def generate_slide_6():
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    draw_header(draw, 
                "PART 3 · ROOT CAUSE", 
                "Root cause: Fast cataloguing created a choice paralysis loop — no pre-purchase bridge exists", 
                "A 5-Why ladder reveals structural friction: browse-heavy UX induces wishlist hoarding instead of buying.", 
                6)
    
    # Left Card: 5-Why Chain
    draw.rounded_rectangle((50, 155, 660, 695), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((70, 175), "THE 5-WHY CHAIN (ROOT CAUSE LADDER)", font=get_font(14, bold=True), fill=TEXT_YELLOW)
    
    whys = [
        ("SURFACE", "Shoppers add 10-20 items to wishlist and let them sit for 30+ days without purchasing."),
        ("WHY?", "They hesitate at cart move -- 63.8% abandon due to fit anxiety and trust deficit."),
        ("WHY?", "Brand size charts vary widely (Roadster L vs Mango S), and fabric feel cannot be verified."),
        ("WHY?", "Myntra platform fees and return friction turn home-trial sizing into a financial risk."),
        ("ROOT CAUSE", "The app is engineered for speed of browsing, not pre-purchase certainty. No 'safe-fit trial' mechanism exists; wishlisting becomes a risk-free holding pen.")
    ]
    
    y = 210
    for label, desc in whys:
        color = ACCENT_RED if label == "ROOT CAUSE" else (TEXT_CYAN if label == "SURFACE" else TEXT_YELLOW)
        draw.rounded_rectangle((70, y, 160, y+24), radius=4, fill=(40, 42, 50))
        draw.text((76, y+4), label, font=get_font(11, bold=True), fill=color)
        
        # Word wrap desc
        lines = []
        words = desc.split()
        curr = ""
        for w in words:
            if len(curr + " " + w) < 54:
                curr += (" " + w if curr else w)
            else:
                lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)
        
        for li, l in enumerate(lines):
            draw.text((175, y + li*18), l, font=get_font(13, bold=(label == "ROOT CAUSE")), fill=TEXT_WHITE if label == "ROOT CAUSE" else TEXT_MUTED)
        
        y += 90

    # Right Top Card: Self Reinforcing Loop
    draw.rounded_rectangle((685, 155, 1325, 435), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((705, 175), "THE SELF-REINFORCING WISHLIST GRAVEYARD LOOP", font=get_font(14, bold=True), fill=TEXT_YELLOW)
    
    steps = [
        ("1. User Browses & Wishlists", "Saves 10-15 attractive items based on photo aesthetics & price signals."),
        ("2. Sizing / Fabric Hesitation", "Unsure of real-life drape, fabric thickness, or true fit across unfamiliar brand."),
        ("3. Indefinite Stagnation", "Item sits in wishlist; fear of non-refundable return fees prevents cart commit."),
        ("4. Stockout or Interest Decay", "Item goes out of stock or trend fades -> Disillusioned user restarts cycle.")
    ]
    
    sy = 210
    for stitle, sdesc in steps:
        draw.text((705, sy), stitle, font=get_font(13, bold=True), fill=TEXT_CYAN)
        draw.text((705, sy+18), sdesc, font=get_font(12, bold=False), fill=TEXT_MUTED)
        sy += 50
    
    draw.text((705, sy+10), "Every abandoned item deepens hesitation and turns the wishlist into a dead catalogue holding zone.", font=get_font(11, bold=False), fill=ACCENT_ORANGE)

    # Right Bottom Card: Redefined Problem Statement
    draw.rounded_rectangle((685, 450, 1325, 695), radius=8, fill=CARD_BG, outline=TEXT_YELLOW)
    draw.text((705, 470), "REDEFINED PRODUCT PROBLEM STATEMENT", font=get_font(14, bold=True), fill=TEXT_YELLOW)
    
    draw.text((705, 505), "When an inspiration browser shortlists items from an unfamiliar brand,", font=get_font(14, bold=True), fill=TEXT_WHITE)
    draw.text((705, 530), "the platform offers no deterministic sizing or fabric assurance mechanism.", font=get_font(14, bold=True), fill=TEXT_WHITE)
    draw.text((705, 565), "Because return penalties create real financial friction, users treat the wishlist as", font=get_font(13, bold=False), fill=TEXT_MUTED)
    draw.text((705, 588), "an indefinite holding pen rather than an active pre-purchase evaluation funnel.", font=get_font(13, bold=False), fill=TEXT_MUTED)
    draw.text((705, 620), "The opportunity: Build a non-monetary 'Confidence Bridge' that resolves sizing & fabric doubts", font=get_font(13, bold=True), fill=TEXT_CYAN)
    draw.text((705, 642), "directly within the wishlist before the user abandons the item.", font=get_font(13, bold=True), fill=TEXT_CYAN)

    draw_footer(draw, "Supporting Evidence: 5-Why Root Cause Analysis · 5,996 Corpus Reviews · Persona Cross-Tabs · Research Appendix")
    return img

# ----------------- SLIDE 7: Prioritization & RICE Scoring -----------------
def generate_slide_7():
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    draw_header(draw, 
                "PART 3 · PRIORITIZATION", 
                "We evaluated 4 non-monetary wedges via RICE — Pre-Purchase Confidence Bridge wins", 
                "Strict adherence to non-monetary constraint: Solving fit uncertainty & return anxiety beats mood boards & social features.", 
                7)
    
    # Table Card
    draw.rounded_rectangle((50, 155, 1325, 390), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((70, 175), "RICE SCORING MATRIX — NON-MONETARY INTERVENTION WEDGES", font=get_font(14, bold=True), fill=TEXT_YELLOW)
    
    headers = ["Wedge / Solution Idea", "Target Reach (MAU)", "Conversion Impact", "Confidence", "Effort", "RICE Score"]
    x_offsets = [70, 480, 710, 890, 1040, 1180]
    
    for i, h in enumerate(headers):
        draw.text((x_offsets[i], 205), h, font=get_font(12, bold=True), fill=TEXT_CYAN)
    
    draw.line((70, 228, 1305, 228), fill=CARD_BORDER, width=1)
    
    rows = [
        ("A. Pre-Purchase Confidence Card (Fit + Fabric DNA + Swap Guarantee)", "110M (All Browsers)", "4.5% - 6.0%", "85%", "Medium", "14.8 [Winner]"),
        ("B. Wardrobe Occasion & Compatibility Matcher", "35M (Occasion Shoppers)", "2.5% - 3.5%", "60%", "High", "6.2"),
        ("C. Wishlist Stagnation Nudge (Non-discount stock urgency)", "50M (Hoarders)", "1.5% - 2.5%", "70%", "Low", "5.8"),
        ("D. Social Peer Review & Collaborative Wishlists", "20M (Gen-Z Browsers)", "1.0% - 2.0%", "45%", "High", "2.1")
    ]
    
    ry = 240
    for r in rows:
        is_winner = "[Winner]" in r[5]
        bg_bar = (35, 42, 50) if is_winner else CARD_BG
        draw.rectangle((65, ry-4, 1310, ry+26), fill=bg_bar)
        
        draw.text((x_offsets[0], ry), r[0], font=get_font(12, bold=is_winner), fill=TEXT_YELLOW if is_winner else TEXT_WHITE)
        draw.text((x_offsets[1], ry), r[1], font=get_font(12, bold=False), fill=TEXT_MUTED)
        draw.text((x_offsets[2], ry), r[2], font=get_font(12, bold=False), fill=ACCENT_GREEN if is_winner else TEXT_MUTED)
        draw.text((x_offsets[3], ry), r[3], font=get_font(12, bold=False), fill=TEXT_MUTED)
        draw.text((x_offsets[4], ry), r[4], font=get_font(12, bold=False), fill=TEXT_MUTED)
        draw.text((x_offsets[5], ry), r[5], font=get_font(13, bold=True), fill=TEXT_YELLOW if is_winner else TEXT_MUTED)
        ry += 34

    # Bottom Left: Why A Wins
    draw.rounded_rectangle((50, 410, 660, 695), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((70, 430), "WHY WEDGE A WINS — THE AIRTIGHT DATA LADDER", font=get_font(13, bold=True), fill=TEXT_YELLOW)
    
    reasons = [
        ("1. Corpus Evidence (5,996)", "818 return policy reviews + 708 trust deficit + 611 quality doubts."),
        ("2. Persona Alignment", "Directly targets Inspiration Browsers (63.8%) and Brand Loyals (19.5%)."),
        ("3. High Stated Preference", "Standardized sizing (3.39/5) & Fabric transparency (3.18/5) ranked highest."),
        ("4. Root Cause Solved", "Eliminates sizing guesswork without touching price or margins.")
    ]
    
    ay = 460
    for r_title, r_desc in reasons:
        draw.text((70, ay), r_title, font=get_font(12, bold=True), fill=TEXT_CYAN)
        draw.text((70, ay+16), r_desc, font=get_font(11, bold=False), fill=TEXT_MUTED)
        ay += 46

    # Bottom Right: Non-Goals
    draw.rounded_rectangle((685, 410, 1325, 695), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((705, 430), "WHAT WE ARE NOT DOING (EXPLICIT NON-GOALS)", font=get_font(13, bold=True), fill=TEXT_YELLOW)
    
    nongoals = [
        ("[X] No Monetary Incentives", "Zero discounts, coupon drops, or price cuts (strict business constraint)."),
        ("[X] Not a Social Network", "No friend feeds or peer chats that add clutter to high-intent shopping."),
        ("[X] Not Generic Recommendations", "Focus is converting existing saved items, not pushing more random discovery."),
        ("[X] No Dark Patterns", "No artificial countdown timers or fake scarcity counters.")
    ]
    
    ny = 460
    for ng_title, ng_desc in nongoals:
        draw.text((705, ny), ng_title, font=get_font(12, bold=True), fill=ACCENT_RED if "[X]" in ng_title else TEXT_WHITE)
        draw.text((705, ny+16), ng_desc, font=get_font(11, bold=False), fill=TEXT_MUTED)
        ny += 46

    draw_footer(draw, "Decision Support: RICE Scoring Matrix · Corpus Grounded Tag Distribution · Research Appendix")
    return img

# ----------------- SLIDE 8: MVP Solution Walkthrough -----------------
def generate_slide_8():
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    draw_header(draw, 
                "PART 4 · MVP SOLUTION WALKTHROUGH", 
                "Confidence Bridge: One card, deterministic sizing consensus & zero-fee swap assurance", 
                "Follow Priya (24, Bangalore, 18 wishlisted items) through a confidence-first conversion flow.", 
                8)
    
    # 3 Stage Cards (Left 60% of screen)
    stages = [
        ("STAGE 1 · WISHLIST CARD", "Dynamic Fit & Fabric Badge", 
         "Priya browses her wishlist. Instead of just a price tag, the card highlights:\n- 'True to Size (88% fit match)'\n- '100% Breathable Cotton (4.6/5)'\n- 'Zero-Fee Size Swap Guaranteed'",
         "Feels: Reassured & curious"),
        
        ("STAGE 2 · ASSURANCE MODAL", "Interactive Confidence Bridge", 
         "Tapping the badge opens 1-screen modal:\n- Customer body-type distribution\n- Verified fabric close-up macro shots\n- Instant size recommendation (Size M for 36 bust)",
         "Feels: High certainty, no doubt"),
        
        ("STAGE 3 · FRICTIONLESS BAG MOVE", "Zero-Risk Trial Lock", 
         "Priya taps 'Move to Bag with Swap Guarantee'.\n- Size M reserved with free doorstep size swap if fit differs.\n- Moves directly to checkout without fee anxiety.",
         "Feels: Confident buyer, zero risk")
    ]
    
    sx = 50
    for snum, (stitle, ssub, sbody, sfeel) in enumerate(stages):
        draw.rounded_rectangle((sx, 155, sx+270, 570), radius=8, fill=CARD_BG, outline=CARD_BORDER)
        draw.rounded_rectangle((sx+10, 165, sx+260, 195), radius=4, fill=(35, 38, 48))
        draw.text((sx+20, 172), stitle, font=get_font(10, bold=True), fill=TEXT_YELLOW)
        
        draw.text((sx+15, 210), ssub, font=get_font(13, bold=True), fill=TEXT_CYAN)
        
        lines = sbody.split('\n')
        by = 245
        for l in lines:
            draw.text((sx+15, by), l, font=get_font(11, bold=False), fill=TEXT_WHITE)
            by += 22
        
        # Phone mockup box inside stage
        draw.rounded_rectangle((sx+20, 390, sx+250, 510), radius=6, fill=(18, 20, 25), outline=CARD_BORDER)
        draw.text((sx+30, 405), ">> Myntra Wishlist UI", font=get_font(10, bold=True), fill=TEXT_PINK)
        draw.text((sx+30, 430), "- Fit: 88% Match", font=get_font(10, bold=False), fill=ACCENT_GREEN)
        draw.text((sx+30, 450), "- Fabric: Pure Cotton", font=get_font(10, bold=False), fill=TEXT_CYAN)
        draw.text((sx+30, 475), "[ Move to Bag (Free Swap) ]", font=get_font(9, bold=True), fill=TEXT_YELLOW)
        
        draw.text((sx+15, 535), sfeel, font=get_font(11, bold=True), fill=ACCENT_GREEN)
        sx += 290

    # Right Column: Why it solves + AI necessity + Moat
    draw.rounded_rectangle((940, 155, 1325, 695), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    
    draw.text((960, 175), "WHY IT SOLVES THE PROBLEM", font=get_font(13, bold=True), fill=TEXT_YELLOW)
    draw.text((960, 198), "- Removes Sizing Anxiety: Replaces generic charts with crowd consensus.", font=get_font(11, bold=False), fill=TEXT_WHITE)
    draw.text((960, 222), "- De-risks Returns: Guaranteed free size swap overcomes fee hesitation.", font=get_font(11, bold=False), fill=TEXT_WHITE)
    draw.text((960, 246), "- Fast Conversion: Resolves doubt at the exact point of decision.", font=get_font(11, bold=False), fill=TEXT_WHITE)
    
    draw.text((960, 290), "WHY AI IS ESSENTIAL", font=get_font(13, bold=True), fill=TEXT_YELLOW)
    draw.text((960, 313), "- NLP extracts real fit sentiment from thousands of unstructured reviews.", font=get_font(11, bold=False), fill=TEXT_WHITE)
    draw.text((960, 337), "- Gemini Flash classifies fabric transparency & drape from verified photos.", font=get_font(11, bold=False), fill=TEXT_WHITE)
    draw.text((960, 361), "- Dynamic copy generation produces context-aware reassurance lines.", font=get_font(11, bold=False), fill=TEXT_WHITE)
    
    draw.text((960, 405), "COMPETITIVE MOAT & DEFENSIBILITY", font=get_font(13, bold=True), fill=TEXT_YELLOW)
    draw.text((960, 428), "- Data Network Effect: Every verified review & fit swap improves accuracy.", font=get_font(11, bold=False), fill=TEXT_WHITE)
    draw.text((960, 452), "- Zero Discounting Margin Protection: Lifts GMV without promotional spend.", font=get_font(11, bold=False), fill=TEXT_WHITE)
    draw.text((960, 476), "- Defensible against Ajio/Meesho which rely heavily on deep price cuts.", font=get_font(11, bold=False), fill=TEXT_WHITE)

    draw.rounded_rectangle((50, 595, 910, 695), radius=8, fill=(24, 28, 38), outline=TEXT_CYAN)
    draw.text((70, 615), "THE CORE CONVERSION LEVER", font=get_font(13, bold=True), fill=TEXT_CYAN)
    draw.text((70, 640), "By eliminating the #1 and #2 causes of hesitation (Return Friction 818 & Fit Doubt 185) directly inside", font=get_font(12, bold=False), fill=TEXT_WHITE)
    draw.text((70, 662), "the Wishlist interface, we transform passive visual bookmarks into high-velocity checkout orders.", font=get_font(12, bold=False), fill=TEXT_WHITE)

    draw_footer(draw, "MVP Solution Architecture · User Experience Flow · Behavioral Psychology · Research Appendix")
    return img

# ----------------- SLIDE 9: Technical Pipeline Rules vs AI -----------------
def generate_slide_9():
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    draw_header(draw, 
                "PART 4 · SYSTEM ARCHITECTURE", 
                "Rules enforce policy and inventory. AI predicts fit and synthesizes customer proof", 
                "A 5-stage real-time inference pipeline mapped to system actors with strict latency budgets.", 
                9)
    
    # 5-Stage Pipeline Cards
    p_stages = [
        ("RULES", "1. Signal Ingestion", "Cart & wishlist state, 30-day browse history, user measurements.", "Context Engine"),
        ("RULES", "2. Hesitation Filter", "Wishlist dwell > 7 days OR item price > Rs. 1,200 from untried brand.", "Rules Engine"),
        ("AI / ML", "3. Fit Consensus", "Extracts sizing sentiment & body match from review corpus.", "Gemini / MiniLM"),
        ("RULES", "4. Policy & Stock", "Verifies size swap inventory & doorstep exchange eligibility.", "Inventory Service"),
        ("AI / ML", "5. Assurance Copy", "Composes <=20-word personalized confidence line live.", "LLM Reasoning")
    ]
    
    px = 50
    for tag, title, desc, actor in p_stages:
        is_ai = "AI" in tag
        draw.rounded_rectangle((px, 155, px+240, 425), radius=8, fill=CARD_BG, outline=TEXT_YELLOW if is_ai else CARD_BORDER)
        
        # Tag badge
        draw.rounded_rectangle((px+10, 165, px+80, 188), radius=4, fill=(40, 42, 50))
        draw.text((px+16, 169), tag, font=get_font(10, bold=True), fill=TEXT_PINK if is_ai else TEXT_CYAN)
        
        draw.text((px+10, 202), title, font=get_font(13, bold=True), fill=TEXT_WHITE)
        
        # Desc lines
        words = desc.split()
        lines = []
        curr = ""
        for w in words:
            if len(curr + " " + w) < 26:
                curr += (" " + w if curr else w)
            else:
                lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)
            
        dy = 230
        for l in lines:
            draw.text((px+10, dy), l, font=get_font(11, bold=False), fill=TEXT_MUTED)
            dy += 18
            
        # Actor at bottom
        draw.rounded_rectangle((px+10, 380, px+230, 410), radius=4, fill=(18, 20, 25))
        draw.text((px+20, 388), f"Actor: {actor}", font=get_font(10, bold=True), fill=TEXT_YELLOW if is_ai else TEXT_CYAN)
        
        px += 258

    # Bottom 4 Feature Cards (Moat & Compounding)
    features = [
        ("DATA MOAT", "Captures proprietary fit-to-body measurements and post-purchase swap outcomes unavailable to general search."),
        ("COMPOUNDING FLYWHEEL", "More conversions -> richer fit consensus -> higher model precision -> lower return rate."),
        ("ZERO LATENCY OVERHEAD", "Deterministic rules pre-filter candidates; LLM generates async copy in <120ms with Redis cache."),
        ("ECOSYSTEM INTEGRATION", "Seamlessly hooks into Myntra's existing Logistics, Order Management, and Review pipelines.")
    ]
    
    fx = 50
    for ftitle, fdesc in features:
        draw.rounded_rectangle((fx, 455, fx+305, 685), radius=8, fill=CARD_BG, outline=CARD_BORDER)
        draw.text((fx+15, 475), ftitle, font=get_font(12, bold=True), fill=TEXT_YELLOW)
        
        words = fdesc.split()
        lines = []
        curr = ""
        for w in words:
            if len(curr + " " + w) < 32:
                curr += (" " + w if curr else w)
            else:
                lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)
            
        fy = 510
        for l in lines:
            draw.text((fx+15, fy), l, font=get_font(11, bold=False), fill=TEXT_MUTED)
            fy += 20
        
        fx += 325

    draw_footer(draw, "Engineering Architecture · Real-time Inference Pipeline · SLA <120ms · Research Appendix")
    return img

# ----------------- SLIDE 10: Metrics, KPI Tree & Rollout -----------------
def generate_slide_10():
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    draw_header(draw, 
                "PART 5 · SUCCESS METRICS & ROLLOUT", 
                "North Star: 30-Day Wishlist Conversion %. Guardrails protect return rates & margins", 
                "A hierarchical KPI tree driving non-monetary conversion, supported by a 3-phase gated rollout.", 
                10)
    
    # North Star Box
    draw.rounded_rectangle((50, 155, 1325, 235), radius=8, fill=(28, 32, 42), outline=TEXT_YELLOW)
    draw.text((70, 168), "NORTH STAR METRIC · 30-Day Wishlist-to-Purchase Conversion Rate", font=get_font(14, bold=True), fill=TEXT_YELLOW)
    draw.text((70, 195), "Baseline: ~16%  -->  Target: 20.0% - 21.0% (+3.5 to +5.0 pp increase across 175M MAU)", font=get_font(13, bold=True), fill=TEXT_WHITE)
    draw.text((70, 215), "Primary Driver: Converting dormant wishlist items through fit & fabric assurance without price discounts.", font=get_font(11, bold=False), fill=TEXT_MUTED)

    # 3 Metric Branches
    branches = [
        ("INPUT METRICS", [
            ("Assurance Card Impression Rate", "> 85% of active wishlists"),
            ("Modal Open / Dwell Time", "> 18s avg engagement"),
            ("Fit Consensus View Rate", "> 45% tap-through rate")
        ], TEXT_CYAN),
        
        ("OUTPUT METRICS", [
            ("Wishlist-to-Cart Move Rate", "+22% vs Control"),
            ("Cart-to-Checkout Completion", "+15% lift in 14 days"),
            ("Organic Repeat Purchase Rate", "+12% 60-day cohort")
        ], ACCENT_GREEN),
        
        ("GUARDRAIL METRICS", [
            ("Sizing Return Rate Breach", "Must drop by >=15%"),
            ("Checkout Latency Overhead", "Must stay < 120ms"),
            ("Order Net AOV", "Zero drop (no margin dilution)")
        ], ACCENT_RED)
    ]
    
    bx = 50
    for btitle, metrics, bcolor in branches:
        draw.rounded_rectangle((bx, 255, bx+405, 465), radius=8, fill=CARD_BG, outline=CARD_BORDER)
        draw.text((bx+20, 275), btitle, font=get_font(13, bold=True), fill=bcolor)
        
        my = 310
        for mname, mval in metrics:
            draw.text((bx+20, my), mname, font=get_font(12, bold=True), fill=TEXT_WHITE)
            draw.text((bx+20, my+18), mval, font=get_font(11, bold=False), fill=TEXT_MUTED)
            my += 45
            
        bx += 440

    # Rollout Phases
    draw.rounded_rectangle((50, 485, 1325, 695), radius=8, fill=CARD_BG, outline=CARD_BORDER)
    draw.text((70, 505), "GATED 3-PHASE ROLLOUT PLAN & RISK MITIGATION", font=get_font(13, bold=True), fill=TEXT_YELLOW)
    
    phases = [
        ("PHASE 1 · PROVE (WEEKS 1-4)", "5% Inspiration Browsers in Bangalore & Mumbai. Validate NSM lift (+3pp) & zero AOV dilution."),
        ("PHASE 2 · EXPAND (WEEKS 5-12)", "50% Rollout across Top 15 Metros. Dynamic LLM copy enabled; verify return rate drop >=15%."),
        ("PHASE 3 · INSTITUTIONALIZE (MONTHS 4-6)", "100% Platform Rollout (175M MAU). Permanent Wishlist AI Confidence Infrastructure.")
    ]
    
    py = 535
    for ptitle, pdesc in phases:
        draw.text((70, py), ptitle, font=get_font(12, bold=True), fill=TEXT_CYAN)
        draw.text((70, py+18), pdesc, font=get_font(11, bold=False), fill=TEXT_MUTED)
        py += 46

    draw_footer(draw, "KPI Framework: Google HEART · Nielsen Norman Group Standards · Financial Model · Research Appendix")
    return img

def main():
    os.makedirs('ppt data', exist_ok=True)
    os.makedirs('ppt_data', exist_ok=True)
    
    # Copy existing slides 2-5 from ppt_data to ppt data
    for i in range(2, 6):
        names = [
            '1_Growth_Strategy_Overview.jpg',
            '2_AI_Discovery_Engine.jpg',
            '3_Architecture_Pipeline.jpg',
            '4_Primary_Research.jpg',
            '5_Root_Cause_Analysis.jpg'
        ]
        src = os.path.join('ppt_data', names[i-1])
        dst = os.path.join('ppt data', f'{i:02d}_{names[i-1][2:]}')
        if os.path.exists(src):
            shutil.copyfile(src, dst)
            print(f"Copied {src} -> {dst}")
            
    # Generate Slides 1, 6-10
    slide_gens = [
        (1, generate_slide_1, "01_Growth_Strategy_Overview.jpg"),
        (6, generate_slide_6, "06_5_Why_Ladder_Habit_Loop.jpg"),
        (7, generate_slide_7, "07_Prioritization_RICE.jpg"),
        (8, generate_slide_8, "08_MVP_Confidence_Bridge.jpg"),
        (9, generate_slide_9, "09_Technical_Pipeline_Rules_vs_AI.jpg"),
        (10, generate_slide_10, "10_Success_Metrics_KPI_Rollout.jpg")
    ]
    
    for snum, gen_func, fname in slide_gens:
        img = gen_func()
        out_path = os.path.join('ppt data', fname)
        img.save(out_path, "JPEG", quality=95)
        # Also copy to ppt_data
        img.save(os.path.join('ppt_data', f"{snum}_{fname[3:]}"), "JPEG", quality=95)
        print(f"Generated Slide {snum}: {out_path}")

if __name__ == '__main__':
    main()
