"""
Gods-Eye OS — Map Command API Endpoints
AI-driven map visualization commands
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

from app.services.map_command_service import get_map_command_service, CommandType, CommandPriority


router = APIRouter(prefix="/map", tags=["Map Commands"])


# ─────────────────────────────────────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────────────────────────────────────

class HighlightCommandRequest(BaseModel):
    country_ids: List[str] = Field(..., description="List of country IDs to highlight")
    color: str = Field("#3b82f6", description="Highlight color")
    pulse: bool = Field(True, description="Enable pulse animation")
    description: str = Field("Highlight countries", description="Command description")
    source: str = Field("user", description="Command source")
    priority: CommandPriority = Field("medium", description="Command priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RouteCommandRequest(BaseModel):
    from_country: str = Field(..., description="Origin country ID")
    to_country: str = Field(..., description="Destination country ID")
    route_type: str = Field("trade", description="Route type")
    color: str = Field("#10b981", description="Route color")
    weight: int = Field(3, description="Route line weight")
    description: str = Field("Draw route", description="Command description")
    source: str = Field("user", description="Command source")
    priority: CommandPriority = Field("medium", description="Command priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class HeatmapCommandRequest(BaseModel):
    data_points: List[Dict[str, Any]] = Field(..., description="Heatmap data points")
    metric: str = Field(..., description="Metric being mapped")
    color_scale: str = Field("red", description="Color scale")
    description: str = Field("Display heatmap", description="Command description")
    source: str = Field("user", description="Command source")
    priority: CommandPriority = Field("medium", description="Command priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FocusCommandRequest(BaseModel):
    country_id: str = Field(..., description="Country ID to focus on")
    zoom_level: int = Field(5, description="Zoom level")
    duration_ms: int = Field(1000, description="Animation duration")
    description: str = Field("Focus on region", description="Command description")
    source: str = Field("user", description="Command source")
    priority: CommandPriority = Field("high", description="Command priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class MarkerCommandRequest(BaseModel):
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    marker_type: str = Field(..., description="Marker type")
    label: str = Field(..., description="Marker label")
    color: str = Field("#f59e0b", description="Marker color")
    description: str = Field("Place marker", description="Command description")
    source: str = Field("user", description="Command source")
    priority: CommandPriority = Field("medium", description="Command priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class OverlayCommandRequest(BaseModel):
    overlay_type: str = Field(..., description="Overlay type")
    overlay_data: Dict[str, Any] = Field(..., description="Overlay data")
    description: str = Field("Display overlay", description="Command description")
    source: str = Field("user", description="Command source")
    priority: CommandPriority = Field("medium", description="Command priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/command/highlight", response_model=Dict[str, Any])
async def create_highlight_command(request: HighlightCommandRequest):
    """Create a command to highlight countries on the map"""
    service = get_map_command_service()
    command = service.create_highlight_command(
        country_ids=request.country_ids,
        color=request.color,
        pulse=request.pulse,
        description=request.description,
        source=request.source,
        priority=request.priority,
        metadata=request.metadata,
    )
    return {"status": "success", "data": command.to_dict()}


@router.post("/command/route", response_model=Dict[str, Any])
async def create_route_command(request: RouteCommandRequest):
    """Create a command to draw a route between countries"""
    service = get_map_command_service()
    command = service.create_route_command(
        from_country=request.from_country,
        to_country=request.to_country,
        route_type=request.route_type,
        color=request.color,
        weight=request.weight,
        description=request.description,
        source=request.source,
        priority=request.priority,
        metadata=request.metadata,
    )
    return {"status": "success", "data": command.to_dict()}


@router.post("/command/heatmap", response_model=Dict[str, Any])
async def create_heatmap_command(request: HeatmapCommandRequest):
    """Create a command to display a heatmap"""
    service = get_map_command_service()
    command = service.create_heatmap_command(
        data_points=request.data_points,
        metric=request.metric,
        color_scale=request.color_scale,
        description=request.description,
        source=request.source,
        priority=request.priority,
        metadata=request.metadata,
    )
    return {"status": "success", "data": command.to_dict()}


@router.post("/command/focus", response_model=Dict[str, Any])
async def create_focus_command(request: FocusCommandRequest):
    """Create a command to focus the map on a specific country"""
    service = get_map_command_service()
    command = service.create_focus_command(
        country_id=request.country_id,
        zoom_level=request.zoom_level,
        duration_ms=request.duration_ms,
        description=request.description,
        source=request.source,
        priority=request.priority,
        metadata=request.metadata,
    )
    return {"status": "success", "data": command.to_dict()}


@router.post("/command/marker", response_model=Dict[str, Any])
async def create_marker_command(request: MarkerCommandRequest):
    """Create a command to place a custom marker"""
    service = get_map_command_service()
    command = service.create_marker_command(
        lat=request.lat,
        lng=request.lng,
        marker_type=request.marker_type,
        label=request.label,
        color=request.color,
        description=request.description,
        source=request.source,
        priority=request.priority,
        metadata=request.metadata,
    )
    return {"status": "success", "data": command.to_dict()}


@router.post("/command/overlay", response_model=Dict[str, Any])
async def create_overlay_command(request: OverlayCommandRequest):
    """Create a command for a custom data overlay"""
    service = get_map_command_service()
    command = service.create_overlay_command(
        overlay_type=request.overlay_type,
        overlay_data=request.overlay_data,
        description=request.description,
        source=request.source,
        priority=request.priority,
        metadata=request.metadata,
    )
    return {"status": "success", "data": command.to_dict()}


@router.get("/commands", response_model=Dict[str, Any])
async def get_all_commands():
    """Get all active map commands"""
    service = get_map_command_service()
    commands = service.get_all_commands()
    return {"status": "success", "data": commands, "count": len(commands)}


@router.get("/commands/{command_id}", response_model=Dict[str, Any])
async def get_command(command_id: str):
    """Get a specific command by ID"""
    service = get_map_command_service()
    command = service.get_command(command_id)
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    return {"status": "success", "data": command}


@router.get("/commands/type/{command_type}", response_model=Dict[str, Any])
async def get_commands_by_type(command_type: CommandType):
    """Get all commands of a specific type"""
    service = get_map_command_service()
    commands = service.get_commands_by_type(command_type)
    return {"status": "success", "data": commands, "count": len(commands)}


@router.get("/commands/source/{source}", response_model=Dict[str, Any])
async def get_commands_by_source(source: str):
    """Get all commands from a specific source"""
    service = get_map_command_service()
    commands = service.get_commands_by_source(source)
    return {"status": "success", "data": commands, "count": len(commands)}


@router.delete("/commands/{command_id}", response_model=Dict[str, Any])
async def remove_command(command_id: str):
    """Remove a specific command"""
    service = get_map_command_service()
    removed = service.remove_command(command_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Command not found")
    return {"status": "success", "message": "Command removed"}


@router.delete("/commands", response_model=Dict[str, Any])
async def clear_commands(
    command_type: Optional[CommandType] = Query(None, description="Filter by command type"),
    source: Optional[str] = Query(None, description="Filter by source"),
):
    """Clear commands (optionally filtered by type or source)"""
    service = get_map_command_service()
    removed = service.clear_commands(command_type=command_type, source=source)
    return {
        "status": "success",
        "message": f"Cleared {removed} command(s)",
        "removed_count": removed,
    }


@router.get("/summary", response_model=Dict[str, Any])
async def get_command_summary():
    """Get a summary of current map command state"""
    service = get_map_command_service()
    summary = service.get_command_summary()
    return {"status": "success", "data": summary}


@router.get("/history", response_model=Dict[str, Any])
async def get_command_history(limit: int = Query(20, ge=1, le=100, description="Number of commands to return")):
    """Get recent command history"""
    service = get_map_command_service()
    history = service.get_command_history(limit=limit)
    return {"status": "success", "data": history, "count": len(history)}
