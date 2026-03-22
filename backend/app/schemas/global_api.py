from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceStatusItem(BaseModel):
    label: str
    status: str
    count: int


class ProvenanceSummary(BaseModel):
    live_sources: int = 0
    limited_sources: int = 0
    unavailable_sources: int = 0
    fallback_sources: int = 0
    error_sources: int = 0
    total_sources: int = 0
    seeded_context: bool = True
    runtime_state_backed: bool = True
    last_refresh: Optional[str] = None
    country_id: Optional[str] = None
    analysis_mode: Optional[str] = None
    live_source_labels: List[str] = Field(default_factory=list)
    limited_source_labels: List[str] = Field(default_factory=list)
    unavailable_source_labels: List[str] = Field(default_factory=list)


class GlobalOverviewData(BaseModel):
    model_config = ConfigDict(extra="allow")

    provenance: ProvenanceSummary


class GlobalOverviewResponse(BaseModel):
    status: str
    data: GlobalOverviewData


class CountryAnalysisData(BaseModel):
    model_config = ConfigDict(extra="allow")

    country: Dict[str, Any]
    summary: str
    research_brief: str
    evidence_points: List[str]
    source_status: List[SourceStatusItem]
    provenance: ProvenanceSummary


class CountryAnalysisResponse(BaseModel):
    status: str
    data: CountryAnalysisData
