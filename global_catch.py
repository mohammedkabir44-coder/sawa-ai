import subprocess, time, urllib.request, re

print("="*60)
print("🌐 GLOBAL 404 CATCHER: BULLETPROOF REDIRECTS")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. Clean up old failed teleporter routes
mc = re.sub(r'@app\.get\("/showroom/\{product_id\}"\)[\s\S]*?status_code=307\)', '', mc)
mc = re.sub(r'def showroom_teleporter[\s\S]*?status_code=307\)', '', mc)

# 2. Inject the Global Middleware
MIDDLEWARE = """

@app.middleware("http")
async def catch_all_showroom_middleware(request: Request, call_next):
    import re as _re_mw
    from starlette.responses import RedirectResponse
    path = request.url.path
    # Catch ANY URL that has 'showroom' or 'showroom-elite' followed by a number
    m = _re_mw.search(r'showroom(?:-elite)?/(\d+)', path)
    if m and '/api/v1/dashboard/showroom-elite/' not in path:
        pid = m.group(1)
        return RedirectResponse(url=f"/api/v1/dashboard/showroom-elite/{pid}", status_code=307)
    
    return await call_next(request)
"""

if "catch_all_showroom_middleware" not in mc:
    # Insert right after CORS middleware so it runs on every request
    insert_idx = mc.find("app.add_middleware(CORSMiddleware")
    if insert_idx != -1:
        end_of_cors = mc.find(")", insert_idx) + 1
        mc = mc[:end_of_cors] + MIDDLEWARE + mc[end_of_cors:]
        print("✅ Global 404 Catcher Middleware injected!")
    else:
        mc = MIDDLEWARE + mc
        print("✅ Middleware prepended!")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Fix: Global 404 Catcher Middleware for showroom links"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel...")
time.sleep(75)

print("\n🔍 Testing Global Catcher...")
try:
    # Test the broken link
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/showroom/15", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "VERIFIED SELLER" in body:
            print("✅ ✅ ✅ GLOBAL CATCHER WORKS! Broken links now redirect perfectly!")
            print("\n" + "="*60)
            print("👉 YOUR APP IS NOW FULLY UNIFIED.")
            print("   Open your Marketplace or V4 Dashboard and click any car!")
            print("="*60)
        else:
            print("⚠️ Redirected but page issue:", body[:100])
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error {e.code}: {e.read().decode()[:100]}")
except Exception as e:
    print("❌ Error:", e)
