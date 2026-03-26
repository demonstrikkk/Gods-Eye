"""
Insight Synthesizer

Generates structured insights from multi-modal analysis.
Uses LLM to synthesize cross-domain connections and causal relationships.
"""

import logging
from typing import List, Dict, Any, Optional
import json

from app.models.visual_intelligence import (
    ParsedIntent,
    DataFetchResult,
    ChartOutput,
    DiagramOutput,
    MapIntelligenceOutput,
    InsightSynthesis,
    ChartInsight,
    DiagramInsight,
    MapInsight,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Insight Templates
# =============================================================================

INSIGHT_TEMPLATES = {
    "trend_increase": "{indicator} has shown an upward trend in {countries}, increasing by {change}% over the analysis period.",
    "trend_decrease": "{indicator} has declined in {countries}, decreasing by {change}% over the analysis period.",
    "comparison": "{country1} leads in {indicator} with {value1}, compared to {country2} at {value2}.",
    "correlation": "Analysis suggests a relationship between {factor1} and {factor2} across the examined regions.",
    "causation": "Changes in {cause} appear to have influenced {effect}, particularly in {region}.",
    "impact": "The impact of {event} on {indicator} is evident in {countries}, with measurable effects on {secondary}.",
}

DOMAIN_INSIGHTS = {
    "economics": [
        "Economic indicators suggest {trend} momentum in the analyzed regions.",
        "Fiscal and monetary factors are contributing to {outcome} economic activity.",
        "Trade dynamics and investment flows indicate {pattern} in economic development.",
    ],
    "trade": [
        "Trade flows between {countries} show {pattern} in bilateral commerce.",
        "Export-import dynamics indicate {trend} in trade relationships.",
        "Supply chain integration is {assessment} across the analyzed corridors.",
    ],
    "infrastructure": [
        "Infrastructure development in {countries} shows {trend} in connectivity.",
        "Investment in {type} infrastructure is driving {outcome}.",
        "Logistics efficiency metrics indicate {assessment} transport capacity.",
    ],
    "climate": [
        "Environmental indicators show {trend} in {metric} across {region}.",
        "Climate-related factors are {impact} economic and social systems.",
        "Sustainability metrics suggest {assessment} progress toward targets.",
    ],
    "defense": [
        "Defense capabilities and expenditure in {countries} show {trend}.",
        "Strategic positioning indicates {assessment} regional dynamics.",
        "Military modernization efforts are {progress} across analyzed nations.",
    ],
    "energy": [
        "Energy production and consumption patterns show {trend} in {countries}.",
        "The transition to renewable sources is {progress} in the analyzed regions.",
        "Energy security considerations indicate {assessment} for {region}.",
    ],
}


# =============================================================================
# LLM-Free Insight Synthesizer
# =============================================================================

class InsightSynthesizer:
    """
    Synthesizes insights from multi-modal analysis.

    Uses template-based generation with statistical analysis
    to create structured insights without requiring LLM calls.
    """

    def __init__(self):
        pass

    async def synthesize(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
        charts: List[ChartOutput],
        diagrams: List[DiagramOutput],
        map_output: MapIntelligenceOutput,
    ) -> InsightSynthesis:
        """
        Generate comprehensive insight synthesis.

        Args:
            intent: Parsed intent
            data_result: Fetched data
            charts: Generated charts
            diagrams: Generated diagrams
            map_output: Map visualization data

        Returns:
            InsightSynthesis with structured insights
        """
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            intent, data_result, charts
        )

        # Extract key findings from data
        key_findings = self._extract_key_findings(intent, data_result)

        # Identify cross-domain connections
        cross_domain_connections = self._identify_cross_domain_connections(
            intent, data_result
        )

        # Build causal chain
        causal_chain = self._build_causal_chain(intent, data_result)

        # Generate chart-specific insights
        chart_insights = self._generate_chart_insights(charts, intent)

        # Generate diagram-specific insights
        diagram_insights = self._generate_diagram_insights(diagrams, intent)

        # Generate map-specific insights
        map_insights = self._generate_map_insights(map_output, intent)

        # Generate recommendations
        recommendations = self._generate_recommendations(intent, data_result)

        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            data_result, len(key_findings), len(cross_domain_connections)
        )

        return InsightSynthesis(
            executive_summary=executive_summary,
            key_findings=key_findings,
            cross_domain_connections=cross_domain_connections,
            causal_chain=causal_chain,
            chart_insights=chart_insights,
            diagram_insights=diagram_insights,
            map_insights=map_insights,
            recommendations=recommendations,
            data_sources=data_result.sources_used,
            confidence_score=confidence_score,
        )

    def _generate_executive_summary(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
        charts: List[ChartOutput],
    ) -> str:
        """Generate executive summary."""
        countries_str = ", ".join(intent.countries[:3]) if intent.countries else "the analyzed regions"
        domain = intent.primary_domain.value
        indicators_str = ", ".join(intent.indicators[:2]) if intent.indicators else "key metrics"

        # Analyze data trends
        trend_analysis = self._analyze_trends(data_result)

        summary_parts = [
            f"Analysis of {domain} indicators for {countries_str} reveals "
            f"{trend_analysis['overall_trend']} patterns in {indicators_str}."
        ]

        if trend_analysis["notable_changes"]:
            summary_parts.append(
                f"Notable observations include {trend_analysis['notable_changes']}."
            )

        if intent.intent_type.value == "comparison" and len(intent.countries) >= 2:
            comparison = self._generate_comparison_summary(data_result, intent.countries)
            if comparison:
                summary_parts.append(comparison)

        summary_parts.append(
            f"Data was sourced from {', '.join(data_result.sources_used)} "
            f"with a quality score of {data_result.data_quality_score:.0%}."
        )

        return " ".join(summary_parts)

    def _analyze_trends(self, data_result: DataFetchResult) -> Dict[str, Any]:
        """Analyze trends in the data."""
        overall_trend = "mixed"
        notable_changes = ""

        for indicator, dataset in data_result.datasets.items():
            values = dataset.values
            if not values or len(values) < 2:
                continue

            # Group by country and calculate trends
            by_country = {}
            for v in values:
                country = v.get("country", "Unknown")
                year = v.get("year")
                value = v.get("value")
                if year and value:
                    if country not in by_country:
                        by_country[country] = []
                    by_country[country].append((year, value))

            for country, data in by_country.items():
                if len(data) >= 2:
                    data.sort(key=lambda x: x[0])
                    start_val = data[0][1]
                    end_val = data[-1][1]

                    if start_val > 0:
                        change_pct = ((end_val - start_val) / start_val) * 100
                        if change_pct > 10:
                            overall_trend = "positive growth"
                            notable_changes = (
                                f"{indicator} in {country} increased by {change_pct:.1f}%"
                            )
                        elif change_pct < -10:
                            overall_trend = "declining"
                            notable_changes = (
                                f"{indicator} in {country} decreased by {abs(change_pct):.1f}%"
                            )

        return {
            "overall_trend": overall_trend,
            "notable_changes": notable_changes,
        }

    def _generate_comparison_summary(
        self,
        data_result: DataFetchResult,
        countries: List[str],
    ) -> str:
        """Generate comparison summary for multiple countries."""
        if len(countries) < 2:
            return ""

        for indicator, dataset in data_result.datasets.items():
            latest_by_country = {}
            for v in dataset.values:
                country = v.get("country")
                value = v.get("value")
                if country in countries and value:
                    latest_by_country[country] = value

            if len(latest_by_country) >= 2:
                sorted_countries = sorted(
                    latest_by_country.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                leader = sorted_countries[0]
                runner = sorted_countries[1]

                ratio = leader[1] / runner[1] if runner[1] > 0 else 0

                return (
                    f"In {indicator}, {leader[0]} leads with "
                    f"{self._format_value(leader[1])}, "
                    f"approximately {ratio:.1f}x that of {runner[0]} "
                    f"({self._format_value(runner[1])})."
                )

        return ""

    def _extract_key_findings(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> List[str]:
        """Extract key findings from data."""
        findings = []

        for indicator, dataset in data_result.datasets.items():
            values = dataset.values
            if not values:
                continue

            # Find max and min values
            max_entry = max(values, key=lambda x: x.get("value", 0) if x.get("value") else 0)
            min_entry = min(values, key=lambda x: x.get("value", float("inf")) if x.get("value") else float("inf"))

            if max_entry.get("value") and min_entry.get("value"):
                findings.append(
                    f"Highest {indicator}: {max_entry.get('country')} "
                    f"({self._format_value(max_entry.get('value'))} in {max_entry.get('year')})"
                )

                if len(intent.countries) > 1:
                    findings.append(
                        f"Lowest {indicator}: {min_entry.get('country')} "
                        f"({self._format_value(min_entry.get('value'))} in {min_entry.get('year')})"
                    )

            # Calculate trend for each country
            by_country = {}
            for v in values:
                country = v.get("country", "Unknown")
                year = v.get("year")
                value = v.get("value")
                if year and value:
                    if country not in by_country:
                        by_country[country] = []
                    by_country[country].append((year, value))

            for country, data in by_country.items():
                if len(data) >= 3:
                    data.sort(key=lambda x: x[0])
                    start = data[0][1]
                    end = data[-1][1]
                    if start > 0:
                        change = ((end - start) / start) * 100
                        if abs(change) > 20:
                            direction = "growth" if change > 0 else "decline"
                            findings.append(
                                f"{country} showed {abs(change):.1f}% {direction} "
                                f"in {indicator} over the analysis period"
                            )

        return findings[:6]  # Limit to 6 findings

    def _identify_cross_domain_connections(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> List[str]:
        """Identify connections across domains."""
        connections = []

        # Domain-specific connection patterns
        domain_connections = {
            "economics": [
                "Economic growth correlates with infrastructure investment",
                "Trade volume impacts GDP and employment metrics",
                "Foreign investment influences currency stability",
            ],
            "trade": [
                "Trade agreements affect export-import balance",
                "Logistics efficiency impacts trade competitiveness",
                "Currency fluctuations influence trade dynamics",
            ],
            "infrastructure": [
                "Infrastructure development enables economic growth",
                "Transportation networks affect logistics efficiency",
                "Digital infrastructure supports trade modernization",
            ],
            "energy": [
                "Energy costs influence industrial competitiveness",
                "Energy security affects geopolitical positioning",
                "Renewable transition impacts carbon emissions",
            ],
            "climate": [
                "Climate factors affect agricultural output",
                "Environmental policies influence energy sector",
                "Climate risks impact infrastructure resilience",
            ],
        }

        primary = intent.primary_domain.value
        if primary in domain_connections:
            connections.extend(domain_connections[primary][:2])

        # Add connections based on secondary domains
        for domain in intent.secondary_domains[:2]:
            domain_val = domain.value if hasattr(domain, "value") else domain
            if domain_val in domain_connections:
                conn = domain_connections[domain_val][0]
                if conn not in connections:
                    connections.append(conn)

        return connections[:4]

    def _build_causal_chain(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> List[str]:
        """Build causal chain based on domain."""
        chains = {
            "economics": [
                "Policy decisions → Investment climate",
                "Investment climate → Capital formation",
                "Capital formation → Economic growth",
                "Economic growth → Employment and prosperity",
            ],
            "trade": [
                "Trade agreements → Market access",
                "Market access → Export growth",
                "Export growth → Trade balance improvement",
                "Trade balance → Economic stability",
            ],
            "infrastructure": [
                "Infrastructure investment → Connectivity",
                "Connectivity → Logistics efficiency",
                "Logistics efficiency → Cost reduction",
                "Cost reduction → Competitiveness",
            ],
            "energy": [
                "Energy policy → Production capacity",
                "Production capacity → Energy security",
                "Energy security → Industrial output",
                "Industrial output → Economic growth",
            ],
            "climate": [
                "Emissions reduction → Environmental quality",
                "Environmental quality → Public health",
                "Public health → Productivity",
                "Productivity → Economic output",
            ],
            "space": [
                "Space investment → R&D capability",
                "R&D capability → Technology development",
                "Technology development → Satellite deployment",
                "Satellite deployment → Communication and navigation benefits",
            ],
            "logistics": [
                "Transport infrastructure → Supply chain efficiency",
                "Supply chain efficiency → Delivery speed",
                "Delivery speed → Customer satisfaction",
                "Customer satisfaction → Market competitiveness",
            ],
            "disaster": [
                "Natural event → Infrastructure damage",
                "Infrastructure damage → Economic disruption",
                "Economic disruption → Recovery needs",
                "Recovery needs → Reconstruction investment",
            ],
        }

        domain = intent.primary_domain.value
        return chains.get(domain, chains["economics"])

    def _generate_chart_insights(
        self,
        charts: List[ChartOutput],
        intent: ParsedIntent,
    ) -> List[ChartInsight]:
        """Generate insights for each chart."""
        insights = []

        for i, chart in enumerate(charts):
            insights.append(ChartInsight(
                chart_id=f"chart_{i}",
                trend_description=chart.insight or f"Visualization of {chart.title}",
                key_values=[chart.data_summary],
                notable_patterns=[
                    f"Chart type: {chart.chart_type.value if hasattr(chart.chart_type, 'value') else chart.chart_type}"
                ],
            ))

        return insights

    def _generate_diagram_insights(
        self,
        diagrams: List[DiagramOutput],
        intent: ParsedIntent,
    ) -> List[DiagramInsight]:
        """Generate insights for each diagram."""
        insights = []

        for i, diagram in enumerate(diagrams):
            dtype = diagram.diagram_type.value if hasattr(diagram.diagram_type, "value") else diagram.diagram_type
            insights.append(DiagramInsight(
                diagram_id=f"diagram_{i}",
                flow_description=diagram.description,
                key_elements=diagram.metadata.get("elements", []),
                relationships=diagram.metadata.get("relationships", []),
            ))

        return insights

    def _generate_map_insights(
        self,
        map_output: MapIntelligenceOutput,
        intent: ParsedIntent,
    ) -> Optional[MapInsight]:
        """Generate map visualization insights."""
        if not map_output.affected_regions:
            return None

        geographic_focus = ", ".join(map_output.affected_regions[:3])

        spatial_patterns = [
            f"Analysis covers {len(map_output.affected_regions)} regions",
        ]

        if map_output.routes:
            spatial_patterns.append(
                f"{len(map_output.routes)} trade/logistics routes identified"
            )

        if map_output.markers:
            spatial_patterns.append(
                f"{len(map_output.markers)} key locations marked"
            )

        regional_highlights = []
        for entity in map_output.geo_entities[:3]:
            regional_highlights.append(
                f"{entity.name} ({entity.entity_type})"
            )

        return MapInsight(
            geographic_focus=geographic_focus,
            spatial_patterns=spatial_patterns,
            regional_highlights=regional_highlights,
        )

    def _generate_recommendations(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        domain_recommendations = {
            "economics": [
                "Monitor key economic indicators for trend continuation",
                "Assess policy impacts on growth trajectories",
                "Consider diversification strategies based on comparative analysis",
            ],
            "trade": [
                "Evaluate trade partnership opportunities",
                "Analyze supply chain resilience factors",
                "Consider tariff and regulatory implications",
            ],
            "infrastructure": [
                "Prioritize infrastructure investments with highest ROI",
                "Assess connectivity gaps in the analyzed regions",
                "Consider public-private partnership models",
            ],
            "climate": [
                "Track sustainability metrics against targets",
                "Evaluate climate risk exposure",
                "Consider green transition investment opportunities",
            ],
            "defense": [
                "Assess strategic capability gaps",
                "Monitor regional security dynamics",
                "Consider defense cooperation opportunities",
            ],
        }

        domain = intent.primary_domain.value
        recommendations = domain_recommendations.get(domain, domain_recommendations["economics"])

        # Add data-driven recommendations
        if data_result.data_quality_score < 0.7:
            recommendations.append(
                "Consider supplementing analysis with additional data sources"
            )

        return recommendations[:4]

    def _calculate_confidence(
        self,
        data_result: DataFetchResult,
        num_findings: int,
        num_connections: int,
    ) -> float:
        """Calculate overall confidence score."""
        base_score = data_result.data_quality_score

        # Boost for findings
        finding_boost = min(num_findings * 0.05, 0.15)

        # Boost for connections
        connection_boost = min(num_connections * 0.03, 0.1)

        # Penalty for failed sources
        failure_penalty = len(data_result.sources_failed) * 0.05

        score = base_score + finding_boost + connection_boost - failure_penalty
        return max(0.3, min(0.95, round(score, 2)))

    def _format_value(self, value: float) -> str:
        """Format numeric value for display."""
        if value >= 1e12:
            return f"${value/1e12:.1f}T"
        elif value >= 1e9:
            return f"${value/1e9:.1f}B"
        elif value >= 1e6:
            return f"${value/1e6:.1f}M"
        elif value >= 1e3:
            return f"{value/1e3:.1f}K"
        else:
            return f"{value:.2f}"


# =============================================================================
# Singleton Instance
# =============================================================================

_insight_synthesizer: Optional[InsightSynthesizer] = None


def get_insight_synthesizer() -> InsightSynthesizer:
    """Get singleton InsightSynthesizer instance."""
    global _insight_synthesizer
    if _insight_synthesizer is None:
        _insight_synthesizer = InsightSynthesizer()
    return _insight_synthesizer
