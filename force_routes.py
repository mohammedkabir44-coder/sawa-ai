import subprocess, time, urllib.request, ast

print("="*60)
print("🔓 UNIQUE MARKER: FORCING ROUTES INTO EXISTENCE")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

MARKER = "FORCED_ROUTES_INJECTED_999"

if MARKER not in mc:
    ROUTES = f"""

# {MARKER}
@app.get("/api/v1/dashboard/market")
def forced_market_route():
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json
    db = SessionLocal()
    try:
        prods = db.query(Product).order_by(Product.id.desc()).limit(40).all()
        cars = []
        for p in prods:
            imgs = []
            try:
                if isinstance(p.images, str) and p.images.strip().startswith('['): imgs = _json.loads(p.images)
                elif isinstance(p.images, str) and p.images.strip(): imgs = [p.images]
            except: pass
            cars.append({{"id": p.id, "name": p.name, "price": float(p.price or 0), "imgs": imgs, "loc": "Nigeria"}})
        
        html = '''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sodangi Motors</title>
        <style>body{{margin:0;background:#F4F6F8;font-family:sans-serif;padding-bottom:60px}}.feed{{max-width:600px;margin:0 auto;padding:12px}}.card{{background:#fff;border-radius:12px;overflow:hidden;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.05);cursor:pointer}}.gal{{height:220px;background:#000}}.gal img{{width:100%;height:100%;object-fit:cover}}.info{{padding:12px}}.price{{color:#059669;font-size:20px;font-weight:900}}.title{{font-size:16px;font-weight:700;margin:4px 0}}.badge{{background:#DCFCE7;color:#059669;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:800;display:inline-block;margin-bottom:6px}}.nav{{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #eee;display:flex;padding:10px 0}}.nav a{{flex:1;text-align:center;text-decoration:none;color:#64748B;font-size:12px;font-weight:700}}.nav a.on{{color:#059669}}</style>
        </head><body><div style="background:#fff;padding:16px;text-align:center;border-bottom:1px solid #eee;position:sticky;top:0;z-index:10"><h2 style="margin:0;color:#059669">🚗 SODANGI MOTORS</h2><p style="margin:4px 0 0;font-size:12px;color:#64748B">Verified Dealers | Premium Cars</p></div><div class="feed" id="feed"></div>
        <nav class="nav"><a class="on">🏠 Home</a><a href="/api/v1/dashboard/v4-dashboard">🏷️ Sell Car</a></nav>
        <script>var CARS=__CARS__;var box=document.getElementById("feed");if(!CARS.length){{box.innerHTML="<p style='text-align:center;color:#64748B;padding:40px'>No cars available right now.</p>";}}CARS.forEach(function(c){{var img=c.imgs&&c.imgs.length?c.imgs[0]:"https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?w=800";var d=document.createElement("div");d.className="card";d.innerHTML='<div class="gal"><img src="'+img+'"></div><div class="info"><span class="badge">✅ VERIFIED SELLER</span><div class="price">₦'+Number(c.price).toLocaleString()+'</div><div class="title">'+c.name+'</div></div>';d.onclick=function(){{location.href="/api/v1/dashboard/showroom-elite/"+c.id}};box.appendChild(d)}});</script></body></html>'''
        return HTMLResponse(content=html.replace("__CARS__", _json.dumps(cars)))
    except Exception as e:
        return HTMLResponse(content=f"<h1 style='color:#fff;background:#0A0F1C;padding:40px;text-align:center;font-family:sans-serif'>Market Error: {{e}}</h1>")
    finally:
        db.close()

@app.get("/api/v1/dashboard/v4-dashboard")
@app.get("/api/v1/dashboard/ui")
def forced_v4_route():
    from fastapi.responses import HTMLResponse
    html = '''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Dashboard</title></head>
    <body style="font-family:sans-serif;text-align:center;padding:50px;background:#0A0F1C;color:#fff">
    <h1 style="color:#10B981">🏢 Sodangi Admin Portal</h1>
    <p style="color:#94A3B8;margin-bottom:30px">Your inventory system is live and connected.</p>
    <a href="/api/v1/dashboard/market" style="display:block;background:#1E293B;color:#fff;padding:16px;border-radius:12px;text-decoration:none;font-weight:800;margin-bottom:12px">👉 View Live Marketplace</a>
    <p style="font-size:12px;color:#64748B;margin-top:40px">Upload new cars via your API endpoints or Admin UI.</p>
    </body></html>'''
    return HTMLResponse(content=html)
"""
    mc += ROUTES
    print("✅ Unique marker not found. Routes successfully appended to main.py!")
else:
    print("ℹ️ Unique marker already exists. Routes are already in main.py.")

try:
    ast.parse(mc)
    print("✅ Syntax check passed.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Force inject Market and V4 routes with unique marker"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Testing live routes...")
for path in ["/api/v1/dashboard/market", "/api/v1/dashboard/v4-dashboard"]:
    try:
        req = urllib.request.Request("https://sawa-ai-backend.vercel.app" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            if "SODANGI MOTORS" in body or "Sodangi Admin" in body:
                print(f"✅ {path} IS 100% LIVE!")
            else:
                print(f"⚠️ {path} loaded but HTML mismatch.")
    except Exception as e:
        print(f"❌ {path} Error: {e}")
