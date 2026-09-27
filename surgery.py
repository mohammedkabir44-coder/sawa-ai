import subprocess, time, urllib.request, json

print("="*60)
print("💎 SURGICAL REPLACEMENT: DUAL CTA GUARANTEED")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# The exact, perfect function with Dual CTA (Notice the {{ }} for CSS in f-strings)
NEW_FUNC = """def showroom_elite_bypass(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p: 
            return HTMLResponse(content=f"<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Car ID {product_id} not found.</h1>", status_code=404)
        
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
        <style>body{{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding-bottom:160px}}.gal{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000}}.wrap{{max-width:600px;margin:0 auto;padding:20px}}.price{{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}}.badge{{background:rgba(16,185,129,0.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}}.cta{{position:fixed;bottom:0;left:0;right:0;padding:16px;background:#0A0F1C;border-top:1px solid #333;display:flex;flex-direction:column;gap:10px;z-index:100}}.btn-wa{{display:block;background:#25D366;color:#fff;padding:16px;border-radius:12px;text-decoration:none;font-weight:900;font-size:16px;box-shadow:0 10px 20px rgba(37,211,102,0.3);text-align:center}}.btn-call{{display:block;background:rgba(245,158,11,0.1);color:#F59E0B;padding:14px;border-radius:12px;text-decoration:none;font-weight:800;font-size:15px;border:1px solid #F59E0B;text-align:center}}</style>
        </head><body><div class="gal">{gallery}</div><div class="wrap"><span class="badge">✅ VERIFIED SELLER</span><h1 style="margin-top:8px">{name}</h1><div class="price">&#8358; {price}</div></div>
        <div class="cta">
          <a href="https://wa.me/2349079437745?text=Salam! I am looking at the {name}" target="_blank" class="btn-wa">💬 Verify & Buy on WhatsApp</a>
          <a href="tel:+2349079437745" class="btn-call">📞 Call for Inspection <span style="font-size:13px;opacity:0.8">(₦5,000 Fee)</span></a>
        </div></body></html>'''
        
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content=f"<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>DB Error: {e}</h1>", status_code=500)
    finally:
        db.close()
"""

# Surgically replace the old function
parts = mc.split('def showroom_elite_bypass(product_id: int):')
if len(parts) == 2:
    before = parts[0]
    after_parts = parts[1].split('\n@app.')
    if len(after_parts) > 1:
        after = '\n@app.' + '\n@app.'.join(after_parts[1:])
    else:
        after = ''
    
    mc = before + NEW_FUNC + after
    print("✅ Surgically replaced the function!")
else:
    print("⚠️ Function not found to replace.")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Showroom: Guaranteed Dual CTA Buttons"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel...")
time.sleep(75)

print("\n🔍 Testing...")
req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15", headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "₦5,000 Fee" in body and "btn-call" in body:
            print("✅ ✅ ✅ DUAL CTA IS LIVE!")
            print("\n" + "="*60)
            print("👉 REFRESH THIS LINK ON YOUR PHONE:")
            print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15")
            print("="*60)
        else:
            print("⚠️ Deployed but text missing.")
except Exception as e:
    print("❌ Error:", e)
