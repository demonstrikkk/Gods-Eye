# Gods-Eye OS Architecture

## 1. Architecture Intent

Gods-Eye OS is designed as a dual-domain intelligence system:

- Civic domain for constituency and booth-level governance operations
- Global domain for world-scale risk, signals, and strategic infrastructure

The architecture prioritizes:

- Evidence grounding over speculative output
- Graceful degradation under partial source failures
- Fast local operability with optional external connectors
- A UI that allows operational drill-down from macro to micro levels

## 2. Logical Architecture

```text
Open Data + Social + RSS + Search
                                                |
                                                v
        Connector/OSINT Aggregator Layer
                                                |
                                                v
         Runtime Intelligence Engine  <----> runtime_state.json
                                                |
                                                +----> In-memory Civic/Global Store
                                                |
                                                v
                        FastAPI Domain APIs
                                                |
                                                v
        React Query + Zustand State Layer
                                                |
                                                v
        Globe/Map/Sidebar/Dashboards/AI Console
```

## 3. Runtime Components

### 3.1 API and Bootstrap

- Application starts in `backend/app/main.py`
- API roots are mounted via `backend/app/api/router.py`
- Startup lifecycle launches:
        - `feed_engine.start()`
        - `runtime_engine.start()`

### 3.2 Data and State Layers

1. Seeded in-memory data store (`backend/app/data/store.py`)
2. Runtime persisted state (`backend/app/data/runtime_state.json`)
3. Optional graph persistence path via Neo4j (`backend/app/models/graph_schema.py`)
4. Optional relational DB path via SQLAlchemy async engine (`backend/app/core/database.py`)

### 3.3 Intelligence Engines

- `runtime_intelligence.py`
        - Periodically captures and normalizes data from OSINT connectors
        - Builds dynamic signals and source-health snapshots
        - Produces enriched countries and country briefs
        - Persists merged runtime state for continuity

- `feed_aggregator.py`
        - Fetches multi-source RSS/news concurrently
        - Deduplicates and classifies briefs
        - Injects extra OSINT snippets
        - Pushes each brief to civic text processing asynchronously

- `strategic_agent.py`
        - Planner -> tool selection -> parallel tool execution -> reasoning synthesis
        - Tool output sanitation and explicit unavailable-tool reporting
        - Grounded fallback response when reasoning or data is unavailable

- `intelligence_engine.py`
        - LangGraph-style civic text processing graph
        - Entity extraction -> sentiment scoring -> geography enrichment -> action recommendation
        - Controlled by `CIVIC_AGENT_MOCK_MODE` flag (default currently true)

## 4. API Domains

### 4.1 Intelligence Endpoints

- NL query endpoint with graph-aware fallback logic
- Strategic analysis endpoint with multi-tool orchestration
- What-if simulation endpoint
- News insight endpoint for feed-context synthesis
- Executive KPI endpoint

### 4.2 Data Endpoints

- Global ontology endpoints: overview, countries, signals, assets, corridors, graph
- Country analysis endpoint combining multi-source evidence
- Civic endpoints: constituencies, booths, citizens, workers, schemes, complaints, projects
- Runtime monitoring endpoints: source-health, markets, feeds, alerts

### 4.3 Action/Ingress Endpoints

- Unstructured ingestion endpoint for civic text intelligence
- Outreach campaign deployment endpoint (queue-oriented pattern)

## 5. Agentic System Architecture

### 5.1 Strategic Agent Pipeline

```text
User Query
         |
         v
Planner Prompt
         |
         v
Validated Tool Plan
         |
         v
Parallel Tool Execution (timeouts + sanitization)
         |
         v
Reasoning Prompt (grounded data only)
         |
         v
Structured Strategic Output + Meta Diagnostics
```

Key controls:

- Planner normalization (valid tool filtering, cap on tool count)
- Per-tool timeout and error capture
- Strict unavailable/fallback marking
- Forced civic grounding tool inclusion
- Predictable fallback object when no trusted evidence is available

### 5.2 Civic Ingestion Agent Pipeline

```text
Raw Text Input
         |
         v
Extract Entities
         |
         v
Analyze Sentiment/Urgency
         |
         v
Enrich Geography + Worker/Scheme Context
         |
         v
Structured Action Recommendation
```

Execution mode:

- `CIVIC_AGENT_MOCK_MODE=True`: mock response branch
- `CIVIC_AGENT_MOCK_MODE=False`: full graph pipeline branch

## 6. Data Modeling

### 6.1 Civic Model

Primary entities in store:

- Constituency
- Ward
- Booth
- Citizen
- Worker
- Scheme
- Project
- Complaint

Derived analytics:

- Booth sentiment labels
- Top issue aggregation
- Segment distributions
- Scheme coverage and unenrolled eligibility
- Executive KPI composites

### 6.2 Global Ontology Model

Primary entities:

- Country nodes (risk, influence, pressure, domains)
- Signal nodes (category, layer, severity, geolocation)
- Structural assets (kind, status, importance, layer)
- Corridors (from/to, status, weight)

Derived synthesis:

- Enriched country posture
- Country research briefs and evidence points
- Global graph overlays for ontology dashboarding

### 6.3 Graph Model (Neo4j)

Documented relationships:

- `(Citizen)-[:LIVES_IN]->(Booth)`
- `(Citizen)-[:COMPLAINED_ABOUT]->(Issue)`
- `(Worker)-[:ASSIGNED_TO]->(Booth)`
- `(Booth)-[:PART_OF]->(Ward)->(Constituency)`

## 7. Frontend Architecture

### 7.1 Shell and Navigation

- `App.tsx` routes all paths to unified cockpit surface
- `CommandCenter.tsx` composes status bars, view nav, map area, and sidebar
- `ViewNav.tsx` maps operational mode to sidebar behavior

### 7.2 State and Fetching

- Zustand (`store/index.ts`) for interaction state:
        - map mode
        - active layers
        - selected entity
        - active view
        - sidebar tab/open state
        - AI handoff prompts
- React Query for interval-driven fetch cycles and cache behavior

### 7.3 Geospatial Rendering

- `MapView.tsx`: orchestrates globe/flat switch
- `GlobeEngine.tsx`:
        - 3D rendering of countries/signals/assets/corridors
        - auto-rotation and focus-on-selection behavior
- `FlatMapEngine.tsx`:
        - Leaflet markers/polylines/popups
        - focus-on-country behavior
        - in-map global brief cards

### 7.4 Intelligence Sidebar

- `IntelligenceSidebar.tsx` acts as right-side execution console
- Handles both:
        - tabbed data modes (global, booths, workers, schemes, alerts, AI)
        - view-specific overlays (executive, strategic, ontology, constituency, comms)

## 8. Layer Taxonomy

System layer keys:

- countries
- corridors
- economics
- governance
- climate
- defense
- conflict
- infrastructure
- mobility
- cyber
- news

These layers are used consistently across backend signal/category mapping and frontend rendering filters.

## 9. Resilience and Degradation Model

1. Runtime snapshots are persisted to disk to survive refresh failures.
2. Source-health objects track per-source status and item counts.
3. Tool sanitation blocks simulated/fallback payloads from appearing as live intelligence.
4. Strategic engine exposes unavailable tools in metadata.
5. Civic engine can stay in mock mode when API budgets or dependencies are constrained.

## 10. Deployment Topology (Current)

`docker-compose.yml` currently provisions:

- PostGIS/PostgreSQL (`db`)
- Neo4j (`neo4j`)
- Redis (`redis`)

Backend and frontend container specs are present but commented, enabling staged infrastructure-first local runs.

## 11. Current Architectural Constraints

- Core data path remains mostly in-memory + file persisted runtime state.
- Connector quality is source dependent and may vary by key availability.
- Duplicate legacy alias routes exist for some paths and should be consolidated in future cleanup.
- Graph and relational stores are integrated but not yet the sole source of truth for all runtime objects.

## 12. Evolution Direction

1. Unify duplicate data route definitions and harden API contract versioning.
2. Promote runtime state from JSON persistence to durable storage layer.
3. Expand deterministic tests for strategic planner/tool/reasoner path.
4. Add typed response schemas for all intelligence outputs.
5. Expand ingestion queueing and retry semantics for high-throughput workflows.
