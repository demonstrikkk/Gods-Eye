// ─────────────────────────────────────────────────────────────────────────────
// JanGraph OS — Shared Type Definitions
// ─────────────────────────────────────────────────────────────────────────────

export interface GeoPoint {
  lat: number;
  lng: number;
}

export interface BoothPoint extends GeoPoint {
  id: string;
  name: string;
  constituency: string;
  sentiment: number;
  sentiment_label: string;
  population: number;
  top_issue: string;
  unresolved: number;
  key_voters: number;
}

export interface GlobalCountry extends GeoPoint {
  id: string;
  iso3?: string;
  name: string;
  region: string;
  macro_region?: string;
  risk_index: number;
  influence_index: number;
  sentiment: number;
  stability: string;
  pressure: string;
  top_domains: string[];
  active_signals: number;
  asset_count?: number;
  capital?: string;
  population?: number;
}

export interface GlobalSignal extends GeoPoint {
  id: string;
  country_id: string;
  title: string;
  summary: string;
  category: string;
  layer?: LayerKey;
  severity: "High" | "Medium" | "Low";
  source: string;
  time: string;
}

export interface GlobalAsset extends GeoPoint {
  id: string;
  country_id: string;
  title: string;
  kind: string;
  layer: LayerKey;
  category: string;
  status: string;
  importance: number;
  description: string;
  source: string;
}

export interface GlobalCorridor {
  id: string;
  label: string;
  category: string;
  status: string;
  weight: number;
  from_country: string;
  to_country: string;
  from_name: string;
  to_name: string;
  start_lat: number;
  start_lng: number;
  end_lat: number;
  end_lng: number;
}

export interface GlobalOverview {
  total_countries: number;
  total_signals: number;
  total_assets?: number;
  critical_zones: number;
  active_corridors: number;
  systemic_stress: number;
  updated_at: string;
  live_sources?: number;
  last_refresh?: string;
  market_tickers?: number;
}

export interface SourceHealth {
  id: string;
  label: string;
  mode: string;
  status: string;
  item_count: number;
  message: string;
  last_updated: string;
  strategy?: string;
}

export interface MarketQuote {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
  high?: number;
  low?: number;
}

export interface CountryAnalysis {
  country: GlobalCountry;
  summary: string;
  risk_factors: Array<{ factor: string; severity: string; description: string }>;
  opportunities: string[];
  signals: GlobalSignal[];
  assets: GlobalAsset[];
  feeds: NewsFeed[];
  weather: {
    source: string;
    status: string;
    current?: Record<string, any>;
    daily?: Record<string, any>;
  };
  world_bank?: Record<string, any>;
  suggested_questions: string[];
  ai_prompt: string;
}

export interface Booth {
  id: string;
  name: string;
  constituency_name: string;
  state: string;
  lat: number;
  lng: number;
  avg_sentiment: number;
  sentiment_label: string;
  top_issues: Array<{ issue: string; count: number }>;
  voters: number;
  workers_assigned: number;
}

export interface Worker {
  id: string;
  name: string;
  status: 'Online' | 'Offline' | 'Field';
  constituency_id: string;
  booth_id: string;
  performance_score: number;
  tasks_completed: number;
  last_active: string;
  phone: string;
}

export interface Scheme {
  id: string;
  name: string;
  ministry: string;
  target_segment: string;
  benefit: string;
  coverage_pct?: number;
}

export interface GeoEvent extends GeoPoint {
  id: string;
  title: string;
  type: string;
  date: string;
  source: string;
  fatalities?: number;
  intensity?: number;
}

export interface FireHotspot extends GeoPoint {
  id: string;
  brightness: number;
  confidence: string;
  date: string;
}

export interface Earthquake extends GeoPoint {
  id: string;
  location: string;
  magnitude: number;
  depth: number;
  time: string;
}

export interface NewsFeed {
  id: string;
  source: string;
  category: string;
  text: string;
  urgency: 'High' | 'Medium' | 'Low';
  time: string;
  url?: string;
}

export interface Alert {
  id: string;
  source: string;
  category: string;
  text: string;
  urgency: 'High' | 'Medium' | 'Low';
  time: string;
}

export interface QueryResponse {
  answer: string;
  cypher?: string;
  data?: any[];
}

export type MapMode = 'globe' | 'flat';

export type LayerKey =
  | 'countries'
  | 'corridors'
  | 'economics'
  | 'governance'
  | 'climate'
  | 'defense'
  | 'conflict'
  | 'infrastructure'
  | 'mobility'
  | 'cyber'
  | 'news';

export type SidebarTab =
  | 'global'
  | 'booths'
  | 'workers'
  | 'schemes'
  | 'alerts'
  | 'ai';
