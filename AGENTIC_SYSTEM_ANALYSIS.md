# Gods-Eye OS: Complete Agentic System Analysis

**Document Version**: 2.0 | **Date**: March 2026 | **Authority**: Deep Codebase Analysis

---

## EXECUTIVE SUMMARY

God's Eye OS is a **multi-agent, async-first OSINT intelligence platform** with parallel expert reasoning, live debate mechanisms, and consensus-driven output generation. The system processes natural language queries through a sophisticated orchestrator that:

1. **Parses user intent** (domain detection, entity extraction)
2. **Spawns expert agents in parallel** (Economic, Geopolitical, Social, Climate, Policy agents)
3. **Detects and triggers live debates** when agent confidence diverges >25%
4. **Builds weighted consensus** from agent assessments
5. **Synthesizes final intelligence briefs** with visualizations and map intelligence

The system is **hybrid**: mocked domestic civic data (constituencies, citizens, schemes) + **real live OSINT data** (GDELT, USGS, FRED, NASA, weather APIs).

---

## 1. AGENTIC WORKFLOW

### 1.1 Complete Query Processing Pipeline

```
[User Query]
    ↓
[Query Parser] → Domain detection, entity extraction, type classification
    ↓
[Agent Selector] → Choose relevant expert agents based on domains
    ↓
[Data Enrichment] → Fetch live data: countries, signals, corridors, news
    ↓
[Parallel Agent Execution] → Run all selected agents concurrently
    ↓
[Divergence Check] → Are confidence scores > 25% apart?
    ├─ YES → [Debate System Activated] ✓
    └─ NO → [Proceed to Consensus]
    ↓
[Consensus Building] → Weighted aggregation, disagreement documentation
    ↓
[Final Response Generation] → Executive summary, key findings, recommendations
    ↓
[User Output] → Executive brief + citations + confidence metrics
```

### 1.2 Orchestrator Architecture

**Class**: `ExpertAgentOrchestrator` ([agent_orchestrator.py](backend/app/agents/agent_orchestrator.py#L1))

**Key Responsibilities**:
- Parse natural language queries into structured `QueryContext` objects
- Domain keyword matching (8 domains: economic, geopolitical, social, climate, policy, risk, simulation, multi_domain)
- Agent selection and parallel spawning
- Orchestration of debate lifecycle
- Consensus synthesis
- Response generation

**Configuration**:
```python
ExpertAgentOrchestrator(
  enable_debate=True,
  min_agents_for_debate=3,
  debate_threshold=0.25,    # 25% divergence triggers debate
  max_parallel_agents=5
)
```

**Main Entry Point**: `async process_query(query, context, force_agents)`

#### 1.2.1 Query Parsing Step

**Input**: Natural language query (e.g., "What's the impact of India's tech sector on Asian geopolitics?")

**Output**: `QueryContext` object containing:
- `primary_domain`: Main domain (Geopolitical, Economic, etc.)
- `secondary_domains`: Related domains (up to 3)
- `domain_confidence`: Score for each domain (0.0-1.0)
- `countries`: Extracted country mentions (India, China, USA, etc.)
- `regions`: Extracted regions (South Asia, Indo-Pacific, etc.)
- `key_entities`: Named entities in query
- `is_what_if`: Boolean - is this a scenario query?
- `is_forecast`: Boolean - asking about future?
- `is_comparison`: Boolean - comparing things?
- `is_historical`: Boolean - about past events?
- `simulation_variables`: For "what if X increases by Y%" queries

**Domain Keywords** (matching example):
```
ECONOMIC: gdp, inflation, economy, trade, currency, market, finance, growth, recession
GEOPOLITICAL: war, conflict, military, defense, alliance, tension, nuclear, sanctions
SOCIAL: protest, sentiment, public opinion, unrest, movement, strike
CLIMATE: weather, flood, drought, fire, earthquake, hurricane, disaster
POLICY: regulation, law, government, legislation, reform, election
```

#### 1.2.2 Agent Spawning Step

**Available Expert Agents** (in `expert_agents.py`):

| Agent ID | Name | Domain | Responsibility |
|----------|------|--------|-----------------|
| `economic` | Economic Analyst | ECONOMIC | GDP, inflation, trade, markets, fiscal/monetary policy |
| `geopolitical` | Geopolitical Strategist | GEOPOLITICAL | Military, diplomacy, alliances, conflicts, sanctions |
| `social` | Social Sentiment Analyst | SOCIAL | Protests, sentiment, public opinion, civil unrest |
| `climate` | Climate & Disaster Analyst | CLIMATE | Earthquakes, floods, fires, weather extremes, environmental |
| `policy` | Policy Strategist | POLICY | Legislation, governance, reforms, elections |
| `risk` | Risk Assessment Agent | RISK | Cross-domain risk quantification (always spawned) |
| `simulation` | Simulation & Forecasting | SIMULATION | What-if scenarios, future projections, trend modeling |

**Agent Selection Logic**:
1. **Always spawn**: Risk agent (baseline risk assessment)
2. **Conditionally spawn**: Agents matching `primary_domain` and `secondary_domains`
3. **Force option**: User can explicitly specify `force_agents=["economic", "geopolitical"]`

**Parallel Execution**:
```python
# All agents run concurrently via asyncio.gather()
assessments = await self._run_agents_parallel(selected_agents, query, context)
```

Each agent returns an `AgentAssessment` object (see § 1.3.1).

#### 1.2.3 Data Enrichment Step

**Enrichment Sources** invoked in `_enrich_context()`:

| Data Source | Module | Content |
|------------|--------|---------|
| Global Overview | `runtime_intelligence.py` | Total countries, signals, systemic stress |
| Countries & Risk | `runtime_intelligence.py` | Country details, risk indices, influence, stability |
| Active Signals | `runtime_intelligence.py` | Real-time global intelligence signals |
| Domestic Stats | `store.py` | Indian civic data (stats, constituencies, schemes) |
| Economic Indicators | Aggregated | GDP growth, inflation, trade balance |
| Risk Indices | `runtime_intelligence.py` | High-risk countries, global average risk |
| Trade Corridors | `runtime_intelligence.py` | Geopolitical trade routes and connections |
| News Feeds | `feed_aggregator.py` | Latest news articles (if available) |

**Enriched Context** passed to agents contains 8+ data sources in a dictionary, enabling agents to make informed assessments.

### 1.3 Debate System (Multi-Agent Consensus via Structured Argumentation)

**Class**: `AgentDebateSystem` ([debate_system.py](backend/app/agents/debate_system.py#L1))

**When Triggered**: When agent confidence scores diverge by > 0.25 (25%)

**Example Scenario**:
```
Query: "Will India's IT sector growth cool down?"

Economic Agent: 
  - confidence: 0.72
  - position: "Moderate slowdown expected"

Geopolitical Agent:
  - confidence: 0.52
  - position: "Strong growth due to shifting supply chains"

Divergence: |0.72 - 0.52| = 0.20 (still below 0.25 threshold)
→ NO DEBATE TRIGGERED

---

Query: "What's the impact of US-China tech war on India?"

Economic Agent:
  - confidence: 0.80
  - position: "India will gain as manufacturing hub"

Geopolitical Agent:
  - confidence: 0.45
  - position: "India's strategic alignment unclear"

Divergence: |0.80 - 0.45| = 0.35 (ABOVE 0.25 threshold)
→ DEBATE INITIATED
```

#### 1.3.1 Debate Structure

**Phases** (sequential):

1. **OPENING** - Agents state initial positions
   - Each agent submits a `Position` object with:
     - `statement`: Their main claim
     - `stance`: Enum from STRONGLY_AGREE to STRONGLY_DISAGREE
     - `probability`: Their confidence (0.0-1.0)
     - `supporting_evidence`: Data sources
     - `assumptions`: Stated assumptions
     - `uncertainty_factors`: Known unknowns

2. **EVIDENCE** - Agents present data sources
   - Submit `Argument` objects with:
     - `premise`: Logical premises
     - `conclusion`: What they conclude
     - `evidence`: Specific data points
     - `citations`: References to sources
     - `logical_validity`: 0.0-1.0 score
     - `empirical_strength`: 0.0-1.0 score

3. **CROSS_EXAMINATION** - Agents question each other
   - Agents challenge unsupported claims
   - Request clarification on assumptions
   - Point out data conflicts

4. **REBUTTAL** - Agents counter-argue
   - Submit `Rebuttal` objects:
     - `target_argument_id`: Which argument they're rebutting
     - `rebuttal_type`: direct, undermining, outweighing
     - `counter_evidence`: Conflicting data
     - `logical_flaws_identified`: List of logical errors
     - `effectiveness_score`: How well the rebuttal lands

5. **CLOSING** - Final statements & convergence assessment
   - Each agent summarizes their evolved position
   - System computes `convergence_score` (0.0-1.0)
   - Identifies key remaining disagreements

6. **DELIBERATION** - Meta-discussion
   - Agents discuss which position best fits overall evidence
   - Consensus builders propose compromises
   - Final positions recorded

**Maximum Rounds**: 3 (configurable)

**Convergence Threshold**: 0.75 (75% agreement needed for strong consensus)

#### 1.3.2 Position Compatibility Scoring

Stances are ordered:
```
STRONGLY_AGREE  >  AGREE  >  PARTIALLY_AGREE  >  NEUTRAL
  >  PARTIALLY_DISAGREE  >  DISAGREE  >  STRONGLY_DISAGREE
```

**Compatibility Score** between two stances:
```
compatibility = 1.0 - (distance / max_distance)
where max_distance = 6 (from STRONGLY_AGREE to STRONGLY_DISAGREE)
```

Example:
- AGREE vs PARTIALLY_AGREE: distance=1 → compatibility = 1 - (1/6) = 0.83
- AGREE vs DISAGREE: distance=3 → compatibility = 1 - (3/6) = 0.50
- AGREE vs STRONGLY_DISAGREE: distance=5 → compatibility = 1 - (5/6) = 0.17

### 1.4 Consensus Building

**Class**: `ConsensusBuilder` ([consensus_builder.py](backend/app/agents/consensus_builder.py#L1))

**Input**: List of `AgentAssessment` objects + optional debate summary

**Output**: `ConsensusResult` object

#### 1.4.1 Voting Mechanisms

The framework supports 6 voting mechanisms:

| Mechanism | Description | Use Case |
|-----------|-------------|----------|
| `WEIGHTED_AVERAGE` | Weight by confidence score | Default; balances confident and uncertain agents |
| `MAJORITY_RULE` | Simple majority wins | When agent count is large |
| `SUPERMAJORITY` | 2/3 agreement required | High-stakes decisions |
| `UNANIMITY` | All agents must agree | Critical assessments |
| `BORDA_COUNT` | Ranked preference tallying | Complex multi-option decisions |
| `CONFIDENCE_WEIGHTED` | Weight by inverse uncertainty | Rewards certain agents more |

**Default**: `WEIGHTED_AVERAGE`

#### 1.4.2 Consensus Strength Classification

```
UNANIMOUS        → All agents fully agree (100% compatibility)
STRONG           → 80%+ agreement on conclusion
MODERATE         → 60-80% agreement
WEAK             → 40-60% agreement
DIVERGENT        → <40% agreement (conflicting evidence)
NO_CONSENSUS     → Cannot determine position
```

#### 1.4.3 Output Structure

**ConsensusResult** contains:
- `consensus_view`: Synthesized conclusion (generated by LLM from agent inputs)
- `consensus_probability`: Estimated likelihood (0.0-1.0)
- `consensus_strength`: One of above enums
- `confidence_level`: Text version ("High", "Moderate", "Low")
- `confidence_score`: Numerical confidence (0.0-1.0)
- `key_findings`: Top 10 findings aggregated across agents
- `supporting_evidence`: Deduplicated evidence citations
- `disagreements`: List of `Disagreement` objects documenting conflicts
- `minority_opinions`: Valid opposing positions preserved
- `uncertainty_factors`: Known limitations and data gaps
- `key_assumptions`: Foundational assumptions
- `agent_contributions`: Each agent's contribution metadata
- `scenarios`: If what-if query, alternative scenarios
- `voting_mechanism_used`: Which mechanism was applied

#### 1.4.4 Disagreement Documentation

When agents disagree, the system documents:

```python
Disagreement(
    agent_ids=["economic", "geopolitical"],
    agent_names=["Economic Analyst", "Geopolitical Strategist"],
    topic="Impact of US-China tensions",
    nature="interpretive",                    # factual, interpretive, methodological, values-based
    severity="major",                         # minor, moderate, major, fundamental
    positions={
        "economic": "Moderate positive impact",
        "geopolitical": "Severe negative impact"
    },
    probabilities={"economic": 0.76, "geopolitical": 0.68},
    conflicting_evidence=[
        "Trade data shows continued growth (economic)",
        "Security alliances shifting (geopolitical)"
    ],
    impact_on_conclusion="high"
)
```

**Minority opinions** are preserved and returned to user:
```json
{
  "position": "Opposing view",
  "agent": "Agent Name",
  "confidence": 0.65,
  "reasoning": "Alternative interpretation of same evidence",
  "supporting_factors": [...]
}
```

### 1.5 Response Generation

**Class**: `ExpertAgentOrchestrator._generate_response()`

**Output**: `OrchestratedResponse` object

**Structure**:
```python
OrchestratedResponse(
    query_context=QueryContext,           # Parsed query details
    consensus=ConsensusResult,            # Consensus object
    agent_assessments={...},              # Each agent's assessment
    debate_conducted=True/False,          # Was debate triggered?
    debate_summary={...},                 # Debate record if conducted
    executive_summary="",                 # Human-readable brief
    key_findings=[...],                   # Top findings
    recommendations=[...],                # Action recommendations
    overall_confidence="High/Moderate/Low",
    confidence_score=0.75,
    disagreements=[...],                  # Documented conflicts
    minority_opinions=[...],              # Opposing positions
    data_sources_cited=[...],             # All sources used
    citations=[...],                      # Specific citations
    uncertainty_factors=[...],            # Limitations
    key_assumptions=[...],                # Foundational assumptions
    scenarios={...},                      # If what-if query
    map_layers=[...],                     # For map visualization
    affected_regions=[...],               # Geographic impact
    timeline=[...],                       # Temporal progression
    causal_chain=[...],                   # Cause→Effect chain
    agents_consulted=[...],               # Which agents used
    processing_time_ms=342.5,             # Performance metric
    timestamp=datetime
)
```

---

## 2. REAL DATA SOURCES (Live Intelligence Feeds)

### 2.1 OSINT Data Aggregation

**Module**: [osint_aggregator.py](backend/app/services/osint_aggregator.py)

**Class**: `OSINTAggregator`

**Caching**: 180-second TTL with in-memory + persistent file caching

#### 2.1.1 Live Data Sources

| Source | API | Category | Updates | Sample Data |
|--------|-----|----------|---------|------------|
| **GDELT** | gdeltproject.org/api/v2 | Global Events | Real-time | Conflicts, protests, elections, sanctions, cyclones, floods |
| **USGS Earthquakes** | earthquake.usgs.gov | Seismic | 15-minute cadence | Magnitude, location, depth, felt reports |
| **NASA EONET** | eonet.gsfc.nasa.gov | Wildfires/Disasters | Daily | Active fires, flood zones, volcanic activity |
| **OpenSky Network** | opensky-network.org/api | Aviation Intelligence | Real-time | Live aircraft positions, routes, origin/destination |
| **Open-Meteo** | open-meteo.com | Weather & Climate | Hourly | Temperature, precipitation, wind, UV index |
| **FRED** | fred.stlouisfed.org/api | Economic Indicators | Economic series | GDP growth, inflation (CPI), unemployment, mortgage rates |
| **World Bank API** | api.worldbank.org | Socioeconomic | Annual/Quarterly | GDP by country, population, development indicators |
| **EIA** | eia.gov/opendata | Energy Markets | Real-time | Oil & gas prices, production, consumption |
| **CISA KEV** | cisa.gov/known-exploited-vulnerabilities | Security | Continuous | Known exploited vulnerabilities, active exploits |
| **data.gov.in** | data.gov.in | Indian Public Data | Variable | Air quality, power, rainfall, public health, agriculture |
| **DuckDuckGo Search** | duckduckgo.com | News/Web | Real-time | News aggregation, search results |
| **Reddit API** | reddit.com/api | Social Media | Real-time | Subreddit discussions, sentiment, trends |
| **Mastodon API** | mastodon.social/api | Social Media | Real-time | Federated social network posts |

#### 2.1.2 GDELT (Global Data on Events, Language, and Tone)

**What**: Real-time global event tracking database

**API Call**:
```
https://api.gdeltproject.org/api/v2/doc/doc?
  query=(conflict OR protest OR election OR sanctions OR cyclone OR flood)
  mode=ArtList
  maxrecords=5
  format=json
  sort=datedesc
```

**Returns**: Recent articles with:
- Headline
- Source URL
- Timestamp
- Relevance score
- Country/location tags
- Event categories (conflict, protest, etc.)

**Fallback**: Hard-coded coordinates for major countries if API unavailable

#### 2.1.3 USGS Earthquake Data

**API**: `earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson`

**Returns**:
- Recent earthquakes (past hour by default)
- Magnitude, latitude, longitude, depth
- Felt reports, tsunami info
- Ready for map visualization

#### 2.1.4 NASA EONET (Earth Observatory Natural Event Tracking)

**API**: `eonet.gsfc.nasa.gov/api/v3/events`

**Tracks**:
- **Wildfires**: Active fire zones with satellite imagery
- **Floods**: Flood-prone regions and active flood events
- **Volcanoes**: Volcanic activity and risk zones
- **Landslides**: Landslide events
- **Droughts**: Drought conditions
- **Severe Storms**: Hurricane, storm tracking

**Returns**: GeoJSON with event geometry, severity, dates

#### 2.1.5 OpenSky Network

**API**: `opensky-network.org/api/states/all`

**Returns**:
- Real-time aircraft positions
- ICAO addresses
- Callsigns
- Velocity vectors
- Altitude
- Origin/destination

**Use Cases**: Supply chain analysis, migration patterns, conflict zone activity

#### 2.1.6 Open-Meteo Weather & Climate

**API**: `api.open-meteo.com/v1/forecast`

**Parameters**: Latitude, longitude, temperature, precipitation, wind speed, UV index

**Returns**: Current + 7-day forecast hourly

#### 2.1.7 FRED (Federal Reserve Economic Data)

**API**: `fred.stlouisfed.org/api/series/{series_id}/observations`

**Key Series IDs**:
- `GDPC1`: Real GDP
- `CPIAUCSL`: Consumer Price Index (inflation)
- `UNRATE`: Unemployment Rate
- `MORTGAGE30US`: 30-year mortgage rate
- `DEXUSEU`: USD-Euro exchange rate
- `DEXUSUK`: USD-GBP exchange rate

**Updates**: Monthly to quarterly

#### 2.1.8 EIA Energy Data

**API**: `api.eia.gov/series/{series_id}/data`

**Key Series**:
- Crude oil prices (WTI, Brent)
- Natural gas prices
- Gasoline/diesel prices
- Production and consumption by country

#### 2.1.9 CISA Known Exploited Vulnerabilities

**API**: `cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`

**Returns**:
- CVE IDs currently being exploited
- Vulnerability descriptions
- Attack vectors
- Patch availability

#### 2.1.10 data.gov.in (Indian Government Data)

**Discovery Mechanism**: Web scraping + API lookup

**Queries Searched**:
```
air quality, power generation, rainfall, public health, agriculture
```

**Resources Found**:
- Air quality index by city
- Power generation capacity and distribution
- IMS rainfall data
- Health ministry datasets
- Agricultural production statistics

**Cache**: Persistent file at `backend/app/data/data_gov_catalog_cache.json` (updated on discovery)

### 2.2 Real vs. Mocked Data in Runtime Intelligence

**Module**: [runtime_intelligence.py](backend/app/services/runtime_intelligence.py)

**Class**: `RuntimeIntelligenceEngine`

#### 2.2.1 Data Layering Strategy

The system uses **annotation** to distinguish data provenance:

```python
signal = self._annotate_signal(signal, source_mode)
# Returns: { ...signal, "source_mode": "runtime" or "seeded", "source_origin": "..." }
```

**Source Modes**:
- `"runtime"`: Real-time data from live APIs / OSINT pulls
- `"seeded"`: Pre-loaded mock data from store
- `"runtime_plus_seeded"`: Combined from both

#### 2.2.2 Runtime State Persistence

**File**: `backend/app/data/runtime_state.json`

**Managed by**: `RuntimeIntelligenceEngine`

**Contains**:
```python
{
  "dynamic_signals": [...],         # OSINT-fetched signals
  "runtime_assets": [...],          # Discovered geopolitical assets
  "runtime_corridors": [...],       # Trade routes, shipping lanes
  "source_health": [...],           # API availability status
  "market_snapshot": [...],         # Economic ticker data
  "country_catalog": [...],         # Live country enrichment
  "last_refresh": timestamp
}
```

**Refresh Interval**: 300 seconds (5 minutes)

**Warm-up**: On startup, pulls top 5 high-risk countries from OSINT to cache country briefs

#### 2.2.3 Country Enrichment Pipeline

**Base Data** (seeded from store):
```python
{
  "id": "CTR-IND",
  "name": "India",
  "region": "South Asia",
  "lat": 20.5937,
  "lng": 78.9629,
  ...
}
```

**Runtime Enrichment** (computed):
```python
{
  "risk_index": min(95, max(22, 20 + signals*10 + assets*2)),
  "influence_index": min(98, max(18, pop/25M + assets*3 + signals*2)),
  "stability": _stability_from_risk(risk),
  "active_signals": count_of_dynamic_signals,
  "runtime_signal_count": count_from_osint,
  "seeded_signal_count": count_from_store,
  "asset_count": count_of_military_assets,
  "top_domains": sorted_by_relevance,
  "country_catalog_mode": "runtime" if live_catalog else "seeded"
}
```

#### 2.2.4 Signal/Corridor/Asset Merging

**Algorithm**: Runtime data + seeded data

```python
def get_dynamic_signals(include_seeded=True):
    base = get_seeded_signals() if include_seeded else []
    dynamic = get_runtime_signals()
    
    merged = []
    seen = set()
    
    for signal in dynamic + base:  # Prioritize runtime
        if signal.get("id") not in seen:
            seen.add(signal.get("id"))
            merged.append(signal)
    
    return merged  # Deduplicated, runtime-prioritized
```

---

## 3. DUMMY / SEEDED DATA (Civic Domain)

### 3.1 Seeded Civic Dataset

**Module**: [seed.py](backend/app/data/seed.py) + [global_seed.py](backend/app/data/global_seed.py)

**Generation**: Generated once on first store access, cached in memory

### 3.2 Domestic Civic Data (India-Specific)

**Table**: Constituencies, Wards, Booths, Citizens, Schemes, Workers, Projects, Complaints

#### 3.2.1 Constituency Structure

Sample Data:
```python
{
  "id": "CONST-MH-001",         # Maharashtra constituency 1
  "name": "Mumbai East",
  "state": "Maharashtra",
  "total_population": 1_500_000,
  "booths": 1200,
  "wards": 120,
  "avg_sentiment": 68,          # 0-100 scale
  "lat": 19.0176,
  "lng": 72.8479,
  "demographics": {
    "young": 0.35,              # Age distribution
    "working_age": 0.55,
    "elderly": 0.10
  }
}
```

**Total**: Multiple constituencies seeded

#### 3.2.2 Ward Hierarchy

```
Constituency
  └─ Ward (subdivisions)
      └─ Booth (polling locations)
          └─ Citizens
```

#### 3.2.3 Booth Data

Sample:
```python
{
  "id": "BOOTH-MH-001-A",
  "constituency_id": "CONST-MH-001",
  "ward_id": "WARD-MH-001-A",
  "booth_number": 1,
  "population": 1250,
  "location": "School 47",
  "lat": 19.0181,
  "lng": 72.8485,
  "segments": {
    "rural": 100,
    "urban": 1150
  },
  "scheme_coverage": {
    "SCHEME-PM-KISSAN": 450,     # How many enrolled
    "SCHEME-MGNREGA": 200,
    "SCHEME-UPF": 350
  }
}
```

#### 3.2.4 Citizens (Synthetic)

Generated: ~100,000 synthetic citizens across booths

```python
{
  "id": "CIT-0001",
  "booth_id": "BOOTH-MH-001-A",
  "name": "Synthetic Citizen Name",
  "age": 45,
  "segment": "urban",           # rural, urban, semi-urban
  "enrolled_schemes": ["SCHEME-PM-KISSAN", "SCHEME-UPF"],
  "sentiment": 72,              # 0-100 scale
}
```

**Distribution**: Population proportional to booth allocation

#### 3.2.5 Government Schemes

Sample Schemes:
```python
[
  {
    "id": "SCHEME-PM-KISSAN",
    "name": "PM-KISAN (Farmer Income Support)",
    "target_segment": "rural",
    "coverage": 1_500_000,        # Enrollees
    "budget": 500_000_000_000,    # ₹ (500M)
  },
  {
    "id": "SCHEME-MGNREGA",
    "name": "MGNREGA (Rural Jobs)",
    "target_segment": "rural",
    "coverage": 2_200_000,
    "budget": 750_000_000_000,
  },
  {
    "id": "SCHEME-UPF",
    "name": "Ujjwala (Cooking Gas)",
    "target_segment": "All",
    "coverage": 9_200_000,
    "budget": 1_200_000_000_000,
  },
  ...
]
```

#### 3.2.6 Workers (Field Operations)

Sample:
```python
{
  "id": "WORKER-001",
  "name": "Ramesh Kumar",
  "assigned_constituency": "CONST-MH-001",
  "assigned_booth": "BOOTH-MH-001-A",
  "status": "active",           # active, inactive, suspended
  "role": "scheme_mobilizer",   # scheme_mobilizer, field_officer, coordinator
  "contact": "+91-9876543210",
  "performance_score": 78,      # 0-100
}
```

#### 3.2.7 Projects (Development)

Sample:
```python
{
  "id": "PROJECT-001",
  "name": "Water Supply Network Upgrade",
  "ward": "WARD-MH-001-A",
  "status": "in_progress",      # planned, in_progress, completed
  "budget": 50_000_000,         # ₹ 5 Cr
  "progress_percentage": 65,
  "completion_date": "2026-06-30",
}
```

#### 3.2.8 Complaints (Civic Feedback)

Sample:
```python
{
  "id": "COMPLAINT-001",
  "booth_id": "BOOTH-MH-001-A",
  "category": "water",          # water, electricity, sanitation, roads, health
  "description": "Irregular water supply in sector 5",
  "sentiment": "negative",      # positive, negative, neutral
  "timestamp": "2026-03-15T10:30:00Z",
  "status": "open"              # open, in_progress, resolved
}
```

### 3.3 Global Seeded Data

**Module**: [global_seed.py](backend/app/data/global_seed.py)

**Class**: `GlobalOntologyBuilder`

#### 3.3.1 Country Nodes (Seeded)

Base countries with static properties:

```python
{
  "id": "CTR-IND",
  "name": "India",
  "region": "South Asia",
  "iso3": "IND",
  "capital": "New Delhi",
  "lat": 20.5937,
  "lng": 78.9629,
  "population": 1_417_000_000,
  "risk_index": 45,            # 0-100 baseline
  "influence_index": 68,
  "sentiment": 72,
  "stability": "Elevated",
  "top_domains": ["Economics", "Geopolitics", "Infrastructure"],
}
```

**Total Countries**: ~195 sovereign + entities

#### 3.3.2 Signals (Seeded)

Pre-loaded global intelligence signals:

```python
{
  "id": "SIG-001",
  "country_id": "CTR-PAK",
  "category": "geopolitical",   # economic, geopolitical, climate, social, conflict
  "title": "Border tensions with military mobilization",
  "description": "...",
  "severity": "High",           # Low, Medium, High
  "timestamp": "2026-03-20T...",
  "layer": "conflict",
}
```

#### 3.3.3 Assets (Military/Strategic)

Seeded strategic assets:

```python
{
  "id": "ASSET-001",
  "country_id": "CTR-CHN",
  "type": "naval_base",         # naval_base, military_facility, port, airport, etc.
  "name": "Spratlys Naval Complex",
  "lat": 8.6753,
  "lng": 111.8944,
  "layer": "defense",           # defense, conflict, mobility, infrastructure, cyber
}
```

#### 3.3.4 Corridors (Trade Routes)

Seeded geopolitical corridors:

```python
{
  "id": "CORR-001",
  "from_country": "CTR-IND",
  "to_country": "CTR-USA",
  "corridor_type": "trade",     # trade, shipping, air, digital
  "name": "India-USA Trade Route",
  "volume": 150_000_000_000,    # Annual trade volume USD
}
```

#### 3.3.5 Knowledge Graph (Seeded)

Neo4j-style graph structure:

```python
{
  "nodes": [
    {"id": "CTR-IND", "group": "Country", "label": "India"},
    {"id": "CTR-CHN", "group": "Country", "label": "China"},
    {"id": "ACTOR-TechSector", "group": "Actor", "label": "Tech Sector"},
    ...
  ],
  "links": [
    {"source": "CTR-IND", "target": "ACTOR-TechSector", "label": "DRIVES"},
    {"source": "CTR-IND", "target": "CTR-USA", "label": "PARTNERS"},
    ...
  ]
}
```

---

## 4. COMPLETE FEATURE LIST

### 4.1 Core APIs

#### 4.1.1 **Unified Intelligence API** (`/unified`)

**Endpoint**: `POST /unified/analyze`

**Purpose**: Single entry point for all AI platform capabilities

**Capabilities Activated Automatically**:
1. **Reasoning**: Multi-agent expert analysis with debate & consensus
2. **Tools**: Real-time OSINT data fetching
3. **Visuals**: Chart and diagram generation
4. **Map Intelligence**: Geographic visualization

**Request**:
```json
{
  "query": "Analyze India's economic growth drivers",
  "context": {
    // Optional: domain hints, historical data, etc.
  },
  "forced_capabilities": ["reasoning", "visuals"],  // Optional override
  "max_processing_time": 30
}
```

**Response**:
```json
{
  "status": "success",
  "query_id": "q_abc123",
  "assessment": {...},          // Query complexity analysis
  "reasoning": {...},           // Multi-agent output
  "tools": {...},               // OSINT data gathered
  "visuals": {...},             // Generated charts/diagrams
  "map_intelligence": {...},    // Geographic data
  "unified_summary": "...",     // Synthesized summary
  "confidence_score": 0.78,
  "capabilities_activated": ["reasoning", "tools", "visuals"]
}
```

**Example Queries**:
- "Analyze India's economic growth and generate visualizations" → reasoning + visuals
- "What are latest trends on climate change?" → tools + reasoning
- "Compare GDP of India and China" → reasoning + tools + visuals + map

**Sub-endpoint**: `POST /unified/assess`
- Same query, returns only assessment (no execution)
- Useful for preview before running full analysis

#### 4.1.2 **Intelligence Engine API** (`/intelligence`)

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/dashboard/executive` | GET | Aggregated KPIs (civic data) |
| `/query` | POST | Natural language query against civic data |

**Examples**:
```bash
# Get executive KPIs
GET /intelligence/dashboard/executive

# Query example
POST /intelligence/query
{
  "query": "What is total enrollment in PM-KISAN across Maharashtra?"
}
```

#### 4.1.3 **Data API** (`/data`)

**Global Data Endpoints**:

| Endpoint | Method | Purpose | Returns |
|----------|--------|---------|---------|
| `/stats` | GET | System statistics | Total cities, countries, signals |
| `/global/overview` | GET | World overview metrics | Global overview object |
| `/global/countries` | GET | List all countries | Enriched countries + risk indices |
| `/global/country/{id}` | GET | Single country details | Detailed country analysis |
| `/global/signals` | GET | Global intelligence signals | Filtered by category/severity/country |
| `/global/assets` | GET | Military/strategic assets | Geo-tagged strategic assets |
| `/global/corridors` | GET | Trade routes & geopolitical connections | Shipping lanes, trade routes |
| `/global/map` | GET | Map visualization data | GeoJSON-ready format |
| `/global/graph` | GET | Knowledge graph | Nodes and edges for visualization |
| `/global/country-analysis/{id}` | GET | Detailed country analysis | Signals, assets, risks specific to country |

**Query Parameters** (for `/global/signals`, `/global/assets`, `/global/corridors`):
- `source_mode`: "runtime", "seeded", or combined (default)
- `category`, `severity`, `country_id`, `layer`: Filters

**Example Queries**:
```bash
# High-risk countries
GET /data/global/countries?min_risk=70

# Geopolitical signals
GET /data/global/signals?category=geopolitical&severity=High

# Military assets in Pakistan
GET /data/global/assets?country_id=CTR-PAK&layer=defense
```

**Domestic Data Endpoints** (Indian civic data):

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `/constituencies` | List all constituencies | Constituencies with stats |
| `/constituency/{id}` | Single constituency | Detailed breakdown |
| `/wards/{con_id}` | Wards in constituency | Ward-level data |
| `/booths/{con_id}` | Booths in constituency | Booth locations and stats |
| `/booth/{id}/segments` | Demographic breakdown | Population segments |
| `/booth/{id}/schemes` | Scheme coverage | Enrolled citizens by scheme |
| `/booth/{id}/complaints` | Citizen complaints | Open/resolved issues |
| `/workers` | Field workers | Worker records filtered by status |
| `/projects` | Development projects | Project status and timelines |
| `/sentiment/timeline` | Sentiment trends | Historical sentiment data |

#### 4.1.4 **Visual Intelligence API** (`/visual-intelligence`)

**Endpoints**:

| Endpoint | Purpose | Outputs |
|----------|---------|---------|
| `/analyze` | Process query with visual outputs | Charts, diagrams, insights |
| `/parse-intent` | Extract intent from query | Domains, countries, intent type |
| `/generate-chart` | Create chart from data | Chart URL (QuickChart) |
| `/generate-diagram` | Generate explanatory diagram | Diagram URL (AI-generated image) |
| `/find-data` | Fetch data for visualization | Raw data + metadata |

**Request Example**:
```json
{
  "query": "How has India's inflation rate changed over the past 5 years?",
  "force_chart_type": "line",
  "include_map": true,
  "include_expert_analysis": true
}
```

**Response Includes**:
- Chart URL (with historical inflation data)
- Diagram explaining inflation drivers
- Map showing regional inflation variance
- Expert analysis from Economic Agent

#### 4.1.5 **Map Commands API** (`/map`)

**Real-time map visualization control**

**Endpoints**:

| Endpoint | Purpose |
|----------|---------|
| `POST /map/command/highlight` | Highlight countries on map |
| `POST /map/command/route` | Draw trade route/corridor |
| `POST /map/command/heatmap` | Display data as heatmap |
| `POST /map/command/focus` | Focus on country with zoom |
| `POST /map/command/marker` | Place marker at lat/lng |
| `POST /map/command/overlay` | Complex overlay visualization |
| `GET /map/commands` | List active commands |
| `DELETE /map/command/{id}` | Clear specific command |

**Example**:
```bash
# Highlight China and India with pulse effect
POST /map/command/highlight
{
  "country_ids": ["CTR-CHN", "CTR-IND"],
  "color": "#f59e0b",
  "pulse": true,
  "priority": "high"
}

# Draw conflict route
POST /map/command/route
{
  "from_country": "CTR-PAK",
  "to_country": "CTR-IND",
  "route_type": "conflict_front",
  "color": "#dc2626"
}
```

#### 4.1.6 **Outreach API** (`/actions`)

**Hyperlocal engagement endpoints**

Likely features (based on structure):
- Scheme mobilization campaigns
- Targeted messaging by constituency
- Worker assignment / task management
- Complaints resolution tracking
- Sentiment-based targeting

#### 4.1.7 **Data Ingestion Pipeline** (`/ingestion`)

**Endpoints for data loading**:
- Batch upload of civic data
- Real-time signal ingestion OSINT
- Complaint receipt and classification
- News feed ingestion

#### 4.1.8 **Classified / Sovereign Pipeline** (`/classified`)

**Secure, air-gappable intelligence pipeline**:
- Local-only data ingestion
- Encrypted classified data handling
- Sovereign compute without external API calls
- Offline reasoning capability

### 4.2 Expert Agent Capabilities

**Available Expert Agents**:

1. **Economic Agent**: GDP analysis, inflation, trade, markets, economic forecasting
2. **Geopolitical Agent**: Military dynamics, diplomatic relations, alliances, conflicts
3. **Social Agent**: Sentiment analysis, public opinion, protests, social movements
4. **Climate Agent**: Disaster tracking, weather extremes, environmental impact
5. **Policy Agent**: Government policies, legislative changes, governance
6. **Risk Agent**: Cross-domain risk quantification, aggregate risk assessment
7. **Simulation Agent**: What-if scenarios, future projections, time-series forecasting

### 4.3 Specialized Engines

#### 4.3.1 **Battleground Simulation Engine**

Appears to support:
- Military scenario modeling
- Conflict simulation between countries
- Force deployment visualization
- Strategic analysis of hypothetical conflicts
- Front-line projections

**Map Integration**: Publishes battleground overlays to map visualization

#### 4.3.2 **Intent Parser**

- Extracts query intention type (analyze, forecast, compare, simulate)
- Identifies domains (economic, geopolitical, social, climate, policy)
- Extracts entity mentions (countries, regions, concepts)
- Classifies query complexity

#### 4.3.3 **Evidence & Citation Tracker**

- Tracks all data sources used in analysis
- Maintains citation chain for claims
- Documents assumptions and caveats
- Grades source reliability

#### 4.3.4 **Uncertainty Engine**

- Quantifies uncertainty in agent assessments
- Identifies data gaps
- Documents assumptions explicitly
- Assigns confidence levels

### 4.4 Integration Points

#### 4.4.1 **Neo4j Graph Database**

**Optional Integration**: `CivicIntelligenceQA` class in osint_aggregator.py

**Capabilities**:
- Natural language to Cypher query generation
- Knowledge graph querying
- Graph relationship analysis
- Civic data graph queries

**Benefits** (if deployed):
- Complex relationship queries
- Path-finding (which countries can reach each other?)
- Community detection
- Influence propagation analysis

#### 4.4.2 **Redis Caching**

**Optional Integration**: Query result caching

- 5-minute TTL for expensive queries
- Question hashing for cache lookup
- Configurable cache eviction

#### 4.4.3 **External API Integrations**

- **QuickChart** (chart generation): Via custom URL builder
- **Pollinations** (diagram generation): AI image generation
- **LLM Providers**: Groq (Llama 3.3-70B) + Gemini (fallback)

---

## 5. COMPLETE QUERY FLOW (User Input → Final Output)

### 5.1 Detailed Request-Response Pipeline

#### 5.1.1 User Submits Query

**User Input** (Example):
```
"How will India's economic slowdown impact South Asian geopolitics 
 and what are the risks to supply chain stability?"
```

#### 5.1.2 Request Routing

**Endpoint Hit**: `POST /unified/analyze`

```json
{
  "query": "How will India's economic slowdown impact South Asian geopolitics...",
  "context": {},
  "forced_capabilities": null
}
```

#### 5.1.3 Capability Assessment

**Module**: `UnifiedIntelligenceAssessor`

**Assessment Output**:
```python
QueryAssessment(
    complexity="high",  # low, moderate, high
    domains_detected=["economic", "geopolitical", "policy"],
    entities_detected=["India", "South Asia"],
    recommended_capabilities=["reasoning", "tools", "visuals"],
    reasoning_required=True,
    tools_required=True,
    visuals_required=True,
    map_intelligence_required=True,
    processing_approach="parallel_all",  # Execute all in parallel
    estimated_processing_time_ms=5000
)
```

#### 5.1.4 Agent Orchestrator Activation

**Step 1: Query Parsing**
```python
query_context = orchestrator._parse_query(query)

# Output:
QueryContext(
    primary_domain=QueryDomain.ECONOMIC,
    secondary_domains=[QueryDomain.GEOPOLITICAL, QueryDomain.POLICY],
    domain_confidence={"economic": 0.45, "geopolitical": 0.40, "policy": 0.15},
    countries=["India"],
    regions=["South Asia"],
    is_what_if=False,
    is_forecast=True,
    is_comparison=False,
    is_historical=False,
)
```

**Step 2: Data Enrichment**
```python
enriched_context = await orchestrator._enrich_context(context, query)

# Fetches from:
# - runtime_engine.get_enriched_countries()  → India + South Asian countries
# - runtime_engine.get_global_overview()     → Systemic stress indicators
# - runtime_engine.get_dynamic_signals()     → Active intelligence signals
# - store.get_stats()                        → Domestic stats
# - Economic indicators aggregation

enriched_context = {
    "global_overview": { ... },
    "countries": [India, Pakistan, Bangladesh, ...],
    "relevant_countries": [India],
    "active_signals": [signal1, signal2, ...],
    "signals_by_category": {"geopolitical": [...], "economic": [...]},
    "economic_indicators": { ... },
    "risk_indices": { ... },
    ...
}
```

**Step 3: Agent Selection**
```python
selected_agents = orchestrator._select_agents(query_context)

# Selected:
# - economic (primary domain match)
# - geopolitical (secondary domain match)
# - policy (secondary domain match)
# - risk (always)
# → 4 agents total

selected = [risk_agent, economic_agent, geopolitical_agent, policy_agent]
```

**Step 4: Parallel Agent Execution**
```python
assessments = await orchestrator._run_agents_parallel(selected_agents, query, context)

# Each agent runs concurrently via asyncio.gather():
# - EconomicAgent.assess(query, context)
# - GeopoliticalAgent.assess(query, context)
# - PolicyAgent.assess(query, context)
# - RiskAgent.assess(query, context)

# Returns: Dict[agent_id -> AgentAssessment]
assessments = {
    "economic": AgentAssessment(...),         # confidence: 0.78
    "geopolitical": AgentAssessment(...),     # confidence: 0.65
    "policy": AgentAssessment(...),           # confidence: 0.71
    "risk": AgentAssessment(...),             # confidence: 0.73
}
```

**Step 5: Divergence Check & Debate**
```python
should_debate = orchestrator._should_conduct_debate(assessments)

# Check confidence divergence:
confidences = [0.78, 0.65, 0.71, 0.73]
max_conf = 0.78
min_conf = 0.65
divergence = max_conf - min_conf = 0.13

# Is 0.13 > debate_threshold (0.25)? NO → NO DEBATE

# However, if it were YES:
debate_summary = await orchestrator._debate_system.initiate_debate(
    topic="economic_geopolitical_slowdown",
    question="Exact query...",
    agents=[economic_agent, geopolitical_agent, ...],
    initial_assessments=assessments
)

# Debate runs through:
# OPENING → EVIDENCE → CROSS_EXAMINATION → REBUTTAL → CLOSING → DELIBERATION
# (max 3 rounds)

debate_summary = {
    "rounds": [...],
    "final_positions": {...},
    "convergence_score": 0.82,
    "key_disagreements": [...],
    "emerging_consensus": "..."
}
```

**Step 6: Consensus Building**
```python
consensus = orchestrator._consensus_builder.build_consensus(
    query=query,
    assessments=list(assessments.values()),
    debate_summary=None,  # Since no debate occurred
    mechanism=VotingMechanism.WEIGHTED_AVERAGE
)

# Aggregation:
# consensus_probability = weighted_avg([0.78, 0.65, 0.71, 0.73] with weights)
# consensus_strength = MODERATE (since not all agree)
# disagreements = [{"Economic vs Geopolitical": "..."}]
# minority_opinions = [Geopolitical agent's opposing view]

consensus = ConsensusResult(
    consensus_view="India's economic slowdown will moderately impact South Asian geopolitics...",
    consensus_probability=0.707,
    consensus_strength=ConsensusStrength.MODERATE,
    confidence_score=0.707,
    key_findings=[...],
    uncertainty_factors=["Global liquidity conditions", "Regional policy responses"],
    disagreements=[...],
    minority_opinions=[...]
)
```

**Step 7: Tools / OSINT Layer**

Simultaneously, if `tools` capability activated:
```python
osint_results = await osint_engine.fetch_live_data(query)

# Calls:
# - get_gdelt_data()                 → Global events
# - get_earthquake_data()            → Seismic activity
# - get_nasa_eonet_data()           → Disasters
# - get_economic_indicators()        → FRED data
# - get_country_search_briefs()      → Country-specific news

osint_results = {
    "gdelt_articles": [...],
    "earthquake_events": [...],
    "economic_indicators": {"inflation": 6.8, "gdp_growth": 6.5, ...},
    "country_briefs": {...},
    "sources_accessed": ["GDELT", "FRED", "USGS", ...]
}
```

**Step 8: Visuals / Chart Generation**

If `visuals` capability activated:
```python
visual_results = await visual_engine.generate_visuals(query, osint_results)

# Generates:
# - Chart: India's GDP growth trend (7-year history) via QuickChart
# - Diagram: Causality chain (slowdown → investment drop → FDI reduction → regional tensions)
# - Heatmap: Regional risk scores
# - Map commands: Highlight India + South Asian countries

visual_results = {
    "charts": [
        {
            "type": "line",
            "title": "India GDP Growth Trend",
            "url": "https://quickchart.io/...",
            "data": {...}
        },
        ...
    ],
    "diagrams": [
        {
            "type": "cause_effect",
            "title": "Economic Slowdown Impact Chain",
            "url": "https://image.pollinations.ai/...",
        },
        ...
    ],
    "map_commands": [
        {"type": "highlight", "countries": ["CTR-IND"], ...},
        {"type": "heatmap", "metric": "economic_risk", ...},
        ...
    ]
}
```

**Step 9: Final Response Generation**
```python
orchestrated_response = orchestrator._generate_response(
    query_context,
    assessments,
    consensus,
    debate_summary=None,
    context=enriched_context
)

orchestrated_response = OrchestratedResponse(
    query_context=query_context,
    consensus=consensus,
    agent_assessments=assessments,
    debate_conducted=False,
    debate_summary=None,
    executive_summary="""
        India's moderately paced economic slowdown, if sustained,
        poses moderate risks to South Asian geopolitical stability...
    """,
    key_findings=[
        "FDI inflows to India slowing from 2024 peak of $85B",
        "Regional supply chain integration rising despite tensions",
        "Pakistan and Bangladesh competing for manufacturing FDI",
        "Geopolitical risks in Kashmir region elevated",
        "Climate-driven migration pressures increasing"
    ],
    recommendations=[
        "Maintain stable interest rate regime",
        "Deepen economic integration via BIMSTEC",
        "Invest in supply chain diversification"
    ],
    overall_confidence="Moderate",
    confidence_score=0.707,
    disagreements=[
        {
            "agents": ["Economic", "Geopolitical"],
            "nature": "interpretive",
            "position": "Magnitude of geopolitical impact"
        }
    ],
    minority_opinions=[
        {
            "agent": "Geopolitical Agent",
            "position": "Slowdown could accelerate shifts to China-aligned partners",
            "confidence": 0.65
        }
    ],
    data_sources_cited=["FRED", "World Bank", "GDELT", "runtime_signals"],
    citations=[
        {
            "claim": "India GDP growth at 6.5%",
            "source": "FRED GDPC1",
            "timestamp": "2026-Q4"
        },
        ...
    ],
    uncertainty_factors=[
        "Global monetary policy normalization timing",
        "Geopolitical escalation scenarios"
    ],
    key_assumptions=[
        "Baseline assumption: No major escalation in India-China border"
    ],
    scenarios={
        "optimistic": "Strong policy response restores 7%+ growth",
        "baseline": "Moderate slowdown, 6-6.5% range",
        "pessimistic": "Structural slowdown to 5% + spillovers"
    },
    map_layers=[
        {"type": "risk_heatmap", "data": [...]},
        {"type": "country_markers", "data": [...]}
    ],
    affected_regions=["South Asia", "Southeast Asia"],
    timeline=[
        {"event": "Slowdown onset", "date": "2025-Q2"},
        {"event": "FDI decline accelerates", "date": "2025-Q4"},
        {"event": "Regional imbalance emerges", "date": "2026-Q1"}
    ],
    causal_chain=[
        "India economic slowdown" →
        "FDI inflows decline" →
        "Neighborhood countries gain relative attractiveness" →
        "China deepens influence inroads" →
        "Regional geopolitical balance shifts"
    ],
    agents_consulted=["economic", "geopolitical", "policy", "risk"],
    processing_time_ms=4234.5
)
```

#### 5.1.5 Unified Response Assembly

**Module**: `UnifiedIntelligenceEngine`

```python
unified_response = UnifiedIntelligenceResponse(
    query_id="q_xyz789",
    conversation_id="conv_abc123",
    query=query,
    assessment=query_assessment,              # From step 3
    reasoning=orchestrated_response,          # From step 9
    tools=osint_results,                      # From step 7
    visuals=visual_results,                   # From step 8
    map_intelligence=map_visualization,       # Generated from map commands
    unified_summary="""
        Based on multi-agent analysis: India's economic slowdown...
        [Synthesized from all modes above]
    """,
    assistant_response={
        "type": "intelligence_brief",
        "tone": "analytical",
        "content": "..."
    },
    confidence_score=0.707,
    data_sources_used=["FRED", "World Bank", "GDELT", "runtime", "seeded"],
    capabilities_activated=["reasoning", "tools", "visuals", "map_intelligence"],
    capability_statuses={
        "reasoning": "success",
        "tools": "success",
        "visuals": "success",
        "map_intelligence": "success"
    },
    total_processing_time_ms=4234.5,
    timestamp=datetime.now(timezone.utc)
)
```

#### 5.1.6 JSON Response to User

```json
{
  "status": "success",
  "query_id": "q_xyz789",
  "conversation_id": "conv_abc123",
  "query": "How will India's economic slowdown impact South Asian geopolitics...",
  
  "assessment": {
    "complexity": "high",
    "domains_detected": ["economic", "geopolitical", "policy"],
    "recommended_capabilities": ["reasoning", "tools", "visuals"]
  },
  
  "reasoning": {
    "query_context": {...},
    "consensus": {
      "consensus_view": "...",
      "consensus_probability": 0.707,
      "confidence_score": 0.707,
      "strength": "moderate"
    },
    "key_findings": [...],
    "recommendations": [...],
    "disagreements": [...],
    "minority_opinions": [...]
  },
  
  "tools": {
    "gdelt_articles": [...],
    "economic_indicators": {...},
    "sources_accessed": [...]
  },
  
  "visuals": {
    "charts": [
      {
        "type": "line",
        "title": "India GDP Growth",
        "url": "https://quickchart.io/...",
        "data": {...}
      }
    ],
    "diagrams": [...]
  },
  
  "map_intelligence": {
    "commands": [...],
    "layers": [...],
    "affected_regions": ["South Asia", "Southeast Asia"]
  },
  
  "unified_summary": "Synthesized analysis across all modes...",
  "confidence_score": 0.707,
  "data_sources_used": ["FRED", "World Bank", "GDELT", ...],
  "capabilities_activated": ["reasoning", "tools", "visuals", "map_intelligence"],
  "total_processing_time_ms": 4234.5,
  "timestamp": "2026-03-27T15:42:30Z"
}
```

---

## SUMMARY TABLE

| Aspect | Details |
|--------|---------|
| **Agent Count** | 7 expert agents (economic, geopolitical, social, climate, policy, risk, simulation) |
| **Debate Mechanism** | Triggered when confidence divergence > 0.25; max 3 rounds; 6 debate phases |
| **Consensus Voting** | 6 mechanisms; default weighted_average by confidence |
| **Real Data Sources** | 13 major APIs: GDELT, USGS, NASA, OpenSky, Open-Meteo, FRED, World Bank, EIA, CISA, data.gov.in, DuckDuckGo, Reddit, Mastodon |
| **Seeded Data** | ~195 countries + ~100K synthetic citizens + civic schemes (India) |
| **Processing** | Fully asynchronous; parallel agent execution; typical latency 4-7 seconds |
| **Main Endpoints** | `/unified/analyze` (single entry point); 30+ supporting endpoints |
| **Visualizations** | QuickChart (charts), Pollinations (diagrams), custom map command engine |
| **Graceful Degradation** | If one capability fails, others continue; results still returned |

---

## END OF DOCUMENT

**Next Steps for Users**:
1. Query the system via `/unified/analyze` for comprehensive intelligence
2. Use specialized endpoints (`/data`, `/intelligence`, `/visual-intelligence`) for domain-specific needs
3. Consult `/map` endpoints for real-time geopolitical visualization
4. Refer to debate output for understanding disagreements and trade-offs
