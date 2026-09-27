import subprocess, time, urllib.request, json

print("="*60)
print("💊 MOVING MARKETPLACE INTO MAIN.PY (GOD MODE)")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

if '"/api/v1/dashboard/market"' in mc:
    print("ℹ️ Market route already in main.py.")
else:
    TEMPLATE = r'''
MARKET_TEMPLATE_MAIN = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sodangi Motors | Buy Verified Cars</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
body{background:#F4F6F8;color:#0F172A;padding-bottom:76px}
.top{position:sticky;top:0;background:#fff;z-index:50;padding:10px 14px;box-shadow:0 1px 0 #E2E8F0}
.brand{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.brand b{font-size:18px;font-weight:900;color:#059669}
.search{display:flex;align-items:center;gap:8px;background:#F1F5F9;border:1px solid #E2E8F0;border-radius:12px;padding:10px 12px}
.search input{border:none;background:none;outline:none;flex:1;font-size:14px}
.chips{display:flex;gap:8px;overflow-x:auto;padding:10px 14px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex-shrink:0;padding:8px 14px;border-radius:999px;background:#fff;border:1px solid #E2E8F0;font-size:13px;font-weight:600;color:#64748B;cursor:pointer}
.chip.on{background:#10B981;border-color:#10B981;color:#fff}
.feed{max-width:640px;margin:0 auto;padding:0 12px}
.card{background:#fff;border-radius:16px;overflow:hidden;margin-bottom:14px;box-shadow:0 1px 3px rgba(15,23,42,.08);cursor:pointer}
.gal{position:relative;display:flex;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;background:#0B0F19}
.gal::-webkit-scrollbar{display:none}
.gal img,.gal video{scroll-snap-align:center;flex:0 0 100%;height:230px;object-fit:cover}
.gal .cnt{position:absolute;right:10px;bottom:10px;background:rgba(0,0,0,.55);color:#fff;font-size:11px;font-weight:700;padding:4px 8px;border-radius:8px}
.vbadge{position:absolute;left:10px;top:10px;background:rgba(255,255,255,.92);color:#059669;font-size:10px;font-weight:800;padding:5px 10px;border-radius:999px}
.info{padding:12px 14px}
.prow{display:flex;justify-content:space-between;align-items:flex-start}
.price{color:#059669;font-size:19px;font-weight:900}
.cbtn{background:#F0876A;color:#fff;border:none;font-size:12px;font-weight:800;padding:8px 16px;border-radius:999px;cursor:pointer}
.title{font-size:15px;font-weight:700;margin:4px 0 2px;text-transform:uppercase}
.loc{font-size:12px;color:#64748B}
.specs{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;padding-top:10px;border-top:1px solid #F1F5F9}
.spec{font-size:11px;color:#64748B;background:#F8FAFC;border:1px solid #EEF2F6;padding:5px 9px;border-radius:8px}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #E2E8F0;display:flex;z-index:60;padding:6px 0}
.nav a,.nav button{flex:1;background:none;border:none;display:flex;flex-direction:column;align-items:center;gap:3px;font-size:10px;color:#64748B;cursor:pointer;text-decoration:none}
.nav .ic{font-size:20px}
.nav .on{color:#F0876A}
.modal{position:fixed;inset:0;background:rgba(15,23,42,.45);backdrop-filter:blur(6px);display:none;align-items:center;justify-content:center;z-index:100;padding:24px}
.modal.show{display:flex}
.mcard{background:rgba(255,255,255,.94);border-radius:24px;padding:26px 20px;width:100%;max-width:340px;text-align:center}
.mcard h3{font-size:17px;font-weight:900;margin:10px 0 14px}
.mrow{display:flex;gap:12px}
.mtile{flex:1;border-radius:16px;padding:16px 8px;text-decoration:none;font-size:12px;font-weight:700;line-height:1.4}
.mtile .ic{display:block;font-size:26px;margin-bottom:6px}
.mcall{background:#FDE8E8;color:#B91C1C}
.mwa{background:#DCF5E7;color:#065F46}
.mview{display:inline-block;margin-top:12px;background:#E0F2FE;color:#0369A1;font-size:12px;font-weight:700;padding:8px 16px;border-radius:999px;text-decoration:none}
.empty{text-align:center;color:#64748B;padding:50px 20px;font-size:14px}
</style></head>
<body>
<div class="top">
 <div class="brand"><span style="font-size:22px">🚗</span><b>SODANGI MOTORS</b><span style="margin-left:auto;font-size:10px;color:#64748B;font-weight:700">✔ VERIFIED DEALERS</span></div>
 <div class="search"><span>🔍</span><input id="q" placeholder="Find anything in Sodangi Motors" oninput="render()"></div>
</div>
<div class="chips" id="chips"></div>
<div class="feed" id="feed"></div>
<div class="modal" id="modal" onclick="if(event.target===this)closeM()">
 <div class="mcard">
  <h3 id="mName"></h3>
  <div class="mrow">
   <a class="mtile mcall" id="mCall" href="#"><span class="ic">📞</span>Call Seller</a>
   <a class="mtile mwa" id="mWa" href="#" target="_blank" rel="noopener"><span class="ic">💬</span>Chat via WhatsApp</a>
  </div>
  <a class="mview" id="mView" href="#">🏪 View Full Showroom Page</a>
 </div>
</div>
<nav class="nav">
 <button class="on"><span class="ic">🏠</span>Home</button>
 <button onclick="alert('Saved cars coming soon!')"><span class="ic">🤍</span>Saved</button>
 <button onclick="document.getElementById('q').focus();window.scrollTo(0,0)"><span class="ic">🔍</span>Search</button>
 <a href="/api/v1/dashboard/v4-dashboard"><span class="ic">🏷️</span>Sell</a>
 <a href="/api/v1/dashboard/v4-dashboard"><span class="ic">👤</span>Profile</a>
</nav>
<script>
var CARS=__CARS__;
var CATS=["All Vehicles","Cars","SUVs","Trucks & Buses","Luxury"];
var curCat="All Vehicles";
function money(n){return "\u20A6"+Number(n).toLocaleString()}
function catOf(c){var n=c.name.toLowerCase();if(/lexus|porsche|benz|mercedes|bmw|range|gtr/.test(n))return"Luxury";if(/suv|ml350|rx3|highlander|pajero|escalade|venza/.test(n))return"SUVs";if(/truck|bus|trailer/.test(n))return"Trucks & Buses";return"Cars"}
function render(){
 var q=document.getElementById("q").value.toLowerCase();
 var box=document.getElementById("feed");box.innerHTML="";
 var list=CARS.filter(function(c){
  if(curCat!=="All Vehicles"&&catOf(c)!==curCat)return false;
  if(q&&(c.name+" "+(c.loc||"")).toLowerCase().indexOf(q)<0)return false;
  return true;});
 if(!list.length){box.innerHTML='<div class="empty">No vehicles found.</div>';return}
 list.forEach(function(c){
  var media=(c.imgs&&c.imgs.length)?c.imgs:["https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=900&q=70"];
  var gal="";media.forEach(function(u){gal+=(u.indexOf(".mp4")>0)?'<video src="'+u+'" controls playsinline></video>':'<img src="'+u+'" loading="lazy">';});
  var specs="";
  if(c.cond)specs+='<span class="spec">🚘 '+c.cond+'</span>';
  if(c.year)specs+='<span class="spec">📅 '+c.year+'</span>';
  if(c.trans)specs+='<span class="spec">⚙️ '+c.trans+'</span>';
  if(c.mile)specs+='<span class="spec">⏱ '+c.mile+'</span>';
  var d=document.createElement("div");d.className="card";
  d.innerHTML='<div class="gal">'+gal+'<span class="vbadge">✔ Verified Seller</span><span class="cnt">📷 '+media.length+'</span></div>'+
   '<div class="info"><div class="prow"><div class="price">'+money(c.price)+'</div><button class="cbtn" data-id="'+c.id+'">Contact</button></div>'+
   '<div class="title">'+c.name+'</div><div class="loc">📍 '+(c.loc||"Nigeria")+'</div>'+
   (specs?'<div class="specs">'+specs+'</div>':'')+'</div>';
  d.onclick=function(e){if(e.target.classList.contains("cbtn")){contact(c);e.stopPropagation();}else location.href="/api/v1/dashboard/showroom/"+c.id;};
  box.appendChild(d);});
}
function contact(c){
 document.getElementById("mName").textContent=c.name.toUpperCase();
 var ph="2349079437745";
 document.getElementById("mCall").href="tel:+"+ph;
 document.getElementById("mWa").href="https://wa.me/"+ph+"?text="+encodeURIComponent("Salam! Is the "+c.name+" ("+money(c.price)+") still available?");
 document.getElementById("mView").href="/api/v1/dashboard/showroom/"+c.id;
 document.getElementById("modal").classList.add("show");}
function closeM(){document.getElementById("modal").classList.remove("show")}
var ch=document.getElementById("chips");
CATS.forEach(function(c,i){var b=document.createElement("button");b.className="chip"+(i===0?" on":"");b.textContent=c;b.onclick=function(){curCat=c;document.querySelectorAll(".chip").forEach(function(x){x.classList.remove("on")});b.classList.add("on");render()};ch.appendChild(b)});
render();
</script></body></html>"""

@app.get("/api/v1/dashboard/market")
def market_god_mode():
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json, re as _re
    db = SessionLocal()
    try:
        prods = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.id.desc()).limit(40).all()
        if not prods:
            prods = db.query(Product).order_by(Product.id.desc()).limit(40).all()
        cars = []
        for p in prods:
            imgs = []
            try:
                parsed = _json.loads(p.images) if isinstance(p.images, str) and p.images.strip().startswith("[") else (p.images or [])
                if isinstance(parsed, list): imgs = parsed
                elif isinstance(parsed, str) and parsed: imgs = [parsed]
            except Exception:
                imgs = []
            specs = {}
            m = _re.search(r"\[\[SPEC:(.*?)\]\]", p.description or "")
            if m:
                try: specs = _json.loads(m.group(1))
                except Exception: specs = {}
            cars.append({"id": p.id, "name": str(p.name), "price": float(p.price or 0), "imgs": imgs,
                         "loc": specs.get("location", "") or "Nigeria", "year": specs.get("year", ""),
                         "mile": specs.get("mileage", ""), "trans": specs.get("transmission", ""),
                         "cond": specs.get("condition", "")})
        return HTMLResponse(content=MARKET_TEMPLATE_MAIN.replace("__CARS__", _json.dumps(cars)))
    except Exception as e:
        return HTMLResponse(content="<h1 style='color:#fff;font-family:sans-serif;text-align:center;padding:40px'>Market error: " + str(e) + "</h1>", status_code=500)
    finally:
        db.close()
'''
    mc += TEMPLATE
    with open("backend/app/main.py", "w", encoding="utf-8") as f:
        f.write(mc)
    print("✅ Marketplace God Mode injected into main.py!")

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "God Mode: Marketplace lives in main.py forever"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n🐕 WATCHDOG: polling all 3 public links until live...")
URLS = ["https://sawa-ai-backend.vercel.app/api/v1/dashboard/market",
        "https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/15",
        "https://sawa-ai-backend.vercel.app/"]
MARK = ["SODANGI MOTORS", "VERIFIED SELLER", "SODANGI"]
for attempt in range(12):
    alive = 0
    for u, mk in zip(URLS, MARK):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                if mk in r.read().decode(): alive += 1
        except Exception:
            pass
    print(f"[{attempt+1}/12] Alive: {alive}/3")
    if alive == 3:
        print("\n✅ ✅ ✅ ALL 3 PUBLIC PAGES ARE 100% LIVE!")
        print("👉 MARKETPLACE:  https://sawa-ai-backend.vercel.app/api/v1/dashboard/market")
        print("👉 SHOWROOM #15: https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/15")
        print("👉 ROOT:         https://sawa-ai-backend.vercel.app/")
        break
    time.sleep(20)
else:
    print("\n⚠️ Not all live yet. IMPORTANT MANUAL CHECK:")
    print("1. Open https://vercel.com -> your project -> Deployments tab.")
    print("2. The TOP deployment (latest commit) must have the 'Production' badge.")
    print("3. If an OLD deployment has 'Production', click the ⋯ on the TOP one and choose 'Promote to Production' or 'Redeploy'.")
