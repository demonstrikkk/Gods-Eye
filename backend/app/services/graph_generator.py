"""
Graph Generation Engine

Generates charts using QuickChart API based on fetched data.
Supports line, bar, pie, scatter, and radar charts.
"""

import json
import urllib.parse
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.models.visual_intelligence import (
    ParsedIntent,
    DataFetchResult,
    ChartOutput,
    ChartType,
    ChartData,
    ChartDataset,
    ChartOptions,
    DomainType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Color Schemes
# =============================================================================

# Color palette for different data series
CHART_COLORS = [
    "#06b6d4",  # cyan-500
    "#8b5cf6",  # violet-500
    "#22c55e",  # green-500
    "#f59e0b",  # amber-500
    "#ef4444",  # red-500
    "#3b82f6",  # blue-500
    "#ec4899",  # pink-500
    "#14b8a6",  # teal-500
]

# Domain-specific colors
DOMAIN_COLORS = {
    DomainType.ECONOMICS: "#22c55e",    # green
    DomainType.GEOPOLITICS: "#ef4444",  # red
    DomainType.CLIMATE: "#06b6d4",      # cyan
    DomainType.DEFENSE: "#6b7280",      # gray
    DomainType.TRADE: "#f59e0b",        # amber
    DomainType.ENERGY: "#f97316",       # orange
    DomainType.DEMOGRAPHICS: "#8b5cf6", # violet
    DomainType.HEALTH: "#ec4899",       # pink
}


# =============================================================================
# Chart Configuration Builder
# =============================================================================

class ChartConfigBuilder:
    """Builds Chart.js configuration for QuickChart."""

    def build_config(
        self,
        chart_type: ChartType,
        data: ChartData,
        options: ChartOptions,
    ) -> Dict[str, Any]:
        """Build Chart.js configuration."""
        config = {
            "type": self._map_chart_type(chart_type),
            "data": {
                "labels": data.labels,
                "datasets": [
                    {
                        "label": ds.label,
                        "data": ds.values,
                        "backgroundColor": self._get_background_colors(chart_type, ds.color, len(ds.values)),
                        "borderColor": ds.border_color or ds.color,
                        "fill": ds.fill,
                        "tension": 0.2 if chart_type == ChartType.LINE else 0,
                    }
                    for ds in data.datasets
                ],
            },
            "options": self._build_options(chart_type, options),
        }

        return config

    def _map_chart_type(self, chart_type: ChartType) -> str:
        """Map ChartType enum to Chart.js type string."""
        mapping = {
            ChartType.LINE: "line",
            ChartType.BAR: "bar",
            ChartType.PIE: "pie",
            ChartType.DOUGHNUT: "doughnut",
            ChartType.SCATTER: "scatter",
            ChartType.RADAR: "radar",
            ChartType.AREA: "line",
            ChartType.HORIZONTAL_BAR: "horizontalBar",
        }
        return mapping.get(chart_type, "bar")

    def _get_background_colors(
        self,
        chart_type: ChartType,
        base_color: str,
        count: int,
    ) -> Any:
        """Get background colors for chart type."""
        if chart_type in [ChartType.PIE, ChartType.DOUGHNUT]:
            # Multiple colors for pie/doughnut
            return CHART_COLORS[:count]
        elif chart_type == ChartType.BAR:
            # Semi-transparent for bars
            return base_color + "cc"  # Add alpha
        else:
            return base_color

    def _build_options(
        self,
        chart_type: ChartType,
        options: ChartOptions,
    ) -> Dict[str, Any]:
        """Build Chart.js options."""
        opts = {
            "responsive": options.responsive,
            "plugins": {
                "title": {
                    "display": True,
                    "text": options.title,
                    "font": {"size": 14, "weight": "bold"},
                    "color": "#e2e8f0",
                },
                "legend": {
                    "display": options.legend_display,
                    "position": "bottom",
                    "labels": {"color": "#94a3b8"},
                },
            },
        }

        # Add scales for applicable chart types
        if chart_type in [ChartType.LINE, ChartType.BAR, ChartType.SCATTER, ChartType.AREA]:
            opts["scales"] = {
                "x": {
                    "title": {
                        "display": bool(options.x_axis_label),
                        "text": options.x_axis_label or "",
                        "color": "#94a3b8",
                    },
                    "ticks": {"color": "#94a3b8"},
                    "grid": {"color": "#334155"},
                },
                "y": {
                    "title": {
                        "display": bool(options.y_axis_label),
                        "text": options.y_axis_label or "",
                        "color": "#94a3b8",
                    },
                    "ticks": {"color": "#94a3b8"},
                    "grid": {"color": "#334155"},
                },
            }

        # Set fill for area charts
        if chart_type == ChartType.AREA:
            opts["elements"] = {"line": {"fill": True}}

        return opts


# =============================================================================
# Graph Generation Engine
# =============================================================================

class GraphGenerationEngine:
    """
    Generates charts using QuickChart API.

    Supports:
    - Line charts (time series, trends)
    - Bar charts (comparisons)
    - Pie charts (composition)
    - Scatter plots (correlations)
    - Radar charts (multi-dimensional)
    """

    QUICKCHART_BASE_URL = "https://quickchart.io/chart"

    def __init__(self):
        self._config_builder = ChartConfigBuilder()

    async def generate_charts_for_data(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> List[ChartOutput]:
        """
        Generate charts based on intent and fetched data.

        Args:
            intent: Parsed intent
            data_result: Fetched data

        Returns:
            List of ChartOutput objects
        """
        charts = []

        if not intent.requires_chart or not data_result.datasets:
            return charts

        chart_type = intent.chart_type or ChartType.BAR

        # Generate a chart for each indicator
        for indicator, dataset in data_result.datasets.items():
            chart_data = self._transform_to_chart_data(
                indicator, dataset, intent, chart_type
            )

            if not chart_data:
                continue

            options = ChartOptions(
                title=self._generate_title(indicator, intent),
                x_axis_label=self._get_x_label(chart_type),
                y_axis_label=indicator,
            )

            chart = await self.generate_chart(chart_type, chart_data, options)
            chart.insight = self._generate_chart_insight(indicator, dataset, intent)
            charts.append(chart)

        return charts

    async def generate_chart(
        self,
        chart_type: ChartType,
        data: ChartData,
        options: ChartOptions,
    ) -> ChartOutput:
        """
        Generate a single chart.

        Args:
            chart_type: Type of chart
            data: Chart data
            options: Chart options

        Returns:
            ChartOutput with URL and metadata
        """
        config = self._config_builder.build_config(chart_type, data, options)

        # Generate QuickChart URL
        chart_url = self._generate_quickchart_url(config)

        # Generate data summary
        data_summary = self._summarize_data(data)

        return ChartOutput(
            chart_url=chart_url,
            chart_type=chart_type,
            title=options.title,
            config=config,
            data_summary=data_summary,
        )

    def _generate_quickchart_url(self, config: Dict[str, Any]) -> str:
        """Generate QuickChart URL from config."""
        # Set background color for dark theme
        config["backgroundColor"] = "#1e293b"

        config_json = json.dumps(config, separators=(",", ":"))
        encoded_config = urllib.parse.quote(config_json)

        return f"{self.QUICKCHART_BASE_URL}?c={encoded_config}&bkg=%231e293b"

    def _transform_to_chart_data(
        self,
        indicator: str,
        dataset: Any,
        intent: ParsedIntent,
        chart_type: ChartType,
    ) -> Optional[ChartData]:
        """Transform fetched data into ChartData format."""
        values = dataset.values
        if not values:
            return None

        if chart_type in [ChartType.LINE, ChartType.AREA]:
            return self._transform_time_series(values, indicator)
        elif chart_type == ChartType.BAR:
            if intent.intent_type.value == "comparison" and len(intent.countries) > 1:
                return self._transform_comparison(values, indicator, intent.countries)
            else:
                return self._transform_time_series(values, indicator)
        elif chart_type == ChartType.PIE:
            return self._transform_pie(values, indicator, intent.countries)
        else:
            return self._transform_time_series(values, indicator)

    def _transform_time_series(
        self,
        values: List[Dict[str, Any]],
        indicator: str,
    ) -> ChartData:
        """Transform data for time series charts."""
        # Group by country
        by_country: Dict[str, List[tuple]] = {}
        for v in values:
            country = v.get("country", "Unknown")
            year = v.get("year")
            value = v.get("value")
            if year and value is not None:
                if country not in by_country:
                    by_country[country] = []
                by_country[country].append((year, value))

        # Sort by year
        for country in by_country:
            by_country[country].sort(key=lambda x: x[0])

        # Get all unique years
        all_years = sorted(set(y for data in by_country.values() for y, _ in data))
        labels = [str(y) for y in all_years]

        # Create datasets
        datasets = []
        for i, (country, data) in enumerate(by_country.items()):
            year_to_value = {y: v for y, v in data}
            data_values = [year_to_value.get(y, 0) for y in all_years]

            datasets.append(ChartDataset(
                label=country,
                values=data_values,
                color=CHART_COLORS[i % len(CHART_COLORS)],
            ))

        return ChartData(labels=labels, datasets=datasets)

    def _transform_comparison(
        self,
        values: List[Dict[str, Any]],
        indicator: str,
        countries: List[str],
    ) -> ChartData:
        """Transform data for comparison bar charts."""
        # Get latest value for each country
        latest_by_country: Dict[str, float] = {}
        for v in values:
            country = v.get("country", "Unknown")
            year = v.get("year", 0)
            value = v.get("value")

            if country in countries and value is not None:
                existing = latest_by_country.get(country)
                if existing is None:
                    latest_by_country[country] = value

        # Ensure order matches requested countries
        labels = [c for c in countries if c in latest_by_country]
        data_values = [latest_by_country[c] for c in labels]

        datasets = [ChartDataset(
            label=indicator,
            values=data_values,
            color=DOMAIN_COLORS.get(DomainType.ECONOMICS, "#22c55e"),
        )]

        return ChartData(labels=labels, datasets=datasets)

    def _transform_pie(
        self,
        values: List[Dict[str, Any]],
        indicator: str,
        countries: List[str],
    ) -> ChartData:
        """Transform data for pie charts."""
        # Get latest value for each country
        latest_by_country: Dict[str, float] = {}
        for v in values:
            country = v.get("country", "Unknown")
            value = v.get("value")
            if value is not None:
                latest_by_country[country] = value

        labels = list(latest_by_country.keys())
        data_values = list(latest_by_country.values())

        datasets = [ChartDataset(
            label=indicator,
            values=data_values,
            color=CHART_COLORS[0],
        )]

        return ChartData(labels=labels, datasets=datasets)

    def _generate_title(self, indicator: str, intent: ParsedIntent) -> str:
        """Generate chart title."""
        if len(intent.countries) == 1:
            return f"{intent.countries[0]} - {indicator}"
        elif len(intent.countries) > 1:
            if intent.intent_type.value == "comparison":
                return f"{indicator} Comparison"
            return f"{indicator} - {', '.join(intent.countries[:3])}"
        return indicator

    def _get_x_label(self, chart_type: ChartType) -> str:
        """Get x-axis label for chart type."""
        if chart_type in [ChartType.LINE, ChartType.AREA]:
            return "Year"
        return ""

    def _summarize_data(self, data: ChartData) -> str:
        """Generate text summary of chart data."""
        if not data.datasets:
            return "No data available"

        summaries = []
        for ds in data.datasets:
            if ds.values:
                avg_val = sum(ds.values) / len(ds.values)
                min_val = min(ds.values)
                max_val = max(ds.values)
                summaries.append(
                    f"{ds.label}: avg={self._format_number(avg_val)}, "
                    f"range={self._format_number(min_val)}-{self._format_number(max_val)}"
                )

        return "; ".join(summaries)

    def _format_number(self, value: float) -> str:
        """Format number for display."""
        if value >= 1e12:
            return f"{value/1e12:.1f}T"
        elif value >= 1e9:
            return f"{value/1e9:.1f}B"
        elif value >= 1e6:
            return f"{value/1e6:.1f}M"
        elif value >= 1e3:
            return f"{value/1e3:.1f}K"
        else:
            return f"{value:.2f}"

    def _generate_chart_insight(
        self,
        indicator: str,
        dataset: Any,
        intent: ParsedIntent,
    ) -> str:
        """Generate insight about the chart."""
        values = dataset.values
        if not values:
            return ""

        # Calculate trend
        by_year = {}
        for v in values:
            year = v.get("year")
            value = v.get("value")
            if year and value:
                by_year[year] = by_year.get(year, 0) + value

        if len(by_year) < 2:
            return f"Showing {indicator} data for {', '.join(intent.countries[:2])}"

        years = sorted(by_year.keys())
        start_val = by_year[years[0]]
        end_val = by_year[years[-1]]

        if start_val > 0:
            change_pct = ((end_val - start_val) / start_val) * 100
            direction = "increased" if change_pct > 0 else "decreased"
            return (
                f"{indicator} has {direction} by {abs(change_pct):.1f}% "
                f"from {years[0]} to {years[-1]}"
            )

        return f"Showing {indicator} trend from {years[0]} to {years[-1]}"


# =============================================================================
# Singleton Instance
# =============================================================================

_graph_engine: Optional[GraphGenerationEngine] = None


def get_graph_generator() -> GraphGenerationEngine:
    """Get singleton GraphGenerationEngine instance."""
    global _graph_engine
    if _graph_engine is None:
        _graph_engine = GraphGenerationEngine()
    return _graph_engine
