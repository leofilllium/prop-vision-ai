# Architecture Decision Records (ADRs)

## ADR-001: React + TypeScript over Angular

**Status:** Accepted  
**Date:** 2026-03-28  
**Context:** Need to choose a frontend framework for the PropVision.AI web application that integrates with Mapbox GL JS, Three.js (WebGL 3D rendering), and Recharts.

**Decision:** React 18 with TypeScript 5.

**Rationale:**
- **Ecosystem compatibility:** Mapbox GL JS has first-class React wrappers (`react-map-gl`). Three.js has a mature React integration (`@react-three/fiber` and `@react-three/drei`). Recharts is built natively for React. Angular requires custom wrappers or imperative integration for all three libraries.
- **Component model:** React's function components with hooks map naturally to the PropVision UI: `useProperties()` for data fetching, `useSearch()` for AI search state, `useComfort()` for score data. Angular's dependency injection and service-based architecture adds unnecessary complexity for a single-page application with 15–20 components.
- **Developer ecosystem:** React has a larger npm ecosystem, more Stack Overflow answers, and more third-party component libraries relevant to mapping and 3D visualization.
- **TypeScript integration:** Both React and Angular support TypeScript. React's TypeScript support has matured significantly with proper generic component typing and hook typing.
- **Bundle size:** React 18 (core + react-dom): ~42 KB gzipped. Angular 17: ~90 KB gzipped. For an MVP targeting 4G connections in Uzbekistan, smaller bundle size matters.

**Alternatives considered:**
- **Angular 17:** Stronger opinionation (built-in routing, forms, HTTP client) but worse ecosystem compatibility with Mapbox/Three.js and larger bundle size.
- **Vue 3:** Good middle ground but weaker Three.js ecosystem (no equivalent to react-three-fiber) and smaller community for geospatial applications.
- **Svelte/SvelteKit:** Excellent performance but immature ecosystem for Mapbox and Three.js integration.

---

## ADR-002: FastAPI over Django / Express.js

**Status:** Accepted  
**Date:** 2026-03-28  
**Context:** Need a backend framework that supports async APIs, AI/ML library integration (OpenAI SDK), geospatial queries (PostGIS via SQLAlchemy), and auto-generated API documentation.

**Decision:** FastAPI (Python 3.11).

**Rationale:**
- **Async native:** FastAPI is built on Starlette (ASGI) with native `async/await` support. The PropVision backend makes concurrent external API calls (OpenAI, Luma AI, Google Places, OSM Overpass) — async Python handlers can make these calls concurrently without blocking.
- **Auto-generated OpenAPI docs:** FastAPI generates an interactive Swagger UI at `/docs` automatically from Pydantic models. This eliminates manual API documentation drift — the docs always match the code.
- **Pydantic v2 integration:** Request and response validation via Pydantic models catches data type errors at the API boundary. GeoJSON serialization from GeoAlchemy2 `WKBElement` objects requires custom Pydantic serializers — FastAPI's dependency injection and model validation make this straightforward.
- **Python AI/ML ecosystem:** OpenAI's SDK is Python-first. GeoAlchemy2, Shapely, and GeoPandas are Python libraries. COLMAP (fallback 3D reconstruction) has Python bindings. Choosing Python eliminates language-boundary complexity for AI and geospatial services.
- **Performance:** FastAPI with Uvicorn achieves ~15,000–30,000 requests/second for simple endpoints (comparable to Express.js). For the MVP's 100-concurrent-user target, this is more than sufficient.

**Alternatives considered:**
- **Django + DRF:** More batteries included (ORM, admin, auth), but synchronous by default. Django's async support (ASGI) is maturing but not as ergonomic as FastAPI's. Django REST Framework's serializer pattern is verbose compared to Pydantic models. GeoDjango provides excellent PostGIS integration, but GeoAlchemy2 with SQLAlchemy provides equivalent functionality with more flexibility.
- **Express.js (Node.js):** JavaScript/TypeScript on both frontend and backend (full stack JS). However, Node.js lacks mature geospatial libraries — PostGIS integration requires raw SQL or less-maintained ORMs (TypeORM, Prisma with limited PostGIS support). OpenAI's Node.js SDK exists but the Python SDK is more feature-complete.
- **Go (Gin/Echo):** Excellent performance but weak AI/ML library ecosystem. No equivalent to GeoAlchemy2. Would require FFI bridges or HTTP calls to Python services for AI functionality.

---

## ADR-003: Mapbox GL JS over Google Maps / Leaflet

**Status:** Accepted  
**Date:** 2026-03-28  
**Context:** Need a web mapping library that supports custom 3D rendering, building extrusions, heatmap layers, custom markers with clustering, and smooth animations (fly-to).

**Decision:** Mapbox GL JS v3.

**Rationale:**
- **3D capabilities:** Mapbox GL JS natively supports 3D terrain, building extrusions, and custom WebGL layers (via `CustomLayerInterface`). This enables rendering 3D building outlines on the map and potentially overlaying Three.js 3D models directly on the map in future versions. Google Maps and Leaflet have limited or no native 3D support.
- **Custom styling:** Mapbox Studio allows complete control over map style — dark mode, custom colors, hidden labels, emphasized roads. Google Maps styling is more limited. Leaflet relies on third-party tile providers with limited style customization.
- **Heatmap layer:** Mapbox has a built-in `heatmap` layer type ideal for visualizing comfort score distributions. Google Maps requires the `visualization` library add-on.
- **Performance:** Mapbox GL JS renders using WebGL, providing smooth 60 FPS interactions even with thousands of markers (via clustering). Leaflet uses DOM-based rendering which degrades with many markers.
- **Free tier:** Mapbox provides 50,000 free map loads per month — more than sufficient for the MVP and early pilot. Google Maps provides $200/month credit (~28,000 map loads).
- **React integration:** `react-map-gl` (maintained by the Mapbox/Vis.gl team) provides idiomatic React components for Mapbox GL JS.

**Alternatives considered:**
- **Google Maps Platform:** More recognizable brand, better global street-level imagery, but weaker 3D/custom rendering, more restrictive terms of service (must display Google branding), and higher cost at scale.
- **Leaflet:** Open source, free, lightweight. But no WebGL rendering (DOM-based, poor performance with many markers), no native 3D support, no heatmap layer without plugins. Suitable for simple maps but insufficient for PropVision's visualization requirements.
- **MapLibre GL JS:** Open-source fork of Mapbox GL JS v1. Free, no token required, WebGL-based. However, it lacks Mapbox v3's latest features (Standard Style, Mapbox Terrain 3D, advanced lighting). Would be a viable fallback if Mapbox pricing becomes prohibitive.

---

## ADR-004: Luma AI over Matterport / Self-hosted COLMAP

**Status:** Accepted (with caveat)  
**Date:** 2026-03-28  
**Context:** Need a photo-to-3D reconstruction solution that accepts 8–15 smartphone photos and produces a web-viewable 3D model (GLB format), without requiring specialized hardware or GPU infrastructure on the server.

**Decision:** Luma AI API as primary provider, with COLMAP as self-hosted fallback.

**Caveat:** As of March 2026, Luma AI's public API documentation primarily covers video/image generation (Dream Machine), not photo-to-3D reconstruction. The 3D reconstruction capability (Genie) may require contacting Luma AI for enterprise API access. If Luma AI access is not available, the implementation falls back to COLMAP or Tripo AI as alternatives.

**Rationale:**
- **No GPU required on server:** Cloud-based reconstruction eliminates the need for expensive GPU instances on AWS. The PropVision server remains a $40/month Lightsail instance (CPU only).
- **Quality vs. cost trade-off:** AI-powered reconstruction from smartphone photos produces prototype-grade models sufficient for spatial layout understanding. This is not architectural visualization — it's "good enough" 3D previews at near-zero marginal cost per property.
- **Processing time:** Cloud APIs typically process a 3D reconstruction in 5–20 minutes, which is acceptable for an asynchronous workflow (upload photos → wait → view model).
- **GLB output:** Both Luma AI and COLMAP produce output compatible with Three.js (GLB/glTF or OBJ → converted to GLB).

**Alternatives considered:**
- **Matterport:** Industry-leading quality but requires a $400+ Matterport camera and trained operator. Not scalable for thousands of listings where sellers use smartphones. Per-property cost: $50–200 for professional capture. Suitable as a premium tier post-MVP, not for the default pipeline.
- **COLMAP (self-hosted only):** Open-source, no API cost, full control. However, requires GPU for reasonable processing speed (CPU-only: 30–120 minutes per property). Running on Lightsail (CPU only) would result in very slow processing. Suitable as a fallback, not a primary solution.
- **Tripo AI:** Well-documented REST API for image-to-3D generation. Strong alternative if Luma AI access is unavailable. Production-ready output with clean topology. Will be used as the practical primary implementation.
- **Gaussian Splatting:** Cutting-edge technology (superior visual quality to mesh-based approaches) but not yet production-ready for automated web pipelines. GLB output format is not standard for splat renderers. Consider for post-MVP upgrade.

---

## ADR-005: PostgreSQL + PostGIS over MongoDB / Elasticsearch

**Status:** Accepted  
**Date:** 2026-03-28  
**Context:** Need a database that supports geospatial queries (proximity, bounding box, nearest neighbor), JSON storage (photos array, field mappings), full-text search, and transactional integrity.

**Decision:** PostgreSQL 16 with PostGIS 3.4 extension.

**Rationale:**
- **Geospatial queries:** PostGIS is the industry standard for spatial databases. Functions used by PropVision: `ST_DWithin(geometry, geometry, distance)` for proximity queries (find POIs within X meters), `ST_Distance(geometry, geometry)` for nearest-neighbor ranking, `ST_MakeEnvelope(xmin, ymin, xmax, ymax, srid)` for bounding box filtering, GiST spatial indexes for sub-millisecond query performance.
- **JSON support:** PostgreSQL's `JSONB` type provides indexed, queryable JSON storage — used for `photos` (array of URLs), `field_mapping` (per-partner configuration), `parsed_filters` (search query results), and `raw_data` (comfort score computation details). No need for a separate document store.
- **Transactional integrity:** ACID compliance ensures that property ingestion, comfort score updates, and API log writes are atomic. MongoDB's eventual consistency model could lead to inconsistencies between properties and their comfort scores.
- **Mature ecosystem:** SQLAlchemy + GeoAlchemy2 provide a well-maintained Python ORM. Alembic handles schema migrations. The PostgreSQL + Python ecosystem is the most mature option for geospatial web applications.
- **Single database:** PostgreSQL handles relational data (properties, partners, logs), geospatial data (locations, boundaries), and document data (JSON fields) in a single database. No need to operate multiple database engines.

**Alternatives considered:**
- **MongoDB:** Flexible schema, native JSON. Has geospatial queries (`$geoNear`, `$geoWithin`) but they are less powerful and less performant than PostGIS for complex spatial operations. Lacks ACID transactions across collections (multi-document transactions added in 4.0 but with performance overhead). Unnecessary flexibility for a schema that is well-defined.
- **Elasticsearch:** Excellent for full-text search and geo-distance queries. However, it's not a primary database — it's a search index. Would need to run alongside PostgreSQL, adding operational complexity. The MVP has only 30 properties — Elasticsearch's value emerges at scale (100K+ documents).
- **SQLite + SpatiaLite:** Simpler to operate (no server process) but lacks concurrent write support, connection pooling, and production-grade reliability. Not suitable for a web application serving concurrent API requests.

---

## ADR-006: Docker Compose over Kubernetes / Bare Metal

**Status:** Accepted  
**Date:** 2026-03-28  
**Context:** Need a deployment strategy for 5 services (FastAPI, React/Nginx, PostgreSQL, Redis, Nginx reverse proxy) on a single AWS Lightsail instance.

**Decision:** Docker Compose on a single Lightsail instance.

**Rationale:**
- **Simplicity:** Docker Compose is a single YAML file that defines all 5 services, their networking, volumes, and health checks. `docker-compose up -d` starts everything. `docker-compose down` stops everything. No Kubernetes manifests, Helm charts, or cluster management required.
- **Reproducibility:** The same `docker-compose.yml` runs identically on a developer's laptop and on the production Lightsail instance. No "works on my machine" issues.
- **Resource efficiency:** Docker Compose has minimal overhead — containers share the host kernel directly. Kubernetes has a control plane overhead (etcd, API server, scheduler, controller manager) that would consume 500 MB–1 GB of the 4 GB available memory.
- **Cost:** $0 additional cost. Docker and Docker Compose are free. Kubernetes would require either self-managed K3s (complex to operate) or a managed service (EKS: $73/month for the control plane alone).
- **Scaling path:** The architecture is containerized, making migration from Docker Compose to Kubernetes straightforward when scaling is needed. The same Dockerfiles work with ECS, EKS, or any container orchestrator.

**Migration trigger:** When the application needs to handle >500 concurrent users or requires multi-instance deployment for high availability, migrate to AWS ECS (Fargate) or Kubernetes. This decision is documented in `SCALING_ROADMAP.md`.
