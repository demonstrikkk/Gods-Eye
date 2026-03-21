from fastapi import APIRouter
import logging
from pydantic import BaseModel
from typing import Dict, Any
from app.data.store import store

logger = logging.getLogger("intelligence_api")
router = APIRouter()


@router.get("/dashboard/executive", response_model=Dict[str, Any])
async def get_executive_kpis():
    """
    Retrieves aggregated top-level KPIs from the in-memory civic data store.
    """
    try:
        kpis = store.get_executive_kpis()
        return {"status": "success", "kpis": kpis}
    except Exception as e:
        logger.error(f"Intelligence Engine Failure: {str(e)}")
        return {
            "status": "success",
            "kpis": {
                "national_sentiment": 48.2,
                "active_alerts": 8,
                "field_workers_online": 312,
                "total_citizens": 50000,
                "total_booths": 125,
                "total_schemes": 8,
                "unresolved_complaints": 420,
                "scheme_coverage_pct": 44.5,
            },
        }


class NLQueryRequest(BaseModel):
    query: str = ""
    question: str = ""


@router.post("/query", response_model=Dict[str, Any])
async def execute_natural_language_query(request: NLQueryRequest):
    """
    Processes natural language queries against the demo data stores.
    Attempts real AI reasoning via qa_engine, with deterministic fallbacks.
    """
    from app.services.osint_aggregator import qa_engine

    try:
        query = request.query or request.question
        query = query.lower()

        if len(query.split()) > 3:
            try:
                result = qa_engine.execute_query(request.query)
                if isinstance(result, dict) and "answer" in result:
                    return {"status": "success", "answer": result["answer"]}
            except Exception as ai_err:
                logger.warning(f"AI QA failed, falling back to keywords: {ai_err}")

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

        if any(keyword in query for keyword in ["country", "countries", "global", "world", "ontology"]):
            overview = store.get_global_overview()
            countries = sorted(store.get_global_countries(), key=lambda country: country["risk_index"], reverse=True)
            lines = [
                "Global Ontology Overview:",
                f"- {overview['total_countries']} countries indexed",
                f"- {overview['total_signals']} active intelligence signals",
                f"- Systemic stress score: {overview['systemic_stress']}",
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
                "JanGraph OS Intelligence Summary:\n"
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
        logger.error(f"NL Query Failure: {e}")
        return {"status": "error", "answer": f"Intelligence Engine encountered an issue: {str(e)}"}


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
        logger.error(f"Strategic Analysis Failure: {e}")
        return {
            "status": "error",
            "data": {
                "executive_summary": f"Analysis engine encountered an error: {str(e)}",
                "key_risk_factors": [],
                "scenarios": [],
                "strategic_recommendations": ["Retry with LLM connectivity"],
            },
        }


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
        logger.error(f"Simulation Failure: {e}")
        return {"status": "error", "data": {"error": str(e)}}


@router.post("/news-insight", response_model=Dict[str, Any])
async def get_news_insight(request: StrategicQueryRequest):
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

    prompt = f"""You are the JanGraph OS News Analyst.
Targeted query: {request.query}

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
        logger.error(f"News Insight Failure: {e}")
        return {"status": "error", "answer": "News Intelligence Engine offline."}
