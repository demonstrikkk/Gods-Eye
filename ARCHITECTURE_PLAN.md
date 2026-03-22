# JanGraph OS - Architecture & Implementation Plan

## 1. System Architecture

**Philosophy & Goals**: 
- **Determinism & Trust**: Enterprise-grade application with strict validation (Pydantic), robust error handling, and transactional integrity. 
- **Sovereign Capability**: A completely air-gappable architecture using Docker Compose, bringing all state (DB, Graph, Cache, AI Inference) onto local or self-hosted infrastructure. 
- **Scalability**: Decoupling the API (FastAPI) from heavy background work (knowledge graph updates, sentiment inference) through a Redis-backed queue.

**Stack Details**:
- **Frontend**: React 18, Vite, TypeScript, TailwindCSS (highly customized for non-generic, professional UI), Mapbox/Leaflet, Recharts.
- **Backend API**: FastAPI (Python 3.10+), strictly typed with async endpoints.
- **Message Broker & Cache**: Redis.
- **Relational / Spatial DB**: PostgreSQL with PostGIS extension.
- **Graph Database**: Neo4j (for mapping Citizen -> Issue -> Booth -> Scheme).
- **AI Inference Layer**: Local LLM support through Ollama/vLLM integration (plus failovers for external APIs in Public Cloud Demo Mode). Background Workers (Celery/RQ) handle ingestion, AI processing, and notifications.

## 2. Folder Structure

We will use a Monorepo strategy handling both frontend and backend seamlessly for simpler automated deployments.

```
/Gods-Eye
├── docker-compose.yml      # Full sovereign orchestration
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/            # Route definitions
│   │   ├── core/           # Config, Security, DB Connections
│   │   ├── models/         # SQLAlchemy (RDBMS) & OGM (Neo4j) Models
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Core business logic (AI, Ingestion, Sentiment)
│   │   ├── tasks/          # Background worker definitions
│   │   └── main.py         # FastAPI application entrypoint
│   ├── requirements.txt    # Python deps
│   └── Dockerfile          # Backend container map
└── frontend/
    ├── public/
    ├── src/
    │   ├── assets/         # Images, fonts, icons
    │   ├── components/     # Custom, high-end UI components
    │   ├── layouts/        # Dashboard layout, navigation
    │   ├── pages/          # Views: Map, Constituency, Booth, Analytics, Alerts
    │   ├── store/          # Zustand / React Query state management
    │   ├── utils/          # Helpers, API clients
    │   ├── App.tsx         # Root Router
    │   └── main.tsx        # React mounting
    ├── package.json        
    ├── tailwind.config.js  # Refined color palette (Dark Mode, Glassmorphism)
    ├── vite.config.ts      
    └── Dockerfile          # Frontend container map
```

## 3. Data Models

Due to the dual nature of our queries (relational vs. graph), we maintain two core data stores.

### A. RDBMS (PostgreSQL + PostGIS)
Holds transactional, structured data where spatial queries or strict ACID is necessary.
- `User`: RBAC (Admin, National Strategist, Worker, Analyst).
- `Constituency`, `Ward`, `Booth` (Includes PostGIS `geometry` column).
- `NotificationLog`: History of sent communications.
- `WorkerTask`: Assignment, status, GPS check-in data.
- `Project`: Roadwork, infrastructure, budget, before/after image references.

### B. Graph (Neo4j)
Holds relationships to compute multidimensional influence and issues.
- `(Citizen)`
- `(Scheme)`
- `(Issue)`
- `(Sentiment)`
- **Relationships**: 
  - `(Citizen)-[:LIVES_IN]->(Booth)`
  - `(Citizen)-[:COMPLAINED_ABOUT]->(Issue)`
  - `(Booth)-[:HAS_DOMINANT_ISSUE]->(Issue)`
  - `(Worker)-[:ASSIGNED_TO]->(Booth)`
  - `(Issue)-[:AFFECTS]->(Sentiment)`

## 4. APIs

RESTful endpoints exposed by FastAPI.
- `POST /api/v1/ingest/csv`: Secure upload mapping algorithm. Kicks off background task.
- `GET /api/v1/intelligence/map`: Returns spatial features + aggregated sentiment + issues.
- `GET /api/v1/intelligence/booth/{booth_id}`: Returns RDBMS demographics + Graph intelligence relationships.
- `POST /api/v1/intelligence/query`: Natural language to Cypher/SQL bridge for the unified search.
- `GET /api/v1/workers/tasks`: Role-based task retrieval.
- `POST /api/v1/actions/outreach`: Triggers the async Outreach Engine over SMS/WhatsApp.

## 5. UI System

- **Token/Theme System**: Avoid raw Tailwind utilities in places where strict consistency is needed. Define custom color palettes extending `slate`, `zinc`, accented by robust semantic colors (Success, Warning, Danger, Info).
- **Layouts**: High-density Data grids. Deep dark-mode aesthetic targeting a "mission control" or "defense" feel, utilizing minimal glassmorphism (translucency + subtle borders).
- **Navigation**: Persistent left-side collapsed nav to maximize map/data viewing area.
- **Maps**: Mapbox/Leaflet full bleed canvas underpinning data overlay components.

## 6. Implementation Strategy

1. **Phase 1: Foundation (Boilerplate & Core Services)**
   - Setup Docker Compose with Postgres, PostGIS, Neo4j, Redis.
   - Initialize FastAPI and setup DB connections.
   - Initialize React Vite with Tailwind and high-end routing.
2. **Phase 2: Schemas & Data Seeding**
   - Create SQLAlchemy and Neo4j data generation scripts (No mock placeholders in the app, but we need deterministic seed data to simulate "Government Data").
3. **Phase 3: The Intelligence Engine**
   - Implement the ingest worker.
   - Implement the natural language -> graph query endpoints.
4. **Phase 4: Mission Control UI**
   - Map View (Pillar 3).
   - Executive & Booth Intelligence Dashboards (Pillars 1, 4, 7).
5. **Phase 5: Outreach & Polish**
   - Worker Ops and Communication Center (Pillars 5, 6).
   - Sovereign mode documentation / final hardening.

---

*End of Architecture Document. I will now proceed to initialize the folder structure, docker configuration, and foundation as per Rule 1 & 2.*
