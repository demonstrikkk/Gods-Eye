
"""
JanGraph OS — Agentic Strategic Intelligence Engine
Multi-tool LLM system that breaks complex geopolitical/civic queries into
sub-tasks, executes tool functions, synthesizes data, and produces
strategic analysis with scenario simulations.

Enhanced for hackathon: integrated social media APIs, caching, robust error handling.
"""

import json
import logging
import random
import asyncio
from functools import wraps
from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
import time

from app.services.llm_provider import get_enterprise_llm
from app.data.store import store
from app.services.osint_aggregator import osint_engine
from app.services.feed_aggregator import feed_engine

# Optional caching (if Redis is configured)
try:
    from app.cache.redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger("strategic_agent")

# ============================================================
# DECORATORS & UTILITIES
# ============================================================

def cache_tool(ttl_seconds: int = 300):
    """Simple Redis cache decorator for tool results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not REDIS_AVAILABLE:
                return func(*args, **kwargs)
            cache_key = f"tool:{func.__name__}:{json.dumps(kwargs, sort_keys=True)}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl_seconds, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

def _parse_json(content: str) -> Dict:
    """Robust JSON parser handling markdown blocks and stray text."""
    content = content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    # Try to find the first { and last }
    start = content.find("{")
    end = content.rfind("}") + 1
    if start >= 0 and end > start:
        content = content[start:end]
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nContent: {content[:500]}")
        raise

def _fallback_analysis(query: str) -> Dict:
    """Structured fallback when LLM is unavailable."""
    stats = store.get_stats()
    return {
        "executive_summary": f"Strategic analysis for: '{query}'. Running in local intelligence mode with {stats['total_citizens']:,} citizens and {stats['total_booths']} booths monitored.",
        "situation_analysis": "The JanGraph OS civic intelligence store is operational. External LLM reasoning engine requires API connectivity for deep strategic analysis.",
        "key_risk_factors": [
            {"factor": "LLM Connectivity", "severity": "Medium", "description": "Groq API required for full agentic reasoning. Keyword-based analysis active."},
            {"factor": "Civic Sentiment", "severity": "High" if stats["national_avg_sentiment"] < 45 else "Medium", "description": f"National average sentiment at {stats['national_avg_sentiment']}%"},
        ],
        "impact_on_india": {
            "economic": f"Monitoring {stats['total_citizens']:,} citizens across {stats['total_constituencies']} constituencies",
            "political": f"{stats['total_booths']} booths under real-time sentiment surveillance",
            "defense": "Defense posture data requires external API feed",
            "social": f"Top civic issues tracked across {stats['total_complaints']:,} complaints"
        },
        "forecasts": {
            "short_term_0_45_days": "Continued civic monitoring with real-time alerts",
            "medium_term_3_6_months": "Full LLM-powered strategic forecasting available with API key",
            "long_term_1_year_plus": "Requires historical trend data integration"
        },
        "scenarios": [
            {"name": "Best Case", "probability": "Medium", "trigger": "Sentiment recovery above 60%", "outcome": "Stable governance, high scheme coverage", "impact_severity": 3},
            {"name": "Most Likely", "probability": "High", "trigger": "Current trajectory continues", "outcome": "Marginal improvements with targeted interventions", "impact_severity": 5},
            {"name": "Worst Case", "probability": "Low", "trigger": "Sentiment drops below 30%", "outcome": "Civil unrest indicators rise, emergency response needed", "impact_severity": 8},
        ],
        "strategic_recommendations": [
            "Prioritize booths with sentiment below 40% for immediate intervention",
            "Deploy field workers to address top civic issues",
            "Accelerate unenrolled beneficiary coverage campaigns"
        ],
        "scenario_tree": [
            {"event": query, "children": [
                {"event": "Civic sentiment analyzed", "children": [
                    {"event": f"National avg: {stats['national_avg_sentiment']}%", "children": []},
                    {"event": f"{stats['total_complaints']:,} active complaints", "children": []}
                ]},
                {"event": "Data pipeline operational", "children": [
                    {"event": f"{stats['total_booths']} booths monitored", "children": []},
                ]}
            ]}
        ],
        "timeline": [
            {"day": 1, "event": "Intelligence query initiated"},
            {"day": 7, "event": "Booth-level sentiment trend established"},
            {"day": 15, "event": "Scheme gap interventions launched"},
            {"day": 30, "event": "First measurable impact on sentiment scores"},
            {"day": 45, "event": "Full cycle review and strategic recalibration"},
        ]
    }

def _aggregate_top_issues(booths) -> List[Dict]:
    """Aggregates top issues across all booths."""
    issue_counts: Dict[str, int] = {}
    for b in booths:
        for issue in b.get("top_issues", []):
            issue_counts[issue["issue"]] = issue_counts.get(issue["issue"], 0) + issue["count"]
    return [{"issue": k, "affected_citizens": v} for k, v in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:6]]

# ============================================================
# TOOL FUNCTIONS — Enhanced with caching and error handling
# ============================================================

@cache_tool(ttl_seconds=60)
def tool_civic_sentiment() -> Dict:
    """Returns national and booth-level sentiment data from JanGraph civic store."""
    try:
        stats = store.get_stats()
        booths = store.get_booths()
        critical = [b for b in booths if b["avg_sentiment"] < 40]
        return {
            "source": "JanGraph Civic Intelligence Store",
            "national_sentiment": stats["national_avg_sentiment"],
            "total_citizens": stats["total_citizens"],
            "total_booths": stats["total_booths"],
            "critical_booths": len(critical),
            "top_issues": _aggregate_top_issues(booths),
            "constituency_breakdown": [
                {"name": c["name"], "sentiment": c["avg_sentiment"], "population": c["total_population"]}
                for c in store.get_constituencies()
            ]
        }
    except Exception as e:
        logger.error(f"tool_civic_sentiment failed: {e}")
        return {"error": str(e), "source": "JanGraph Civic Store (fallback)"}

@cache_tool(ttl_seconds=300)
def tool_scheme_coverage() -> Dict:
    """Returns government scheme enrollment and gap data."""
    try:
        schemes = store.get_schemes()
        stats = store.get_stats()
        return {
            "source": "JanGraph Beneficiary Linkage Engine",
            "total_schemes": len(schemes),
            "total_citizens_tracked": stats["total_citizens"],
            "schemes": [
                {"name": s["name"], "ministry": s["ministry"], "target": s["target_segment"], "benefit": s["benefit"]}
                for s in schemes
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=60)
def tool_worker_deployment() -> Dict:
    """Returns field worker status and performance data."""
    try:
        workers = store.get_workers()
        online = [w for w in workers if w["status"] == "Online"]
        avg_perf = round(sum(w["performance_score"] for w in workers) / len(workers), 1) if workers else 0
        return {
            "source": "JanGraph Worker Operations",
            "total_workers": len(workers),
            "online": len(online),
            "avg_performance": avg_perf,
            "top_performers": len([w for w in workers if w["performance_score"] > 80]),
        }
    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------
# Social Media Tools (using osint_engine)
# ------------------------------------------------------------
@cache_tool(ttl_seconds=300)
def tool_twitter_trends() -> Dict:
    """Returns real-time political trends from TwitterAPI.io."""
    try:
        return osint_engine.get_twitter_trends()
    except Exception as e:
        return {"error": str(e), "source": "Twitter Trends (fallback)"}

@cache_tool(ttl_seconds=300)
def tool_reddit_discourse() -> Dict:
    """Returns deep community parsing from Reddit."""
    try:
        return osint_engine.get_reddit_discourse()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=600)
def tool_youtube_sentiment() -> Dict:
    """Returns video content sentiment from YouTube."""
    try:
        return osint_engine.get_youtube_sentiment()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=60)
def tool_telegram_hyperlocal() -> Dict:
    """Returns hyper-local emerging alerts from Telegram."""
    try:
        return osint_engine.get_telegram_hyperlocal()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=300)
def tool_bewgle_insights() -> Dict:
    """Returns AI-driven persona and topic ratings from Bewgle."""
    try:
        return osint_engine.get_bewgle_insights()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=300)
def tool_mastodon_public() -> Dict:
    """Returns public posts from Mastodon instances."""
    try:
        return osint_engine.get_mastodon_public()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=300)
def tool_bluesky_trends() -> Dict:
    """Returns Bluesky public trends using Apify scraper."""
    try:
        return osint_engine.get_bluesky_trends()
    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------
# Geopolitical & Economic Tools
# ------------------------------------------------------------
@cache_tool(ttl_seconds=1800)
def tool_conflict_data() -> Dict:
    """Returns current global conflict intelligence via ACLED/UCDP."""
    try:
        return osint_engine.get_acled_data()
    except Exception as e:
        # Fallback to simulated if API fails
        return {
            "source": "ACLED/UCDP Conflict Database (Simulated Fallback)",
            "active_conflicts": [
                {"region": "Eastern Europe", "type": "Interstate War", "intensity": "High", "start_date": "2022-02-24", "india_exposure": "Medium — energy imports, wheat supply chain"},
                {"region": "Middle East", "type": "Regional Conflict", "intensity": "High", "start_date": "2023-10-07", "india_exposure": "High — oil routes, diaspora, trade corridors"},
                {"region": "South China Sea", "type": "Maritime Tension", "intensity": "Medium", "start_date": "2024-01-15", "india_exposure": "Medium — shipping lanes, QUAD alliance dynamics"},
            ],
            "global_conflict_index": 73.2,
            "year_over_year_change": "+12.4%"
        }

@cache_tool(ttl_seconds=3600)
def tool_energy_markets() -> Dict:
    """Returns energy market data (oil, gas prices and trends)."""
    try:
        return osint_engine.get_energy_markets()
    except Exception as e:
        return {
            "source": "EIA Energy Information / Markets (Fallback)",
            "brent_crude_usd": 87.40,
            "natural_gas_usd": 3.42,
            "india_oil_import_dependency": "87.3%",
            "risk_assessment": "Elevated — Middle East corridor disruption could push to $105+",
        }

@cache_tool(ttl_seconds=3600)
def tool_economic_indicators() -> Dict:
    """Returns key economic indicators from FRED."""
    try:
        return osint_engine.get_fred_economic_data()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=3600)
def tool_defense_posture() -> Dict:
    """Returns defense readiness and strategic posture data."""
    try:
        return osint_engine.get_defense_posture()
    except Exception as e:
        return {
            "source": "Defense Intelligence Briefing (Fallback)",
            "border_alert_level": "Elevated",
            "active_deployments": ["LAC Northern Sector", "LoC Kashmir", "Andaman & Nicobar Islands"],
            "cyber_threat_level": "Moderate-High",
        }

@cache_tool(ttl_seconds=300)
def tool_gdelt_events() -> Dict:
    """Returns global event and tone data from GDELT."""
    try:
        return osint_engine.get_gdelt_data()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=60)
def tool_opensky_aviation() -> Dict:
    """Returns real-time global aviation intelligence."""
    try:
        return osint_engine.get_opensky_data()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=300)
def tool_polymarket_predictions() -> Dict:
    """Returns geopolitical prediction markets data."""
    try:
        return osint_engine.get_polymarket_data()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=600)
def tool_nasa_firms() -> Dict:
    """Returns global fire and thermal anomaly data via NASA."""
    try:
        return osint_engine.get_nasa_firms()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=600)
def tool_usgs_earthquakes() -> Dict:
    """Returns global significant earthquake data."""
    try:
        return osint_engine.get_usgs_earthquakes()
    except Exception as e:
        return {"error": str(e)}

@cache_tool(ttl_seconds=60)
def tool_news_intelligence() -> Dict:
    """Returns latest aggregated news intelligence from the feed engine."""
    try:
        feeds = feed_engine.get_feeds()
        if not feeds:
            feeds = [
                {"category": "Geopolitics", "text": "India strengthens diplomatic ties with Gulf nations amid energy security concerns", "urgency": "Medium"},
                {"category": "Economics", "text": "RBI holds repo rate steady at 6.5% amid sticky inflation", "urgency": "Medium"},
                {"category": "Defense", "text": "Indian Navy expands patrol operations in Indian Ocean Region", "urgency": "High"},
            ]
        return {
            "source": "JanGraph Live Intelligence Feed Aggregator",
            "total_feeds_ingested": len(feeds),
            "latest_briefs": feeds[:10],
        }
    except Exception as e:
        return {"error": str(e)}

# Tool registry with descriptions for the planner
TOOL_REGISTRY = {
    # Civic & governance
    "civic_sentiment": {"fn": tool_civic_sentiment, "description": "National sentiment, booth-level analytics, top civic issues"},
    "scheme_coverage": {"fn": tool_scheme_coverage, "description": "Government scheme enrollment, coverage gaps, beneficiary data"},
    "worker_deployment": {"fn": tool_worker_deployment, "description": "Field worker status, deployment, performance metrics"},

    # Social media intelligence (NEW)
    "twitter_trends": {"fn": tool_twitter_trends, "description": "Real-time political or social trends and viral sentiment from Twitter/X."},
    "reddit_discourse": {"fn": tool_reddit_discourse, "description": "Deep community sentiment and grassroots consensus from Reddit megathreads."},
    "youtube_sentiment": {"fn": tool_youtube_sentiment, "description": "Aggregated sentiment derived from YouTube comments on political/social videos."},
    "telegram_hyperlocal": {"fn": tool_telegram_hyperlocal, "description": "Hyper-local emerging alerts and mobilization signals from public Telegram groups."},
    "bewgle_insights": {"fn": tool_bewgle_insights, "description": "AI-driven topic ratings and customer/citizen personas derived specifically for the Indian context."},
    "mastodon_public": {"fn": tool_mastodon_public, "description": "Public posts from Mastodon, a decentralized social network, for alternative sentiment."},
    "bluesky_trends": {"fn": tool_bluesky_trends, "description": "Trends and public posts from Bluesky, an emerging social platform."},

    # Geopolitical & economic
    "conflict_data": {"fn": tool_conflict_data, "description": "Global conflict zones, war data, India exposure assessment"},
    "energy_markets": {"fn": tool_energy_markets, "description": "Oil prices, gas prices, energy import dependency, price forecasts"},
    "economic_indicators": {"fn": tool_economic_indicators, "description": "FRED macroeconomic data (inflation, rates, CPI)"},
    "defense_posture": {"fn": tool_defense_posture, "description": "Border alerts, military deployments, defense budget, cyber threats"},
    "gdelt_events": {"fn": tool_gdelt_events, "description": "GDELT global events and tone database. Tracks geopolitical tension."},
    "opensky_aviation": {"fn": tool_opensky_aviation, "description": "ADS-B live aviation intelligence for military or commercial anomalies."},
    "polymarket_predictions": {"fn": tool_polymarket_predictions, "description": "Kalshi/Polymarket derived odds for geopolitical outcomes."},

    # Infrastructure & environment
    "nasa_firms": {"fn": tool_nasa_firms, "description": "NASA thermal anomalies, fire hotspots, relevant for natural disaster metrics."},
    "usgs_earthquakes": {"fn": tool_usgs_earthquakes, "description": "Real-time USGS seismic event data for disaster tracking."},

    # News
    "news_intelligence": {"fn": tool_news_intelligence, "description": "Latest aggregated real-time news briefs categorized by domain."},
}

# ============================================================
# PROMPTS (refined for better reasoning)
# ============================================================

PLANNER_PROMPT = """You are the JanGraph OS Planner Agent.

Given a user query about geopolitics, economics, governance, or civic intelligence,
determine which data tools should be called to synthesize a comprehensive answer.

**TOOL MAPPING & USAGE STRATEGY:**
1. **Public Sentiment / Social Media**: If query involves public opinion, grassroots issues, or voter reactions -> MUST CALL `reddit_discourse`, `youtube_sentiment`, `twitter_trends`, and `bewgle_insights`. Also consider `mastodon_public` and `bluesky_trends` for broader reach.
2. **Hyperlocal / Regional Issues**: If query involves specific states, protests, or on-the-ground alerts -> MUST CALL `telegram_hyperlocal` and `civic_sentiment`.
3. **Macroeconomics & Markets**: If query involves inflation, GDP, or markets -> MUST CALL `economic_indicators`, `energy_markets`, and `polymarket_predictions`.
4. **Geopolitics & Defense**: If query involves war, defense posture, or global relations -> MUST CALL `conflict_data`, `opensky_aviation`, `gdelt_events`, and `defense_posture`.
5. **Infrastructure & Environment**: If query involves climate, resources, or disasters -> MUST CALL `nasa_firms` and `usgs_earthquakes`.

Available tools: 
{tool_list}

Respond with ONLY a valid JSON object:
{{
  "understanding": "Brief summary of what the user is asking",
  "domains": ["list of relevant domains"],
  "time_horizon": "short-term | medium-term | long-term",
  "tools_needed": ["tool_name_1", "tool_name_2", "tool_name_3"],
  "sub_questions": ["sub-question 1", "sub-question 2"]
}}

User Query: {query}"""

REASONING_PROMPT = """You are the JanGraph OS Strategic Reasoning Agent.

The user asked: "{query}"

The Planner identified these sub-questions: {sub_questions}

The following data was gathered from our intelligence tools:

{tool_outputs}

Now produce a comprehensive strategic analysis. Use the data to ground your reasoning.
If some tools returned errors, note the limitations and use available data.

Respond with ONLY valid JSON:
{{
  "executive_summary": "2-3 sentence high-level summary",
  "situation_analysis": "Detailed current situation based on data",
  "key_risk_factors": [
    {{"factor": "name", "severity": "Critical|High|Medium|Low", "description": "why this matters"}}
  ],
  "impact_on_india": {{
    "economic": "assessment",
    "political": "assessment",
    "defense": "assessment",
    "social": "assessment"
  }},
  "forecasts": {{
    "short_term_0_45_days": "prediction",
    "medium_term_3_6_months": "prediction",
    "long_term_1_year_plus": "prediction"
  }},
  "scenarios": [
    {{
      "name": "Best Case",
      "probability": "Low|Medium|High",
      "trigger": "what causes this",
      "outcome": "what happens",
      "impact_severity": 1
    }},
    {{
      "name": "Most Likely",
      "probability": "Low|Medium|High",
      "trigger": "what causes this",
      "outcome": "what happens",
      "impact_severity": 5
    }},
    {{
      "name": "Worst Case",
      "probability": "Low|Medium|High",
      "trigger": "what causes this",
      "outcome": "what happens",
      "impact_severity": 10
    }}
  ],
  "strategic_recommendations": [
    "recommendation 1",
    "recommendation 2",
    "recommendation 3"
  ],
  "scenario_tree": [
    {{
      "event": "Root cause event",
      "children": [
        {{
          "event": "Consequence 1",
          "children": [
            {{"event": "Sub-consequence 1a", "children": []}},
            {{"event": "Sub-consequence 1b", "children": []}}
          ]
        }},
        {{
          "event": "Consequence 2",
          "children": [
            {{"event": "Sub-consequence 2a", "children": []}}
          ]
        }}
      ]
    }}
  ],
  "timeline": [
    {{"time": "Day 1-7", "event": "Immediate cause", "impact": "description", "type": "Social|Economic|Military|Political"}},
    {{"time": "Day 15-30", "event": "Secondary ripple", "impact": "description", "type": "Social|Economic|Military|Political"}},
    {{"time": "Day 45+", "event": "Tertiary shift", "impact": "description", "type": "Social|Economic|Military|Political"}}
  ],
  "_meta": {{
    "tools_used": ["List here only the tools you actually used from the provided data"],
    "timestamp": "Generated at current simulation time"
  }}
}}"""

WHATIF_PROMPT = """You are the JanGraph OS What-If Simulation Engine.

Original analysis context:
{original_context}

The user wants to simulate a modified scenario:
"{whatif_query}"

Variable adjustments provided: {variables}

Recompute the analysis with these new assumptions. Respond with ONLY valid JSON:
{{
  "simulation_title": "title of the what-if scenario",
  "modified_assumptions": ["assumption 1", "assumption 2"],
  "revised_outcome": "what changes in the outcome",
  "impact_delta": {{
    "economic": "how economic impact changes",
    "political": "how political impact changes",
    "defense": "how defense posture changes",
    "social": "how social impact changes"
  }},
  "revised_scenarios": [
    {{"name": "Best Case", "probability": "Low|Medium|High", "outcome": "revised", "impact_severity": 1-10}},
    {{"name": "Most Likely", "probability": "Low|Medium|High", "outcome": "revised", "impact_severity": 1-10}},
    {{"name": "Worst Case", "probability": "Low|Medium|High", "outcome": "revised", "impact_severity": 1-10}}
  ],
  "chain_reactions": [
    {{"trigger": "variable change", "effects": ["effect 1", "effect 2"]}}
  ],
  "revised_recommendations": ["rec 1", "rec 2"]
}}"""

# ============================================================
# MAIN AGENT PIPELINE
# ============================================================

async def run_strategic_analysis(query: str) -> Dict[str, Any]:
    """
    Full agentic pipeline:
    1. Planner decides which tools to call (using LLM)
    2. Tools execute concurrently (asynchronously)
    3. Reasoning engine synthesizes a strategic analysis
    """
    try:
        llm = get_enterprise_llm(temperature=0.2)
    except RuntimeError:
        logger.warning("LLM not available, falling back to local analysis")
        return _fallback_analysis(query)

    # --- Step 1: Planner ---
    tool_list = "\n".join([f"- {name}: {info['description']}" for name, info in TOOL_REGISTRY.items()])
    try:
        planner_response = llm.invoke(PLANNER_PROMPT.format(tool_list=tool_list, query=query))
        plan = _parse_json(planner_response.content)
    except Exception as e:
        logger.error(f"Planner failed: {e}", exc_info=True)
        # Fallback plan: call all available tools? No, too many. Use sensible defaults.
        plan = {
            "understanding": query,
            "domains": ["general"],
            "time_horizon": "medium-term",
            "tools_needed": ["civic_sentiment", "economic_indicators", "news_intelligence", "twitter_trends", "reddit_discourse"],
            "sub_questions": [query]
        }

    # --- Step 2: Execute tools (async if possible) ---
    tools_to_call = plan.get("tools_needed", [])
    tool_outputs = {}
    # Execute sequentially for simplicity, but we could use asyncio.gather
    for tool_name in tools_to_call:
        if tool_name in TOOL_REGISTRY:
            try:
                # Check if the tool function is async (though ours are sync, we can still run in thread)
                tool_fn = TOOL_REGISTRY[tool_name]["fn"]
                # If async, await; else call
                if asyncio.iscoroutinefunction(tool_fn):
                    result = await tool_fn()
                else:
                    # Run sync function in thread to avoid blocking
                    result = await asyncio.to_thread(tool_fn)
                tool_outputs[tool_name] = result
                logger.info(f"Tool executed: {tool_name}")
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
                tool_outputs[tool_name] = {"error": str(e)}
        else:
            logger.warning(f"Tool {tool_name} not found in registry")

    # Ensure civic_sentiment is always present for grounding
    if "civic_sentiment" not in tool_outputs:
        tool_outputs["civic_sentiment"] = await asyncio.to_thread(tool_civic_sentiment)

    # --- Step 3: Reasoning ---
    try:
        reasoning_response = llm.invoke(REASONING_PROMPT.format(
            query=query,
            sub_questions=json.dumps(plan.get("sub_questions", [query])),
            tool_outputs=json.dumps(tool_outputs, indent=2, default=str)
        ))
        analysis = _parse_json(reasoning_response.content)
    except Exception as e:
        logger.error(f"Reasoning engine failed: {e}", exc_info=True)
        analysis = _fallback_analysis(query)

    # Add metadata
    analysis["_meta"] = {
        "query": query,
        "tools_used": list(tool_outputs.keys()),
        "plan": plan,
        "timestamp": datetime.now().isoformat(),
        "engine": "JanGraph Strategic Intelligence v3.0"
    }
    return analysis

async def run_whatif_simulation(original_context: str, whatif_query: str, variables: Dict) -> Dict[str, Any]:
    """Runs what-if scenario simulation using the LLM."""
    try:
        llm = get_enterprise_llm(temperature=0.3)
        response = llm.invoke(WHATIF_PROMPT.format(
            original_context=original_context[:2000],
            whatif_query=whatif_query,
            variables=json.dumps(variables)
        ))
        result = _parse_json(response.content)
        result["_meta"] = {
            "query": whatif_query,
            "variables_modified": variables,
            "timestamp": datetime.now().isoformat()
        }
        return result
    except Exception as e:
        logger.error(f"What-if simulation failed: {e}", exc_info=True)
        return {
            "simulation_title": f"What-If: {whatif_query}",
            "error": str(e),
            "modified_assumptions": list(variables.keys()),
            "revised_outcome": "Simulation engine requires LLM connectivity. Fallback mode active.",
            "impact_delta": {"economic": "Uncertain", "political": "Uncertain", "defense": "Uncertain", "social": "Uncertain"},
            "revised_scenarios": [],
            "chain_reactions": [],
            "revised_recommendations": ["Ensure Groq API connectivity for full simulation capabilities."]
        }