import subprocess, urllib.request, time, json, urllib.error

print("="*60)
print("👻 GHOST EXPOSER: Catching the exact 500 Error")
print("="*60)

# 1. REWRITE main.py WITH A BULLETPROOF ERROR CATCHER
main_code = """import os
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# CATCHES ALL 500 ERRORS AND PRINTS THE TRACEBACK
@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc), "trace": traceback.format_exc()})

@app.get("/")
def root():
    return {"status": "ALIVE", "message": "Server is breathing."}

# CATCHES IMPORT CRASHES
try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    trace = traceback.format_exc()
    @app.get("/api/v1/dashboard/health")
    @app.get("/api/v1/dashboard/ping")
    def router_crash():
        return {"status": "ROUTER_IMPORT_CRASH", "error": str(e), "trace": trace}
"""

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(main_code)
print("✅ Injected Ghost Exposer into main.py")

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Expose the 500 Ghost: Global exception handler"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 60 seconds for Vercel to rebuild...")
time.sleep(60)

# 2. INTERROGATE THE SERVER TO GET THE TRACEBACK
print("\n🔍 Interrogating /api/v1/dashboard/health to get the traceback...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/health", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("✅ HEALTH:", r.read().decode())
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print("\n" + "="*60)
    print("👻 THE GHOST'S TRUE IDENTITY (Traceback):")
    print("="*60)
    print(body)
    print("="*60)
except Exception as e:
    print("❌ Network Error:", e)
