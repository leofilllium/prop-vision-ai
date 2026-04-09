# API Documentation

## Base URL

```
https://api.propvision.ai/api/v1
```

## Authentication

All endpoints require an API key passed via the `X-API-Key` header:

```
X-API-Key: pv_live_a1b2c3d4e5f6g7h8i9j0
```

API keys are issued per partner. Contact PropVision.AI to obtain a key.

## Rate Limiting

- **Limit**: 100 requests per minute per API key
- **Headers**: Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **Exceeded**: Returns `429 Too Many Requests` with `Retry-After` header

## Error Response Format

All errors return a consistent JSON structure:

```json
{
    "detail": "Human-readable error description",
    "error_code": "MACHINE_READABLE_ERROR_CODE",
    "status_code": 422
}
```

| Status Code | Meaning |
|------------|---------|
| 400 | Bad Request — malformed request body |
| 401 | Unauthorized — invalid or missing API key |
| 404 | Not Found — resource does not exist |
| 422 | Unprocessable Entity — validation error |
| 429 | Too Many Requests — rate limit exceeded |
| 500 | Internal Server Error |

---

## Endpoints

### 1. POST /api/v1/properties

**Create a new property listing.**

Partners push property data to PropVision. Fields are mapped using the partner's `field_mapping` configuration.

**Request:**
```json
{
    "title": "Modern 3-room apartment in Yunusabad",
    "description": "Bright apartment with renovated kitchen and balcony. 5 minutes walk to Buyuk Ipak Yuli metro station.",
    "price": 68000,
    "currency": "USD",
    "rooms": 3,
    "area_sqm": 85.5,
    "floor": 7,
    "total_floors": 12,
    "district": "Yunusabad",
    "address": "Yunusabad district, Amir Temur street 45",
    "latitude": 41.3385,
    "longitude": 69.2856,
    "photos": [
        "https://partner-cdn.example.com/photos/apt-001/living-room.jpg",
        "https://partner-cdn.example.com/photos/apt-001/kitchen.jpg",
        "https://partner-cdn.example.com/photos/apt-001/bedroom-1.jpg"
    ],
    "external_id": "partner-apt-001"
}
```

**Response (201 Created):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Modern 3-room apartment in Yunusabad",
    "price": 68000,
    "currency": "USD",
    "rooms": 3,
    "area_sqm": 85.5,
    "district": "Yunusabad",
    "location": {
        "type": "Point",
        "coordinates": [69.2856, 41.3385]
    },
    "photos": [
        "https://partner-cdn.example.com/photos/apt-001/living-room.jpg",
        "https://partner-cdn.example.com/photos/apt-001/kitchen.jpg",
        "https://partner-cdn.example.com/photos/apt-001/bedroom-1.jpg"
    ],
    "model_3d_url": null,
    "partner_id": "660e8400-e29b-41d4-a716-446655440001",
    "created_at": "2026-03-28T10:00:00Z"
}
```

---

### 2. GET /api/v1/properties

**List and filter properties.**

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `district` | string | Filter by district name | `Yunusabad` |
| `min_price` | float | Minimum price (USD) | `30000` |
| `max_price` | float | Maximum price (USD) | `80000` |
| `rooms` | int | Exact room count | `3` |
| `min_rooms` | int | Minimum room count | `2` |
| `max_rooms` | int | Maximum room count | `4` |
| `bbox` | string | Bounding box: `sw_lng,sw_lat,ne_lng,ne_lat` | `69.1,41.2,69.4,41.4` |
| `limit` | int | Max results (default 50, max 100) | `20` |
| `offset` | int | Pagination offset (default 0) | `20` |
| `sort_by` | string | Sort field: `price`, `rooms`, `created_at` | `price` |
| `sort_order` | string | `asc` or `desc` (default `desc`) | `asc` |

**Request:**
```
GET /api/v1/properties?district=Yunusabad&min_price=40000&max_price=80000&rooms=3&limit=10
```

**Response (200 OK):**
```json
{
    "total": 5,
    "limit": 10,
    "offset": 0,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Modern 3-room apartment in Yunusabad",
            "price": 68000,
            "currency": "USD",
            "rooms": 3,
            "area_sqm": 85.5,
            "floor": 7,
            "total_floors": 12,
            "district": "Yunusabad",
            "address": "Yunusabad district, Amir Temur street 45",
            "location": {
                "type": "Point",
                "coordinates": [69.2856, 41.3385]
            },
            "photos": ["https://..."],
            "model_3d_url": null,
            "comfort_score": {
                "overall_score": 78.5,
                "data_confidence": "HIGH"
            },
            "created_at": "2026-03-28T10:00:00Z"
        }
    ]
}
```

---

### 3. GET /api/v1/properties/{id}

**Get a single property with full comfort scores.**

**Response (200 OK):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Modern 3-room apartment in Yunusabad",
    "description": "Bright apartment with renovated kitchen...",
    "price": 68000,
    "currency": "USD",
    "rooms": 3,
    "area_sqm": 85.5,
    "floor": 7,
    "total_floors": 12,
    "district": "Yunusabad",
    "address": "Yunusabad district, Amir Temur street 45",
    "location": {
        "type": "Point",
        "coordinates": [69.2856, 41.3385]
    },
    "photos": ["https://..."],
    "model_3d_url": "https://propvision-models.s3.amazonaws.com/models/550e8400.glb",
    "comfort_scores": {
        "transport_score": 85.0,
        "shopping_score": 72.5,
        "education_score": 68.0,
        "green_space_score": 55.0,
        "safety_score": 74.0,
        "overall_score": 73.5,
        "data_confidence": "HIGH",
        "computed_at": "2026-03-28T01:00:00Z"
    },
    "partner_id": "660e8400-e29b-41d4-a716-446655440001",
    "created_at": "2026-03-28T10:00:00Z",
    "updated_at": "2026-03-28T10:00:00Z"
}
```

---

### 4. POST /api/v1/search

**AI-powered natural language property search.**

**Request:**
```json
{
    "query": "2-room flat near metro under $70,000"
}
```

**Response (200 OK):**
```json
{
    "query": "2-room flat near metro under $70,000",
    "parsed_filters": {
        "rooms": 2,
        "max_price": 70000,
        "proximity_to": "metro_station",
        "max_distance_m": 1000,
        "district": null,
        "min_area_sqm": null,
        "max_area_sqm": null
    },
    "total": 8,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "title": "Cozy 2-room apartment near Buyuk Ipak Yuli",
            "price": 52000,
            "rooms": 2,
            "area_sqm": 62.0,
            "district": "Yunusabad",
            "location": {
                "type": "Point",
                "coordinates": [69.2790, 41.3112]
            },
            "photos": ["https://..."],
            "comfort_score": {
                "overall_score": 82.0,
                "data_confidence": "HIGH"
            },
            "distance_to_poi_m": 350
        }
    ]
}
```

**Supported query patterns:**
- Room count: "2 rooms", "3-room", "3 xonali", "двухкомнатная"
- Price range: "under $70k", "$40,000–$60,000", "до 80 тысяч", "50 ming dollar"
- District: "Yunusabad", "Chilanzar", "Mirzo Ulugbek", "Чиланзар"
- Proximity: "near metro", "close to a park", "рядом с метро", "metro yaqinida"
- Area: "80 square meters", "80 m²", "80 кв.м"

---

### 5. GET /api/v1/comfort/{property_id}

**Get detailed comfort score breakdown for a property.**

**Response (200 OK):**
```json
{
    "property_id": "550e8400-e29b-41d4-a716-446655440000",
    "scores": {
        "transport": {
            "score": 85.0,
            "details": {
                "metro_stations_within_1km": 2,
                "bus_stops_within_1km": 8,
                "nearest_metro_distance_m": 320,
                "nearest_bus_stop_distance_m": 85
            }
        },
        "shopping": {
            "score": 72.5,
            "details": {
                "supermarkets_within_800m": 3,
                "convenience_stores_within_800m": 5,
                "markets_within_800m": 1,
                "nearest_supermarket_distance_m": 210
            }
        },
        "education": {
            "score": 68.0,
            "details": {
                "schools_within_1500m": 4,
                "kindergartens_within_1500m": 2,
                "universities_within_1500m": 0,
                "nearest_school_distance_m": 450
            }
        },
        "green_space": {
            "score": 55.0,
            "details": {
                "parks_within_1km": 1,
                "gardens_within_1km": 0,
                "nearest_park_distance_m": 680
            }
        },
        "safety": {
            "score": 74.0,
            "details": {
                "street_lamps_within_500m": 15,
                "police_stations_within_1km": 1,
                "hospitals_within_1km": 1,
                "nearest_hospital_distance_m": 780
            }
        }
    },
    "overall_score": 73.5,
    "data_confidence": "HIGH",
    "weights": {
        "transport": 0.25,
        "shopping": 0.20,
        "education": 0.20,
        "green_space": 0.15,
        "safety": 0.20
    },
    "computed_at": "2026-03-28T01:00:00Z"
}
```

---

### 6. POST /api/v1/3d/upload

**Upload photos for 3D reconstruction.**

**Request (multipart/form-data):**
```
POST /api/v1/3d/upload
Content-Type: multipart/form-data

property_id: 550e8400-e29b-41d4-a716-446655440000
photos: [8–15 JPEG/PNG files, max 10 MB each]
```

**Response (202 Accepted):**
```json
{
    "property_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_id": "recon-job-abc123",
    "status": "pending",
    "message": "Reconstruction job submitted. 12 photos received. Estimated processing time: 10–20 minutes.",
    "status_url": "/api/v1/3d/550e8400-e29b-41d4-a716-446655440000/status"
}
```

**Validation errors:**
- Fewer than 8 or more than 15 photos → 422
- Non-JPEG/PNG file → 422
- Single file exceeds 10 MB → 422
- Property not found → 404

---

### 7. GET /api/v1/3d/{property_id}/status

**Check 3D reconstruction job status.**

**Response (200 OK) — Processing:**
```json
{
    "property_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_id": "recon-job-abc123",
    "status": "processing",
    "progress_percent": 45,
    "estimated_remaining_seconds": 480,
    "created_at": "2026-03-28T10:00:00Z"
}
```

**Response (200 OK) — Completed:**
```json
{
    "property_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_id": "recon-job-abc123",
    "status": "completed",
    "model_url": "https://propvision-models.s3.amazonaws.com/models/550e8400.glb",
    "model_size_bytes": 8245760,
    "processing_time_seconds": 840,
    "created_at": "2026-03-28T10:00:00Z",
    "completed_at": "2026-03-28T10:14:00Z"
}
```

---

### 8. GET /api/v1/analytics/dashboard

**Get engagement metrics for the internal analytics dashboard.**

**Response (200 OK):**
```json
{
    "api_calls": {
        "daily": [
            {"date": "2026-03-27", "count": 1250},
            {"date": "2026-03-26", "count": 1180},
            {"date": "2026-03-25", "count": 980}
        ],
        "total_last_30_days": 28500
    },
    "top_queries": [
        {"query": "2 rooms near metro Yunusabad", "count": 45},
        {"query": "3-room apartment Chilanzar", "count": 38},
        {"query": "cheap flat Sergeli", "count": 31}
    ],
    "comfort_scores_by_district": [
        {"district": "Yunusabad", "avg_overall_score": 78.5},
        {"district": "Mirzo Ulugbek", "avg_overall_score": 75.2},
        {"district": "Chilanzar", "avg_overall_score": 72.8}
    ],
    "model_3d_views": {
        "total": 342,
        "last_7_days": 89
    }
}
```
