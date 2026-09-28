import urllib.request, json, subprocess, time

print("="*60)
print("🕵️ LIVE SERVER DIAGNOSTIC SCANNER")
print("="*60)

# 1. FORCE A FRESH DEPLOY (in case Vercel is stuck on a cached build)
print("\n[1/3] Forcing fresh deployment...")
fp = "backend/app/main.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    c = f.read()
if "# FORCE DEPLOY" not in c:
    c += "\n# FORCE DEPLOY " + str(time.time()) + "\n"
    with open(fp, "w", encoding="utf-8") as f:
        f.write(c)
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Force fresh Vercel deploy"])
    subprocess.run(["git", "push", "origin", "main", "--force"])
    print("⏳ Pushed! Waiting 60s for Vercel to boot...")
    time.sleep(60)
else:
    print("ℹ️ Already forced.")

# 2. SCAN OPENAPI (The Server's Brain)
print("\n[2/3] Scanning Live Routes (openapi.json)...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/openapi.json", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())
        paths = list(data.get("paths", {}).keys())
        print(f"✅ Server is alive! Found {len(paths)} total routes.")
        showroom_routes = [p for p in paths if "showroom" in p.lower()]
        if showroom_routes:
            print("👉 SHOWROOM ROUTES REGISTERED:")
            for p in showroom_routes: print(f"   - {p}")
        else:
            print("❌ NO SHOWROOM ROUTES FOUND IN OPENAPI!")
            print("   The server does not know about the showroom.")
except Exception as e:
    print(f"❌ Server unreachable: {e}")

# 3. TEST EVERY POSSIBLE URL
print("\n[3/3] Testing Exact URLs...")
urls_to_test = [
    "https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/15",
    "https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15",
    "https://sawa-ai-backend.vercel.app/api/v1/showroom/15",
    "https://sawa-ai-backend.vercel.app/showroom/15"
]
for u in urls_to_test:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode()
            if "VERIFIED SELLER" in body:
                print(f"✅ {u} -> LIVE HTML!")
            elif "Server Error" in body:
                print(f"💥 {u} -> 500 CRASH: {body[:100]}")
            else:
                print(f"⚠️ {u} -> Unknown: {body[:100]}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"❌ {u} -> HTTP {e.code}: {err_body[:100]}")
    except Exception as e:
        print(f"❌ {u} -> Error: {e}")

print("\n" + "="*60)
print("PASTE THIS ENTIRE OUTPUT BACK TO ME!")
print("="*60)
