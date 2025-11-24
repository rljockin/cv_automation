#!/usr/bin/env python3
"""
CV Automation REST API
FastAPI application for programmatic access to CV processing
"""

import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logger import setup_logger
from src.core.database import get_database

logger = setup_logger(__name__)


# ============================================================================
# LIFESPAN EVENTS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting CV Automation API...")
    
    # Initialize database
    db = get_database()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CV Automation API...")


# ============================================================================
# APPLICATION
# ============================================================================

app = FastAPI(
    title="CV Automation API",
    description="REST API for automated CV to Resumé conversion",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else "An error occurred"
        }
    )


# ============================================================================
# ROUTES
# ============================================================================

# Import and include routers
from API.routes import health, upload, status, results, batch

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(status.router, prefix="/api", tags=["Status"])
app.include_router(results.router, prefix="/api", tags=["Results"])
app.include_router(batch.router, prefix="/api", tags=["Batch"])


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "CV Automation API",
        "version": "0.2.0",
        "documentation": "/api/docs",
        "health": "/api/health"
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting CV Automation API on port {port}")
    
    uvicorn.run(
        "API.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level="info"
    )

