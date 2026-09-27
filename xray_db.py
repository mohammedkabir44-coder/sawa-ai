import subprocess, time, urllib.request, json

print("="*60)
print("🔍 DATABASE X-RAY: CHECKING CAR #15 IMAGES")
print("="*60)

# 1. Inject X-Ray endpoint into main.py
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

NEW_DEBUG = """

@app.get("/api/v1/dashboard/debug-car-15")
def debug_car_15():
    from app.core.database import SessionLocal
    from app.models.product import Product
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == 15).first()
        if not p: return {"error": "Car 15 not found"}
        return {
            "id": p.id,
            "name": p.name,
            "images_raw": p.images,
            "images_type": str(type(p.images)),
            "is_json_string": isinstance(p.images, str) and p.images.startswith('[')
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
"""

if "/debug-car-15" not in mc:
    mc += NEW_DEBUG
    with open("backend/app/main.py", "w", encoding="utf-8") as f:
        f.write(mc)
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Debug: X-Ray car 15 images"])
    subprocess.run(["git", "push", "origin", "main", "--force"])
    print("⏳ Waiting 60s for Vercel...")
    time.sleep(60)
else:
    print("ℹ️ X-Ray already exists.")

# 2. Fetch the raw data
print("\nFetching raw database content for car #15...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/debug-car-15", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
        print("\n" + "="*60)
        print("📋 DATABASE X-RAY RESULTS:")
        print("="*60)
        print(json.dumps(data, indent=2))
        print("="*60)
        
        if data.get("images_raw") in [None, "", "[]", "null"]:
            print("\n❌ DIAGNOSIS: The 'images' column in the database is EMPTY.")
            print("   The upload succeeded, but the backend didn't save the URL to the database.")
            print("   FIX: We need to patch the /products/upload endpoint to save the URL.")
        else:
            print("\n✅ DIAGNOSIS: The database HAS the image URLs!")
            print("   The issue is how the Showroom page is parsing them.")
            
except Exception as e:
    print("❌ Error:", e)
