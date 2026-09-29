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

@app.get("/", include_in_schema=False)
def root_market():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/dashboard/market")

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
        out = T.replace("__GALLERY__", gal).replace("__NAME__", name).replace("__PRICE__", price).replace("__WA__", wa)
        return HTMLResponse(content=out)
    except Exception as e:
        return HTMLResponse(content="<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Server Error: " + str(e) + "</h1>", status_code=500)
    finally:
        db.close()

# FORCE DEPLOY 1790639648.4990754


@app.get("/api/v1/dashboard/v4-dashboard")
@app.get("/api/v1/dashboard/ui")
def v4_dashboard_god_mode():
    from fastapi.responses import HTMLResponse
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Sodangi Motors - Dashboard</title>
<style>
:root{--bg:#0B0F19;--card:#151F38;--accent:#22C55E;--text:#F8FAFC;--muted:#94A3B8}
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,sans-serif}
body{background:var(--bg);color:var(--text);padding-bottom:80px;min-height:100vh}
header{background:linear-gradient(135deg,#065F46,#0369A1);padding:20px;text-align:center}
header h1{font-size:22px;font-weight:800;letter-spacing:1px}
.container{max-width:600px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid #1E293B;border-radius:16px;padding:20px;margin-bottom:16px}
.card h2{font-size:18px;margin-bottom:16px;color:#7DD3FC}
label{display:block;font-size:13px;color:var(--muted);margin:12px 0 6px;font-weight:600}
input,textarea,select{width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:var(--text);font-size:15px}
.btn{width:100%;padding:14px;border:none;border-radius:10px;font-weight:700;font-size:16px;cursor:pointer;margin-top:12px}
.btn-primary{background:var(--accent);color:#052E16}
.btn-danger{background:#EF4444;color:#fff}
.btn-ghost{background:#334155;color:var(--text)}
.hidden{display:none!important}
.nav{position:fixed;bottom:0;left:0;right:0;background:#0F172A;border-top:1px solid #1E293B;display:flex;justify-content:space-around;padding:8px 0;z-index:100}
.nav button{background:none;border:none;color:var(--muted);font-size:12px;display:flex;flex-direction:column;align-items:center;gap:4px;padding:8px 12px;border-radius:12px;cursor:pointer}
.nav button.active{color:var(--accent);background:rgba(34,197,94,0.1)}
.nav button span{font-size:22px}
.item{background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:12px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.item-info h3{font-size:15px;margin-bottom:4px}
.item-info p{font-size:13px;color:var(--muted)}
#toast{position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#16A34A;color:#fff;padding:12px 24px;border-radius:10px;font-weight:600;display:none;z-index:999;box-shadow:0 4px 12px rgba(0,0,0,0.3)}
</style>
</head>
<body>
<div id="toast"></div>
<header><h1>SODANGI MOTORS</h1><div style="font-size:13px;color:#E0F2FE;margin-top:4px" id="who">Dashboard</div></header>
<div class="container">
  <section id="tabUpload" class="card">
    <h2>+ Add Vehicle</h2>
    <label>Vehicle Name</label><input id="pName" placeholder="Toyota Camry 2022">
    <label>Price (Naira)</label><input id="pPrice" type="number" placeholder="8500000">
    <label>Description</label><textarea id="pDesc" rows="3" placeholder="Clean interior, low mileage..."></textarea>
    <label>Year</label><input id="sYear" placeholder="2009">
    <label>Mileage</label><input id="sMile" placeholder="214,710 km">
    <label>Transmission</label><select id="sTrans" style="width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:#F8FAFC"><option>Automatic</option><option>Manual</option></select>
    <label>Condition</label><select id="sCond" style="width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:#F8FAFC"><option>Foreign Used</option><option>Local Used</option><option>Brand New</option></select>
    <label>Location</label><input id="sLoc" placeholder="Abule egba, Lagos">
    <label>Photos (up to 10)</label>
    <input type="file" id="pPhotos" accept="image/*" multiple onchange="compressAndPreview()" style="padding:10px;background:#1E293B;border-radius:10px">
    <div id="photoPreview" style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px"></div>
    <div id="uploadStatus" style="font-size:12px;color:#7DD3FC;margin-top:6px"></div>
    <label>Video (walk-around, optional)</label>
    <input type="file" id="pVideo" accept="video/*" onchange="previewVideo()" style="padding:10px;background:#1E293B;border-radius:10px">
    <div id="videoPreview" style="margin-top:10px"></div>
    <button class="btn btn-primary" onclick="publishCar()" style="margin-top:16px">🚀 Publish Vehicle</button>
  </section>
  <section id="tabCars" class="card hidden">
    <h2>My Inventory</h2>
    <div id="carsList"></div>
  </section>
  <section id="tabAgents" class="card hidden">
    <h2>Sales Team (Owner Only)</h2>
    <div style="background:#1E293B;padding:16px;border-radius:12px;margin-bottom:16px">
      <h3 style="font-size:15px;margin-bottom:12px;color:#7DD3FC">Create New Agent Profile</h3>
      <label>Full Name</label><input id="newAgentName" placeholder="Musa Abdullahi">
      <label>Email</label><input id="newAgentEmail" type="email" placeholder="musa@sodangi.com">
      <label>Phone</label><input id="newAgentPhone" placeholder="080...">
      <label>Password</label><input id="newAgentPass" type="password" placeholder="Min 6 characters">
      <button class="btn btn-primary" onclick="createAgent()">Create Agent</button>
    </div>
    <h3 style="font-size:15px;margin-bottom:12px;color:#7DD3FC">Your Agents</h3>
    <div id="agentsList"></div>
  </section>
  <section id="tabProfile" class="card hidden">
    <h2>My Profile & Showroom</h2>
    <div id="myShowroomLink" style="margin-bottom:16px"></div>
    <label>Phone</label><input id="mPhone" placeholder="080...">
    <label>Bio</label><textarea id="mBio" rows="3" placeholder="Tell buyers about yourself..."></textarea>
    <button class="btn btn-primary" onclick="saveProfile()">Save Profile</button>
    <button class="btn btn-danger" onclick="logout()" style="margin-top:10px">Sign Out</button>
  </section>
</div>
<nav class="nav">
  <button id="navUpload" onclick="go('Upload')" class="active"><span>+</span>Add</button>
  <button id="navCars" onclick="go('Cars')"><span>C</span>Cars</button>
  <button id="navAgents" onclick="go('Agents')" class="hidden"><span>T</span>Team</button>
  <button id="navProfile" onclick="go('Profile')"><span>P</span>Me</button>
</nav>
<script>
var API="/api/v1/dashboard";
var TOKEN=localStorage.getItem("sodangi_token")||"";
var ROLE=localStorage.getItem("sodangi_role")||"";
var NAME=localStorage.getItem("sodangi_name")||"";

document.getElementById("who").textContent=NAME+" ("+ROLE+")";

if(ROLE==="owner"){
  document.getElementById("navAgents").classList.remove("hidden");
}

function toast(m,c){var t=document.getElementById("toast");t.textContent=m;t.style.background=c||"#16A34A";t.style.display="block";setTimeout(function(){t.style.display="none";},3000);}
async function api(p,m,b){var h={"Content-Type":"application/json","Authorization":"Bearer "+TOKEN};var r=await fetch(API+p,{method:m,headers:h,body:b?JSON.stringify(b):undefined});if(!r.ok){var e={};try{e=await r.json();}catch(x){}throw new Error(e.detail||("HTTP "+r.status));}return r.json();}

function go(tab){
  ["Upload","Cars","Agents","Profile"].forEach(function(t){
    var el=document.getElementById("tab"+t);if(el)el.classList.add("hidden");
    var nb=document.getElementById("nav"+t);if(nb)nb.classList.remove("active");
  });
  var el=document.getElementById("tab"+tab);if(el)el.classList.remove("hidden");
  var nb=document.getElementById("nav"+tab);if(nb)nb.classList.add("active");
  if(tab==="Cars")loadCars();
  if(tab==="Profile")loadProfile();
  if(tab==="Agents")loadAgents();
}


function buildSpec(){var s={year:document.getElementById("sYear").value,mileage:document.getElementById("sMile").value,transmission:document.getElementById("sTrans").value,condition:document.getElementById("sCond").value,location:document.getElementById("sLoc").value};return "[[SPEC:"+JSON.stringify(s)+"]]";}
var uploadedPhotos = [];
var uploadedVideo = "";

async function compressAndPreview(){
  var files = document.getElementById("pPhotos").files;
  var preview = document.getElementById("photoPreview");
  var status = document.getElementById("uploadStatus");
  preview.innerHTML = "";
  uploadedPhotos = [];
  
  for(var i=0; i<files.length && i<10; i++){
    var f = files[i];
    status.textContent = "Compressing photo " + (i+1) + " of " + Math.min(files.length,10) + "...";
    
    // Compress image
    var blob = await compressImg(f, 900);
    status.textContent = "Uploading photo " + (i+1) + " (" + Math.round(blob.size/1024) + "KB)...";
    
    // Upload to server
    try {
      var fd = new FormData();
      fd.append("file", blob, "photo" + i + ".jpg");
      var r = await fetch(API + "/upload-media", {method:"POST", body:fd}); // No auth header to prevent CORS preflight
      var txt = await r.text(); if(!r.ok) throw new Error("Server " + r.status + ": " + txt.substring(0,80));
      var d = await r.json();
      uploadedPhotos.push(d.url);
      
      // Show preview
      var img = document.createElement("img");
      img.src = d.url;
      img.style.cssText = "width:70px;height:70px;object-fit:cover;border-radius:10px;border:2px solid #22C55E";
      preview.appendChild(img);
    } catch(e) {
      status.textContent = "Failed to upload photo " + (i+1) + ": " + e.message;
      return;
    }
  }
  status.textContent = "✅ " + uploadedPhotos.length + " photos uploaded successfully!";
}

function compressImg(file, maxW){
  return new Promise(function(res, rej){
    var img = new Image();
    var u = URL.createObjectURL(file);
    img.onload = function(){
      var w = img.width, h = img.height;
      if(w > maxW){ h = Math.round(h * maxW / w); w = maxW; }
      var c = document.createElement("canvas");
      c.width = w; c.height = h;
      c.getContext("2d").drawImage(img, 0, 0, w, h);
      URL.revokeObjectURL(u);
      c.toBlob(function(b){ b ? res(b) : rej(new Error("compress failed")); }, "image/jpeg", 0.72);
    };
    img.onerror = function(){ URL.revokeObjectURL(u); rej(new Error("load failed")); };
    img.src = u;
  });
}

function previewVideo(){
  var f = document.getElementById("pVideo").files[0];
  var pv = document.getElementById("videoPreview");
  pv.innerHTML = "";
  uploadedVideo = "";
  if(!f) return;
  
  if(f.size > 50*1024*1024){
    pv.innerHTML = "<p style='color:#EF4444;font-size:12px'>Video too large (max 50MB). Please use a shorter clip.</p>";
    return;
  }
  
  pv.innerHTML = "<p style='color:#7DD3FC;font-size:12px'>Uploading video... (this may take 30 seconds)</p>";
  var fd = new FormData();
  fd.append("file", f, f.name);
  fetch(API + "/upload-media", {method:"POST", headers:{"Authorization":"Bearer "+TOKEN}, body:fd})
    .then(function(r){ return r.json(); })
    .then(function(d){
      uploadedVideo = d.url;
      pv.innerHTML = "<video src='" + d.url + "' controls style='width:100%;border-radius:12px;max-height:200px'></video><p style='color:#22C55E;font-size:12px;margin-top:4px'>✅ Video uploaded!</p>";
    })
    .catch(function(e){
      pv.innerHTML = "<p style='color:#EF4444;font-size:12px'>Video upload failed: " + e.message + "</p>";
    });
}

async function publishCar(){
  var n=document.getElementById("pName").value;
  var p=parseFloat(document.getElementById("pPrice").value);
  if(!n||isNaN(p)){alert("Please fill Name and Price!");return;}
  if(uploadedPhotos.length===0){alert("Please upload at least 1 photo!");return;}
  
  var allMedia = uploadedPhotos.slice();
  if(uploadedVideo) allMedia.push(uploadedVideo);
  
  try{
    await api("/products/upload","POST",{name:n,price:p,image_url:JSON.stringify(allMedia),description:buildSpec()+document.getElementById("pDesc").value,stock:1});
    toast("🚀 Vehicle published with " + uploadedPhotos.length + " photos!");
    document.getElementById("pName").value="";
    document.getElementById("pPrice").value="";
    document.getElementById("pDesc").value="";
    document.getElementById("pPhotos").value="";
    document.getElementById("pVideo").value="";
    document.getElementById("photoPreview").innerHTML="";
    document.getElementById("videoPreview").innerHTML="";
    document.getElementById("uploadStatus").textContent="";
    uploadedPhotos=[];
    uploadedVideo="";
    go("Cars");
    notifyMatches(n, p);
  }catch(e){alert("Failed: "+e.message);}
}

async function loadCars(){
  try{
    var CARS=await api("/products/mine","POST",{});
    var box=document.getElementById("carsList");
    box.innerHTML="";
    if(!CARS.length){box.innerHTML="<p style='color:#94A3B8;text-align:center;padding:20px'>No vehicles yet.</p>";return;}
    window.V4CARS=CARS;
    CARS.forEach(function(c){
      var d=document.createElement("div");
      d.className="item";
      d.style.flexDirection="column";
      d.style.alignItems="stretch";
      d.style.gap="8px";
      d.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div><button class="btn btn-danger" style="width:auto;padding:8px 12px;font-size:12px;margin:0" onclick="delCar('+c.id+')">Delete</button></div><div style="display:flex;gap:6px;flex-wrap:wrap"><button class="btn btn-ghost" style="flex:1;min-width:80px;padding:10px;font-size:12px;margin:0" onclick="editCar('+c.id+')">Edit</button><a class="btn btn-primary" style="flex:1;min-width:80px;padding:10px;font-size:12px;margin:0;text-decoration:none;text-align:center" href="/api/v1/dashboard/showroom/'+c.id+'" target="_blank">Showroom</a></div>';
      box.appendChild(d);
    });
  }catch(e){document.getElementById("carsList").innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}
}

async function delCar(pid){
  if(!confirm("Delete?"))return;
  try{await api("/products/delete","POST",{product_id:pid});toast("Deleted");loadCars();}
  catch(e){alert(e.message);}
}

function editCar(id){var c=(window.V4CARS||[]).filter(function(x){return x.id===id;})[0];if(!c)return;var n=prompt("Vehicle name:",c.name);if(n===null||n==="")return;var p=prompt("Price:",c.price);if(p===null||p==="")return;var ds=prompt("Description:",c.description||"");if(ds===null)return;api("/products/"+id,"PUT",{name:n,price:parseFloat(p),description:ds,image_url:JSON.stringify(c.images||[]),stock:c.stock||1}).then(function(){toast("Updated!");loadCars();}).catch(function(e){alert("Failed: "+e.message);});}

async function loadProfile(){
  try{
    var me=await api("/profile/me","GET");
    document.getElementById("mPhone").value=me.phone||"";
    document.getElementById("mBio").value=me.bio||"";
    var showroomUrl=location.origin+"/api/v1/dashboard/agent/"+me.id;
    document.getElementById("myShowroomLink").innerHTML='<a href="'+showroomUrl+'" target="_blank" class="btn btn-primary" style="background:#3B82F6;color:#fff;text-decoration:none;text-align:center">View My Showroom</a><button class="btn btn-ghost" onclick="navigator.clipboard.writeText(&quot;'+showroomUrl+'&quot;);toast(&quot;Link copied!&quot;)">Copy Showroom Link</button>';
  }catch(e){}
}

async function saveProfile(){
  try{
    await api("/profile/update","POST",{phone:document.getElementById("mPhone").value,bio:document.getElementById("mBio").value});
    toast("Profile saved!");
  }catch(e){alert(e.message);}
}

async function createAgent(){
  var name=document.getElementById("newAgentName").value;
  var email=document.getElementById("newAgentEmail").value;
  var phone=document.getElementById("newAgentPhone").value;
  var pass=document.getElementById("newAgentPass").value;
  if(!name||!email||!pass){alert("Name, email, and password required!");return;}
  try{
    await api("/agents/create","POST",{full_name:name,email:email,phone:phone,password:pass});
    toast("Agent created! They can now log in.");
    document.getElementById("newAgentName").value="";
    document.getElementById("newAgentEmail").value="";
    document.getElementById("newAgentPhone").value="";
    document.getElementById("newAgentPass").value="";
    loadAgents();
  }catch(e){alert("Failed: "+e.message);}
}

async function loadAgents(){
  try{
    var agents=await api("/agents/list","GET");
    var box=document.getElementById("agentsList");
    box.innerHTML="";
    if(!agents.length){box.innerHTML="<p style='color:#94A3B8;text-align:center;padding:20px'>No agents yet.</p>";return;}
    agents.forEach(function(a){
      var d=document.createElement("div");
      d.className="item";
      d.style.flexDirection="column";
      d.style.alignItems="stretch";
      d.style.gap="8px";
      d.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center"><div class="item-info"><h3>'+a.full_name+'</h3><p>'+a.email+'</p></div><button class="btn btn-danger" style="width:auto;padding:8px 12px;font-size:12px;margin:0" onclick="deleteAgent('+a.id+')">Delete</button></div><a href="/api/v1/dashboard/agent/'+a.id+'" target="_blank" class="btn btn-primary" style="padding:10px;font-size:12px;text-decoration:none;text-align:center">View Agent Showroom</a>';
      box.appendChild(d);
    });
  }catch(e){document.getElementById("agentsList").innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}
}

async function deleteAgent(id){
  if(!confirm("Delete agent?"))return;
  try{await api("/agents/"+id,"DELETE");toast("Deleted");loadAgents();}
  catch(e){alert(e.message);}
}

function logout(){
  localStorage.removeItem("sodangi_token");
  localStorage.removeItem("sodangi_role");
  localStorage.removeItem("sodangi_name");
  location.href="/api/v1/dashboard/ui";
}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)
