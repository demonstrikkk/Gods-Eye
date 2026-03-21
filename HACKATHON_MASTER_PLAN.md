# 🇮🇳 India Innovates 2026 — JanGraph OS Master Execution Plan
# World's Largest Civic Tech Hackathon | Bharat Mandapam, New Delhi | 28 March 2026

---

## Problem Statement (Selected Domain)

> Design and develop an AI-powered Global Ontology Engine that collects structured data,
> unstructured content, and live real-time feeds from geopolitics, economics, defense,
> technology, climate, and society—connecting into a single, unified, constantly updating
> intelligence graph for decision-makers.

### Sub-Objectives from PS:
1. **Intelligent Segmentation** — Auto-classify booth data into Youth, Businessmen, Farmers, Women → "Key Voters"
2. **Hyper-Local Content Delivery** — Precision engine for tailored info per segment
3. **Micro-Accountability Mapping** — Street-level Before/After notifications to affected residents only
4. **Beneficiary Linkage** — Track Ayushman Bharat, PM-Kisan beneficiaries within booths
5. **Party Worker Management** — Worker profiles, GPS tracking, task assignment, performance
6. **AI Sentiment Analysis Engine** — Multi-language NLP, booth-wise + constituency-wise heatmaps/alerts

---

## CURRENT STATUS AUDIT

### ✅ Working
- [x] FastAPI backend starts on port 8000
- [x] React + Vite frontend on port 5173
- [x] Leaflet map renders with dark CARTO tiles
- [x] 7 dashboard pages render (Executive, Map, Constituency, Workers, Accountability, Comms, Alerts)
- [x] Tailwind CSS design system with custom theme tokens
- [x] LangChain + LangGraph architecture scaffolded
- [x] Groq/Gemini LLM failover provider exists
- [x] Neo4j + PostGIS schema design documented
- [x] CORS and routing fully functional

### ❌ Broken / Missing
- [ ] ALL data is hardcoded mock arrays (no backend data flowing)
- [ ] No data seeder / realistic demo data
- [ ] No actual sentiment analysis (just labels)
- [ ] No voter segmentation logic
- [ ] No beneficiary tracking
- [ ] No RSS/news feed aggregation
- [ ] No Before/After image slider component
- [ ] No 3D globe visualization
- [ ] No live feed ticker
- [ ] No force-directed graph visualization (ontology is invisible)
- [ ] No multi-language support
- [ ] No worker GPS tracking
- [ ] Backend API endpoints crash without databases

---

## EXECUTION PLAN — 7 Days to Win

### ═══════════════════════════════════════
### PHASE 1: BACKEND DATA ENGINE (Priority: CRITICAL)
### ═══════════════════════════════════════

#### Task 1.1: In-Memory Data Store (No External DB Required)
**Why:** Judges won't have Neo4j/Postgres. Demo must work on ANY laptop with zero setup.

**File:** `backend/app/data/seed.py`

**Data to generate:**
```
- 5 Constituencies (real Indian names: Chandni Chowk, Varanasi, etc.)
  └── 25 Wards (5 per constituency)
      └── 125 Booths (5 per ward)
          └── 50,000 Citizens (400 per booth)
              ├── Demographics: age, gender, occupation, income_band
              ├── Segment: Youth (18-35), Farmer, Business, Women, Senior
              ├── Schemes: [Ayushman, PM-Kisan, Mudra, Ujjwala, PMAY]
              ├── Sentiment: positive/negative/neutral (per issue)
              └── Issues: [Water, Roads, Health, Jobs, Education, Electricity]
          └── 4 Workers per booth (500 total)
              ├── name, phone, GPS_lat, GPS_lng
              ├── tasks_assigned, tasks_completed
              └── performance_score
          └── 2 Infrastructure Projects per ward (50 total)
              ├── name, type, budget, status
              ├── before_image_url, after_image_url
              └── affected_street, affected_citizens[]
```

**Implementation:** Store as Python dicts/dataclasses in memory. Load once on startup. No database dependency.

#### Task 1.2: API Endpoints That Serve Real Data
**Files:** `backend/app/api/endpoints/`

| Endpoint | Serves | Priority |
|----------|--------|----------|
| `GET /api/v1/data/constituencies` | Full constituency list with aggregated stats | P0 |
| `GET /api/v1/data/constituency/{id}/booths` | Booth-level data with segments | P0 |
| `GET /api/v1/data/booth/{id}/citizens` | Citizen roster with demographics | P0 |
| `GET /api/v1/data/booth/{id}/segments` | Voter segmentation breakdown | P0 |
| `GET /api/v1/data/booth/{id}/schemes` | Beneficiary linkage data | P0 |
| `GET /api/v1/data/booth/{id}/sentiment` | Sentiment scores per issue | P0 |
| `GET /api/v1/data/workers` | Worker roster with GPS + tasks | P1 |
| `GET /api/v1/data/projects` | Infrastructure projects with Before/After | P1 |
| `GET /api/v1/data/feeds` | Aggregated RSS intelligence feeds | P1 |
| `POST /api/v1/intelligence/segment` | Run segmentation on booth data | P1 |
| `POST /api/v1/intelligence/sentiment` | Analyze text sentiment (Groq LLM) | P1 |
| `GET /api/v1/data/graph/ontology` | Return graph nodes/edges for visualization | P2 |

#### Task 1.3: RSS Feed Aggregation Engine
**Why:** The PS literally says "live real-time feeds from geopolitics, economics, defense"

**File:** `backend/app/services/feed_aggregator.py`

**Feeds to aggregate (Indian + Global):**
```python
FEEDS = [
    # Indian News
    {"name": "NDTV", "url": "https://feeds.ndtv.com/all-news"},
    {"name": "The Hindu", "url": "https://www.thehindu.com/feeder/default.rss"},
    {"name": "Times of India", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"},
    {"name": "India Today", "url": "https://www.indiatoday.in/rss/home"},
    # Global Intelligence
    {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldNews"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    # Economics
    {"name": "Economic Times", "url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms"},
    # Defense
    {"name": "Defense News", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/"},
]
```

**Implementation:**
- Use `feedparser` library to pull RSS
- Run on startup + every 5 minutes via background task
- Classify each article using Groq LLM: category (Geopolitics/Economics/Defense/Climate/Society)
- Store in memory as intelligence briefs
- Serve via `/api/v1/data/feeds` endpoint

#### Task 1.4: Sentiment Analysis Pipeline (REAL, not mock)
**File:** `backend/app/services/sentiment_engine.py`

**Implementation:**
```
Input: Raw text (citizen complaint, news headline, social media post)
   │
   ├── Step 1: Language Detection (regex for Hindi/English/Tamil/etc.)
   ├── Step 2: Translation to English (if needed, via Groq)
   ├── Step 3: Sentiment Classification (Groq Llama 3.1):
   │     └── Returns: { sentiment: "positive"|"negative"|"neutral", score: 0-100, issues: ["water", "roads"] }
   └── Step 4: Store result + link to citizen/booth in data store
```

**Fallback:** If LLM unavailable, use keyword-based scoring:
```python
NEGATIVE_KEYWORDS = ["broken", "corrupt", "delay", "problem", "angry", "failure"]
POSITIVE_KEYWORDS = ["thank", "good", "improved", "fixed", "happy", "excellent"]
```

### ═══════════════════════════════════════
### PHASE 2: FRONTEND — WIRE TO REAL DATA
### ═══════════════════════════════════════

#### Task 2.1: Replace ALL Mock Arrays with API Calls
**Every page must fetch from backend.** No more hardcoded data.

| Page | Current State | Target State |
|------|--------------|--------------|
| ExecutiveDashboard.tsx | Fetches `/executive` (works with fallback) | Wire to real aggregated stats |
| MapDashboard.tsx | Hardcoded 3 nodes | Fetch 125 booths with GPS + sentiment colors |
| ConstituencyLens.tsx | 5 mock booths | Fetch real booth roster + segmentation |
| WorkerDashboard.tsx | Mock worker array | Fetch real worker data + tasks |
| AccountabilityDashboard.tsx | Static project array | Fetch real projects with Before/After URLs |
| CommunicationsEngine.tsx | Mock campaigns | Fetch real outreach history |
| RiskAlerts.tsx | Static alerts | Fetch real-time sentiment-triggered alerts |

#### Task 2.2: Voter Segmentation Visualization (NEW)
**File:** `frontend/src/pages/SegmentationDashboard.tsx`

**Features:**
- Pie chart: Youth vs Business vs Farmer vs Women per booth
- Bar chart: Scheme enrollment per segment
- Interactive filter: Click segment → see key voters list
- "Key Voter" badge: Citizens with high influence score
- Export segmentation report

#### Task 2.3: Beneficiary Linkage Dashboard (NEW)
**File:** `frontend/src/pages/BeneficiaryTracker.tsx`

**Features:**
- Table: Scheme name → Enrolled count → Booth coverage %
- Map overlay: Color-coded beneficiary density per booth
- Drill-down: Click booth → see individual beneficiary list
- Gap analysis: "These 2,400 eligible citizens in Booth 103 are NOT enrolled in PM-Kisan"
- Action button: "Trigger enrollment awareness campaign" → links to Comms Engine

#### Task 2.4: Before/After Image Slider Component (NEW)
**File:** `frontend/src/components/BeforeAfterSlider.tsx`

**Features:**
- Drag-to-reveal comparison slider (CSS clip-path technique)
- Before image (pre-construction) overlaid with After image (post-construction)
- Timestamp overlay + project metadata
- "Notify Affected Residents" button → Micro-Accountability trigger

#### Task 2.5: Live Feed Ticker (NEW)
**File:** `frontend/src/components/LiveFeedTicker.tsx`

**Features:**
- Horizontal scrolling bar at top of dashboard
- Shows latest RSS intelligence briefs
- Color-coded by category: 🔴 Defense | 🟡 Economics | 🔵 Technology | 🟢 Climate
- Click to expand brief → shows AI-generated summary
- "435+ feeds aggregated" counter (matching WorldMonitor aesthetic)

### ═══════════════════════════════════════
### PHASE 3: WOW FACTOR — JUDGE IMPACT
### ═══════════════════════════════════════

#### Task 3.1: 3D Globe Visualization (KILLER FEATURE)
**File:** `frontend/src/components/Globe3D.tsx`
**Library:** `react-globe.gl`

**Features:**
- Interactive 3D Earth with India highlighted
- Pulsing dots on each constituency showing sentiment (red=negative, green=positive)
- Arc lines connecting constituencies showing data flow
- Click dot → zoom into constituency → transition to 2D Leaflet map
- "Wow" entrance animation on page load

#### Task 3.2: Ontology Graph Visualization (DIFFERENTIATOR)
**File:** `frontend/src/components/OntologyGraph.tsx`
**Library:** `react-force-graph-2d` or `d3-force`

**Features:**
- Force-directed graph showing the KNOWLEDGE GRAPH:
  - Citizen nodes (small dots)
  - Booth nodes (medium circles)
  - Issue nodes (colored hexagons)
  - Scheme nodes (stars)
  - Worker nodes (triangles)
- Edges showing relationships: LIVES_IN, COMPLAINED_ABOUT, BENEFICIARY_OF
- Real-time animation: New data flows through as glowing edges
- This IS the "Ontology Engine" — judges must SEE it working

#### Task 3.3: Sentiment Heatmap Overlay
**File:** `frontend/src/components/SentimentHeatmap.tsx`
**Library:** `leaflet.heat`

**Features:**
- Heat overlay on Map Dashboard showing sentiment intensity
- Red zones = negative sentiment clusters
- Green zones = positive sentiment
- Toggle: Issue-specific heatmaps (Water issues vs Road issues)
- Animated transitions when switching issue filters

#### Task 3.4: Multi-Language UI Toggle
**File:** `frontend/src/i18n/` directory

**Languages:** English, Hindi (हिन्दी), Tamil (தமிழ்)
**Implementation:** Simple JSON translation files + React context provider
**Why:** PS explicitly mentions "multi-language data analysis"

### ═══════════════════════════════════════
### PHASE 4: DEMO NARRATIVE FOR JUDGES
### ═══════════════════════════════════════

#### Task 4.1: Judge Walkthrough Flow
The demo should follow this exact narrative:

```
STEP 1: "The Brain" (30 seconds)
→ Show 3D Globe spinning to India
→ "This is JanGraph OS — India's Civic Intelligence Operating System"
→ Pulsing sentiment nodes across India

STEP 2: "The Data Pipeline" (45 seconds)
→ Show Live Feed Ticker aggregating 100+ news sources
→ Show Ontology Graph building in real-time
→ "We ingest geopolitical, economic, and civic data into a unified knowledge graph"

STEP 3: "The Intelligence" (60 seconds)
→ Drill into Chandni Chowk constituency
→ Show booth-level sentiment heatmap
→ "Booth 103 has critical negative sentiment on Water Supply"
→ Show voter segmentation: "68% are Farmers, 22% are Youth"

STEP 4: "The Action Loop" (60 seconds)
→ Type natural language query: "Show booths where water sentiment is negative"
→ System returns graph-powered answer
→ Click "Deploy Outreach" → Automated WhatsApp broadcast
→ Show Before/After slider for completed road project
→ "Only residents of Gali 4, Sector 8 received this notification"

STEP 5: "The Edge" (30 seconds)
→ Show beneficiary tracking: "2,400 eligible but unenrolled in PM-Kisan"
→ Worker GPS map: "340 field workers tracked in real-time"
→ "JanGraph OS transforms governance from reactive to predictive"
```

#### Task 4.2: README & Architecture Diagram
**File:** `README.md` (root)

Must include:
- Project name, tagline, screenshot
- Architecture diagram (Mermaid)
- Tech stack badges
- Quick start instructions
- Demo video link
- Team info

#### Task 4.3: Pitch Deck
**File:** `PITCH.md`

- Problem → Solution → Demo → Architecture → Impact → Team
- 6 slides max
- Numbers-driven: "125 booths, 50,000 citizens, 100+ data sources"

### ═══════════════════════════════════════
### PHASE 5: POLISH & HARDENING
### ═══════════════════════════════════════

#### Task 5.1: Error Handling
- ALL API endpoints must return graceful JSON errors
- Frontend must show "Connecting..." states, never crash
- Offline mode: App works with seeded data even without internet

#### Task 5.2: Performance
- React.memo on heavy components
- Virtualized lists for 50K citizen tables
- Debounced search inputs
- Lazy-loaded routes (React.lazy)

#### Task 5.3: Code Quality
- Fix ALL TypeScript lint errors
- Remove unused imports
- Consistent naming conventions
- No console.log statements in production

---

## NPM PACKAGES TO INSTALL

### Frontend
```bash
npm install react-globe.gl           # 3D Globe
npm install react-force-graph-2d     # Ontology graph visualization
npm install leaflet.heat             # Sentiment heatmap
npm install react-compare-image      # Before/After slider
npm install framer-motion            # Smooth animations
npm install @tanstack/react-table    # Data tables for citizen/worker lists
npm install date-fns                 # Date formatting
```

### Backend
```bash
pip install feedparser               # RSS feed parsing
pip install textblob                 # Fallback sentiment analysis
pip install aiohttp                  # Async HTTP for feed fetching
```

---

## FILE CREATION CHECKLIST

### Backend New Files
- [ ] `backend/app/data/__init__.py`
- [ ] `backend/app/data/seed.py` — Master data generator
- [ ] `backend/app/data/store.py` — In-memory data store singleton
- [ ] `backend/app/api/endpoints/data.py` — All data-serving endpoints
- [ ] `backend/app/services/feed_aggregator.py` — RSS engine
- [ ] `backend/app/services/sentiment_engine.py` — NLP pipeline
- [ ] `backend/app/services/segmentation.py` — Voter classification

### Frontend New Files
- [ ] `frontend/src/components/Globe3D.tsx`
- [ ] `frontend/src/components/OntologyGraph.tsx`
- [ ] `frontend/src/components/SentimentHeatmap.tsx`
- [ ] `frontend/src/components/BeforeAfterSlider.tsx`
- [ ] `frontend/src/components/LiveFeedTicker.tsx`
- [ ] `frontend/src/components/DataTable.tsx`
- [ ] `frontend/src/pages/SegmentationDashboard.tsx`
- [ ] `frontend/src/pages/BeneficiaryTracker.tsx`
- [ ] `frontend/src/i18n/en.json`
- [ ] `frontend/src/i18n/hi.json`

### Root Files
- [ ] `README.md` — Project overview with screenshots
- [ ] `PITCH.md` — Judge-facing pitch document

---

## TIMELINE (7 Days: March 21-28)

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Day 1 (Mar 21) | Phase 1.1 + 1.2 | Data seeder + API endpoints serving real data |
| Day 2 (Mar 22) | Phase 1.3 + 1.4 | RSS aggregation + Sentiment analysis pipeline |
| Day 3 (Mar 23) | Phase 2.1 + 2.2 | All pages wired to real data + Segmentation UI |
| Day 4 (Mar 24) | Phase 2.3 + 2.4 + 2.5 | Beneficiary tracker + Before/After + Feed ticker |
| Day 5 (Mar 25) | Phase 3.1 + 3.2 | 3D Globe + Ontology Graph visualization |
| Day 6 (Mar 26) | Phase 3.3 + 3.4 + Phase 4 | Heatmap + Multi-language + Demo narrative |
| Day 7 (Mar 27) | Phase 5 | Polish, README, pitch deck, dry run |
| **Day 8 (Mar 28)** | **HACKATHON DAY** | **PRESENT & WIN** |

---

## SUCCESS CRITERIA

For judges to declare us winners, they must see:
1. ✅ **Real data flowing** — Not static. Click any booth, see different real numbers.
2. ✅ **AI actually working** — Type a query, get LLM-powered answer from graph.
3. ✅ **Visual wow** — 3D globe, animated heatmaps, force-directed graph.
4. ✅ **PS alignment** — Every sub-objective visibly addressed (segmentation, Before/After, beneficiaries).
5. ✅ **Production quality** — No crashes, graceful errors, fast performance.
6. ✅ **Narrative** — Clear 3-minute demo story that builds to a climax.

---

*Generated: 20 March 2026 | JanGraph OS v2.0 Sprint Plan*
