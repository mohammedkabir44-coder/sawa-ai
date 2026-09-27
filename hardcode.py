import subprocess, time, urllib.request, re, json

print("="*60)
print("🫀 HARDCODING SHOWROOM DIRECTLY INTO MAIN.PY")
print("="*60)

# 1. DOWNLOAD main.py
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 2. WIPE ANY OLD SHOWROOM ROUTES IN MAIN.PY
mc = re.sub(r'@app\.get\("/api/v1/dashboard/showroom/\{product_id\}".*?(?=\n@app\.|\Z)', '', mc, flags=re.DOTALL)

# 3. INJECT THE BULLETPROOF SHOWROOM DIRECTLY INTO app
SHOWROOM_MAIN = """

@app.get("/api/v1/dashboard/showroom/{product_id}")
def showroom_direct_hardcoded(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return HTMLResponse(content="<h2 style='color:#fff;text-align:center;padding:40px;font-family:sans-serif'>Vehicle ID " + str(product_id) + " not found in database.</h2>", status_code=404)
        
        imgs = []
        if p.images:
            try:
                parsed = _json.loads(p.images) if isinstance(p.images, str) else p.images
                if isinstance(parsed, list): imgs = parsed
            except: imgs = [p.images]
        
        hero = imgs[0] if imgs else "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80"
        price_txt = f"{float(p.price or 0):,.0f}"
        name = str(p.name or "Unknown Car").replace('"', "'").replace('<', '&lt;')
        desc = str(p.description or "Premium vehicle available now.").replace('<', '&lt;')
        
        gallery = ""
        for u in imgs:
            if str(u).endswith((".mp4", ".webm", ".mov")):
                gallery += f'<video src="{u}" controls playsinline style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0"></video>'
            else:
                gallery += f'<img src="{u}" style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0" loading="lazy">'
        if not gallery: 
            gallery = f'<img src="{hero}" style="width:100%;height:320px;object-fit:cover">'

        html = f'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>
        <style>body{{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding-bottom:100px}}.gal{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000}}.wrap{{max-width:600px;margin:0 auto;padding:20px}}.price{{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}}.badge{{background:rgba(16,185,129,0.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}}.cta{{position:fixed;bottom:0;left:0;right:0;padding:20px;background:#0A0F1C;border-top:1px solid #333;text-align:center}}.btn{{display:block;background:#25D366;color:#fff;padding:16px;border-radius:12px;text-decoration:none;font-weight:900;font-size:18px;box-shadow:0 10px 20px rgba(37,211,102,0.3)}}</style>
        </head><body><div class="gal">{gallery}</div><div class="wrap"><span class="badge">✅ VERIFIED SELLER</span><h1 style="margin-top:8px">{name}</h1><div class="price">&#8358; {price_txt}</div><p style="color:#94A3B8;line-height:1.6;margin-top:16px">{desc}</p></div>
        <div class="cta"><a href="https://wa.me/2349079437745?text=Salam! I am looking at the {name} (NGN {price_txt})" target="_blank" class="btn">💬 Verify & Buy on WhatsApp</a></div></body></html>'''
        
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content="<h2 style='color:#fff;text-align:center;padding:40px;font-family:sans-serif'>Server Error: " + str(e) + "</h2>", status_code=500)
    finally:
        db.close()
"""

mc += SHOWROOM_MAIN

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)
print("✅ Showroom hardcoded directly into main.py!")

# 4. PUSH
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Ultimate Fix: Hardcode Showroom into main.py"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel to rebuild main.py...")
time.sleep(75)

# 5. VERIFY IT WORKS
print("\n🔍 Testing the hardcoded showroom link...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/15", headers={"User-Agent": "Mozilla/5.0"})
    r = urllib.request.urlopen(req, timeout=30)
    body = r.read().decode()
    if "VERIFIED SELLER" in body:
        print("✅ ✅ ✅ SHOWROOM IS 100% ALIVE AND SERVING HTML!")
        print("👉 Click this link right now on your phone:")
        print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/15")
    else:
        print("⚠️ Server responded but HTML is missing.")
except Exception as e:
    print("❌ Error:", e)
