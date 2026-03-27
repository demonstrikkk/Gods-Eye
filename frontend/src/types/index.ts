// ─────────────────────────────────────────────────────────────────────────────
// Gods-Eye OS — Shared Type Definitions
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
  runtime_signal_count?: number;
  seeded_signal_count?: number;
  asset_count?: number;
  capital?: string;
  population?: number;
  country_catalog_mode?: "runtime" | "seeded";
  signal_source_mode?: "runtime_only" | "seeded_only" | "runtime_plus_seeded" | "none";
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
  source_mode?: "runtime" | "seeded";
  source_origin?: string;
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
  source_mode?: "runtime" | "seeded";
  source_origin?: string;
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
  source_mode?: "runtime" | "seeded";
  source_origin?: string;
}

export interface GlobalOverview {
  total_countries: number;
  total_signals: number;
  runtime_signals?: number;
  seeded_signals?: number;
  total_assets?: number;
  runtime_assets?: number;
  seeded_assets?: number;
  critical_zones: number;
  active_corridors: number;
  runtime_corridors?: number;
  seeded_corridors?: number;
  systemic_stress: number;
  updated_at: string;
  live_sources?: number;
  last_refresh?: string;
  market_tickers?: number;
  provenance?: SourceProvenance;
}

export interface SourceProvenance {
  live_sources: number;
  limited_sources: number;
  unavailable_sources: number;
  fallback_sources: number;
  error_sources: number;
  total_sources: number;
  seeded_context: boolean;
  runtime_state_backed: boolean;
  last_refresh?: string;
  country_id?: string;
  analysis_mode?: string;
  runtime_signal_count?: number;
  seeded_signal_count?: number;
  live_source_labels?: string[];
  limited_source_labels?: string[];
  unavailable_source_labels?: string[];
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
  research_brief?: string;
  evidence_points?: string[];
  source_status?: Array<{ label: string; status: string; count: number }>;
  provenance?: SourceProvenance;
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
  search_briefs?: {
    source: string;
    country: string;
    query: string;
    status: string;
    results: Array<{ title: string; url: string; source: string }>;
  };
  world_bank?: Record<string, any>;
  macro_indicators?: Array<{
    id: string;
    label: string;
    value: number | null;
    unit: string;
    status: string;
  }>;
  stability_vector?: Array<{
    label: string;
    score: number;
  }>;
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
  | 'ai'
  | 'expert'
  | 'visual'
  | 'unified'
  | 'battleground'
  | 'officials'
  | 'workspace';

// ─────────────────────────────────────────────────────────────────────────────
// Expert Agent System Types
// ─────────────────────────────────────────────────────────────────────────────

export type ConfidenceLevel =
  | 'very_high'
  | 'high'
  | 'moderate'
  | 'low'
  | 'very_low'
  | 'insufficient';

export type ConsensusStrength =
  | 'unanimous'
  | 'strong'
  | 'moderate'
  | 'weak'
  | 'divergent'
  | 'no_consensus';

export interface ExpertAgent {
  id: string;
  name: string;
  domain: string;
  description: string;
}

export interface AgentClaim {
  id: string;
  statement: string;
  probability: number;
  confidence_level: ConfidenceLevel;
  supporting_observations: string[];
  reasoning_chain: string[];
  assumptions: string[];
  methodology: string;
  timestamp: string;
}

export interface AgentContribution {
  name: string;
  domain: string;
  confidence: number;
  key_claims: number;
  data_sources: number;
}

export interface Disagreement {
  id: string;
  agents: string[];
  topic: string;
  nature: string;
  severity: 'minor' | 'moderate' | 'major' | 'fundamental';
  positions: Record<string, string>;
  probabilities: Record<string, number>;
  resolution_attempted: boolean;
  partial_resolution?: string;
  conflicting_evidence: string[];
  impact_on_conclusion: string;
}

export interface MinorityOpinion {
  agent: string;
  domain: string;
  position: string;
  probability: number;
  difference_from_consensus: number;
  reasoning: string[];
  key_evidence: string[];
}

export interface DebateRound {
  id: string;
  round_number: number;
  phase: string;
  topic: string;
  participants: string[];
  convergence_score: number;
  key_disagreements: string[];
  emerging_consensus?: string;
  start_time: string;
  end_time?: string;
}

export interface DebateSummary {
  topic: string;
  question: string;
  rounds_conducted: number;
  final_convergence: number;
  convergence_achieved: boolean;
  consensus_view?: {
    statement: string;
    probability: number;
    confidence: number;
  };
  disagreements: string[];
  position_summary: Array<{
    agent: string;
    stance: string;
    probability: number;
    confidence: number;
    key_evidence: string[];
  }>;
  total_arguments: number;
  total_rebuttals: number;
}

export interface ProbabilisticScenario {
  description: string;
  probability: number;
  key_factors: string[];
}

export interface ExpertConsensus {
  view: string;
  probability: number;
  strength: ConsensusStrength;
  confidence_level: string;
  confidence_score: number;
}

export interface ExpertAssessment {
  consensus_view?: string;
  confidence: {
    level: string;
    score: number;
    strength?: string;
  };
  key_findings: string[];
  data_sources_cited: string[];
  disagreements?: Disagreement[];
  disagreement_summary?: string;
  minority_opinions?: MinorityOpinion[];
}

export interface UncertaintyQuantification {
  overall_confidence: number;
  confidence_level: string;
  uncertainty_factors: string[];
  key_assumptions: string[];
  data_gaps: string[];
}

export interface ExpertAnalysisResponse {
  executive_summary: string;
  situation_analysis?: string;
  key_risk_factors?: Array<{
    factor: string;
    severity: string;
    description: string;
  }>;
  impact_on_india?: Record<string, string>;
  forecasts?: Record<string, string>;
  scenarios?: Array<{
    name: string;
    probability: string;
    trigger: string;
    outcome: string;
    impact_severity: number;
  }>;
  strategic_recommendations: string[];
  scenario_tree?: Array<{
    event: string;
    children: any[];
  }>;
  timeline?: Array<{
    time: string;
    event: string;
    impact: string;
    type: string;
  }>;

  // Expert-specific fields
  expert_assessment?: ExpertAssessment;
  uncertainty_quantification?: UncertaintyQuantification;
  probabilistic_scenarios?: Record<string, ProbabilisticScenario>;
  causal_reasoning_chain?: string[];
  debate_summary?: DebateSummary;
  agent_contributions?: Record<string, AgentContribution>;
  map_visualization?: {
    layers: Array<{
      type: string;
      name: string;
      data: any;
      color?: string;
      color_scale?: string;
    }>;
    affected_regions: string[];
  };

  _meta?: {
    query?: string;
    tools_used?: string[];
    unavailable_tools?: Record<string, any>;
    grounding_mode?: string;
    plan?: Record<string, any>;
    timestamp?: string;
    engine?: string;
    expert_agents_consulted?: string[];
    debate_conducted?: boolean;
    consensus_strength?: string;
    expert_processing_time_ms?: number;
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Visual Intelligence Types
// ─────────────────────────────────────────────────────────────────────────────

export type ViDomainType =
  | 'economics'
  | 'geopolitics'
  | 'climate'
  | 'infrastructure'
  | 'demographics'
  | 'defense'
  | 'trade'
  | 'technology'
  | 'energy'
  | 'agriculture'
  | 'health'
  | 'space'
  | 'logistics'
  | 'disaster';

export type ViChartType =
  | 'line'
  | 'bar'
  | 'pie'
  | 'scatter'
  | 'radar'
  | 'doughnut'
  | 'area'
  | 'horizontalBar';

export type ViDiagramType =
  | 'workflow'
  | 'cause_effect'
  | 'pipeline'
  | 'infrastructure'
  | 'network'
  | 'process'
  | 'hierarchy'
  | 'comparison';

export type ViIntentType =
  | 'comparison'
  | 'trend'
  | 'forecast'
  | 'what_if'
  | 'analysis'
  | 'correlation'
  | 'impact'
  | 'simulation'
  | 'overview';

export type ViMapFeatureType =
  | 'markers'
  | 'heatmap'
  | 'routes'
  | 'polygons'
  | 'highlight'
  | 'focus'
  | 'overlay';

export interface ViParsedIntent {
  query_id: string;
  raw_query: string;
  countries: string[];
  regions: string[];
  cities: string[];
  primary_domain: ViDomainType;
  secondary_domains: ViDomainType[];
  domain_confidence: Record<string, number>;
  intent_type: ViIntentType;
  time_range?: { start_year: number; end_year: number };
  requires_chart: boolean;
  chart_type?: ViChartType;
  requires_diagram: boolean;
  diagram_type?: ViDiagramType;
  requires_map: boolean;
  map_features: ViMapFeatureType[];
  indicators: string[];
  comparison_entities: string[];
  parse_confidence: number;
}

export interface ViChartOutput {
  chart_url: string;
  chart_type: ViChartType;
  title: string;
  config: Record<string, any>;
  data_summary: string;
  insight?: string;
}

export interface ViDiagramOutput {
  image_url: string;
  diagram_type: ViDiagramType;
  prompt_used: string;
  description: string;
  metadata?: Record<string, any>;
}

export interface ViGeoEntity {
  name: string;
  entity_type: string;
  iso_code?: string;
  lat?: number;
  lng?: number;
  confidence: number;
}

export interface ViMapMarker {
  lat: number;
  lng: number;
  label: string;
  marker_type: string;
  description?: string;
  color: string;
}

export interface ViMapRoute {
  from_lat: number;
  from_lng: number;
  to_lat: number;
  to_lng: number;
  route_type: string;
  label?: string;
  color: string;
}

export interface ViMapData {
  commands: Array<Record<string, any>>;
  affected_regions: string[];
  geo_entities: ViGeoEntity[];
  markers: ViMapMarker[];
  routes: ViMapRoute[];
  heatmap_data?: Record<string, number>;
  coordinate_data?: Record<string, any>;
  layer_recommendations: string[];
}

export interface ViChartInsight {
  chart_id: string;
  trend_description: string;
  key_values: string[];
  notable_patterns: string[];
}

export interface ViDiagramInsight {
  diagram_id: string;
  flow_description: string;
  key_elements: string[];
  relationships: string[];
}

export interface ViMapInsight {
  geographic_focus: string;
  spatial_patterns: string[];
  regional_highlights: string[];
}

export interface ViInsightSynthesis {
  executive_summary: string;
  key_findings: string[];
  cross_domain_connections: string[];
  causal_chain: string[];
  chart_insights: ViChartInsight[];
  diagram_insights: ViDiagramInsight[];
  map_insights?: ViMapInsight;
  recommendations: string[];
  data_sources: string[];
  confidence_score: number;
}

export interface VisualIntelligenceResponse {
  query_id: string;
  parsed_intent: ViParsedIntent;
  data_sources: string[];
  data_quality_score: number;
  charts: ViChartOutput[];
  diagrams: ViDiagramOutput[];
  map_data: ViMapData;
  insight: ViInsightSynthesis;
  expert_analysis?: ExpertAnalysisResponse;
  processing_time_ms: number;
  timestamp: string;
}

export interface ViDataSource {
  id: string;
  name: string;
  status: 'available' | 'limited' | 'unavailable';
  indicators: string[];
  last_check?: string;
}

export interface ViDomain {
  id: string;
  name: string;
  description: string;
  example_queries: string[];
}

export interface ViChartTypeInfo {
  id: ViChartType;
  name: string;
  description: string;
  use_cases: string[];
}

export interface ViDiagramTypeInfo {
  id: ViDiagramType;
  name: string;
  description: string;
  use_cases: string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Unified Intelligence Types
// ─────────────────────────────────────────────────────────────────────────────

export type UnifiedCapabilityType = 'reasoning' | 'tools' | 'visuals' | 'map';
export type UnifiedExecutionMode =
  | 'auto'
  | 'fast'
  | 'manual'
  | 'visual_only'
  | 'reasoning_only'
  | 'tools_only'
  | 'map_only';

export interface UnifiedConversationMessageInput {
  role: 'system' | 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface UnifiedAssistantResponseSection {
  title: string;
  content: string;
  tone: string;
}

export interface UnifiedAssistantResponse {
  title: string;
  executive_brief: string;
  key_takeaways: string[];
  next_actions: string[];
  suggested_follow_ups: string[];
  memory_summary: string;
  response_blocks: UnifiedAssistantResponseSection[];
  artifact_overview: {
    charts: number;
    diagrams: number;
    map_markers: number;
    map_routes: number;
    successful_capabilities: number;
    failed_capabilities: number;
  };
  response_mode: string;
}

export interface UnifiedQueryAssessment {
  complexity: 'simple' | 'moderate' | 'complex' | 'very_complex';
  domains: string[];
  has_geographic_entities: boolean;
  has_data_indicators: boolean;
  has_time_dimension: boolean;
  requires_external_data: boolean;
  requires_multi_perspective: boolean;
  confidence: number;
  suggested_capabilities: string[];
}

export interface UnifiedReasoningResult {
  executive_summary: string;
  analysis: string;
  key_findings: string[];
  confidence: number;
  expert_agents_used: string[];
  consensus_achieved: boolean;
  risk_factors: Array<{ factor: string; severity: string; description: string }>;
  strategic_recommendations: string[];
  uncertainty_factors: string[];
  timeline: Array<{ time: string; event: string; impact: string; type: string }>;
  processing_time_ms: number;
}

export interface UnifiedToolsResult {
  tools_executed: string[];
  data_sources: string[];
  tool_outputs: Record<string, any>;
  insights: string[];
  unavailable_tools: Record<string, any>;
  processing_time_ms: number;
}

export interface UnifiedVisualsResult {
  charts: ViChartOutput[];
  diagrams: ViDiagramOutput[];
  chart_insights: string[];
  diagram_insights: string[];
  processing_time_ms: number;
}

export interface UnifiedMapResult {
  commands: Array<Record<string, any>>;
  affected_regions: string[];
  markers: ViMapMarker[];
  routes: ViMapRoute[];
  heatmap_data?: Record<string, number>;
  map_commands?: Array<Record<string, any>>;
  visual_markers?: CommandVisualMarker[];
  spawned_panels?: Array<Record<string, any>>;
  processing_time_ms: number;
}

export interface CommandVisualMarker {
  id: string;
  type: string;
  label: string;
  coordinates: GeoPoint;
  color: string;
  pulse?: boolean;
}

export interface CockpitState {
  priority_alert: {
    title: string;
    body: string;
    severity: string;
    dismissible?: boolean;
  };
  global_threat_level: {
    label: string;
    score: number;
    severity: string;
  };
  ontology_pulse: {
    countries: number;
    signals: number;
    sources: number;
  };
  risk_watchlist: Array<{
    title: string;
    severity: string;
  }>;
  operating_logic: {
    title: string;
    summary: string;
  };
  active_overlays: Array<{
    key: string;
    count: number;
    delta: number;
    color: string;
    icon: string;
  }>;
  subpanels: Array<Record<string, any>>;
  stream_phases: Array<{
    agent: string;
    phase: string;
    status: string;
  }>;
  core_intelligence: Array<{
    id: string;
    label: string;
    description: string;
  }>;
  demo_mode: boolean;
  cache_hit: boolean;
}

export interface UnifiedIntelligenceResponse {
  status: string;
  query_id: string;
  conversation_id: string;
  query: string;
  assessment: UnifiedQueryAssessment;
  reasoning?: UnifiedReasoningResult;
  tools?: UnifiedToolsResult;
  visuals?: UnifiedVisualsResult;
  map_intelligence?: UnifiedMapResult;
  unified_summary: string;
  assistant_response: UnifiedAssistantResponse;
  confidence_score: number;
  data_sources_used: string[];
  map_commands?: Array<Record<string, any>>;
  visual_markers?: CommandVisualMarker[];
  cockpit_state?: CockpitState | null;
  capabilities_activated: string[];
  capability_statuses: Array<{
    capability: UnifiedCapabilityType;
    success: boolean;
    error_message?: string | null;
    fallback_used?: boolean;
    execution_time_ms: number;
  }>;
  total_processing_time_ms: number;
  timestamp: string;
}
