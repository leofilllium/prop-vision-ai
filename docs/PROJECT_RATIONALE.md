# Section 1 — Project Overview & Rationale

## 1.1 Problem Statement

### The Current State of Real Estate Platforms in Uzbekistan

Uzbekistan's real estate market is experiencing a period of remarkable growth. In 2025 alone, the country recorded 319,500 residential property transactions — a 15.8% increase year-over-year — with mortgage lending surging 29% to reach 21.2 trillion soums (~$1.7 billion USD). Tashkent, the capital, accounts for approximately 30% of all transactions, while regional markets in Bukhara (+25.6%), Syrdarya (+23.1%), and Samarkand (+19.2%) are expanding rapidly. New residential construction grew 7.2%, with 15.9 million square meters of floor area commissioned nationwide.

Despite this explosive growth, the digital infrastructure supporting property discovery and evaluation remains fundamentally primitive. The three dominant platforms — **OLX Uzbekistan**, **Uysot**, and **Birbir** — operate on an identical paradigm established over a decade ago: flat 2D listings consisting of photo galleries (typically 5–15 photos per listing), free-text descriptions written by sellers (often inconsistent, incomplete, or misleading), basic attribute fields (room count, square meters, price), a location pin on a 2D map, and seller contact information.

This flat-listing model creates measurable problems across the entire transaction lifecycle:

**For Buyers and Renters:**
- **Decision paralysis**: The average property seeker in Tashkent spends 3–5 minutes per listing, browsing through photos and reading descriptions, yet leaves the page without a clear spatial understanding of the property. Without immersive visualization, buyers cannot assess room flow, ceiling heights, natural light orientation, or the general "feel" of a space from photos alone.
- **Information asymmetry**: Buyers have no standardized way to evaluate neighborhood quality. Questions like "How far is the nearest metro station?", "Are there good schools nearby?", or "Is this area safe at night?" require manual research across multiple sources — Google Maps, word-of-mouth, and physical neighborhood visits.
- **High bounce rates**: Industry benchmarks for property listing platforms show bounce rates of 55–70% on individual property pages, largely because users cannot extract sufficient value from flat descriptions and static photos. In markets without immersive visualization tools, bounce rates trend toward the higher end of this range.
- **Inefficient search**: Boolean filter-based search (select district, set price range, choose room count) fails to capture the nuanced requirements that drive real purchasing decisions. A buyer who wants "a quiet 3-room flat near a park in Yunusabad, under $70,000" must manually apply filters, scan results, and cross-reference each listing against external data sources.

**For Sellers and Real Estate Agents:**
- **Listing commoditization**: When every listing looks identical — photos, text, pin on map — sellers cannot differentiate their properties. Premium properties with excellent locations, superior finishes, or desirable neighborhood amenities have no mechanism to communicate this advantage digitally.
- **Low conversion rates**: The typical listing-to-inquiry conversion rate on Uzbek property platforms is estimated at 2–5%. Sellers receive fewer inquiries than their properties deserve because buyers cannot form sufficient confidence from the listing alone.
- **Wasted physical visits**: Without immersive previews, both buyers and sellers invest time in physical property visits that could have been filtered out digitally. Industry estimates suggest that 40–60% of in-person property visits result in an immediate "no" that could have been determined from a better digital preview.

**For Platform Operators (OLX, Uysot, Birbir):**
- **Stagnant engagement metrics**: Platforms compete on inventory size (number of listings) rather than on user experience or data intelligence. This creates a race to the bottom where differentiation is impossible.
- **Missed monetization opportunities**: Without advanced features, platforms cannot justify premium listing tiers, value-added services, or B2B data products. Revenue remains limited to basic listing fees and banner advertising.
- **No competitive moat**: Any new entrant with a larger marketing budget can replicate the flat-listing model overnight. Platform loyalty is near zero — users cross-post listings on all platforms simultaneously.

### Quantifying the Gap

| Metric | Current State (Estimated) | With PropVision.AI (Target) |
|--------|--------------------------|---------------------------|
| Average time on property page | 3–5 minutes | 6–10 minutes (+80–100%) |
| Property page bounce rate | 60–70% | 35–45% (-35%) |
| Listing-to-inquiry conversion | 2–5% | 5–10% (+100%) |
| Physical visits per transaction | 8–12 | 4–6 (-50%) |
| Search-to-relevant-result rate | ~40% (filter mismatch) | ~75% (AI-parsed intent) |
| Neighborhood data available | None (manual research) | 5 automated comfort scores |

---

## 1.2 Proposed Solution — PropVision.AI: The Main Idea

### Core Concept

**PropVision.AI is a B2B plug-and-play visualization and AI intelligence layer that integrates into existing real estate platforms.** It is explicitly **not** a new marketplace, not a listing aggregator, and not a consumer-facing application. PropVision.AI provides technology that makes existing platforms smarter, more immersive, and more valuable — without requiring those platforms to rebuild their core product.

Think of PropVision.AI as infrastructure: it sits behind the scenes, powering features that appear native to the partner platform's user interface.

### What "Plug-and-Play" Means Technically

PropVision.AI provides two integration surfaces:

1. **A set of lightweight REST APIs** that partner platforms call to ingest property data, retrieve computed analytics, execute AI-powered searches, and manage 3D reconstruction jobs.

2. **Embeddable frontend widgets** (iframe-based or JavaScript SDK) that partner platforms drop into their existing property pages. These widgets render the 3D map viewer, AI search bar, comfort analytics panel, and 3D property previewer — all styled to match the partner's branding via configurable themes.

**Integration complexity is deliberately minimal.** A partner platform's development team integrates PropVision.AI by:
- (a) Sending their property listing data to PropVision's ingestion API via a simple POST endpoint with flexible JSON field mapping.
- (b) Embedding PropVision's frontend widgets into their existing property detail pages via a `<script>` tag and a `<div>` container with data attributes (API key, property ID, theme color).

**Target integration time: under 5 working days** for a developer familiar with the partner platform's codebase. No major re-architecture of the partner platform is required. The partner does not need to adopt new databases, frameworks, or deployment infrastructure.

### What "3D Visualization" Means Specifically

PropVision.AI does **NOT** require property sellers to perform professional 3D scans using expensive equipment like Matterport cameras or LiDAR scanners. Instead, the system uses **AI-powered 3D reconstruction from existing 2D photographs**.

**How it works:**

1. **Input**: Sellers upload 8–15 standard smartphone photos of a property, taken from different angles with overlapping coverage. No special equipment, no technical skill required — just walk through the rooms and photograph from corners and doorways.

2. **Processing**: PropVision's backend sends these photos to a cloud-based photogrammetry service. The primary integration uses the **Luma AI API** for AI-driven 3D reconstruction. As a fallback for cases where the cloud API is unavailable or cost-prohibitive, the system supports **COLMAP** as a self-hosted open-source alternative (requires GPU resources on the server).

3. **Output**: The pipeline produces a **GLB/glTF file under 10 MB** — a compact, web-optimized 3D mesh with approximate textures extracted from the source photographs.

4. **Rendering**: The GLB model is displayed in-browser using **Three.js** with **OrbitControls**, allowing the user to rotate, zoom, and pan around the property interactively. Additional controls include auto-rotation toggle and fullscreen mode.

**Fidelity expectations (critical to set correctly):**

This is **NOT** a high-fidelity digital twin. It is a **low-to-medium fidelity 3D reconstruction** sufficient to give buyers a spatial understanding of:
- Room layout and flow between rooms
- Approximate room dimensions and proportions
- Window and door placement
- General ceiling height

**Expected artifacts and limitations:**
- Visible holes in surfaces, especially in occluded areas (behind furniture, inside closets)
- Blurred or approximate textures (not accurate material/finish representation)
- Incorrect geometry where photo coverage is insufficient
- This is prototype-grade reconstruction, suitable for spatial orientation — not architectural visualization or interior design evaluation

**For the MVP**: 5 of the 30 demo properties will have 3D reconstructions. The remaining 25 will display standard photo galleries with a fallback 360° CSS image carousel.

### What "AI-Powered Search" Means

Traditional property search on Uzbek platforms is filter-based: users select a district from a dropdown, set a price range with sliders, choose a room count, and click "Search." This forces users to think in the platform's data model rather than expressing their actual needs.

PropVision.AI introduces **natural language property search**. Users type free-form queries like:
- "2-room flat near metro under $70,000"
- "quiet area with parks, 3 rooms, Yunusabad district"
- "3 xonali kvartira Chilanzar, 50,000 dollardan past"
- "большая квартира рядом с метро, до 80 тысяч"

**How it works:**

1. The user's natural language query is sent to the backend.
2. The backend calls **OpenAI's API (GPT-4o-mini model)** with a carefully engineered system prompt that includes:
   - The structured output schema (rooms, price range, district, proximity constraints)
   - A **RAG context layer**: a glossary of 200+ Uzbek real estate terms, district names, local landmarks, and pricing conventions injected into the system prompt
3. The AI model parses the query into **structured filters**: `{ "rooms": 2, "max_price": 70000, "proximity_to": "metro", "max_distance_m": 1000, "district": null }`
4. These structured filters are executed as **PostGIS spatial queries** against the property database using functions like `ST_DWithin` for proximity and `ST_Distance` for ranking.
5. Results are returned as ranked property listings, displayed both as map markers (with fly-to animation) and a scrollable list.

**Critical design principle**: The AI does NOT hallucinate listings. It does NOT generate property descriptions, fabricate prices, or invent data. It **only** translates natural language into database query filters. All returned results are real properties from the database.

### What "Comfort Analytics" Means Precisely

For each property listing, PropVision computes a set of **location-based livability scores** derived from nearby points of interest (POIs) and geographic data. This is **NOT** AI-generated opinion — it is **computed from real geospatial data** using distance calculations and density analysis.

**The five comfort dimensions:**

| Score | Range | Methodology | Data Source | Radius |
|-------|-------|-------------|-------------|--------|
| **Transport Score** | 0–100 | Count and distance to nearest bus stops, metro stations, and taxi stands | OpenStreetMap (Overpass API) | 1 km |
| **Shopping Score** | 0–100 | Count and distance to supermarkets, convenience stores, and markets | Google Places API + OSM | 800 m |
| **Education Score** | 0–100 | Count and distance to schools, kindergartens, and universities | Google Places API + OSM | 1.5 km |
| **Green Space Score** | 0–100 | Count and area of parks, gardens, and recreational zones | OSM land-use data | 1 km |
| **Safety Score** | 0–100 | Approximated from street lighting density, proximity to police stations and hospitals, neighborhood classification | OSM + municipal data | 1 km |

**Safety Score Limitation (explicitly acknowledged):** Uzbekistan does not publish open crime data, noise level measurements, or air quality indices at neighborhood granularity. The safety score is a **rough proxy** based on infrastructure indicators (street lighting, emergency services proximity), **not** actual crime statistics. This limitation is displayed to users via a confidence indicator ("Based on limited data") when fewer than 3 data points exist within the scoring radius.

**Overall Comfort Index:** Weighted average of all sub-scores:
- Transport: 25%
- Shopping: 20%
- Education: 20%
- Green Space: 15%
- Safety: 20%

Weights are **configurable per partner** — a family-oriented platform might weight education higher, while a young-professionals platform might weight transport and shopping higher.

**Visualization:** Scores are displayed as:
- A **radar chart** (5-axis spider chart) on the property detail panel
- **Colored overlays on the map** (heatmap-style) showing comfort score distribution across neighborhoods

**Data freshness:** Comfort scores are computed on a **batch schedule** (nightly cron job), not in real-time. POI data is refreshed weekly from OSM and Google Places. This is acceptable for MVP because neighborhood infrastructure changes slowly.

---

## 1.3 BaaS (Business-as-a-Service) Model

PropVision.AI operates as a **B2B technology provider**, not a consumer-facing product. The company sells capabilities to platform operators, not to individual property seekers or sellers.

**Revenue model progression:**

| Phase | Model | Details |
|-------|-------|---------|
| **MVP (Months 1–5)** | Free pilot | Free integration with 1 local platform partner to prove value and gather metrics |
| **Post-MVP (Months 6–12)** | Per-API-call pricing | Tiered pricing: $0.01 per property view with comfort analytics, $0.05 per AI search query, $0.50 per 3D reconstruction job |
| **Scale (Year 2+)** | Monthly SaaS subscription | $500–$5,000/month per partner based on API call volume tiers |

**Why B2B, not B2C:**
- **Lower customer acquisition cost**: Signing one platform partner (OLX Uzbekistan) instantly reaches their entire user base. No need for consumer marketing.
- **Defensible positioning**: Platform partners become dependent on PropVision's infrastructure, creating switching costs and long-term contracts.
- **Data network effects**: As more partners integrate, PropVision's POI database, comfort analytics, and AI search model improve — benefiting all partners and creating a compounding advantage.
- **Regulatory simplicity**: By never collecting end-user data directly, PropVision avoids consumer data protection obligations. All user interactions happen on the partner's platform.

---

## 1.4 Value Proposition

### For Partner Platforms (OLX, Uysot, Birbir)

| Capability | Partner Benefit | Expected Impact |
|-----------|----------------|-----------------|
| 3D Property Previews | Differentiated listings attract more buyers, justify premium listing tiers | +40% average time on property page |
| AI Natural Language Search | Users find relevant properties faster, reducing bounce and improving satisfaction | ≥30% click-through from AI search results to property detail |
| Comfort Analytics | Unique neighborhood intelligence unavailable on competing platforms | Competitive differentiation, no domestic competitor offers this |
| Embeddable Widget | Zero-effort integration, no platform re-architecture needed | Integration in <5 days developer time |
| Engagement Data | API usage analytics help platforms understand user behavior | Data-driven product decisions |

### For End Users (Property Buyers and Renters)

| Capability | User Benefit |
|-----------|-------------|
| 3D Property Previews | Understand spatial layout without physical visits; reduce wasted viewings |
| AI Search | Express real needs in natural language; find relevant properties 3× faster than manual filtering |
| Comfort Analytics | Make informed decisions about neighborhood quality using objective, data-driven scores |
| Interactive Map | Explore properties spatially; compare neighborhoods visually; understand district geography |

### Summary

PropVision.AI transforms Uzbekistan's static, photo-based property listings into an intelligent, immersive, data-rich property discovery experience — delivered as a plug-and-play module that any platform can integrate in under a week. It addresses a clear market gap (no domestic competitor offers 3D + AI + comfort analytics), serves a growing market (319,500 transactions/year, +15.8% growth), and follows a capital-efficient B2B distribution model that minimizes go-to-market risk.
