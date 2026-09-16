
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
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Sodangi Motors | Agent Portal</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#0B0F19;--surface:rgba(30,41,59,0.95);--surface-hover:rgba(51,65,85,0.95);--border:rgba(148,163,184,0.3);--text:#F8FAFC;--muted:#94A3B8;--primary:#10B981;--primary-glow:rgba(16,185,129,0.2);--accent:#06B6D4;--danger:#EF4444}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding-bottom:100px;overflow-x:hidden}
body::before{content:'';position:fixed;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 20%,rgba(6,182,212,0.08) 0%,transparent 50%),radial-gradient(circle at 70% 80%,rgba(16,185,129,0.08) 0%,transparent 50%);z-index:-1}
header{position:sticky;top:0;z-index:50;padding:16px 20px;backdrop-filter:blur(12px);background:rgba(11,15,25,0.8);border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
header h1{font-size:18px;font-weight:800;background:linear-gradient(90deg,#10B981,#06B6D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.who{font-size:12px;color:var(--muted);font-weight:500}
main{max-width:600px;margin:20px auto;padding:0 16px;display:grid;gap:20px}
.card{background:var(--surface);backdrop-filter:blur(10px);border:1px solid var(--border);border-radius:24px;padding:24px;box-shadow:0 8px 32px rgba(0,0,0,0.2)}
.card h2{font-size:18px;font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.card h2::before{content:'';width:4px;height:20px;background:var(--primary);border-radius:4px}
label{display:block;font-size:13px;font-weight:600;color:var(--muted);margin:16px 0 8px;text-transform:uppercase;letter-spacing:0.5px}
input,textarea{width:100%;padding:14px 16px;border-radius:14px;border:1px solid var(--border);background:#0F172A;border:1px solid #334155;color:var(--text);font-size:16px;font-family:inherit;transition:all 0.2s}
input:focus,textarea:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 4px var(--primary-glow)}
textarea{min-height:80px;resize:vertical}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:400px){.row{grid-template-columns:1fr}}
.btn{width:100%;padding:16px;border:none;border-radius:16px;font-size:16px;font-weight:700;cursor:pointer;transition:all 0.2s;margin-top:20px;display:flex;align-items:center;justify-content:center;gap:8px}
.btn-primary{background:linear-gradient(135deg,#10B981,#059669);color:white;box-shadow:0 4px 12px rgba(16,185,129,0.3)}
.btn-primary:active{transform:scale(0.98)}
.btn-ghost{background:var(--surface-hover);color:var(--text);border:1px solid var(--border)}
.btn-danger{background:rgba(239,68,68,0.1);color:#FCA5A5;border:1px solid rgba(239,68,68,0.2)}
.file-drop{border:2px dashed var(--border);border-radius:16px;padding:24px;text-align:center;cursor:pointer;transition:all 0.2s;background:rgba(0,0,0,0.1)}
.file-drop:active{border-color:var(--primary);background:var(--primary-glow)}
.file-drop input{display:none}
.file-drop p{color:var(--muted);font-size:14px;margin-top:8px}
.file-drop .icon{font-size:32px;margin-bottom:8px}
nav{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);width:calc(100% - 32px);max-width:400px;background:rgba(15,23,42,0.9);backdrop-filter:blur(20px);border:1px solid var(--border);border-radius:24px;padding:8px;display:flex;justify-content:space-around;z-index:100;box-shadow:0 10px 40px rgba(0,0,0,0.5)}
nav button{flex:1;background:none;border:none;color:var(--muted);padding:10px 0;font-size:11px;font-weight:600;display:flex;flex-direction:column;align-items:center;gap:4px;border-radius:16px;transition:all 0.2s}
nav button.on{background:var(--primary-glow);color:var(--primary)}
nav button span{font-size:20px}
.car{background:#0F172A;border:1px solid #334155;border:1px solid var(--border);border-radius:20px;padding:16px;margin-top:16px}
.car h3{font-size:16px;font-weight:700;color:var(--text);margin-bottom:4px}
.car .price{color:var(--primary);font-weight:800;font-size:18px;margin-bottom:12px}
.gal{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}
.gal div{position:relative;aspect-ratio:1;border-radius:12px;overflow:hidden}
.gal img{width:100%;height:100%;object-fit:cover}
.gal button{position:absolute;top:4px;right:4px;width:24px;height:24px;border-radius:50%;background:rgba(239,68,68,0.9);color:white;border:none;font-size:14px;display:flex;align-items:center;justify-content:center}
.pill{display:inline-block;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px}
.pill.on{background:rgba(16,185,129,0.15);color:#34D399}
.pill.off{background:rgba(239,68,68,0.15);color:#F87171}
#toast{position:fixed;top:80px;left:50%;transform:translateX(-50%);background:rgba(15,23,42,0.95);backdrop-filter:blur(10px);color:white;padding:14px 24px;border-radius:16px;display:none;z-index:200;font-size:14px;font-weight:600;box-shadow:0 10px 30px rgba(0,0,0,0.3);border:1px solid var(--border);max-width:90%;text-align:center}
.hidden{display:none !important}
a{color:var(--primary);text-decoration:none;font-weight:600}
</style>

<style>
/* NUCLEAR OVERRIDE: FORCE VISIBILITY */
body { background: #0f172a !important; color: #f8fafc !important; }
.card, section, .agent-inner, .car-card { 
    background: #1e293b !important; 
    border: 1px solid #334155 !important; 
    color: #f8fafc !important; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
}
h1, h2, h3, label, p, span, div { color: #f8fafc !important; }
input, textarea, select { 
    background: #020617 !important; 
    color: #f8fafc !important; 
    border: 1px solid #475569 !important; 
}
.btn, button { 
    background: #10b981 !important; 
    color: #ffffff !important; 
    border: none !important;
}
.btn-danger { background: #ef4444 !important; }
.btn-ghost { background: #334155 !important; }
nav { background: #1e293b !important; border-top: 1px solid #334155 !important; }
nav button { color: #94a3b8 !important; }
nav button.on { color: #10b981 !important; background: rgba(16,185,129,0.1) !important; }
</style>

</head>
<body>
<header><h1>SODANGI MOTORS</h1><div class="who" id="who"></div></header>
<main>
  <section class="card" id="authCard"><h2>Agent Portal</h2><label>Email</label><input id="liEmail" type="email" placeholder="agent@sodangi.com"><label>Password</label><input id="liPass" type="password" placeholder="••••••••"><button class="btn btn-primary" onclick="doLogin()">Sign In</button></section>
  <section class="card hidden" id="tabUpload"><h2>Add to Showroom</h2><label>Vehicle Name</label><input id="pName" placeholder="e.g. Toyota Camry 2022"><div class="row"><div><label>Price (₦)</label><input id="pPrice" type="number" placeholder="15,000,000"></div><div><label>Stock</label><input id="pStock" type="number" value="1"></div></div><label>Photos</label><div class="file-drop" onclick="document.getElementById('pFile').click()"><div class="icon">📸</div><p>Tap to select photos</p><input type="file" id="pFile" accept="image/*" multiple onchange="uploadMedia()"></div><div id="mediaPreview" style="margin-top:12px;color:var(--primary);font-size:13px;font-weight:600"></div><label>Video (Optional)</label><div class="file-drop" onclick="document.getElementById('pVideo').click()"><div class="icon">🎥</div><p>Tap to select video</p><input type="file" id="pVideo" accept="video/*" onchange="uploadVideo()"></div><div id="videoPreview" style="margin-top:12px;color:var(--accent);font-size:13px;font-weight:600"></div><label>Description</label><textarea id="pDesc" placeholder="Highlight key features..."></textarea><button class="btn btn-primary" onclick="uploadProduct()">Publish Vehicle</button><input id="pImg" type="hidden"><input id="pVid" type="hidden"></section>
  <section class="card hidden" id="tabCars"><h2>My Showroom</h2><div id="carsList"></div></section>
  <section class="card hidden" id="tabAgents"><h2>Manage Agents</h2><label>Full Name</label><input id="aName"><label>Email</label><input id="aEmail" type="email"><label>Temp Password</label><input id="aPass" type="password"><label>WhatsApp</label><input id="aPhone" type="tel" placeholder="080..."><label>Bio</label><textarea id="aBio"></textarea><label>Profile Photo</label><div class="file-drop" onclick="document.getElementById('aPhoto').click()"><div class="icon">👤</div><p>Upload Photo</p><input type="file" id="aPhoto" accept="image/*" onchange="uploadAgentPhoto()"></div><div id="aPhotoPrev" style="font-size:12px;color:var(--primary);margin-top:8px"></div><input id="aPhotoUrl" type="hidden"><button class="btn btn-primary" onclick="createAgent()">Create Agent</button><h2 style="margin-top:24px">Active Agents</h2><div id="agentsList"></div></section>
  <section class="card hidden" id="tabProfile"><h2>My Profile</h2><label>Profile Photo</label><div class="file-drop" onclick="document.getElementById('mPhoto').click()"><div class="icon">📷</div><p>Update Photo</p><input type="file" id="mPhoto" accept="image/*" onchange="uploadMyPhoto()"></div><div id="mPhotoPrev" style="font-size:12px;color:var(--primary);margin-top:8px"></div><input id="mPhotoUrl" type="hidden"><label>WhatsApp</label><input id="mPhone" type="tel"><label>Bio</label><textarea id="mBio"></textarea><button class="btn btn-primary" onclick="saveProfile()">Save Profile</button><div id="myPage" style="margin-top:16px;padding:16px;background:#0F172A;border:1px solid #334155;border-radius:16px;font-size:13px"></div><button class="btn btn-danger" onclick="logout()">Sign Out</button></section>
  <section class="card hidden" id="tabStats"><h2>Business Analytics</h2><div id="statsBox"></div></section><section class="card hidden" id="tabMedia"><h2>Media Engine</h2><label>Cloudinary Cloud Name</label><input id="cCloud"><label>Upload Preset</label><input id="cPreset"><button class="btn btn-primary" onclick="saveSettings()">Save Settings</button></section>
</main>
<nav id="bottomNav" class="hidden"><button id="navUpload" onclick="go('Upload')"><span>➕</span>Add</button><button id="navCars" onclick="go('Cars')"><span>🚗</span>Cars</button><button id="navAgents" onclick="go('Agents')" class="hidden"><span>👥</span>Team</button><button id="navProfile" onclick="go('Profile')"><span>👤</span>Me</button><button id="navStats" onclick="go('Stats')" class="hidden"><span>📊</span>Stats</button><button id="navMedia" onclick="go('Media')" class="hidden"><span>⚙️</span>API</button></nav>
<div id="toast"></div>
<script>

var API="/api/v1/dashboard";
var TOKEN=localStorage.getItem("sodangi_token")||"";
var ROLE=localStorage.getItem("sodangi_role")||"";
var NAME=localStorage.getItem("sodangi_name")||"";
var CARS=[];var CLOUD={name:"",preset:""};

function toast(m,c){var t=document.getElementById("toast");if(!t)return;t.textContent=m;t.style.background=c||"#10B981";t.style.display="block";setTimeout(function(){t.style.display="none";},3500);}
async function api(p,m,b,a){var h={"Content-Type":"application/json"};if(a)h["Authorization"]="Bearer "+TOKEN;var r=await fetch(API+p,{method:m,headers:h,body:b?JSON.stringify(b):undefined});if(!r.ok){var e={};try{e=await r.json();}catch(x){}throw new Error(e.detail||("HTTP "+r.status));}return r.json();}

function go(tab){
  ["Upload","Cars","Agents","Profile","Media","Stats"].forEach(function(t){
    var el=document.getElementById("tab"+t);if(el)el.className="card hidden";
    var nb=document.getElementById("nav"+t);if(nb)nb.className=nb.className.replace(" on","");
  });
  var el=document.getElementById("tab"+tab);if(el)el.className="card";
  var nb=document.getElementById("nav"+tab);if(nb)nb.className=nb.className+" on";
  if(tab==="Cars")loadCars();if(tab==="Agents")loadAgents();if(tab==="Profile")loadProfile();
  if(tab==="Stats")loadStats();
}

function enterDash(){
  var ac=document.getElementById("authCard");if(ac)ac.className="card hidden";
  var bn=document.getElementById("bottomNav");if(bn)bn.className="";
  var who=document.getElementById("who");if(who)who.textContent=NAME+" ("+ROLE+")";
  if(ROLE==="owner"){var na=document.getElementById("navAgents");if(na)na.className="";var nm=document.getElementById("navMedia");if(nm)nm.className="";var ns=document.getElementById("navStats");if(ns)ns.className="";}
  loadSettings();go("Upload");
}

async function doLogin(){try{var r=await api("/login","POST",{email:document.getElementById("liEmail").value,password:document.getElementById("liPass").value});TOKEN=r.token;ROLE=r.role;NAME=r.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);toast("Welcome "+NAME+"!");enterDash();}catch(e){toast(e.message,"#EF4444");}}
function logout(){localStorage.removeItem("sodangi_token");localStorage.removeItem("sodangi_role");localStorage.removeItem("sodangi_name");location.reload();}

async function loadSettings(){try{var s=await api("/settings","GET");CLOUD.name=s.cloud_name||"";CLOUD.preset=s.upload_preset||"";var c1=document.getElementById("cCloud");if(c1)c1.value=CLOUD.name;var c2=document.getElementById("cPreset");if(c2)c2.value=CLOUD.preset;}catch(e){}}
async function saveSettings(){try{var r=await api("/settings","POST",{cloud_name:document.getElementById("cCloud").value,upload_preset:document.getElementById("cPreset").value},true);CLOUD.name=document.getElementById("cCloud").value;CLOUD.preset=document.getElementById("cPreset").value;toast(r.message);}catch(e){toast(e.message,"#EF4444");}}

async function putCloudinary(f){var fd=new FormData();fd.append("file",f);fd.append("upload_preset",CLOUD.preset);var r=await fetch("https://api.cloudinary.com/v1_1/"+CLOUD.name+"/auto/upload",{method:"POST",body:fd});if(!r.ok)throw new Error("cloudinary "+r.status);var d=await r.json();return d.secure_url;}
async function putRelay(f){if(f.size>4000000)throw new Error("too big");var fd=new FormData();fd.append("file",f);var r=await fetch(API+"/upload-media",{method:"POST",headers:{"Authorization":"Bearer "+TOKEN},body:fd});if(!r.ok)throw new Error("relay "+r.status);var d=await r.json();return d.url;}
async function uploadOne(f){var chain=[];if(CLOUD.name&&CLOUD.preset)chain.push(putCloudinary);chain.push(putRelay);var lastErr="unknown";for(var a=0;a<chain.length;a++){for(var att=0;att<2;att++){try{return await chain[a](f);}catch(e){lastErr=e.message;}}}throw new Error(f.name+": "+lastErr);}

async function uploadMedia(){var files=document.getElementById("pFile").files;if(!files.length)return;var prev=document.getElementById("mediaPreview");var urls=[];var failed=[];for(var i=0;i<files.length;i++){prev.textContent="Uploading "+(i+1)+" of "+files.length+"...";try{var u=await uploadOne(files[i]);urls.push(u);}catch(e){failed.push(files[i].name);}}document.getElementById("pImg").value=JSON.stringify(urls);prev.textContent="Uploaded "+urls.length+"/"+files.length+" photos.";toast("Photos ready!");}
async function uploadVideo(){var f=document.getElementById("pVideo").files[0];if(!f)return;var prev=document.getElementById("videoPreview");prev.textContent="Uploading video...";try{var u=await uploadOne(f);document.getElementById("pVid").value=u;prev.textContent="Video ready!";}catch(e){prev.textContent="Failed";toast(e.message,"#EF4444");}}

async function uploadProduct(){var nameV=document.getElementById("pName").value;var priceV=parseFloat(document.getElementById("pPrice").value);if(!nameV||isNaN(priceV)){toast("Fill name and price","#EF4444");return;}var urls=[];try{urls=JSON.parse(document.getElementById("pImg").value||"[]");}catch(e){urls=[];}var vid=document.getElementById("pVid").value;if(vid)urls.push(vid);try{var r=await api("/products/upload","POST",{name:nameV,price:priceV,image_url:JSON.stringify(urls),description:document.getElementById("pDesc").value,stock:parseInt(document.getElementById("pStock").value||"1",10)},true);toast("Published!");document.getElementById("pName").value="";document.getElementById("pPrice").value="";document.getElementById("pDesc").value="";document.getElementById("pFile").value="";document.getElementById("pVideo").value="";document.getElementById("pImg").value="";document.getElementById("pVid").value="";document.getElementById("mediaPreview").textContent="";document.getElementById("videoPreview").textContent="";go("Cars");}catch(e){toast(e.message,"#EF4444");}}

async function loadCars(){try{CARS=await api("/products/mine","POST",{},true);renderCars();}catch(e){}}
function renderCars(){var box=document.getElementById("carsList");box.innerHTML="";if(!CARS.length){box.innerHTML="<p style='color:#94A3B8;text-align:center;padding:20px'>No vehicles yet. Add your first car!</p>";return;}CARS.forEach(function(c){var d=document.createElement("div");d.className="car";var gal="";(c.images||[]).forEach(function(u,i){gal+='<div><img src="'+u+'"><button data-act="delphoto" data-pid="'+c.id+'" data-idx="'+i+'">x</button></div>';});d.innerHTML='<h3>'+c.name+'</h3><div class="price">₦'+Number(c.price).toLocaleString()+'</div><div class="gal">'+gal+'</div><button class="btn btn-danger" data-act="delcar" data-pid="'+c.id+'">Delete Vehicle</button>';box.appendChild(d);});}

async function loadAgents(){try{var as=await api("/agents","GET",null,true);var box=document.getElementById("agentsList");box.innerHTML="";as.forEach(function(a){var d=document.createElement("div");d.className="car";d.innerHTML='<h3>'+a.full_name+' <span class="pill '+(a.active?"on":"off")+'">'+(a.active?"ACTIVE":"OFF")+'</span></h3><p style="color:#94A3B8;font-size:13px;margin:8px 0">'+a.email+' | '+a.phone+'</p><button class="btn btn-ghost" data-act="toggle" data-email="'+a.email+'" data-on="'+(a.active?0:1)+'">'+(a.active?"Deactivate":"Activate")+'</button>';box.appendChild(d);});}catch(e){}}
async function createAgent(){try{var r=await api("/agents/create","POST",{full_name:document.getElementById("aName").value,email:document.getElementById("aEmail").value,password:document.getElementById("aPass").value,phone:document.getElementById("aPhone").value,bio:document.getElementById("aBio").value,photo_url:document.getElementById("aPhotoUrl").value},true);toast("Agent created!");loadAgents();}catch(e){toast(e.message,"#EF4444");}}

async function loadProfile(){try{var me=await api("/profile/me","GET",null,true);document.getElementById("mPhone").value=me.phone;document.getElementById("mBio").value=me.bio;document.getElementById("mPhotoUrl").value=me.photo_url;document.getElementById("myPage").innerHTML='Your Ad Page: <a href="'+location.origin+me.page.replace("/agent/","/ad/")+'" target="_blank">Open</a>';}catch(e){}}
async function saveProfile(){try{var r=await api("/profile/update","POST",{bio:document.getElementById("mBio").value,photo_url:document.getElementById("mPhotoUrl").value,phone:document.getElementById("mPhone").value},true);toast("Profile saved!");}catch(e){toast(e.message,"#EF4444");}}

document.addEventListener("click",function(ev){var b=ev.target;while(b&&b.tagName!=="BUTTON"){b=b.parentElement;}if(!b)return;var act=b.getAttribute("data-act");if(!act)return;if(act==="delcar"){if(confirm("Delete?"))api("/products/delete","POST",{product_id:parseInt(b.getAttribute("data-pid"))},true).then(function(){toast("Deleted");loadCars()})}if(act==="toggle"){api("/agents/toggle","POST",{email:b.getAttribute("data-email"),active:b.getAttribute("data-on")==="1"},true).then(function(){toast("Toggled");loadAgents()})}});

async function loadStats(){try{var s=await api("/analytics","GET",null,true);var box=document.getElementById("statsBox");var html="<p style='color:#94A3B8;font-size:13px'>Total lead events: "+s.total_events+"</p>";s.agents.forEach(function(a){html+='<div class="car"><h3>'+a.name+' <span class="pill '+(a.active?"on":"off")+'">'+(a.active?"ACTIVE":"OFF")+'</span></h3><p style="color:#94A3B8;font-size:13px;margin:6px 0'>📢 Ad Leads: '+a.ad_lead+' | 🤝 Handoffs: '+a.handoff+' | 📸 Photo Bursts: '+a.photo_burst+' | 🎥 Videos: '+a.video_sent+'</p></div>';});html+='<h3 style="margin-top:16px">Recent Activity</h3>';s.recent.forEach(function(r){html+='<p style="color:#94A3B8;font-size:12px;margin:4px 0">['+r.time+'] '+r.type+' | '+r.customer+' | '+r.product+'</p>';});box.innerHTML=html;}catch(e){toast(e.message,"#EF4444");}}

if(TOKEN){enterDash();}

</script>
</body>
</html>"""

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

_heal_agent_schema()

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

_heal_agent_schema()


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
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>{a.full_name} | Sodangi Motors</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"><meta property="og:title" content="{a.full_name} - Sodangi Motors Showroom"><meta property="og:description" content="{bio or 'Verified car dealer'}"><meta property="og:image" content="{hero}"><style>{css}</style></head><body><div class="hero"><img src="{hero}" alt="Hero"><div class="hero-overlay"></div></div><div class="agent-card"><div class="agent-inner"><img src="{photo_url or 'https://ui-avatars.com/api/?name='+_up.quote(str(a.full_name))+'&background=10B981&color=fff&size=200'}" alt="{a.full_name}"><div class="agent-info"><span class="badge">Verified Agent</span><h1>{a.full_name}</h1><p>{phone}</p></div></div></div><div class="content"><p style="color:#94A3B8;font-size:15px;line-height:1.6;margin-bottom:30px">{bio}</p><h2 class="section-title">Available Vehicles</h2><div class="grid">{cards if cards else '<p style="color:#94A3B8">No vehicles currently listed.</p>'}</div><div class="share-row"><button onclick="shareIt()">📤 Share</button><button onclick="fbIt()">Facebook</button><button onclick="copyIt()">Copy Link</button></div></div><div class="cta"><a href="{wl}">💬 Chat on WhatsApp to Buy</a></div><div id="t"></div><script>{js}</script></body></html>"""
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
