"""SAWA AI FastAPI application entry point."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

# CRITICAL FIX: Prevent OpenAI from crashing on startup if no API key is set.
# This MUST be above the other imports so the OpenAI library sees it!
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-local-testing-12345"

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.scheduler import run_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the background worker on startup; cancel it on shutdown.

    The worker self-disables under pytest (see app.services.scheduler),
    leaving the existing test-suite untouched.
    """
    worker_task = asyncio.create_task(run_worker())
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS: locked down to the configured origins (no wildcard in production).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch any unhandled exception and return a clean JSON 500.

    Stack traces are logged server-side but never leaked to the client.
    """
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# All API routes are already included via api_router in api.py
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}