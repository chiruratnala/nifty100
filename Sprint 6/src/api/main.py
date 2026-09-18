"""
Nifty 100 Financial Analytics - FastAPI Institutional Backend Engine
Module: src/api/main.py
"""

import logging
import os
import sys
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, "/content")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("api.gateway")

app = FastAPI(
    title="Nifty 100 Institutional Fundamental Intelligence API",
    description="REST backend service providing fundamental analytics, screener filtering, and macro intelligence.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Timing & Logging Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Latency: {duration_ms:.2f}ms")
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response


# Import Routers
from src.api.routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

# Mount Routes under /api/v1
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Companies"])
app.include_router(screener.router, prefix="/api/v1/screener", tags=["Screener"])
app.include_router(sectors.router, prefix="/api/v1/sectors", tags=["Sectors"])
app.include_router(peers.router, prefix="/api/v1/peers", tags=["Peers"])
app.include_router(valuation.router, prefix="/api/v1", tags=["Valuation"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])


@app.get("/", tags=["Root"])
def root():
    """Execute Root routine."""
    return {"service": "Nifty 100 Institutional API", "docs": "/docs", "health": "/api/v1/health"}
