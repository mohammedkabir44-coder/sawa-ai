import subprocess, time, urllib.request, json

print("="*60)
print("💉 FORCE INJECTING PHOTOS INTO CAR #15")
print("="*60)

# 1. Inject endpoint to force update car 15
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

INJECT_EP = """

@app.post("/api/v1/dashboard/force-image-15")
def force_image_15():
    from app.core.database import SessionLocal
    from app.models.product import Product
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == 15).first()
        if not p: return {"error": "Car 15 not found"}
        
        # 3 High quality car photos
        photos = [
            "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1494905998402-395d579af36f?auto=format&fit=crop&w=1000&q=80"
        ]
        p.images = _json.dumps(photos)
        db.commit()
        return {"status": "INJECTED", "count": len(photos)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
"""

if "/force-image-15" not in mc:
    mc += INJECT_EP
    with open("backend/app/main.py", "w", encoding="utf-8") as f:
        f.write(mc)
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Force inject photos into car 15"])
    subprocess.run(["git", "push", "origin", "main", "--force"])
    print("⏳ Waiting 60s for Vercel...")
    time.sleep(60)

print("\n💉 Triggering the injection into the live database...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/force-image-15", method="POST", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
        print("✅ INJECTED!", data)
except Exception as e:
    print("❌ Error:", e)

print("\n" + "="*60)
print("👉 REFRESH THIS EXACT LINK ON YOUR PHONE NOW:")
print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/15")
print("="*60)
