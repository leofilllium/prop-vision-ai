# Integration Guide for Partner Developers

## Overview

This guide explains how to integrate PropVision.AI's visualization and intelligence features into your existing real estate platform. Integration involves two parts:

1. **Data Ingestion** — Push your property listings to PropVision's API
2. **Widget Embedding** — Display PropVision's comfort analytics and 3D viewer on your property pages

**Estimated integration time: 3–5 working days.**

---

## Step 1: Get Your API Key

Contact the PropVision.AI team to receive:
- An **API key** (format: `pv_live_xxxxxxxxxxxxxxxxxxxx`)
- A **partner ID** (UUID)
- Access to the PropVision staging environment for testing

All API calls require the API key in the `X-API-Key` header:
```
X-API-Key: pv_live_a1b2c3d4e5f6g7h8i9j0
```

---

## Step 2: Configure Field Mapping

Your property data may use different field names than PropVision's internal schema. We configure a field mapping for your platform.

**PropVision's internal fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ | Property title/headline |
| `description` | string | ❌ | Full description text |
| `price` | number | ✅ | Price in specified currency |
| `currency` | string | ❌ | ISO 4217 code (default: USD) |
| `rooms` | integer | ❌ | Number of rooms |
| `area_sqm` | number | ❌ | Area in square meters |
| `floor` | integer | ❌ | Floor number |
| `total_floors` | integer | ❌ | Total floors in building |
| `district` | string | ❌ | District/neighborhood name |
| `address` | string | ❌ | Full address |
| `latitude` | number | ✅ | Latitude (WGS84) |
| `longitude` | number | ✅ | Longitude (WGS84) |
| `photos` | string[] | ❌ | Array of photo URLs |
| `external_id` | string | ❌ | Your platform's property ID |

**Example field mapping:**

If your platform uses `apartment_name` instead of `title` and `cost_usd` instead of `price`, we configure:

```json
{
    "apartment_name": "title",
    "apartment_description": "description",
    "cost_usd": "price",
    "room_count": "rooms",
    "total_area": "area_sqm",
    "neighborhood": "district",
    "full_address": "address",
    "lat": "latitude",
    "lng": "longitude",
    "image_urls": "photos",
    "listing_id": "external_id"
}
```

Send your field name mappings to our team, and we'll configure them on our end.

---

## Step 3: Push Property Data

Send property data to PropVision using the ingestion API. You can call this endpoint whenever a new listing is created or updated on your platform.

### cURL

```bash
curl -X POST https://api.propvision.ai/api/v1/properties \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pv_live_a1b2c3d4e5f6g7h8i9j0" \
  -d '{
    "title": "Modern 3-room apartment in Yunusabad",
    "description": "Bright apartment with renovated kitchen and balcony.",
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
      "https://your-cdn.com/photos/living-room.jpg",
      "https://your-cdn.com/photos/kitchen.jpg"
    ],
    "external_id": "your-listing-12345"
  }'
```

### Python

```python
import requests

API_KEY = "pv_live_a1b2c3d4e5f6g7h8i9j0"
BASE_URL = "https://api.propvision.ai/api/v1"

def push_property(property_data: dict) -> dict:
    """Push a single property to PropVision."""
    response = requests.post(
        f"{BASE_URL}/properties",
        json=property_data,
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
    )
    response.raise_for_status()
    return response.json()

# Example usage
property = {
    "title": "Modern 3-room apartment in Yunusabad",
    "description": "Bright apartment with renovated kitchen and balcony.",
    "price": 68000,
    "currency": "USD",
    "rooms": 3,
    "area_sqm": 85.5,
    "district": "Yunusabad",
    "address": "Yunusabad district, Amir Temur street 45",
    "latitude": 41.3385,
    "longitude": 69.2856,
    "photos": [
        "https://your-cdn.com/photos/living-room.jpg",
        "https://your-cdn.com/photos/kitchen.jpg"
    ],
    "external_id": "your-listing-12345"
}

result = push_property(property)
print(f"Property created with ID: {result['id']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_KEY = 'pv_live_a1b2c3d4e5f6g7h8i9j0';
const BASE_URL = 'https://api.propvision.ai/api/v1';

async function pushProperty(propertyData) {
  const response = await axios.post(
    `${BASE_URL}/properties`,
    propertyData,
    {
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      }
    }
  );
  return response.data;
}

// Example usage
const property = {
  title: 'Modern 3-room apartment in Yunusabad',
  description: 'Bright apartment with renovated kitchen and balcony.',
  price: 68000,
  currency: 'USD',
  rooms: 3,
  area_sqm: 85.5,
  district: 'Yunusabad',
  address: 'Yunusabad district, Amir Temur street 45',
  latitude: 41.3385,
  longitude: 69.2856,
  photos: [
    'https://your-cdn.com/photos/living-room.jpg',
    'https://your-cdn.com/photos/kitchen.jpg'
  ],
  external_id: 'your-listing-12345'
};

pushProperty(property).then(result => {
  console.log(`Property created with ID: ${result.id}`);
});
```

### Batch Sync

To sync your entire property catalog, iterate through your listings and call the endpoint for each. The API supports 100 requests/minute per API key. For large catalogs (10,000+ properties), contact us for bulk import support.

```python
import time

def sync_all_properties(properties: list[dict]):
    """Sync all properties with rate limiting."""
    for i, prop in enumerate(properties):
        try:
            result = push_property(prop)
            print(f"[{i+1}/{len(properties)}] Synced: {result['id']}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited — wait and retry
                retry_after = int(e.response.headers.get('Retry-After', 60))
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                result = push_property(prop)
            else:
                print(f"Error syncing property: {e}")
        time.sleep(0.6)  # ~100 requests/minute
```

---

## Step 4: Embed the Widget

Add PropVision's visualization widget to your property detail pages. Two lines of code are required.

### Basic Integration

Add this to the `<head>` or end of `<body>` on your property pages:

```html
<!-- PropVision Widget -->
<script src="https://api.propvision.ai/widget.js" async></script>
```

Add a container `<div>` where you want the widget to appear:

```html
<div
  id="propvision-widget"
  data-api-key="pv_live_a1b2c3d4e5f6g7h8i9j0"
  data-property-id="550e8400-e29b-41d4-a716-446655440000"
  data-theme="light"
></div>
```

### Configuration Options

| Attribute | Required | Values | Description |
|-----------|----------|--------|-------------|
| `data-api-key` | ✅ | Your API key | Authentication for widget API calls |
| `data-property-id` | ✅ | Property UUID | PropVision property ID to display |
| `data-theme` | ❌ | `light` (default), `dark` | Widget color scheme |
| `data-height` | ❌ | CSS value (default: `600px`) | Widget height |
| `data-show-scores` | ❌ | `true` (default), `false` | Show/hide comfort scores |
| `data-show-3d` | ❌ | `true` (default), `false` | Show/hide 3D viewer |
| `data-locale` | ❌ | `en`, `ru` (default) | Widget language |

### Dynamic Property Loading

If your page loads property data dynamically (e.g., SPA), you can update the widget's property ID using JavaScript:

```javascript
// Change the displayed property
window.postMessage({
  type: 'propvision:update',
  propertyId: 'new-property-uuid-here'
}, '*');
```

### Responsive Behavior

The widget automatically:
- Fills the width of its container `<div>`
- Maintains a minimum height of 400px
- Supports heights from 400px to 800px
- Adapts layout for mobile screens (< 768px wide)

### Full Page Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property Listing - Your Platform</title>
    <style>
        .property-page { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .property-main { display: flex; gap: 24px; }
        .property-info { flex: 1; }
        .propvision-container { flex: 1; min-width: 400px; }
    </style>
</head>
<body>
    <div class="property-page">
        <h1>Modern 3-Room Apartment</h1>
        <div class="property-main">
            <div class="property-info">
                <p><strong>Price:</strong> $68,000</p>
                <p><strong>Rooms:</strong> 3</p>
                <p><strong>Area:</strong> 85.5 m²</p>
                <p><strong>District:</strong> Yunusabad</p>
                <p>Bright apartment with renovated kitchen and balcony...</p>
            </div>
            <div class="propvision-container">
                <!-- PropVision Widget -->
                <div
                    id="propvision-widget"
                    data-api-key="pv_live_a1b2c3d4e5f6g7h8i9j0"
                    data-property-id="550e8400-e29b-41d4-a716-446655440000"
                    data-theme="light"
                    data-height="600px"
                ></div>
            </div>
        </div>
    </div>
    <script src="https://api.propvision.ai/widget.js" async></script>
</body>
</html>
```

---

## Step 5: Use the AI Search API (Optional)

If you want to add PropVision's AI-powered search to your platform, call the search endpoint directly:

```javascript
async function searchProperties(query) {
  const response = await fetch('https://api.propvision.ai/api/v1/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'pv_live_a1b2c3d4e5f6g7h8i9j0'
    },
    body: JSON.stringify({ query })
  });
  return response.json();
}

// Example: User types a natural language query
const results = await searchProperties('2-room flat near metro under $70,000');
console.log(`Found ${results.total} properties`);
console.log('Parsed filters:', results.parsed_filters);
results.results.forEach(prop => {
  console.log(`- ${prop.title} ($${prop.price})`);
});
```

---

## Step 6: Monitor Integration

Use the analytics dashboard (internal) or call the analytics endpoint to monitor API usage:

```bash
curl -X GET https://api.propvision.ai/api/v1/analytics/dashboard \
  -H "X-API-Key: pv_live_a1b2c3d4e5f6g7h8i9j0"
```

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Widget doesn't load | Check browser console for errors. Verify `data-api-key` is correct. Ensure `widget.js` URL is accessible. |
| 401 Unauthorized | API key is invalid or expired. Contact PropVision team for a new key. |
| 422 Validation Error | Check the error response `detail` field for specific field errors. Ensure required fields (title, price, latitude, longitude) are provided. |
| 429 Rate Limited | You're exceeding 100 requests/minute. Add delays between API calls or contact us for a higher rate limit. |
| Widget shows "No data" | The `data-property-id` doesn't match any property in PropVision's database. Ensure you've pushed the property via the ingestion API first. |
| 3D model not showing | 3D reconstruction may not be complete or available for this property. Check status via `GET /api/v1/3d/{property_id}/status`. |

---

## Support

- **Email:** dev-support@propvision.ai
- **Documentation:** https://docs.propvision.ai
- **API Status:** https://status.propvision.ai
