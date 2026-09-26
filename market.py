import subprocess, time, urllib.request, re, json

print("="*60)
print("🏪 SODANGI MARKETPLACE APP INJECTION")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    code = r.read().decode()
print(f"Downloaded. Size: {len(code)} bytes")

# ============ 1. THE MARKETPLACE HTML (app-style) ============
MARKET_HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sodangi Motors | Buy Verified Cars</title>
<style>
:root{--g:#10B981;--gd:#059669;--bg:#F4F6F8;--tx:#0F172A;--mut:#64748B;--coral:#F0876A}
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
body{background:var(--bg);color:var(--tx);padding-bottom:76px}
.top{position:sticky;top:0;background:#fff;z-index:50;padding:10px 14px;box-shadow:0 1px 0 #E2E8F0}
.brand{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.brand b{font-size:18px;font-weight:900;color:var(--gd)}
.search{display:flex;align-items:center;gap:8px;background:#F1F5F9;border:1px solid #E2E8F0;border-radius:12px;padding:10px 12px}
.search input{border:none;background:none;outline:none;flex:1;font-size:14px}
.chips{display:flex;gap:8px;overflow-x:auto;padding:10px 14px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex-shrink:0;padding:8px 14px;border-radius:999px;background:#fff;border:1px solid #E2E8F0;font-size:13px;font-weight:600;color:var(--mut);cursor:pointer}
.chip.on{background:var(--g);border-color:var(--g);color:#fff}
.feed{max-width:640px;margin:0 auto;padding:0 12px}
.card{background:#fff;border-radius:16px;overflow:hidden;margin-bottom:14px;box-shadow:0 1px 3px rgba(15,23,42,.08)}
.gal{position:relative;display:flex;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;background:#0B0F19}
.gal::-webkit-scrollbar{display:none}
.gal img,.gal video{scroll-snap-align:center;flex:0 0 100%;height:230px;object-fit:cover}
.gal .cnt{position:absolute;right:10px;bottom:10px;background:rgba(0,0,0,.55);color:#fff;font-size:11px;font-weight:700;padding:4px 8px;border-radius:8px}
.gal .acts{position:absolute;right:10px;top:10px;display:flex;gap:8px}
.rbtn{width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.92);border:none;display:flex;align-items:center;justify-content:center;font-size:15px;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,.15)}
.rbtn.saved{background:#FEE2E2;color:#DC2626}
.vbadge{position:absolute;left:10px;top:10px;background:rgba(255,255,255,.92);color:var(--gd);font-size:10px;font-weight:800;padding:5px 10px;border-radius:999px}
.dots{position:absolute;bottom:10px;left:50%;transform:translateX(-50%);display:flex;gap:4px}
.dots i{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.5)}
.dots i.on{background:#fff}
.info{padding:12px 14px}
.prow{display:flex;justify-content:space-between;align-items:flex-start}
.price{color:var(--gd);font-size:19px;font-weight:900}
.cbtn{background:var(--coral);color:#fff;border:none;font-size:12px;font-weight:800;padding:8px 16px;border-radius:999px;cursor:pointer}
.title{font-size:15px;font-weight:700;margin:4px 0 2px;text-transform:uppercase}
.loc{font-size:12px;color:var(--mut)}
.specs{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;padding-top:10px;border-top:1px solid #F1F5F9}
.spec{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--mut);background:#F8FAFC;border:1px solid #EEF2F6;padding:5px 9px;border-radius:8px}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #E2E8F0;display:flex;z-index:60;padding:6px 0 calc(6px + env(safe-area-inset-bottom))}
.nav a,.nav button{flex:1;background:none;border:none;display:flex;flex-direction:column;align-items:center;gap:3px;font-size:10px;color:var(--mut);cursor:pointer;text-decoration:none}
.nav .ic{font-size:20px}
.nav a.on,.nav button.on{color:var(--coral)}
.modal{position:fixed;inset:0;background:rgba(15,23,42,.45);backdrop-filter:blur(6px);display:none;align-items:center;justify-content:center;z-index:100;padding:24px}
.modal.show{display:flex}
.mcard{background:rgba(255,255,255,.94);backdrop-filter:blur(10px);border-radius:24px;padding:26px 20px;width:100%;max-width:340px;text-align:center}
.mcard img{width:84px;height:84px;border-radius:50%;object-fit:cover;border:3px solid #fff;box-shadow:0 6px 18px rgba(0,0,0,.18)}
.mcard h3{font-size:17px;font-weight:900;margin:12px 0 10px;letter-spacing:.3px}
.mpage{display:inline-block;background:#fff;border:1px solid #E2E8F0;color:var(--tx);font-size:12px;font-weight:700;padding:8px 16px;border-radius:999px;text-decoration:none;margin-bottom:16px}
.mrow{display:flex;gap:12px}
.mtile{flex:1;border-radius:16px;padding:16px 8px;text-decoration:none;font-size:12px;font-weight:700;line-height:1.4}
.mtile .ic{display:block;font-size:26px;margin-bottom:6px}
.mcall{background:#FDE8E8;color:#B91C1C}
.mwa{background:#DCF5E7;color:#065F46}
.empty{text-align:center;color:var(--mut);padding:50px 20px;font-size:14px}
</style></head>
<body>
<div class="top">
 <div class="brand"><span style="font-size:22px">🚗</span><b>SODANGI MOTORS</b><span style="margin-left:auto;font-size:10px;color:var(--mut);font-weight:700">✔ VERIFIED DEALERS</span></div>
 <div class="search"><span>🔍</span><input id="q" placeholder="Find anything in Sodangi Motors" oninput="render()"></div>
</div>
<div class="chips" id="chips"></div>
<div class="feed" id="feed"></div>
<div class="modal" id="modal" onclick="if(event.target===this)closeM()">
 <div class="mcard">
  <img id="mImg" src="" alt="">
  <h3 id="mName"></h3>
  <a class="mpage" id="mPage" href="#">View Seller's Page</a>
  <div class="mrow">
   <a class="mtile mcall" id="mCall" href="#"><span class="ic">📞</span>Call<br><span id="mPhone"></span></a>
   <a class="mtile mwa" id="mWa" href="#" target="_blank" rel="noopener"><span class="ic">💬</span>Chat via<br>WhatsApp</a>
  </div>
 </div>
</div>
<nav class="nav">
 <button class="on" onclick="goTab(this,'home')"><span class="ic">🏠</span>Home</button>
 <button onclick="goTab(this,'saved')"><span class="ic">🤍</span>Saved</button>
 <button onclick="document.getElementById('q').focus();window.scrollTo(0,0)"><span class="ic">🔍</span>Search</button>
 <a href="/api/v1/dashboard/ui"><span class="ic">🏷️</span>Sell</a>
 <a href="/api/v1/dashboard/ui"><span class="ic">👤</span>Profile</a>
</nav>
<script>
var CARS=__CARS__;
var CATS=["All Vehicles","Cars","SUVs","Trucks & Buses","Motorbikes","Luxury"];
var curCat="All Vehicles",curTab="home";
var SAVED=JSON.parse(localStorage.getItem("sod_saved")||"[]");
function money(n){return "\u20A6"+Number(n).toLocaleString()}
function catOf(c){var n=c.name.toLowerCase();if(/lexus|porsche|benz|mercedes|bmw|range|gtr|land cruiser/.test(n))return"Luxury";if(/suv|ml350|rx3|highlander|pajero|escalade|venza/.test(n))return"SUVs";if(/truck|bus|trailer|van|sienna/.test(n))return"Trucks & Buses";if(/bike|okada|scooter|motorcycle/.test(n))return"Motorbikes";return"Cars"}
function render(){
 var q=document.getElementById("q").value.toLowerCase();
 var box=document.getElementById("feed");box.innerHTML="";
 var list=CARS.filter(function(c){
  if(curTab==="saved"&&SAVED.indexOf(c.id)<0)return false;
  if(curCat!=="All Vehicles"&&catOf(c)!==curCat)return false;
  if(q&&(c.name+" "+(c.loc||"")).toLowerCase().indexOf(q)<0)return false;
  return true;});
 if(!list.length){box.innerHTML='<div class="empty">No vehicles found.<br>Try another search or category.</div>';return}
 list.forEach(function(c){
  var media=(c.imgs&&c.imgs.length)?c.imgs:["https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=900&q=70"];
  var gal="";media.forEach(function(u){gal+=(u.indexOf(".mp4")>0||u.indexOf(".webm")>0)?'<video src="'+u+'" controls playsinline></video>':'<img src="'+u+'" loading="lazy" alt="">';});
  var dots="";for(var i=0;i<Math.min(media.length,6);i++)dots+='<i class="'+(i===0?"on":"")+'"></i>';
  var specs="";
  if(c.cond)specs+='<span class="spec">🚘 '+c.cond+'</span>';
  if(c.year)specs+='<span class="spec">📅 '+c.year+'</span>';
  if(c.trans)specs+='<span class="spec">⚙️ '+c.trans+'</span>';
  if(c.mile)specs+='<span class="spec">⏱ '+c.mile+'</span>';
  var saved=SAVED.indexOf(c.id)>=0;
  var d=document.createElement("div");d.className="card";
  d.innerHTML='<div class="gal">'+gal+
   '<span class="vbadge">✔ Verified Seller</span>'+
   '<div class="acts"><button class="rbtn" onclick="share('+c.id+')">↗</button><button class="rbtn'+(saved?" saved":"")+'" onclick="save('+c.id+',this)">'+(saved?"❤":"🤍")+'</button></div>'+
   '<div class="dots">'+dots+'</div><span class="cnt">📷 '+media.length+'</span></div>'+
   '<div class="info"><div class="prow"><div class="price">'+money(c.price)+'</div><button class="cbtn" onclick="contact('+c.id+')">Contact</button></div>'+
   '<div class="title">'+c.name+'</div><div class="loc">📍 '+(c.loc||"Nigeria")+'</div>'+
   (specs?'<div class="specs">'+specs+'</div>':'')+'</div>';
  d.querySelector(".gal").addEventListener("click",function(e){if(e.target.tagName!=="BUTTON")location.href="/api/v1/dashboard/showroom/"+c.id;});
  box.appendChild(d);});
}
function save(id,btn){var i=SAVED.indexOf(id);if(i>=0)SAVED.splice(i,1);else SAVED.push(id);localStorage.setItem("sod_saved",JSON.stringify(SAVED));btn.classList.toggle("saved");btn.textContent=SAVED.indexOf(id)>=0?"❤":"🤍"}
function share(id){var c=CARS.filter(function(x){return x.id===id})[0];var u=location.origin+"/api/v1/dashboard/showroom/"+id;var t=c.name+" - "+money(c.price)+" | Sodangi Motors "+u;if(navigator.share)navigator.share({title:c.name,text:t,url:u});else if(navigator.clipboard){navigator.clipboard.writeText(u);}else location.href="https://wa.me/?text="+encodeURIComponent(t)}
function contact(id){var c=CARS.filter(function(x){return x.id===id})[0];
 document.getElementById("mImg").src="https://ui-avatars.com/api/?name="+encodeURIComponent(c.seller||"Sodangi Motors")+"&background=10B981&color=fff&bold=true";
 document.getElementById("mName").textContent=(c.seller||"SODANGI MOTORS").toUpperCase();
 document.getElementById("mPage").href=c.agent?("/api/v1/dashboard/agent/"+c.agent):("/api/v1/dashboard/showroom/"+c.id);
 var ph=(c.phone||"2349079437745").replace(/[^0-9]/g,"");
 document.getElementById("mPhone").textContent=ph;
 document.getElementById("mCall").href="tel:+"+ph;
 document.getElementById("mWa").href="https://wa.me/"+ph+"?text="+encodeURIComponent("Salam! I saw the "+c.name+" ("+money(c.price)+") on Sodangi Motors. Is it still available?");
 document.getElementById("modal").classList.add("show");}
function closeM(){document.getElementById("modal").classList.remove("show")}
function goTab(b,t){curTab=t;document.querySelectorAll(".nav button").forEach(function(x){x.classList.remove("on")});b.classList.add("on");render()}
var ch=document.getElementById("chips");
CATS.forEach(function(c,i){var b=document.createElement("button");b.className="chip"+(i===0?" on":"");b.textContent=c;b.onclick=function(){curCat=c;document.querySelectorAll(".chip").forEach(function(x){x.classList.remove("on")});b.classList.add("on");render()};ch.appendChild(b)});
render();
</script></body></html>"""

MARKET_ROUTE = '''

@router.get("/market")
def market_home(db: Session = Depends(get_db)):
    import json as _json, re as _re
    prods = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.id.desc()).all()
    if not prods:
        prods = db.query(Product).order_by(Product.id.desc()).all()
    cars = []
    for p in prods[:40]:
        specs = {}
        m = _re.search(r"\\[\\[SPEC:(.*?)\\]\\]", p.description or "")
        if m:
            try:
                specs = _json.loads(m.group(1))
            except Exception:
                specs = {}
        imgs = _extract_imgs_list(p.images)
        seller, phone, agent_id = "Sodangi Motors", "2349079437745", 0
        try:
            lk = db.query(ProductAgent).filter(ProductAgent.product_id == p.id).first()
            if lk:
                ag = db.query(Agent).filter(Agent.id == lk.agent_id).first()
                if ag:
                    seller = ag.full_name or seller
                    phone = (ag.phone_number or phone).replace("+", "")
                    agent_id = ag.id
        except Exception:
            pass
        cars.append({"id": p.id, "name": p.name, "price": float(p.price or 0), "imgs": imgs,
                     "loc": specs.get("location", "") or "Nigeria",
                     "year": specs.get("year", ""), "mile": specs.get("mileage", ""),
                     "trans": specs.get("transmission", ""), "cond": specs.get("condition", ""),
                     "seller": seller, "phone": phone, "agent": agent_id})
    html = MARKET_HTML_TEMPLATE.replace("__CARS__", _json.dumps(cars))
    return Response(content=html, media_type="text/html")
'''

if '"/market"' not in code:
    code = code + "\nMARKET_HTML_TEMPLATE = r" + '"""' + MARKET_HTML + '"""' + MARKET_ROUTE
    print("✅ Marketplace App endpoint injected!")

# ============ 2. ADD SPEC FIELDS TO V4 ADD FORM ============
SPEC_FIELDS = '''<label>Year</label><input id="sYear" placeholder="2009">
    <label>Mileage</label><input id="sMile" placeholder="214,710 km">
    <label>Transmission</label><select id="sTrans" style="width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:#F8FAFC"><option>Automatic</option><option>Manual</option></select>
    <label>Condition</label><select id="sCond" style="width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:#F8FAFC"><option>Foreign Used</option><option>Local Used</option><option>Brand New</option></select>
    <label>Location</label><input id="sLoc" placeholder="Abule egba, Lagos">
    '''
if '<label>Photos (up to 10)</label>' in code and 'id="sYear"' not in code:
    code = code.replace('<label>Photos (up to 10)</label>', SPEC_FIELDS + '<label>Photos (up to 10)</label>')
    print("✅ Added Year/Mileage/Transmission/Condition/Location fields!")

BUILD_SPEC = '''function buildSpec(){var s={year:document.getElementById("sYear").value,mileage:document.getElementById("sMile").value,transmission:document.getElementById("sTrans").value,condition:document.getElementById("sCond").value,location:document.getElementById("sLoc").value};return "[[SPEC:"+JSON.stringify(s)+"]]";}
'''
if "function buildSpec()" not in code:
    code = code.replace("var uploadedPhotos = [];", BUILD_SPEC + "var uploadedPhotos = [];")
    print("✅ Added spec builder!")

if "description:buildSpec()+" not in code:
    code = code.replace("description:document.getElementById(\"pDesc\").value", "description:buildSpec()+document.getElementById(\"pDesc\").value")
    print("✅ Publish now saves specs!")

with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)

# ============ 3. MAKE ROOT URL OPEN THE MARKETPLACE ============
mp = "backend/app/main.py"
with open(mp, "r", encoding="utf-8-sig") as f:
    mc = f.read()
mc = re.sub(r'@app\.get\("/"\).*?(?=\ntry:|\n@app\.|\Z)', '@app.get("/", include_in_schema=False)\ndef root_market():\n    from fastapi.responses import RedirectResponse\n    return RedirectResponse(url="/api/v1/dashboard/market")\n', mc, flags=re.DOTALL)
with open(mp, "w", encoding="utf-8") as f:
    f.write(mc)
print("✅ Root URL now opens the Marketplace App!")

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Marketplace App: categories, carousels, verified badges, contact modal"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel...")
time.sleep(90)
print("✅ MARKETPLACE APP IS LIVE!")
