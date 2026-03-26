# Gods-Eye OS

Gods-Eye OS is an intelligence command platform that combines:

- A global ontology cockpit (countries, corridors, signals, strategic assets)
- A civic operations intelligence layer (booths, citizens, workers, schemes, complaints)
- A multi-source runtime intelligence pipeline (RSS + open APIs + social signals)
- A strategic agentic analysis engine with tool planning, evidence synthesis, and scenario simulation
- A modern React control surface with 3D globe, 2D map, dashboards, and AI console

The system is built to run in degraded environments and can operate with partial connectivity, using seeded ontology data plus best-effort live enrichment.

## Core Capabilities

- World map intelligence with 11 layer families and live overlays
- Country-level evidence briefs combining signals, feeds, weather, World Bank, and open search results
- Strategic analysis endpoint that plans tools, executes them in parallel, and synthesizes grounded output
- What-if scenario simulation endpoint
- Civic ingestion endpoint for unstructured text routed through LangGraph-style processing
- Feed aggregation loop that ingests RSS and open-source intelligence signals
- Runtime persistence so refreshed intelligence survives process restarts

## Repository Layout

```text
jangram/
  backend/
    app/
      api/
      core/
      data/
      models/
      schemas/
      services/
      main.py
    requirements.txt
  frontend/
    src/
      components/
      features/
      pages/
      services/
      store/
      types/
    package.json
  docker-compose.yml
  ARCHITECTURE.md
  ARCHITECTURE_PLAN.md
```

## Technology Stack

### Backend

- FastAPI
- Pydantic v2
- SQLAlchemy async engine (PostgreSQL/PostGIS-ready)
- Neo4j integration for graph operations
- Redis-ready caching hooks
- LangChain + LangGraph + Groq/Gemini model providers
- aiohttp + feedparser for external feeds and open-source ingestion

### Frontend

- React 19 + TypeScript + Vite
- React Query for data orchestration
- Zustand for interaction state
- react-globe.gl (3D globe)
- Leaflet/react-leaflet (2D geospatial view)
- Framer Motion for interaction polish
- Tailwind CSS for styling

## End-to-End Workflows

### 1. Runtime Intelligence Refresh Loop

1. Backend startup starts `runtime_engine` and `feed_engine`.
2. Runtime engine collects data from GDELT, USGS, NASA, World Bank, EIA, data.gov.in, OpenSky, CISA, search sources, and market snapshots.
3. Signals are normalized into a common shape with category, layer, severity, source, geolocation, and country binding.
4. Runtime state is persisted into `backend/app/data/runtime_state.json`.
5. Frontend queries `/api/v1/data/global/*` endpoints on intervals and re-renders overlays.

### 2. Feed Ingestion and Enrichment

1. Feed aggregator fetches configured RSS and optional NewsAPI content concurrently.
2. Briefs are deduplicated and classified into categories + urgency.
3. Briefs are stored in the in-memory store as recent feed context.
4. Each brief is sent asynchronously into civic text processing (`process_unstructured_civic_text`) for additional extraction and sentiment processing.

### 3. Strategic Agentic Analysis

1. Client posts query to `/api/v1/intelligence/strategic-analysis`.
2. Planner prompt selects relevant tools from the strategic tool registry.
3. Tool plan is normalized and constrained for validity.
4. Tools execute in parallel with timeout handling.
5. Results are sanitized to reject simulated/fallback evidence as live signals.
6. Reasoning prompt synthesizes executive summary, risks, impacts, forecasts, scenarios, recommendations, timeline, and metadata.
7. If connectors are unavailable, engine returns explicit grounded fallback output rather than fabricated analysis.

### 4. Civic Unstructured Ingestion

1. Payload is submitted to `/api/v1/ingestion/unstructured`.
2. Background task runs civic pipeline and extracts issue + urgency.
3. Graph query writes complaint linkage into Neo4j.
4. Action recommendation payload is generated through structured schema.

Note: civic pipeline currently defaults to mock mode (`CIVIC_AGENT_MOCK_MODE=True`) unless changed in environment/config.

## Data Model

### Civic Domain (seeded and in-memory)

- Constituencies
- Wards
- Booths
- Citizens
- Workers
- Schemes
- Projects
- Complaints

Derived metrics include national sentiment, critical booths, unresolved complaints, and scheme coverage.

### Global Ontology Domain

- Countries
- Live/global signals
- Strategic assets
- Corridors
- Global graph nodes/links

Runtime overlays merge seeded ontology + live signals into enriched country objects.

## API Surface (Primary)

### Intelligence

- `POST /api/v1/intelligence/query`
- `POST /api/v1/intelligence/strategic-analysis`
- `POST /api/v1/intelligence/scenario-simulate`
- `POST /api/v1/intelligence/news-insight`
- `GET /api/v1/intelligence/dashboard/executive`

### Global and Civic Data

- `GET /api/v1/data/global/overview`
- `GET /api/v1/data/global/countries`
- `GET /api/v1/data/global/signals`
- `GET /api/v1/data/global/assets`
- `GET /api/v1/data/global/corridors`
- `GET /api/v1/data/global/country-analysis/{country_id}`
- `GET /api/v1/data/source-health`
- `GET /api/v1/data/markets`
- `GET /api/v1/data/feeds`
- `GET /api/v1/data/alerts`

### Ingestion and Outreach

- `POST /api/v1/ingestion/unstructured`
- `POST /api/v1/actions/campaigns/deploy`

## Configuration

Environment is loaded from repository root `.env` by backend settings.

Important variables:

- `GROQ_API_KEY`, `GEMINI_API_KEY`, `PRIMARY_LLM_MODEL`
- `NEWS_API_KEY`, `FRED_API_KEY`, `FINNHUB_API_KEY`, `EIA_API_KEY`
- `DATA_GOV_IN_KEY`, `DATA_GOV_IN_RESOURCE_IDS`, `DATA_GOV_IN_QUERY_TERMS`
- `TWITTER_API_IO_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
- `YOUTUBE_API_KEY`, `TELEGRAM_BOT_TOKEN`, `BEWGLE_API_KEY`
- `CIVIC_AGENT_MOCK_MODE` (currently `True` by default)
- `LOCAL_MODE_ENABLED`

## Local Development

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
```

Backend default URL: `http://localhost:8000`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://localhost:5173`

### Optional infra services via Docker

```powershell
docker compose up -d db neo4j redis
```

Note: `docker-compose.yml` currently provisions infra services; backend/frontend containers are present but commented out.

## UI Interaction Model

- `ViewNav` switches high-level operational mode (cockpit, executive, strategic, workers, schemes, comms, alerts, ontology).
- `MapView` toggles between globe and flat map.
- `LayerControl` toggles ontology and signal layers.
- Selecting a country opens research context in right sidebar.
- AI Console supports standard query, strategic mode, and news desk mode.

## Operational Notes

- The platform is intentionally resilient-first: partial source outages should degrade gracefully.
- Strategic output is designed to stay evidence-grounded and explicit about unavailable tools.
- Civic agent pipeline is implemented with configurable mock/real execution mode.

## Documentation Map

- Detailed runtime/system architecture: `ARCHITECTURE.md`
- Refactor and hardening plan: `ARCHITECTURE_PLAN.md`
