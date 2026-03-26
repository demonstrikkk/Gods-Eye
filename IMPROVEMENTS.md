# Gods-Eye OS Improvements

This file tracks the practical improvement path for the current codebase, not just the original hackathon vision.

## 1. What Is Already Improved

- Global country map now supports live all-country coverage through a public country catalog.
- Runtime intelligence is persisted, so signals survive backend restarts.
- Layer system has expanded beyond basic country/signal/corridor rendering.
- Clicked-country analysis now exists as a real backend + UI flow.
- Feed coverage is broader and more global.
- Source-health and market pulse are visible in the UI.
- `data.gov.in` can use explicit resource IDs or cached query discovery.

## 2. Highest-Value Next Improvements

### 2.1 Country Intelligence Depth

- Add a dedicated full-page country workspace instead of only a sidebar column.
- Add comparative country mode, so two or three countries can be analyzed side-by-side.
- Add trend history per country, not just current synthesized posture.
- Add country-specific scenario simulation presets.

### 2.2 Better Entity Resolution

- Resolve feed mentions into canonical country, actor, company, and corridor entities.
- Merge duplicate signals from multiple sources.
- Introduce confidence scoring per signal.
- Add source-weighting logic so weak headlines do not dominate the ontology.

### 2.3 Stronger Global Telemetry

- Add optional ship telemetry if a reliable free tier is available.
- Add optional outage telemetry for internet disruptions where public APIs allow it.
- Add more climate and disaster feeds with regional granularity.
- Add better aviation and military-activity differentiation.

### 2.4 Ontology Graph Upgrade

- Move from simple linked nodes to typed relationships with richer semantics.
- Add actor-to-asset, actor-to-event, and event-to-corridor edges.
- Add temporal validity on signals and relationships.
- Add graph snapshots or replay mode.

## 3. Product-Level Improvements

- Add saved watchlists for countries, assets, and corridors.
- Add alert rules and thresholds per layer.
- Add timeline scrubber and incident playback mode.
- Add exportable intelligence briefs as Markdown or PDF.
- Add operator notes and pinned map annotations.

## 4. UI/UX Improvements

- Add layer legend with counts and source provenance.
- Add clustering on dense maps when all-country coverage is active.
- Add hover summaries for assets and signals on globe mode.
- Add better empty/loading states for slow connectors.
- Add mini trend charts inside country analysis.

## 5. Backend Improvements

- Persist runtime state into a real database instead of only JSON files.
- Add scheduled source backoff and retry policy by connector health.
- Add connector-level caching and freshness metadata.
- Split source normalization into dedicated adapters instead of one large aggregator file.
- Add tests around runtime merge logic and country-analysis synthesis.

## 6. AI Improvements

- Use country-analysis payloads as structured context for the AI console by default.
- Add query templates tied to clicked entities.
- Add explainability blocks showing which signals drove each AI conclusion.
- Add "why is this risky?" and "what changed?" style deterministic explainers before LLM generation.
- Add multi-source contradiction detection.

## 7. Known Gaps

- Not every requested layer is truly real-time yet.
- Some infrastructure layers are curated ontology assets rather than live telemetry.
- Free/public sources have uneven coverage across regions.
- Feed-driven inference is still weaker than a real graph-resolution pipeline.
- The backend currently mixes demo-safe seeded data and live-source enrichment in the same service layer.

## 8. Recommended Execution Order

1. Add tests for runtime state, country analysis, and layer filtering.
2. Split connectors into cleaner modules by domain.
3. Build a dedicated country workspace.
4. Add better entity resolution and confidence scoring.
5. Introduce a proper graph/database-backed ontology runtime.
6. Add premium or optional connectors only after the free-source path is stable.
