"""
Unified Intelligence API Endpoints

Single entry point for all AI capabilities:
- Reasoning (Expert Multi-Agent Analysis)
- Tools (External Data Fetching & OSINT)
- Visuals (Charts, Diagrams, Map Intelligence)

The system automatically detects and activates appropriate capabilities.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List

from app.models.unified_intelligence import (
    UnifiedIntelligenceRequest,
    UnifiedIntelligenceResponse,
    CapabilityType,
)
from app.services.unified_intelligence_engine import get_unified_intelligence_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Unified Intelligence"])


# =============================================================================
# Main Unified Endpoint
# =============================================================================

@router.post("/analyze")
async def analyze_unified(
    request: UnifiedIntelligenceRequest,
) -> Dict[str, Any]:
    """
    **UNIFIED INTELLIGENCE ENDPOINT**

    Single entry point for all AI capabilities. The system automatically:
    1. Assesses query complexity and requirements
    2. Activates appropriate capabilities (reasoning, tools, visuals, map)
    3. Executes capabilities in parallel
    4. Returns unified response with all results

    **Capabilities:**
    - **Reasoning**: Expert multi-agent analysis with consensus building
    - **Tools**: Real-time data fetching from OSINT, social media, APIs
    - **Visuals**: Chart and diagram generation with AI
    - **Map Intelligence**: Geographic visualization with markers/heatmaps

    **Example Queries:**
    - "Analyze India's economic growth and generate visualizations"
      → Activates: reasoning + visuals + map

    - "What are the latest trends on social media about climate change?"
      → Activates: tools + reasoning

    - "Compare GDP of India and China with projections"
      → Activates: reasoning + tools + visuals + map

    **Parameters:**
    - `query`: Natural language query (required)
    - `context`: Additional context (optional)
    - `forced_capabilities`: Override auto-detection (optional)
    - `max_processing_time`: Timeout in seconds (default: 30)
    - `include_debug_info`: Include activation details (default: false)

    **Response:**
    - `assessment`: Query complexity and capability recommendations
    - `reasoning`: Expert analysis results (if activated)
    - `tools`: External data fetching results (if activated)
    - `visuals`: Charts and diagrams (if activated)
    - `map_intelligence`: Geographic visualization (if activated)
    - `unified_summary`: Synthesized summary of all results
    - `confidence_score`: Overall confidence (0.0-1.0)
    - `capabilities_activated`: List of capabilities that were used

    **Performance:**
    - Average latency: 5-7 seconds
    - Parallel execution: Yes
    - Graceful degradation: Yes (if one capability fails, others continue)
    """
    engine = get_unified_intelligence_engine()

    try:
        result = await engine.analyze(request)

        return {
            "status": "success",
            "query_id": result.query_id,
            "conversation_id": result.conversation_id,
            "query": result.query,
            "assessment": result.assessment.to_dict(),
            "reasoning": result.reasoning.to_dict() if result.reasoning else None,
            "tools": result.tools.to_dict() if result.tools else None,
            "visuals": result.visuals.to_dict() if result.visuals else None,
            "map_intelligence": result.map_intelligence.to_dict() if result.map_intelligence else None,
            "unified_summary": result.unified_summary,
            "assistant_response": result.assistant_response.to_dict(),
            "confidence_score": result.confidence_score,
            "data_sources_used": result.data_sources_used,
            "capabilities_activated": result.capabilities_activated,
            "capability_statuses": result.capability_statuses,
            "total_processing_time_ms": result.total_processing_time_ms,
            "timestamp": result.timestamp,
        }

    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unified intelligence error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# =============================================================================
# Quick Assessment Endpoint (No Execution)
# =============================================================================

@router.post("/assess")
async def assess_query(
    query: str = Query(..., description="Query to assess"),
) -> Dict[str, Any]:
    """
    **QUERY ASSESSMENT ENDPOINT**

    Analyzes a query to determine:
    - Complexity level
    - Required capabilities
    - Domains involved
    - Expected processing approach

    Useful for:
    - Preview what capabilities will be activated
    - Understanding query characteristics
    - Debugging capability selection

    **Does NOT execute the query**, only analyzes it.
    """
    engine = get_unified_intelligence_engine()

    try:
        assessment = await engine._assessor.assess_query(query)

        return {
            "status": "success",
            "assessment": assessment.to_dict(),
        }

    except Exception as e:
        logger.error(f"Assessment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Capability Info Endpoints
# =============================================================================

@router.get("/capabilities")
async def get_capabilities_info() -> Dict[str, Any]:
    """
    **CAPABILITIES INFORMATION**

    Returns detailed information about available capabilities:
    - What each capability does
    - When it gets activated
    - Example queries for each
    """
    capabilities = [
        {
            "id": "reasoning",
            "name": "Expert Multi-Agent Reasoning",
            "description": "Deep analysis using multiple expert agents with debate and consensus building",
            "activation_triggers": [
                "Complex queries requiring multiple perspectives",
                "Analysis requests (analyze, assess, evaluate)",
                "Comparison and contrast queries",
                "Strategic planning queries",
            ],
            "example_queries": [
                "Analyze the geopolitical impact of India's economic rise",
                "Compare military capabilities of India and China",
                "What are the long-term consequences of climate change?",
            ],
        },
        {
            "id": "tools",
            "name": "External Data Fetching & OSINT",
            "description": "Real-time data from social media, news, APIs, and intelligence sources",
            "activation_triggers": [
                "Queries mentioning 'latest', 'current', 'recent'",
                "Social media references (Twitter, Reddit)",
                "Real-time or trending topics",
                "Queries requiring external data",
            ],
            "example_queries": [
                "What are the latest trends on Twitter about climate change?",
                "Current news about India-China relations",
                "What's trending on Reddit about AI?",
            ],
        },
        {
            "id": "visuals",
            "name": "Charts & Diagram Generation",
            "description": "AI-generated visualizations including charts, diagrams, and workflows",
            "activation_triggers": [
                "Queries with data indicators (GDP, inflation, population)",
                "Requests for visualization (chart, graph, diagram)",
                "Comparison queries with time dimensions",
                "Trend analysis requests",
            ],
            "example_queries": [
                "Show GDP growth trend of India over last 10 years",
                "Compare population of India and China with charts",
                "Create a diagram of supply chain disruptions",
            ],
        },
        {
            "id": "map_intelligence",
            "name": "Geographic Visualization",
            "description": "Interactive map features including markers, heatmaps, routes, and highlights",
            "activation_triggers": [
                "Geographic entities mentioned (countries, cities, regions)",
                "Location-based queries",
                "Spatial analysis requests",
            ],
            "example_queries": [
                "Show conflict zones in Middle East on map",
                "Highlight trade routes between India and Europe",
                "Display earthquake risk zones in South Asia",
            ],
        },
    ]

    return {
        "status": "success",
        "count": len(capabilities),
        "capabilities": capabilities,
        "notes": [
            "Multiple capabilities can activate simultaneously",
            "Capabilities execute in parallel for better performance",
            "System gracefully handles individual capability failures",
        ],
    }


@router.get("/examples")
async def get_example_queries() -> Dict[str, Any]:
    """
    **EXAMPLE QUERIES**

    Returns categorized example queries demonstrating different capability combinations.
    """
    examples = {
        "simple_reasoning": [
            "What is India's current economic status?",
            "Explain the concept of inflation",
            "What are the main issues facing developing countries?",
        ],
        "reasoning_with_visuals": [
            "Analyze India's GDP growth and show charts",
            "Compare military spending of top 5 countries",
            "Show climate change trends over last 50 years",
        ],
        "tools_with_reasoning": [
            "What are people saying on social media about AI regulations?",
            "Latest news about India-Pakistan relations and analysis",
            "Current trends in renewable energy adoption",
        ],
        "all_capabilities": [
            "Comprehensive analysis of India-China economic competition with visualizations",
            "Analyze global trade disruptions with charts and geographic impact",
            "Space race analysis with spending trends and country highlights",
        ],
        "quick_data": [
            "Latest earthquake reports",
            "Current stock market snapshot",
            "Today's trending topics on Twitter",
        ],
    }

    return {
        "status": "success",
        "examples": examples,
        "tip": "Try asking complex multi-faceted questions to see multiple capabilities working together!",
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    **HEALTH CHECK**

    Returns health status of the unified intelligence system and all sub-components.
    """
    # TODO: Add actual health checks for each component
    return {
        "status": "healthy",
        "service": "unified-intelligence",
        "components": {
            "query_assessor": "ok",
            "reasoning_engine": "ok",
            "tools_engine": "ok",
            "visual_intelligence": "ok",
            "map_intelligence": "ok",
            "orchestrator": "ok",
        },
        "version": "1.0.0",
    }


# =============================================================================
# Backward Compatibility Wrappers
# =============================================================================

@router.post("/expert-mode")
async def expert_mode_wrapper(
    query: str = Body(..., embed=True, description="Query for expert analysis"),
    context: Dict[str, Any] = Body(default_factory=dict, embed=True),
) -> Dict[str, Any]:
    """
    **BACKWARD COMPATIBILITY: Expert Mode**

    Wrapper for existing expert mode functionality.
    Internally uses unified intelligence with reasoning-only.

    **Migrated to**: `/analyze` with `forced_capabilities: ["reasoning"]`
    """
    engine = get_unified_intelligence_engine()

    try:
        request = UnifiedIntelligenceRequest(
            query=query,
            context=context,
            forced_capabilities=[CapabilityType.REASONING],
        )

        result = await engine.analyze(request)

        # Format as expert response
        return {
            "status": "success",
            "executive_summary": result.reasoning.executive_summary if result.reasoning else result.unified_summary,
            "analysis": result.reasoning.analysis if result.reasoning else "",
            "key_findings": result.reasoning.key_findings if result.reasoning else [],
            "confidence": result.confidence_score,
            "expert_agents_used": result.reasoning.expert_agents_used if result.reasoning else [],
            "_meta": {
                "note": "This endpoint is deprecated. Use /analyze for full unified intelligence.",
                "query_id": result.query_id,
            },
        }

    except Exception as e:
        logger.error(f"Expert mode error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual-mode")
async def visual_mode_wrapper(
    query: str = Body(..., embed=True, description="Query for visual intelligence"),
) -> Dict[str, Any]:
    """
    **BACKWARD COMPATIBILITY: Visual Mode**

    Wrapper for existing visual intelligence functionality.
    Internally uses unified intelligence with visuals-only.

    **Migrated to**: `/analyze` with `forced_capabilities: ["visuals"]`
    """
    engine = get_unified_intelligence_engine()

    try:
        request = UnifiedIntelligenceRequest(
            query=query,
            forced_capabilities=[CapabilityType.VISUALS],
        )

        result = await engine.analyze(request)

        # Format as visual response
        return {
            "status": "success",
            "charts": result.visuals.charts if result.visuals else [],
            "diagrams": result.visuals.diagrams if result.visuals else [],
            "insights": result.visuals.chart_insights if result.visuals else [],
            "_meta": {
                "note": "This endpoint is deprecated. Use /analyze for full unified intelligence.",
                "query_id": result.query_id,
            },
        }

    except Exception as e:
        logger.error(f"Visual mode error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
