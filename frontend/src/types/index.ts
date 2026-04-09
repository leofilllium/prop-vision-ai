/**
 * TypeScript type definitions for PropVision.AI data models.
 */

export interface GeoJSONPoint {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
}

export interface ComfortScoreBrief {
  transport_score?: number;
  shopping_score?: number;
  education_score?: number;
  green_space_score?: number;
  safety_score?: number;
  healthcare_score?: number;
  entertainment_score?: number;
  overall_score: number | null;
  data_confidence: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface Property {
  id: string;
  title: string;
  description?: string;
  price: number;
  currency: string;
  rooms?: number;
  area_sqm?: number;
  floor?: number;
  total_floors?: number;
  district?: string;
  address?: string;
  location: GeoJSONPoint;
  photos: string[];
  model_3d_url?: string | null;
  video_walkthrough_url?: string | null;
  video_generation_status?: string | null;
  video_generation_job_id?: string | null;
  comfort_score?: ComfortScoreBrief | null;
  partner_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PropertyListResponse {
  total: number;
  limit: number;
  offset: number;
  results: Property[];
}

export interface ParsedFilters {
  rooms?: number | null;
  min_price?: number | null;
  max_price?: number | null;
  district?: string | null;
  proximity_to?: string | null;
  max_distance_m?: number | null;
  min_area_sqm?: number | null;
  max_area_sqm?: number | null;
  sort_by_comfort?: string | null;
}

export interface SearchResponse {
  query: string;
  parsed_filters: ParsedFilters;
  total: number;
  results: Property[];
}

export interface ScoreDetails {
  score: number;
  details: Record<string, number>;
}

export interface ComfortScoreDetail {
  property_id: string;
  scores: {
    transport: ScoreDetails;
    shopping: ScoreDetails;
    education: ScoreDetails;
    green_space: ScoreDetails;
    safety: ScoreDetails;
    healthcare: ScoreDetails;
    entertainment: ScoreDetails;
  };
  overall_score: number;
  data_confidence: string;
  weights: {
    transport: number;
    shopping: number;
    education: number;
    green_space: number;
    safety: number;
    healthcare: number;
    entertainment: number;
  };
  computed_at: string;
}

export interface TopQuery {
  query: string;
  count: number;
}

export interface AmenityDemand {
  amenity: string;
  count: number;
}

export interface DistrictQueryStats {
  district: string;
  search_count: number;
}

export interface UserBudgetStats {
  avg_min_price: number;
  avg_max_price: number;
}

export interface MarketIntelligence {
  amenity_demand: AmenityDemand[];
  district_popularity: DistrictQueryStats[];
  average_budget: UserBudgetStats;
}

export interface ComfortPriceEfficiency {
  district: string;
  efficiency_gap: number;
}

export interface InventoryInsights {
  comfort_price_efficiency: ComfortPriceEfficiency[];
  spatial_conversion_lift: number;
}

export interface ProximityHotspot {
  name: string;
  mentions: number;
}

export interface DashboardData {
  api_calls: {
    daily: Array<{ date: string; count: number }>;
    total_last_30_days: number;
  };
  top_queries: TopQuery[];
  comfort_scores_by_district: Array<{ district: string; avg_overall_score: number }>;
  model_3d_views: {
    total: number;
    last_7_days: number;
  };
  market_intelligence: MarketIntelligence;
  inventory_insights: InventoryInsights;
  geo_hotspots: ProximityHotspot[];
}

