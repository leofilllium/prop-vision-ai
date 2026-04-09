/**
 * App configuration — API URLs, Mapbox token, and feature flags.
 */

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  mapboxToken: import.meta.env.VITE_MAPBOX_TOKEN || '',
  apiKey: import.meta.env.VITE_API_KEY || 'pv_demo_1234567890abcdef',

  // Map defaults (Tashkent center)
  map: {
    center: { lng: 69.2401, lat: 41.2995 } as { lng: number; lat: number },
    zoom: 12,
    style: 'mapbox://styles/mapbox/dark-v11',
  },

  // Feature flags
  features: {
    enable3DViewer: true,
    enableAISearch: true,
    enableComfortHeatmap: true,
    enableWidget: true,
  },
} as const;
