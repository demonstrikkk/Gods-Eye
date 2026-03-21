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
  | 'sentiment'
  | 'events'
  | 'fires'
  | 'earthquakes'
  | 'news';

export type SidebarTab =
  | 'booths'
  | 'workers'
  | 'schemes'
  | 'alerts'
  | 'ai';
