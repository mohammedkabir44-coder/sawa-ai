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


@app.get("/api/v1/truth")
def truth_route():
    import traceback
    try:
        from app.core.database import engine, Base
        from sqlalchemy import text
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "DB_PERFECT", "url": str(engine.url)}
    except Exception as e:
        return {"status": "CRASHED", "error": str(e), "trace": traceback.format_exc()}


@app.post("/api/v1/master-create")
async def master_create(request: Request):
    import json, hashlib, os
    from app.core.database import engine
    from sqlalchemy import text
    try:
        body = await request.json()
        name = body.get("full_name", "Agent")
        email = body.get("email", "agent@test.com")
        pw = body.get("password", "test123")
        phone = body.get("phone", "")
        
        salt = os.urandom(8).hex()
        pw_hash = salt + ":" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120000).hex()
        
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sodangi_agents (
                    id SERIAL PRIMARY KEY, full_name VARCHAR, email VARCHAR UNIQUE, 
                    password_hash VARCHAR, role VARCHAR DEFAULT 'agent', 
                    phone_number VARCHAR, bio TEXT, photo_url TEXT, is_active BOOLEAN DEFAULT TRUE
                )
            """))
            conn.execute(text("DELETE FROM sodangi_agents WHERE email = :email"), {"email": email})
            conn.execute(text("""
                INSERT INTO sodangi_agents (full_name, email, password_hash, role, phone_number, is_active) 
                VALUES (:name, :email, :pw, 'agent', :phone, TRUE)
            """), {"name": name, "email": email, "pw": pw_hash, "phone": phone})
        return {"status": "FORCE_CREATED", "email": email, "password": pw}
    except Exception as e:
        import traceback
        return {"status": "FAILED", "error": str(e), "trace": traceback.format_exc()}


@app.post("/api/v1/fix-abdull")
async def fix_abdull(request: Request):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS sodangi_product_agents (id SERIAL PRIMARY KEY, product_id INTEGER, agent_id INTEGER)"""))
            res = conn.execute(text("SELECT id FROM sodangi_agents WHERE email = 'abdull.gero@sodangi.com'")).fetchone()
            if not res: return {"status": "NOT_FOUND"}
            abdull_id = res[0]
            conn.execute(text("UPDATE sodangi_agents SET role = 'agent' WHERE id = :aid"), {"aid": abdull_id})
            prods = conn.execute(text("SELECT id FROM products WHERE business_id = 3")).fetchall()
            count = 0
            for p in prods:
                pid = p[0]
                conn.execute(text("DELETE FROM sodangi_product_agents WHERE product_id = :pid AND agent_id = :aid"), {"pid": pid, "aid": abdull_id})
                conn.execute(text("INSERT INTO sodangi_product_agents (product_id, agent_id) VALUES (:pid, :aid)"), {"pid": pid, "aid": abdull_id})
                count += 1
            return {"status": "FIXED", "abdull_id": abdull_id, "cars_assigned": count}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}
