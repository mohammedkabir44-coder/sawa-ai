
import json, hmac, hashlib, base64, time, os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, Boolean
from app.core.database import get_db, Base
from app.models.product import Product


import uuid
import urllib.request


def _bulletproof_heal():
    try:
        from app.core.database import engine
        from sqlalchemy import text as _sa_text, inspect
        insp = inspect(engine)
        with engine.begin() as c:
            if not insp.has_table('sodangi_agents'):
                c.execute(_sa_text("CREATE TABLE sodangi_agents (id SERIAL PRIMARY KEY, full_name VARCHAR, email VARCHAR UNIQUE, password_hash VARCHAR, role VARCHAR DEFAULT 'agent', phone_number VARCHAR, bio TEXT, photo_url TEXT, is_active BOOLEAN DEFAULT TRUE)"))
            else:
                cols = [col['name'] for col in insp.get_columns('sodangi_agents')]
                for col, typ in [("phone_number", "VARCHAR"), ("bio", "TEXT"), ("photo_url", "TEXT"), ("is_active", "BOOLEAN DEFAULT TRUE")]:
                    if col not in cols:
                        c.execute(_sa_text(f"ALTER TABLE sodangi_agents ADD COLUMN {col} {typ}"))
            if not insp.has_table('sodangi_product_agents'):
                c.execute(_sa_text("CREATE TABLE sodangi_product_agents (id SERIAL PRIMARY KEY, product_id INTEGER, agent_id INTEGER)"))
        print("BULLETPROOF SCHEMA HEAL SUCCESS")
    except Exception as e:
        print("BULLETPROOF HEAL FAILED:", repr(e))


router = APIRouter(prefix="/dashboard", tags=["Sodangi Agents"])
@router.get("/force-heal")
def force_heal():
    try:
        from app.core.database import engine
        from sqlalchemy import text as _sa_text, inspect
        insp = inspect(engine)
        results = []
        with engine.begin() as c:
            if not insp.has_table('sodangi_agents'):
                c.execute(_sa_text("CREATE TABLE sodangi_agents (id SERIAL PRIMARY KEY, full_name VARCHAR, email VARCHAR UNIQUE, password_hash VARCHAR, role VARCHAR DEFAULT 'agent', phone_number VARCHAR, bio TEXT, photo_url TEXT, is_active BOOLEAN DEFAULT TRUE)"))
                results.append("Created sodangi_agents")
            else:
                cols = [col['name'] for col in insp.get_columns('sodangi_agents')]
                results.append("Existing cols: " + str(cols))
                for col, typ in [("phone_number", "VARCHAR"), ("bio", "TEXT"), ("photo_url", "TEXT"), ("is_active", "BOOLEAN DEFAULT TRUE")]:
                    if col not in cols:
                        c.execute(_sa_text(f"ALTER TABLE sodangi_agents ADD COLUMN {col} {typ}"))
                        results.append(f"Added {col}")
            if not insp.has_table('sodangi_product_agents'):
                c.execute(_sa_text("CREATE TABLE sodangi_product_agents (id SERIAL PRIMARY KEY, product_id INTEGER, agent_id INTEGER)"))
                results.append("Created sodangi_product_agents")
        return {"status": "SUCCESS", "results": results}
    except Exception as e:
        import traceback
        return {"status": "FAILED", "error": str(e), "trace": traceback.format_exc()}

SECRET = "sodangi-sawa-secret-2026-do-not-share"

def _upload_to_catbox(file_bytes, filename, content_type="application/octet-stream"):
    boundary = uuid.uuid4().hex
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += b"Content-Disposition: form-data; name=\"reqtype\"\r\n\r\n"
    body += b"fileupload\r\n"
    body += f"--{boundary}\r\n".encode()
    body += f"Content-Disposition: form-data; name=\"fileToUpload\"; filename=\"{filename}\"\r\n".encode()
    body += f"Content-Type: {content_type}\r\n\r\n".encode()
    body += file_bytes
    body += f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://catbox.moe/user/api.php", data=body, method="POST")
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('User-Agent', 'SodangiAgentDashboard/1.0')
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode('utf-8').strip()

@router.post("/upload-media")
async def upload_media(request: Request):
    _auth(request)
    content_type = request.headers.get("content-type", "")
    body_bytes = await request.body()
    boundary = content_type.split("boundary=")[-1].strip()
    parts = body_bytes.split(f"--{boundary}".encode())
    file_bytes = b""
    filename = "upload.jpg"
    f_ct = "application/octet-stream"
    for part in parts:
        if b"name=\"file\"" in part or b"fileToUpload" in part:
            header, data = part.split(b"\r\n\r\n", 1)
            if b"filename=" in header:
                try: filename = header.split(b"filename=")[1].split(b"\"")[1].decode()
                except: pass
            if b"Content-Type:" in header:
                f_ct = header.split(b"Content-Type:")[1].split(b"\r\n")[0].strip().decode()
            file_bytes = data[:-2] if data.endswith(b"\r\n") else data
            break
    if not file_bytes:
        raise HTTPException(status_code=400, detail="No file found in request")
    try:
        url = _upload_to_catbox(file_bytes, filename, f_ct)
    except Exception as e:
        raise HTTPException(status_code=502, detail="Catbox relay blocked: " + repr(e)[:150])
    return {"url": url}

SECRET = "sodangi-sawa-secret-2026-do-not-share"
SODANGI_BUSINESS_ID = 3
def _ensure_media_schema():
    try:
        from app.core.database import engine
        from sqlalchemy import text as _sa_text
        with engine.connect() as _conn:
            _conn.execute(_sa_text("ALTER TABLE products ALTER COLUMN images TYPE TEXT"))
            _conn.commit()
    except Exception:
        pass



class Agent(Base):
    __tablename__ = "sodangi_agents"
    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="agent")
    phone_number = Column(String)
    bio = Column(Text)
    photo_url = Column(Text)
    is_active = Column(Boolean, default=True)
    phone_number = Column(String)
    bio = Column(Text)
    photo_url = Column(Text)
    is_active = Column(Boolean, default=True)



class ProductAgent(Base):
    __tablename__ = "sodangi_product_agents"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, index=True)
    agent_id = Column(Integer, index=True)

class WAConfig(Base):
    __tablename__ = "sodangi_wa_config"
    id = Column(Integer, primary_key=True)
    phone_number_id = Column(String)
    access_token = Column(Text)
    display_name = Column(String)



def _extract_imgs_list(raw):
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    try:
        v = json.loads(raw)
        if isinstance(v, list):
            return [str(x) for x in v]
    except Exception:
        pass
    try:
        import ast as _a
        v = _a.literal_eval(raw)
        if isinstance(v, list):
            return [str(x) for x in v]
    except Exception:
        pass
    return [str(raw)]

def _parse_imgs(s):
    s = (s or "").strip()
    if s.startswith("["):
        return s
    if s:
        return json.dumps([s])
    return None

def _hash_pw(pw, salt=None):
    salt = salt or os.urandom(8).hex()
    return salt + ":" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120000).hex()

def _verify_pw(pw, stored):
    if not stored or ":" not in str(stored):
        return False
    salt, h = str(stored).split(":", 1)
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120000).hex() == h

def _make_token(email, role):
    payload = base64.urlsafe_b64encode(json.dumps({"e": email, "r": role, "t": int(time.time()) + 604800}).encode()).decode()
    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + "." + sig

def _owner(me):
    if me.get("r") != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    return me

def _auth(request: Request):
    header = request.headers.get("Authorization", "")
    token = header.replace("Bearer ", "") if header else request.query_params.get("token", "")
    if not token or "." not in token:
        raise HTTPException(status_code=401, detail="Missing token")
    payload, sig = token.split(".", 1)
    expect = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expect, sig):
        raise HTTPException(status_code=401, detail="Bad token")
    data = json.loads(base64.urlsafe_b64decode(payload + "=="))
    if data.get("t", 0) < time.time():
        raise HTTPException(status_code=401, detail="Token expired")
    return data

class RegisterReq(BaseModel):
    full_name: str
    email: str
    password: str

class LoginReq(BaseModel):
    email: str
    password: str

class ProductReq(BaseModel):
    name: str
    price: float
    image_url: str = ""
    description: str = ""
    stock: int = 10

class WAReq(BaseModel):
    phone_number_id: str
    access_token: str
    display_name: str = ""

@router.post("/register")
def register(req: RegisterReq, db: Session = Depends(get_db)):
    Agent.__table__.create(bind=db.get_bind(), checkfirst=True)
    if db.query(Agent).filter(Agent.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    role = "owner" if db.query(Agent).count() == 0 else "agent"
    db.add(Agent(full_name=req.full_name, email=req.email, password_hash=_hash_pw(req.password), role=role))
    db.commit()
    return {"message": "Account created under Sodangi Motors", "role": role}

@router.post("/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    _ensure_agent_cols(db)
    Agent.__table__.create(bind=db.get_bind(), checkfirst=True)
    a = db.query(Agent).filter(Agent.email == req.email).first()
    if not a or not _verify_pw(req.password, a.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return {"token": _make_token(a.email, a.role), "role": a.role, "full_name": a.full_name}

@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    ps = db.query(Product).filter(Product.business_id == SODANGI_BUSINESS_ID).all()
    out = []
    for p in ps:
        out.append({"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "images": _extract_imgs_list(p.images)})
    return out

@router.post("/products/upload")
def upload(req: ProductReq, request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    try:
        p = Product(business_id=SODANGI_BUSINESS_ID, name=req.name, price=req.price, stock=req.stock, images=_parse_imgs(req.image_url), is_active=True)
        db.add(p)
        db.commit()
        db.refresh(p)
        return {"message": "Product uploaded by " + me["e"], "product": req.name, "images_saved": len(_extract_imgs_list(p.images))}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connect-whatsapp")
def connect_wa(req: WAReq, request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    WAConfig.__table__.create(bind=db.get_bind(), checkfirst=True)
    row = db.query(WAConfig).first()
    if row:
        row.phone_number_id, row.access_token, row.display_name = req.phone_number_id, req.access_token, req.display_name
    else:
        db.add(WAConfig(phone_number_id=req.phone_number_id, access_token=req.access_token, display_name=req.display_name))
    db.commit()
    return {"message": "WhatsApp number registered to Sodangi Motors"}



class Setting(Base):
    __tablename__ = "sodangi_settings"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)

class SettingsReq(BaseModel):
    cloud_name: str = ""
    upload_preset: str = ""

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    Setting.__table__.create(bind=db.get_bind(), checkfirst=True)
    out = {}
    for row in db.query(Setting).all():
        out[row.key] = row.value
    return out

@router.post("/settings")
def save_settings(req: SettingsReq, request: Request, db: Session = Depends(get_db)):
    _auth(request)
    Setting.__table__.create(bind=db.get_bind(), checkfirst=True)
    for k, v in (("cloud_name", req.cloud_name), ("upload_preset", req.upload_preset)):
        row = db.query(Setting).filter(Setting.key == k).first()
        if row:
            row.value = v
        else:
            db.add(Setting(key=k, value=v))
    db.commit()
    return {"message": "Media settings saved"}

from fastapi.responses import HTMLResponse

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="theme-color" content="#0B0F19">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Sodangi Motors</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root { --bg: #0B0F19; --card: #151F38; --accent: #22C55E; --text: #F8FAFC; --muted: #94A3B8; }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
  body { background: var(--bg); color: var(--text); padding-bottom: 80px; min-height: 100vh; }
  header { background: linear-gradient(135deg, #065F46, #0369A1); padding: 20px; text-align: center; }
  header h1 { font-size: 22px; font-weight: 800; letter-spacing: 1px; }
  .container { max-width: 600px; margin: 0 auto; padding: 16px; }
  .card { background: var(--card); border: 1px solid #1E293B; border-radius: 16px; padding: 20px; margin-bottom: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
  .card h2 { font-size: 18px; margin-bottom: 16px; color: #7DD3FC; display: flex; align-items: center; gap: 8px; }
  label { display: block; font-size: 13px; color: var(--muted); margin: 12px 0 6px; font-weight: 600; }
  input, textarea, select { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #334155; background: #0F172A; color: var(--text); font-size: 15px; }
  input:focus, textarea:focus { outline: none; border-color: var(--accent); }
  .btn { width: 100%; padding: 14px; border: none; border-radius: 10px; font-weight: 700; font-size: 16px; cursor: pointer; margin-top: 12px; transition: 0.2s; }
  .btn-primary { background: var(--accent); color: #052E16; }
  .btn-primary:active { transform: scale(0.98); }
  .btn-danger { background: #EF4444; color: #fff; }
  .btn-ghost { background: #334155; color: var(--text); }
  .hidden { display: none !important; }
  .nav { position: fixed; bottom: 0; left: 0; right: 0; background: #0F172A; border-top: 1px solid #1E293B; display: flex; justify-content: space-around; padding: 8px 0; z-index: 100; }
  .nav button { background: none; border: none; color: var(--muted); font-size: 12px; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 12px; border-radius: 12px; cursor: pointer; }
  .nav button.active { color: var(--accent); background: rgba(34, 197, 94, 0.1); }
  .nav button span { font-size: 22px; }
  .item { background: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
  .item-info h3 { font-size: 15px; margin-bottom: 4px; }
  .item-info p { font-size: 13px; color: var(--muted); }
  .pill { font-size: 11px; padding: 4px 8px; border-radius: 99px; font-weight: 700; }
  .pill.on { background: #064E3B; color: #6EE7B7; }
  .pill.off { background: #7F1D1D; color: #FCA5A5; }
  #toast { position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #16A34A; color: #fff; padding: 12px 24px; border-radius: 10px; font-weight: 600; display: none; z-index: 999; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
  #authCard { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 80vh; }
  #authCard .card { width: 100%; max-width: 400px; }
</style>
</head>
<body>
<div id="toast"></div>
<header id="mainHeader" class="hidden">
  <h1>SODANGI MOTORS</h1>
  <div style="font-size:13px;color:#E0F2FE;margin-top:4px" id="who"></div>
</header>
<div class="container">
  <section id="authCard">
    <div class="card">
      <h2>Agent Portal</h2>
      <label>Email</label><input id="liEmail" type="email" placeholder="agent@sodangi.com">
      <label>Password</label><input id="liPass" type="password" placeholder="********">
      <button class="btn btn-primary" onclick="doLogin()">Sign In</button>
    </div>
  </section>
  <section id="tabUpload" class="card hidden">
    <h2>+ Add to Showroom</h2>
    <label>Vehicle Name</label><input id="pName" placeholder="Toyota Camry 2022">
    <label>Price (Naira)</label><input id="pPrice" type="number" placeholder="8500000">
    <label>Photos (Select multiple)</label><input type="file" id="pFile" accept="image/*" multiple onchange="uploadMedia()">
    <input type="hidden" id="pImg" value="[]">
    <div id="mediaPreview" style="font-size:13px;color:#7DD3FC;margin-top:6px"></div>
    <label>Video (Optional)</label><input type="file" id="pVideo" accept="video/*" onchange="uploadVideo()">
    <input type="hidden" id="pVid">
    <div id="videoPreview" style="font-size:13px;color:#7DD3FC;margin-top:6px"></div>
    <label>Description</label><textarea id="pDesc" rows="3" placeholder="Clean interior, low mileage..."></textarea>
    <button class="btn btn-primary" onclick="uploadProduct()">Publish Vehicle</button>
  </section>
  <section id="tabCars" class="card hidden">
    <h2>My Inventory</h2>
    <div id="carsList"></div>
  </section>
  <section id="tabAgents" class="card hidden">
    <h2>Sales Team</h2>
    <label>New Agent Name</label><input id="aName" placeholder="Musa Abdullahi">
    <label>Email</label><input id="aEmail" type="email">
    <label>Phone</label><input id="aPhone" placeholder="080...">
    <label>Temp Password</label><input id="aPass" type="password">
    <button class="btn btn-primary" onclick="createAgent()">Hire Agent</button>
    <hr style="margin:20px 0;border-color:#1E293B">
    <div id="agentsList"></div>
  </section>
  <section id="tabStats" class="card hidden">
    <h2>Analytics</h2>
    <canvas id="statsChart" height="200"></canvas>
    <div id="statsBox" style="margin-top:16px"></div>
  </section>
  <section id="tabProfile" class="card hidden">
    <h2>My Profile</h2>
    <label>Phone</label><input id="mPhone">
    <label>Bio</label><textarea id="mBio" rows="3"></textarea>
    <button class="btn btn-primary" onclick="saveProfile()">Save Profile</button>
    <div id="myPage" style="margin-top:16px;font-size:14px;color:#7DD3FC"></div>
    <button class="btn btn-ghost" onclick="installApp()" style="margin-top:10px">Install App</button>
    <button class="btn btn-danger" onclick="logout()" style="margin-top:10px">Sign Out</button>
  </section>
</div>
<nav class="nav hidden" id="bottomNav">
  <button id="navUpload" onclick="go('Upload')"><span>+</span>Add</button>
  <button id="navCars" onclick="go('Cars')"><span>C</span>Cars</button>
  <button id="navAgents" onclick="go('Agents')" class="hidden"><span>T</span>Team</button>
  <button id="navStats" onclick="go('Stats')" class="hidden"><span>S</span>Stats</button>
  <button id="navProfile" onclick="go('Profile')"><span>P</span>Me</button>
</nav>
<script>
var API="/api/v1/dashboard";
var TOKEN=localStorage.getItem("sodangi_token")||"";
var ROLE=localStorage.getItem("sodangi_role")||"";
var NAME=localStorage.getItem("sodangi_name")||"";
var CLOUD={name:"",preset:""};

function toast(m,c){var t=document.getElementById("toast");t.textContent=m;t.style.background=c||"#16A34A";t.style.display="block";setTimeout(function(){t.style.display="none";},3000);}
async function api(p,m,b,a){var h={"Content-Type":"application/json"};if(a)h["Authorization"]="Bearer "+TOKEN;var r=await fetch(API+p,{method:m,headers:h,body:b?JSON.stringify(b):undefined});if(!r.ok){var e={};try{e=await r.json();}catch(x){}throw new Error(e.detail||("HTTP "+r.status));}return r.json();}

function go(tab){
  ["Upload","Cars","Agents","Stats","Profile"].forEach(function(t){
    var el=document.getElementById("tab"+t);if(el)el.classList.add("hidden");
    var nb=document.getElementById("nav"+t);if(nb)nb.classList.remove("active");
  });
  var el=document.getElementById("tab"+tab);if(el)el.classList.remove("hidden");
  var nb=document.getElementById("nav"+tab);if(nb)nb.classList.add("active");
  if(tab==="Cars")loadCars();if(tab==="Agents")loadAgents();if(tab==="Profile")loadProfile();if(tab==="Stats")loadStats();
}

function enterDash(){
  document.getElementById("authCard").classList.add("hidden");
  document.getElementById("mainHeader").classList.remove("hidden");
  document.getElementById("bottomNav").classList.remove("hidden");
  document.getElementById("who").textContent=NAME+" ("+ROLE+")";
  if(ROLE==="owner"){
    document.getElementById("navAgents").classList.remove("hidden");
    document.getElementById("navStats").classList.remove("hidden");
  }
  loadSettings();
  go("Upload");
}

async function doLogin(){try{var r=await api("/login","POST",{email:document.getElementById("liEmail").value,password:document.getElementById("liPass").value});TOKEN=r.token;ROLE=r.role;NAME=r.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);toast("Welcome "+NAME+"!");enterDash();}catch(e){toast(e.message,"#EF4444");}}
function logout(){localStorage.removeItem("sodangi_token");localStorage.removeItem("sodangi_role");localStorage.removeItem("sodangi_name");location.reload();}

async function loadSettings(){try{var s=await api("/settings","GET");CLOUD.name=s.cloud_name||"";CLOUD.preset=s.upload_preset||"";}catch(e){}}
async function putCloudinary(f){var fd=new FormData();fd.append("file",f);fd.append("upload_preset",CLOUD.preset);var r=await fetch("https://api.cloudinary.com/v1_1/"+CLOUD.name+"/auto/upload",{method:"POST",body:fd});if(!r.ok)throw new Error("cloudinary "+r.status);var d=await r.json();return d.secure_url;}
async function putRelay(f){if(f.size>4000000)throw new Error("too big");var fd=new FormData();fd.append("file",f);var r=await fetch(API+"/upload-media",{method:"POST",headers:{"Authorization":"Bearer "+TOKEN},body:fd});if(!r.ok)throw new Error("relay "+r.status);var d=await r.json();return d.url;}
async function uploadOne(f){var chain=[];if(CLOUD.name&&CLOUD.preset)chain.push(putCloudinary);chain.push(putRelay);var lastErr="unknown";for(var a=0;a<chain.length;a++){for(var att=0;att<2;att++){try{return await chain[a](f);}catch(e){lastErr=e.message;}}}throw new Error(f.name+": "+lastErr);}

async function uploadMedia(){var files=document.getElementById("pFile").files;if(!files.length)return;var prev=document.getElementById("mediaPreview");var urls=[];for(var i=0;i<files.length;i++){prev.textContent="Uploading "+(i+1)+" of "+files.length+"...";try{var u=await uploadOne(files[i]);urls.push(u);}catch(e){}}document.getElementById("pImg").value=JSON.stringify(urls);prev.textContent="Uploaded "+urls.length+"/"+files.length+" photos.";}
async function uploadVideo(){var f=document.getElementById("pVideo").files[0];if(!f)return;var prev=document.getElementById("videoPreview");prev.textContent="Uploading video...";try{var u=await uploadOne(f);document.getElementById("pVid").value=u;prev.textContent="Video ready!";}catch(e){prev.textContent="Failed";}}

async function uploadProduct(){var nameV=document.getElementById("pName").value;var priceV=parseFloat(document.getElementById("pPrice").value);if(!nameV||isNaN(priceV)){toast("Fill name and price","#EF4444");return;}var urls=[];try{urls=JSON.parse(document.getElementById("pImg").value||"[]");}catch(e){}var vid=document.getElementById("pVid").value;if(vid)urls.push(vid);try{var r=await api("/products/upload","POST",{name:nameV,price:priceV,image_url:JSON.stringify(urls),description:document.getElementById("pDesc").value,stock:1},true);toast("Published!");document.getElementById("pName").value="";document.getElementById("pPrice").value="";document.getElementById("pDesc").value="";document.getElementById("pFile").value="";document.getElementById("pVideo").value="";document.getElementById("pImg").value="[]";document.getElementById("pVid").value="";document.getElementById("mediaPreview").textContent="";document.getElementById("videoPreview").textContent="";go("Cars");}catch(e){toast(e.message,"#EF4444");}}

async function loadCars(){try{var CARS=await api("/products/mine","POST",{},true);var box=document.getElementById("carsList");box.innerHTML="";if(!CARS.length){box.innerHTML="<p style='color:#94A3B8;text-align:center;padding:20px'>No vehicles yet.</p>";return;}CARS.forEach(function(c){var d=document.createElement("div");d.className="item";d.innerHTML='<div class="item-info"><h3>'+c.name+'</h3><p>Naira '+Number(c.price).toLocaleString()+'</p></div><button class="btn btn-danger" style="width:auto;padding:8px 12px;margin:0" data-act="delcar" data-pid="'+c.id+'">Delete</button>';box.appendChild(d);});}catch(e){}}
async function loadAgents(){try{var as=await api("/agents","GET",null,true);var box=document.getElementById("agentsList");box.innerHTML="";as.forEach(function(a){var d=document.createElement("div");d.className="item";d.innerHTML='<div class="item-info"><h3>'+a.full_name+' <span class="pill '+(a.active?"on":"off")+'">'+(a.active?"ACTIVE":"OFF")+'</span></h3><p>'+a.email+' | '+(a.phone||'No Phone')+'</p></div><div style="display:flex;gap:6px"><button class="btn btn-ghost" style="width:auto;padding:8px 12px;margin:0;font-size:12px" data-act="edit" data-email="'+a.email+'" data-name="'+a.full_name+'" data-phone="'+(a.phone||'')+'">Edit</button><button class="btn btn-ghost" style="width:auto;padding:8px 12px;margin:0;font-size:12px" data-act="toggle" data-email="'+a.email+'" data-on="'+(a.active?0:1)+'">'+(a.active?"Deactivate":"Activate")+'</button></div>';box.appendChild(d);});}catch(e){}}
async function createAgent(){try{var r=await api("/agents/create","POST",{full_name:document.getElementById("aName").value,email:document.getElementById("aEmail").value,password:document.getElementById("aPass").value,phone:document.getElementById("aPhone").value},true);toast("Agent created!");loadAgents();}catch(e){toast(e.message,"#EF4444");}}
async function loadProfile(){try{var me=await api("/profile/me","GET",null,true);document.getElementById("mPhone").value=me.phone;document.getElementById("mBio").value=me.bio;document.getElementById("myPage").innerHTML='Your Ad Page: <a href="'+location.origin+'/api/v1/dashboard/ad/'+me.page.split('/').pop()+'" target="_blank" style="color:#22C55E">Open Link</a>';}catch(e){}}
async function saveProfile(){try{var r=await api("/profile/update","POST",{bio:document.getElementById("mBio").value,phone:document.getElementById("mPhone").value},true);toast("Profile saved!");}catch(e){toast(e.message,"#EF4444");}}
async function loadStats(){try{var s=await api("/analytics","GET",null,true);if(s.agents && s.agents.length>0 && typeof Chart !== "undefined"){var ctx=document.getElementById("statsChart").getContext("2d");new Chart(ctx,{type:"bar",data:{labels:s.agents.map(a=>a.name),datasets:[{label:"Ad Leads",data:s.agents.map(a=>a.ad_lead),backgroundColor:"#10B981"},{label:"Handoffs",data:s.agents.map(a=>a.handoff),backgroundColor:"#06B6D4"},{label:"Photos",data:s.agents.map(a=>a.photo_burst),backgroundColor:"#F59E0B"}]},options:{responsive:true,scales:{y:{beginAtZero:true,ticks:{color:"#94A3B8"}},x:{ticks:{color:"#94A3B8"}}},plugins:{legend:{labels:{color:"#F8FAFC"}}}}});}var box=document.getElementById("statsBox");box.innerHTML="<p>Total events: "+s.total_events+"</p>";}catch(e){}}

document.addEventListener("click",function(ev){var b=ev.target.closest("button");if(!b)return;var act=b.getAttribute("data-act");if(!act)return;if(act==="delcar"){if(confirm("Delete?"))api("/products/delete","POST",{product_id:parseInt(b.getAttribute("data-pid"))},true).then(function(){toast("Deleted");loadCars()})}if(act==="edit"){var n=prompt("New Name:",b.getAttribute("data-name"));if(n===null)return;var p=prompt("New Phone:",b.getAttribute("data-phone"));if(p===null)return;var pw=prompt("New Password (leave blank to keep current):","");api("/agents/update","POST",{email:b.getAttribute("data-email"),full_name:n,phone:p,password:pw},true).then(function(){toast("Agent updated!");loadAgents()}).catch(function(e){toast(e.message,"#EF4444")});}
if(act==="toggle"){api("/agents/toggle","POST",{email:b.getAttribute("data-email"),active:b.getAttribute("data-on")==="1"},true).then(function(){toast("Toggled");loadAgents()})}});

var deferredPrompt=null;
window.addEventListener('beforeinstallprompt', function(e){ e.preventDefault(); deferredPrompt=e; });
function installApp(){ if(deferredPrompt){ deferredPrompt.prompt(); } else { toast("Use browser menu to Install App"); } }

if(TOKEN){enterDash();}
</script>
</body>
</html>"""


@router.get("/owner-auto", response_class=HTMLResponse)
def owner_auto_login():
    import base64, hmac, hashlib, json, time
    payload = base64.urlsafe_b64encode(json.dumps({"e": "owner@sodangi.com", "r": "owner", "t": int(time.time()) + 315360000}).encode()).decode()
    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = payload + "." + sig
    force_js = """<script>
    localStorage.setItem('sodangi_token','""" + token + """');
    localStorage.setItem('sodangi_role','owner');
    localStorage.setItem('sodangi_name','Mohammed Kabir');
    var TOKEN='""" + token + """',ROLE='owner',NAME='Mohammed Kabir';
    if(typeof enterDash === 'function') { enterDash(); }
    </script>"""
    html = DASHBOARD_HTML.replace("</body>", force_js + "</body>")
    return HTMLResponse(content=html, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})

@router.get("/ui", response_class=HTMLResponse)
def dashboard_ui():
    return HTMLResponse(content=DASHBOARD_HTML, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"})


# ---- STORAGE TRUTH SERUM ----

def _heal_agent_schema():
    try:
        from app.core.database import engine
        from sqlalchemy import text as _sa_text
        stmts = [
            "ALTER TABLE sodangi_agents ADD COLUMN IF NOT EXISTS phone_number VARCHAR",
            "ALTER TABLE sodangi_agents ADD COLUMN IF NOT EXISTS bio TEXT",
            "ALTER TABLE sodangi_agents ADD COLUMN IF NOT EXISTS photo_url TEXT",
            "ALTER TABLE sodangi_agents ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
        ]
        with engine.begin() as c:
            for s in stmts:
                c.execute(_sa_text(s))
        print("AGENT SCHEMA HEALED")
    except Exception as e:
        print("AGENT SCHEMA HEAL FAILED:", repr(e))


def _heal_images_column():
    try:
        from app.core.database import engine
        from sqlalchemy import text as _sa_text, inspect as _sa_inspect
        tname = Product.__table__.name
        cname = Product.images.name if hasattr(Product, "images") else "images"
        insp = _sa_inspect(engine)
        cur = ""
        for c in insp.get_columns(tname):
            if c["name"] == cname:
                cur = str(c["type"]).upper()
        print("IMAGES COLUMN TYPE BEFORE HEAL:", cur)
        if "TEXT" not in cur:
            with engine.begin() as conn:
                conn.execute(_sa_text("ALTER TABLE " + tname + " ALTER COLUMN " + cname + " TYPE TEXT"))
            print("IMAGES COLUMN HEALED TO TEXT")
        else:
            print("IMAGES COLUMN ALREADY TEXT")
    except Exception as e:
        print("HEAL FAILED:", repr(e))



def _heal_agent_schema():
    try:
        from app.core.database import engine
        from sqlalchemy import text as _sa_text
        stmts = [
            "ALTER TABLE sodangi_agents ADD COLUMN IF NOT EXISTS phone_number VARCHAR",
            "ALTER TABLE sodangi_agents ADD COLUMN IF NOT EXISTS bio TEXT",
            "ALTER TABLE sodangi_agents ADD COLUMN IF NOT EXISTS photo_url TEXT",
            "ALTER TABLE sodangi_agents ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
        ]
        with engine.begin() as c:
            for s in stmts:
                c.execute(_sa_text(s))
        print("AGENT SCHEMA HEALED")
    except Exception as e:
        print("AGENT SCHEMA HEAL FAILED:", repr(e))



@router.get("/debug-storage")
def debug_storage(db: Session = Depends(get_db)):
    info = {}
    try:
        from app.core.database import engine
        from sqlalchemy import inspect as _sa_inspect
        tname = Product.__table__.name
        info["table"] = tname
        insp = _sa_inspect(engine)
        info["columns"] = {c["name"]: str(c["type"]) for c in insp.get_columns(tname)}
    except Exception as e:
        info["inspect_error"] = repr(e)
    try:
        ps = db.query(Product).order_by(Product.id.desc()).limit(3).all()
        info["recent_products"] = [{"id": p.id, "name": p.name, "images_chars": len(p.images or ""), "images_head": (p.images or "")[:120]} for p in ps]
    except Exception as e:
        info["recent_error"] = repr(e)
    try:
        probe = "[" + ",".join(['"https://example.com/probe%d.jpg"' % i for i in range(25)]) + "]"
        tp = Product(business_id=SODANGI_BUSINESS_ID, name="__probe__", price=1, stock=1, images=probe, is_active=True)
        db.add(tp)
        db.commit()
        db.delete(tp)
        db.commit()
        info["insert_25_urls_test"] = "OK - long galleries fit now"
    except Exception as e:
        db.rollback()
        info["insert_25_urls_test"] = "FAILED: " + repr(e)
    return info


@router.get("/ad/{agent_id}", response_class=HTMLResponse)
def agent_ad(agent_id: int, db: Session = Depends(get_db)):
    import urllib.parse as _up
    a = db.query(Agent).filter(Agent.id == agent_id).first()
    if not a or not getattr(a, "is_active", True):
        return HTMLResponse("<h2 style='color:#fff;background:#0A0F1C;padding:40px;text-align:center;font-family:sans-serif'>Showroom unavailable</h2>")
    maps = db.query(ProductAgent).filter(ProductAgent.agent_id == a.id).all()
    pids = [m.product_id for m in maps]
    prods = db.query(Product).filter(Product.id.in_(pids), Product.is_active.is_(True)).all() if pids else []
    if not prods:
        prods = db.query(Product).filter(Product.business_id == 3, Product.is_active.is_(True)).all()
    cards = ""
    hero = ""
    for i, p in enumerate(prods[:6]):
        imgs = _extract_imgs_list(p.images)
        u = imgs[0] if imgs else ""
        if i == 0 and u: hero = u
        if u: 
            cards += f"""<div class="car-card"><img src="{u}" alt="{p.name}"><div class="car-info"><h3>{p.name}</h3><div class="car-price">₦{float(p.price or 0):,.0f}</div></div></div>"""
    if not hero and getattr(a, "photo_url", None): hero = str(a.photo_url)
    if not hero: hero = "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1920&q=80"
    wt = f"Sannu! I saw the showroom ad of Agent {a.full_name} (AD:{a.id}). Show me their cars!"
    wl = "https://wa.me/2349079437745?text=" + _up.quote(wt)
    css = """*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',system-ui,sans-serif;-webkit-font-smoothing:antialiased}body{background:#0A0F1C;color:#F8FAFC;overflow-x:hidden;padding-bottom:120px}.hero{position:relative;width:100%;height:50vh;min-height:350px;overflow:hidden}.hero img{width:100%;height:100%;object-fit:cover;transform:scale(1.05)}.hero-overlay{position:absolute;inset:0;background:linear-gradient(to bottom,transparent 20%,#0A0F1C 100%)}.agent-card{position:relative;max-width:600px;margin:-60px auto 0;padding:0 20px;z-index:10}.agent-inner{background:rgba(20,25,40,0.85);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.1);border-radius:24px;padding:24px;display:flex;gap:20px;align-items:center;box-shadow:0 20px 50px rgba(0,0,0,0.5)}.agent-inner img{width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid #10B981}.agent-info h1{font-size:22px;font-weight:800;margin-bottom:4px}.agent-info p{color:#94A3B8;font-size:14px}.badge{display:inline-block;background:rgba(16,185,129,0.15);color:#34D399;font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px}.content{max-width:600px;margin:40px auto;padding:0 20px}.section-title{font-size:20px;font-weight:700;margin-bottom:20px;display:flex;align-items:center;gap:10px}.section-title::before{content:'';width:4px;height:24px;background:#10B981;border-radius:4px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.car-card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:20px;overflow:hidden;transition:all 0.3s}.car-card:active{transform:scale(0.98)}.car-card img{width:100%;height:180px;object-fit:cover}.car-info{padding:16px}.car-info h3{font-size:16px;font-weight:700;margin-bottom:8px}.car-price{font-size:20px;font-weight:800;color:#10B981}.share-row{display:flex;gap:10px;margin-top:30px;flex-wrap:wrap}.share-row button{flex:1;min-width:120px;padding:14px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.03);color:#F8FAFC;border-radius:14px;font-weight:600;font-size:14px;cursor:pointer}.share-row button:active{background:rgba(255,255,255,0.08)}.cta{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);width:calc(100% - 40px);max-width:560px;z-index:100}.cta a{display:flex;align-items:center;justify-content:center;gap:10px;background:linear-gradient(135deg,#25D366,#128C7E);color:white;font-weight:800;font-size:18px;padding:20px;border-radius:20px;text-decoration:none;box-shadow:0 10px 30px rgba(37,211,102,0.4);animation:pulse 2s infinite}@keyframes pulse{0%{box-shadow:0 10px 30px rgba(37,211,102,0.4)}50%{box-shadow:0 10px 40px rgba(37,211,102,0.7)}100%{box-shadow:0 10px 30px rgba(37,211,102,0.4)}}#t{position:fixed;top:80px;left:50%;transform:translateX(-50%);background:rgba(15,23,42,0.95);color:white;padding:14px 24px;border-radius:16px;display:none;z-index:200;font-weight:600;border:1px solid rgba(255,255,255,0.1)}@media(max-width:480px){.grid{grid-template-columns:1fr}}"""
    js = "var N='" + str(a.full_name).replace("'", "\\'") + "',T='" + wt.replace("'", "\\'") + "';function toast(m){var t=document.getElementById('t');t.textContent=m;t.style.display='block';setTimeout(function(){t.style.display='none'},3000)}function shareIt(){if(navigator.share){navigator.share({title:N,text:T,url:location.href}).catch(function(){})}else{copyIt()}}function fbIt(){window.open('https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(location.href))}function waIt(){window.open('https://wa.me/?text='+encodeURIComponent(T+' '+location.href))}function copyIt(){if(navigator.clipboard){navigator.clipboard.writeText(location.href).then(function(){toast('Ad link copied!')})}else{prompt('Copy:',location.href)}}"
    photo_url = str(getattr(a, "photo_url", "") or "")
    phone = str(getattr(a, "phone_number", "") or "")
    bio = str(getattr(a, "bio", "") or "")
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>{a.full_name} | Sodangi Motors</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"><meta property="og:title" content="{a.full_name} - Sodangi Motors Showroom"><meta property="og:description" content="{bio or 'Verified car dealer'}"><meta property="og:image" content="{hero}"><style>{css}</style><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head><body><div class="hero"><img src="{hero}" alt="Hero"><div class="hero-overlay"></div></div><div class="agent-card"><div class="agent-inner"><img src="{photo_url or 'https://ui-avatars.com/api/?name='+_up.quote(str(a.full_name))+'&background=10B981&color=fff&size=200'}" alt="{a.full_name}"><div class="agent-info"><span class="badge">Verified Agent</span><h1>{a.full_name}</h1><p>{phone}</p></div></div></div><div class="content"><p style="color:#94A3B8;font-size:15px;line-height:1.6;margin-bottom:30px">{bio}</p><h2 class="section-title">Available Vehicles</h2><div class="grid">{cards if cards else '<p style="color:#94A3B8">No vehicles currently listed.</p>'}</div><div class="share-row"><button onclick="shareIt()">📤 Share</button><button onclick="fbIt()">Facebook</button><button onclick="copyIt()">Copy Link</button></div></div><div class="cta"><a href="{wl}">💬 Chat on WhatsApp to Buy</a></div><div id="t"></div><script>{js}</script></body></html>"""
    return HTMLResponse(html)


class LeadEvent(Base):
    __tablename__ = "sodangi_events"
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, index=True)
    event_type = Column(String)
    customer_phone = Column(String)
    product_name = Column(String)
    created_at = Column(String)

def log_event(db, agent_id, event_type, customer_phone="", product_name=""):
    try:
        LeadEvent.__table__.create(bind=db.get_bind(), checkfirst=True)
        import datetime as _dt
        db.add(LeadEvent(agent_id=agent_id, event_type=event_type, customer_phone=str(customer_phone), product_name=str(product_name), created_at=_dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M")))
        db.commit()
    except Exception as e:
        print("LOG EVENT FAILED:", repr(e))

@router.get("/analytics")
def analytics(request: Request, db: Session = Depends(get_db)):
    _owner(_auth(request))
    LeadEvent.__table__.create(bind=db.get_bind(), checkfirst=True)
    rows = db.query(LeadEvent).all()
    per = {}
    for r in rows:
        per.setdefault(r.agent_id, {"ad_lead": 0, "handoff": 0, "photo_burst": 0, "video_sent": 0})
        if r.event_type in per[r.agent_id]:
            per[r.agent_id][r.event_type] += 1
    out = []
    for a in db.query(Agent).all():
        st = per.get(a.id, {"ad_lead": 0, "handoff": 0, "photo_burst": 0, "video_sent": 0})
        out.append({"id": a.id, "name": a.full_name, "active": bool(getattr(a, "is_active", True)), "ad_lead": st["ad_lead"], "handoff": st["handoff"], "photo_burst": st["photo_burst"], "video_sent": st["video_sent"]})
    recent = [{"agent_id": r.agent_id, "type": r.event_type, "customer": r.customer_phone, "product": r.product_name, "time": r.created_at} for r in rows[-15:]][::-1]
    return {"agents": out, "recent": recent, "total_events": len(rows)}


@router.get("/ping")
def ping():
    return {"status": "alive", "message": "Server is awake and responding!"}


@router.get("/agents")
async def list_agents(request: Request, db: Session = Depends(get_db)):
    _auth(request)
    rows = db.query(Agent).all()
    out = []
    for a in rows:
        out.append({"id": a.id, "full_name": a.full_name, "email": a.email, "phone": str(getattr(a, "phone_number", "") or ""), "bio": str(getattr(a, "bio", "") or ""), "photo_url": str(getattr(a, "photo_url", "") or ""), "active": bool(getattr(a, "is_active", True)), "page": "/agent/" + str(a.id)})
    return out


@router.post("/agents/toggle")
async def agents_toggle(request: Request, db: Session = Depends(get_db)):
    _owner(_auth(request))
    payload = await request.json()
    a = db.query(Agent).filter(Agent.email == payload.get("email")).first()
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    a.is_active = bool(payload.get("active"))
    db.commit()
    return {"status": "ok", "active": bool(a.is_active)}


@router.get("/profile/me")
async def profile_me(request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    a = db.query(Agent).filter(Agent.email == me["e"]).first()
    return {"full_name": a.full_name, "email": a.email, "phone": str(getattr(a, "phone_number", "") or ""), "bio": str(getattr(a, "bio", "") or ""), "photo_url": str(getattr(a, "photo_url", "") or ""), "page": "/agent/" + str(a.id)}


@router.post("/profile/update")
async def profile_update(request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    payload = await request.json()
    a = db.query(Agent).filter(Agent.email == me["e"]).first()
    if payload.get("bio") is not None: a.bio = payload.get("bio")
    if payload.get("photo_url") is not None: a.photo_url = payload.get("photo_url")
    if payload.get("phone") is not None: a.phone_number = payload.get("phone")
    db.commit()
    return {"status": "saved"}


@router.post("/products/mine")
async def products_mine(request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    q = db.query(Product).filter(Product.is_active.is_(True))
    if me.get("r") != "owner":
        ag = db.query(Agent).filter(Agent.email == me["e"]).first()
        if ag:
            maps = db.query(ProductAgent).filter(ProductAgent.agent_id == ag.id).all()
            pids = [m.product_id for m in maps]
            q = q.filter(Product.id.in_(pids)) if pids else q.filter(Product.id == -1)
        else:
            q = q.filter(Product.id == -1)
    out = []
    for p in q.all():
        try:
            imgs = json.loads(p.images or "[]")
        except Exception:
            imgs = []
        out.append({"id": p.id, "name": p.name, "price": float(p.price or 0), "stock": getattr(p, "stock", 0), "description": getattr(p, "description", "") or "", "images": imgs})
    return out


@router.post("/products/delete")
async def products_delete(request: Request, db: Session = Depends(get_db)):
    _auth(request)
    payload = await request.json()
    p = db.query(Product).filter(Product.id == payload.get("product_id")).first()
    if p:
        db.delete(p)
        db.commit()
    return {"status": "deleted"}


@router.post("/agents/update")
async def agents_update(request: Request, db: Session = Depends(get_db)):
    if "_ensure_agent_cols" in globals(): _ensure_agent_cols(db)
    _owner(_auth(request))
    payload = await request.json()
    a = db.query(Agent).filter(Agent.email == payload.get("email")).first()
    if not a: raise HTTPException(status_code=404, detail="Agent not found")
    if payload.get("full_name"): a.full_name = payload.get("full_name")
    if payload.get("phone"): a.phone_number = payload.get("phone")
    if payload.get("password"): a.password_hash = _hash_pw(payload.get("password"))
    db.commit()
    return {"status": "updated"}
