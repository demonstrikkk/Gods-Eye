# JanGraph OS Architecture

## 1. System Shape

JanGraph OS is a layered intelligence application:

- `Frontend`: React 19 + Vite + Zustand + React Query
- `Backend`: FastAPI
- `Runtime intelligence`: background refresh loop + feed loop
- `Data model`: seeded civic dataset + seeded global ontology + persisted runtime state
- `Experience`: globe, flat map, right-side intelligence panel, AI console, tickers, ontology graph

## 2. High-Level Flow

```text
Public/Free APIs + RSS
        |
        v
OSINT Aggregator + Feed Aggregator
        |
        v
Runtime Intelligence Engine
        |
        +--> runtime_state.json
        |
        v
FastAPI /api/v1 endpoints
        |
        v
React Query service layer
        |
        v
Map + Sidebar + AI Console + Tickers
```

## 3. Backend Layers

### 3.1 API

- Router root: [backend/app/api/router.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/api/router.py)
- Data endpoints: [backend/app/api/endpoints/data.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/api/endpoints/data.py)
- Intelligence endpoints: [backend/app/api/endpoints/intelligence.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/api/endpoints/intelligence.py)

Main global endpoints:

- `/api/v1/data/global/overview`
- `/api/v1/data/global/countries`
- `/api/v1/data/global/country/{country_id}`
- `/api/v1/data/global/country-analysis/{country_id}`
- `/api/v1/data/global/signals`
- `/api/v1/data/global/assets`
- `/api/v1/data/global/corridors`
- `/api/v1/data/source-health`
- `/api/v1/data/markets`
- `/api/v1/data/feeds`
- `/api/v1/data/alerts`

### 3.2 Runtime Services

- App bootstrap: [backend/app/main.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/main.py)
- Runtime engine: [backend/app/services/runtime_intelligence.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/services/runtime_intelligence.py)
- Feed engine: [backend/app/services/feed_aggregator.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/services/feed_aggregator.py)
- Connector layer: [backend/app/services/osint_aggregator.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/services/osint_aggregator.py)

Runtime responsibilities:

- Refresh free/public data connectors on an interval
- Normalize raw source payloads into ontology signals
- Persist merged runtime state to disk
- Expose source-health and market snapshots
- Synthesize country-level analysis for UI and AI workflows

### 3.3 Data Model

- Civic seed: [backend/app/data/seed.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/data/seed.py)
- Global seed: [backend/app/data/global_seed.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/data/global_seed.py)
- Global assets: [backend/app/data/global_assets.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/data/global_assets.py)
- In-memory store: [backend/app/data/store.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/data/store.py)
- Runtime persistence: [backend/app/data/runtime_state.json](/c:/Users/asus/Downloads/Gods-Eye/backend/app/data/runtime_state.json)
- data.gov.in cache: [backend/app/data/data_gov_catalog_cache.json](/c:/Users/asus/Downloads/Gods-Eye/backend/app/data/data_gov_catalog_cache.json)

The global model has four main object types:

- `countries`
- `signals`
- `assets`
- `corridors`

## 4. Frontend Layers

### 4.1 Shell

- App entry: [frontend/src/App.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/App.tsx)
- Main page: [frontend/src/pages/CommandCenter.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/pages/CommandCenter.tsx)

### 4.2 State and Data Access

- Zustand store: [frontend/src/store/index.ts](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/store/index.ts)
- API client: [frontend/src/services/api.ts](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/services/api.ts)
- Shared types: [frontend/src/types/index.ts](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/types/index.ts)

### 4.3 Map Experience

- Map orchestrator: [frontend/src/features/map/MapView.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/features/map/MapView.tsx)
- 3D globe: [frontend/src/features/map/GlobeEngine.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/features/map/GlobeEngine.tsx)
- 2D map: [frontend/src/features/map/FlatMapEngine.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/features/map/FlatMapEngine.tsx)
- Layer toggles: [frontend/src/components/LayerControl.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/components/LayerControl.tsx)

Map renders:

- Country nodes
- Live signals
- Structural assets
- Corridors
- Feed labels

### 4.4 Sidebar Experience

- Sidebar shell: [frontend/src/features/intelligence/IntelligenceSidebar.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/features/intelligence/IntelligenceSidebar.tsx)
- Global drill-down: [frontend/src/features/global/GlobalTab.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/features/global/GlobalTab.tsx)
- Overview panel: [frontend/src/features/panels/GlobalOverviewPanel.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/features/panels/GlobalOverviewPanel.tsx)
- AI console: [frontend/src/features/intelligence/AIConsoleTab.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/features/intelligence/AIConsoleTab.tsx)

Clicked-country flow:

- Map click sets selected country in Zustand
- Global tab requests `/global/country-analysis/{country_id}`
- Sidebar renders summary, risks, assets, signals, feeds, weather, and AI prompts

## 5. Persistence Model

There are two persistence styles:

- `Seeded`: deterministic base ontology and civic demo data
- `Runtime`: refreshed live overlays saved into JSON

This split keeps the product demo-safe while still allowing live enrichment.

## 6. Layer Taxonomy

The global map currently uses these layer families:

- `countries`
- `corridors`
- `economics`
- `governance`
- `climate`
- `defense`
- `conflict`
- `infrastructure`
- `mobility`
- `cyber`
- `news`

## 7. Source Strategy

The system intentionally favors free/public sources first. It mixes:

- Live APIs for structured data
- RSS and Google News RSS for breadth
- Curated static ontology assets for globally important infrastructure

This is why not every layer is "telemetry-grade" yet. Some are event streams; some are strategic map primitives.

## 8. Operational Constraints

- The backend is currently demo-friendly and mostly file/in-memory based.
- Runtime quality depends on source availability and any configured keys.
- Some connectors remain best-effort because free public sources are unstable or partial.
- The architecture is ready for a future graph database and stronger entity-resolution layer, but that is not yet the core runtime path.
