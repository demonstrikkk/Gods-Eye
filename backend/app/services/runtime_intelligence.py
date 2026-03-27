import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List

from app.data.store import store
from app.services.osint_aggregator import osint_engine

logger = logging.getLogger("runtime_intelligence")

REFRESH_INTERVAL_SECONDS = 300


class RuntimeIntelligenceEngine:
    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self._warm_task: asyncio.Task | None = None
        self._state_path = Path(__file__).resolve().parent.parent / "data" / "runtime_state.json"
        self._state = self._load_state()

    def _warm_country_search_cache(self, top_n: int = 5):
        try:
            watchlist = sorted(self.get_enriched_countries(), key=lambda country: country["risk_index"], reverse=True)[:top_n]
            for country in watchlist:
                osint_engine.get_country_search_briefs(country["name"], country.get("region"))
            logger.info(f"Country search cache warmed for {len(watchlist)} watchlist countries.")
        except Exception as e:
            logger.warning(f"Country search cache warm failed: {e}")

    async def _warm_country_search_cache_async(self):
        await asyncio.to_thread(self._warm_country_search_cache)

    def _default_state(self) -> Dict[str, Any]:
        return {
            "dynamic_signals": [],
            "runtime_assets": [],
            "runtime_corridors": [],
            "source_health": [],
            "market_snapshot": [],
            "country_catalog": [],
            "last_refresh": None,
        }

    def _load_state(self) -> Dict[str, Any]:
        if not self._state_path.exists():
            return self._default_state()
        try:
            return json.loads(self._state_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load runtime intelligence state: {e}")
            return self._default_state()

    def _persist_state(self):
        try:
            self._state_path.write_text(json.dumps(self._state, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to persist runtime intelligence state: {e}")

    def get_state(self) -> Dict[str, Any]:
        return self._state

    def get_source_health(self) -> List[Dict[str, Any]]:
        return self._state.get("source_health", [])

    def get_market_snapshot(self) -> List[Dict[str, Any]]:
        return self._state.get("market_snapshot", [])

    def get_country_catalog(self) -> List[Dict[str, Any]]:
        return self._state.get("country_catalog", [])

    def get_seeded_assets(
        self,
        country_id: str | None = None,
        layer: str | None = None,
    ) -> List[Dict[str, Any]]:
        assets = store.get_global_assets(country_id=country_id, layer=layer)
        return [self._annotate_asset(asset, "seeded") for asset in assets]

    def get_runtime_assets(
        self,
        country_id: str | None = None,
        layer: str | None = None,
    ) -> List[Dict[str, Any]]:
        assets = [
            self._annotate_asset(asset, asset.get("source_mode", "runtime"))
            for asset in self._state.get("runtime_assets", [])
        ]
        if country_id:
            assets = [asset for asset in assets if asset.get("country_id") == country_id]
        if layer:
            assets = [asset for asset in assets if asset.get("layer") == layer]
        return assets

    def get_structural_assets(
        self,
        country_id: str | None = None,
        layer: str | None = None,
        include_seeded: bool = True,
    ) -> List[Dict[str, Any]]:
        runtime_assets = self.get_runtime_assets(country_id=country_id, layer=layer)
        seeded_assets = self.get_seeded_assets(country_id=country_id, layer=layer) if include_seeded else []
        seen = set()
        merged: List[Dict[str, Any]] = []
        for asset in runtime_assets + seeded_assets:
            asset_id = asset.get("id")
            if asset_id in seen:
                continue
            seen.add(asset_id)
            merged.append(asset)
        return merged

    def get_seeded_corridors(self) -> List[Dict[str, Any]]:
        return [self._annotate_corridor(corridor, "seeded") for corridor in store.get_global_corridors()]

    def get_runtime_corridors(self) -> List[Dict[str, Any]]:
        return [
            self._annotate_corridor(corridor, corridor.get("source_mode", "runtime"))
            for corridor in self._state.get("runtime_corridors", [])
        ]

    def get_global_corridors(self, include_seeded: bool = True) -> List[Dict[str, Any]]:
        runtime_corridors = self.get_runtime_corridors()
        seeded_corridors = self.get_seeded_corridors() if include_seeded else []
        seen = set()
        merged: List[Dict[str, Any]] = []
        for corridor in runtime_corridors + seeded_corridors:
            corridor_id = corridor.get("id")
            if corridor_id in seen:
                continue
            seen.add(corridor_id)
            merged.append(corridor)
        return merged

    def _source_provenance_summary(self) -> Dict[str, Any]:
        health = self.get_source_health()
        counts = {
            "live_sources": 0,
            "limited_sources": 0,
            "unavailable_sources": 0,
            "fallback_sources": 0,
            "error_sources": 0,
        }

        for item in health:
            status = item.get("status")
            if status == "live":
                counts["live_sources"] += 1
            elif status == "limited":
                counts["limited_sources"] += 1
            elif status == "unavailable":
                counts["unavailable_sources"] += 1
            elif status == "fallback":
                counts["fallback_sources"] += 1
            elif status == "error":
                counts["error_sources"] += 1

        return {
            **counts,
            "total_sources": len(health),
            "seeded_context": True,
            "runtime_state_backed": True,
            "last_refresh": self._state.get("last_refresh"),
        }

    @staticmethod
    def _stability_from_risk(risk: int) -> str:
        if risk >= 75:
            return "Critical"
        if risk >= 55:
            return "Watch"
        if risk >= 40:
            return "Elevated"
        return "Stable"

    @staticmethod
    def _domain_from_layer(layer: str) -> str:
        mapping = {
            "conflict": "Geopolitics",
            "defense": "Defense",
            "mobility": "Trade",
            "infrastructure": "Infrastructure",
            "cyber": "Cyber",
            "climate": "Climate",
            "economics": "Economics",
            "governance": "Governance",
        }
        return mapping.get(layer, "Global")

    def _nearest_country_id(self, lat: float | None, lng: float | None) -> str:
        if lat is None or lng is None:
            return "CTR-IND"
        candidates = self.get_country_catalog() or store.get_global_countries()
        nearest = None
        best_distance = None
        for country in candidates:
            clat = country.get("lat")
            clng = country.get("lng")
            if clat is None or clng is None:
                continue
            distance = (clat - lat) ** 2 + (clng - lng) ** 2
            if best_distance is None or distance < best_distance:
                best_distance = distance
                nearest = country.get("id")
        return nearest or "CTR-IND"

    @staticmethod
    def _annotate_signal(signal: Dict[str, Any], source_mode: str) -> Dict[str, Any]:
        annotated = dict(signal)
        annotated["source_mode"] = source_mode
        annotated["source_origin"] = "runtime_state" if source_mode == "runtime" else "seeded_ontology"
        return annotated

    @staticmethod
    def _annotate_asset(asset: Dict[str, Any], source_mode: str) -> Dict[str, Any]:
        annotated = dict(asset)
        annotated["source_mode"] = source_mode
        annotated["source_origin"] = "runtime_state" if source_mode == "runtime" else "seeded_ontology"
        return annotated

    @staticmethod
    def _annotate_corridor(corridor: Dict[str, Any], source_mode: str) -> Dict[str, Any]:
        annotated = dict(corridor)
        annotated["source_mode"] = source_mode
        annotated["source_origin"] = "runtime_state" if source_mode == "runtime" else "seeded_ontology"
        return annotated

    def _signal_counts(self, signals: List[Dict[str, Any]]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for signal in signals:
            country_id = signal.get("country_id")
            if not country_id:
                continue
            counts[country_id] = counts.get(country_id, 0) + 1
        return counts

    def get_seeded_signals(self) -> List[Dict[str, Any]]:
        return [self._annotate_signal(signal, "seeded") for signal in store.get_global_signals()]

    def get_runtime_signals(self) -> List[Dict[str, Any]]:
        return [
            self._annotate_signal(signal, signal.get("source_mode", "runtime"))
            for signal in self._state.get("dynamic_signals", [])
        ]

    def get_enriched_countries(self) -> List[Dict[str, Any]]:
        runtime_counts = self._signal_counts(self.get_runtime_signals())
        seeded_counts = self._signal_counts(self.get_seeded_signals())
        counts = self._signal_counts(self.get_dynamic_signals())
        base_map = {country["id"]: dict(country) for country in store.get_global_countries()}
        asset_counts: Dict[str, int] = {}
        layer_domains: Dict[str, set[str]] = {}
        for asset in self.get_structural_assets():
            country_id = asset.get("country_id")
            if not country_id:
                continue
            asset_counts[country_id] = asset_counts.get(country_id, 0) + 1
            layer_domains.setdefault(country_id, set()).add(self._domain_from_layer(asset.get("layer", "")))

        for signal in self.get_dynamic_signals():
            country_id = signal.get("country_id")
            if not country_id:
                continue
            layer_domains.setdefault(country_id, set()).add(self._domain_from_layer(signal.get("layer", "")))
            if signal.get("category"):
                layer_domains[country_id].add(signal["category"])

        live_countries = self.get_country_catalog()
        rows = live_countries or store.get_global_countries()
        countries = []
        for row in rows:
            country = dict(row)
            base = base_map.get(country["id"], {})
            runtime_signal_count = runtime_counts.get(country["id"], 0)
            seeded_signal_count = seeded_counts.get(country["id"], 0)
            active_signals = max(base.get("active_signals", 0), counts.get(country["id"], 0))
            asset_count = max(base.get("asset_count", 0), asset_counts.get(country["id"], 0))
            population = country.get("population") or base.get("population") or 0
            influence = base.get("influence_index")
            if influence is None:
                influence = min(98, max(18, int(population / 25_000_000) + asset_count * 3 + active_signals * 2))
            risk = base.get("risk_index")
            if risk is None:
                risk = min(95, max(22, 20 + active_signals * 10 + asset_count * 2))
            stability = base.get("stability") or self._stability_from_risk(risk)
            top_domains = base.get("top_domains") or sorted(layer_domains.get(country["id"], {"Economics", "Climate", "Infrastructure"}))[:3]
            country.update(
                {
                    "risk_index": risk,
                    "influence_index": influence,
                    "sentiment": base.get("sentiment", max(35, min(78, 68 - int(risk / 2) + active_signals))),
                    "stability": stability,
                    "pressure": base.get("pressure", "Live world-scale signals synthesized from open-source feeds."),
                    "top_domains": top_domains,
                    "active_signals": active_signals,
                    "runtime_signal_count": runtime_signal_count,
                    "seeded_signal_count": seeded_signal_count,
                    "asset_count": asset_count,
                    "capital": country.get("capital") or base.get("capital"),
                    "population": population,
                    "macro_region": country.get("macro_region") or country.get("region"),
                    "iso3": country.get("iso3") or country["id"].replace("CTR-", ""),
                    "country_catalog_mode": "runtime" if live_countries else "seeded",
                    "signal_source_mode": (
                        "runtime_plus_seeded"
                        if runtime_signal_count and seeded_signal_count
                        else "runtime_only"
                        if runtime_signal_count
                        else "seeded_only"
                        if seeded_signal_count
                        else "none"
                    ),
                }
            )
            countries.append(country)
        return sorted(countries, key=lambda item: (-item["risk_index"], item["name"]))

    def get_country(self, country_id: str) -> Dict[str, Any] | None:
        return next((country for country in self.get_enriched_countries() if country["id"] == country_id), None)

    def find_country_by_query(self, query: str) -> Dict[str, Any] | None:
        normalized = (query or "").strip().lower()
        if not normalized:
            return None

        candidates = self.get_enriched_countries()
        exact_fields = ("name", "capital", "iso3")
        partial_fields = ("name", "capital", "region", "macro_region", "iso3")

        for country in candidates:
            for field in exact_fields:
                value = str(country.get(field) or "").strip().lower()
                if value and normalized == value:
                    return country

        for country in candidates:
            for field in partial_fields:
                value = str(country.get(field) or "").strip().lower()
                if value and normalized in value:
                    return country

        return None

    def get_dynamic_signals(self, include_seeded: bool = True) -> List[Dict[str, Any]]:
        base = self.get_seeded_signals() if include_seeded else []
        dynamic = self.get_runtime_signals()
        seen = set()
        merged = []
        for signal in dynamic + base:
            if signal.get("id") in seen:
                continue
            seen.add(signal.get("id"))
            merged.append(signal)
        return merged

    def get_global_overview(self) -> Dict[str, Any]:
        overview = dict(store.get_global_overview())
        overview["total_countries"] = len(self.get_enriched_countries())
        overview["total_signals"] = len(self.get_dynamic_signals())
        overview["runtime_signals"] = len(self.get_runtime_signals())
        overview["seeded_signals"] = len(self.get_seeded_signals())
        overview["total_assets"] = len(self.get_structural_assets())
        overview["runtime_assets"] = len(self.get_runtime_assets())
        overview["seeded_assets"] = len(self.get_seeded_assets())
        overview["active_corridors"] = len(self.get_global_corridors())
        overview["runtime_corridors"] = len(self.get_runtime_corridors())
        overview["seeded_corridors"] = len(self.get_seeded_corridors())
        overview["live_sources"] = len([item for item in self.get_source_health() if item.get("status") == "live"])
        overview["last_refresh"] = self._state.get("last_refresh")
        overview["market_tickers"] = len(self.get_market_snapshot())
        overview["provenance"] = self._source_provenance_summary()
        return overview

    def get_global_graph(self) -> Dict[str, Any]:
        graph = store.get_global_graph()
        nodes = list(graph["nodes"])
        links = list(graph["links"])
        for signal in self.get_runtime_signals()[:24]:
            node_id = f"SIGNAL-{signal['id']}"
            nodes.append(
                {
                    "id": node_id,
                    "group": "Signal",
                    "label": signal.get("title", "Live signal"),
                    "val": 4,
                    "color": "#ef4444" if signal.get("severity") == "High" else "#38bdf8",
                }
            )
            if signal.get("country_id"):
                links.append({"source": signal["country_id"], "target": node_id, "label": "LIVE_SIGNAL"})
        return {"nodes": nodes, "links": links}

    def get_country_analysis(self, country_id: str) -> Dict[str, Any] | None:
        country = self.get_country(country_id)
        if not country:
            return None

        signals = [signal for signal in self.get_dynamic_signals() if signal.get("country_id") == country_id][:8]
        runtime_signals = [signal for signal in signals if signal.get("source_mode", "runtime") == "runtime"]
        seeded_signals = [signal for signal in signals if signal.get("source_mode") == "seeded"]
        assets = self.get_structural_assets(country_id=country_id)[:8]
        all_feeds = store.get_recent_feed_briefs(limit=250)
        country_terms = {country["name"].lower()}
        if country.get("capital"):
            country_terms.add(str(country["capital"]).lower())
        related_feeds = [
            feed
            for feed in all_feeds
            if any(term in f"{feed.get('text', '')} {feed.get('summary', '')}".lower() for term in country_terms)
        ][:6]

        weather = osint_engine.get_open_meteo_weather(country["lat"], country["lng"])
        world_bank = osint_engine.get_world_bank_snapshot().get("countries", {}).get(country.get("iso3"), {})
        search_briefs = osint_engine.get_country_search_briefs(country["name"], country.get("region"))
        search_providers = search_briefs.get("providers", []) if isinstance(search_briefs.get("providers"), list) else []
        world_bank_live = any(
            isinstance(metric, dict) and metric.get("value") is not None
            for metric in world_bank.values()
        )
        search_live = bool(search_briefs.get("results")) and any(provider.get("status") == "live" for provider in search_providers)
        search_limited = bool(search_briefs.get("results")) and not search_live
        search_status = "live" if search_live else "limited" if search_limited else "unavailable"
        if search_status == "unavailable":
            search_briefs = {
                **search_briefs,
                "results": [],
                "status": "unavailable",
            }
        corridors = [
            corridor
            for corridor in self.get_global_corridors()
            if corridor.get("from_country") == country_id or corridor.get("to_country") == country_id
        ][:8]
        market_quotes = self.get_market_snapshot()[:6]

        risk_factors: List[Dict[str, Any]] = []
        if country["risk_index"] >= 70:
            risk_factors.append(
                {
                    "factor": "High systemic risk",
                    "severity": "Critical",
                    "description": f"{country['name']} is currently running at risk index {country['risk_index']} with {country['active_signals']} active signals.",
                }
            )
        if signals:
            top_signal = signals[0]
            risk_factors.append(
                {
                    "factor": top_signal["title"],
                    "severity": top_signal["severity"],
                    "description": top_signal["summary"],
                }
            )
        if assets:
            risk_factors.append(
                {
                    "factor": f"{assets[0]['kind']} exposure",
                    "severity": "High" if assets[0]["importance"] >= 85 else "Medium",
                    "description": assets[0]["description"],
                }
            )
        if weather.get("current", {}).get("wind_speed_10m") or weather.get("daily", {}).get("precipitation_sum"):
            risk_factors.append(
                {
                    "factor": "Weather posture",
                    "severity": "Medium",
                    "description": f"Current weather snapshot indicates wind {weather.get('current', {}).get('wind_speed_10m')} and precipitation {weather.get('daily', {}).get('precipitation_sum')}.",
                }
            )

        opportunities = []
        if country["influence_index"] >= 70:
            opportunities.append(f"{country['name']} remains a high-influence node for {', '.join(country['top_domains'][:2])}.")
        if world_bank.get("gdp_current_usd", {}).get("value"):
            opportunities.append("World Bank macro snapshot is available for deeper economic comparison.")
        if assets:
            opportunities.append(f"{len(assets)} mapped strategic assets give this country strong ontology coverage.")

        source_status = [
            {"label": "Signals", "status": "live" if signals else "limited", "count": len(signals)},
            {"label": "Open-Meteo", "status": weather.get("status", "error"), "count": 1 if weather.get("current") else 0},
            {"label": "World Bank", "status": "live" if world_bank_live else "unavailable", "count": len(world_bank) if world_bank_live else 0},
            {"label": "RSS Feeds", "status": "live" if related_feeds else "limited", "count": len(related_feeds)},
            {"label": "Open Search", "status": search_status, "count": len(search_briefs.get("results", []))},
            {"label": "Corridors", "status": "live" if corridors else "limited", "count": len(corridors)},
            {"label": "Market Snapshot", "status": "live" if market_quotes else "limited", "count": len(market_quotes)},
        ]

        evidence_points: List[str] = []
        if signals:
            evidence_points.append(f"{len(signals)} live signals are currently associated with {country['name']}.")
        if related_feeds:
            evidence_points.append(f"{len(related_feeds)} recent feed mentions reference {country['name']} or its capital.")
        if weather.get("status") == "live":
            evidence_points.append(
                f"Weather evidence is live with temperature {weather.get('current', {}).get('temperature_2m')} and wind {weather.get('current', {}).get('wind_speed_10m')}."
            )
        if world_bank_live:
            gdp_year = world_bank.get("gdp_current_usd", {}).get("date")
            inflation_year = world_bank.get("inflation_consumer", {}).get("date")
            evidence_points.append(
                f"World Bank macro series are available for GDP ({gdp_year or 'n/a'}) and inflation ({inflation_year or 'n/a'})."
            )
        if search_live:
            evidence_points.append(f"{len(search_briefs.get('results', []))} live open-web search hits were retrieved for validation.")
        elif search_limited:
            evidence_points.append(f"{len(search_briefs.get('results', []))} cached or fallback search hits were retained with limited confidence.")
        if corridors:
            evidence_points.append(f"{len(corridors)} corridor links are currently mapped to {country['name']}.")
        if not evidence_points:
            evidence_points.append("No live external evidence is currently available for this country; rely on mapped ontology context only.")

        summary = (
            f"{country['name']} is in {country['stability'].lower()} posture with risk {country['risk_index']} "
            f"and influence {country['influence_index']}. Pressure centers on {country['pressure']}. "
            f"The system currently tracks {country['active_signals']} live signals and {country.get('asset_count', 0)} structural assets for this node."
        )

        research_brief_parts = [
            f"{country['name']} currently sits in a {country['stability'].lower()} operating posture."
        ]
        if signals:
            research_brief_parts.append(
                f"The real-time layer is active with {len(signals)} country-linked signals, led by '{signals[0]['title']}'."
            )
        if related_feeds:
            research_brief_parts.append(
                f"Recent feed coverage is active across {len(related_feeds)} tracked mentions."
            )
        if weather.get("status") == "live":
            research_brief_parts.append(
                f"Open-Meteo weather is live for the capital zone and can be used as current operating context."
            )
        if world_bank_live:
            research_brief_parts.append(
                "World Bank macro data is present for baseline economic framing."
            )
        if search_live:
            research_brief_parts.append(
                f"Open search validation returned {len(search_briefs.get('results', []))} usable links."
            )
        elif search_limited:
            research_brief_parts.append(
                "Open search returned limited fallback evidence; use these links as weak validation only."
            )
        else:
            research_brief_parts.append(
                "Open search validation is currently unavailable, so this brief excludes unsupported search claims."
            )
        if corridors:
            research_brief_parts.append(
                f"The country is linked to {len(corridors)} active corridor records, improving logistics and trade context quality."
            )

        climate_active = any(signal.get("layer") == "climate" for signal in signals)
        economic_active = any(signal.get("layer") == "economics" for signal in signals) or world_bank_live
        geopolitics_active = any(signal.get("layer") == "conflict" for signal in signals)
        logistics_active = bool(corridors) or any(asset.get("layer") in {"mobility", "infrastructure"} for asset in assets)

        relationship_intelligence: List[Dict[str, Any]] = []
        if climate_active and economic_active:
            relationship_intelligence.append(
                {
                    "link": "climate<->economy",
                    "confidence": "high",
                    "insight": "Climate volatility is currently interacting with economic indicators and should be modeled jointly.",
                }
            )
        if geopolitics_active and logistics_active:
            relationship_intelligence.append(
                {
                    "link": "geopolitics<->trade",
                    "confidence": "high",
                    "insight": "Geopolitical signal intensity intersects with mapped corridors and likely trade-route exposure.",
                }
            )
        if logistics_active and (economic_active or country.get("influence_index", 0) >= 65):
            relationship_intelligence.append(
                {
                    "link": "logistics<->growth",
                    "confidence": "moderate",
                    "insight": "Mobility and infrastructure posture remains a direct growth-side driver for this country node.",
                }
            )
        if not relationship_intelligence:
            relationship_intelligence.append(
                {
                    "link": "cross-domain",
                    "confidence": "low",
                    "insight": "Cross-domain linkage signals are currently weak; continue monitoring for convergence.",
                }
            )
        research_brief = " ".join(research_brief_parts)

        search_highlights = [item.get("title") for item in search_briefs.get("results", [])[:3] if item.get("title")]
        prompt_context = "\n".join(f"- {title}" for title in search_highlights) if search_highlights else "- No live web search highlights available"

        def _metric_value(key: str) -> float | None:
            metric = world_bank.get(key, {}) if isinstance(world_bank, dict) else {}
            value = metric.get("value") if isinstance(metric, dict) else None
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        inflation_value = _metric_value("inflation_consumer")
        debt_value = _metric_value("debt_to_gdp")
        gdp_value = _metric_value("gdp_current_usd")
        population_value = _metric_value("population_total")

        macro_indicators = [
            {
                "id": "stability_index",
                "label": "Stability",
                "value": max(0, min(100, 100 - float(country.get("risk_index", 50)))),
                "unit": "index",
                "status": "strong" if country.get("risk_index", 50) < 45 else "watch" if country.get("risk_index", 50) < 70 else "stress",
            },
            {
                "id": "economic_influence",
                "label": "Economic Influence",
                "value": float(country.get("influence_index", 0)),
                "unit": "index",
                "status": "strong" if country.get("influence_index", 0) >= 70 else "watch",
            },
            {
                "id": "inflation_consumer",
                "label": "Inflation (CPI)",
                "value": inflation_value,
                "unit": "%",
                "status": "strong" if inflation_value is not None and inflation_value < 4 else "watch" if inflation_value is not None and inflation_value < 7 else "stress",
            },
            {
                "id": "debt_to_gdp",
                "label": "Debt-to-GDP",
                "value": debt_value,
                "unit": "%",
                "status": "strong" if debt_value is not None and debt_value < 55 else "watch" if debt_value is not None and debt_value < 85 else "stress",
            },
            {
                "id": "population_total",
                "label": "Population",
                "value": population_value,
                "unit": "people",
                "status": "info",
            },
            {
                "id": "gdp_current_usd",
                "label": "GDP (current USD)",
                "value": gdp_value,
                "unit": "usd",
                "status": "info",
            },
        ]

        stability_vector = [
            {
                "label": "Stability",
                "score": max(0, min(100, 100 - float(country.get("risk_index", 50)))),
            },
            {
                "label": "Economic Condition",
                "score": max(0, min(100, float(country.get("influence_index", 0)))),
            },
            {
                "label": "Debt Posture",
                "score": 50 if debt_value is None else max(0, min(100, 100 - debt_value)),
            },
            {
                "label": "Signal Pressure",
                "score": max(0, min(100, 100 - min(float(country.get("active_signals", 0)) * 8, 100))),
            },
        ]

        return {
            "country": country,
            "summary": summary,
            "research_brief": research_brief,
            "evidence_points": evidence_points,
            "source_status": source_status,
            "provenance": {
                **self._source_provenance_summary(),
                "country_id": country_id,
                "analysis_mode": "seeded_context_plus_live_enrichment",
                "runtime_signal_count": len(runtime_signals),
                "seeded_signal_count": len(seeded_signals),
                "live_source_labels": [item["label"] for item in source_status if item["status"] == "live"],
                "limited_source_labels": [item["label"] for item in source_status if item["status"] == "limited"],
                "unavailable_source_labels": [item["label"] for item in source_status if item["status"] == "unavailable"],
            },
            "risk_factors": risk_factors,
            "opportunities": opportunities,
            "signals": signals,
            "assets": assets,
            "corridors": corridors,
            "feeds": related_feeds,
            "search_briefs": search_briefs,
            "search_provider_status": search_providers,
            "weather": weather,
            "world_bank": world_bank,
            "economic_snapshot": {
                "market_quotes": market_quotes,
                "world_bank_available": world_bank_live,
            },
            "macro_indicators": macro_indicators,
            "stability_vector": stability_vector,
            "relationship_intelligence": relationship_intelligence,
            "suggested_questions": [
                f"What are the main escalation pathways for {country['name']} over the next 14 days?",
                f"How do climate and infrastructure stress interact in {country['name']}?",
                f"Which trade and mobility chokepoints matter most for {country['name']}?",
            ],
            "ai_prompt": (
                f"Provide a strategic intelligence brief for {country['name']} covering conflict, climate, infrastructure, cyber, and economic posture. "
                f"Use the following live search highlights for context:\n{prompt_context}"
            ),
        }

    def get_alerts(self) -> List[Dict[str, Any]]:
        alerts = []
        for signal in self.get_dynamic_signals():
            if signal.get("severity") not in {"High", "Medium"}:
                continue
            alerts.append(
                {
                    "id": signal.get("id"),
                    "source": signal.get("source", "Runtime"),
                    "category": signal.get("category", "Signal"),
                    "text": signal.get("title", ""),
                    "urgency": signal.get("severity", "Medium"),
                    "time": signal.get("time", "LIVE"),
                }
            )
        return alerts[:16]

    def get_all_signals(self) -> List[Dict[str, Any]]:
        """Returns all signals (runtime + seeded) - used by agent orchestrator."""
        return self.get_dynamic_signals(include_seeded=True)

    def get_corridors(self) -> List[Dict[str, Any]]:
        """Returns all corridors (runtime + seeded) - used by agent orchestrator."""
        return self.get_global_corridors(include_seeded=True)

    async def _capture_source(
        self,
        *,
        source_id: str,
        label: str,
        mode: str,
        fetcher: Callable[[], Dict[str, Any]],
        signal_builder: Callable[[Dict[str, Any]], List[Dict[str, Any]]] | None = None,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        try:
            payload = await asyncio.to_thread(fetcher)
            signals = signal_builder(payload) if signal_builder else []
            status = payload.get("status", "live")
            if status in {"missing_key", "missing_resource_ids"}:
                status = "fallback"
            return signals, {
                "id": source_id,
                "label": label,
                "mode": mode,
                "status": status,
                "item_count": len(signals) if signals else len(payload.get("quotes", []) or payload.get("datasets", []) or payload.get("recent_events", []) or payload.get("hotspots", []) or payload.get("recent_significant", [])),
                "message": payload.get("message", payload.get("source", label)),
                "last_updated": datetime.utcnow().isoformat(),
                "strategy": payload.get("strategy"),
            }
        except Exception as e:
            logger.warning(f"Source capture failed for {label}: {e}")
            return [], {
                "id": source_id,
                "label": label,
                "mode": mode,
                "status": "error",
                "item_count": 0,
                "message": str(e),
                "last_updated": datetime.utcnow().isoformat(),
            }

    async def refresh_once(self):
        named_countries = {country["name"]: country["id"] for country in self.get_enriched_countries()}

        def gdelt_builder(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
            signals = []
            for item in payload.get("recent_events", [])[:8]:
                lat = item.get("lat")
                lng = item.get("lng")
                signals.append(
                    {
                        "id": f"dyn-{item['id']}",
                        "country_id": self._nearest_country_id(lat, lng),
                        "title": item.get("title", "Global event"),
                        "summary": f"{item.get('source', 'GDELT')} reported a live geopolitical event.",
                        "category": "Geopolitics",
                        "layer": "conflict",
                        "severity": "High" if "war" in item.get("title", "").lower() or "attack" in item.get("title", "").lower() or "disruption" in item.get("title", "").lower() else "Medium",
                        "source": item.get("source", "GDELT"),
                        "time": item.get("date", "LIVE"),
                        "lat": lat,
                        "lng": lng,
                    }
                )
            return signals

        def quake_builder(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
            signals = []
            for item in payload.get("recent_significant", [])[:5]:
                lat = item.get("lat")
                lng = item.get("lng")
                signals.append(
                    {
                        "id": f"quake-{item.get('id')}",
                        "country_id": self._nearest_country_id(lat, lng),
                        "title": f"M{item.get('magnitude')} seismic event",
                        "summary": item.get("location", "Seismic activity"),
                        "category": "Climate",
                        "layer": "climate",
                        "severity": "High" if (item.get("magnitude") or 0) >= 6 else "Medium",
                        "source": "USGS",
                        "time": "LIVE",
                        "lat": lat,
                        "lng": lng,
                    }
                )
            return signals

        def fire_builder(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
            signals = []
            for item in payload.get("hotspots", [])[:6]:
                lat = item.get("lat")
                lng = item.get("lng")
                signals.append(
                    {
                        "id": f"fire-{item.get('id')}",
                        "country_id": self._nearest_country_id(lat, lng),
                        "title": item.get("title", "Wildfire hotspot"),
                        "summary": "NASA wildfire event detected in open-event feed.",
                        "category": "Climate",
                        "layer": "climate",
                        "severity": "Medium",
                        "source": "NASA EONET",
                        "time": "LIVE",
                        "lat": lat,
                        "lng": lng,
                    }
                )
            return signals

        def world_bank_builder(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
            signals = []
            for code, country_data in payload.get("countries", {}).items():
                inflation = country_data.get("inflation_consumer", {}).get("value")
                country_id = f"CTR-{code}"
                country = self.get_country(country_id)
                if inflation is None or not country:
                    continue
                signals.append(
                    {
                        "id": f"wb-{code}",
                        "country_id": country_id,
                        "title": f"{code} inflation at {round(float(inflation), 2)}%",
                        "summary": "World Bank macro snapshot refreshed.",
                        "category": "Economics",
                        "layer": "economics",
                        "severity": "Medium" if float(inflation) >= 5 else "Low",
                        "source": "World Bank",
                        "time": country_data.get("inflation_consumer", {}).get("date", "LIVE"),
                        "lat": country["lat"],
                        "lng": country["lng"],
                    }
                )
            return signals

        def eia_builder(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
            brent = payload.get("series", {}).get("brent", {}).get("value")
            if brent is None:
                return []
            return [
                {
                    "id": "eia-brent",
                    "country_id": "CTR-SAU",
                    "title": f"Brent crude at {brent}",
                    "summary": "EIA energy pricing refresh.",
                    "category": "Economics",
                    "layer": "economics",
                    "severity": "High" if float(brent) >= 90 else "Medium",
                    "source": "EIA",
                    "time": payload.get("series", {}).get("brent", {}).get("period", "LIVE"),
                    "lat": 24.7136,
                    "lng": 46.6753,
                }
            ]

        def datagov_builder(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
            datasets = payload.get("datasets", [])
            if not datasets:
                return []
            return [
                {
                    "id": f"datagov-{index}",
                    "country_id": "CTR-IND",
                    "title": dataset.get("title", f"India dataset {index + 1}"),
                    "summary": f"data.gov.in dataset refreshed with {dataset.get('record_count', 0)} sampled records.",
                    "category": "Governance",
                    "layer": "governance",
                    "severity": "Low",
                    "source": "data.gov.in",
                    "time": "LIVE",
                    "lat": 28.6139,
                    "lng": 77.209,
                }
                for index, dataset in enumerate(datasets[:3])
            ]

        def opensky_builder(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
            signals = []
            for index, flight in enumerate(payload.get("sample_flights", [])[:8]):
                country_name = flight.get("country")
                country_id = named_countries.get(country_name) or self._nearest_country_id(flight.get("lat"), flight.get("lng"))
                signals.append(
                    {
                        "id": f"opensky-{index}",
                        "country_id": country_id,
                        "title": f"Aviation activity: {flight.get('callsign') or 'UNKNOWN'}",
                        "summary": f"OpenSky aircraft state linked to {country_name or 'global airspace'}.",
                        "category": "Aviation",
                        "layer": "mobility",
                        "severity": "Low",
                        "source": "OpenSky",
                        "time": "LIVE",
                        "lat": flight.get("lat"),
                        "lng": flight.get("lng"),
                    }
                )
            return signals

        def cisa_builder(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
            hubs = [
                ("CTR-USA", 39.0438, -77.4874),
                ("CTR-IND", 17.385, 78.4867),
                ("CTR-DEU", 50.1109, 8.6821),
            ]
            signals = []
            for index, vuln in enumerate(payload.get("vulnerabilities", [])[:3]):
                country_id, lat, lng = hubs[index % len(hubs)]
                signals.append(
                    {
                        "id": f"cisa-{vuln.get('cve')}",
                        "country_id": country_id,
                        "title": f"CISA KEV: {vuln.get('cve')} on {vuln.get('product')}",
                        "summary": vuln.get("description") or "Known exploited vulnerability catalog update.",
                        "category": "Cyber",
                        "layer": "cyber",
                        "severity": "High",
                        "source": "CISA KEV",
                        "time": vuln.get("added", "LIVE"),
                        "lat": lat,
                        "lng": lng,
                    }
                )
            return signals

        def search_builder(payload: Dict[str, Any], source_label: str) -> List[Dict[str, Any]]:
            signals: List[Dict[str, Any]] = []
            for index, item in enumerate(payload.get("results", [])[:4]):
                title = item.get("title")
                if not title:
                    continue
                signals.append(
                    {
                        "id": f"{source_label.lower()}-{index}-{abs(hash(title)) % 100000}",
                        "country_id": "CTR-IND",
                        "title": f"{source_label}: {title[:90]}",
                        "summary": f"Open search signal captured from {source_label}.",
                        "category": "Geopolitics",
                        "layer": "conflict",
                        "severity": "Medium",
                        "source": source_label,
                        "time": "LIVE",
                        "lat": 28.6139,
                        "lng": 77.209,
                    }
                )
            return signals

        country_task = asyncio.to_thread(osint_engine.get_country_catalog)
        market_task = asyncio.to_thread(osint_engine.get_market_snapshot)
        captures = await asyncio.gather(
            self._capture_source(source_id="gdelt", label="GDELT", mode="free", fetcher=osint_engine.get_gdelt_data, signal_builder=gdelt_builder),
            self._capture_source(source_id="usgs", label="USGS", mode="free", fetcher=osint_engine.get_usgs_earthquakes, signal_builder=quake_builder),
            self._capture_source(source_id="nasa", label="NASA EONET", mode="free", fetcher=osint_engine.get_nasa_firms, signal_builder=fire_builder),
            self._capture_source(source_id="fred", label="FRED", mode="free", fetcher=osint_engine.get_fred_economic_data),
            self._capture_source(source_id="worldbank", label="World Bank", mode="free", fetcher=osint_engine.get_world_bank_snapshot, signal_builder=world_bank_builder),
            self._capture_source(source_id="eia", label="EIA", mode="free", fetcher=osint_engine.get_eia_energy_data, signal_builder=eia_builder),
            self._capture_source(source_id="datagov", label="data.gov.in", mode="free", fetcher=osint_engine.get_data_gov_snapshot, signal_builder=datagov_builder),
            self._capture_source(source_id="opensky", label="OpenSky", mode="free", fetcher=osint_engine.get_opensky_data, signal_builder=opensky_builder),
            self._capture_source(source_id="cisa", label="CISA KEV", mode="free", fetcher=osint_engine.get_cisa_kev_data, signal_builder=cisa_builder),
            self._capture_source(source_id="reddit", label="Reddit", mode="free", fetcher=osint_engine.get_reddit_discourse),
            self._capture_source(source_id="mastodon", label="Mastodon", mode="free", fetcher=osint_engine.get_mastodon_public),
            self._capture_source(
                source_id="yahoo-search",
                label="Yahoo Search",
                mode="free",
                fetcher=osint_engine.get_yahoo_search_results,
                signal_builder=lambda payload: search_builder(payload, "Yahoo Search"),
            ),
            self._capture_source(
                source_id="duckduckgo-search",
                label="DuckDuckGo Search",
                mode="free",
                fetcher=osint_engine.get_duckduckgo_search_results,
                signal_builder=lambda payload: search_builder(payload, "DuckDuckGo"),
            ),
            self._capture_source(
                source_id="serpapi-search",
                label="SerpAPI Search",
                mode="free",
                fetcher=osint_engine.get_serpapi_search_results,
                signal_builder=lambda payload: search_builder(payload, "SerpAPI"),
            ),
        )
        country_payload, market_payload = await asyncio.gather(country_task, market_task)

        dynamic_signals: List[Dict[str, Any]] = []
        source_health: List[Dict[str, Any]] = []
        for signals, health in captures:
            dynamic_signals.extend(signals)
            source_health.append(health)

        source_health.append(
            {
                "id": "country-catalog",
                "label": "REST Countries",
                "mode": "free",
                "status": country_payload.get("status", "fallback"),
                "item_count": len(country_payload.get("countries", [])),
                "message": country_payload.get("source", "REST Countries"),
                "last_updated": datetime.utcnow().isoformat(),
            }
        )
        source_health.append(
            {
                "id": "markets",
                "label": "Finnhub Market Pulse",
                "mode": "free",
                "status": "live" if market_payload.get("status") == "live" else "fallback",
                "item_count": len(market_payload.get("quotes", [])),
                "message": market_payload.get("source", "Finnhub"),
                "last_updated": datetime.utcnow().isoformat(),
            }
        )

        deduped_signals: List[Dict[str, Any]] = []
        seen_ids = set()
        for signal in dynamic_signals:
            signal_id = signal.get("id")
            if not signal_id or signal_id in seen_ids:
                continue
            seen_ids.add(signal_id)
            deduped_signals.append(signal)

        self._state = {
            "dynamic_signals": deduped_signals[:260],
            "source_health": source_health,
            "market_snapshot": market_payload.get("quotes", []),
            "country_catalog": country_payload.get("countries", []) or self._state.get("country_catalog", []),
            "last_refresh": datetime.utcnow().isoformat(),
        }
        self._persist_state()

        # Keep this lightweight: warm search caches asynchronously for top-risk countries.
        if not self._warm_task or self._warm_task.done():
            self._warm_task = asyncio.create_task(self._warm_country_search_cache_async())

    async def _loop(self):
        while self._running:
            try:
                await self.refresh_once()
            except Exception as e:
                logger.error(f"Runtime refresh loop failed: {e}")
            await asyncio.sleep(REFRESH_INTERVAL_SECONDS)

    def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        if self._warm_task and not self._warm_task.done():
            self._warm_task.cancel()


runtime_engine = RuntimeIntelligenceEngine()
