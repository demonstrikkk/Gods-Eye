# Gods-Eye OS Architecture Plan

This plan is aligned with the current implementation and describes how to harden it into a production-grade agentic intelligence platform.

## 1. Current Baseline (As Implemented)

### Platform Shape

- Monorepo with FastAPI backend and React/Vite frontend
- Runtime intelligence loops for global signal refresh and feed aggregation
- Seeded in-memory civic + global ontology model
- Strategic and civic agentic pipelines
- Optional infra services via Docker Compose (Postgres/PostGIS, Neo4j, Redis)

### Agentic Baseline

- Strategic pipeline: planner + parallel tools + reasoner + structured metadata
- Civic pipeline: extraction + sentiment + geography + action recommendation
- Civic pipeline currently defaults to mock mode (`CIVIC_AGENT_MOCK_MODE=True`)

## 2. Plan Objectives

1. Stabilize runtime behavior and API contracts before expanding scope
2. Separate real-source evidence from seeded/demo data structurally
3. Increase trustworthiness and explainability of agentic outputs
4. Improve durability, observability, and deployment repeatability
5. Create room for a dedicated country intelligence workspace

## 3. Workstreams and Phases

## Phase 0: Stabilization Baseline

### Goals

- Lock down the current behavior of runtime state, country analysis, and global map APIs
- Catch regressions before additional architecture refactors

### Tasks

1. Add regression tests for runtime state merge/dedup behavior in `runtime_intelligence.py`
2. Add country-analysis tests for evidence/source-status handling, especially unavailable search or sparse live data
3. Add API contract tests for `GET /data/global/overview`, `/countries`, `/signals`, `/assets`, `/corridors`, and `/country-analysis/{id}`
4. Add frontend-safe filtering tests for layer-level data assumptions where possible

### Exit Criteria

- A runnable backend test suite exists and passes locally
- The core global data endpoints have stable response expectations
- Map-critical data paths are protected against malformed/null coordinates

## Phase A: Contract and Source-Boundary Hardening

### Goals

- Ensure endpoint uniqueness and deterministic behavior
- Prevent seeded/demo-safe values from being exposed as live intelligence

### Tasks

1. Consolidate duplicate route declarations in `backend/app/api/endpoints/data.py`
2. Introduce explicit response models for strategic and country-analysis outputs
3. Split source normalization from runtime synthesis so live evidence, cached evidence, and seeded context are tagged separately
4. Add freshness/provenance fields to the top-level global and country-analysis payloads

### Exit Criteria

- No duplicate method/path handlers for primary APIs
- Stable schema for top-level intelligence and global endpoints
- Real, cached, and seeded data are distinguishable in the service layer and payloads

## Phase B: Country Intelligence Workspace

### Goals

- Move beyond sidebar-only country analysis
- Create a usable analyst workflow for country research and comparison

### Tasks

1. Build a dedicated country workspace view
2. Add comparative country mode for two or three countries
3. Add trend history and mini time-series views inside country analysis
4. Add country-specific scenario presets and AI query templates

### Exit Criteria

- Country research no longer depends on the sidebar alone
- Comparison and trend workflows are available without manual prompt assembly

## Phase C: Entity Resolution and Signal Quality

### Goals

- Reduce noise from broader feed coverage
- Improve confidence and entity consistency across layers

### Tasks

1. Resolve mentions into canonical country, actor, company, and corridor entities
2. Merge duplicate signals across feeds and connectors
3. Introduce confidence scoring and source-weighting
4. Add deterministic "what changed?" and "why is this risky?" explainers before LLM generation

### Exit Criteria

- Duplicate headline bursts no longer dominate the ontology
- Every important signal can be traced to evidence and confidence logic

## Phase D: Agentic Reliability Hardening

### Goals

- Keep outputs grounded, reproducible, and inspectable
- Improve planner/tool/reasoning validation and traceability

### Tasks

1. Add planner quality checks (domain coverage, tool rationale)
2. Add structured tool execution telemetry (latency, success/failure, timeout reason)
3. Add output validation layer for strategic JSON shape
4. Add deterministic fallback templates for each major query class
5. Add replayable fixtures for strategic pipeline integration tests

### Exit Criteria

- Strategic endpoint always returns a valid schema object
- Per-tool execution diagnostics are available for every run
- Golden-test prompts produce expected structural outputs

## Phase E: Data Durability and State Management

### Goals

- Move from file-first runtime state toward robust persistence

### Tasks

1. Create a persistence abstraction around runtime state read/write
2. Add optional DB-backed runtime signal/history storage
3. Store source-health history for trend tracking
4. Add retention and pruning policies for feed briefs and runtime signals

### Exit Criteria

- Runtime state survives restart without JSON-only dependency
- Historical source health and signal trends are queryable

## Phase F: Frontend Reliability and UX Trust

### Goals

- Improve user trust in freshness, provenance, and interaction behavior

### Tasks

1. Standardize live/stale/limited badges across global, AI, and map panels
2. Add per-view loading/error empty-state consistency
3. Add layer legend with counts and source provenance
4. Add map render performance guardrails for high marker counts and dense overlays

### Exit Criteria

- Every major panel displays freshness and source status
- Map interaction remains reliable at expected runtime dataset sizes

## Phase G: Civic Pipeline Activation Strategy

### Goals

- Keep current mock mode for cost control while enabling safe real-mode rollout

### Tasks

1. Keep `CIVIC_AGENT_MOCK_MODE=True` in default config
2. Add environment profile docs for mock mode and real mode
3. Add smoke test command to validate real-mode dependency readiness
4. Add per-stage error reporting in civic pipeline responses

### Exit Criteria

- One-step switch exists between mock and real mode
- Clear operational checklist exists before enabling real mode

## Phase H: Deployment and Operations

### Goals

- Make local/dev/prod profiles explicit and repeatable

### Tasks

1. Provide separate compose profiles:
   - `infra-only`
   - `full-stack`
2. Add backend/frontend containerization docs for the current repository
3. Add startup health checklist and dependency verification commands
4. Add CI pipeline stages: lint, type-check, backend checks, frontend build

### Exit Criteria

- Deterministic setup docs exist for all modes
- CI validates baseline functionality on every change

## 4. Data Modeling Evolution Plan

### Current

- In-memory seeded civic and ontology objects
- Runtime overlays in JSON file
- Neo4j writes for complaint relationships

### Target

1. Unified domain models with shared IDs across civic/global graph
2. Event history model for signals and feed evidence
3. Provenance model for each strategic assertion
4. Materialized summaries for fast UI loading

## 5. Quality Gates

For each phase, enforce:

1. Static checks
   - backend syntax and imports
   - frontend type checks
2. Endpoint smoke tests
   - global overview/countries/signals/assets
   - strategic-analysis and scenario-simulate
3. Agentic regression tests
   - planner output validity
   - tool timeout handling
   - fallback behavior quality

## 6. Risks and Mitigations

### Risk: External source instability

- Mitigation: status tagging, cached snapshots, fallback narratives

### Risk: LLM output schema drift

- Mitigation: strict parser + schema validation + deterministic fallback

### Risk: Seeded and live evidence are mixed in the same runtime layer

- Mitigation: source-boundary hardening in Phase A plus provenance tagging in payloads

### Risk: Route ambiguity from duplicate handlers

- Mitigation: route deduplication and contract tests in Phase A

### Risk: Runtime memory growth with feed/signal accumulation

- Mitigation: retention limits and periodic pruning

## 7. Recommended Execution Order

1. Phase 0 (stabilization baseline)
2. Phase A (contracts/source boundaries)
3. Phase B (country workspace)
4. Phase C (entity resolution and signal quality)
5. Phase D (agentic reliability)
6. Phase E (durability)
7. Phase F (frontend reliability)
8. Phase G (civic mode strategy)
9. Phase H (deployment and CI)

This ordering minimizes regression risk, separates trust and provenance concerns early, and delays feed/connectivity expansion until the current intelligence path is measurable and testable.
