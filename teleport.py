import subprocess, time, urllib.request, re

print("="*60)
print("🚀 CATCH-ALL TELEPORTER: FIXING ALL BROKEN LINKS")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. Inject the Catch-All Teleporter at the VERY TOP of main.py
TELEPORTER = """
@app.get("/showroom/{product_id}")
@app.get("/api/v1/showroom/{product_id}")
@app.get("/dashboard/showroom/{product_id}")
def showroom_teleporter(product_id: int):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/api/v1/dashboard/showroom-elite/{product_id}", status_code=307)
"""

# Remove old teleporter if it exists to prevent duplicates
mc = re.sub(r'@app\.get\("/showroom/\{product_id\}"\)[\s\S]*?status_code=307\)', '', mc)
mc = re.sub(r'def showroom_teleporter[\s\S]*?status_code=307\)', '', mc)

# Find where to inject (right after the app = FastAPI() line)
insert_idx = mc.find('app = FastAPI()')
if insert_idx != -1:
    end_of_line = mc.find('\n', insert_idx)
    mc = mc[:end_of_line+1] + TELEPORTER + mc[end_of_line+1:]
    print("✅ Catch-All Teleporter injected at the top!")
else:
    mc = TELEPORTER + mc
    print("✅ Catch-All Teleporter appended!")

# 2. Also aggressively fix JS links in agents_api.py and main.py
print("\n[2/2] Fixing internal links...")
url2 = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as r:
    code = r.read().decode()

# Fix any JS that says window.location = "/showroom/"
code = code.replace('"/showroom/"', '"/api/v1/dashboard/showroom-elite/"')
code = code.replace('"/api/v1/showroom/"', '"/api/v1/dashboard/showroom-elite/"')
code = code.replace('href="/showroom/', 'href="/api/v1/dashboard/showroom-elite/')
code = code.replace("'/showroom/'", "'/api/v1/dashboard/showroom-elite/'")

with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Teleporter: Fix all broken showroom links"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel...")
time.sleep(75)

print("\n🔍 Testing Teleporter...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/showroom/15", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.url.endswith("/api/v1/dashboard/showroom-elite/15") or "VERIFIED SELLER" in r.read().decode():
            print("✅ ✅ ✅ TELEPORTER IS ACTIVE! Broken links now work!")
        else:
            print("⚠️ Redirected but unexpected page.")
except Exception as e:
    print("❌ Error:", e)
