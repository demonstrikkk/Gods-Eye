# JanGraph OS

JanGraph OS is a full-stack global ontology and civic-intelligence cockpit. It combines a FastAPI backend, a React/Vite frontend, seeded ontology assets, and free/public data connectors to render a world-scale command center with live signals, map layers, country analysis, market context, and an AI console.

## What It Does

- Renders a 3D globe and 2D map with toggleable global layers.
- Tracks countries, corridors, live signals, and structural assets.
- Aggregates free/public feeds across geopolitics, climate, cyber, governance, economics, and mobility.
- Persists runtime intelligence so refreshed signals survive restarts.
- Lets the operator click a country and get a synthesized country brief with weather, feeds, signals, assets, and AI follow-up prompts.

## Current Layer Families

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

## Data Sources

The app is designed around free or public-development sources first.

- REST Countries
- World Bank Indicators API
- Open-Meteo
- NASA EONET
- USGS Earthquake feeds
- OpenSky
- GDELT
- FRED
- EIA
- data.gov.in
- CISA KEV catalog
- Public RSS and Google News RSS queries
- Finnhub if a free token is present

## Repo Structure

```text
backend/
  app/
    api/
    core/
    data/
    services/
frontend/
  src/
    components/
    features/
    pages/
```

## Local Run

### Backend

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
```

Backend runs on `http://localhost:8000`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

## Environment

The app reads the root `.env`. Some connectors are optional.

- Required for base demo: none beyond local defaults.
- Recommended for richer live data: `NEWS_API_KEY`, `FRED_API_KEY`, `FINNHUB_API_KEY`, `EIA_API_KEY`, `VITE_DATA_GOV_IN_KEY` or `DATA_GOV_IN_KEY`.
- Optional query-driven `data.gov.in` discovery: `DATA_GOV_IN_QUERY_TERMS`.

## Main Runtime Files

- Backend entry: [backend/app/main.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/main.py)
- Runtime orchestration: [backend/app/services/runtime_intelligence.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/services/runtime_intelligence.py)
- OSINT connectors: [backend/app/services/osint_aggregator.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/services/osint_aggregator.py)
- Feed aggregation: [backend/app/services/feed_aggregator.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/services/feed_aggregator.py)
- Global seed and assets: [backend/app/data/global_seed.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/data/global_seed.py), [backend/app/data/global_assets.py](/c:/Users/asus/Downloads/Gods-Eye/backend/app/data/global_assets.py)
- Frontend shell: [frontend/src/pages/CommandCenter.tsx](/c:/Users/asus/Downloads/Gods-Eye/frontend/src/pages/CommandCenter.tsx)

## Verification

These checks currently pass:

- `python -m compileall backend\app`
- `npx tsc -b` in `frontend`

## Notes

- Country coverage is global, but analytics depth still depends on which free sources emit usable live data.
- Some layer types are live telemetry; others are curated structural ontology assets.
- Existing planning docs remain in the repo: [ARCHITECTURE_PLAN.md](/c:/Users/asus/Downloads/Gods-Eye/ARCHITECTURE_PLAN.md) and [HACKATHON_MASTER_PLAN.md](/c:/Users/asus/Downloads/Gods-Eye/HACKATHON_MASTER_PLAN.md).
