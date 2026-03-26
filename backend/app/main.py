from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import traceback
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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}")
    logging.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": str(exc),
            "code": "INTERNAL_ERROR"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logging.warning(f"Validation error for {request.url}: {errors}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Invalid input",
            "details": errors
        }
    )

from fastapi import HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP Error",
            "message": exc.detail,
            "code": f"HTTP_{exc.status_code}"
        }
    )

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
        "message": "Gods-Eye OS API is operational.",
        "mode": "Sovereign/Air-Gapped" if settings.LOCAL_MODE_ENABLED else "Public Cloud"
    }

@app.get("/")
async def root():
    return {"message": "Welcome to the Gods-Eye OS Backend Services"}
