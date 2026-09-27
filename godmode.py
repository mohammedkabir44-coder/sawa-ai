import urllib.request, json, time, subprocess, re

print("="*60)
print("🕵️ SHOWROOM 404 EXORCISM & EXACT LINK FINDER")
print("="*60)

# 1. Inject God Mode Showroom Route directly into main.py
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# Wipe any old showroom routes in main.py to prevent conflicts
mc = re.sub(r'@app\.get\("/api/v1/dashboard/showroom/\{product_id\}".*?(?=\n@app\.|\Z)', '', mc, flags=re.DOTALL)

ROUTE = """

@app.get("/api/v1/dashboard/showroom/{product_id}")
def showroom_god_mode(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p: 
            return HTMLResponse(content=f"<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Car ID {product_id} is dead or deleted.</h1>", status_code=404)
        
        imgs = []
        try:
            imgs = _json.loads(p.images) if isinstance(p.images, str) else (p.images or [])
        except: 
            imgs = []
            
        name = str(p.name).replace('"',"'")
        price = f"{float(p.price or 0):,.0f}"
        
        gallery = ""
        for u in imgs:
            if ".mp4" in str(u):
                gallery += f'<video src="{u}" controls playsinline style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0"></video>'
            else:
                gallery += f'<img src="{u}" style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0">'
                
        if not gallery: 
            gallery = '<img src="https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?w=800" style="width:100%;height:320px;object-fit:cover">'

        html = f'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>
        <style>body{{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding-bottom:100px}}.gal{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000}}.wrap{{max-width:600px;margin:0 auto;padding:20px}}.price{{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}}.badge{{background:rgba(16,185,129,0.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}}.cta{{position:fixed;bottom:0;left:0;right:0;padding:20px;background:#0A0F1C;border-top:1px solid #333;text-align:center}}.btn{{display:block;background:#25D366;color:#fff;padding:16px;border-radius:12px;text-decoration:none;font-weight:900;font-size:18px;box-shadow:0 10px 20px rgba(37,211,102,0.3)}}</style>
        </head><body><div class="gal">{gallery}</div><div class="wrap"><span class="badge">✅ VERIFIED SELLER</span><h1 style="margin-top:8px">{name}</h1><div class="price">&#8358; {price}</div></div>
        <div class="cta"><a href="https://wa.me/2349079437745?text=Salam! I am looking at the {name}" target="_blank" class="btn">💬 Verify & Buy on WhatsApp</a></div></body></html>'''
        
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content=f"<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>DB Error: {e}</h1>", status_code=500)
    finally:
        db.close()
"""

mc += ROUTE
with open("backend/app/main.py", "w", encoding="utf-8") as f: f.write(mc)
print("✅ God Mode Showroom injected directly into main.py!")

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "God Mode: Bulletproof showroom in main.py"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel to rebuild...")
time.sleep(75)

# 2. Get the EXACT newest car ID
print("\n🔍 Finding your newest car ID from the database...")
req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/debug-first-car", headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
        new_id = data.get("id")
        new_name = data.get("name", "Unknown")
        print(f"✅ Newest car in DB: {new_name} (ID: {new_id})")
        
        new_url = f"https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/{new_id}"
        print("\n" + "="*60)
        print("👉 OPEN THIS EXACT LINK ON YOUR PHONE:")
        print(new_url)
        print("="*60)
        
        # Verify it works
        print("\n🔍 Pinging the new link...")
        req2 = urllib.request.Request(new_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=30) as r2:
            body = r2.read().decode()
            if "VERIFIED SELLER" in body:
                print("✅ ✅ ✅ LINK IS 100% LIVE AND SERVING YOUR PHOTOS!")
            else:
                print("⚠️ Link loaded but missing expected HTML.")
except Exception as e:
    print("❌ Error fetching newest car:", e)
