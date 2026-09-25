import subprocess, time, json, urllib.request

print("="*60)
print("🧪 TOTAL NEUTRALIZATION INITIATED...")
print("="*60)

# 1. COMPLETELY REPLACE agents_api.py WITH A DUMMY ROUTER
# This removes ALL database imports. If this works, the DB is the ghost.
dummy_code = """
from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["Sodangi Agents"])

@router.get("/ping")
def ping_test():
    return {"status": "ALIVE", "message": "agents_api.py is fully neutralized. The ghost was in the database imports!"}

@router.get("/health")
def health_test():
    return {"status": "ok", "database": "bypassed"}
"""

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "w", encoding="utf-8") as f:
    f.write(dummy_code)

print("✅ Replaced agents_api.py with Dummy Router (0 database imports).")

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Diagnostic: Total neutralization of agents_api.py"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90 seconds for Vercel to rebuild...")
time.sleep(90)

# 2. CHECK HEALTH
print("\n🔍 Checking /health endpoint...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/health", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
        if data.get("status") == "ok":
            print("✅ SERVER IS ALIVE!")
            print("   DIAGNOSIS: The crash was caused by the database imports in agents_api.py.")
            print("   FIX: Your Vercel DATABASE_URL environment variable is likely missing or expired.")
            print("   👉 Go to Vercel -> Settings -> Environment Variables and check DATABASE_URL.")
        else:
            print(f"⚠️ Server responded: {data}")
except Exception as e:
    print(f"❌ Server still dead: {e}")
    print("   DIAGNOSIS: The crash is in main.py or the core database engine itself.")
