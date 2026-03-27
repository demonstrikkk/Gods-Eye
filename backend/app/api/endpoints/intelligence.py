from fastapi import APIRouter, Request
import logging
import asyncio
from pydantic import BaseModel
from typing import Dict, Any, List
from app.data.store import store
from app.core.rate_limit import limiter

logger = logging.getLogger("intelligence_api")
router = APIRouter()


def _publish_battleground_map_commands(simulation: Dict[str, Any], country_a: str, country_b: str) -> List[str]:
    """Publish battleground simulation overlays as centralized map commands."""
    from app.services.map_command_service import get_map_command_service

    service = get_map_command_service()
    source = "strategic_battleground_agent"
    service.clear_commands(source=source)

    command_ids: List[str] = []

    # Always keep country actors highlighted and add a conflict route for context.
    highlight = service.create_highlight_command(
        country_ids=[country_a, country_b],
        color="#ef4444",
        pulse=True,
        description="Battleground simulation actors",
        source=source,
        priority="high",
        metadata={"mode": "battleground", "actors": [country_a, country_b]},
    )
    command_ids.append(highlight.id)

    route = service.create_route_command(
        from_country=country_a,
        to_country=country_b,
        route_type="conflict_front",
        color="#dc2626",
        weight=4,
        description="Simulated front line",
        source=source,
        priority="high",
        metadata={"mode": "battleground", "actors": [country_a, country_b]},
    )
    command_ids.append(route.id)

    # Convert battleground layers to overlay + marker commands for map rendering.
    map_layers = simulation.get("map_visualization", [])
    points: List[Dict[str, Any]] = []

    for layer in map_layers:
        layer_type = str(layer.get("type", ""))
        layer_data = layer.get("data")

        if layer_type == "force_deployment" and isinstance(layer_data, list):
            for entry in layer_data:
                try:
                    lat = float(entry.get("lat"))
                    lng = float(entry.get("lng"))
                except (TypeError, ValueError):
                    continue

                country_id = str(entry.get("country_id") or "")
                marker = service.create_marker_command(
                    lat=lat,
                    lng=lng,
                    marker_type="force_deployment",
                    label=f"{country_id} deployment",
                    color="#f59e0b",
                    description="Simulated force deployment",
                    source=source,
                    priority="high",
                    metadata={"mode": "battleground", "country_id": country_id, "force_type": entry.get("type")},
                )
                command_ids.append(marker.id)

                points.append(
                    {
                        "lat": lat,
                        "lng": lng,
                        "country_id": country_id,
                        "label": f"{country_id} deployment",
                        "impact": 0.7,
                    }
                )

        if layer_type == "conflict_zone" and isinstance(layer_data, dict):
            center = layer_data.get("center")
            if isinstance(center, (list, tuple)) and len(center) == 2:
                try:
                    lat = float(center[0])
                    lng = float(center[1])
                    points.append(
                        {
                            "lat": lat,
                            "lng": lng,
                            "label": "Conflict zone",
                            "impact": 0.9,
                        }
                    )
                except (TypeError, ValueError):
                    pass

    if points:
        overlay = service.create_overlay_command(
            overlay_type="scenario_impact_zones",
            overlay_data={
                "title": "Battleground conflict zones",
                "points": points,
            },
            description="Battleground impact zones",
            source=source,
            priority="high",
            metadata={"mode": "battleground", "actors": [country_a, country_b]},
        )
        command_ids.append(overlay.id)

    focus = service.create_focus_command(
        country_id=country_a,
        zoom_level=5,
        duration_ms=1200,
        description="Battleground simulation focus",
        source=source,
        priority="high",
        metadata={"mode": "battleground", "actors": [country_a, country_b]},
    )
    command_ids.append(focus.id)

    return command_ids


@router.get("/dashboard/executive", response_model=Dict[str, Any])
async def get_executive_kpis():
    """
    Retrieves aggregated top-level KPIs from the in-memory civic data store.
    """
    kpis = store.get_executive_kpis()
    return {"status": "success", "kpis": kpis}


class NLQueryRequest(BaseModel):
    query: str = ""
    question: str = ""


@router.post("/query", response_model=Dict[str, Any])
@limiter.limit("24/minute")
async def execute_natural_language_query(request: Request, payload: NLQueryRequest):
    """
    Processes natural language queries against the demo data stores.
    Attempts real AI reasoning via qa_engine, with deterministic fallbacks.
    """
    from app.services.osint_aggregator import qa_engine
    from app.services.map_command_service import get_map_command_service

    try:
        query_text = (payload.query or payload.question or "").strip()
        query = query_text.lower()

        if len(query.split()) > 3:
            try:
                # Keep the endpoint responsive even when deeper QA tooling is slow.
                result = await asyncio.wait_for(
                    asyncio.to_thread(qa_engine.execute_query, query_text),
                    timeout=8.0,
                )
                if isinstance(result, dict) and "answer" in result:
                    return {"status": "success", "answer": result["answer"]}
            except asyncio.TimeoutError:
                logger.warning("QA engine timeout; falling back to deterministic responder")
            except Exception as ai_err:
                logger.warning(f"QA engine unavailable; falling back: {ai_err}")
        if "sentiment" in query and "negative" in query:
            booths = store.get_booths()
            critical = [booth for booth in booths if booth["avg_sentiment"] < 40]
            if critical:
                lines = [f"Found {len(critical)} booths with negative sentiment:"]
                for booth in critical[:5]:
                    lines.append(
                        f"- {booth['name']} ({booth['constituency_name']}): Sentiment {booth['avg_sentiment']}%, "
                        f"Top Issue: {booth['top_issues'][0]['issue'] if booth['top_issues'] else 'N/A'}"
                    )
                return {"status": "success", "answer": "\n".join(lines)}

        if "water" in query:
            complaints = store.get_complaints(limit=200)
            water_complaints = [complaint for complaint in complaints if "water" in complaint["text"].lower()]
            lines = [f"Found {len(water_complaints)} water-related complaints across all booths:"]
            booth_counts: Dict[str, int] = {}
            for complaint in water_complaints:
                booth_counts[complaint["booth_id"]] = booth_counts.get(complaint["booth_id"], 0) + 1
            for booth_id, count in sorted(booth_counts.items(), key=lambda item: item[1], reverse=True)[:5]:
                booth = store.get_booth(booth_id)
                lines.append(f"- {booth['name'] if booth else booth_id}: {count} complaints")
            return {"status": "success", "answer": "\n".join(lines)}

        if "worker" in query or "field" in query:
            workers = store.get_workers()
            online = [worker for worker in workers if worker["status"] == "Online"]
            lines = [
                f"Total Workers: {len(workers)}",
                f"Currently Online: {len(online)}",
                f"Average Performance: {round(sum(worker['performance_score'] for worker in workers) / len(workers), 1)}%",
            ]
            return {"status": "success", "answer": "\n".join(lines)}

        if "scheme" in query or "beneficiar" in query:
            stats = store.get_stats()
            schemes = store.get_schemes()
            lines = ["Government Scheme Coverage Analysis:"]
            for scheme in schemes:
                lines.append(
                    f"- {scheme['name']} ({scheme['ministry']}): "
                    f"Target = {scheme['target_segment']}, Benefit = {scheme['benefit']}"
                )
            lines.append(f"\nOverall coverage: {stats.get('total_citizens', 0):,} citizens tracked")
            return {"status": "success", "answer": "\n".join(lines)}

        if "segment" in query or "youth" in query or "farmer" in query:
            constituencies = store.get_constituencies()
            lines = ["Voter Segmentation Summary:"]
            for constituency in constituencies:
                segments = store.get_constituency_segments(constituency["id"])
                total = sum(segments.values())
                seg_str = ", ".join(
                    f"{key}: {round(value / total * 100)}%"
                    for key, value in sorted(segments.items(), key=lambda item: item[1], reverse=True)[:3]
                )
                lines.append(f"- {constituency['name']}: {seg_str}")
            return {"status": "success", "answer": "\n".join(lines)}

        from app.services.runtime_intelligence import runtime_engine
        for country in runtime_engine.get_enriched_countries():
            country_name = country["name"].lower()
            if country_name in query and any(keyword in query for keyword in ["country", "analy", "brief", "risk", "global", "world", "situation"]):
                analysis = runtime_engine.get_country_analysis(country["id"])
                if analysis:
                    command_service = get_map_command_service()
                    command_service.create_highlight_command(
                        country_ids=[country["id"]],
                        color="#06b6d4",
                        pulse=True,
                        description=f"AI query focus: {country['name']}",
                        source="nl_query_engine",
                        priority="high",
                        metadata={"mode": "query", "country_id": country["id"]},
                    )
                    command_service.create_focus_command(
                        country_id=country["id"],
                        zoom_level=4,
                        duration_ms=1000,
                        description=f"Focus on {country['name']}",
                        source="nl_query_engine",
                        priority="high",
                        metadata={"mode": "query", "country_id": country["id"]},
                    )

                    lines = [
                        f"{country['name']} Intelligence Brief:",
                        analysis["summary"],
                        "Top risk factors:",
                    ]
                    for factor in analysis["risk_factors"][:3]:
                        lines.append(f"- {factor['factor']} ({factor['severity']}): {factor['description']}")
                    if analysis["signals"]:
                        lines.append("Live signals:")
                        for signal in analysis["signals"][:3]:
                            lines.append(f"- {signal['title']} [{signal['category']}]")
                    search_hits = analysis.get("search_briefs", {}).get("results", [])
                    if search_hits:
                        lines.append("Live web search context:")
                        for item in search_hits[:3]:
                            lines.append(f"- {item.get('title')} ({item.get('source')})")
                    return {"status": "success", "answer": "\n".join(lines)}

        if any(keyword in query for keyword in ["country", "countries", "global", "world", "ontology"]):
            overview = store.get_global_overview()
            countries = sorted(runtime_engine.get_enriched_countries(), key=lambda country: country["risk_index"], reverse=True)
            lines = [
                "Global Ontology Overview:",
                f"- {len(countries)} countries indexed",
                f"- {runtime_engine.get_global_overview()['total_signals']} active intelligence signals",
                f"- Systemic stress score: {runtime_engine.get_global_overview()['systemic_stress']}",
                "Priority watchlist:",
            ]
            for country in countries[:5]:
                lines.append(
                    f"- {country['name']} ({country['region']}): risk {country['risk_index']}, "
                    f"influence {country['influence_index']}, pressure = {country['pressure']}"
                )
            return {"status": "success", "answer": "\n".join(lines)}

        stats = store.get_stats()
        global_stats = store.get_global_overview()
        return {
            "status": "success",
            "answer": (
                "Gods-Eye OS Intelligence Summary:\n"
                f"- {stats['total_constituencies']} constituencies monitored\n"
                f"- {global_stats['total_countries']} countries indexed in the global ontology\n"
                f"- {stats['total_booths']} booths with {stats['total_citizens']:,} citizens profiled\n"
                f"- {stats['total_workers']} field workers deployed\n"
                f"- National sentiment: {stats['national_avg_sentiment']}%\n"
                f"- {stats['total_complaints']:,} citizen complaints tracked\n\n"
                "Try asking: 'Show countries under highest risk' or 'Show booths with negative sentiment'"
            ),
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

class StrategicQueryRequest(BaseModel):
    query: str


class WhatIfRequest(BaseModel):
    original_context: str
    whatif_query: str
    variables: Dict[str, Any] = {}


@router.post("/strategic-analysis", response_model=Dict[str, Any])
async def execute_strategic_analysis(request: StrategicQueryRequest):
    """
    Agentic Strategic Intelligence Engine.
    Takes a complex query, plans tool execution, gathers multi-source data,
    and produces structured strategic analysis with scenarios.
    """
    from app.services.strategic_agent import run_strategic_analysis

    try:
        analysis = await run_strategic_analysis(request.query)
        return {"status": "success", "data": analysis}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/scenario-simulate", response_model=Dict[str, Any])
async def execute_scenario_simulation(request: WhatIfRequest):
    """
    What-If Scenario Simulation Engine.
    Takes an original analysis context and a modified scenario query,
    then recomputes strategic outcomes with adjusted variables.
    """
    from app.services.strategic_agent import run_whatif_simulation

    try:
        result = await run_whatif_simulation(
            original_context=request.original_context,
            whatif_query=request.whatif_query,
            variables=request.variables,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
class ExpertAnalysisRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}
    force_agents: list = []


@router.post("/expert-analysis", response_model=Dict[str, Any])
async def execute_expert_analysis(request: ExpertAnalysisRequest):
    """
    Expert-Level Multi-Agent Strategic Intelligence Engine.

    This endpoint provides:
    - Multi-agent expert reasoning
    - Evidence-based citations
    - Uncertainty quantification
    - Cross-agent validation
    - Internal debate mechanism
    - Consensus/disagreement documentation

    Returns:
    - consensus_view: Agreed-upon assessment
    - disagreements: Areas where agents disagree
    - confidence_level: Overall confidence with score
    - data_sources_cited: Evidence chain
    - probabilistic_scenarios: Monte Carlo projections
    """
    from app.services.expert_strategic_agent import run_expert_strategic_analysis

    try:
        analysis = await run_expert_strategic_analysis(
            query=request.query,
            context=request.context,
        )
        return {"status": "success", "data": analysis}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/expert-agents", response_model=Dict[str, Any])
async def get_available_expert_agents():
    """
    Returns list of available expert agents and their capabilities.
    """
    from app.agents.agent_orchestrator import expert_orchestrator

    try:
        agents = expert_orchestrator.get_available_agents()
        return {"status": "success", "agents": agents}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
class CounterQuestionRequest(BaseModel):
    expert_assessment: Dict[str, Any]
    context: Dict[str, Any] = {}


@router.post("/counter-question", response_model=Dict[str, Any])
async def execute_counter_questioning(request: CounterQuestionRequest):
    """
    Counter-Questioning / Red Team Analysis

    Adversarially tests expert analysis by:
    - Challenging assumptions
    - Identifying evidence gaps
    - Generating critical counter-questions
    - Proposing alternative explanations
    - Assessing confidence calibration

    This acts as a "red team" that tries to poke holes in the analysis.

    Returns:
    - counter_questions: List of critical questions
    - assumption_challenges: Assumptions that may be flawed
    - evidence_gaps: Missing data or perspectives
    - alternative_interpretations: Other ways to interpret the data
    - confidence_adjustment: Recommended confidence level change
    - red_team_summary: Executive summary of red team findings
    """
    from app.services.counter_questioning import counter_questioning_agent

    try:
        counter_analysis = counter_questioning_agent.analyze(
            expert_assessment=request.expert_assessment,
            context=request.context,
        )
        return {"status": "success", "data": counter_analysis.to_dict()}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/news-insight", response_model=Dict[str, Any])
@limiter.limit("12/minute")
async def get_news_insight(request: Request, payload: StrategicQueryRequest):
    """
    AI-driven news extraction and summarization.
    Specifically parses the current news feed storage to provide gists and reasoning.
    """
    from app.services.feed_aggregator import feed_engine
    from app.services.llm_provider import get_enterprise_llm

    feeds = feed_engine.get_feeds()
    if not feeds:
        return {"status": "success", "answer": "No news feeds available for analysis."}

    context = "\n".join([f"- [{feed['category']}] {feed['text']}" for feed in feeds[:15]])

    prompt = f"""You are the Gods-Eye OS News Analyst.
Targeted query: {payload.query}

Current news context:
{context}

Provide a detailed gist of relevant news items matching the query.
Include reasoning for why these items are significant.
Respond with a clear, professional intelligence summary."""

    try:
        llm = get_enterprise_llm(temperature=0.3)
        res = llm.invoke(prompt)
        return {"status": "success", "answer": res.content}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ═══════════════════════════════════════════════════════════════════════════════
# VIRTUAL BATTLEGROUND ENDPOINTS
# Strategic simulation and military comparison APIs
# ═══════════════════════════════════════════════════════════════════════════════

class MilitaryComparisonRequest(BaseModel):
    country_a: str
    country_b: str
    include_allies: bool = False


class ConflictSimulationRequest(BaseModel):
    country_a: str
    country_b: str
    scenario_type: str = "conventional"
    duration_days: int = 30


@router.get("/battleground/military-strength/{country_id}", response_model=Dict[str, Any])
async def get_military_strength(country_id: str):
    """
    Get military strength data for a specific country.

    Returns force composition, rankings, and capability indices.
    """
    from app.services.battleground_engine import battleground_engine

    try:
        strength = battleground_engine.get_military_strength(country_id)
        return {"status": "success", "data": strength}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/battleground/compare-forces", response_model=Dict[str, Any])
async def compare_military_forces(request: MilitaryComparisonRequest):
    """
    Compare military forces between two countries.

    Provides:
    - Force composition comparison
    - Power ratio analysis
    - Alliance network (if include_allies=True)
    - Advantage assessment
    """
    from app.services.battleground_engine import battleground_engine

    try:
        comparison = battleground_engine.compare_forces(
            country_a=request.country_a,
            country_b=request.country_b,
            include_allies=request.include_allies,
        )
        return {"status": "success", "data": comparison}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/battleground/alliance-network", response_model=Dict[str, Any])
async def get_alliance_network():
    """
    Get the full global alliance/adversary network graph.

    Returns nodes (countries) and edges (relationships) for visualization.
    """
    from app.services.battleground_engine import battleground_engine

    try:
        network = battleground_engine.get_alliance_network()
        return {"status": "success", "data": network}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/battleground/simulate-conflict", response_model=Dict[str, Any])
async def simulate_conflict(request: ConflictSimulationRequest):
    """
    Simulate a conflict scenario between two countries.

    Returns:
    - Force comparison
    - Outcome probabilities
    - Projected timeline
    - Economic/humanitarian impacts
    - Map visualization layers
    - Strategic warnings
    """
    from app.services.battleground_engine import battleground_engine

    try:
        simulation = battleground_engine.simulate_conflict(
            country_a=request.country_a,
            country_b=request.country_b,
            scenario_type=request.scenario_type,
            duration_days=request.duration_days,
        )

        map_command_ids = _publish_battleground_map_commands(
            simulation,
            request.country_a,
            request.country_b,
        )
        simulation.setdefault("_meta", {})
        simulation["_meta"]["map_command_ids"] = map_command_ids
        simulation["_meta"]["map_command_source"] = "strategic_battleground_agent"

        return {"status": "success", "data": simulation}
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=str(e))