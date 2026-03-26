"""
Visual Intelligence API Endpoints

API endpoints for the Visual + Data + Map Intelligence Engine.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List

from app.models.visual_intelligence import (
    VisualIntelligenceRequest,
    ChartGenerationRequest,
    DiagramGenerationRequest,
    ChartType,
    DiagramType,
)
from app.services.visual_intelligence_engine import get_visual_intelligence_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Visual Intelligence"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ParseIntentRequest(BaseModel):
    """Request model for intent parsing."""
    query: str = Field(..., description="Natural language query", min_length=3)


class ChartRequest(BaseModel):
    """Request model for chart generation."""
    chart_type: ChartType
    data: Dict[str, Any] = Field(..., description="Chart data with labels and datasets")
    title: str = Field(..., description="Chart title")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional chart options")


class DiagramRequest(BaseModel):
    """Request model for diagram generation."""
    diagram_type: DiagramType
    description: str = Field(..., description="Description of what to diagram")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/analyze")
async def analyze_with_visuals(
    request: VisualIntelligenceRequest,
) -> Dict[str, Any]:
    """
    Process a query and return unified visual intelligence output.

    This is the main endpoint that orchestrates:
    - Intent parsing
    - Data fetching from external APIs
    - Chart generation (QuickChart)
    - Diagram generation (Pollinations)
    - Map command generation
    - Insight synthesis

    Returns:
        Complete VisualIntelligenceResponse with all outputs
    """
    engine = get_visual_intelligence_engine()

    try:
        result = await engine.process_query(
            query=request.query,
            context=request.context,
            options={
                "force_chart_type": request.force_chart_type,
                "force_diagram_type": request.force_diagram_type,
                "include_map": request.include_map,
                "include_expert_analysis": request.include_expert_analysis,
            }
        )

        return {
            "status": "success",
            "data": result.to_dict(),
        }

    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing visual intelligence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.post("/parse-intent")
async def parse_query_intent(
    request: ParseIntentRequest,
) -> Dict[str, Any]:
    """
    Parse a query into structured intent without full analysis.

    Useful for previewing how a query will be interpreted before
    running the full analysis pipeline.

    Returns:
        ParsedIntent with extracted countries, domains, intent type, etc.
    """
    engine = get_visual_intelligence_engine()

    try:
        intent = await engine.parse_intent(request.query)

        return {
            "status": "success",
            "data": intent.to_dict(),
        }

    except Exception as e:
        logger.error(f"Error parsing intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-chart")
async def generate_chart_only(
    request: ChartRequest,
) -> Dict[str, Any]:
    """
    Generate a chart from provided data.

    This endpoint allows direct chart generation without query parsing
    or data fetching. Useful when you already have the data.

    Request body:
        - chart_type: line, bar, pie, scatter, radar, doughnut
        - data: { labels: [...], datasets: [{ label, data, backgroundColor }] }
        - title: Chart title
        - options: { x_axis_label, y_axis_label }

    Returns:
        ChartOutput with chart URL and metadata
    """
    engine = get_visual_intelligence_engine()

    try:
        chart = await engine.generate_chart(
            chart_type=request.chart_type,
            data=request.data,
            title=request.title,
            options=request.options,
        )

        return {
            "status": "success",
            "data": chart.to_dict(),
        }

    except Exception as e:
        logger.error(f"Error generating chart: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-diagram")
async def generate_diagram_only(
    request: DiagramRequest,
) -> Dict[str, Any]:
    """
    Generate a diagram from provided context.

    This endpoint allows direct diagram generation without query parsing.

    Request body:
        - diagram_type: workflow, cause_effect, pipeline, infrastructure, network
        - description: What to show in the diagram
        - context: { elements: [...], relationships: [...], style: "professional" }

    Returns:
        DiagramOutput with image URL and metadata
    """
    engine = get_visual_intelligence_engine()

    try:
        diagram = await engine.generate_diagram(
            diagram_type=request.diagram_type,
            description=request.description,
            context=request.context,
        )

        return {
            "status": "success",
            "data": diagram.to_dict(),
        }

    except Exception as e:
        logger.error(f"Error generating diagram: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-sources")
async def get_available_data_sources() -> Dict[str, Any]:
    """
    Get list of available external data sources and their status.

    Returns information about:
    - World Bank API
    - Data Commons API
    - QuickChart API
    - Pollinations API

    Returns:
        List of data sources with status and available indicators
    """
    engine = get_visual_intelligence_engine()

    try:
        sources = engine.get_data_source_status()

        return {
            "status": "success",
            "count": len(sources),
            "data": sources,
        }

    except Exception as e:
        logger.error(f"Error getting data sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-domains")
async def get_supported_domains() -> Dict[str, Any]:
    """
    Get list of supported analysis domains.

    Returns:
        List of domains with descriptions and example queries
    """
    domains = [
        {
            "id": "economics",
            "name": "Economics",
            "description": "GDP, inflation, trade, investment analysis",
            "example_queries": [
                "Compare GDP growth of India and China",
                "India inflation trend over last 5 years",
            ],
        },
        {
            "id": "trade",
            "name": "Trade",
            "description": "Import/export, trade balances, agreements",
            "example_queries": [
                "India trade balance with United States",
                "ASEAN export trends",
            ],
        },
        {
            "id": "infrastructure",
            "name": "Infrastructure",
            "description": "Roads, ports, railways, connectivity",
            "example_queries": [
                "India infrastructure development impact",
                "South Asia connectivity analysis",
            ],
        },
        {
            "id": "climate",
            "name": "Climate",
            "description": "Emissions, temperature, environmental data",
            "example_queries": [
                "CO2 emissions comparison G20 countries",
                "Climate impact on South Asia",
            ],
        },
        {
            "id": "energy",
            "name": "Energy",
            "description": "Oil, gas, renewable energy, consumption",
            "example_queries": [
                "India energy consumption trend",
                "Oil prices impact on economy",
            ],
        },
        {
            "id": "defense",
            "name": "Defense",
            "description": "Military spending, capabilities",
            "example_queries": [
                "Military expenditure comparison",
                "Defense capabilities South Asia",
            ],
        },
        {
            "id": "space",
            "name": "Space",
            "description": "Space programs, satellites, missions",
            "example_queries": [
                "India space missions economics trend",
                "Space program capabilities comparison",
            ],
        },
        {
            "id": "logistics",
            "name": "Logistics",
            "description": "Supply chain, shipping, freight",
            "example_queries": [
                "Supply chain efficiency India",
                "Logistics infrastructure impact",
            ],
        },
        {
            "id": "disaster",
            "name": "Disaster",
            "description": "Natural disasters, impact analysis",
            "example_queries": [
                "Earthquake impact South Asia economy",
                "Flood damage assessment",
            ],
        },
    ]

    return {
        "status": "success",
        "count": len(domains),
        "data": domains,
    }


@router.get("/chart-types")
async def get_supported_chart_types() -> Dict[str, Any]:
    """
    Get list of supported chart types.

    Returns:
        List of chart types with descriptions and use cases
    """
    chart_types = [
        {
            "id": "line",
            "name": "Line Chart",
            "description": "Best for time series and trends",
            "use_cases": ["Trends over time", "Growth patterns", "Historical data"],
        },
        {
            "id": "bar",
            "name": "Bar Chart",
            "description": "Best for comparisons",
            "use_cases": ["Country comparisons", "Category comparisons", "Rankings"],
        },
        {
            "id": "pie",
            "name": "Pie Chart",
            "description": "Best for composition/proportion",
            "use_cases": ["Market share", "Budget allocation", "Distribution"],
        },
        {
            "id": "scatter",
            "name": "Scatter Plot",
            "description": "Best for correlations",
            "use_cases": ["Relationship between variables", "Cluster analysis"],
        },
        {
            "id": "radar",
            "name": "Radar Chart",
            "description": "Best for multi-dimensional comparison",
            "use_cases": ["Capability comparison", "Performance metrics"],
        },
        {
            "id": "doughnut",
            "name": "Doughnut Chart",
            "description": "Pie chart variant with center hole",
            "use_cases": ["Same as pie chart", "With center annotation"],
        },
    ]

    return {
        "status": "success",
        "count": len(chart_types),
        "data": chart_types,
    }


@router.get("/diagram-types")
async def get_supported_diagram_types() -> Dict[str, Any]:
    """
    Get list of supported diagram types.

    Returns:
        List of diagram types with descriptions and use cases
    """
    diagram_types = [
        {
            "id": "workflow",
            "name": "Workflow Diagram",
            "description": "Process flows and step sequences",
            "use_cases": ["Business processes", "Decision flows", "Procedures"],
        },
        {
            "id": "cause_effect",
            "name": "Cause-Effect Diagram",
            "description": "Fishbone/Ishikawa diagrams",
            "use_cases": ["Root cause analysis", "Impact chains", "Problem solving"],
        },
        {
            "id": "pipeline",
            "name": "Pipeline Diagram",
            "description": "Stage-based processing flows",
            "use_cases": ["Supply chains", "Data pipelines", "Manufacturing"],
        },
        {
            "id": "infrastructure",
            "name": "Infrastructure Diagram",
            "description": "Network and system diagrams",
            "use_cases": ["Network topology", "System architecture", "Asset maps"],
        },
        {
            "id": "network",
            "name": "Network Diagram",
            "description": "Node and connection graphs",
            "use_cases": ["Relationships", "Connections", "Dependencies"],
        },
        {
            "id": "hierarchy",
            "name": "Hierarchy Diagram",
            "description": "Tree structures and org charts",
            "use_cases": ["Organization charts", "Categories", "Taxonomies"],
        },
    ]

    return {
        "status": "success",
        "count": len(diagram_types),
        "data": diagram_types,
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the Visual Intelligence service.

    Returns:
        Service status and component health
    """
    return {
        "status": "healthy",
        "service": "visual-intelligence",
        "components": {
            "intent_parser": "ok",
            "data_fetch_layer": "ok",
            "graph_generator": "ok",
            "diagram_generator": "ok",
            "map_intelligence": "ok",
            "insight_synthesizer": "ok",
        },
    }
