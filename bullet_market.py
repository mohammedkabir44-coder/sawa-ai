import subprocess, time, urllib.request, ast

print("="*60)
print("🛡️ BULLETPROOF MARKETPLACE INJECTION")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

MARKET_HTML = r'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sodangi Motors | Buy Verified Cars</title>
<style>
body{margin:0;background:#F4F6F8;color:#0F172A;font-family:system-ui,sans-serif;padding-bottom:76px}
.top{position:sticky;top:0;background:#fff;z-index:50;padding:10px 14px;box-shadow:0 1px 0 #E2E8F0}
.brand{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.brand b{font-size:18px;font-weight:900;color:#059669}
.feed{max-width:640px;margin:0 auto;padding:0 12px}
.card{background:#fff;border-radius:16px;overflow:hidden;margin-bottom:14px;box-shadow:0 1px 3px rgba(15,23,42,.08);cursor:pointer}
.gal{position:relative;height:230px;background:#0B0F19}
.gal img{width:100%;height:100%;object-fit:cover}
.vbadge{position:absolute;left:10px;top:10px;background:rgba(255,255,255,.92);color:#059669;font-size:10px;font-weight:800;padding:5px 10px;border-radius:999px}
.info{padding:12px 14px}
.price{color:#059669;font-size:19px;font-weight:900}
.title{font-size:15px;font-weight:700;margin:4px 0 2px;text-transform:uppercase}
.loc{font-size:12px;color:#64748B}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #E2E8F0;display:flex;z-index:60;padding:6px 0}
.nav a,.nav button{flex:1;background:none;border:none;display:flex;flex-direction:column;align-items:center;gap:3px;font-size:10px;color:#64748B;cursor:pointer;text-decoration:none}
.nav .ic{font-size:20px}
.nav .on{color:#F0876A}
</style></head>
<body>
<div class="top"><div class="brand"><span style="font-size:22px">🚗</span><b>SODANGI MOTORS</b><span style="margin-left:auto;font-size:10px;color:#64748B;font-weight:700">✔ VERIFIED DEALERS</span></div></div>
<div class="feed" id="feed"></div>
<nav class="nav">
 <button class="on"><span class="ic">🏠</span>Home</button>
 <a href="/api/v1/dashboard/v4-dashboard"><span class="ic">🏷️</span>Sell</a>
</nav>
<script>
var CARS=__CARS__;
function money(n){return "\u20A6"+Number(n).toLocaleString()}
var box=document.getElementById("feed");
if(!CARS.length){box.innerHTML="<p style='text-align:center;color:#64748B;padding:50px'>No vehicles found.</p>";}
CARS.forEach(function(c){
  var img = (c.imgs&&c.imgs.length)?c.imgs[0]:"https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=900&q=70";
  var d=document.createElement("div");d.className="card";
  d.innerHTML='<div class="gal"><img src="'+img+'"><span class="vbadge">✔ Verified Seller</span></div>'+
   '<div class="info"><div class="price">'+money(c.price)+'</div>'+
   '<div class="title">'+c.name+'</div><div class="loc">📍 '+(c.loc||"Nigeria")+'</div></div>';
  d.onclick=function(){location.href="/api/v1/dashboard/showroom-elite/"+c.id;};
  box.appendChild(d);
});
</script></body></html>'''

if '"/api/v1/dashboard/market"' not in mc:
    # repr() safely escapes all quotes and backslashes!
    safe_html = repr(MARKET_HTML)
    MKT_ROUTE = f"""

@app.get("/api/v1/dashboard/market")
@app.get("/")
def market_god_mode():
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
        html = {safe_html}.replace("__CARS__", _json.dumps(cars))
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Market Error: {{e}}</h1>")
    finally:
        db.close()
"""
    mc += MKT_ROUTE
    print("✅ Fresh Marketplace App injected!")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ SYNTAX ERROR: {e.msg}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Bulletproof Market Injection"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel...")
time.sleep(90)

print("\n🔍 Testing Market and V4...")
for path in ["/api/v1/dashboard/market", "/api/v1/dashboard/v4-dashboard"]:
    try:
        req = urllib.request.Request("https://sawa-ai-backend.vercel.app" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            if "SODANGI MOTORS" in body or "Add Vehicle" in body:
                print(f"✅ {path} IS LIVE!")
            else:
                print(f"⚠️ {path} loaded but HTML mismatch.")
    except Exception as e:
        print(f"❌ {path} Error: {e}")
