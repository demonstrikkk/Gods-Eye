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
        self._state_path = Path(__file__).resolve().parent.parent / "data" / "runtime_state.json"
        self._state = self._load_state()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "dynamic_signals": [],
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

    def get_structural_assets(
        self,
        country_id: str | None = None,
        layer: str | None = None,
    ) -> List[Dict[str, Any]]:
        return store.get_global_assets(country_id=country_id, layer=layer)

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

    def _signal_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for signal in self.get_dynamic_signals():
            country_id = signal.get("country_id")
            if not country_id:
                continue
            counts[country_id] = counts.get(country_id, 0) + 1
        return counts

    def get_enriched_countries(self) -> List[Dict[str, Any]]:
        counts = self._signal_counts()
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
                    "asset_count": asset_count,
                    "capital": country.get("capital") or base.get("capital"),
                    "population": population,
                    "macro_region": country.get("macro_region") or country.get("region"),
                    "iso3": country.get("iso3") or country["id"].replace("CTR-", ""),
                }
            )
            countries.append(country)
        return sorted(countries, key=lambda item: (-item["risk_index"], item["name"]))

    def get_country(self, country_id: str) -> Dict[str, Any] | None:
        return next((country for country in self.get_enriched_countries() if country["id"] == country_id), None)

    def get_dynamic_signals(self) -> List[Dict[str, Any]]:
        base = store.get_global_signals()
        dynamic = self._state.get("dynamic_signals", [])
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
        overview["total_assets"] = len(self.get_structural_assets())
        overview["live_sources"] = len([item for item in self.get_source_health() if item.get("status") == "live"])
        overview["last_refresh"] = self._state.get("last_refresh")
        overview["market_tickers"] = len(self.get_market_snapshot())
        return overview

    def get_global_graph(self) -> Dict[str, Any]:
        graph = store.get_global_graph()
        nodes = list(graph["nodes"])
        links = list(graph["links"])
        for signal in self._state.get("dynamic_signals", [])[:24]:
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

        summary = (
            f"{country['name']} is in {country['stability'].lower()} posture with risk {country['risk_index']} "
            f"and influence {country['influence_index']}. Pressure centers on {country['pressure']}. "
            f"The system currently tracks {country['active_signals']} live signals and {country.get('asset_count', 0)} structural assets for this node."
        )

        return {
            "country": country,
            "summary": summary,
            "risk_factors": risk_factors,
            "opportunities": opportunities,
            "signals": signals,
            "assets": assets,
            "feeds": related_feeds,
            "weather": weather,
            "world_bank": world_bank,
            "suggested_questions": [
                f"What are the main escalation pathways for {country['name']} over the next 14 days?",
                f"How do climate and infrastructure stress interact in {country['name']}?",
                f"Which trade and mobility chokepoints matter most for {country['name']}?",
            ],
            "ai_prompt": f"Provide a strategic intelligence brief for {country['name']} covering conflict, climate, infrastructure, cyber, and economic posture.",
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


runtime_engine = RuntimeIntelligenceEngine()
