// ─────────────────────────────────────────────────────────────────────────────
// JanGraph OS — API Service Layer
// All functions hit the real backend. No fallback mock data.
// ─────────────────────────────────────────────────────────────────────────────

import type {
  BoothPoint, Booth, Worker, Scheme, GlobalCountry, GlobalSignal, GlobalCorridor, GlobalOverview, SourceHealth, MarketQuote,
  GlobalAsset, CountryAnalysis,
  GeoEvent, FireHotspot, Earthquake, NewsFeed, Alert, QueryResponse,
  ExpertAnalysisResponse, ExpertAgent
} from '@/types';

const BASE = '/api/v1';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status} ${res.statusText}`);
  }
  const json = await res.json();
  return json.data ?? json;
}

export const fetchSentimentHeatmap = (): Promise<BoothPoint[]> =>
  apiFetch('/data/sentiment/heatmap');

export const fetchGlobalOverview = (): Promise<GlobalOverview> =>
  apiFetch('/data/global/overview');

export const fetchGlobalCountries = (): Promise<GlobalCountry[]> =>
  apiFetch('/data/global/countries');

export const fetchGlobalSignals = (): Promise<GlobalSignal[]> =>
  apiFetch('/data/global/signals');

export const fetchGlobalAssets = (): Promise<GlobalAsset[]> =>
  apiFetch('/data/global/assets');

export const fetchGlobalCorridors = (): Promise<GlobalCorridor[]> =>
  apiFetch('/data/global/corridors');

export const fetchGlobalGraph = (): Promise<any> =>
  apiFetch('/data/global/graph');

export const fetchCountryAnalysis = (countryId: string): Promise<CountryAnalysis> =>
  apiFetch(`/data/global/country-analysis/${countryId}`);

export const fetchSourceHealth = (): Promise<SourceHealth[]> =>
  apiFetch('/data/source-health');

export const fetchMarketSnapshot = (): Promise<MarketQuote[]> =>
  apiFetch('/data/markets');

export const fetchBooths = (): Promise<Booth[]> =>
  apiFetch('/data/booths');

export const fetchWorkers = (): Promise<Worker[]> =>
  apiFetch('/data/workers');

export const fetchSchemes = (): Promise<Scheme[]> =>
  apiFetch('/data/schemes');

export const fetchEvents = (): Promise<GeoEvent[]> =>
  apiFetch('/data/geopolitical/events');

export const fetchFires = (): Promise<any> =>
  apiFetch('/data/fires');

export const fetchEarthquakes = (): Promise<Earthquake[]> =>
  apiFetch('/data/earthquakes');

export const fetchNews = (): Promise<NewsFeed[]> =>
  apiFetch('/data/news');

export const fetchAlerts = (): Promise<Alert[]> =>
  apiFetch('/data/alerts');

export const fetchExecutiveKPIs = (): Promise<any> =>
  apiFetch('/intelligence/dashboard/executive').then((r: any) => r.kpis ?? r);

export const fetchSentimentTimeline = (): Promise<any[]> =>
  apiFetch('/data/sentiment/timeline?hours=24');

export const postQuery = async (question: string): Promise<QueryResponse> => {
  const res = await fetch(`${BASE}/intelligence/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, query: question }),
  });
  if (!res.ok) throw new Error(`Query failed: ${res.status}`);
  return await res.json();
};

export const postStrategicAnalysis = async (query: string): Promise<any> => {
  const res = await fetch(`${BASE}/intelligence/strategic-analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Strategic analysis failed: ${res.status}`);
  return await res.json();
};

export const postScenarioSimulate = async (original: string, query: string): Promise<any> => {
  const res = await fetch(`${BASE}/intelligence/scenario-simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ original_context: original, whatif_query: query }),
  });
  if (!res.ok) throw new Error(`Simulation failed: ${res.status}`);
  return await res.json();
};

export const postNewsInsight = async (query: string): Promise<any> => {
  const res = await fetch(`${BASE}/intelligence/news-insight`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`News insight failed: ${res.status}`);
  return await res.json();
};

export const apiClient = {
  get: async (url: string) => {
    const res = await fetch(`${BASE}${url}`);
    if (!res.ok) throw new Error(`API GET ${url} failed`);
    return { data: await res.json() };
  },
  post: async (url: string, data: any) => {
    const res = await fetch(`${BASE}${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`API POST ${url} failed`);
    return { data: await res.json() };
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Expert Agent System API
// ─────────────────────────────────────────────────────────────────────────────

export interface ExpertAnalysisRequest {
  query: string;
  context?: Record<string, any>;
  force_agents?: string[];
}

export const postExpertAnalysis = async (
  query: string,
  context?: Record<string, any>,
  forceAgents?: string[]
): Promise<{ status: string; data: ExpertAnalysisResponse }> => {
  const res = await fetch(`${BASE}/intelligence/expert-analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      context: context || {},
      force_agents: forceAgents || [],
    }),
  });
  if (!res.ok) throw new Error(`Expert analysis failed: ${res.status}`);
  return await res.json();
};

export const fetchExpertAgents = async (): Promise<{ status: string; agents: ExpertAgent[] }> => {
  const res = await fetch(`${BASE}/intelligence/expert-agents`);
  if (!res.ok) throw new Error(`Failed to fetch expert agents: ${res.status}`);
  return await res.json();
};

export const postExpertWhatIf = async (
  originalContext: string,
  whatIfQuery: string,
  variables: Record<string, any>
): Promise<any> => {
  const res = await fetch(`${BASE}/intelligence/scenario-simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      original_context: originalContext,
      whatif_query: whatIfQuery,
      variables,
    }),
  });
  if (!res.ok) throw new Error(`Expert what-if simulation failed: ${res.status}`);
  return await res.json();
};
