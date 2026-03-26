"""
Unified Intelligence Models

Request/Response models for the Unified Adaptive Intelligence Layer.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


# =============================================================================
# Enums
# =============================================================================

class CapabilityType(str, Enum):
    """Types of intelligence capabilities."""
    REASONING = "reasoning"          # Expert multi-agent analysis
    TOOLS = "tools"                  # External data fetching and tool usage
    VISUALS = "visuals"              # Chart and diagram generation
    MAP_INTELLIGENCE = "map"         # Geographic visualization

class QueryComplexity(str, Enum):
    """Complexity levels for query assessment."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


# =============================================================================
# Request Models
# =============================================================================

class UnifiedIntelligenceRequest(BaseModel):
    """Request model for unified intelligence analysis."""
    query: str = Field(..., description="Natural language query", min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    conversation_id: Optional[str] = Field(
        None,
        description="Client conversation id for maintaining assistant memory"
    )
    conversation_history: List["ConversationMessage"] = Field(
        default_factory=list,
        description="Recent conversation history for chat-style follow-ups"
    )
    forced_capabilities: Optional[List[CapabilityType]] = Field(
        None,
        description="Force specific capabilities (overrides auto-detection)"
    )
    max_processing_time: Optional[float] = Field(
        30.0,
        description="Maximum processing time in seconds"
    )
    include_debug_info: bool = Field(
        False,
        description="Include capability activation details"
    )


# =============================================================================
# Capability Configuration
# =============================================================================

@dataclass
class CapabilitySet:
    """Configuration for which capabilities to activate."""
    reasoning: bool = False
    tools: bool = False
    visuals: bool = False
    map_intelligence: bool = False

    def to_list(self) -> List[str]:
        """Convert to list of active capability names."""
        active = []
        if self.reasoning:
            active.append("reasoning")
        if self.tools:
            active.append("tools")
        if self.visuals:
            active.append("visuals")
        if self.map_intelligence:
            active.append("map")
        return active

    def count(self) -> int:
        """Count number of active capabilities."""
        return len(self.to_list())


# =============================================================================
# Query Assessment
# =============================================================================

@dataclass
class QueryAssessment:
    """Assessment of query characteristics for capability selection."""
    complexity: QueryComplexity
    domains: List[str]
    has_geographic_entities: bool
    has_data_indicators: bool
    has_time_dimension: bool
    requires_external_data: bool
    requires_multi_perspective: bool
    confidence: float

    # Suggested capabilities
    suggested_capabilities: CapabilitySet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "complexity": self.complexity.value,
            "domains": self.domains,
            "has_geographic_entities": self.has_geographic_entities,
            "has_data_indicators": self.has_data_indicators,
            "has_time_dimension": self.has_time_dimension,
            "requires_external_data": self.requires_external_data,
            "requires_multi_perspective": self.requires_multi_perspective,
            "confidence": self.confidence,
            "suggested_capabilities": self.suggested_capabilities.to_list(),
        }


# =============================================================================
# Capability-Specific Results
# =============================================================================

class ConversationMessage(BaseModel):
    """Minimal conversation message for unified chat memory."""
    role: Literal["system", "user", "assistant"] = "user"
    content: str = Field(..., min_length=1)
    timestamp: Optional[str] = None


@dataclass
class AssistantResponseSection:
    """Structured assistant response block for frontend rendering."""
    title: str
    content: str
    tone: str = "default"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "tone": self.tone,
        }


@dataclass
class AssistantResponsePayload:
    """Conversation-friendly assistant response payload."""
    title: str
    executive_brief: str
    key_takeaways: List[str]
    next_actions: List[str]
    suggested_follow_ups: List[str]
    memory_summary: str
    response_blocks: List[AssistantResponseSection]
    artifact_overview: Dict[str, Any]
    response_mode: str = "conversational_assistant"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "executive_brief": self.executive_brief,
            "key_takeaways": self.key_takeaways,
            "next_actions": self.next_actions,
            "suggested_follow_ups": self.suggested_follow_ups,
            "memory_summary": self.memory_summary,
            "response_blocks": [block.to_dict() for block in self.response_blocks],
            "artifact_overview": self.artifact_overview,
            "response_mode": self.response_mode,
        }


@dataclass
class ReasoningResult:
    """Results from reasoning capability (Expert Agents)."""
    executive_summary: str
    analysis: str
    key_findings: List[str]
    confidence: float
    expert_agents_used: List[str]
    consensus_achieved: bool
    processing_time_ms: float
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    strategic_recommendations: List[str] = field(default_factory=list)
    uncertainty_factors: List[str] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "analysis": self.analysis,
            "key_findings": self.key_findings,
            "confidence": self.confidence,
            "expert_agents_used": self.expert_agents_used,
            "consensus_achieved": self.consensus_achieved,
            "risk_factors": self.risk_factors,
            "strategic_recommendations": self.strategic_recommendations,
            "uncertainty_factors": self.uncertainty_factors,
            "timeline": self.timeline,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class ToolsResult:
    """Results from tools capability (Strategic Agent)."""
    tools_executed: List[str]
    data_sources: List[str]
    tool_outputs: Dict[str, Any]
    insights: List[str]
    processing_time_ms: float
    unavailable_tools: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tools_executed": self.tools_executed,
            "data_sources": self.data_sources,
            "tool_outputs": self.tool_outputs,
            "insights": self.insights,
            "unavailable_tools": self.unavailable_tools,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class VisualsResult:
    """Results from visuals capability (Visual Intelligence)."""
    charts: List[Dict[str, Any]]
    diagrams: List[Dict[str, Any]]
    chart_insights: List[str]
    diagram_insights: List[str]
    processing_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "charts": self.charts,
            "diagrams": self.diagrams,
            "chart_insights": self.chart_insights,
            "diagram_insights": self.diagram_insights,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class MapIntelligenceResult:
    """Results from map intelligence capability."""
    commands: List[Dict[str, Any]]
    affected_regions: List[str]
    markers: List[Dict[str, Any]]
    routes: List[Dict[str, Any]]
    heatmap_data: Optional[Dict[str, float]]
    processing_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commands": self.commands,
            "affected_regions": self.affected_regions,
            "markers": self.markers,
            "routes": self.routes,
            "heatmap_data": self.heatmap_data,
            "processing_time_ms": self.processing_time_ms,
        }


# =============================================================================
# Unified Response
# =============================================================================

@dataclass
class UnifiedIntelligenceResult:
    """Complete unified intelligence result."""
    query_id: str
    conversation_id: str
    query: str
    assessment: QueryAssessment
    unified_summary: str
    assistant_response: AssistantResponsePayload
    confidence_score: float
    data_sources_used: List[str]
    capabilities_activated: List[str]
    capability_statuses: List[Dict[str, Any]]
    total_processing_time_ms: float
    timestamp: str

    # Capability-specific results (only populated if capability was activated)
    reasoning: Optional[ReasoningResult] = None
    tools: Optional[ToolsResult] = None
    visuals: Optional[VisualsResult] = None
    map_intelligence: Optional[MapIntelligenceResult] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "conversation_id": self.conversation_id,
            "query": self.query,
            "assessment": self.assessment.to_dict(),
            "reasoning": self.reasoning.to_dict() if self.reasoning else None,
            "tools": self.tools.to_dict() if self.tools else None,
            "visuals": self.visuals.to_dict() if self.visuals else None,
            "map_intelligence": self.map_intelligence.to_dict() if self.map_intelligence else None,
            "unified_summary": self.unified_summary,
            "assistant_response": self.assistant_response.to_dict(),
            "confidence_score": self.confidence_score,
            "data_sources_used": self.data_sources_used,
            "capabilities_activated": self.capabilities_activated,
            "capability_statuses": self.capability_statuses,
            "total_processing_time_ms": self.total_processing_time_ms,
            "timestamp": self.timestamp,
        }


# =============================================================================
# Response Models (Pydantic for API)
# =============================================================================

class UnifiedIntelligenceResponse(BaseModel):
    """API response model for unified intelligence."""
    status: str
    query_id: str
    conversation_id: str
    query: str

    # Assessment
    assessment: Dict[str, Any]

    # Results
    reasoning: Optional[Dict[str, Any]] = None
    tools: Optional[Dict[str, Any]] = None
    visuals: Optional[Dict[str, Any]] = None
    map_intelligence: Optional[Dict[str, Any]] = None

    # Unified output
    unified_summary: str
    assistant_response: Dict[str, Any]
    confidence_score: float
    data_sources_used: List[str]

    # Metadata
    capabilities_activated: List[str]
    capability_statuses: List[Dict[str, Any]]
    total_processing_time_ms: float
    timestamp: str

    # Debug info (optional)
    debug: Optional[Dict[str, Any]] = None


# =============================================================================
# Capability Execution Status
# =============================================================================

@dataclass
class CapabilityExecutionStatus:
    """Status of capability execution for error handling."""
    capability: CapabilityType
    success: bool
    error_message: Optional[str] = None
    fallback_used: bool = False
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability": self.capability.value,
            "success": self.success,
            "error_message": self.error_message,
            "fallback_used": self.fallback_used,
            "execution_time_ms": self.execution_time_ms,
        }


UnifiedIntelligenceRequest.model_rebuild()
