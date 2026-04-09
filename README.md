# PropVision.AI

**AI-Powered Real Estate Visualization & Intelligence Layer for Uzbekistan**

[![CI Pipeline](https://github.com/propvision-ai/propvision/actions/workflows/ci.yml/badge.svg)](https://github.com/propvision-ai/propvision/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)]()

> A B2B platform that transforms flat 2D property listings into immersive, data-rich experiences with interactive maps, AI-powered natural language search, comfort analytics, and 3D property models.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Nginx (SSL/Proxy)                  │
├───────────────────────┬──────────────────────────────┤
│   React + TypeScript  │    FastAPI (Python 3.11)     │
│   Mapbox GL JS v3     │    PostgreSQL 16 + PostGIS   │
│   Three.js (R3F)      │    Redis 7                   │
│   Recharts            │    OpenAI GPT-4o-mini        │
│   Framer Motion       │    Luma AI / COLMAP          │
└───────────────────────┴──────────────────────────────┘
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗺️ **Interactive Map** | Dark-themed Mapbox GL JS map with 3D buildings, property markers with price badges, and comfort heatmap overlay |
| 🤖 **AI Search** | Natural language property search in English, Russian, and Uzbek using OpenAI GPT-4o-mini with RAG glossary (200+ terms) |
| 📊 **Comfort Analytics** | 5-axis livability scores (transport, shopping, education, green space, safety) computed from OSM + Google Places POI data |
| 🏠 **3D Property Viewer** | Photo-to-3D reconstruction pipeline producing browser-viewable GLB models via Three.js |
| 🔌 **Embeddable Widget** | 2-line JavaScript embed for partner platforms with theming support |
| 📈 **Analytics Dashboard** | API usage metrics, search query analytics, and district comfort comparisons |

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- API keys: [OpenAI](https://platform.openai.com), [Mapbox](https://mapbox.com), [Google Places](https://console.cloud.google.com)

### Setup

```bash
# Clone the repository
git clone https://github.com/propvision-ai/propvision.git
cd propvision

# Create .env file
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Seed demo data (30 properties across 6 Tashkent districts)
docker-compose exec api python -m scripts.seed_demo_data

# Fetch POI data from OpenStreetMap
docker-compose exec api python -c "
import asyncio
from app.database import async_session_factory
from app.services.poi_fetcher import POIFetcherService
async def fetch():
    async with async_session_factory() as db:
        svc = POIFetcherService(db)
        await svc.fetch_osm_pois()
        await db.commit()
asyncio.run(fetch())
"
```

### Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/api/v1/docs |
| API Docs (ReDoc) | http://localhost:8000/api/v1/redoc |
| Health Check | http://localhost:8000/api/v1/health |

### Demo API Key
```
pv_demo_1234567890abcdef
```

## 📁 Project Structure

```
prop-vision-ai/
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/                 # Route handlers + middleware
│   │   │   ├── routes/          # properties, search, comfort, 3d, analytics
│   │   │   ├── dependencies.py  # Auth + rate limiting
│   │   │   └── middleware.py    # Request logging
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── services/            # Business logic services
│   │   │   ├── property_service.py
│   │   │   ├── ai_search_service.py
│   │   │   ├── comfort_service.py
│   │   │   ├── reconstruction_service.py
│   │   │   ├── poi_fetcher.py
│   │   │   └── rag_context.py
│   │   ├── data/                # RAG glossary (200+ Uzbek terms)
│   │   ├── tasks/               # Cron background tasks
│   │   ├── config.py            # Pydantic BaseSettings
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   └── main.py              # FastAPI application entry
│   ├── scripts/                 # Data seeding scripts
│   ├── tests/                   # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map/             # MapView (Mapbox GL JS)
│   │   │   ├── Search/          # AISearchBar, SearchResults
│   │   │   ├── Property/        # PropertyPanel, ThreeViewer
│   │   │   └── Comfort/         # ComfortRadar (Recharts)
│   │   ├── api/                 # Axios client
│   │   ├── hooks/               # React Query hooks
│   │   ├── types/               # TypeScript definitions
│   │   └── config.ts            # App configuration
│   ├── public/
│   │   └── widget.js            # Embeddable widget script
│   ├── Dockerfile
│   └── package.json
├── infra/
│   └── nginx/                   # Nginx reverse proxy config
├── docs/                        # Project documentation
│   ├── PROJECT_RATIONALE.md
│   ├── OBJECTIVES.md
│   ├── SCOPE_AND_DELIVERABLES.md
│   ├── METHODOLOGY.md
│   ├── ARCHITECTURE.md
│   ├── API_DOCUMENTATION.md
│   ├── INTEGRATION_GUIDE.md
│   ├── PROJECT_PLAN.md
│   ├── RISK_REGISTER.md
│   ├── SCALING_ROADMAP.md
│   ├── LIMITATIONS.md
│   └── ANALYTICAL_FRAMEWORKS.md
├── .github/workflows/ci.yml    # GitHub Actions CI/CD
├── docker-compose.yml
├── openapi.yaml                 # OpenAPI 3.0 specification
└── README.md
```

## 🧪 Testing

```bash
# Backend unit and integration tests
docker-compose exec api pytest tests/ -v

# Frontend type checking
docker-compose exec frontend npx tsc --noEmit

# Frontend linting
docker-compose exec frontend npx eslint src/ --ext .ts,.tsx
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Project Rationale](docs/PROJECT_RATIONALE.md) | Problem statement, market analysis, value proposition |
| [Architecture](docs/ARCHITECTURE.md) | System diagrams, database schema, API specification |
| [API Documentation](docs/API_DOCUMENTATION.md) | Complete endpoint reference with examples |
| [Integration Guide](docs/INTEGRATION_GUIDE.md) | Partner developer integration instructions |
| [Project Plan](docs/PROJECT_PLAN.md) | 100-day development timeline |
| [Risk Register](docs/RISK_REGISTER.md) | 12 risks with mitigation strategies |
| [Scaling Roadmap](docs/SCALING_ROADMAP.md) | From Lightsail to EKS scaling path |
| [ADRs](docs/ARCHITECTURE_DECISION_RECORDS.md) | Technology selection rationale |

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript 5, Vite 6 |
| Map | Mapbox GL JS v3, react-map-gl |
| 3D Viewer | Three.js, @react-three/fiber |
| Charts | Recharts |
| Animation | Framer Motion |
| Backend | FastAPI, Python 3.11 |
| ORM | SQLAlchemy 2.0 (async), GeoAlchemy2 |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Cache | Redis 7 |
| AI | OpenAI GPT-4o-mini (structured output) |
| 3D Reconstruction | Luma AI API / COLMAP (fallback) |
| POI Data | OpenStreetMap Overpass API, Google Places API |
| Deployment | Docker Compose, Nginx, AWS Lightsail |
| CI/CD | GitHub Actions |

## 📄 License

Proprietary — © 2026 PropVision.AI. All rights reserved.
