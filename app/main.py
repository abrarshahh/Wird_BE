"""FastAPI Application Entrypoint for Wird Quran Engine."""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import async_session_factory, close_db, init_db
from app.services.quran_service import QuranService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler managing application startup and shutdown."""
    print(f"Starting {settings.PROJECT_NAME}...")

    # 1. Initialize database tables if not existing
    await init_db()

    # 2. Warm in-memory Quran cache
    t0 = time.perf_counter()
    async with async_session_factory() as session:
        await QuranService.warm_cache(session)
    warm_time = (time.perf_counter() - t0) * 1000
    print(f"[STARTUP] In-memory Quran cache warmed in {warm_time:.2f} ms")

    yield

    # Clean shutdown
    print("Shutting down database connections...")
    await close_db()
    print("Shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Production-grade, high-performance API service for Quranic reading, "
        "authentic Uthmanic typography, and multi-language translations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Standardized JSON response for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
        },
    )


# Health Check Endpoints
@app.get("/health", tags=["Health"], summary="System Health Check")
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"], summary="API v1 Health Check")
async def health_check():
    """Return service status and cache readiness."""
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "cache_warmed": QuranService.is_warmed(),
    }


# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
