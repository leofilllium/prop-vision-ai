# 🤖 PropVision.AI: Developer & AI Context Guide

This document provides a "mental model" of the PropVision.AI codebase for AI coding assistants (**Antigravity, Claude Code, Copilot, Codex**). Use this to understand the project's purpose, core logic, and coding patterns without scanning every file.

---

## 🎯 Project Mission
**PropVision.AI** is a B2B real estate intelligence platform for Uzbekistan. It transforms 2D listings into 3D, data-rich experiences using:
1. **Natural Language Search**: Multilingual (EN/RU/UZ) property search via GPT-4o-mini + RAG.
2. **Comfort Analytics**: 5-axis livability scoring based on OpenStreetMap POI data.
3. **Immersive 3D**: Photo-to-3D reconstruction (Meshy AI) and cinematic video walkthroughs.

---

## 🏗️ Technical Architecture (AI Mental Model)

### Backend: FastAPI + PostgreSQL/PostGIS
- **Database**: PostgreSQL 16 with **PostGIS** for spatial queries (SRID 4326).
- **ORM**: SQLAlchemy 2.0 (Async) with **GeoAlchemy2**.
- **AI Models**: OpenAI GPT-4o-mini for query parsing and structured output.
- **3D Pipeline**: Integration with [Meshy AI](https://meshy.ai) for 3D model generation.
- **Data Source**: OpenStreetMap (OSM) Overpass API for POI (Point of Interest) discovery.

### Frontend: React + Mapbox v3 + Three.js
- **Map**: Mapbox GL JS v3 with custom 3D building layers and proximity heatmaps.
- **3D Viewer**: **react-three-fiber** (R3F) for viewing GLB models.
- **Styling**: Vanilla CSS / Tailwind (if requested) with Framer Motion for high-fidelity animations.

---

## 🧬 Core Domain Models & Logic

### 1. Property Listing (`backend/app/models/property.py`)
- **Spatial**: Stored as a PostGIS `Geometry(POINT, 4326)`.
- **Media**: Photos are JSONB arrays; `model_3d_url` and `video_walkthrough_url` hold S3/External links.
- **Status**: `reconstruction_status` (pending, processing, completed, failed).

### 2. AI Search Pipeline (`backend/app/services/ai_search_service.py`)
- **Process**: `NL Query` → `GPT-4o-mini + RAG Glossary` → `Structured Filters` → `PostGIS Query`.
- **RAG Context**: Uses `backend/app/data/uzbek_realestate_glossary.json` to bridge Uzbek terms (e.g., *hovli* → house with yard) to English filter keys.
- **Spatial Filter**: Uses `ST_DWithin` to find properties near specific POIs (metro, parks).

### 3. Comfort Analytics (`backend/app/services/comfort_service.py`)
- **5-Axis Score**: Transport, Shopping, Education, Greenery, Safety.
- **Algorithm**: Counts POIs within specific radii (weighted) and normalizes to a 0-100 scale.
- **Storage**: Each property has a 1:1 relationship with `ComfortScore`.

---

## 📏 Implicit Conventions & Rules

- **Coordinates**: Always (Latitude, Longitude) in decimal degrees.
- **PostGIS SRID**: 4326 (WGS84) for storage; transform to 3857 for distance calculations in meters.
- **Currency**: Primary currency is **USD**. Conversion to UZS happens on the frontend if needed.
- **Language**: Backend is locale-agnostic; AI services handle triple-language (EN/RU/UZ) query parsing.
- **Async First**: All backend database I/O and external API calls (OpenAI, Meshy) MUST be `async`.

---

## 🗺️ High-Importance File Map (Start Here)

| Feature area | Key Files for AI to Read |
|:---|:---|
| **API Entry** | `backend/app/main.py`, `backend/app/api/api_v1/api.py` |
| **Search Engine** | `backend/app/services/ai_search_service.py`, `backend/app/schemas/search.py` |
| **3D / Video** | `backend/app/services/reconstruction_service.py`, `backend/app/services/video_walkthrough_service.py` |
| **Data Schema** | `backend/app/models/property.py`, `backend/app/models/comfort.py` |
| **Frontend Map**| `frontend/src/components/Map/MapView.tsx`, `frontend/src/hooks/useProperties.ts` |

---

## 🛠️ How-To for AI (Coding Patterns)

### Adding a new Database Model
1. Define in `backend/app/models/`.
2. Inherit from `Base` (NOT `MappedAsDataclass`).
3. Use `Mapped` and `mapped_column` for SQLAlchemy 2.0 style.
4. Run `alembic revision --autogenerate -m "description"`.

### Adding a new AI Service
1. Create service in `backend/app/services/`.
2. Inject `AsyncSession` in `__init__`.
3. Use `app.config.get_settings()` for API keys.
4. Return Pydantic schemas (from `backend/app/schemas/`).

---

> [!TIP]
> When adding features to the search engine, always check the **Glossary JSON** for relevant cultural or linguistic terms in Uzbekistan to update the AI prompt.
