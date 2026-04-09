# Section 4 — Limitations

## 4.1 Local Geospatial Data Gaps

**(a) What the limitation is:**
OpenStreetMap (OSM) coverage in Uzbekistan is incomplete for some neighborhoods, particularly newer residential developments on the outskirts of Tashkent (e.g., parts of Sergeli, Bektemir, and newly built areas in Yashnabad). Bus stops may be unmapped, parks may lack proper boundary polygons, and street lighting data is sparse outside central districts. The Google Places API free tier limits data retrieval to 200 requests per day, which constrains the volume and freshness of POI data for shops, restaurants, and educational institutions. Most critically, **crime data, noise level measurements, and air quality indices are NOT publicly available** in Uzbekistan at neighborhood granularity — the national statistics bureau and municipal authorities do not publish this data in machine-readable formats.

**(b) Why it exists:**
OSM is a volunteer-driven project, and the mapping community in Uzbekistan is smaller than in Western European or North American cities. Government open data initiatives are still in early stages — the Uzbek government has prioritized digitalization of tax, cadastral, and business registration systems, but neighborhood-level quality-of-life data is not yet part of the open data agenda. Google Places API free tier limitations are a commercial constraint that cannot be bypassed without paying for the Standard or Premium plan.

**(c) What the concrete impact is:**
- Comfort analytics scores (especially safety score) will be **approximate or incomplete** in some areas. A property in a newly developed part of Sergeli might receive a LOW confidence safety score because there are only 1–2 relevant data points (a hospital 1.2 km away, no street lights mapped in OSM).
- Transport scores may undercount bus stops in areas where OSM volunteers haven't mapped them yet.
- Some properties may display a "Based on limited data" warning, which could reduce user confidence in the comfort analytics feature.
- The safety score is **not** a measure of actual safety — it is a proxy based on infrastructure indicators. Users must understand this distinction.

**(d) Mitigation and future solution:**
- **MVP mitigation:** Display confidence indicators on all scores. When fewer than 3 data points exist within the scoring radius, show a prominent warning: "⚠ Based on limited data — this score may not fully reflect the area." This sets user expectations transparently.
- **Short-term (6 months post-MVP):** Supplement OSM data with community-contributed POI data from partner platforms. Partner platform users can flag missing POIs (e.g., "there's a bus stop here that isn't on the map").
- **Medium-term (12 months post-MVP):** Establish data partnerships with municipal authorities (the Tashkent city administration has expressed interest in smart city initiatives) to access official transport route data, street lighting inventories, and planned infrastructure projects.
- **Long-term:** Integrate paid data sources (e.g., Google Places Premium, commercial noise/air quality monitoring APIs if they become available in Uzbekistan).

---

## 4.2 3D Reconstruction Fidelity

**(a) What the limitation is:**
AI-powered 3D reconstruction from smartphone photos (using Luma AI or COLMAP) produces **prototype-grade** 3D models, not architectural visualization quality. The output is a low-to-medium fidelity mesh with approximate textures extracted from the source photographs. Common artifacts include:
- **Holes and gaps** in surfaces, especially in areas occluded from camera angles (behind furniture, inside closets, under sinks)
- **Blurred or stretched textures** where photo resolution or angle was insufficient
- **Incorrect geometry** in complex areas (glass reflections, mirrors, transparent surfaces, thin objects like curtain rods)
- **Scale inaccuracies** — room dimensions may appear distorted by 5–15% without calibration reference points
- **Missing ceilings** — overhead surfaces are rarely captured in standard walkaround photography

**(b) Why it exists:**
Photogrammetry from uncalibrated smartphone photos is an inherently limited technique. Professional 3D scanning (Matterport, LiDAR) uses specialized hardware with calibrated sensors, structured light patterns, and known baselines to produce precise geometry. Consumer smartphone photos provide none of this calibration data. The reconstruction algorithm must infer 3D structure from 2D images using feature matching and multi-view geometry, which works well for textured surfaces with good coverage but fails for reflective, transparent, or texture-less surfaces.

**(c) What the concrete impact is:**
- Users will find the 3D preview useful for understanding **general spatial layout** (room sizes, doorway positions, room flow) but NOT for evaluating **finishes, materials, exact dimensions, or ceiling heights**.
- Some users may perceive the 3D models as "low quality" compared to Matterport-style digital twins they've seen on international platforms (Zillow, Realtor.com).
- Models with significant artifacts (large holes, distorted rooms) may create a negative impression of the property itself, not just the technology.

**(d) Mitigation and future solution:**
- **MVP mitigation:** Display a disclaimer on every 3D preview: "🔍 3D preview is approximate — generated from photos. It shows general room layout, not exact dimensions or finishes." Include a comparison note: "For a precise walkthrough, schedule a physical visit with the seller."
- **Photo quality guidance:** Provide sellers with clear photo requirements: minimum 8 photos, overlap between adjacent photos, cover every room from at least 2 angles, avoid mirrors and glass surfaces, ensure adequate lighting.
- **Post-MVP:** Integrate with professional 3D scanning services (Matterport, Polycam Pro) as a premium tier. Add mesh cleanup and hole-filling algorithms in the processing pipeline. Explore Gaussian Splatting as an alternative rendering method that may produce better visual quality from the same input photos.

---

## 4.3 AI Language Limitations

**(a) What the limitation is:**
OpenAI's GPT-4o-mini model is **not fine-tuned** for the Uzbek language (Latin or Cyrillic script). While the model has some understanding of Uzbek (it's included in the training data to a limited extent), its parsing accuracy for Uzbek-language property queries is significantly lower than for English or Russian. Specific challenges include:
- Uzbek real estate jargon may not be recognized (e.g., "xonadon" for apartment, "xona" for room)
- Uzbek district names with non-Latin characters may be misspelled or misinterpreted
- Price expressions in Uzbek (e.g., "50 ming dollar" for "50 thousand dollars") may not parse correctly
- Mixed Uzbek-Russian queries (common in everyday Uzbek speech) add complexity

**(b) Why it exists:**
GPT-4o-mini's training data is heavily weighted toward English, with good coverage of Russian but limited coverage of Uzbek. Fine-tuning a model on domain-specific Uzbek real estate data would require a labeled dataset of thousands of query-filter pairs, which doesn't exist yet. The Uzbek NLP research community is growing but hasn't produced domain-specific models for real estate.

**(c) What the concrete impact is:**
- Users querying entirely in Uzbek may get **poor or incorrect search results** — the AI might misparse "3 xonali kvartira" into wrong filter values or fail to extract the room count entirely.
- Estimated parse accuracy for Uzbek queries: 50–65% (compared to ≥85% for English/Russian).
- This limits the product's accessibility for Uzbek-dominant speakers who are less comfortable with Russian or English.

**(d) Mitigation and future solution:**
- **MVP mitigation (RAG layer):** Implement a **Retrieval-Augmented Generation** layer that provides the AI model with a local context dictionary — a structured glossary of 200+ Uzbek real estate terms injected into the system prompt. The glossary includes:
  - Room types: xona = room, yotoqxona = bedroom, oshxona = kitchen, hammom = bathroom
  - Property types: xonadon = apartment, kvartira = apartment (Russian loanword), uy = house, ofis = office
  - District names: all Tashkent districts in Uzbek, Russian, and transliterated forms
  - Price terms: ming = thousand, million = million, dollar/so'm (currency indicators)
  - Amenities: metro, avtobus = bus, maktab = school, bog' = park/garden, do'kon = shop
  - This glossary is loaded at startup and injected into every AI search prompt as few-shot examples.
- **Short-term post-MVP:** Build a labeled dataset of 500+ Uzbek property queries with expected filter outputs. Use this to evaluate and improve prompt engineering.
- **Long-term:** Fine-tune a smaller model (e.g., LLaMA 3 or Mistral) on Uzbek real estate data for self-hosted deployment, eliminating dependency on OpenAI for Uzbek queries.

---

## 4.4 Financial and Infrastructure Constraints

**(a) What the limitation is:**
The MVP runs on a **single AWS Lightsail instance** ($40/month fixed cost) with 4 GB RAM, 2 vCPU, and 80 GB SSD. This is a shared-tenancy virtual machine with no redundancy (single point of failure), no auto-scaling (fixed resources), no load balancer, and no multi-region deployment. All services (FastAPI, PostgreSQL, Redis, Nginx) run as Docker containers on this single instance, competing for the same CPU and memory resources.

**(b) Why it exists:**
This is an MVP/academic project with a minimal budget. AWS Lightsail is chosen for its predictable pricing ($40/month flat rate) and simplicity — no surprise charges, no complex IAM/VPC configuration. The total monthly cost target is ≤ $60 (including API usage).

**(c) What the concrete impact is:**
- **Capacity limit:** The system can handle approximately **100 concurrent users** before response times degrade. Under load, the bottleneck is PostgreSQL connection pooling (20 connections) and Python's asyncio event loop on 2 vCPU.
- **No high availability:** If the Lightsail instance goes down (hardware failure, kernel panic, OOM kill), the entire application is offline. No failover, no replica.
- **No automatic scaling:** A sudden traffic spike (e.g., if a partner platform features PropVision prominently) could overwhelm the instance and cause 502/503 errors.
- **Shared resources:** A heavy 3D reconstruction job (CPU-intensive COLMAP fallback) could degrade API response times for other users.

**(d) Mitigation and future solution:**
- **MVP mitigation:** Monitor resource usage with `docker stats` and set memory limits per container in Docker Compose (e.g., API: 1 GB, PostgreSQL: 1.5 GB, Redis: 256 MB, Nginx: 128 MB, Frontend: 128 MB). Configure PostgreSQL connection pooling via PgBouncer if connection limits become an issue.
- **Documented scaling path:** The `SCALING_ROADMAP.md` document details how to migrate from Lightsail to:
  - **1K users/month:** Upgrade to 8 GB Lightsail instance ($80/month), add separate Lightsail database ($15/month).
  - **10K users/month:** Migrate to AWS ECS Fargate with auto-scaling, RDS for PostgreSQL, ElastiCache for Redis (~$200–400/month).
  - **100K users/month:** Full Kubernetes (EKS) deployment with horizontal pod autoscaling, multi-AZ RDS, CloudFront CDN (~$1,000–2,000/month).

---

## 4.5 Legal and Regulatory

**(a) What the limitation is:**
Data privacy regulations in Uzbekistan are evolving. The **Law on Personal Data** (2019) establishes requirements for processing personal data, but enforcement mechanisms, specific technical standards, and cross-border data transfer rules are still being clarified. The MVP uses only publicly available data (OSM, Google Places) and does not collect any personally identifiable information (PII) from end users. However, future partner integrations involving user behavior data, search history, or property inquiry tracking will require compliance with Uzbek data protection law.

**(b) Why it exists:**
Uzbekistan's legal framework for technology companies is actively developing as part of the broader Digital Uzbekistan 2030 strategy. The regulatory environment is less mature than the EU (GDPR) or Russia (Federal Law No. 152-FZ), creating uncertainty about specific compliance requirements.

**(c) What the concrete impact is:**
- For the MVP: **minimal legal risk** — no PII collected, no user accounts, no cookies, all data sources are public.
- For post-MVP: any feature that involves user tracking, search history, or partner platform user data will require legal review to ensure compliance with Uzbek data protection law.
- Cross-border data transfer (user data flowing through OpenAI's US-based API) may face regulatory scrutiny in the future.

**(d) Mitigation and future solution:**
- **MVP mitigation:** Design the API to avoid storing any PII. API logs record partner API key and endpoint, but not end-user IP addresses or identifiers. The architecture is "privacy by design" — no user data flows through PropVision's systems.
- **Post-MVP:** Engage a local legal advisor specializing in Uzbek technology law to review the platform before any feature involving user data is launched. Prepare a Data Processing Agreement (DPA) template for partner platforms. Implement consent management if user-facing features (accounts, saved searches) are added.
- **Long-term:** Monitor the progress of Uzbekistan's data protection regulatory framework and adapt compliance measures accordingly. Consider data residency requirements (keeping data within Uzbekistan) which may be mandated for certain categories of personal data.
