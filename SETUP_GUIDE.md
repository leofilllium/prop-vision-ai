# 🏁 PropVision AI: Roadmap to Running the Application

Welcome to the PropVision AI setup guide. Follow these steps to get the complete stack running with real-world data from Tashkent.

## 🗺️ High-Level Setup Roadmap

| Phase | Goal | Key Command |
| :--- | :--- | :--- |
| **Phase 1** | 🛠️ Environment Configuration | `cp .env.example .env` |
| **Phase 2** | 🚀 Orchestration (Spin up containers) | `docker-compose up -d --build` |
| **Phase 3** | 📦 Database Integrity (Migrations) | `alembic upgrade head` |
| **Phase 4** | 📍 Data Population (POI & Marketplace) | `python -m scripts.seed_poi_data` |
| **Phase 5** | ✅ Verification & Launch | Visit `http://localhost:53000` |

---

## 🛠️ Detailed Setup Steps

### Phase 1: Environment Readiness
Ensure you have the necessary API tokens in your `.env` file. You will need:
- **OpenStreetMap (OSM)**: No key required for small volumes, but use carefully.
- **OpenAI**: For AI search and descriptive analysis.
- **Mapbox**: For frontend map rendering and backend calculation.
- **deAPI**: For video walkthrough generation.

### Phase 2: Service Initialization
Start the Docker services. This will pull the necessary images and build the local backend and frontend containers.
```bash
docker-compose up -d --build
```
> [!NOTE]
> Check container health with `docker-compose ps`.

### Phase 3 & 4: The Data "Jumpstart"
We have automated the database migrations and data seeding into a single script. Run this command to initialize the database schema and populate it with Tashkent POI data (and sync marketplace listings):

```bash
docker exec -it propvision-api bash scripts/setup_data.sh
```

**What this script does:**
1. **Migrations**: Updates the PostgreSQL schema to the latest version.
2. **POI Seed**: Fetches thousands of real-world points (Metros, Parks, Hospitals) from OpenStreetMap for the Tashkent Metro area.
3. **Marketplace Sync**: Synchronizes the latest listings from the Uybor marketplace.

---

## 🔍 Service Ports & Endpoints
After setup, the following services are available:

- **Frontend Application**: [http://localhost:53000](http://localhost:53000)
- **Nginx Reverse Proxy**: [http://localhost:50080](http://localhost:50080)
- **API Health Check**: [http://localhost:50080/health](http://localhost:50080/health)
- **PostgreSQL**: `localhost:55433`
- **Redis**: `localhost:56379`

## ⚠️ Common Issues & Tips
- **Rate Limiting**: If the OSM seed fails with a 429 error, wait a few minutes and run the setup script again.
- **CORS Errors**: Ensure `CORS_ORIGINS` in your `.env` includes `http://localhost:53000`.
- **Database Logs**: Use `docker-compose logs -f postgres` to debug database connectivity.

---
🚀 *Prop-Vision AI is now ready for analysis and visualization.*
