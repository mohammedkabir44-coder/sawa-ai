import os
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def catch_all_showroom_middleware(request: Request, call_next):
    import re as _re_mw
    from starlette.responses import RedirectResponse
    path = request.url.path
    # Catch ANY URL that has 'showroom' or 'showroom-elite' followed by a number
    m = _re_mw.search(r'showroom(?:-elite)?/(\d+)', path)
    if m and '/api/v1/dashboard/showroom-elite/' not in path:
        pid = m.group(1)
        return RedirectResponse(url=f"/api/v1/dashboard/showroom-elite/{pid}", status_code=307)
    
    return await call_next(request)


# CATCHES ALL 500 ERRORS AND PRINTS THE TRACEBACK
@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc), "trace": traceback.format_exc()})



try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    trace = traceback.format_exc()
    @app.get("/api/v1/dashboard/health")
    @app.get("/api/v1/dashboard/ping")
    def router_crash():
        return {"status": "ROUTER_IMPORT_CRASH", "error": str(e), "trace": trace}


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




@app.get("/api/v1/dashboard/showroom/{product_id}")

@app.get("/api/v1/dashboard/stats")
def ceo_stats_endpoint():
    from app.core.database import SessionLocal
    from app.models.product import Product
    db = SessionLocal()
    try:
        prods = db.query(Product).all()
        total = sum(float(p.price or 0) for p in prods)
        cats = {"Luxury":0, "SUVs":0, "Sedans":0, "Trucks":0}
        for p in prods:
            n = str(p.name).lower()
            if any(x in n for x in ["lexus","benz","bmw","porsche","range","gtr"]): cats["Luxury"]+=1
            elif any(x in n for x in ["suv","highlander","rx3","ml3","pajero","escalade","venza"]): cats["SUVs"]+=1
            elif any(x in n for x in ["truck","bus","van","sienna","trailer"]): cats["Trucks"]+=1
            else: cats["Sedans"]+=1
        return {"total_value": total, "total_cars": len(prods), "categories": cats, "commission": total*0.05}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@app.get("/api/v1/dashboard/alert-save")
def alert_save(phone: str, budget: int, car: str = ""):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS buyer_alerts(id SERIAL PRIMARY KEY, phone TEXT, budget BIGINT, car TEXT, created_at TIMESTAMP DEFAULT NOW())"))
            conn.commit()
            conn.execute(text("INSERT INTO buyer_alerts(phone,budget,car) VALUES(:p,:b,:c)"), {"p":phone,"b":budget,"c":car})
            conn.commit()
        return {"status":"saved"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/dashboard/alert-match")
def alert_match(price: int = 0):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT phone, budget, car FROM buyer_alerts WHERE budget >= :p"), {"p": price}).fetchall()
        return {"matches": [{"phone": r[0], "budget": r[1], "car": r[2]} for r in rows]}
    except Exception as e:
        return {"matches": [], "error": str(e)}


@app.get("/api/v1/dashboard/showroom/{product_id}")
@app.get("/api/v1/dashboard/showroom-elite/{product_id}")
def ultimate_showroom_247(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    from urllib.parse import quote as _q
    import json as _json
    T = r'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__NAME__ | Sodangi Motors</title>
<meta property="og:title" content="__NAME__ - ₦__PRICE__ | Sodangi Motors">
<meta property="og:description" content="✅ Verified Seller. Click to view photos and contact seller instantly!">
<meta property="og:image" content="__FIRST_IMG__">
<meta property="og:url" content="https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/__PID__">
<meta name="twitter:card" content="summary_large_image">
<style>
body{margin:0;background:#0A0F1C;color:#fff;font-family:system-ui,sans-serif;padding-bottom:250px}
.gal{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000;scrollbar-width:none}
.gal::-webkit-scrollbar{display:none}
.gal img,.gal video{width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0}
.wrap{max-width:600px;margin:0 auto;padding:20px}
.badge{background:rgba(16,185,129,.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}
.price{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}
.cta{position:fixed;bottom:0;left:0;right:0;padding:12px;background:#0A0F1C;border-top:1px solid #333;display:flex;flex-direction:column;gap:8px;z-index:100}
.b{display:block;padding:14px;border-radius:12px;text-decoration:none;font-weight:900;font-size:15px;text-align:center;border:none;width:100%;cursor:pointer}
.bcap{background:#3B82F6;color:#fff}
.bwa{background:#25D366;color:#fff}
.bcall{background:rgba(245,158,11,.1);color:#F59E0B;border:1px solid #F59E0B}
.bmkt{background:#1E293B;color:#93C5FD;border:1px solid #334155}
</style></head><body>
<div class="gal">__GALLERY__</div>
<div class="wrap">
<span class="badge">✅ VERIFIED SELLER</span>
<h1 style="margin-top:8px">__NAME__</h1>
<div class="price">₦ __PRICE__</div>
</div>
<div class="cta">
<button class="b bcap" onclick="copyCap()">📣 Copy Ad Caption</button>
<a class="b bwa" href="__WA__" target="_blank" rel="noopener">💬 WhatsApp Seller</a>
<a class="b bcall" href="tel:+2348142969979">📞 Call Inspection (₦5,000 Fee)</a>
<a class="b bmkt" href="/api/v1/dashboard/market">🏪 Checkout Full Showroom</a>
</div>
<script>
function copyCap(){
  var lines=[document.title, document.querySelector(".price").innerText, "✅ Verified Seller | Sodangi Motors", "👉 " + location.href];
  var t=lines.join(String.fromCharCode(10));
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(t).then(function(){alert("📣 Caption copied! Paste on WhatsApp Status / IG / FB");},function(){prompt("Copy this caption:",t);});
  }else{prompt("Copy this caption:",t);}
}
</script>

<button onclick="shareCar()" style="position:fixed;bottom:180px;left:20px;right:20px;background:#8B5CF6;color:#fff;padding:14px;border-radius:12px;border:none;font-weight:800;font-size:15px;text-align:center;z-index:101;box-shadow:0 4px 12px rgba(139,92,246,0.4)">📱 Share to Social Media</button>
<script>
function shareCar() {
  var t = document.title + " - " + document.querySelector('.price').innerText + "\n" + location.href;
  if (navigator.share) { navigator.share({title: document.title, text: t, url: location.href}).catch(function(){}); }
  else { navigator.clipboard.writeText(t); alert("Link copied! Share on FB, X, WhatsApp."); }
}
</script>

<script>
(function(){
  var pid = __PID__;
  fetch('/api/v1/track?event=view&pid='+pid).catch(function(){});
  document.querySelectorAll('.btn-wa, .btn-call').forEach(function(b){
    b.addEventListener('click', function(){ fetch('/api/v1/track?event=click&pid='+pid).catch(function(){}); });
  });
  var oldShare = window.shareCar;
  window.shareCar = function(){ fetch('/api/v1/track?event=share&pid='+pid).catch(function(){}); if(oldShare) oldShare(); };
})();
</script>
</body></html>'''
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return HTMLResponse("<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Car " + str(product_id) + " not found. <a style='color:#10B981' href='/api/v1/dashboard/market'>Browse all cars</a></h1>", status_code=404)
        imgs = []
        try:
            if isinstance(p.images, str):
                s = p.images.strip()
                if s.startswith("["):
                    parsed = _json.loads(s)
                    imgs = parsed if isinstance(parsed, list) else []
                elif s:
                    imgs = [s]
        except Exception:
            imgs = []
        if not imgs:
            imgs = ["https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80",
                    "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
                    "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1200&q=80"]
        name = str(p.name or "Vehicle").replace("&", "&amp;").replace("<", "&lt;").replace('"', "'")
        price = format(float(p.price or 0), ",.0f")
        gal = ""
        for u in imgs:
            su = str(u)
            if su.endswith(".mp4") or su.endswith(".webm") or su.endswith(".mov"):
                gal += '<video src="' + su + '" controls playsinline></video>'
            else:
                gal += '<img src="' + su + '" loading="lazy" alt="">'
        wa = "https://wa.me/2348142969979?text=" + _q("Salam! I am looking at the " + name + " (NGN " + price + ") on Sodangi Motors")
        out = T.replace("__GALLERY__", gal).replace("__NAME__", name).replace("__PRICE__", price).replace("__WA__", wa).replace("__FIRST_IMG__", imgs[0] if imgs else "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?w=1200").replace("__PID__", str(product_id))
        return HTMLResponse(content=out)
    except Exception as e:
        return HTMLResponse(content="<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Server Error: " + str(e) + "</h1>", status_code=500)
    finally:
        db.close()

# FORCE DEPLOY 1790639648.4990754


# FORCED_ROUTES_INJECTED_999
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
            cars.append({"id": p.id, "name": p.name, "price": float(p.price or 0), "imgs": imgs, "loc": "Nigeria"})
        
        html = '''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sodangi Motors</title>
        <style>body{margin:0;background:#F4F6F8;font-family:sans-serif;padding-bottom:60px}.feed{max-width:600px;margin:0 auto;padding:12px}.card{background:#fff;border-radius:12px;overflow:hidden;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.05);cursor:pointer}.gal{height:220px;background:#000}.gal img{width:100%;height:100%;object-fit:cover}.info{padding:12px}.price{color:#059669;font-size:20px;font-weight:900}.title{font-size:16px;font-weight:700;margin:4px 0}.badge{background:#DCFCE7;color:#059669;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:800;display:inline-block;margin-bottom:6px}.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #eee;display:flex;padding:10px 0}.nav a{flex:1;text-align:center;text-decoration:none;color:#64748B;font-size:12px;font-weight:700}.nav a.on{color:#059669}</style>
        </head><body><div style="background:#fff;padding:16px;text-align:center;border-bottom:1px solid #eee;position:sticky;top:0;z-index:10"><h2 style="margin:0;color:#059669">🚗 SODANGI MOTORS</h2><p style="margin:4px 0 0;font-size:12px;color:#64748B">Verified Dealers | Premium Cars</p></div><div class="feed" id="feed"></div>
        <nav class="nav"><a class="on">🏠 Home</a><a href="/api/v1/dashboard/v4-dashboard">🏷️ Sell Car</a></nav>
        <script>var CARS=__CARS__;var box=document.getElementById("feed");if(!CARS.length){box.innerHTML="<p style='text-align:center;color:#64748B;padding:40px'>No cars available right now.</p>";}CARS.forEach(function(c){var img=c.imgs&&c.imgs.length?c.imgs[0]:"https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?w=800";var d=document.createElement("div");d.className="card";d.innerHTML='<div class="gal"><img src="'+img+'"></div><div class="info"><span class="badge">✅ VERIFIED SELLER</span><div class="price">₦'+Number(c.price).toLocaleString()+'</div><div class="title">'+c.name+'</div></div>';d.onclick=function(){location.href="/api/v1/dashboard/showroom-elite/"+c.id};box.appendChild(d)});</script>
<button onclick="shareCar()" style="position:fixed;bottom:180px;left:20px;right:20px;background:#8B5CF6;color:#fff;padding:14px;border-radius:12px;border:none;font-weight:800;font-size:15px;text-align:center;z-index:101;box-shadow:0 4px 12px rgba(139,92,246,0.4)">📱 Share to Social Media</button>
<script>
function shareCar() {
  var t = document.title + " - " + document.querySelector('.price').innerText + "\n" + location.href;
  if (navigator.share) { navigator.share({title: document.title, text: t, url: location.href}).catch(function(){}); }
  else { navigator.clipboard.writeText(t); alert("Link copied! Share on FB, X, WhatsApp."); }
}
</script>

<script>
(function(){
  var pid = __PID__;
  fetch('/api/v1/track?event=view&pid='+pid).catch(function(){});
  document.querySelectorAll('.btn-wa, .btn-call').forEach(function(b){
    b.addEventListener('click', function(){ fetch('/api/v1/track?event=click&pid='+pid).catch(function(){}); });
  });
  var oldShare = window.shareCar;
  window.shareCar = function(){ fetch('/api/v1/track?event=share&pid='+pid).catch(function(){}); if(oldShare) oldShare(); };
})();
</script>
</body></html>'''
        return HTMLResponse(content=html.replace("__CARS__", _json.dumps(cars)))
    except Exception as e:
        return HTMLResponse(content=f"<h1 style='color:#fff;background:#0A0F1C;padding:40px;text-align:center;font-family:sans-serif'>Market Error: {e}</h1>")
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
    
<button onclick="shareCar()" style="position:fixed;bottom:180px;left:20px;right:20px;background:#8B5CF6;color:#fff;padding:14px;border-radius:12px;border:none;font-weight:800;font-size:15px;text-align:center;z-index:101;box-shadow:0 4px 12px rgba(139,92,246,0.4)">📱 Share to Social Media</button>
<script>
function shareCar() {
  var t = document.title + " - " + document.querySelector('.price').innerText + "\n" + location.href;
  if (navigator.share) { navigator.share({title: document.title, text: t, url: location.href}).catch(function(){}); }
  else { navigator.clipboard.writeText(t); alert("Link copied! Share on FB, X, WhatsApp."); }
}
</script>

<script>
(function(){
  var pid = __PID__;
  fetch('/api/v1/track?event=view&pid='+pid).catch(function(){});
  document.querySelectorAll('.btn-wa, .btn-call').forEach(function(b){
    b.addEventListener('click', function(){ fetch('/api/v1/track?event=click&pid='+pid).catch(function(){}); });
  });
  var oldShare = window.shareCar;
  window.shareCar = function(){ fetch('/api/v1/track?event=share&pid='+pid).catch(function(){}); if(oldShare) oldShare(); };
})();
</script>
</body></html>'''
    return HTMLResponse(content=html)

@app.get("/")
@app.get("/")
@app.get("/api/v1/dashboard/portal")
def sodangi_hub():
    from fastapi.responses import HTMLResponse
    html = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sodangi Hub</title>
<style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:20px;box-sizing:border-box}
h1{color:#10B981;font-size:28px;margin-bottom:8px;text-align:center}p{color:#94A3B8;margin-bottom:30px;text-align:center}
.container{display:flex;flex-direction:column;gap:16px;width:100%;max-width:400px}
.btn{display:flex;align-items:center;justify-content:center;gap:12px;background:#1E293B;color:#fff;padding:20px;border-radius:16px;text-decoration:none;font-weight:800;font-size:18px;border:1px solid #334155;box-shadow:0 4px 12px rgba(0,0,0,0.2);transition:transform 0.1s}
.btn:active{transform:scale(0.98)}
.btn-market{border-color:#059669;background:linear-gradient(135deg,#064E3B,#065F46)}
.btn-admin{border-color:#2563EB;background:linear-gradient(135deg,#1E3A8A,#1D4ED8)}
.btn-show{border-color:#F59E0B;background:linear-gradient(135deg,#78350F,#92400E)}
.btn-agents{border-color:#EC4899;background:linear-gradient(135deg,#831843,#BE185D)}
.btn-analytics{border-color:#F59E0B;background:linear-gradient(135deg,#92400E,#B45309)}
.btn-agent-login{border-color:#8B5CF6;background:linear-gradient(135deg,#4C1D95,#6D28D9)}
</style></head>
<body><h1>🚗 SODANGI MOTORS</h1><p>The Ultimate Automotive Hub</p>
<div class="container">
<a href="/api/v1/dashboard/market" class="btn btn-market">🏪 Marketplace (Buy Cars)</a>
<a href="/api/v1/dashboard/v4-dashboard" class="btn btn-admin">🏢 Admin Dashboard (Sell Cars)</a>
<a href="/api/v1/dashboard/showroom-elite/15" class="btn btn-show">🚗 Showroom Demo (Car #15)</a>
<a href="/admin-agents" class="btn btn-agents">👥 Manage Agents (Create Profiles)</a>
<a href="/admin-analytics" class="btn btn-analytics">📊 Admin Analytics & Tracking</a>
<a href="/agent-login" class="btn btn-agent-login">👤 Agent Login</a>
</div></body></html>"""
    return HTMLResponse(content=html)

@app.get("/agent-portal")
def agent_portal_page():
    from fastapi.responses import HTMLResponse
    html = r'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Showroom</title>
<style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding:20px;padding-bottom:80px}
.top{background:#1E293B;padding:16px;border-radius:12px;margin-bottom:20px;border:1px solid #334155}
h2{color:#10B981;margin:0}
.card{background:#1E293B;padding:16px;border-radius:12px;margin-bottom:12px;border:1px solid #334155}
.price{color:#10B981;font-size:20px;font-weight:900}
.btn{display:block;text-align:center;background:#EF4444;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:800;margin-top:20px}
</style></head>
<body>
<div class="top"><h2 id="name">My Showroom</h2><p id="role" style="color:#94A3B8;margin:4px 0 0;font-size:13px"></p></div>
<div id="cars"></div>
<a href="/agent-login" class="btn" onclick="localStorage.clear()">Sign Out</a>
<script>
var t=localStorage.getItem("sodangi_token");
if(!t){location.href="/agent-login";}
document.getElementById("name").innerText = localStorage.getItem("sodangi_name") || "Agent";
document.getElementById("role").innerText = "Role: " + (localStorage.getItem("sodangi_role") || "Agent");

async function load(){
  var box=document.getElementById("cars");
  box.innerHTML="<p style='text-align:center;color:#94A3B8'>Loading your cars...</p>";
  try{
    var r=await fetch("/api/v1/products/mine",{headers:{"Authorization":"Bearer "+t}});
    if(!r.ok){throw new Error("Session expired");}
    var cars=await r.json();
    if(!cars.length){box.innerHTML="<p style='text-align:center;color:#94A3B8;padding:40px'>No cars assigned to your profile yet.</p>";return;}
    var html="";
    cars.forEach(function(c){
      html+='<div class="card"><a href="/api/v1/dashboard/showroom-elite/'+c.id+'" style="text-decoration:none;color:#fff"><div class="title" style="font-weight:800;font-size:16px">'+c.name+'</div><div class="price">₦'+Number(c.price).toLocaleString()+'</div></a></div>';
    });
    box.innerHTML=html;
  }catch(e){ box.innerHTML="<p style='text-align:center;color:#EF4444'>"+e.message+" <a href='/agent-login' style='color:#10B981'>Login again</a></p>"; }
}
load();
</script>
<button onclick="shareCar()" style="position:fixed;bottom:180px;left:20px;right:20px;background:#8B5CF6;color:#fff;padding:14px;border-radius:12px;border:none;font-weight:800;font-size:15px;text-align:center;z-index:101;box-shadow:0 4px 12px rgba(139,92,246,0.4)">📱 Share to Social Media</button>
<script>
function shareCar() {
  var t = document.title + " - " + document.querySelector('.price').innerText + "\n" + location.href;
  if (navigator.share) { navigator.share({title: document.title, text: t, url: location.href}).catch(function(){}); }
  else { navigator.clipboard.writeText(t); alert("Link copied! Share on FB, X, WhatsApp."); }
}
</script>

<script>
(function(){
  var pid = __PID__;
  fetch('/api/v1/track?event=view&pid='+pid).catch(function(){});
  document.querySelectorAll('.btn-wa, .btn-call').forEach(function(b){
    b.addEventListener('click', function(){ fetch('/api/v1/track?event=click&pid='+pid).catch(function(){}); });
  });
  var oldShare = window.shareCar;
  window.shareCar = function(){ fetch('/api/v1/track?event=share&pid='+pid).catch(function(){}); if(oldShare) oldShare(); };
})();
</script>
</body></html>'''
    return HTMLResponse(content=html)


@app.get("/api/v1/track")
def track_event(event: str, pid: int = 0, aid: int = 0):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS site_analytics(id SERIAL PRIMARY KEY, event TEXT, pid INT, aid INT, created_at TIMESTAMP DEFAULT NOW())"))
            conn.commit()
            conn.execute(text("INSERT INTO site_analytics(event,pid,aid) VALUES(:e,:p,:a)"), {"e":event,"p":pid,"a":aid})
            conn.commit()
        return {"status":"ok"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/admin-analytics")
def admin_analytics_page():
    from app.core.database import engine
    from sqlalchemy import text
    from fastapi.responses import HTMLResponse
    stats = {"views":0, "clicks":0, "shares":0}
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS site_analytics(id SERIAL PRIMARY KEY, event TEXT, pid INT, aid INT, created_at TIMESTAMP DEFAULT NOW())"))
            conn.commit()
            rows = conn.execute(text("SELECT event, COUNT(*) FROM site_analytics GROUP BY event")).fetchall()
            for r in rows:
                if r[0] == 'view': stats["views"] = r[1]
                elif r[0] == 'click': stats["clicks"] = r[1]
                elif r[0] == 'share': stats["shares"] = r[1]
    except: pass
    html = r'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Analytics</title>
    <style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding:20px}.card{background:#1E293B;padding:20px;border-radius:12px;margin-bottom:16px;border:1px solid #334155}h2{color:#10B981;margin-top:0}.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}.stat{background:#0F172A;padding:16px;border-radius:10px;text-align:center}.stat h3{margin:0;font-size:28px;color:#F59E0B}.stat p{margin:4px 0 0;font-size:12px;color:#94A3B8}.btn{display:inline-block;background:#3B82F6;color:#fff;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:800;margin-top:20px;margin-right:10px}</style></head>
    <body><h1>📊 Admin Analytics & Tracking</h1>
    <div class="card"><h2>Live Site Performance</h2><div class="grid">
    <div class="stat"><h3>__VIEWS__</h3><p>👁️ Total Page Views</p></div>
    <div class="stat"><h3>__CLICKS__</h3><p>👆 WhatsApp/Call Clicks</p></div>
    <div class="stat"><h3>__SHARES__</h3><p>🚀 Social Media Shares</p></div>
    </div></div>
    <a href="/admin-agents" class="btn" style="background:#EC4899">👥 Manage Agents</a>
    <a href="/" class="btn" style="background:#334155">🏠 Back to Hub</a>
    
<script>
(function(){
  var pid = __PID__;
  fetch('/api/v1/track?event=view&pid='+pid).catch(function(){});
  document.querySelectorAll('.btn-wa, .btn-call').forEach(function(b){
    b.addEventListener('click', function(){ fetch('/api/v1/track?event=click&pid='+pid).catch(function(){}); });
  });
  var oldShare = window.shareCar;
  window.shareCar = function(){ fetch('/api/v1/track?event=share&pid='+pid).catch(function(){}); if(oldShare) oldShare(); };
})();
</script>
</body></html>'''
    html = html.replace("__VIEWS__", str(stats["views"])).replace("__CLICKS__", str(stats["clicks"])).replace("__SHARES__", str(stats["shares"]))
    return HTMLResponse(content=html)

@app.get("/admin-agents")
def admin_agents_page():
    from fastapi.responses import HTMLResponse
    html = '''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Manage Agents</title>
    <style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding:20px}.card{background:#1E293B;padding:20px;border-radius:12px;margin-bottom:16px;border:1px solid #334155}h2{color:#10B981;margin-top:0}label{display:block;margin-top:12px;font-size:13px;color:#94A3B8}input{width:100%;padding:12px;border-radius:8px;border:1px solid #334155;background:#0F172A;color:#fff;font-size:16px;box-sizing:border-box;margin-top:4px}.btn{width:100%;padding:14px;margin-top:16px;background:#8B5CF6;color:#fff;border:none;border-radius:10px;font-weight:800;font-size:16px;cursor:pointer}.msg{padding:10px;border-radius:8px;margin-top:10px;text-align:center}</style></head>
    <body><h1>👥 Agent Manager</h1>
    <div class="card"><h2>Create New Agent Profile</h2>
    <label>Full Name</label><input id="name" placeholder="Musa Abdullahi">
    <label>Email (Username)</label><input id="email" placeholder="agent@sodangi.com">
    <label>Password</label><input id="pass" type="password" placeholder="Min 6 characters">
    <button class="btn" onclick="createAgent()">🚀 Create Agent Profile</button>
    <div id="msg" class="msg" style="display:none"></div>
    </div>
    <a href="/admin-analytics" style="display:block;text-align:center;color:#3B82F6;margin-top:20px">← Back to Analytics</a>
    <script>
    async function createAgent(){
      var n=document.getElementById("name").value;
      var e=document.getElementById("email").value;
      var p=document.getElementById("pass").value;
      var m=document.getElementById("msg");
      if(!n||!e||!p){m.innerText="❌ Fill all fields!";m.style.background="#7F1D1D";m.style.display="block";return;}
if(p.length<8){m.innerText="❌ Password must be at least 8 characters!";m.style.background="#7F1D1D";m.style.display="block";return;}
      m.innerText="⏳ Creating...";m.style.background="#1E3A8A";m.style.display="block";
      try{
        var r=await fetch("/api/v1/auth/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({full_name:n, name:n, email:e, username:e, password:p, role:"agent"})});
        var d=await r.json();
        if(d.access_token || d.id || d.email){
          m.innerHTML="✅ Agent Created!<br><b>Email:</b> "+e+"<br><b>Password:</b> "+p+"<br><br>Give these details to your agent to login at <a href='/agent-login' style='color:#10B981'>/agent-login</a>";
          m.style.background="#065F46";
          document.getElementById("name").value="";document.getElementById("email").value="";document.getElementById("pass").value="";
        } else { m.innerText="❌ Error: "+(typeof d.detail==="object"?JSON.stringify(d.detail):(d.detail||"Unknown"));m.style.background="#7F1D1D"; }
      }catch(ex){ m.innerText="❌ "+ex.message;m.style.background="#7F1D1D"; }
    }
    </script>
<script>
(function(){
  var pid = __PID__;
  fetch('/api/v1/track?event=view&pid='+pid).catch(function(){});
  document.querySelectorAll('.btn-wa, .btn-call').forEach(function(b){
    b.addEventListener('click', function(){ fetch('/api/v1/track?event=click&pid='+pid).catch(function(){}); });
  });
  var oldShare = window.shareCar;
  window.shareCar = function(){ fetch('/api/v1/track?event=share&pid='+pid).catch(function(){}); if(oldShare) oldShare(); };
})();
</script>
</body></html>'''
    return HTMLResponse(content=html)


@app.get("/agent-login")
def agent_login_page():
    from fastapi.responses import HTMLResponse
    html = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agent Login</title>
<style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;box-sizing:border-box}
.box{background:#1E293B;padding:30px;border-radius:16px;width:100%;max-width:400px;border:1px solid #334155}
h2{color:#10B981;margin-top:0;text-align:center}
label{display:block;margin-top:16px;font-size:14px;color:#94A3B8}
input{width:100%;padding:14px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:#fff;font-size:16px;box-sizing:border-box;margin-top:6px}
.btn{width:100%;padding:16px;margin-top:24px;background:#10B981;color:#052E16;border:none;border-radius:10px;font-weight:800;font-size:16px;cursor:pointer}
.err{color:#EF4444;text-align:center;margin-top:12px;font-size:14px}</style></head>
<body><div class="box"><h2>👤 Agent Portal Login</h2>
<label>Email / Username</label><input id="email" type="text" placeholder="agent@sodangi.com">
<label>Password</label><input id="pass" type="password" placeholder="••••••••">
<button class="btn" onclick="login()">Sign In</button>
<p class="err" id="err"></p>
<p style="text-align:center;margin-top:20px;font-size:13px;color:#64748B">Only Admin can create new profiles.</p>
</div>
<script>
async function login(){
  var e=document.getElementById("email").value;
  var p=document.getElementById("pass").value;
  document.getElementById("err").innerText="Signing in...";
  try{
    var fd=new FormData(); fd.append("username",e); fd.append("password",p);
    var r=await fetch("/api/v1/auth/login",{method:"POST",body:fd});
    var d=await r.json();
    if(d.access_token){
      localStorage.setItem("sodangi_token", d.access_token);
      localStorage.setItem("sodangi_role", d.role||"agent");
      localStorage.setItem("sodangi_name", d.full_name||e);
      location.href="/agent-portal";
    } else { document.getElementById("err").innerText="Login failed: "+(d.detail||"Check credentials"); }
  }catch(ex){ document.getElementById("err").innerText="Error: "+ex.message; }
}
</script></body></html>"""
    return HTMLResponse(content=html)
