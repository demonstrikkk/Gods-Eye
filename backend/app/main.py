from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api.router import api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
import logging

# Configure enterprise logging standards
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Civic Intelligence Operating System for Digital Democracy - Sovereign Module",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Broadened CORS for development and cross-port consistency
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)

from app.services.feed_aggregator import feed_engine
from app.services.runtime_intelligence import runtime_engine

@app.on_event("startup")
async def on_startup():
    feed_engine.start()
    runtime_engine.start()

@app.on_event("shutdown")
async def on_shutdown():
    feed_engine.stop()
    runtime_engine.stop()

app.include_router(api_router, prefix="/api/v1")

class HealthResponse(BaseModel):
    status: str
    message: str
    mode: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "ok", 
        "message": "JanGraph OS API is operational.",
        "mode": "Sovereign/Air-Gapped" if settings.LOCAL_MODE_ENABLED else "Public Cloud"
    }

@app.get("/")
async def root():
    return {"message": "Welcome to the JanGraph OS Backend Services"}
