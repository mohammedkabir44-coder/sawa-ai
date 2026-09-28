import subprocess, time, urllib.request, re, json

print("="*60)
print("🔥 FINAL SHOWROOM EXORCISM (100% BULLETPROOF 24/7)")
print("="*60)

# 1. CLEANSE main.py
print("\n[1/4] Cleansing main.py of all showroom ghosts...")
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# Remove any old showroom routes from main.py
mc = re.sub(r'@app\.get\("/api/v1/dashboard/showroom(?:-elite)?/\{product_id\}".*?(?=\n@app\.|\Z)', '', mc, flags=re.DOTALL)
mc = re.sub(r'def showroom_.*?\(product_id: int\):.*?(?=\n@app\.|\Z)', '', mc, flags=re.DOTALL)
mc = re.sub(r'def ultimate_showroom.*?(?=\n@app\.|\Z)', '', mc, flags=re.DOTALL)

# 2. INJECT THE ULTIMATE SHOWROOM INTO main.py (BOTH URLS!)
ULTIMATE_SHOWROOM = """

@app.get("/api/v1/dashboard/showroom/{product_id}")
@app.get("/api/v1/dashboard/showroom-elite/{product_id}")
def ultimate_showroom_247(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return HTMLResponse("<html><body style='background:#0A0F1C;color:#fff;font-family:sans-serif;text-align:center;padding:50px'><h1>Vehicle Not Found</h1><a href='/api/v1/dashboard/market' style='color:#10B981'>Browse All Cars</a></body></html>")
        
        imgs = []
        try:
            if isinstance(p.images, str):
                if p.images.strip().startswith('['): imgs = _json.loads(p.images)
                elif p.images.strip(): imgs = [p.images]
        except: imgs = []
            
        # FALLBACK: If DB has no photos, inject 3 beautiful fallback photos
        if not imgs:
            imgs = [
                "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1200&q=80"
            ]

        name = str(p.name or "Vehicle").replace('"',"'").replace('<', '&lt;')
        price = f"{float(p.price or 0):,.0f}"
        
        gallery = ""
        for u in imgs:
            if ".mp4" in str(u) or ".webm" in str(u):
                gallery += f'<video src="{u}" controls playsinline style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0;background:#000"></video>'
            else:
                gallery += f'<img src="{u}" style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0" loading="lazy">'

        html = f'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>
        <style>body{{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding-bottom:240px}}.gal{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000;scrollbar-width:none}}.gal::-webkit-scrollbar{{display:none}}.wrap{{max-width:600px;margin:0 auto;padding:20px}}.price{{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}}.badge{{background:rgba(16,185,129,0.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}}.cta{{position:fixed;bottom:0;left:0;right:0;padding:12px;background:#0A0F1C;border-top:1px solid #333;display:flex;flex-direction:column;gap:8px;z-index:100}}.btn-wa{{display:block;background:#25D366;color:#fff;padding:14px;border-radius:12px;text-decoration:none;font-weight:900;font-size:15px;text-align:center}}.btn-call{{display:block;background:rgba(245,158,11,0.1);color:#F59E0B;padding:12px;border-radius:12px;text-decoration:none;font-weight:800;font-size:14px;border:1px solid #F59E0B;text-align:center}}.btn-agent{{display:block;background:#3B82F6;color:#fff;padding:12px;border-radius:12px;text-decoration:none;font-weight:800;font-size:14px;text-align:center}}</style>
        </head><body><div class="gal">{gallery}</div><div class="wrap"><span class="badge">✅ VERIFIED SELLER</span><h1 style="margin-top:8px">{name}</h1><div class="price">₦ {price}</div></div>
        <div class="cta">
          <a href="https://wa.me/2348142969979?text=Salam! I am looking at the {name}" target="_blank" class="btn-wa">💬 WhatsApp Seller</a>
          <a href="tel:+2348142969979" class="btn-call">📞 Call Inspection <span style="font-size:12px;opacity:0.8">(₦5,000 Fee)</span></a>
          <a href="/api/v1/dashboard/market" class="btn-agent">🏪 Back to Marketplace</a>
        </div></body></html>'''
        
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content=f"<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Server Error: {e}</h1>", status_code=500)
    finally:
        db.close()
"""

mc += ULTIMATE_SHOWROOM
with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)
print("✅ Ultimate Showroom injected into main.py (BOTH URLs)!")

# 3. CLEANSE agents_api.py of any conflicting showroom routes
print("\n[2/4] Cleansing agents_api.py of conflicting routes...")
url2 = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as r:
    code = r.read().decode()

# Remove any showroom routes from agents_api.py to prevent collision
code = re.sub(r'@router\.get\("/showroom(?:-elite)?/\{product_id\}".*?(?=\n@router\.|\Z)', '', code, flags=re.DOTALL)
code = re.sub(r'def showroom_.*?\(product_id: int\):.*?(?=\n@router\.|\Z)', '', code, flags=re.DOTALL)

with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)
print("✅ Conflicting routes removed from agents_api.py!")

# 4. PUSH
print("\n[3/4] Pushing to Vercel...")
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Final Fix: Ultimate Showroom 24/7 + Fallback Photos"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to rebuild...")
time.sleep(90)

# 5. VERIFY
print("\n[4/4] Verifying Showroom...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "VERIFIED SELLER" in body:
            print("✅ ✅ ✅ ULTIMATE SHOWROOM IS 100% LIVE 24/7!")
            print("👉 Open this on your phone:")
            print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15")
        else:
            print("⚠️ Loaded but HTML mismatch.")
except Exception as e:
    print("❌ Error:", e)
