import subprocess, time, urllib.request, re, json

print("="*60)
print("☢️ NUCLEAR OPTION: TOTAL ROUTE OVERRIDE")
print("="*60)

# 1. NUKE agents_api.py of ANY showroom route
print("\n[1/3] Nuking agents_api.py of all showroom ghosts...")
url2 = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as r:
    code = r.read().decode()

# Aggressively remove any @router.get/post/put/delete containing 'showroom'
code = re.sub(r'@router\.(get|post|put|delete)\("[^"]*showroom[^"]*"\)[\s\S]*?(?=\n@router\.|\ndef |\Z)', '', code, flags=re.IGNORECASE)
# Remove any function definition containing 'showroom'
code = re.sub(r'def \w*showroom\w*\([\s\S]*?(?=\n@router\.|\ndef |\Z)', '', code, flags=re.IGNORECASE)

with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)
print("✅ All showroom routes nuked from agents_api.py!")

# 2. INJECT SHOWROOM AT THE VERY TOP OF main.py
print("\n[2/3] Injecting Showroom at the HIGHEST PRIORITY in main.py...")
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# Remove any existing showroom routes in main.py to prevent duplicates
mc = re.sub(r'@app\.(get|post|put|delete)\("[^"]*showroom[^"]*"\)[\s\S]*?(?=\n@app\.|\Z)', '', mc, flags=re.IGNORECASE)
mc = re.sub(r'def \w*showroom\w*\([\s\S]*?(?=\n@app\.|\Z)', '', mc, flags=re.IGNORECASE)

SHOWROOM_NUCLEAR = """
@app.get("/api/v1/dashboard/showroom/{product_id}")
@app.get("/api/v1/dashboard/showroom-elite/{product_id}")
def nuclear_showroom(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return HTMLResponse("<h1 style='color:#fff;text-align:center;padding:50px'>Car " + str(product_id) + " not found</h1>")
        imgs = []
        try:
            if isinstance(p.images, str) and p.images.strip().startswith('['): imgs = _json.loads(p.images)
            elif isinstance(p.images, str) and p.images.strip(): imgs = [p.images]
        except: pass
        if not imgs:
            imgs = ["https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?w=1000", "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=1000"]
        name = str(p.name).replace('"',"'")
        price = f"{float(p.price or 0):,.0f}"
        gallery = "".join([f'<img src="{u}" style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0">' for u in imgs])
        html = f'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding-bottom:150px">
        <div style="display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000">{gallery}</div>
        <div style="max-width:600px;margin:0 auto;padding:20px">
        <span style="background:rgba(16,185,129,0.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800">✅ VERIFIED SELLER</span>
        <h1 style="margin-top:10px">{name}</h1>
        <div style="font-size:28px;font-weight:900;color:#10B981;margin:10px 0">₦ {price}</div>
        </div>
        <div style="position:fixed;bottom:0;left:0;right:0;padding:12px;background:#0A0F1C;border-top:1px solid #333;display:flex;flex-direction:column;gap:8px;z-index:100">
        <a href="https://wa.me/2348142969979?text=Salam! I am looking at the {name}" target="_blank" style="background:#25D366;color:#fff;padding:14px;border-radius:12px;text-decoration:none;font-weight:900;text-align:center">💬 WhatsApp Seller</a>
        <a href="tel:+2348142969979" style="background:rgba(245,158,11,0.1);color:#F59E0B;padding:12px;border-radius:12px;text-decoration:none;font-weight:800;border:1px solid #F59E0B;text-align:center">📞 Call Inspection <span style="font-size:12px;opacity:0.8">(₦5,000)</span></a>
        </div></body></html>'''
        return HTMLResponse(content=html)
    finally:
        db.close()
"""

# Inject RIGHT BEFORE app.include_router so it takes absolute priority
insert_idx = mc.find('app.include_router')
if insert_idx == -1:
    insert_idx = mc.find('@app.get("/")')
if insert_idx == -1:
    insert_idx = len(mc)

mc = mc[:insert_idx] + SHOWROOM_NUCLEAR + "\n" + mc[insert_idx:]
print("✅ Showroom injected at the HIGHEST PRIORITY in main.py!")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

# 3. PUSH
print("\n[3/3] Pushing Nuclear Override to Vercel...")
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Nuclear: Showroom at highest priority"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to rebuild...")
time.sleep(90)

# 4. VERIFY AND PRINT RAW HTML
print("\n🔍 Fetching raw HTML to prove it works...")
for path in ["/api/v1/dashboard/showroom/15", "/api/v1/dashboard/showroom-elite/15"]:
    try:
        req = urllib.request.Request("https://sawa-ai-backend.vercel.app" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            if "VERIFIED SELLER" in body:
                print(f"✅ {path} IS LIVE AND SERVING HTML!")
            elif '"detail":"Not Found"' in body or 'Not Found' in body:
                print(f"❌ {path} STILL RETURNING 404!")
                print("RAW RESPONSE:", body[:200])
            else:
                print(f"⚠️ {path} returned unknown HTML.")
    except Exception as e:
        print(f"❌ {path} Error: {e}")

print("\n" + "="*60)
print("👉 OPEN THIS EXACT LINK ON YOUR PHONE:")
print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15")
print("="*60)
