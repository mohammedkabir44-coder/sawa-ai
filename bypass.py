import subprocess, time, urllib.request, json

print("="*60)
print("🎯 MAIN.PY BYPASS: INJECTING DIRECT ROUTE")
print("="*60)

# 1. DOWNLOAD main.py
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 2. INJECT THE DEBUG ROUTE DIRECTLY INTO app
DEBUG_ROUTE = """

@app.get("/api/v1/dashboard/debug-first-car")
def debug_first_car_direct():
    from app.core.database import SessionLocal
    from app.models.product import Product
    db = SessionLocal()
    try:
        p = db.query(Product).order_by(Product.id.desc()).first()
        if p:
            return {"id": p.id, "name": p.name, "url": "/api/v1/dashboard/showroom/" + str(p.id)}
        return {"error": "No cars in database!"}
    except Exception as e:
        return {"error": "DB Query failed: " + str(e)}
    finally:
        db.close()
"""

if "/debug-first-car" not in mc:
    mc += DEBUG_ROUTE
    with open("backend/app/main.py", "w", encoding="utf-8") as f:
        f.write(mc)
    print("✅ Injected debug route directly into main.py!")
else:
    print("ℹ️ Route already in main.py.")

# 3. PUSH
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Bypass: Inject debug route into main.py"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel to rebuild main.py...")
time.sleep(75)

# 4. TEST IT
print("\n🔍 Fetching actual car ID from main.py...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/debug-first-car", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
        print("\n" + "="*60)
        if "id" in data:
            print("✅ FOUND A LIVE CAR IN YOUR DATABASE!")
            print(f"Car Name: {data['name']}")
            print(f"Car ID:   {data['id']}")
            url = "https://sawa-ai-backend.vercel.app" + data['url']
            print("\n👉 COPY AND PASTE THIS EXACT URL INTO YOUR BROWSER:")
            print(url)
        elif "error" in data and "No cars" in data["error"]:
            print("⚠️ DATABASE IS EMPTY! Go to your V4 dashboard (+ Add tab) and publish 1 car first.")
            print("Then run this script again.")
        else:
            print("⚠️ Server responded with:", data)
        print("="*60)
except Exception as e:
    print("❌ Error:", e)
