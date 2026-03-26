"""
Visual Intelligence Models

Pydantic models and enums for the Visual + Data + Map Intelligence Engine.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid


# =============================================================================
# Enums
# =============================================================================

class DomainType(str, Enum):
    """Domain classification for queries."""
    ECONOMICS = "economics"
    GEOPOLITICS = "geopolitics"
    CLIMATE = "climate"
    INFRASTRUCTURE = "infrastructure"
    DEMOGRAPHICS = "demographics"
    DEFENSE = "defense"
    TRADE = "trade"
    TECHNOLOGY = "technology"
    ENERGY = "energy"
    AGRICULTURE = "agriculture"
    HEALTH = "health"
    SPACE = "space"
    LOGISTICS = "logistics"
    DISASTER = "disaster"


class ChartType(str, Enum):
    """Types of charts that can be generated."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    RADAR = "radar"
    DOUGHNUT = "doughnut"
    AREA = "area"
    HORIZONTAL_BAR = "horizontalBar"


class DiagramType(str, Enum):
    """Types of diagrams that can be generated."""
    WORKFLOW = "workflow"
    CAUSE_EFFECT = "cause_effect"
    PIPELINE = "pipeline"
    INFRASTRUCTURE = "infrastructure"
    NETWORK = "network"
    PROCESS = "process"
    HIERARCHY = "hierarchy"
    COMPARISON = "comparison"


class IntentType(str, Enum):
    """Types of query intents."""
    COMPARISON = "comparison"
    TREND = "trend"
    FORECAST = "forecast"
    WHAT_IF = "what_if"
    ANALYSIS = "analysis"
    CORRELATION = "correlation"
    IMPACT = "impact"
    SIMULATION = "simulation"
    OVERVIEW = "overview"


class MapFeatureType(str, Enum):
    """Types of map features that can be generated."""
    MARKERS = "markers"
    HEATMAP = "heatmap"
    ROUTES = "routes"
    POLYGONS = "polygons"
    HIGHLIGHT = "highlight"
    FOCUS = "focus"
    OVERLAY = "overlay"


class DataSourceType(str, Enum):
    """Available data sources."""
    WORLD_BANK = "world_bank"
    DATA_COMMONS = "data_commons"
    INTERNAL_OSINT = "internal_osint"
    NASA_FIRMS = "nasa_firms"
    USGS_EARTHQUAKE = "usgs_earthquake"
    GDELT = "gdelt"
    IMF = "imf"
    UN_DATA = "un_data"


# =============================================================================
# Dataclasses for Internal Use
# =============================================================================

@dataclass
class TimeRange:
    """Time range for data queries."""
    start_year: int
    end_year: int

    def to_dict(self) -> Dict[str, int]:
        return {"start_year": self.start_year, "end_year": self.end_year}


@dataclass
class GeoEntity:
    """Geographic entity extracted from query."""
    name: str
    entity_type: str  # country, region, city, continent
    iso_code: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "iso_code": self.iso_code,
            "lat": self.lat,
            "lng": self.lng,
            "confidence": self.confidence,
        }


@dataclass
class DataSet:
    """A dataset fetched from an external source."""
    source: DataSourceType
    indicator: str
    values: List[Dict[str, Any]]  # [{year, value, country}, ...]
    unit: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source.value if isinstance(self.source, DataSourceType) else self.source,
            "indicator": self.indicator,
            "values": self.values,
            "unit": self.unit,
            "metadata": self.metadata,
        }


@dataclass
class ChartData:
    """Data structure for chart generation."""
    labels: List[str]
    datasets: List["ChartDataset"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "labels": self.labels,
            "datasets": [ds.to_dict() for ds in self.datasets],
        }


@dataclass
class ChartDataset:
    """A single dataset within a chart."""
    label: str
    values: List[float]
    color: str = "#06b6d4"  # cyan-500
    border_color: Optional[str] = None
    fill: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "data": self.values,
            "backgroundColor": self.color,
            "borderColor": self.border_color or self.color,
            "fill": self.fill,
        }


@dataclass
class ChartOptions:
    """Options for chart generation."""
    title: str
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    responsive: bool = True
    legend_display: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "x_axis_label": self.x_axis_label,
            "y_axis_label": self.y_axis_label,
            "responsive": self.responsive,
            "legend_display": self.legend_display,
        }


@dataclass
class DiagramContext:
    """Context for diagram generation."""
    description: str
    elements: List[str]
    relationships: List[str] = field(default_factory=list)
    style: str = "professional"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "elements": self.elements,
            "relationships": self.relationships,
            "style": self.style,
        }


@dataclass
class MapMarker:
    """A marker to place on the map."""
    lat: float
    lng: float
    label: str
    marker_type: str = "default"
    description: Optional[str] = None
    color: str = "#06b6d4"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lat": self.lat,
            "lng": self.lng,
            "label": self.label,
            "marker_type": self.marker_type,
            "description": self.description,
            "color": self.color,
        }


@dataclass
class MapRoute:
    """A route/connection on the map."""
    from_lat: float
    from_lng: float
    to_lat: float
    to_lng: float
    route_type: str = "trade"
    label: Optional[str] = None
    color: str = "#22c55e"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_lat": self.from_lat,
            "from_lng": self.from_lng,
            "to_lat": self.to_lat,
            "to_lng": self.to_lng,
            "route_type": self.route_type,
            "label": self.label,
            "color": self.color,
        }


# =============================================================================
# Output Dataclasses
# =============================================================================

@dataclass
class ParsedIntent:
    """Structured intent extracted from user query."""
    query_id: str
    raw_query: str
    countries: List[str]
    regions: List[str]
    cities: List[str]
    primary_domain: DomainType
    secondary_domains: List[DomainType]
    domain_confidence: Dict[str, float]
    intent_type: IntentType
    time_range: Optional[TimeRange]
    requires_chart: bool
    chart_type: Optional[ChartType]
    requires_diagram: bool
    diagram_type: Optional[DiagramType]
    requires_map: bool
    map_features: List[MapFeatureType]
    indicators: List[str]
    comparison_entities: List[str]
    parse_confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "raw_query": self.raw_query,
            "countries": self.countries,
            "regions": self.regions,
            "cities": self.cities,
            "primary_domain": self.primary_domain.value if isinstance(self.primary_domain, DomainType) else self.primary_domain,
            "secondary_domains": [d.value if isinstance(d, DomainType) else d for d in self.secondary_domains],
            "domain_confidence": self.domain_confidence,
            "intent_type": self.intent_type.value if isinstance(self.intent_type, IntentType) else self.intent_type,
            "time_range": self.time_range.to_dict() if self.time_range else None,
            "requires_chart": self.requires_chart,
            "chart_type": self.chart_type.value if isinstance(self.chart_type, ChartType) else self.chart_type,
            "requires_diagram": self.requires_diagram,
            "diagram_type": self.diagram_type.value if isinstance(self.diagram_type, DiagramType) else self.diagram_type,
            "requires_map": self.requires_map,
            "map_features": [f.value if isinstance(f, MapFeatureType) else f for f in self.map_features],
            "indicators": self.indicators,
            "comparison_entities": self.comparison_entities,
            "parse_confidence": self.parse_confidence,
        }


@dataclass
class DataFetchResult:
    """Result from data fetch layer."""
    datasets: Dict[str, DataSet]
    sources_used: List[str]
    sources_failed: List[str]
    data_quality_score: float
    time_coverage: Optional[TimeRange]
    geo_coverage: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datasets": {k: v.to_dict() for k, v in self.datasets.items()},
            "sources_used": self.sources_used,
            "sources_failed": self.sources_failed,
            "data_quality_score": self.data_quality_score,
            "time_coverage": self.time_coverage.to_dict() if self.time_coverage else None,
            "geo_coverage": self.geo_coverage,
            "metadata": self.metadata,
        }


@dataclass
class ChartOutput:
    """Output from chart generation."""
    chart_url: str
    chart_type: ChartType
    title: str
    config: Dict[str, Any]
    data_summary: str
    insight: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_url": self.chart_url,
            "chart_type": self.chart_type.value if isinstance(self.chart_type, ChartType) else self.chart_type,
            "title": self.title,
            "config": self.config,
            "data_summary": self.data_summary,
            "insight": self.insight,
        }


@dataclass
class DiagramOutput:
    """Output from diagram generation."""
    image_url: str
    diagram_type: DiagramType
    prompt_used: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_url": self.image_url,
            "diagram_type": self.diagram_type.value if isinstance(self.diagram_type, DiagramType) else self.diagram_type,
            "prompt_used": self.prompt_used,
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass
class MapIntelligenceOutput:
    """Output from map intelligence layer."""
    commands: List[Dict[str, Any]]
    affected_regions: List[str]
    geo_entities: List[GeoEntity]
    markers: List[MapMarker]
    routes: List[MapRoute]
    heatmap_data: Optional[Dict[str, float]] = None
    coordinate_data: Dict[str, Any] = field(default_factory=dict)
    layer_recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commands": self.commands,
            "affected_regions": self.affected_regions,
            "geo_entities": [e.to_dict() for e in self.geo_entities],
            "markers": [m.to_dict() for m in self.markers],
            "routes": [r.to_dict() for r in self.routes],
            "heatmap_data": self.heatmap_data,
            "coordinate_data": self.coordinate_data,
            "layer_recommendations": self.layer_recommendations,
        }


@dataclass
class ChartInsight:
    """Insight about a specific chart."""
    chart_id: str
    trend_description: str
    key_values: List[str]
    notable_patterns: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "trend_description": self.trend_description,
            "key_values": self.key_values,
            "notable_patterns": self.notable_patterns,
        }


@dataclass
class DiagramInsight:
    """Insight about a specific diagram."""
    diagram_id: str
    flow_description: str
    key_elements: List[str]
    relationships: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagram_id": self.diagram_id,
            "flow_description": self.flow_description,
            "key_elements": self.key_elements,
            "relationships": self.relationships,
        }


@dataclass
class MapInsight:
    """Insight about map visualization."""
    geographic_focus: str
    spatial_patterns: List[str]
    regional_highlights: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "geographic_focus": self.geographic_focus,
            "spatial_patterns": self.spatial_patterns,
            "regional_highlights": self.regional_highlights,
        }


@dataclass
class InsightSynthesis:
    """Synthesized insights from all analysis."""
    executive_summary: str
    key_findings: List[str]
    cross_domain_connections: List[str]
    causal_chain: List[str]
    chart_insights: List[ChartInsight]
    diagram_insights: List[DiagramInsight]
    map_insights: Optional[MapInsight]
    recommendations: List[str]
    data_sources: List[str]
    confidence_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "cross_domain_connections": self.cross_domain_connections,
            "causal_chain": self.causal_chain,
            "chart_insights": [i.to_dict() for i in self.chart_insights],
            "diagram_insights": [i.to_dict() for i in self.diagram_insights],
            "map_insights": self.map_insights.to_dict() if self.map_insights else None,
            "recommendations": self.recommendations,
            "data_sources": self.data_sources,
            "confidence_score": self.confidence_score,
        }


@dataclass
class VisualIntelligenceResult:
    """Complete result from visual intelligence processing."""
    query_id: str
    parsed_intent: ParsedIntent
    data_result: DataFetchResult
    charts: List[ChartOutput]
    diagrams: List[DiagramOutput]
    map_output: MapIntelligenceOutput
    insight_synthesis: InsightSynthesis
    processing_time_ms: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "parsed_intent": self.parsed_intent.to_dict(),
            "data_sources": self.data_result.sources_used,
            "data_quality_score": self.data_result.data_quality_score,
            "charts": [c.to_dict() for c in self.charts],
            "diagrams": [d.to_dict() for d in self.diagrams],
            "map_data": self.map_output.to_dict(),
            "insight": self.insight_synthesis.to_dict(),
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp,
        }


# =============================================================================
# Pydantic Request/Response Models
# =============================================================================

class VisualIntelligenceRequest(BaseModel):
    """Request model for visual intelligence analysis."""
    query: str = Field(..., description="Natural language query", min_length=3)
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    force_chart_type: Optional[ChartType] = Field(None, description="Force specific chart type")
    force_diagram_type: Optional[DiagramType] = Field(None, description="Force specific diagram type")
    include_map: bool = Field(True, description="Include map visualization")
    include_expert_analysis: bool = Field(True, description="Include expert agent analysis")


class ChartGenerationRequest(BaseModel):
    """Request model for standalone chart generation."""
    chart_type: ChartType
    data: Dict[str, Any] = Field(..., description="Chart data with labels and datasets")
    title: str = Field(..., description="Chart title")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional chart options")


class DiagramGenerationRequest(BaseModel):
    """Request model for standalone diagram generation."""
    diagram_type: DiagramType
    description: str = Field(..., description="Description of what to diagram")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ParsedIntentResponse(BaseModel):
    """Response model for parsed intent."""
    query_id: str
    raw_query: str
    countries: List[str]
    regions: List[str]
    primary_domain: str
    secondary_domains: List[str]
    intent_type: str
    indicators: List[str]
    requires_chart: bool
    requires_diagram: bool
    requires_map: bool
    parse_confidence: float


class ChartOutputResponse(BaseModel):
    """Response model for chart output."""
    chart_url: str
    chart_type: str
    title: str
    data_summary: str
    insight: Optional[str] = None


class DiagramOutputResponse(BaseModel):
    """Response model for diagram output."""
    image_url: str
    diagram_type: str
    description: str


class MapDataResponse(BaseModel):
    """Response model for map data."""
    commands: List[Dict[str, Any]]
    affected_regions: List[str]
    markers: List[Dict[str, Any]]
    routes: List[Dict[str, Any]]
    heatmap_data: Optional[Dict[str, float]] = None


class InsightResponse(BaseModel):
    """Response model for insights."""
    executive_summary: str
    key_findings: List[str]
    cross_domain_connections: List[str]
    causal_chain: List[str]
    recommendations: List[str]
    confidence_score: float


class VisualIntelligenceResponse(BaseModel):
    """Complete response model for visual intelligence."""
    status: str
    query_id: str
    parsed_intent: ParsedIntentResponse
    data_sources: List[str]
    data_quality_score: float
    charts: List[ChartOutputResponse]
    diagrams: List[DiagramOutputResponse]
    map_data: MapDataResponse
    insight: InsightResponse
    expert_analysis: Optional[Dict[str, Any]] = None
    processing_time_ms: float
    timestamp: str


class DataSourceStatus(BaseModel):
    """Status of a data source."""
    id: str
    name: str
    status: str  # available, limited, unavailable
    indicators: List[str]
    last_check: Optional[str] = None
