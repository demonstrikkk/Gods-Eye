from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# User / Authentication Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    department: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Region (Hierarchical Geospatial Entity)
class RegionBase(BaseModel):
    name: str = Field(..., description="Name of the state, district, constituency, ward, or booth")
    type: str = Field(..., description="'STATE', 'DISTRICT', 'CONSTITUENCY', 'WARD', 'BOOTH'")
    parent_id: Optional[UUID] = None
    demographics: Dict[str, Any] = {}
    sentiment_score: Optional[float] = None

class RegionResponse(RegionBase):
    id: UUID
    class Config:
        from_attributes = True

# Citizen Validation for Knowledge Graph (Used internally when parsing LLM extractions)
class CitizenGraphNode(BaseModel):
    citizen_id: str
    age_group: str = Field(..., description="E.g., Youth, Senior")
    occupation_group: str
    inferred_income_band: Optional[str] = None
    primary_issue: Optional[str] = None
    sentiment_state: str = Field(..., description="POSITIVE, NEGATIVE, NEUTRAL")

class ActionRecommendation(BaseModel):
    """ Used strictly to validate LLM output for sovereign inference engine """
    action_type: str = Field(..., description="E.g. DISPATCH_WORKER, SEND_AWARENESS_SMS")
    target_region_id: str = Field(..., description="Booth or Ward ID targeted")
    urgency: int = Field(ge=1, le=10, description="1 to 10 Urgency Scale")
    justification_summary: str = Field(..., description="Brief one-line rationale")
    suggested_message: Optional[str] = Field(None, description="Drafted SMS/Notification content if applicable")

class ProjectLog(BaseModel):
    name: str
    location_lat: float
    location_lng: float
    status: str
    budget: float
    before_image_url: Optional[str] = None
    after_image_url: Optional[str] = None

class OutreachCampaign(BaseModel):
    target_segments: List[str]
    region_ids: List[UUID]
    content_template: str
    channel: str = Field(..., description="'SMS', 'WHATSAPP', 'APP'")
