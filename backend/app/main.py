import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Prevent OpenAI crash
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"status": "ALIVE", "message": "Server is breathing."}

# LAZY LOAD ROUTERS (Prevents timeout crashes)
try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    logging.error(f"Router crash: {e}")
    @app.get("/api/v1/dashboard/health")
    def fallback_health():
        return {"status": "crashed", "error": str(e)}
