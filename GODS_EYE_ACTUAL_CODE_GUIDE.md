# God's Eye OS: True Technical & Implementation Guide

This document supersedes older architectural plans and provides a **code-accurate, thoroughly realized** explanation of what the God's Eye OS project *actually* is and how it functions as of the latest repository state.

---

## 1. WHAT is God's Eye OS Currently?

**God's Eye OS** is an asynchronous, API-heavy OSINT (Open Source Intelligence) aggregator connected to an **autonomous multi-agent LLM orchestrator**. 

Contrary to theoretical architectural diagrams that might suggest heavy reliance on massive deployed clusters of PostgreSQL or Neo4j, the **actual implemented system** is designed for extreme portability, resilience, and "air-gapped" capabilities. It functions as a tactical intelligence dashboard that pulls live global events, parses them via AI, debates the outcomes internally, and visually renders them on a geographic interface.

### Key Active Features
1.  **Unified Intelligence API:** A centralized 'brain' router (`/unified/analyze`) that automatically triages user commands. It doesn't ask the user to pick tools—it parses the intent and dynamically runs reasoning engines, visual diagram generators, and map intelligence layers concurrently.
2.  **True Multi-Agent Debate System:** The system uses distinct `ExpertAgents` (specializing in economics, geopolitics, climate, etc.). When a query is made, these agents run in parallel. **If their confidence scores diverge by more than a set threshold (0.25), the system enforces a live AI debate** (`AgentDebateSystem.initiate_debate()`) to hash out discrepancies before presenting the final brief to the user.
3.  **Live OSINT Feed Engine:** The `RuntimeIntelligenceEngine` continuously pulls, filters, and standardizes data from massive real-world APIs directly into a JSON-based state.

---

## 2. WHY was it built this way?

The system was heavily optimized for **speed, AI token throughput, and stateless resilience** (likely for hackathon environments or rapid field-deployment scenarios):
*   **Air-Gapped / Portable Design:** By relying on an in-memory `app.data.store` and a local `runtime_state.json` instead of a heavy Relational DB, the system essentially guarantees it won't crash due to a database connection timeout. 
*   **Speed over Bloat:** Using `asyncio.gather()` aggressively throughout the FastAPI backend ensures that fetching 10 different global APIs and running 3 LLM agents happens in absolute parallel.

---

## 3. HOW does it actually work? (The Real Tech Stack)

### A. The LLM Core (Language Models)
The AI layer is NOT just a simple text generator. It uses a robust factory pattern (`llm_provider.py`) wrapped in **LangChain**:
*   **Primary Engine:** **Llama-3.3-70b-versatile** (via Groq API) for blazingly fast inference and strict JSON/function-calling outputs.
*   **Fallback Engine:** **Gemini-1.5-Pro** (via Google GenAI) is physically hardcoded as the automatic `get_enterprise_llm` fallback. If Groq rate-limits, Gemini automatically catches the query. 
*   **Agent Workflows:** Agents output strict `AgentClaim` models with quantifiable confidence scores, causation chains, and source citations, preventing loose hallucinations.

### B. The Live Data / Intelligence Inputs
The backend is strapped to a phenomenal array of active data feeds out-of-the-box:
*   **Geopolitics & News:** GDELT, Reddit, Mastodon, DuckDuckGo.
*   **Earth/Climate/Space:** USGS (Earthquakes), NASA EONET (Wildfires), OpenSky (Live aviation), Open-Meteo.
*   **Economics:** FRED (Fed Reserve), World Bank, EIA (Oil pricing).
*   **Cybersecurity:** CISA KEV (Known Exploited Vulnerabilities).

### C. The Backend Framework
*   **Python / FastAPI:** Utilizes strict Pydantic v2 validation.
*   **Concurrency:** Heavy reliance on Python's `asyncio` and `aiohttp` for non-blocking I/O.
*   **State Persistence:** Local JSON stores (`runtime_state.json`) and seeded mock graphs.

### D. The Frontend UI
*   **React 19 & TypeScript:** Scalable, strictly-typed front end.
*   **Feature Modules:** Organized by domain (`booths/`, `global/`, `intelligence/`, `schemes/`, `workers/`).
*   **Visual Stack:** Expected heavy use of visualizers (globe maps, network graphs).

---

## 4. WHERE does the Intelligence Live?

Instead of relying solely on an external graph database requiring complex configuration, the system maintains a "State of the World" locally. 
*   The `RuntimeIntelligenceEngine` wakes up on backend launch.
*   It grabs external signals (e.g., "Earthquake in Japan", "Brent crude drops 2%").
*   It logs these directly into a `Unified Intelligence` state. 
*   When the frontend queries for the state of the world, it interacts with these pre-digested Python dictionaries and schemas rather than making heavy SQL queries.

---

## 5. WHO drives the analysis?

When a user submits a complex prompt (e.g., "How will current Middle East tensions affect Indian energy markets?"):
1.  **The Orchestrator (`AgentOrchestrator`)** reads the query.
2.  **Parallel Domain Experts** (e.g., `EconomicAgent`, `GeopoliticalAgent`) are spawned.
3.  **Data Fetchers** extract real-time EIA oil prices and latest newswires.
4.  **The Agents output Claims**. If the Economic Agent says "Severe Impact" and the Geopolitical Agent says "Low Impact", the **Debate System** forces them to interact.
5.  **The Consensus Builder** aggregates the surviving claims, formulates an executive summary, highlights minority opinions/risks, and serves this back to the user interface.

## Summary
The codebase reveals that God's Eye OS is less of a traditional CRUD dashboard and more of a **reactive, multi-agent command center**. It leverages high-speed open-source weights (Llama 3.3 via Groq) for rapid reasoning, relies on lightweight JSON datastores for peak resilience, and continuously taps into a dozen live global OSINT APIs to form its world model.