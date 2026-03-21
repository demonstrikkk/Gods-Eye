from fastapi import APIRouter
from app.api.endpoints import intelligence, outreach, ingestion, data

api_router = APIRouter()

# Core Intelligence Engine (NL Query, Executive KPIs)
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["Intelligence Engine"])

# Civic Data API (Constituencies, Booths, Citizens, Schemes, Workers, Projects)
api_router.include_router(data.router, prefix="/data", tags=["Civic Data Engine"])

# Outreach Actions
api_router.include_router(outreach.router, prefix="/actions", tags=["Hyperlocal Outreach"])

# Data Ingestion Pipeline
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Data Processing Pipeline"])
