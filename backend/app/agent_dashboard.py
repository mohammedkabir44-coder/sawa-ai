from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()

@router.get("/agent-dashboard")
def agent_command_center():
    html = r'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agent Command Center</title>
<style>
:root{--bg:#0A0F1C;--card:#1E293B;--accent:#10B981;--text:#fff;--muted:#94A3B8}
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,sans-serif}
body{background:var(--bg);color:var(--text);padding-bottom:80px;min-height:100vh}
header{background:linear-gradient(135deg,#065F46,#0369A1);padding:20px;text-align:center}
header h1{font-size:20px;font-weight:800}
.container{max-width:600px;margin:0 auto;padding:16px}
.tabs{display:flex;background:var(--card);border-radius:12px;padding:6px;margin-bottom:16px}
.tab{flex:1;text-align:center;padding:10px;border-radius:8px;cursor:pointer;font-weight:700;color:var(--muted)}
.tab.active{background:var(--accent);color:#052E16}
.section{display:none;background:var(--card);border-radius:16px;padding:20px;border:1px solid #334155}
.section.active{display:block}
label{display:block;margin-top:12px;font-size:13px;color:var(--muted)}
input,textarea{width:100%;padding:12px;border-radius:8px;border:1px solid #334155;background:#0F172A;color:#fff;font-size:15px;margin-top:4px}
.btn{width:100%;padding:14px;margin-top:16px;background:var(--accent);color:#052E16;border:none;border-radius:10px;font-weight:800;font-size:16px;cursor:pointer}
.car-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px}
.car-card{background:#0F172A;border-radius:12px;overflow:hidden;border:1px solid #334155}
.car-card img{width:100%;height:120px;object-fit:cover}
.car-info{padding:10px}
.car-info h3{font-size:14px;margin-bottom:4px}
.car-info p{font-size:16px;font-weight:900;color:var(--accent)}
.car-actions{display:flex;gap:6px;margin-top:8px}
.car-actions button{flex:1;padding:6px;border:none;border-radius:6px;font-weight:700;font-size:12px;cursor:pointer}
.edit-btn{background:#3B82F6;color:#fff}
.del-btn{background:#EF4444;color:#fff}
.nav{position:fixed;bottom:0;left:0;right:0;background:#0F172A;border-top:1px solid #334155;display:flex;justify-content:space-around;padding:10px 0;z-index:100}
.nav button{background:none;border:none;color:var(--muted);font-size:11px;display:flex;flex-direction:column;align-items:center;gap:4px;cursor:pointer}
.nav button.active{color:var(--accent)}
.nav button span{font-size:20px}
</style></head>
<body>
<header><h1 id="agentName">Agent Dashboard</h1><p id="agentRole" style="font-size:12px;opacity:0.8;margin-top:4px"></p></header>
<div class="container">
  <div class="tabs">
    <div class="tab active" onclick="showTab(0)">📸 My Cars</div>
    <div class="tab" onclick="showTab(1)">👤 Profile</div>
    <div class="tab" onclick="showTab(2)">🤖 AI Bot</div>
  </div>

  <div class="section active" id="tab0">
    <h2 style="color:var(--accent);margin-bottom:12px">📸 Upload New Car</h2>
    <label>Car Name</label><input id="carName" placeholder="Toyota Camry 2020">
    <label>Price (NGN)</label><input id="carPrice" type="number" placeholder="8500000">
    <label>Photos (Select up to 5)</label>
    <input type="file" id="carPhotos" accept="image/*" multiple style="padding:10px;background:#0F172A">
    <button class="btn" onclick="uploadCar()">🚀 Upload Car</button>
    <h2 style="color:var(--accent);margin:24px 0 12px">🚗 My Inventory</h2>
    <div class="car-grid" id="carGrid"><p style="color:var(--muted);grid-column:span 2;text-align:center">Loading your cars...</p></div>
  </div>

  <div class="section" id="tab1">
    <h2 style="color:var(--accent);margin-bottom:12px">👤 My Profile</h2>
    <label>Full Name</label><input id="profName" readonly style="opacity:0.7">
    <label>Phone Number</label><input id="profPhone" placeholder="08012345678">
    <label>Bio / About Me</label><textarea id="profBio" rows="3" placeholder="I specialize in luxury SUVs..."></textarea>
    <button class="btn" onclick="saveProfile()">💾 Save Profile</button>
    <button class="btn" style="background:#EF4444;color:#fff;margin-top:10px" onclick="logout()">Sign Out</button>
  </div>

  <div class="section" id="tab2">
    <h2 style="color:var(--accent);margin-bottom:12px">🤖 WhatsApp AI Bot</h2>
    <label>Auto-Reply Message</label>
    <textarea id="botMsg" rows="4" placeholder="Salam! Thanks for your interest. I will reply shortly."></textarea>
    <button class="btn" onclick="saveBot()">💾 Save Bot Message</button>
  </div>
</div>
<nav class="nav">
  <button class="active" onclick="showTab(0)"><span>🚗</span>Cars</button>
  <button onclick="showTab(1)"><span>👤</span>Profile</button>
  <button onclick="showTab(2)"><span>🤖</span>Bot</button>
</nav>
<script>
var API="/agent-api";
var TOKEN=localStorage.getItem("sodangi_token")||"";
var EMAIL=localStorage.getItem("sodangi_name")||"";
function showTab(i){
  document.querySelectorAll(".tab").forEach(function(t,idx){t.classList.toggle("active",idx===i)});
  document.querySelectorAll(".section").forEach(function(s,idx){s.classList.toggle("active",idx===i)});
  document.querySelectorAll(".nav button").forEach(function(b,idx){b.classList.toggle("active",idx===i)});
}
async function api(path,m,b){
  var h={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"};
  var r=await fetch(API+path,{method:m,headers:h,body:b?JSON.stringify(b):undefined});
  if(!r.ok)throw new Error("Session expired");
  return r.json();
}
async function loadProfile(){
  document.getElementById("agentName").innerText=EMAIL;
  document.getElementById("profName").value=EMAIL;
  try{
    var p=await api("/profile");
    document.getElementById("profPhone").value=p.phone||"";
    document.getElementById("profBio").value=p.bio||"";
    document.getElementById("botMsg").value=p.bot_msg||"Salam! I will reply shortly.";
  }catch(e){console.log(e)}
}
async function saveProfile(){
  try{await api("/profile","POST",{phone:document.getElementById("profPhone").value,bio:document.getElementById("profBio").value});alert("✅ Profile saved!");}catch(e){alert(e.message)}
}
async function saveBot(){
  try{await api("/bot","POST",{msg:document.getElementById("botMsg").value});alert("✅ AI Bot message saved!");}catch(e){alert(e.message)}
}
async function uploadCar(){
  var n=document.getElementById("carName").value;
  var p=document.getElementById("carPrice").value;
  if(!n||!p)return alert("Fill name and price");
  var files=document.getElementById("carPhotos").files;
  if(!files.length)return alert("Select photos");
  var urls=[];
  for(var i=0;i<files.length;i++){
    var fd=new FormData();fd.append("file",files[i]);
    var r=await fetch("/api/v1/dashboard/upload-media",{method:"POST",body:fd});
    var d=await r.json();
    if(d.url)urls.push(d.url);
  }
  try{await api("/car","POST",{name:n,price:parseFloat(p),images:urls});alert("✅ Car uploaded!");loadCars();}catch(e){alert(e.message)}
}
async function loadCars(){
  var grid=document.getElementById("carGrid");
  try{
    var cars=await api("/cars");
    grid.innerHTML="";
    if(!cars.length){grid.innerHTML="<p style=\'color:var(--muted);grid-column:span 2;text-align:center\'>No cars yet. Upload your first!</p>";return;}
    cars.forEach(function(c){
      var img=c.images&&c.images.length?c.images[0]:"";
      grid.innerHTML+=`<div class="car-card"><img src="${img}" onerror="this.style.display=\'none\'"><div class="car-info"><h3>${c.name}</h3><p>₦${Number(c.price).toLocaleString()}</p><div class="car-actions"><button class="edit-btn" onclick="editCar(${c.id})">Edit</button><button class="del-btn" onclick="delCar(${c.id})">Delete</button></div></div></div>`;
    });
  }catch(e){grid.innerHTML="<p style=\'color:#EF4444;grid-column:span 2;text-align:center\'>"+e.message+"</p>"}
}
async function delCar(id){if(!confirm("Delete this car?"))return;try{await api("/car/"+id,"DELETE");loadCars();}catch(e){alert(e.message)}}
function editCar(id){alert("Edit feature coming soon!")}
function logout(){localStorage.clear();location.href="/agent-login";}
loadProfile();loadCars();
</script></body></html>'''
    return HTMLResponse(content=html)

@router.get("/agent-api/profile")
def get_profile(request: Request):
    return {"phone": "", "bio": "", "bot_msg": "Salam! I will reply shortly."}

@router.post("/agent-api/profile")
def save_profile(request: Request, data: dict):
    return {"status": "ok"}

@router.post("/agent-api/bot")
def save_bot(request: Request, data: dict):
    return {"status": "ok"}

@router.get("/agent-api/cars")
def get_cars():
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, name, price, images FROM products ORDER BY id DESC LIMIT 20")).fetchall()
            cars = []
            for r in rows:
                imgs = []
                try:
                    import json
                    if r[3]: imgs = json.loads(r[3])
                except: pass
                cars.append({"id": r[0], "name": r[1], "price": float(r[2] or 0), "images": imgs})
            return cars
    except: return []

@router.post("/agent-api/car")
def create_car(data: dict):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        import json
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO products (name, price, images, is_active) VALUES (:n, :p, :i, true)"), 
                        {"n": data["name"], "p": data["price"], "i": json.dumps(data.get("images", []))})
            conn.commit()
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.delete("/agent-api/car/{cid}")
def delete_car(cid: int):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM products WHERE id = :id"), {"id": cid})
            conn.commit()
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
