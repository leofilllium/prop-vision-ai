# PropVision.AI — Presentation Guide

**Format:** 20 min presentation · 5 min Q&A · 5 min live tasks  
**Project:** AI-Powered Real Estate Visualization Platform for Uzbekistan  
**Student:** Solo developer, 100-day BISP project

---

## Part 1 — Presentation Script (20 minutes)

---

### Slide 1 · Opening (1 min)

**What to say:**

> "Good [morning/afternoon]. My project is called PropVision.AI — an AI-powered visualization and intelligence layer built for the Uzbek real estate market. In the next 20 minutes I'll walk you through the problem it solves, the system I built, the architectural decisions I made, and what the results look like."

**Key framing to establish early:**
- This is NOT a new real estate marketplace
- It is B2B infrastructure — a layer that makes existing platforms smarter
- Think of it as what Mapbox is to apps — you plug it in and get capabilities you couldn't build yourself

---

### Slide 2 · Problem & Market Context (2 min)

**What to say:**

> "In 2025 Uzbekistan processed 319,500 real estate transactions — up 15.8% year-on-year. Mortgage lending alone surged 29% to $1.7 billion USD. The market is growing fast."

> "But if you open OLX.uz, Uysot.uz, or Birbir.uz — the three dominant property platforms — you see the same product that existed a decade ago: flat photo galleries, a price, and a district label. That's it."

> "Three specific gaps I identified:"

1. **No neighborhood context** — you cannot see whether the flat is 5 minutes or 45 minutes from a metro station
2. **No livability data** — there is no way to compare how 'family-friendly' two districts are
3. **No spatial search** — users filter by city and rooms, not by "2km from school, 10 min to Chorsu bazaar"

> "These gaps cause decision paralysis and low conversion. Industry benchmarks show listing-to-inquiry rates of 2–5% on these platforms. My target is 5–10% through better information."

---

### Slide 3 · Solution Overview (2 min)

**What to say:**

> "PropVision.AI has four core capabilities:"

| Capability | What it does |
|---|---|
| **3D Map Viewer** | Dark-themed interactive map showing properties with 3D building extrusions, district filters, and detail panels on click |
| **AI Natural Language Search** | Type in English, Russian, or Uzbek — the system parses intent and queries the database spatially |
| **Comfort Analytics** | 7 livability scores computed automatically: transport, shopping, education, green space, safety, healthcare, entertainment |
| **3D Property Viewer** | Upload 8–15 smartphone photos → AI reconstruction → walkable 3D model in the browser |

> "Partners — existing platforms — integrate via two routes: a REST API or a drop-in JavaScript widget that works like a Google Maps embed."

---

### Slide 4 · Architecture Overview (3 min)

**What to say:**

> "Let me walk through the system architecture. I'll go layer by layer."

**Frontend:**
> "React 18 with TypeScript. I chose React over Angular primarily because the two most critical libraries — Mapbox GL JS and Three.js — both have mature React-first wrappers. Angular bindings for these exist but lag behind. Bundle size was also a factor: 42 KB gzipped vs. ~90 KB for Angular."

**Backend:**
> "FastAPI on Python 3.11. The key reason over Django was native async/await — I'm making concurrent calls to OpenAI, Google Places, and Meshy AI simultaneously. FastAPI also auto-generates OpenAPI documentation that stays in sync with the code, which matters for a B2B API product."

**Database:**
> "PostgreSQL 16 with the PostGIS extension. Real estate is fundamentally a geospatial problem — I need to answer questions like 'all properties within 1km of a metro station'. PostGIS gives me that with a single function: `ST_DWithin`. MongoDB or Elasticsearch would require me to implement that geometry myself."

**Infrastructure:**
> "Five Docker containers orchestrated with Docker Compose: the FastAPI backend, the React frontend served by Nginx, PostgreSQL, Redis, and a top-level Nginx reverse proxy handling SSL. Deployed on a single AWS Lightsail instance at $40/month — appropriate for an MVP with 100 concurrent users. The scaling path to EKS is documented if the project grows."

**CI/CD:**
> "GitHub Actions pipeline — on every push to main: lint and test, build Docker images, SSH into the Lightsail instance, pull and restart containers. Zero-downtime for stateless services."

---

### Slide 5 · AI Search — Deep Dive (3 min)

**What to say:**

> "Let me go deeper on the AI search because it's the most technically novel part."

**The pipeline step by step:**

1. User types: *"2-room flat near metro station under $70,000"*
2. Frontend sends `POST /api/v1/search` with the raw string
3. Backend loads a RAG context file — a glossary of 200+ Uzbek real estate terms — and injects it into the system prompt
4. GPT-4o-mini parses the query into a structured JSON object:
   ```json
   { "rooms": 2, "max_price": 70000, "proximity_to": "metro_station" }
   ```
5. The backend runs a PostGIS query:
   ```sql
   SELECT * FROM properties
   WHERE rooms = 2
     AND price <= 70000
     AND ST_DWithin(
           location,
           (SELECT location FROM pois WHERE category = 'metro_station'
            ORDER BY location <-> properties.location LIMIT 1),
           1000
         )
   ```
6. Results are returned ranked by relevance; the map flies to the first result

> "The RAG glossary is critical. Without it, the model doesn't know that 'Yunusobod' is a district, or that '2-xonali' means 2-room in Uzbek. With it, the system handles Russian and Uzbek queries accurately. My target accuracy is ≥85% on a 50-query test set."

> "Importantly — there is no hallucination risk on results because the model only parses the query. All actual property data comes from the database."

---

### Slide 6 · Comfort Analytics — Deep Dive (2 min)

**What to say:**

> "The comfort scoring system gives every property a livability profile across 7 dimensions."

**How it works:**
- Data sources: OpenStreetMap Overpass API (free, no quota) + Google Places API (200 free requests/day)
- For each property, I fetch all Points of Interest within a configurable radius
- Each dimension scores 0–100 using two factors: distance to the nearest POI (40% weight) and density of POIs in the area (60% weight)
- Scores are computed by a nightly cron job using APScheduler
- Results cached in Redis with a 24-hour TTL
- Each score carries a confidence flag: LOW / MEDIUM / HIGH based on how many POIs were found

> "The weights are configurable per partner — a platform targeting families might weight education and green space higher; a platform for young professionals might weight entertainment and transport more."

> "The output is displayed as a radar chart in the frontend and as a heatmap overlay on the map."

---

### Slide 7 · 3D Reconstruction (2 min)

**What to say:**

> "The 3D viewer feature turns smartphone photos into a walkable 3D model."

**Pipeline:**
1. Agent uploads 8–15 JPEG/PNG photos via the API (≤10 MB each)
2. Backend validates, uploads to S3, submits job to Meshy AI's cloud API
3. The job is async — typical processing time is 5–20 minutes
4. The frontend polls for status every 30 seconds
5. When complete, a GLB file (target ≤10 MB) is stored in S3 and linked to the property
6. Three.js renders it with OrbitControls, auto-rotation, and fullscreen

> "The fallback if no 3D model exists is a standard photo carousel — the UI degrades gracefully."

> "I chose cloud-based reconstruction via Meshy AI specifically so the server doesn't need a GPU. The Lightsail instance stays cheap. The trade-off is the processing latency and a per-call API cost in production."

---

### Slide 8 · Results & Metrics (2 min)

**What to say:**

> "Let me summarize what was delivered:"

| Metric | Target | Status |
|---|---|---|
| Map load time | ≤ 2s on 10 Mbps | Achieved |
| AI search accuracy | ≥ 85% on 50 queries | Achieved |
| Comfort score refresh | Nightly, < 30 min total | Achieved |
| 3D processing time | 5–20 min per property | Achieved |
| API p95 response time | < 500 ms search, < 200 ms detail | Achieved |
| Rate limiting | 100 req/min per API key | Achieved |
| Demo dataset | 30 properties, 5 with 3D models | Achieved |
| Infrastructure cost | ≤ $60/month | $40/month |

> "The project covers 17 formal success criteria across system, business, and learning objectives. All 17 are met at MVP level."

---

### Slide 9 · Limitations & Future Work (1 min)

**What to say:**

> "I want to be honest about the limitations."

- **Safety data** — the 'safety' comfort dimension is a proxy (street lighting density from OSM) because Tashkent does not publish granular crime data. This is disclosed to partners.
- **Primary data** — user research (focus groups, usability testing) is planned post-MVP. The problem framing was validated through secondary market data, not live user interviews.
- **Single-instance deployment** — the $40/month setup has no redundancy. The documented scaling path is to AWS ECS or EKS when load justifies it.
- **3D quality** — photogrammetry from 8–15 smartphone photos produces prototype-grade models, not Matterport quality. Suitable for spatial understanding, not architectural rendering.

**Future roadmap:**
- AR mobile viewer (WebXR or native iOS/Android)
- Predictive pricing model (price per district over time)
- Expand beyond Tashkent to Samarkand, Bukhara
- Deeper marketplace integrations (Uysot, OLX direct API access)

---

### Slide 10 · Closing (1 min)

**What to say:**

> "To summarize: PropVision.AI is a full-stack B2B SaaS platform that adds AI search, geospatial comfort analytics, and 3D visualization to existing real estate platforms in Uzbekistan. It uses a modern async Python backend, a React TypeScript frontend, PostGIS for spatial queries, GPT-4o-mini for natural language understanding, and runs on a cost-efficient containerized AWS deployment."

> "The project demonstrates end-to-end skills: system design, AI integration, geospatial engineering, DevOps, and market analysis. I'm happy to open the demo or dive into any part of the implementation."

---

## Part 2 — Likely Professor Questions & Answers (5 min)

---

### Category A: Technical Depth

**Q: Why did you use GPT-4o-mini instead of a larger model like GPT-4o?**

> GPT-4o-mini is sufficient for structured extraction tasks. The query parsing job is classification and slot-filling, not open-ended reasoning. GPT-4o-mini is 15× cheaper per token and has lower latency — both matter in a real-time search UX. I tested the accuracy and it met the ≥85% target on my test set. I would upgrade to GPT-4o only if accuracy dropped on more complex multi-constraint queries.

**Q: How does your RAG (Retrieval Augmented Generation) work exactly?**

> My RAG is a static context injection, not a vector database RAG. I maintain a JSON file of 200+ domain-specific terms — Uzbek neighborhood names, Uzbek/Russian real estate vocabulary, and common price formats. This glossary is loaded at startup and injected into every search request's system prompt. This is appropriate because the context is small (~3 KB), doesn't need to be searched, and is fully deterministic. A vector database RAG (like Pinecone + embeddings) would be warranted if the knowledge base grew to tens of thousands of documents.

**Q: What happens if the OpenAI API is down?**

> The search endpoint returns a 503 with a clear error message. The frontend shows a "AI search unavailable" state and offers the user a manual filter panel as a fallback. I use the Tenacity library for retry logic with exponential backoff — 3 retries with 2s, 4s, 8s delays before failing. Rate limit errors (429) from OpenAI are caught separately and surfaced to the user as "Search is temporarily busy."

**Q: How do you prevent SQL injection in your PostGIS queries?**

> All queries use SQLAlchemy's parameterized query builder — no raw string concatenation. The parsed filters from GPT-4o-mini are validated against Pydantic schemas before touching the database. For example, `rooms` must be an integer between 1 and 10, `max_price` must be a positive float. If the structured output from OpenAI contains unexpected fields, Pydantic raises a validation error before any database query is executed.

**Q: Why PostGIS instead of Elasticsearch with geo_point?**

> Both are valid choices. I chose PostGIS because: (1) I already needed PostgreSQL for ACID-compliant property CRUD, (2) PostGIS co-locates my geospatial and relational data in one engine, reducing operational complexity, and (3) PostGIS's spatial functions — particularly `ST_DWithin` and nearest-neighbor ordering — are more expressive than Elasticsearch's geo queries for this use case. If I needed full-text search across property descriptions at scale, Elasticsearch would be worth adding.

**Q: What is your database schema? Can you explain the main tables?**

> Seven primary tables:
> 1. `properties` — core listing data: title, price, rooms, district, `location` (GEOMETRY POINT — this is a PostGIS spatial column), `photos` (JSONB array of S3 URLs), `model_3d_url`, `reconstruction_status`
> 2. `comfort_scores` — one row per property, 7 float columns for each dimension plus a `data_confidence` enum
> 3. `pois` — Points of Interest fetched from OSM and Google Places: name, `category` (ENUM), `location` (GEOMETRY POINT), `source`, `metadata` (JSONB)
> 4. `partners` — B2B client accounts: name, `api_key_hash` (SHA-256), `field_mapping` (JSONB for schema flexibility), `webhook_url`
> 5. `api_logs` — every request logged: endpoint, method, status code, response time, partner ID
> 6. `search_queries` — every AI search logged: raw query, parsed filters as JSONB, result count, parse success flag, processing time
> 7. `reconstructions` — 3D job tracking: status, S3 URLs, Meshy job ID, timestamps

**Q: How does your authentication work?**

> Partners authenticate using API keys in the `X-API-Key` header. Keys are generated as cryptographically random 32-byte hex strings, then hashed with SHA-256 before storage. At request time I hash the incoming key and compare to the stored hash — the plaintext key is never stored. On top of that I have a Redis-based sliding window rate limiter: 100 requests per minute per API key. If exceeded, the response is HTTP 429 with `Retry-After` and `X-RateLimit-Reset` headers.

**Q: How does the CI/CD pipeline work?**

> GitHub Actions runs on every push to `main`. Three jobs in sequence: (1) Lint and run Pytest unit tests, (2) Build Docker images for frontend and backend, (3) SSH into the Lightsail instance, run `docker-compose pull && docker-compose up -d`. The database migration (`alembic upgrade head`) runs as part of the API container's startup command. Rollback is handled by reverting the git commit and re-deploying.

---

### Category B: Design Decisions

**Q: Why not build a mobile app?**

> Three reasons. First, a web-first approach means zero installation friction for partners — they embed a script tag. Second, Mapbox GL JS and Three.js are fully capable in modern mobile browsers via WebGL. Third, a native app was out of scope for a 100-day solo project. The scaling roadmap includes a WebXR mobile AR viewer as the next major feature.

**Q: Why not use Next.js instead of Vite + React?**

> PropVision is not a content site — there is no SEO benefit to server-side rendering because property listings are behind authentication. The application is a dynamic SPA (Single Page Application) used by logged-in partner admins or end users within an iframe widget. SSR adds operational complexity (Node.js server) for no meaningful benefit in this context.

**Q: The architecture is a monolith. Why not microservices?**

> At this scale — one developer, MVP, 100 concurrent users — microservices would add network overhead, deployment complexity, and distributed tracing overhead without benefit. The services inside the monolith ARE separated by concern (each feature has its own service class), making extraction straightforward if needed. The documented scaling roadmap shows the natural split: the 3D reconstruction worker is the first candidate for extraction because it has very different compute characteristics.

**Q: Why Meshy AI for 3D reconstruction instead of building your own?**

> Building a photogrammetry pipeline (COLMAP + OpenSfM + Instant-NGP) requires a GPU server, which immediately multiplies infrastructure cost and operational complexity. Meshy AI provides API access to a managed reconstruction service. For an MVP, the per-call cost is acceptable and the time-to-market is dramatically faster. The technical trade-off is acknowledged in the architecture decision records.

---

### Category C: Business & Academic

**Q: Who is the target customer?**

> The primary customer is a B2B client — an existing Uzbek real estate platform like Uysot.uz or Birbir.uz. They pay a SaaS fee to access the API and get visualization and AI features without building them in-house. The business model is freemium: a basic embeddable widget is free, advanced analytics and dedicated widget support are paid tiers.

**Q: How did you validate the market need?**

> Through secondary data analysis: market reports (CBU mortgage data, Stat.uz transaction records), competitive analysis of OLX, Uysot, and Birbir, and benchmarking against international proptech leaders (Zillow, Matterport, Rightmove). Primary validation through user research (focus groups, usability tests) is planned post-MVP and documented in the methodology section. I explicitly acknowledge this limitation.

**Q: What is the biggest technical risk?**

> The dependency on the Meshy AI API for 3D reconstruction. If Meshy changes pricing, goes down, or is unavailable in Uzbekistan, that feature fails. Mitigations: (1) fallback to photo carousel already implemented, (2) COLMAP is documented as an open-source self-hosted alternative, (3) the service layer is abstracted so the reconstruction provider can be swapped without frontend changes.

**Q: What did you learn from this project?**

> Six main areas per the formal learning objectives: geospatial development (PostGIS, coordinate systems, spatial indexes), LLM integration and prompt engineering, photogrammetry and 3D web rendering, B2B product design (API-first architecture, partner integration), DevOps (Docker, CI/CD, cloud infrastructure), and business analysis (SWOT, Porter's Five Forces, PESTEL applied to the Uzbek proptech market).

---

## Part 3 — Practical Tasks Professors Might Assign (5 min)

This section covers likely live-coding or live-configuration tasks. Read each task, orient yourself, then act quickly.

---

### Task 1: Change a UI color or label

**What they might say:** "Change the map marker color to blue" / "Change the header title" / "Make the accent color green"

**Where to look:**
- `frontend/src/index.css` — CSS custom properties (`--color-accent`, `--color-primary`, etc.)
- `frontend/src/components/Nav/NavBar.tsx` — NavBar branding text
- `frontend/src/components/Map/MapView.tsx` — marker colors inside the Mapbox layer paint properties

**Example — change accent color:**
```css
/* frontend/src/index.css */
--color-accent: #e07b54;  /* change this hex value */
```

**Example — change NavBar title:**
```tsx
/* frontend/src/components/Nav/NavBar.tsx */
<span>PropVision</span>  {/* change text here */}
```

**Time estimate:** 30 seconds to find, 10 seconds to change.

---

### Task 2: Add a new API endpoint

**What they might say:** "Add a GET /health endpoint" / "Add an endpoint that returns the total property count"

**Where to look:**
- `backend/app/api/routes/` — pick the most relevant route file, or create a new one
- `backend/app/main.py` — where routers are mounted

**Example — health check:**
```python
# backend/app/api/routes/properties.py (or any route file)
@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "propvision-api"}
```

**Example — property count:**
```python
@router.get("/properties/count")
async def get_property_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count()).select_from(Property))
    return {"count": result.scalar()}
```

**Time estimate:** 2 minutes including restart.

---

### Task 3: Change a database query filter

**What they might say:** "Show only properties cheaper than $50,000 by default" / "Filter properties to only show active ones"

**Where to look:**
- `backend/app/services/property_service.py` — main property query logic
- `backend/app/api/routes/properties.py` — endpoint parameters

**Example:**
```python
# Add a default price filter to the query
query = select(Property).where(Property.price <= 50000)
```

---

### Task 4: Adjust comfort score weights

**What they might say:** "Make transport score count double" / "Reduce the weight of entertainment"

**Where to look:**
- `backend/app/services/comfort_service.py` — scoring weights dictionary

**What to do:** Find the weights dict, adjust the numeric values, explain that the nightly job would recompute scores — for immediate demo you'd trigger a manual recalculation.

---

### Task 5: Add a field to an API response

**What they might say:** "Add a `floor_count` field to the property response"

**Where to look:**
- `backend/app/schemas/property.py` — Pydantic response schema (add the field here)
- `backend/app/models/property.py` — SQLAlchemy model (add column if it doesn't exist)

**Example — schema change:**
```python
class PropertyResponse(BaseModel):
    id: int
    title: str
    price: float
    floor_count: Optional[int] = None  # add this line
```

---

### Task 6: Change rate limit value

**What they might say:** "Change the rate limit to 200 requests per minute"

**Where to look:**
- `backend/app/api/dependencies.py` — rate limit constant
- `backend/app/config.py` — if it's an environment variable

**What to do:** Change the constant value. Explain the Redis sliding window mechanism.

---

### Task 7: Explain a specific file live

**What they might say:** "Open the AI search service and explain it line by line"

**File:** `backend/app/services/ai_search_service.py`

**Key things to point out:**
- RAG context loading function
- System prompt construction
- OpenAI structured output call
- Pydantic validation of the parsed result
- How filters map to PostGIS queries

---

## Part 4 — Quick Reference Card

### Key numbers to memorize

| Fact | Value |
|---|---|
| Uzbekistan transactions (2025) | 319,500 (+15.8% YoY) |
| Mortgage growth | 29% → $1.7B USD |
| Target listing-to-inquiry rate | 5–10% (industry: 2–5%) |
| AI search accuracy target | ≥85% |
| Comfort score dimensions | 7 |
| RAG glossary size | 200+ terms |
| 3D model processing time | 5–20 min |
| Rate limit | 100 req/min per API key |
| Infrastructure cost | $40/month (AWS Lightsail) |
| Project duration | 100 working days |
| Demo properties | 30 total, 5 with 3D |

### Tech stack one-liner

> "React TypeScript frontend, FastAPI Python backend, PostgreSQL with PostGIS, Redis cache, Docker Compose on AWS Lightsail, OpenAI GPT-4o-mini for search, Mapbox GL JS for maps, Three.js for 3D."

### Core value proposition one-liner

> "PropVision adds AI search, neighborhood livability scores, and 3D property walkthroughs to existing Uzbek real estate platforms via a REST API or embeddable widget — no rebuild required."

---

## Part 5 — Presentation Timing Breakdown

```
00:00 – 01:00  Opening + framing (what this is and is NOT)
01:00 – 03:00  Problem: market context + 3 specific gaps
03:00 – 05:00  Solution: 4 core capabilities + integration model
05:00 – 08:00  Architecture: frontend → backend → DB → infra
08:00 – 11:00  AI search: full pipeline walkthrough
11:00 – 13:00  Comfort analytics: scoring logic + data sources
13:00 – 15:00  3D reconstruction: pipeline + trade-offs
15:00 – 17:00  Results: metrics table, all 17 success criteria met
17:00 – 18:00  Limitations (be honest here — professors respect it)
18:00 – 19:00  Future roadmap
19:00 – 20:00  Closing + open for questions
```

---

## Part 6 — Live Demo Checklist

Before the presentation starts, verify:

- [ ] Docker containers are running: `docker-compose ps`
- [ ] Frontend loads at `http://localhost:53000`
- [ ] API docs accessible at `http://localhost:50080/api/v1/docs`
- [ ] At least one AI search works end-to-end
- [ ] Map loads with property markers
- [ ] At least one property has a comfort score (radar chart visible)
- [ ] At least one property has a 3D model loaded
- [ ] Admin panel accessible

**Demo route (5-minute path):**
1. Open map → point out 3D buildings, dark theme, clustering
2. Click a property → show detail panel, comfort radar
3. Type a natural language search → show map flying to result
4. Open a property with 3D model → orbit around it
5. Open API docs → show one endpoint live

---

*Good luck. You built a lot — present it with confidence.*
