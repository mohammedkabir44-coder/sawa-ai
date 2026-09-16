
import json, hmac, hashlib, base64, time, os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Text, Boolean
from app.core.database import get_db, Base
from app.models.product import Product


import uuid
import urllib.request


def _bulletproof_heal():
    try:
        from app.core.database import engine
        from sqlalchemy import text as _sa_text, inspect
        insp = inspect(engine)
        with engine.connect() as c:
            # 1. Ensure Agent table exists
            if not insp.has_table('sodangi_agents'):
                c.execute(_sa_text("CREATE TABLE sodangi_agents (id SERIAL PRIMARY KEY, full_name VARCHAR, email VARCHAR UNIQUE, password_hash VARCHAR, role VARCHAR DEFAULT 'agent')"))
                c.commit()
            # 2. Add missing columns to Agent table
            cols = [col['name'] for col in insp.get_columns('sodangi_agents')]
            for col, typ in [("phone_number", "VARCHAR"), ("bio", "TEXT"), ("photo_url", "TEXT"), ("is_active", "BOOLEAN DEFAULT TRUE")]:
                if col not in cols:
                    c.execute(_sa_text(f"ALTER TABLE sodangi_agents ADD COLUMN {col} {typ}"))
                    c.commit()
            # 3. Ensure ProductAgent table exists
            if not insp.has_table('sodangi_product_agents'):
                c.execute(_sa_text("CREATE TABLE sodangi_product_agents (id SERIAL PRIMARY KEY, product_id INTEGER, agent_id INTEGER)"))
                c.commit()
        print("BULLETPROOF SCHEMA HEAL SUCCESS")
    except Exception as e:
        print("BULLETPROOF HEAL FAILED:", repr(e))

_bulletproof_heal()

router = APIRouter(prefix="/dashboard", tags=["Sodangi Agents"])
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

_ensure_media_schema()


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
    salt, h = stored.split(":", 1)
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
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sodangi Motors - Agent Dashboard</title>
<style>
:root{--bg:#0b1220;--card:#151f38;--accent:#22c55e;--accent2:#0ea5e9;--text:#e5e7eb;--muted:#94a3b8}
*{box-sizing:border-box;margin:0;padding:0;font-family:Segoe UI,Arial,sans-serif}
body{background:var(--bg);color:var(--text);padding-bottom:60px}
header{background:linear-gradient(90deg,#059669,#0ea5e9);padding:16px 22px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
header h1{font-size:20px;color:#fff}
.who{font-size:13px;color:#e0f2fe;margin-right:10px}
button{cursor:pointer;border:none;border-radius:8px;padding:10px 16px;font-weight:600}
.btn-primary{background:var(--accent);color:#052e16}
.btn-ghost{background:transparent;color:#fff;border:1px solid #ffffff66}
main{max-width:960px;margin:24px auto;padding:0 16px;display:grid;gap:18px}
.card{background:var(--card);border:1px solid #1e293b;border-radius:14px;padding:20px}
.card h2{font-size:16px;margin-bottom:12px;color:#7dd3fc}
label{display:block;font-size:12px;color:var(--muted);margin:8px 0 4px}
input{width:100%;padding:10px;border-radius:8px;border:1px solid #334155;background:#0b1220;color:#e5e7eb}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:8px;border-bottom:1px solid #1e293b;text-align:left}
th{color:var(--muted);font-size:12px}
#toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#16a34a;color:#fff;padding:12px 20px;border-radius:10px;display:none;z-index:99}
.hidden{display:none}
.tabs{display:flex;gap:8px;margin-bottom:12px}
.tab{padding:8px 14px;border-radius:8px;background:#1e293b;color:var(--muted)}
.tab.active{background:var(--accent2);color:#fff}
</style>
</head>
<body>
<header>
  <h1>SODANGI MOTORS - Agent Dashboard <span style="font-size:11px;opacity:.8">ENGINE v3</span></h1>
  <div><span class="who" id="who"></span><button class="btn-ghost hidden" id="logoutBtn" onclick="logout()">Logout</button></div>
</header>
<main>
  <section class="card hidden" id="cfgBanner" style="border-color:#dc2626">
    <h2 style="color:#f87171">Media storage not configured</h2>
    <div style="font-size:13px;color:#fbbf24">Pictures and videos CANNOT upload until the free Cloudinary pipe is connected (2 minutes, one time, forever). Click below to open the Media Storage card.</div>
    <br><button class="btn-primary" style="background:#dc2626;color:#fff" onclick="document.getElementById('setCard').scrollIntoView();document.getElementById('cCloud').focus();">Open Media Storage Setup</button>
  </section>

  <section class="card" id="authCard">
    <div class="tabs">
      <button class="tab active" id="tabLogin" onclick="showTab('login')">Login</button>
      <button class="tab" id="tabReg" onclick="showTab('reg')">Create Agent Account</button>
    </div>
    <div id="loginForm">
      <label>Email</label><input id="liEmail" type="email" placeholder="agent@sodangi.com">
      <label>Password</label><input id="liPass" type="password">
      <br><br><button class="btn-primary" onclick="doLogin()">Login</button>
    </div>
    <div id="regForm" class="hidden">
      <label>Full Name</label><input id="rgName" placeholder="Musa Abdullahi">
      <label>Email</label><input id="rgEmail" type="email">
      <label>Password</label><input id="rgPass" type="password">
      <br><br><button class="btn-primary" onclick="doRegister()">Create Account</button>
    </div>
  </section>
  <section class="card hidden" id="dashCard">
    <h2>Upload Product</h2>
    <div class="row">
      <div><label>Product Name</label><input id="pName" placeholder="Toyota Corolla 2020"></div>
      <div><label>Price (Naira)</label><input id="pPrice" type="number" placeholder="7500000"></div>
    </div>
    <div class="row">
      <div><label>Product Photos (select many from gallery)</label><input type="file" id="pFile" accept="image/*" multiple onchange="uploadMedia()"><input id="pImg" type="hidden"><div id="mediaPreview" style="margin-top:8px;color:#7dd3fc;font-size:13px;"></div><button class="btn-ghost" style="margin-top:8px;border:1px solid #334155;color:#7dd3fc" onclick="testEngine()">Test Media Engine</button><div style="margin-top:10px"><label>Product Video (optional - sent only when customer asks for bidiyo)</label><input type="file" id="pVideo" accept="video/*" onchange="uploadVideo()"><input id="pVid" type="hidden"><div id="videoPreview" style="margin-top:8px;color:#7dd3fc;font-size:13px;"></div></div></div>
      <div><label>Stock</label><input id="pStock" type="number" value="5"></div>
    </div>
    <label>Description</label><input id="pDesc" placeholder="Short sales description">
    <br><br><button class="btn-primary" onclick="uploadProduct()">Upload Product</button>
  </section>
  <section class="card hidden" id="listCard">
    <h2>Live Inventory (what the WhatsApp bot sells)</h2>
    <table><thead><tr><th>Name</th><th>Price</th><th>Stock</th><th>Media</th></tr></thead><tbody id="prodBody"></tbody></table>
  </section>
  <section class="card hidden" id="waCard">
    <h2>Register Company WhatsApp Number (Owner only)</h2>
    <label>Phone Number ID</label><input id="waPid" placeholder="1332619033263966">
    <label>Access Token (EAA...)</label><input id="waTok">
    <label>Display Name</label><input id="waName" placeholder="Sodangi Motors">
    <br><br><button class="btn-primary" onclick="connectWA()">Save WhatsApp Config</button>
  </section>

  <section class="card hidden" id="setCard">
    <h2>Media Storage (Cloudinary - required for video & big files)</h2>
    <label>Cloudinary Cloud Name</label><input id="cCloud" placeholder="e.g. dx123abc4">
    <label>Unsigned Upload Preset</label><input id="cPreset" placeholder="e.g. sodangi">
    <br><br><button class="btn-primary" onclick="saveSettings()">Save Media Settings</button>
    <div style="margin-top:10px;font-size:12px;color:#fbbf24">REQUIRED for pictures and videos: cloudinary.com > Sign up free with Google > copy the Cloud Name shown on dashboard > gear Settings > Upload > Upload presets > Add upload preset > name: sodangi > Signing mode: UNSIGNED > Save > paste both values above > Save Media Settings > then click Test Media Engine.</div>
  </section>
</main>
<div id="toast"></div>
<script>
var API="/api/v1/dashboard";
var TOKEN=localStorage.getItem("sodangi_token")||"";
var ROLE=localStorage.getItem("sodangi_role")||"";
var NAME=localStorage.getItem("sodangi_name")||"";
function toast(m,c){var t=document.getElementById("toast");t.textContent=m;t.style.background=c||"#16a34a";t.style.display="block";setTimeout(function(){t.style.display="none";},3500);}
function showTab(w){document.getElementById("tabLogin").className="tab"+(w=="login"?" active":"");document.getElementById("tabReg").className="tab"+(w=="reg"?" active":"");document.getElementById("loginForm").className=(w=="login"?"":"hidden");document.getElementById("regForm").className=(w=="reg"?"":"hidden");}
async function api(path,method,body,auth){var h={"Content-Type":"application/json"};if(auth){h["Authorization"]="Bearer "+TOKEN;}var r=await fetch(API+path,{method:method,headers:h,body:body?JSON.stringify(body):undefined});if(!r.ok){var e={};try{e=await r.json();}catch(x){}throw new Error(e.detail||("HTTP "+r.status));}return r.json();}
function enterDash(){document.getElementById("authCard").className="card hidden";document.getElementById("dashCard").className="card";document.getElementById("listCard").className="card";document.getElementById("waCard").className=(ROLE=="owner"?"card":"card hidden");document.getElementById("setCard").className=(ROLE=="owner"?"card":"card hidden");document.getElementById("logoutBtn").className="btn-ghost";document.getElementById("who").textContent=NAME+" ("+ROLE+")";loadProducts();loadSettings();}
async function doLogin(){try{var r=await api("/login","POST",{email:document.getElementById("liEmail").value,password:document.getElementById("liPass").value});TOKEN=r.token;ROLE=r.role;NAME=r.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);toast("Welcome "+NAME+"!");enterDash();}catch(e){toast(e.message,"#dc2626");}}
async function doRegister(){try{await api("/register","POST",{full_name:document.getElementById("rgName").value,email:document.getElementById("rgEmail").value,password:document.getElementById("rgPass").value});toast("Account created! Now login.");showTab("login");}catch(e){toast(e.message,"#dc2626");}}
function logout(){localStorage.removeItem("sodangi_token");localStorage.removeItem("sodangi_role");localStorage.removeItem("sodangi_name");location.reload();}
async function loadProducts(){try{var ps=await api("/products","GET");var b=document.getElementById("prodBody");b.innerHTML="";ps.forEach(function(p){var tr=document.createElement("tr");var imgs=p.images||[];
      var thumb=imgs.length?"<img src='"+imgs[0]+"' style='width:44px;height:44px;object-fit:cover;border-radius:6px;margin-right:8px;vertical-align:middle'>":"";
      var gal=imgs.length?"<a href='"+imgs[0]+"' target='_blank' style='color:#22c55e'>"+imgs.length+" media</a>":"-";
      tr.innerHTML="<td>"+thumb+p.name+"</td><td>&#8358;"+Number(p.price).toLocaleString()+"</td><td>"+p.stock+"</td><td>"+gal+"</td>";b.appendChild(tr);});}catch(e){toast(e.message,"#dc2626");}}
async function uploadProduct(){
  var nameV=document.getElementById("pName").value;
  var priceV=parseFloat(document.getElementById("pPrice").value);
  if(!nameV||isNaN(priceV)){toast("Fill product name and price first","#dc2626");return;}
  var filesCount=document.getElementById("pFile").files.length+document.getElementById("pVideo").files.length;
  var urls=[];try{urls=JSON.parse(document.getElementById("pImg").value||"[]");}catch(e){urls=[];}
  var vid=document.getElementById("pVid").value;
  if(vid){urls.push(vid);}
  if(filesCount>0&&urls.length===0){toast("No media uploaded yet! Pick your files and wait for the green check BEFORE saving.","#dc2626");return;}
  try{
    var r=await api("/products/upload","POST",{name:nameV,price:priceV,image_url:JSON.stringify(urls),description:document.getElementById("pDesc").value,stock:parseInt(document.getElementById("pStock").value||"1",10)},true);
    toast(r.message+" | "+(r.images_saved||0)+" media saved in DB");
    document.getElementById("pFile").value="";
    document.getElementById("pVideo").value="";
    document.getElementById("pImg").value="";
    document.getElementById("pVid").value="";
    document.getElementById("mediaPreview").textContent="";
    document.getElementById("videoPreview").textContent="";
    loadProducts();
  }catch(e){toast(e.message,"#dc2626");}
}

async function connectWA(){try{var r=await api("/connect-whatsapp","POST",{phone_number_id:document.getElementById("waPid").value,access_token:document.getElementById("waTok").value,display_name:document.getElementById("waName").value},true);toast(r.message);}catch(e){toast(e.message,"#dc2626");}}

var CLOUD={name:"",preset:""};
async function loadSettings(){try{var s=await api("/settings","GET");CLOUD.name=s.cloud_name||"";CLOUD.preset=s.upload_preset||"";document.getElementById("cCloud").value=CLOUD.name;document.getElementById("cPreset").value=CLOUD.preset;document.getElementById("cfgBanner").className=(ROLE=="owner"&&!CLOUD.name)?"card":"card hidden";}catch(e){}}
async function saveSettings(){try{var r=await api("/settings","POST",{cloud_name:document.getElementById("cCloud").value,upload_preset:document.getElementById("cPreset").value},true);CLOUD.name=document.getElementById("cCloud").value;CLOUD.preset=document.getElementById("cPreset").value;toast(r.message);document.getElementById("cfgBanner").className="card hidden";}catch(e){toast(e.message,"#dc2626");}}
async function putCloudinary(f){
  var fd=new FormData();fd.append("file",f);fd.append("upload_preset",CLOUD.preset);
  var r=await fetch("https://api.cloudinary.com/v1_1/"+CLOUD.name+"/auto/upload",{method:"POST",body:fd});
  if(!r.ok)throw new Error("cloudinary "+r.status);
  var d=await r.json();return d.secure_url;
}
async function putPixeldrain(f){
  var fd=new FormData();fd.append("file",f);
  var r=await fetch("https://pixeldrain.com/api/file/file",{method:"POST",body:fd});
  if(!r.ok)throw new Error("pixeldrain "+r.status);
  var d=await r.json();
  if(!d.id)throw new Error("pixeldrain no id");
  return "https://pixeldrain.com/api/file/"+d.id;
}
async function putRelay(f){
  if(f.size>4000000)throw new Error("too big for relay");
  var fd=new FormData();fd.append("file",f);
  var r=await fetch(API+"/upload-media",{method:"POST",headers:{"Authorization":"Bearer "+TOKEN},body:fd});
  if(!r.ok)throw new Error("relay "+r.status);
  var d=await r.json();return d.url;
}
async function uploadOne(f){
  var chain=[];
  if(CLOUD.name&&CLOUD.preset)chain.push(putCloudinary);
  chain.push(putPixeldrain);
  chain.push(putRelay);
  var lastErr="unknown";
  for(var a=0;a<chain.length;a++){
    for(var attempt=0;attempt<2;attempt++){
      try{return await chain[a](f);}catch(e){lastErr=e.message;}
    }
  }
  throw new Error(f.name+": "+lastErr);
}
async function uploadMedia(){
  var files=document.getElementById("pFile").files;
  if(!files.length)return;
  var prev=document.getElementById("mediaPreview");
  var urls=[];var failed=[];
  for(var i=0;i<files.length;i++){
    prev.textContent="Uploading "+(i+1)+" of "+files.length+": "+files[i].name;
    try{var u=await uploadOne(files[i]);urls.push(u);}
    catch(e){failed.push(files[i].name+" ["+e.message+"]");}
  }
  document.getElementById("pImg").value=JSON.stringify(urls);
  var msg="Uploaded "+urls.length+"/"+files.length+" file(s).";
  if(failed.length)msg+=" Failed: "+failed.join(", ");
  prev.innerHTML=(urls.length==files.length?"✅ ":"⚠️ ")+msg;
  toast(msg, urls.length==files.length?"#16a34a":"#dc2626");
}

async function testEngine(){
  var prev=document.getElementById("mediaPreview");
  try{
    var c=document.createElement("canvas");c.width=8;c.height=8;
    var ctx=c.getContext("2d");ctx.fillStyle="#22c55e";ctx.fillRect(0,0,8,8);
    var blob=await new Promise(function(res){c.toBlob(res,"image/png");});
    var f=new File([blob],"engine-test.png",{type:"image/png"});
    prev.textContent="Testing media engine...";
    var u=await uploadOne(f);
    prev.innerHTML="✅ Engine OK: <a href='"+u+"' target='_blank' style='color:#22c55e'>"+u.slice(0,60)+"</a>";
    toast("Media engine works! Select your gallery now.");
  }catch(e){
    prev.textContent="Engine test failed: "+e.message;
    toast("Engine test failed: "+e.message,"#dc2626");
  }
}

async function uploadVideo(){
  var f=document.getElementById("pVideo").files[0];
  if(!f)return;
  var prev=document.getElementById("videoPreview");
  prev.textContent="Uploading video "+f.name+" ... (videos are big, be patient)";
  try{
    var u=await uploadOne(f);
    document.getElementById("pVid").value=u;
    prev.innerHTML="Video ready! <a href='"+u+"' target='_blank' style='color:#22c55e'>Preview</a>";
    toast("Video uploaded! Customers get it only when they ask for bidiyo.");
  }catch(e){
    prev.textContent="Video upload failed: "+e.message;
    toast("Video upload failed: "+e.message,"#dc2626");
  }
}

function shareAd(){if(!AD_URL){toast("Open Profile tab first","#dc2626");return;}var u=location.origin+AD_URL;if(navigator.share){navigator.share({title:"Sodangi Motors Showroom",text:"Check my showroom!",url:u}).catch(function(){});}else{copyAd();}}
function copyAd(){if(!AD_URL){toast("Open Profile tab first","#dc2626");return;}var u=location.origin+AD_URL;if(navigator.clipboard){navigator.clipboard.writeText(u).then(function(){toast("Ad link copied! Paste on Instagram/Facebook status.");});}else{prompt("Copy your ad link:",u);}}

if(TOKEN){enterDash();}
</script>
</body>
</html>"""

@router.get("/ui", response_class=HTMLResponse)
def dashboard_ui():
    return HTMLResponse(content=DASHBOARD_HTML, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"})


# ---- STORAGE TRUTH SERUM ----
def 



_heal_images_column():
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





_heal_images_column()

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
    if not a or not a.is_active:
        return HTMLResponse("<h2 style='color:#fff;background:#0b1220;padding:40px;text-align:center'>Showroom unavailable</h2>")
    maps = db.query(ProductAgent).filter(ProductAgent.agent_id == a.id).all()
    pids = [m.product_id for m in maps]
    prods = db.query(Product).filter(Product.id.in_(pids), Product.is_active.is_(True)).all() if pids else []
    cards = ""
    hero = ""
    for i, p in enumerate(prods[:6]):
        imgs = _extract_imgs_list(p.images)
        u = imgs[0] if imgs else ""
        if i == 0 and u: hero = u
        if u: cards += "<div style='background:#151f38;border-radius:12px;overflow:hidden'><img src='" + u + "' style='width:100%;height:140px;object-fit:cover'><div style='padding:8px'><div style='color:#7dd3fc;font-size:13px;font-weight:700'>" + str(p.name) + "</div><div style='color:#22c55e;font-weight:800'>&#8358;" + format(float(p.price or 0), ",.0f") + "</div></div></div>"
    if not hero and a.photo_url: hero = str(a.photo_url)
    wt = "Sannu! I saw the showroom ad of Agent " + str(a.full_name) + " (AD:" + str(a.id) + "). Show me their cars!"
    wl = "https://wa.me/2349079437745?text=" + _up.quote(wt)
    nj = json.dumps(str(a.full_name)); hj = json.dumps(hero); tj = json.dumps(wt)
    css = "*{margin:0;padding:0;box-sizing:border-box;font-family:Segoe UI,Arial}body{background:#0b1220;color:#e5e7eb;padding-bottom:90px}.w{max-width:640px;margin:auto;padding:0 12px}.b{display:inline-block;background:#14532d;color:#86efac;font-size:11px;font-weight:800;padding:4px 10px;border-radius:99px;margin:10px 0 6px}.c{background:#151f38;border:1px solid #1e293b;border-radius:16px;padding:12px;margin-top:10px}.g{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}.cta{position:fixed;bottom:0;left:0;right:0;padding:10px;background:#0f172a}.cta a{display:block;text-align:center;background:#22c55e;color:#052e16;font-weight:900;font-size:17px;padding:15px;border-radius:14px;text-decoration:none}.r{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}.r button{flex:1;min-width:90px;border:0;border-radius:10px;padding:12px 6px;font-size:12px;font-weight:700;background:#1e293b;color:#e5e7eb}#t{position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#16a34a;color:#fff;padding:10px 16px;border-radius:10px;display:none;font-size:13px}"
    js = "var N=" + nj + ",H=" + hj + ",T=" + tj + ";function toast(m){var t=document.getElementById('t');t.textContent=m;t.style.display='block';setTimeout(function(){t.style.display='none'},3000)}function shareIt(){if(navigator.share){navigator.share({title:N,text:T,url:location.href}).catch(function(){})}else{copyIt()}}function fbIt(){window.open('https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(location.href))}function waIt(){window.open('https://wa.me/?text='+encodeURIComponent(T+' '+location.href))}function copyIt(){if(navigator.clipboard){navigator.clipboard.writeText(location.href).then(function(){toast('Ad link copied!')})}else{prompt('Copy:',location.href)}}function poster(){var c=document.createElement('canvas');c.width=1080;c.height=1350;var x=c.getContext('2d');var g=x.createLinearGradient(0,0,0,1350);g.addColorStop(0,'#065f46');g.addColorStop(1,'#0369a1');x.fillStyle=g;x.fillRect(0,0,1080,1350);x.fillStyle='#fff';x.font='bold 60px Arial';x.fillText('SODANGI MOTORS',60,130);x.font='34px Arial';x.fillStyle='#bbf7d0';x.fillText('VERIFIED AGENT SHOWROOM',60,190);function fin(){x.fillStyle='#fff';x.font='bold 78px Arial';x.fillText(N,60,1210);x.font='38px Arial';x.fillStyle='#e0f2fe';x.fillText('Tap ad link to chat on WhatsApp',60,1280);c.toBlob(function(b){var a2=document.createElement('a');a2.href=URL.createObjectURL(b);a2.download='sodangi-ad.png';a2.click();toast('Poster downloaded!')})}var im=new Image();im.crossOrigin='anonymous';im.onload=function(){x.drawImage(im,60,240,960,880);fin()};im.onerror=fin;if(H){im.src=H}else{fin()}}"
    html = "<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>" + str(a.full_name) + " | Sodangi Showroom</title><meta property='og:title' content='" + str(a.full_name) + " - Sodangi Motors'><meta property='og:description' content='" + str(a.bio or 'Verified car dealer') + "'><meta property='og:image' content='" + hero + "'><style>" + css + "</style></head><body><img src='" + hero + "' style='width:100%;height:220px;object-fit:cover'><div class='w'><span class='b'>SODANGI MOTORS VERIFIED SHOWROOM AD</span><div class='c' style='display:flex;gap:12px;align-items:center'><img src='" + str(a.photo_url or '') + "' style='width:60px;height:60px;border-radius:50%;object-fit:cover'><div><h1 style='font-size:18px;color:#fff'>" + str(a.full_name) + "</h1><div style='color:#94a3b8;font-size:13px'>" + str(a.phone_number or '') + "</div></div></div><p style='color:#94a3b8;font-size:14px;margin-top:8px'>" + str(a.bio or '') + "</p><div class='g'>" + cards + "</div><div class='r'><button onclick='shareIt()'>Share</button><button onclick='fbIt()'>Facebook</button><button onclick='waIt()'>WhatsApp</button><button onclick='copyIt()'>Copy Link</button><button onclick='poster()'>Poster</button></div></div><div class='cta'><a href='" + wl + "'>Chat on WhatsApp to Buy</a></div><div id='t'></div><script>" + js + "</script></body></html>"
    return HTMLResponse(html)


class AgentCreateReq(BaseModel):
    full_name: str
    email: str
    password: str
    phone: str = ""
    bio: str = ""
    photo_url: str = ""

class ToggleReq(BaseModel):
    email: str
    active: bool

class ProfileReq(BaseModel):
    bio: str = ""
    photo_url: str = ""
    phone: str = ""

def _owner(me):
    if me.get("r") != "owner":
        raise HTTPException(status_code=403, detail="Owner only")

@router.get("/agents")
def agents_list(request: Request, db: Session = Depends(get_db)):
    _owner(_auth(request))
    out = []
    for a in db.query(Agent).all():
        out.append({"id": a.id, "full_name": a.full_name, "email": a.email, "phone": a.phone_number or "", "active": bool(a.is_active), "page": "/api/v1/dashboard/agent/" + str(a.id)})
    return out

@router.post("/agents/create")
def agents_create(req: AgentCreateReq, request: Request, db: Session = Depends(get_db)):
    _owner(_auth(request))
    if db.query(Agent).filter(Agent.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    a = Agent(full_name=req.full_name, email=req.email, password_hash=_hash_pw(req.password), role="agent", phone_number=req.phone, bio=req.bio, photo_url=req.photo_url, is_active=True)
    db.add(a); db.commit(); db.refresh(a)
    return {"message": "Agent profile created", "agent_id": a.id, "page": "/api/v1/dashboard/agent/" + str(a.id)}

@router.post("/agents/toggle")
def agents_toggle(req: ToggleReq, request: Request, db: Session = Depends(get_db)):
    _owner(_auth(request))
    a = db.query(Agent).filter(Agent.email == req.email).first()
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    a.is_active = req.active
    db.commit()
    return {"message": ("Agent ACTIVATED" if req.active else "Agent DEACTIVATED"), "email": req.email}

@router.post("/products/mine")
def products_mine(request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    ag = db.query(Agent).filter(Agent.email == me["e"]).first()
    if me.get("r") == "owner":
        prods = db.query(Product).filter(Product.business_id == SODANGI_BUSINESS_ID).all()
    else:
        if not ag:
            return []
        maps = db.query(ProductAgent).filter(ProductAgent.agent_id == ag.id).all()
        pids = [m.product_id for m in maps]
        prods = db.query(Product).filter(Product.id.in_(pids)).all() if pids else []
    out = []
    for p in prods:
        imgs = _extract_imgs_list(p.images)
        out.append({"id": p.id, "name": p.name, "price": p.price, "media": len(imgs), "first_image": imgs[0] if imgs else "", "images": imgs})
    return out

class DeleteReq(BaseModel):
    product_id: int

@router.post("/products/delete")
def products_delete(req: DeleteReq, request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    if me.get("r") != "owner":
        ag = db.query(Agent).filter(Agent.email == me["e"]).first()
        if not ag or not db.query(ProductAgent).filter(ProductAgent.product_id == req.product_id, ProductAgent.agent_id == ag.id).first():
            raise HTTPException(status_code=403, detail="Not your car")
    p = db.query(Product).filter(Product.id == req.product_id).first()
    if p:
        db.delete(p)
    for m in db.query(ProductAgent).filter(ProductAgent.product_id == req.product_id).all():
        db.delete(m)
    db.commit()
    return {"message": "Product deleted"}

class PhotosReq(BaseModel):
    product_id: int
    image_urls: list

@router.post("/products/photos")
def products_photos(req: PhotosReq, request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    if me.get("r") != "owner":
        ag = db.query(Agent).filter(Agent.email == me["e"]).first()
        if not ag or not db.query(ProductAgent).filter(ProductAgent.product_id == req.product_id, ProductAgent.agent_id == ag.id).first():
            raise HTTPException(status_code=403, detail="Not your car")
    p = db.query(Product).filter(Product.id == req.product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    p.images = json.dumps([str(x) for x in req.image_urls])
    db.commit()
    return {"message": "Photos updated", "count": len(req.image_urls)}

@router.post("/profile/update")
def profile_update(req: ProfileReq, request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    a = db.query(Agent).filter(Agent.email == me["e"]).first()
    if not a:
        raise HTTPException(status_code=404, detail="Profile not found")
    if req.bio: a.bio = req.bio
    if req.photo_url: a.photo_url = req.photo_url
    if req.phone: a.phone_number = req.phone
    db.commit()
    return {"message": "Profile updated", "page": "/api/v1/dashboard/agent/" + str(a.id)}

@router.get("/profile/me")
def profile_me(request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    a = db.query(Agent).filter(Agent.email == me["e"]).first()
    if not a:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"full_name": a.full_name, "email": a.email, "phone": a.phone_number or "", "bio": a.bio or "", "photo_url": a.photo_url or "", "page": "/api/v1/dashboard/agent/" + str(a.id)}
