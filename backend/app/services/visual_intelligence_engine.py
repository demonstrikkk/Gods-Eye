"""
Visual Intelligence Engine

Main orchestrator for the Visual + Data + Map Intelligence system.
Coordinates intent parsing, data fetching, visualization generation, and insight synthesis.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.visual_intelligence import (
    ParsedIntent,
    DataFetchResult,
    ChartOutput,
    DiagramOutput,
    MapIntelligenceOutput,
    InsightSynthesis,
    VisualIntelligenceResult,
    ChartType,
    DiagramType,
    ChartData,
    ChartDataset,
    ChartOptions,
    DiagramContext,
    DataSourceStatus,
)

from app.services.intent_parser import get_intent_parser
from app.services.data_fetch_layer import get_data_fetch_layer
from app.services.graph_generator import get_graph_generator
from app.services.diagram_generator import get_diagram_generator
from app.services.map_intelligence_layer import get_map_intelligence_layer
from app.services.insight_synthesizer import get_insight_synthesizer

logger = logging.getLogger(__name__)


# =============================================================================
# Visual Intelligence Engine
# =============================================================================

class VisualIntelligenceEngine:
    """
    Unified engine for Visual + Data + Map Intelligence.

    Orchestrates the complete pipeline:
    1. Parse user query into structured intent
    2. Fetch relevant data from external APIs
    3. Generate visualizations (charts, diagrams)
    4. Create map commands for geographic context
    5. Synthesize insights connecting all outputs

    Usage:
        engine = get_visual_intelligence_engine()
        result = await engine.process_query("Compare GDP growth of India and China")
    """

    def __init__(self):
        self._intent_parser = get_intent_parser()
        self._data_fetcher = get_data_fetch_layer()
        self._graph_generator = get_graph_generator()
        self._diagram_generator = get_diagram_generator()
        self._map_intelligence = get_map_intelligence_layer()
        self._insight_synthesizer = get_insight_synthesizer()

    async def process_query(
        self,
        query: str,
        context: Dict[str, Any] = None,
        options: Dict[str, Any] = None,
    ) -> VisualIntelligenceResult:
        """
        Process a natural language query and generate visual intelligence.

        Args:
            query: Natural language query string
            context: Additional context (selected country, view, etc.)
            options: Processing options (force_chart_type, include_map, etc.)

        Returns:
            VisualIntelligenceResult with all generated outputs
        """
        start_time = time.time()
        context = context or {}
        options = options or {}

        logger.info(f"Processing visual intelligence query: {query[:100]}...")

        try:
            # Phase 1: Parse Intent
            intent = await self.parse_intent(query)
            logger.debug(f"Parsed intent: {intent.primary_domain.value}, {intent.intent_type.value}")

            # Apply option overrides
            if options.get("force_chart_type"):
                intent.chart_type = options["force_chart_type"]
                intent.requires_chart = True

            if options.get("force_diagram_type"):
                intent.diagram_type = options["force_diagram_type"]
                intent.requires_diagram = True

            if options.get("include_map") is not None:
                intent.requires_map = options["include_map"]

            # Phase 2: Fetch Data
            data_result = await self._data_fetcher.fetch_for_intent(intent)
            logger.debug(f"Fetched data from {len(data_result.sources_used)} sources")

            # Phase 3: Generate Visualizations (in parallel)
            charts_task = self._graph_generator.generate_charts_for_data(intent, data_result)
            diagrams_task = self._diagram_generator.generate_diagrams_for_intent(intent, data_result)
            map_task = self._map_intelligence.generate_map_intelligence(intent, data_result)

            charts, diagrams, map_output = await asyncio.gather(
                charts_task,
                diagrams_task,
                map_task,
            )

            logger.debug(f"Generated {len(charts)} charts, {len(diagrams)} diagrams")

            # Phase 4: Synthesize Insights
            insight_synthesis = await self._insight_synthesizer.synthesize(
                intent=intent,
                data_result=data_result,
                charts=charts,
                diagrams=diagrams,
                map_output=map_output,
            )

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            return VisualIntelligenceResult(
                query_id=intent.query_id,
                parsed_intent=intent,
                data_result=data_result,
                charts=charts,
                diagrams=diagrams,
                map_output=map_output,
                insight_synthesis=insight_synthesis,
                processing_time_ms=round(processing_time_ms, 2),
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"Error processing visual intelligence query: {e}", exc_info=True)
            raise

    async def parse_intent(self, query: str) -> ParsedIntent:
        """
        Parse a query into structured intent.

        Args:
            query: Natural language query

        Returns:
            ParsedIntent with extracted information
        """
        return await self._intent_parser.parse(query)

    async def generate_chart(
        self,
        chart_type: ChartType,
        data: Dict[str, Any],
        title: str,
        options: Dict[str, Any] = None,
    ) -> ChartOutput:
        """
        Generate a standalone chart.

        Args:
            chart_type: Type of chart
            data: Chart data with labels and datasets
            title: Chart title
            options: Additional chart options

        Returns:
            ChartOutput with chart URL
        """
        options = options or {}

        # Convert dict data to ChartData
        labels = data.get("labels", [])
        datasets = []
        for ds in data.get("datasets", []):
            datasets.append(ChartDataset(
                label=ds.get("label", "Data"),
                values=ds.get("data", []),
                color=ds.get("backgroundColor", "#06b6d4"),
            ))

        chart_data = ChartData(labels=labels, datasets=datasets)
        chart_options = ChartOptions(
            title=title,
            x_axis_label=options.get("x_axis_label"),
            y_axis_label=options.get("y_axis_label"),
        )

        return await self._graph_generator.generate_chart(
            chart_type=chart_type,
            data=chart_data,
            options=chart_options,
        )

    async def generate_diagram(
        self,
        diagram_type: DiagramType,
        description: str,
        context: Dict[str, Any] = None,
    ) -> DiagramOutput:
        """
        Generate a standalone diagram.

        Args:
            diagram_type: Type of diagram
            description: Description of what to diagram
            context: Additional context

        Returns:
            DiagramOutput with image URL
        """
        context = context or {}

        diagram_context = DiagramContext(
            description=description,
            elements=context.get("elements", []),
            relationships=context.get("relationships", []),
            style=context.get("style", "professional"),
        )

        return await self._diagram_generator.generate_diagram(
            diagram_type=diagram_type,
            context=diagram_context,
        )

    def get_data_source_status(self) -> List[Dict[str, Any]]:
        """
        Get status of available data sources.

        Returns:
            List of data source status objects
        """
        sources = [
            DataSourceStatus(
                id="world_bank",
                name="World Bank Open Data",
                status="available",
                indicators=[
                    "GDP", "GDP Growth", "Inflation", "Unemployment",
                    "Population", "Exports", "Imports", "FDI"
                ],
                last_check=datetime.now().isoformat(),
            ),
            DataSourceStatus(
                id="data_commons",
                name="Google Data Commons",
                status="available",
                indicators=[
                    "Population", "Life Expectancy", "CO2 Emissions"
                ],
                last_check=datetime.now().isoformat(),
            ),
            DataSourceStatus(
                id="quickchart",
                name="QuickChart API",
                status="available",
                indicators=["Chart Generation"],
                last_check=datetime.now().isoformat(),
            ),
            DataSourceStatus(
                id="pollinations",
                name="Pollinations API",
                status="available",
                indicators=["Diagram Generation"],
                last_check=datetime.now().isoformat(),
            ),
        ]

        return [
            {
                "id": s.id,
                "name": s.name,
                "status": s.status,
                "indicators": s.indicators,
                "last_check": s.last_check,
            }
            for s in sources
        ]

    async def close(self):
        """Clean up resources."""
        await self._data_fetcher.close()


# =============================================================================
# Singleton Instance
# =============================================================================

_visual_intelligence_engine: Optional[VisualIntelligenceEngine] = None


def get_visual_intelligence_engine() -> VisualIntelligenceEngine:
    """Get singleton VisualIntelligenceEngine instance."""
    global _visual_intelligence_engine
    if _visual_intelligence_engine is None:
        _visual_intelligence_engine = VisualIntelligenceEngine()
    return _visual_intelligence_engine
