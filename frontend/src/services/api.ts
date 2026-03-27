// ─────────────────────────────────────────────────────────────────────────────
// Gods-Eye OS — API Service Layer
// All functions hit the real backend. No fallback mock data.
// ─────────────────────────────────────────────────────────────────────────────

import type {
  BoothPoint, Booth, Worker, Scheme, GlobalCountry, GlobalSignal, GlobalCorridor, GlobalOverview, SourceHealth, MarketQuote,
  GlobalAsset, CountryAnalysis,
  GeoEvent, FireHotspot, Earthquake, NewsFeed, Alert, QueryResponse,
  ExpertAnalysisResponse, ExpertAgent,
  VisualIntelligenceResponse, ViChartOutput, ViDiagramOutput, ViParsedIntent,
  ViDataSource, ViDomain, ViChartTypeInfo, ViDiagramTypeInfo, ViChartType, ViDiagramType,
  UnifiedIntelligenceResponse, UnifiedCapabilityType, UnifiedConversationMessageInput
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

// ─────────────────────────────────────────────────────────────────────────────
// Visual Intelligence API
// ─────────────────────────────────────────────────────────────────────────────

export interface VisualIntelligenceRequest {
  query: string;
  context?: Record<string, any>;
  force_chart_type?: ViChartType;
  force_diagram_type?: ViDiagramType;
  include_map?: boolean;
  include_expert_analysis?: boolean;
}

export const postVisualIntelligence = async (
  query: string,
  options?: {
    context?: Record<string, any>;
    forceChartType?: ViChartType;
    forceDiagramType?: ViDiagramType;
    includeMap?: boolean;
    includeExpertAnalysis?: boolean;
  }
): Promise<{ status: string; data: VisualIntelligenceResponse }> => {
  const res = await fetch(`${BASE}/visual-intelligence/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      context: options?.context || {},
      force_chart_type: options?.forceChartType,
      force_diagram_type: options?.forceDiagramType,
      include_map: options?.includeMap ?? true,
      include_expert_analysis: options?.includeExpertAnalysis ?? true,
    }),
  });
  if (!res.ok) throw new Error(`Visual intelligence failed: ${res.status}`);
  return await res.json();
};

export const parseVisualIntent = async (
  query: string
): Promise<{ status: string; data: ViParsedIntent }> => {
  const res = await fetch(`${BASE}/visual-intelligence/parse-intent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Intent parsing failed: ${res.status}`);
  return await res.json();
};

export const generateChart = async (
  chartType: ViChartType,
  data: { labels: string[]; datasets: Array<{ label: string; data: number[]; backgroundColor?: string }> },
  title: string,
  options?: Record<string, any>
): Promise<{ status: string; data: ViChartOutput }> => {
  const res = await fetch(`${BASE}/visual-intelligence/generate-chart`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chart_type: chartType,
      data,
      title,
      options: options || {},
    }),
  });
  if (!res.ok) throw new Error(`Chart generation failed: ${res.status}`);
  return await res.json();
};

export const generateDiagram = async (
  diagramType: ViDiagramType,
  description: string,
  context?: Record<string, any>
): Promise<{ status: string; data: ViDiagramOutput }> => {
  const res = await fetch(`${BASE}/visual-intelligence/generate-diagram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      diagram_type: diagramType,
      description,
      context: context || {},
    }),
  });
  if (!res.ok) throw new Error(`Diagram generation failed: ${res.status}`);
  return await res.json();
};

export const fetchViDataSources = async (): Promise<{
  status: string;
  count: number;
  data: ViDataSource[]
}> => {
  const res = await fetch(`${BASE}/visual-intelligence/data-sources`);
  if (!res.ok) throw new Error(`Failed to fetch data sources: ${res.status}`);
  return await res.json();
};

export const fetchViDomains = async (): Promise<{
  status: string;
  count: number;
  data: ViDomain[];
}> => {
  const res = await fetch(`${BASE}/visual-intelligence/supported-domains`);
  if (!res.ok) throw new Error(`Failed to fetch domains: ${res.status}`);
  return await res.json();
};

export const fetchViChartTypes = async (): Promise<{
  status: string;
  count: number;
  data: ViChartTypeInfo[];
}> => {
  const res = await fetch(`${BASE}/visual-intelligence/chart-types`);
  if (!res.ok) throw new Error(`Failed to fetch chart types: ${res.status}`);
  return await res.json();
};

export const fetchViDiagramTypes = async (): Promise<{
  status: string;
  count: number;
  data: ViDiagramTypeInfo[];
}> => {
  const res = await fetch(`${BASE}/visual-intelligence/diagram-types`);
  if (!res.ok) throw new Error(`Failed to fetch diagram types: ${res.status}`);
  return await res.json();
};

// ─────────────────────────────────────────────────────────────────────────────
// Unified Intelligence API (Single Entry Point for All Capabilities)
// ─────────────────────────────────────────────────────────────────────────────

export const postUnifiedIntelligence = async (
  query: string,
  options?: {
    context?: Record<string, any>;
    conversation_id?: string;
    conversation_history?: UnifiedConversationMessageInput[];
    forced_capabilities?: UnifiedCapabilityType[];
    manual_capabilities?: UnifiedCapabilityType[];
    execution_mode?: 'auto' | 'fast' | 'manual' | 'visual_only' | 'reasoning_only' | 'tools_only' | 'map_only';
    max_processing_time?: number;
    include_debug_info?: boolean;
  }
): Promise<UnifiedIntelligenceResponse> => {
  const res = await fetch(`${BASE}/unified/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      context: options?.context || {},
      conversation_id: options?.conversation_id,
      conversation_history: options?.conversation_history || [],
      forced_capabilities: options?.forced_capabilities,
      manual_capabilities: options?.manual_capabilities,
      execution_mode: options?.execution_mode || 'auto',
      max_processing_time: options?.max_processing_time || 30.0,
      include_debug_info: options?.include_debug_info || false,
    }),
  });
  if (!res.ok) throw new Error(`Unified intelligence failed: ${res.status}`);
  const data = await res.json();
  return data;
};

export type UnifiedStreamEvent = {
  type: string;
  timestamp?: string;
  phase?: string;
  message?: string;
  [key: string]: any;
};

export type UnifiedStreamCallbacks = {
  onOpen?: () => void;
  onEvent?: (event: UnifiedStreamEvent) => void;
  onResult?: (response: UnifiedIntelligenceResponse) => void;
  onError?: (error: string) => void;
  onClose?: (event: CloseEvent) => void;
};

export const streamUnifiedIntelligence = (
  payload: {
    query: string;
    context?: Record<string, any>;
    conversation_id?: string;
    conversation_history?: UnifiedConversationMessageInput[];
    forced_capabilities?: UnifiedCapabilityType[];
    manual_capabilities?: UnifiedCapabilityType[];
    execution_mode?: 'auto' | 'fast' | 'manual' | 'visual_only' | 'reasoning_only' | 'tools_only' | 'map_only';
    max_processing_time?: number;
    include_debug_info?: boolean;
  },
  callbacks: UnifiedStreamCallbacks,
): WebSocket => {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${protocol}://${window.location.host}${BASE}/unified/stream`;
  const socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    callbacks.onOpen?.();
    socket.send(JSON.stringify({
      query: payload.query,
      context: payload.context || {},
      conversation_id: payload.conversation_id,
      conversation_history: payload.conversation_history || [],
      forced_capabilities: payload.forced_capabilities,
      manual_capabilities: payload.manual_capabilities,
      execution_mode: payload.execution_mode || 'auto',
      max_processing_time: payload.max_processing_time || 30.0,
      include_debug_info: payload.include_debug_info || false,
    }));
  };

  socket.onmessage = (messageEvent: MessageEvent<string>) => {
    try {
      const event = JSON.parse(messageEvent.data) as UnifiedStreamEvent;
      if (event.type === 'result' && event.response) {
        callbacks.onResult?.(event.response as UnifiedIntelligenceResponse);
        return;
      }
      if (event.type === 'error') {
        callbacks.onError?.(String(event.message || 'Unified streaming failed'));
        return;
      }
      callbacks.onEvent?.(event);
    } catch (err) {
      callbacks.onError?.(err instanceof Error ? err.message : 'Failed to parse unified stream event');
    }
  };

  socket.onerror = () => {
    callbacks.onError?.('Unified intelligence websocket connection error');
  };

  socket.onclose = (event) => {
    callbacks.onClose?.(event);
  };

  return socket;
};

export const assessUnifiedQuery = async (
  query: string
): Promise<{ status: string; assessment: any }> => {
  const res = await fetch(`${BASE}/unified/assess`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Query assessment failed: ${res.status}`);
  return await res.json();
};

export const fetchUnifiedCapabilities = async (): Promise<{
  status: string;
  count: number;
  capabilities: Array<{
    id: string;
    name: string;
    description: string;
    activation_triggers: string[];
    example_queries: string[];
  }>;
}> => {
  const res = await fetch(`${BASE}/unified/capabilities`);
  if (!res.ok) throw new Error(`Failed to fetch unified capabilities: ${res.status}`);
  return await res.json();
};

export const fetchUnifiedExamples = async (): Promise<{
  status: string;
  examples: Record<string, string[]>;
}> => {
  const res = await fetch(`${BASE}/unified/examples`);
  if (!res.ok) throw new Error(`Failed to fetch unified examples: ${res.status}`);
  return await res.json();
};
