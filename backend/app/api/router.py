from fastapi import APIRouter
from app.api.endpoints import intelligence, outreach, ingestion, data, map_commands, classified, visual_intelligence, unified_intelligence

api_router = APIRouter()

# Unified Intelligence Engine (Single Entry Point for All AI Capabilities)
# Auto-detects and activates: reasoning, tools, visuals, map intelligence
api_router.include_router(unified_intelligence.router, prefix="/unified", tags=["Unified Intelligence"])

# Core Intelligence Engine (NL Query, Executive KPIs)
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["Intelligence Engine"])

# Civic Data API (Constituencies, Booths, Citizens, Schemes, Workers, Projects)
api_router.include_router(data.router, prefix="/data", tags=["Civic Data Engine"])

# Outreach Actions
api_router.include_router(outreach.router, prefix="/actions", tags=["Hyperlocal Outreach"])

# Data Ingestion Pipeline
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Data Processing Pipeline"])

# Classified local-only ingestion and query pipeline
api_router.include_router(classified.router, prefix="/classified", tags=["Classified Sovereign Pipeline"])

# Map Visualization Commands
api_router.include_router(map_commands.router, tags=["Map Commands"])

# Visual + Data + Map Intelligence Engine
api_router.include_router(visual_intelligence.router, prefix="/visual-intelligence", tags=["Visual Intelligence"])
