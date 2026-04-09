# PropVision.AI | API Setup Guide

This document explains how to obtain the necessary credentials for the **PropVision.AI** platform. These tokens are required for the AI-driven search, 3D spatial mapping, and location-based scoring to function.

---

## 🔑 Primary Service Keys

### 1. OpenAI (AI Search & Query Parsing)
**Used by**: `AISearchService` to convert natural language into PostGIS queries.
1.  Go to the [OpenAI Platform](https://platform.openai.com/api-keys).
2.  Log in and create a new **Secret Key**.
3.  Ensure your account has at least $5 of credit for API usage.
4.  **Cost**: Extremely low ($0.15/1M tokens) using the `gpt-4o-mini` model.

### 2. Mapbox (High-End Map Rendering)
**Used by**: `MapView` component for 3D terrain and vector tile rendering.
1.  Sign up at [Mapbox.com](https://www.mapbox.com/).
2.  Your **Default Public Token** is available immediately on your [Dashboard](https://account.mapbox.com/).
3.  Copy the token starting with `pk.`.
4.  **Free Tier**: Up to 50,000 monthly map loads (generous for MVP).

### 3. Google Places API (POI Context)
**Used by**: `POIFetcherService` to calculate human-centric Comfort Scores.
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable the **Places API (New)**.
3.  Go to **APIs & Services > Credentials** and create an **API Key**.
4.  Restrict the key to the Places API for security.

---

## 🧊 Advanced Spatial Keys

### 4. Luma AI (3D Reconstruction)
**Used by**: `ReconstructionService` to generate 3D spatial splats from listing photos.
1.  Access the [Luma AI API Dashboard](https://lumalabs.ai/luma-api).
2.  Generate a new API key.
3.  Note: This enables the capture-to-3D pipeline for new property listings.

### 5. AWS S3 (Object Storage)
**Used by**: File storage for 3D models and high-res property images.
1.  Log in to [AWS Management Console](https://aws.amazon.com/console/).
2.  Create an **S3 Bucket** (e.g., `propvision-models`).
3.  Go to **IAM** and create a User with `AmazonS3FullAccess` (or custom policy for that bucket).
4.  Copy the **Access Key ID** and **Secret Access Key**.

---

## 🛡️ Internal Security

### 6. API Secret Key
**Used by**: Token signing and internal hashing.
Generate a random 32-character string. You can use this command in your terminal:
```bash
openssl rand -hex 32
```

> [!IMPORTANT]
> **Minimal Setup**: To get the map running immediately, only **Mapbox** (`pk.xx`) is required. To enable the AI search bar, you'll also need **OpenAI** (`sk-xx`).
