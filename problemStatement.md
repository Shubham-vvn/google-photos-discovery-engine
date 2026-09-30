# 📸 Google Photos AI Discovery Engine — Product Requirements & Problem Definition

> **Project:** NextLeap Product Manager Fellowship — Graduation Project (Sep 2026)  
> **Role:** Product Manager, Core Experience Team @ Google Photos  
> **Strategic Objective:** Increase the percentage of users who successfully retrieve a photo they remember but cannot precisely describe when they start searching.  
> **Deliverables:**  
> 1. AI-Powered Discovery Engine ([Link where tested] + 1 Slide Architecture)  
> 2. 10-Slide Fellowship Capstone Deck (PDF)  
> 3. Deployed AI-Native Retrieval MVP ([Link to interactive prototype])

---

## 1. Executive Summary & Problem Framing

Over years of smartphone camera usage, users accumulate tens of thousands of uncurated photos, videos, screenshots, bills, and visual memories in Google Photos. While exact-match keyword search (e.g., *"dogs"*, *"Paris 2023"*, *"receipts"*) works reasonably well, **retrieval collapses when memory is incomplete, episodic, or associative**.

### Real User Scenarios
* *"That small café we went to during our Goa trip where we had breakfast by the sea."*
* *"The photo of the white medicine tablet strip I bought when I had food poisoning last monsoon."*
* *"A screenshot of a book recommendation someone posted on Twitter with an orange cover."*

Users retain vivid **episodic memory** (emotions, surrounding context, co-present people, broad seasons, visual aesthetics), but digital search systems strictly index **semantic keywords, exact dates, and GPS metadata**. When users cannot recall exact timestamps or locations, existing search yields either **zero results** or **an unranked scroll abyss of 4,000 photos**, leading to retrieval abandonment.

---

## 2. Part 1: AI-Powered Discovery Engine Requirements

The Discovery Engine is an automated AI intelligence pipeline that ingests public user voice across the web to uncover:
1. **What kinds of old photos do users struggle to retrieve?** (e.g., utility/receipts, fleeting moments, screenshots, aesthetic vibes, personal milestones).
2. **What clues do users actually remember?** (color palette, companion present, event context, emotion/vibe, physical object anchor).
3. **What have users forgotten?** (exact calendar date, exact location/geotag, album name, specific OCR wording).
4. **How do users formulate searches with partial memory?** (vague keywords, descriptive stories, multi-query churn, repeated synonym bashing).
5. **Where does the product experience break down?** (zero hits, semantic misunderstanding, overwhelming candidate sets, lack of conversational refinement).

### Public Ingestion Targets
* **Google Play Store:** Package `com.google.android.apps.photos` (1B+ installs, thousands of retrieval & search reviews).
* **Apple App Store:** Google Photos iOS App (ID: `962194608`).
* **Reddit Communities:** `r/googlephotos`, `r/google`, `r/Android`, `r/techsupport` (threads containing search frustrations, lost memories, query struggles).
* **Google Support Community & Forums:** Search queries on photo retrieval failures, timeline scroll exhaustion.

---

## 3. Part 2: Business Metric Decomposition

$$\text{Successful Retrieval Rate} = P(\text{Retrieval Success} \mid \text{Vague Memory Trigger})$$

We decompose this strategic business metric into four sequential product outcomes along the retrieval funnel:

```mermaid
graph LR
    A[1. Query Formulation Rate] --> B[2. Semantic Clue Match Rate]
    B --> C[3. Candidate Set Evaluation Rate]
    C --> D[4. Search Refinement Rate]
    D --> E[Successful Retrieval Outcome]
```

1. **Query Formulation Success ($Q_f$):**  
   *Does the user know how to express their vague memory into the search box, or do they immediately give up and resort to endless manual scrolling?*
2. **Semantic Clue Match Precision ($S_m$):**  
   *Does Google Photos correctly translate multi-modal/episodic clues (e.g., "sunny breakfast café") into relevant visual embeddings, rather than failing on literal lexical mismatch?*
3. **Candidate Set Disambiguation ($C_d$):**  
   *When 100+ photos match, can the user quickly spot the target image without scanning through hundreds of nearly identical vacation shots?*
4. **Iterative Refinement Efficiency ($R_e$):**  
   *If the first search fails, does the system guide the user to add or swap clues ("Was anyone else with you?", "Was it outdoors?"), or does it leave them at a dead end?*

---

## 4. Part 4: Target Personas & Opportunity Matrix

| Persona | Primary Retrieval Goal | What They Remember | What They Forgot | Primary Failure Mode |
|---|---|---|---|---|
| **The Life Documenter** (Heavy mobile photographer, 30K+ photos) | Fleeting life moments, trips, family events | Emotional vibe, weather, who was with them | Exact year/month, specific location name | 500+ photo scroll fatigue; query returns 0 hits |
| **The Visual Note-Taker** (Professionals, students) | Receipts, whiteboards, book pages, medicine labels | Purpose of note, color/shape of item | When taken, exact text on the document | OCR search misses blurry text or synonyms |
| **The Nostalgia Seeker** (Occasional searcher) | Deep archive memories (5–10 years ago) | Life phase (e.g., "college days", "first apartment") | Year, camera used, device source | Search doesn't understand relative life phases |
| **The Screenshot Hoarder** | Saved recommendations, memes, fashion inspirations | Visual composition, platform origin (Instagram/Twitter) | Date saved, text inside screenshot | Unindexed text, visual similarity collapse |

---

## 5. Scope of Deliverables

1. **Interactive Discovery Engine:**  
   * Production-deployed dashboard displaying high-level stats, cognitive clue breakdown, retrieval failure modes, query formulation friction, and an interactive LLM chat query interface for product managers.
2. **10-Slide Capstone Deck:**  
   * Business Metric Decomposition, Discovery Engine findings, User Research synthesis, Target Segment & Root Cause, Solution Rationale, AI-Native MVP specifications, Metrics & Risk mitigations.
3. **AI-Native Retrieval MVP Prototype:**  
   * An interactive associative retrieval experience allowing users to query photos using vague memories and conversational context.
