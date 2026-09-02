# Myntra Wishlist-to-Purchase AI Discovery Engine

## Background

Myntra is one of India's largest online fashion and lifestyle platforms. Users regularly browse products and add items they like to their wishlist — a signal of clear interest, but not yet a purchase decision. Over weeks and months, users can accumulate dozens or even hundreds of wishlisted items, while only a small fraction of those items are ever actually bought.

## Business Goal

The company wants to increase the percentage of users who purchase at least one item from their wishlist within 30 days of adding it. Improving this **"Wishlist → Purchase Conversion"** rate matters because it would increase purchase frequency and help the company extract more value from demand that already exists on the platform — users who are already interested don't need to be convinced to like the product, only to complete the purchase.

## Constraint

> [!IMPORTANT]
> The solution **CANNOT** use monetary incentives. That means no discounts, coupons, cashback, wallet credits, or price-based offers.

Whatever explains the drop-off between wishlisting and buying, the fix has to work through **information, trust, confidence, or experience** — not price.

## The Problem We Don't Yet Know

We do not know why wishlisted items go unpurchased. It could be:

- Uncertainty about fit or size
- Doubts about quality
- Price hesitation
- Not being sure the item suits the occasion
- Wanting outside opinions before deciding
- Forgetting about the item entirely
- Using the wishlist just as a mood board rather than real purchase intent
- Or something else entirely

> [!WARNING]
> We are **not** allowed to guess this upfront — it has to be discovered from real user behavior and language, not assumed.

## What This Tool Should Do

Build an **AI-powered discovery engine** that reads large volumes of public, real user conversations about Myntra and online fashion shopping — Google Play Store reviews, Reddit posts and comments, and similar public sources — and extracts structured patterns from that unstructured text.

Specifically, for each piece of user text, the system should try to identify:

1. **Why** the user saved or wishlisted a product in the first place
2. **What is stopping them** from completing the purchase, if anything
3. **What kind of uncertainty** they express (about fit, quality, price, occasion, trustworthiness of reviews, availability, etc.)
4. **Shopper persona clues** — what type of shopper they are (budget-conscious, occasion shopper, browsing for inspiration, etc.)
5. **Confidence level** — whether the evidence is a direct statement, an inference, or just a weak signal — so we never overstate how certain a finding is

> [!NOTE]
> This should go beyond basic sentiment analysis (positive/negative) or a generic review summary. The output should be an organized, evidence-backed view of the recurring reasons wishlisted items don't convert to purchases, so that a product team can use it to decide which specific problem is worth solving next — and eventually design a non-monetary product feature to fix it.

## Output This Project Should Produce

1. **Clean structured data** extracted from raw public reviews/posts
2. **A summary of the most common patterns**, clearly labeled as directional/qualitative evidence (not statistically proven, since the sample is small)
3. **A simple, shareable dashboard** where these findings can be browsed and verified by a reviewer, without needing to read raw code or spreadsheets
