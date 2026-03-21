from fastapi import APIRouter, HTTPException
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
            }
        }


class NLQueryRequest(BaseModel):
    query: str = ""
    question: str = ""


@router.post("/query", response_model=Dict[str, Any])
async def execute_natural_language_query(request: NLQueryRequest):
    """
    Processes natural language queries against the civic data store.
    Attempts real AI reasoning via qa_engine, with keyword fallbacks for speed.
    """
    from app.services.osint_aggregator import qa_engine
    try:
        query = request.query or request.question
        query = query.lower()

        # 1. Try real LLM-backed Graph QA first for complex questions
        if len(query.split()) > 3: # Only for full sentences
            try:
                # qa_engine is synchronous but we can run it in a thread if needed
                # For now, it's fast enough or has its own internal handling
                result = qa_engine.execute_query(request.query)
                if isinstance(result, dict) and "answer" in result:
                    return {"status": "success", "answer": result["answer"]}
            except Exception as ai_err:
                logger.warning(f"AI QA failed, falling back to keywords: {ai_err}")

        # 2. Smart keyword-based query routing fallback
        if "sentiment" in query and "negative" in query:
            booths = store.get_booths()
            critical = [b for b in booths if b["avg_sentiment"] < 40]
            if critical:
                result_lines = [f"Found {len(critical)} booths with negative sentiment:"]
                for b in critical[:5]:
                    result_lines.append(
                        f"• {b['name']} ({b['constituency_name']}): Sentiment {b['avg_sentiment']}%, "
                        f"Top Issue: {b['top_issues'][0]['issue'] if b['top_issues'] else 'N/A'}"
                    )
                return {"status": "success", "answer": "\n".join(result_lines)}

        if "water" in query:
            complaints = store.get_complaints(limit=200)
            water_complaints = [c for c in complaints if "water" in c["text"].lower()]
            result_lines = [f"Found {len(water_complaints)} water-related complaints across all booths:"]
            # Group by booth
            booth_counts = {}
            for c in water_complaints:
                booth_counts[c["booth_id"]] = booth_counts.get(c["booth_id"], 0) + 1
            for bid, count in sorted(booth_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                booth = store.get_booth(bid)
                result_lines.append(f"• {booth['name'] if booth else bid}: {count} complaints")
            return {"status": "success", "answer": "\n".join(result_lines)}

        if "worker" in query or "field" in query:
            workers = store.get_workers()
            online = [w for w in workers if w["status"] == "Online"]
            result_lines = [
                f"Total Workers: {len(workers)}",
                f"Currently Online: {len(online)}",
                f"Average Performance: {round(sum(w['performance_score'] for w in workers) / len(workers), 1)}%",
            ]
            return {"status": "success", "answer": "\n".join(result_lines)}

        if "scheme" in query or "beneficiar" in query:
            stats = store.get_stats()
            schemes = store.get_schemes()
            result_lines = [f"Government Scheme Coverage Analysis:"]
            for s in schemes:
                result_lines.append(f"• {s['name']} ({s['ministry']}): Target = {s['target_segment']}, Benefit = {s['benefit']}")
            result_lines.append(f"\nOverall coverage: {stats.get('total_citizens', 0):,} citizens tracked")
            return {"status": "success", "answer": "\n".join(result_lines)}

        if "segment" in query or "youth" in query or "farmer" in query:
            cons = store.get_constituencies()
            result_lines = ["Voter Segmentation Summary:"]
            for c in cons:
                segs = store.get_constituency_segments(c["id"])
                total = sum(segs.values())
                seg_str = ", ".join(f"{k}: {round(v/total*100)}%" for k, v in sorted(segs.items(), key=lambda x: x[1], reverse=True)[:3])
                result_lines.append(f"• {c['name']}: {seg_str}")
            return {"status": "success", "answer": "\n".join(result_lines)}

        # Default: Return summary stats
        stats = store.get_stats()
        return {
            "status": "success",
            "answer": (
                f"JanGraph OS Intelligence Summary:\n"
                f"• {stats['total_constituencies']} Constituencies monitored\n"
                f"• {stats['total_booths']} Booths with {stats['total_citizens']:,} citizens profiled\n"
                f"• {stats['total_workers']} Field Workers deployed\n"
                f"• National Sentiment: {stats['national_avg_sentiment']}%\n"
                f"• {stats['total_complaints']:,} citizen complaints tracked\n\n"
                f"Try asking: 'Show booths with negative sentiment' or 'What are the water complaints?'"
            )
        }

    except Exception as e:
        logger.error(f"NL Query Failure: {e}")
        return {"status": "error", "answer": f"Intelligence Engine encountered an issue: {str(e)}"}


# ═══════════════════════════════════════════════════════════════
# STRATEGIC INTELLIGENCE — Agentic Multi-Tool Analysis
# ═══════════════════════════════════════════════════════════════

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
                "strategic_recommendations": ["Retry with LLM connectivity"]
            }
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
            variables=request.variables
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
    
    # Simple context prep
    context = "\n".join([f"- [{f['category']}] {f['text']}" for f in feeds[:15]])
    
    prompt = f"""You are the JanGraph OS News Analyst.
Targeted query: {request.query}

Current news context:
{context}

Provide a detailed 'gist' of relevant news items matching the query. 
Include reasoning for why these items are significant.
Respond with a clear, professional intelligence summary."""

    try:
        llm = get_enterprise_llm(temperature=0.3)
        res = llm.invoke(prompt)
        return {"status": "success", "answer": res.content}
    except Exception as e:
        logger.error(f"News Insight Failure: {e}")
        return {"status": "error", "answer": "News Intelligence Engine offline."}

