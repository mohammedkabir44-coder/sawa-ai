
import json, hmac, hashlib, base64, time, os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Text
from app.core.database import get_db, Base
from app.models.product import Product


import uuid
import urllib.request

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
    url = _upload_to_catbox(file_bytes, filename, f_ct)
    return {"url": url}

SECRET = "sodangi-sawa-secret-2026-do-not-share"
SODANGI_BUSINESS_ID = 3

class Agent(Base):
    __tablename__ = "sodangi_agents"
    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="agent")

class WAConfig(Base):
    __tablename__ = "sodangi_wa_config"
    id = Column(Integer, primary_key=True)
    phone_number_id = Column(String)
    access_token = Column(Text)
    display_name = Column(String)

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
    return [{"id": p.id, "name": p.name, "price": p.price, "stock": p.stock} for p in ps]

@router.post("/products/upload")
def upload(req: ProductReq, request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    try:
        p = Product(business_id=SODANGI_BUSINESS_ID, name=req.name, price=req.price, stock=req.stock, images=json.dumps([req.image_url]) if req.image_url else None, is_active=True)
        db.add(p)
        db.commit()
        return {"message": "Product uploaded by " + me["e"], "product": req.name}
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
  <h1>SODANGI MOTORS - Agent Dashboard</h1>
  <div><span class="who" id="who"></span><button class="btn-ghost hidden" id="logoutBtn" onclick="logout()">Logout</button></div>
</header>
<main>
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
      <div><label>Product Image or Video (from Gallery)</label><input type="file" id="pFile" accept="image/*,video/*" onchange="uploadMedia()"><input id="pImg" type="hidden"><div id="mediaPreview" style="margin-top:8px;color:#7dd3fc;font-size:13px;"></div></div>
      <div><label>Stock</label><input id="pStock" type="number" value="5"></div>
    </div>
    <label>Description</label><input id="pDesc" placeholder="Short sales description">
    <br><br><button class="btn-primary" onclick="uploadProduct()">Upload Product</button>
  </section>
  <section class="card hidden" id="listCard">
    <h2>Live Inventory (what the WhatsApp bot sells)</h2>
    <table><thead><tr><th>Name</th><th>Price</th><th>Stock</th></tr></thead><tbody id="prodBody"></tbody></table>
  </section>
  <section class="card hidden" id="waCard">
    <h2>Register Company WhatsApp Number (Owner only)</h2>
    <label>Phone Number ID</label><input id="waPid" placeholder="1332619033263966">
    <label>Access Token (EAA...)</label><input id="waTok">
    <label>Display Name</label><input id="waName" placeholder="Sodangi Motors">
    <br><br><button class="btn-primary" onclick="connectWA()">Save WhatsApp Config</button>
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
function enterDash(){document.getElementById("authCard").className="card hidden";document.getElementById("dashCard").className="card";document.getElementById("listCard").className="card";document.getElementById("waCard").className=(ROLE=="owner"?"card":"card hidden");document.getElementById("logoutBtn").className="btn-ghost";document.getElementById("who").textContent=NAME+" ("+ROLE+")";loadProducts();}
async function doLogin(){try{var r=await api("/login","POST",{email:document.getElementById("liEmail").value,password:document.getElementById("liPass").value});TOKEN=r.token;ROLE=r.role;NAME=r.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);toast("Welcome "+NAME+"!");enterDash();}catch(e){toast(e.message,"#dc2626");}}
async function doRegister(){try{await api("/register","POST",{full_name:document.getElementById("rgName").value,email:document.getElementById("rgEmail").value,password:document.getElementById("rgPass").value});toast("Account created! Now login.");showTab("login");}catch(e){toast(e.message,"#dc2626");}}
function logout(){localStorage.removeItem("sodangi_token");localStorage.removeItem("sodangi_role");localStorage.removeItem("sodangi_name");location.reload();}
async function loadProducts(){try{var ps=await api("/products","GET");var b=document.getElementById("prodBody");b.innerHTML="";ps.forEach(function(p){var tr=document.createElement("tr");tr.innerHTML="<td>"+p.name+"</td><td>&#8358;"+Number(p.price).toLocaleString()+"</td><td>"+p.stock+"</td>";b.appendChild(tr);});}catch(e){toast(e.message,"#dc2626");}}
async function uploadProduct(){try{var r=await api("/products/upload","POST",{name:document.getElementById("pName").value,price:parseFloat(document.getElementById("pPrice").value),image_url:document.getElementById("pImg").value,description:document.getElementById("pDesc").value,stock:parseInt(document.getElementById("pStock").value||"1",10)},true);toast(r.message);loadProducts();}catch(e){toast(e.message,"#dc2626");}}
async function connectWA(){try{var r=await api("/connect-whatsapp","POST",{phone_number_id:document.getElementById("waPid").value,access_token:document.getElementById("waTok").value,display_name:document.getElementById("waName").value},true);toast(r.message);}catch(e){toast(e.message,"#dc2626");}}

async function uploadMedia(){
  var f = document.getElementById("pFile").files[0];
  if(!f) return;
  var prev = document.getElementById("mediaPreview");
  prev.textContent = "Uploading " + f.name + "... (this may take a moment)";
  var fd = new FormData();
  fd.append("file", f);
  try {
    var r = await fetch(API + "/upload-media", {
      method: "POST",
      headers: {"Authorization": "Bearer " + TOKEN},
      body: fd
    });
    if(!r.ok) throw new Error("Upload failed");
    var data = await r.json();
    document.getElementById("pImg").value = data.url;
    prev.innerHTML = "✅ Uploaded! <a href='"+data.url+"' target='_blank' style='color:#22c55e'>View Media</a>";
    toast("Media uploaded! Now click Upload Product.");
  } catch(e) {
    prev.textContent = "Error: " + e.message;
    toast("Upload failed", "#dc2626");
  }
}

if(TOKEN){enterDash();}
</script>
</body>
</html>"""

@router.get("/ui", response_class=HTMLResponse)
def dashboard_ui():
    return DASHBOARD_HTML
