# God's Eye OS: Comprehensive Project Guide

This document serves as the ultimate detailed explanation of the **God's Eye OS** project. It breaks down the project by answering the fundamental questions: **What**, **Why**, **How**, **Where**, **When**, and **Who**, covering both the macro (global) and micro (civic) aspects of this highly advanced command platform.

---

## 1. WHAT is God's Eye OS?

**God's Eye OS** is an AI-powered global ontology engine and dual-domain command platform. It is a comprehensive situation awareness dashboard designed to ingest massive amounts of data from multiple domains (geopolitics, economics, defense, climate, and local society) and distill it into a single, constantly updating intelligence graph.

It operates on two distinct layers:
*   **Global/Macro Layer:** Tracks countries, risk signals, trade corridors, macro-economics, defense postures, and strategic global assets. It visualizes global threats, supply chain disruptions, and geopolitical relationships.
*   **Civic/Micro Layer (India Focus):** Tracks granular Indian democratic components down to the street level. This includes constituencies, wards, voting booths, citizen demographics, political field workers, active government schemes (e.g., PM-KISAN, Jal Jeevan), infrastructure projects, and real-time citizen complaints.

**Core Distinctive Features:**
*   **Agentic Intelligence Engine:** Features a "Strategic Agent" (AI planner) powered by Large Language Models (LLMs) that can answer natural language queries, connect disparate data points, simulate "what-if" scenarios, and track the evidence path of its hypotheses.
*   **Interactive 3D Knowledge Space:** Uses an interactive 3D globe with sentiment heatmap pulsing, a force-directed visual knowledge graph, and 2D geographic maps.
*   **Omni-channel Ingestion:** Consumes structured data (via APIs from USGS, World Bank, etc.) and unstructured data (RSS feeds, social media, citizen complaints).
*   **Graceful Degradation:** Capable of working fully offline with seeded/cached data, ensuring high resilience during connectivity drops.

---

## 2. WHY was it built?

God's Eye OS was conceived and built specifically for the **India Innovates 2026 — World's Largest Civic Tech Hackathon**.

**The Core Problem it Solves:**
Decision-makers (national leaders, strategic advisors, and local politicians) often suffer from disconnected data silos. A global oil price surge or a geopolitical conflict far away eventually trickles down to affect local inflation, triggering specific local civic complaints in a remote Indian ward. Traditional systems track these separately.

God's Eye OS bridges this gap. It exists to unify these silos and shift governance, defense planning, and political strategy from being **strictly reactive to highly predictive**. It allows leadership to:
1. Anticipate global shocks before they hit the local level.
2. Track the effectiveness of on-ground infrastructure and welfare schemes.
3. Automatically route civic complaints to the responsible human field workers with AI-generated action plans.

---

## 3. HOW does it work? (Architecture & Technical Stack)

The system works as a continuous loop of ingestion, graph synthesis, AI reasoning, and front-end visualization. 

### A. The Data Pipeline & Intelligence Loop
1. **Ingestion (The Eyes & Ears):** Background services continually scrape live RSS feeds (Reuters, Al Jazeera, Govt of India portals), global APIs (Earthquake data from USGS, stock/economic data), and social sentiment (Reddit, Mastodon). 
2. **Synthesis (The Brain):** An AI component (Intent Parser & Insight Synthesizer) reads these inputs. It performs Entity Extraction (e.g., identifying a politician's name or a geographic location), runs Sentiment Analysis, and standardizes the info into "Signals".
3. **Graph Storage (The Memory):** These signals are mapped into a massive semantic graph. Entities are linked via relationships (e.g., `[Conflict X] --affects--> [Trade Route Y] --causes_inflation_in--> [Constituency Z]`).
4. **Resolution (The Output):** When a user asks a complex question ("How will the ongoing strife in the Middle East affect supply chains in Mumbai?"), the orchestrator agent plans out tool calls, queries the graph and external APIs, filters out hallucinations, and returns a synthetic briefing and interactive UI nodes.

### B. The Technology Stack
*   **Backend & Orchestration:**
    *   **Python / FastAPI:** High-performance async API server.
    *   **LLM Providers:** **LangChain / LangGraph** acting as the orchestration framework, backed heavily by **Groq** (for fast inference) and **Google Gemini/OpenAI** as reasoning alternatives. Pydantic v2 is used for strict data validation (preventing AI hallucination formatting errors).
    *   **Async Processing:** Makes heavy use of `asyncio` and `aiohttp` to do high-throughput concurrent data fetching.

*   **Data & Persistence:**
    *   **Neo4j:** The core Knowledge Graph database maintaining the relationships between world events, local assets, and civic entities.
    *   **PostgreSQL + PostGIS:** Relational storage for geospatial geometries (mapping constituencies, wards, infrastructure).
    *   **Redis:** Fast caching layer to prevent API rate limits.
    *   **Fallback engine:** Standard `.json` seeding and in-memory caches to keep the app alive during network failures.

*   **Frontend (The Command UI):**
    *   **React 19 & TypeScript:** Scalable, strictly-typed UI layer scaffolded with **Vite**.
    *   **State Management:** **Zustand** for global shared states (theme, selected entities) and **React Query** for caching server data.
    *   **Visualizations:** 
        *   `react-globe.gl` / Three.js for the volumetric Earth and heat maps.
        *   `Leaflet` for the 2D command map.
        *   `react-force-graph` for relationship visualizations.
    *   **Styling & Animation:** **Tailwind CSS** (for layout) and **Framer Motion** (for smooth, sci-fi cyber-command UI transitions).

---

## 4. WHERE does it operate?

**Visually & Operationally:**
*   **The Macro Canvas (Global):** Functions as an international War Room spanning weather paths, global market dynamics, shipping lanes, and international conflict zones.
*   **The Micro Canvas (India):** Dives down into an exact hyper-local level. It renders Indian states, narrows into specific constituencies (e.g., Chandni Chowk), down to wards, and exactly to the street level where specific political field workers (Karyakartas/Pramukhs) and infrastructure development zones exist.

---

## 5. WHEN does it happen?

*   **Real-time execution:** The system is explicitly designed not as a static dashboard, but as a live `Runtime Intelligence` loop. As long as the backend is awake, it updates sentiments, plots ongoing natural disasters (wildfires, earthquakes), and parses incoming JSON civic complaints.
*   **Project Timeline Context:** Developed specifically as a high-speed sprint tailored for the final hackathon demo targeted on **March 28, 2026**. 

---

## 6. WHO uses it?

**Target Users (End-Users):**
1.  **National/State Strategic Leaders:** To view macro-economic shocks, defense alerts, and geopolitical threat vectors.
2.  **Political Campaign Managers / Governance Teams:** To monitor voter sentiment, trace the successful delivery of government welfare schemes (beneficiary tracking), and gauge regional risk.
3.  **Local Civic Operators (Field Workers):** Who receive auto-generated action plans based on complaints logged by citizens regarding roads, water, or electricity. (Though they don't use the massive OS, they are the functional endpoints driven by it).

---

## Summary

In short, **God's Eye OS** is exactly what its name implies: an omniscient, deeply interconnected command-and-control platform. It marries high-level global strategic reconnaissance with grounded Indian socio-political analytics. Through an intricate web of Python microservices, graph databases, and LLM reasoning, it turns raw, chaotic world data into clear, geographic, and actionable insights rendered in an immersive 3D/2D React interface.