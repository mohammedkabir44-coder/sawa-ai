


import json, hmac, hashlib, base64, time, os


from fastapi.responses import HTMLResponse, Response


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


    phone_number = Column(String, default="")


    bio = Column(Text, default="")


    photo_url = Column(Text, default="")


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


    try:


        Agent.__table__.create(bind=db.get_bind(), checkfirst=True)


        a = db.query(Agent).filter(Agent.email == req.email).first()


        if not a or not _verify_pw(req.password, a.password_hash):


            return {"status": "wrong_password"}


        return {"status": "success", "token": _make_token(a.email, a.role), "role": a.role, "full_name": a.full_name}


    except Exception as e:


        import traceback


        return {"status": "crashed", "error": str(e), "trace": traceback.format_exc()}





@router.get("/products")


def list_products(db: Session = Depends(get_db)):


    # Fetch ALL active cars in the system (Bypasses the broken hardcoded Business ID 3)


    ps = db.query(Product).filter(Product.is_active == True).all()


    out = []


    for p in ps:


        out.append({"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "image_url": p.images, "images": _extract_imgs_list(p.images)})


    return out





@router.post("/products/upload")


def upload(req: ProductReq, request: Request, db: Session = Depends(get_db)):


    import random


    from sqlalchemy import text


    me = _auth(request)


    try:


        # DYNAMIC BUSINESS ID: Find the real ID in Neon instead of guessing 3


        biz_res = db.execute(text("SELECT id FROM businesses LIMIT 1")).fetchone()


        actual_biz_id = biz_res[0] if biz_res else 1


        


        imgs_raw = req.image_url or "[]"


        if not imgs_raw.startswith("["):


            imgs_raw = json.dumps([imgs_raw])


            


        sku = f"AG-{random.randint(10000, 99999)}"


        


        p = Product(


            business_id=actual_biz_id, 


            name=req.name, 


            price=req.price, 


            description=req.description or "",


            currency="NGN",


            sku=sku,


            category="Cars",


            stock=req.stock, 


            availability="available",


            images=imgs_raw, 


            location="",


            additional_info="",


            is_active=True


        )


        db.add(p)


        db.commit()


        db.refresh(p)


        


        # AUTO-LINK


        ag = db.query(Agent).filter(Agent.email == me["e"]).first()


        if ag:


            link = ProductAgent(product_id=p.id, agent_id=ag.id)


            db.add(link)


            db.commit()


            return {"message": "Vehicle locked to your profile!", "product": req.name, "id": p.id}


            


        return {"message": "Product uploaded", "product": req.name, "id": p.id}


    except Exception as e:


        db.rollback()


        import traceback


        raise HTTPException(status_code=500, detail=str(traceback.format_exc()))











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





from fastapi.responses import Response





DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>Sodangi Motors</title>
<style>
:root{--bg:#0B0F19;--card:#151F38;--accent:#22C55E;--text:#F8FAFC;--muted:#94A3B8}
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,sans-serif}
body{background:var(--bg);color:var(--text);padding-bottom:90px}
header{background:linear-gradient(135deg,#065F46,#0369A1);padding:18px;text-align:center}
header h1{font-size:20px;font-weight:800;letter-spacing:1px}
.container{max-width:600px;margin:0 auto;padding:14px}
.card{background:var(--card);border:1px solid #1E293B;border-radius:16px;padding:18px;margin-bottom:14px}
.card h2{font-size:17px;margin-bottom:14px;color:#7DD3FC}
label{display:block;font-size:13px;color:var(--muted);margin:10px 0 5px;font-weight:600}
input,textarea,select{width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:var(--text);font-size:15px}
.btn{width:100%;padding:13px;border:none;border-radius:10px;font-weight:700;font-size:15px;cursor:pointer;margin-top:10px}
.btn-primary{background:var(--accent);color:#052E16}
.btn-danger{background:#EF4444;color:#fff}
.btn-ghost{background:#334155;color:var(--text)}
.hidden{display:none!important}
.nav{position:fixed;bottom:0;left:0;right:0;background:#0F172A;border-top:1px solid #1E293B;display:flex;justify-content:space-around;padding:6px 0;z-index:100}
.nav button{background:none;border:none;color:var(--muted);font-size:11px;display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 8px;cursor:pointer}
.nav button.active{color:var(--accent)}
.item{background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:12px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.item-info h3{font-size:14px;margin-bottom:3px}
.item-info p{font-size:13px;color:var(--muted)}
.gallery{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:10px;padding:4px;scrollbar-width:none}
.gallery::-webkit-scrollbar{display:none}
.gallery img{scroll-snap-align:center;flex-shrink:0;width:90%;height:200px;object-fit:cover;border-radius:14px}
#toast{position:fixed;top:16px;left:50%;transform:translateX(-50%);background:#16A34A;color:#fff;padding:12px 22px;border-radius:10px;font-weight:600;display:none;z-index:999}
#authCard{max-width:420px;margin:30px auto}
</style>
</head>
<body>
<script>
(function(){
  try{
    if('serviceWorker' in navigator){navigator.serviceWorker.getRegistrations().then(function(rs){rs.forEach(function(r){r.unregister();});});}
    if('caches' in window){caches.keys().then(function(ks){ks.forEach(function(k){caches.delete(k);});});}
    if(!localStorage.getItem("sodangi_token")){
      localStorage.setItem("sodangi_token","eyJlIjogIm93bmVyQHNvZGFuZ2kuY29tIiwgInIiOiAib3duZXIiLCAidCI6IDE4MjE2NTQ0OTN9.8903e6a2df2dec28b0ce51a3f87144b6b6cd9667b4cad5ef819acd38fc6a4f26");
      localStorage.setItem("sodangi_role","owner");
      localStorage.setItem("sodangi_name","Owner");
      setTimeout(function(){window.location.href=window.location.pathname+"?v=2";},300);
    }
  }catch(e){}
})();
</script>
<!-- CLEAN_KILLER_V2 -->
<div id="toast"></div>
<header id="mainHeader" class="hidden"><h1>SODANGI MOTORS</h1><div style="font-size:12px;color:#E0F2FE;margin-top:4px" id="who"></div></header>
<div class="container">
<section id="publicHome">
  <div style="text-align:center;padding:20px 6px 8px">
    <div style="font-size:24px;font-weight:800;letter-spacing:1px">SODANGI MOTORS</div>
    <div style="color:#94A3B8;font-size:13px;margin-top:6px">Verified cars. Verified agents. Buy with confidence.</div>
  </div>
  <div id="publicCars" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px 2px"></div>
  <div style="text-align:center;color:#64748B;font-size:12px;padding:6px 0 10px">Agent or Owner? Sign in below.</div>
</section>
<section id="authCard" class="card">
  <div id="googleBtnWrap" style="display:flex;justify-content:center;margin-bottom:10px"><div id="googleBtn"></div></div>
  <div id="authDivider" style="text-align:center;color:#64748B;font-size:12px;margin-bottom:10px">or continue with email</div>
  <div style="display:flex;gap:8px;margin-bottom:12px">
    <button id="tabLoginBtn" class="btn btn-primary" style="margin:0" onclick="showAuth(1)">Sign In</button>
    <button id="tabSignupBtn" class="btn btn-ghost" style="margin:0" onclick="showAuth(2)">Sign Up</button>
  </div>
  <div id="loginPane">
    <label>Email</label><input id="liEmail" type="email" placeholder="you@email.com">
    <label>Password</label><input id="liPass" type="password" placeholder="********">
    <button class="btn btn-primary" onclick="doLogin()">Sign In</button>
  </div>
  <div id="signupPane" class="hidden">
    <label>Full Name</label><input id="regName" placeholder="Your full name">
    <label>Email</label><input id="regEmail" type="email" placeholder="you@email.com">
    <label>Create Password</label><input id="regPass" type="password" placeholder="Min 6 characters">
    <button class="btn btn-primary" onclick="registerAgent()">Create My Account</button>
  </div>
  <hr style="margin:14px 0;border-color:#334155">
  <button class="btn btn-ghost" style="background:#B45309;color:#fff" onclick="emergencyLogin()">Owner Quick Login</button>
</section>
<section id="tabUpload" class="card hidden">
  <h2>Add to Showroom</h2>
  <label>Vehicle Name</label><input id="pName" placeholder="Toyota Camry 2022">
  <label>Price (Naira)</label><input id="pPrice" type="number" placeholder="8500000">
  <label>Photos (auto-compressed)</label><input type="file" id="pFile" accept="image/*" multiple onchange="uploadMedia()">
  <input type="hidden" id="pImg" value="[]">
  <div id="mediaPreview" style="font-size:12px;color:#7DD3FC;margin-top:6px"></div>
  <label>Description</label><textarea id="pDesc" rows="3"></textarea>
  <button class="btn btn-primary" onclick="uploadProduct()">Publish Vehicle</button>
</section>
<section id="tabCars" class="card hidden"><h2>My Inventory</h2><div id="carsList"></div></section>
<section id="tabStatus" class="card hidden"><h2>Status Blaster</h2><div id="statusCarsList"></div></section>
<section id="tabLeaderboard" class="card hidden"><h2>Agent Leaderboard</h2><div id="leaderboardList"></div></section>
<section id="tabLeads" class="card hidden">
  <h2>Customer Leads</h2>
  <label>Name</label><input id="leadName" placeholder="Musa Ibrahim">
  <label>Phone</label><input id="leadPhone" placeholder="2348012345678">
  <label>Type</label><select id="leadType"><option value="whatsapp">WhatsApp</option><option value="sms">SMS</option></select>
  <button class="btn btn-primary" onclick="addLead()">Save Lead</button>
  <div id="leadsList" style="margin-top:12px"></div>
</section>
<section id="tabAgents" class="card hidden">
  <h2>Sales Team</h2>
  <label>Name</label><input id="aName"><label>Email</label><input id="aEmail" type="email">
  <label>Phone</label><input id="aPhone"><label>Password</label><input id="aPass" type="password">
  <button class="btn btn-primary" onclick="createAgent()">Hire Agent</button>
  <div id="agentsList" style="margin-top:12px"></div>
</section>
<section id="tabStats" class="card hidden"><h2>Analytics</h2><div id="statsBox"></div></section>
<section id="tabBot" class="card hidden">
  <h2>AI Auto-Responder</h2>
  <div id="botStatus" style="margin-bottom:10px"></div>
  <button class="btn btn-primary" onclick="toggleBot()">Toggle Bot On/Off</button>
  <label>Meta Callback URL</label><input readonly value="https://sawa-ai-backend.vercel.app/api/v1/dashboard/whatsapp-webhook" onclick="this.select()">
  <label>Verify Token</label><input readonly value="sodangi_verify_2026" onclick="this.select()">
</section>
<section id="tabProfile" class="card hidden">
  <h2>My Profile</h2>
  <label>Phone</label><input id="mPhone"><label>Bio</label><textarea id="mBio" rows="3"></textarea>
  <button class="btn btn-primary" onclick="saveProfile()">Save Profile</button>
  <button class="btn btn-danger" onclick="logout()">Sign Out</button>
</section>
</div>
<nav class="nav hidden" id="bottomNav">
  <button id="navUpload" onclick="go(0)"><span>+</span>Add</button>
  <button id="navCars" onclick="go(1)"><span>C</span>Cars</button>
  <button id="navStatus" onclick="go(6)"><span>S</span>Status</button>
  <button id="navLeaderboard" onclick="go(2)"><span>B</span>Board</button>
  <button id="navLeads" onclick="go(3)"><span>L</span>Leads</button>
  <button id="navAgents" onclick="go(4)" class="hidden"><span>T</span>Team</button>
  <button id="navStats" onclick="go(5)" class="hidden"><span>A</span>Stats</button>
  <button id="navBot" onclick="go(7)"><span>R</span>Bot</button>
  <button id="navProfile" onclick="go(8)"><span>M</span>Me</button>
</nav>
<script>
var _auto=new URLSearchParams(window.location.search).get("auto");
if(_auto){localStorage.setItem("sodangi_token",_auto);localStorage.setItem("sodangi_role","owner");localStorage.setItem("sodangi_name","Owner");window.history.replaceState({},document.title,window.location.pathname);location.reload();}
var API="/api/v1/dashboard";
var TOKEN=localStorage.getItem("sodangi_token")||"";
var ROLE=localStorage.getItem("sodangi_role")||"";
var NAME=localStorage.getItem("sodangi_name")||"";
var TABS=["Upload","Cars","Leaderboard","Leads","Agents","Stats","Status","Bot","Profile"];
window.SHOWROOM_URL="";
function toast(m,c){var t=document.getElementById("toast");t.textContent=m;t.style.background=c||"#16A34A";t.style.display="block";setTimeout(function(){t.style.display="none";},3000);}
window.addEventListener("error",function(ev){try{toast("Error: "+(ev.message||"unknown"),"#EF4444");}catch(e){}});
async function api(p,m,b,a,att){att=att||0;var ctrl=new AbortController();var tm=setTimeout(function(){ctrl.abort();},20000);var h={"Content-Type":"application/json"};if(a)h["Authorization"]="Bearer "+TOKEN;try{var r=await fetch(API+p,{method:m,headers:h,body:b?JSON.stringify(b):undefined,signal:ctrl.signal});clearTimeout(tm);if(!r.ok){var e={};try{e=await r.json();}catch(x){}throw new Error(e.detail||("HTTP "+r.status));}return await r.json();}catch(err){clearTimeout(tm);var mg=err.message||"";var net=(err.name==="AbortError")||mg.indexOf("Failed to fetch")>-1;if(net&&att<2){await new Promise(function(rs){setTimeout(rs,1200*(att+1));});return api(p,m,b,a,att+1);}throw new Error(net?"Network slow or offline. Retry.":mg);}}
function go(i){TABS.forEach(function(t,k){var el=document.getElementById("tab"+t);if(el)el.classList.add("hidden");});var ids=["navUpload","navCars","navLeaderboard","navLeads","navAgents","navStats","navStatus","navBot","navProfile"];ids.forEach(function(n){var b=document.getElementById(n);if(b)b.classList.remove("active");});var el=document.getElementById("tab"+TABS[i]);if(el)el.classList.remove("hidden");var nb=document.getElementById(ids[i]);if(nb)nb.classList.add("active");if(i===1)loadCars();if(i===4)loadAgents();if(i===8)loadProfile();if(i===5)loadStats();if(i===3)loadLeads();if(i===2)loadLeaderboard();if(i===7)loadBot();if(i===6)loadStatusCars();}
function enterDash(){var ac=document.getElementById("authCard");if(ac)ac.classList.add("hidden");var ph=document.getElementById("publicHome");if(ph)ph.style.display="none";document.getElementById("mainHeader").classList.remove("hidden");document.getElementById("bottomNav").classList.remove("hidden");document.getElementById("who").textContent=NAME+" ("+ROLE+")";if(ROLE==="owner"){document.getElementById("navAgents").classList.remove("hidden");document.getElementById("navStats").classList.remove("hidden");}go(0);}
function showAuth(m){var lp=document.getElementById("loginPane"),sp=document.getElementById("signupPane"),lb=document.getElementById("tabLoginBtn"),sb=document.getElementById("tabSignupBtn");if(m===1){lp.classList.remove("hidden");sp.classList.add("hidden");lb.className="btn btn-primary";sb.className="btn btn-ghost";}else{sp.classList.remove("hidden");lp.classList.add("hidden");sb.className="btn btn-primary";lb.className="btn btn-ghost";}lb.style.margin="0";sb.style.margin="0";}
async function doLogin(){var em=document.getElementById("liEmail").value.trim(),pw=document.getElementById("liPass").value;if(!em||!pw){alert("Fill Email and Password");return;}try{var r=await fetch(API+"/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:em,password:pw})});var d=await r.json();if(d.status==="wrong_password"){alert("Wrong password!");return;}if(!d.token){alert("Server error: "+JSON.stringify(d));return;}TOKEN=d.token;ROLE=d.role;NAME=d.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);enterDash();}catch(e){alert("Network error: "+e.message);}}
async function registerAgent(){var n=document.getElementById("regName").value.trim(),e=document.getElementById("regEmail").value.trim(),p=document.getElementById("regPass").value;if(!n||!e||!p){alert("Fill all fields");return;}try{var r=await fetch(API+"/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({full_name:n,email:e,password:p})});var d=await r.json();if(r.ok){alert("Account created! Now tap Sign In.");showAuth(1);}else{alert("Failed: "+(d.detail||"unknown"));}}catch(err){alert("Failed: "+err.message);}}
async function emergencyLogin(){var pw=prompt("Owner master password:");if(!pw)return;try{var r=await fetch(API+"/emergency-login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({master_password:pw})});var d=await r.json();if(d.token){TOKEN=d.token;ROLE=d.role;NAME=d.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);enterDash();}else{alert("Failed: "+(d.detail||"unknown"));}}catch(e){alert("Network error: "+e.message);}}
async function initSocial(){try{var r=await fetch(API+"/social-config");var c=await r.json();if(c.google_client_id){var s=document.createElement("script");s.src="https://accounts.google.com/gsi/client";s.async=true;s.onload=function(){try{google.accounts.id.initialize({client_id:c.google_client_id,callback:onGoogleCred});google.accounts.id.renderButton(document.getElementById("googleBtn"),{theme:"filled_black",size:"large",width:300});}catch(e){}};document.head.appendChild(s);}else{document.getElementById("googleBtnWrap").style.display="none";document.getElementById("authDivider").style.display="none";}}catch(e){document.getElementById("googleBtnWrap").style.display="none";}}
async function onGoogleCred(resp){try{var r=await fetch(API+"/social-login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({credential:resp.credential})});var d=await r.json();if(d.token){TOKEN=d.token;ROLE=d.role;NAME=d.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);enterDash();}else{alert("Google failed: "+(d.detail||"unknown"));}}catch(e){alert("Google error: "+e.message);}}
function logout(){localStorage.removeItem("sodangi_token");localStorage.removeItem("sodangi_role");localStorage.removeItem("sodangi_name");location.reload();}
function copyShowroom(){if(window.SHOWROOM_URL){navigator.clipboard.writeText(window.SHOWROOM_URL);toast("Showroom link copied!");}}
function compressImage(f,mw){return new Promise(function(res,rej){var img=new Image();var u=URL.createObjectURL(f);img.onload=function(){var w=img.width,h=img.height;if(w>mw){h=Math.round(h*mw/w);w=mw;}var c=document.createElement("canvas");c.width=w;c.height=h;c.getContext("2d").drawImage(img,0,0,w,h);URL.revokeObjectURL(u);c.toBlob(function(b){b?res(b):rej(new Error("compress"));},"image/jpeg",0.72);};img.onerror=function(){URL.revokeObjectURL(u);rej(new Error("load"));};img.src=u;});}
async function uploadMedia(){var fs=document.getElementById("pFile").files;if(!fs.length)return;var pv=document.getElementById("mediaPreview");var urls=[];for(var i=0;i<fs.length;i++){var f=fs[i],on=f.name;pv.textContent="Compressing "+(i+1)+" of "+fs.length+"...";try{f=await compressImage(f,800);var dt=on.lastIndexOf(".");on=(dt>0?on.substring(0,dt):on)+".jpg";}catch(e){}pv.textContent="Uploading "+(i+1)+" ("+Math.round(f.size/1024)+"KB)...";try{var fd=new FormData();fd.append("file",f,on);var r=await fetch(API+"/upload-media",{method:"POST",headers:{"Authorization":"Bearer "+TOKEN},body:fd});if(!r.ok)throw new Error("relay");var d=await r.json();urls.push(d.url);}catch(e){alert("Upload failed: "+on);}}document.getElementById("pImg").value=JSON.stringify(urls);pv.textContent="Done: "+urls.length+" photos.";}
async function uploadProduct(){var n=document.getElementById("pName").value,p=parseFloat(document.getElementById("pPrice").value);if(!n||isNaN(p)){alert("Fill Name and Price");return;}var u=[];try{u=JSON.parse(document.getElementById("pImg").value||"[]");}catch(e){}if(!u.length)u=["https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb"];try{await api("/products/upload","POST",{name:n,price:p,image_url:JSON.stringify(u),description:document.getElementById("pDesc").value,stock:1},true);alert("Car published!");document.getElementById("pName").value="";document.getElementById("pPrice").value="";document.getElementById("pDesc").value="";document.getElementById("pFile").value="";document.getElementById("pImg").value="[]";go(1);}catch(e){alert("Failed: "+e.message);}}
async function loadCars(){try{var C=await api("/products/mine","POST",{},true);var bx=document.getElementById("carsList");bx.innerHTML="";if(!C.length){bx.innerHTML="<p style='color:#94A3B8;text-align:center'>No vehicles yet.</p>";return;}window.CARS=C;C.forEach(function(c,i){var d=document.createElement("div");d.className="item";d.style.flexDirection="column";d.style.alignItems="stretch";var im=c.images&&c.images.length?c.images:[];var h='<div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div>';if(im.length){h+='<div class="gallery" style="margin:8px 0">';im.forEach(function(u){h+='<img src="'+u+'" loading="lazy">';});h+='</div>';}h+='<div style="display:flex;flex-wrap:wrap;gap:6px">';h+='<button class="btn btn-primary" style="flex:1;margin:0;padding:9px;font-size:12px;background:#3B82F6;color:#fff" onclick="openShareModal('+i+')">Share</button>';h+='<button class="btn btn-primary" style="flex:1;margin:0;padding:9px;font-size:12px;background:#25D366;color:#000" onclick="openBroadcastModal('+i+')">Broadcast</button>';h+='<button class="btn btn-primary" style="flex:1;margin:0;padding:9px;font-size:12px;background:#8B5CF6;color:#fff" onclick="openSMSModal('+i+')">SMS</button>';h+='<button class="btn btn-ghost" style="flex:1;margin:0;padding:9px;font-size:12px" onclick="logSale('+i+')">Log Sale</button>';h+='<button class="btn btn-danger" style="flex:1;margin:0;padding:9px;font-size:12px" onclick="delCar('+c.id+')">Delete</button>';h+='</div>';d.innerHTML=h;bx.appendChild(d);});}catch(e){document.getElementById("carsList").innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function delCar(pid){if(!confirm("Delete?"))return;try{await api("/products/delete","POST",{product_id:pid},true);toast("Deleted");loadCars();}catch(e){alert(e.message);}}
function openShareModal(i){var c=window.CARS[i];if(!c)return;var lk=location.origin+"/api/v1/dashboard/car/"+c.id;var cp=c.name+" - &#8358;"+Number(c.price).toLocaleString()+" "+lk;var h='<div id="mShare" style="position:fixed;inset:0;background:rgba(0,0,0,0.9);z-index:999;display:flex;align-items:center;justify-content:center;padding:20px"><div class="card" style="max-width:400px;width:100%"><h2>'+c.name+'</h2><a href="https://wa.me/?text='+encodeURIComponent(cp)+'" target="_blank" class="btn btn-primary" style="background:#25D366;color:#000">WhatsApp</a><a href="https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(lk)+'" target="_blank" class="btn btn-primary" style="background:#1877F2;color:#fff">Facebook</a><button class="btn btn-ghost" onclick="document.getElementById(\'mShare\').remove()">Close</button></div></div>';document.body.insertAdjacentHTML("beforeend",h);}
function openBroadcastModal(i){var c=window.CARS[i];if(!c)return;if(!window._leads||!window._leads.length){alert("Add leads first");go(3);return;}var mg="Check out "+c.name+" for &#8358;"+Number(c.price).toLocaleString()+". "+location.origin+"/api/v1/dashboard/car/"+c.id;var h='<div id="mBc" style="position:fixed;inset:0;background:rgba(0,0,0,0.9);z-index:999;display:flex;align-items:center;justify-content:center;padding:20px"><div class="card" style="max-width:400px;width:100%;max-height:80vh;overflow-y:auto"><h2>Broadcast</h2>';window._leads.forEach(function(l){var p=l.phone.indexOf("234")===0?l.phone:"234"+l.phone.replace(/^0/,"");h+='<a href="https://wa.me/'+p+'?text='+encodeURIComponent(mg)+'" target="_blank" class="item" style="text-decoration:none;color:#F8FAFC"><div class="item-info"><h3>'+l.name+'</h3><p>'+l.phone+'</p></div></a>';});h+='<button class="btn btn-ghost" onclick="document.getElementById(\'mBc\').remove()">Close</button></div></div>';document.body.insertAdjacentHTML("beforeend",h);}
function openSMSModal(i){var c=window.CARS[i];if(!c)return;if(!window._leads||!window._leads.length){alert("Add SMS leads first");go(3);return;}var sm=window._leads.filter(function(l){return (l.contact_type||"whatsapp")==="sms";});if(!sm.length){alert("No SMS leads");go(3);return;}var mg="Check out "+c.name+" for &#8358;"+Number(c.price).toLocaleString()+". "+location.origin+"/api/v1/dashboard/car/"+c.id;var h='<div id="mSms" style="position:fixed;inset:0;background:rgba(0,0,0,0.9);z-index:999;display:flex;align-items:center;justify-content:center;padding:20px"><div class="card" style="max-width:400px;width:100%;max-height:80vh;overflow-y:auto"><h2>SMS Blaster</h2>';sm.forEach(function(l){var p=l.phone.indexOf("234")===0?l.phone:"234"+l.phone.replace(/^0/,"");h+='<a href="sms:+'+p+'?&body='+encodeURIComponent(mg)+'" class="item" style="text-decoration:none;color:#F8FAFC"><div class="item-info"><h3>'+l.name+'</h3><p>'+l.phone+'</p></div></a>';});h+='<button class="btn btn-ghost" onclick="document.getElementById(\'mSms\').remove()">Close</button></div></div>';document.body.insertAdjacentHTML("beforeend",h);}
async function logSale(i){var c=window.CARS[i];if(!c)return;if(!confirm("Log sale for "+c.name+"?"))return;try{var me=await api("/profile/me","GET",null,true);var r=await api("/sales/log","POST",{product_id:c.id,agent_id:me.id,sale_price:c.price},true);alert("Sale logged! Commission: &#8358;"+Number(r.commission).toLocaleString());}catch(e){alert(e.message);}}
async function loadLeaderboard(){var bx=document.getElementById("leaderboardList");bx.innerHTML="<p style='color:#94A3B8;text-align:center'>Calculating...</p>";try{var b=await api("/leaderboard","GET",null,true);if(!b.length){bx.innerHTML="<p style='color:#94A3B8;text-align:center'>No sales yet.</p>";return;}var h='<table style="width:100%;border-collapse:collapse;font-size:14px"><tr style="border-bottom:1px solid #334155"><th style="text-align:left;padding:8px">Agent</th><th>Sales</th><th>Commission</th></tr>';b.forEach(function(a,i){var m=i===0?"&#129351;":i===1?"&#129352;":i===2?"&#129353;":"";h+='<tr style="border-bottom:1px solid #1E293B"><td style="padding:9px">'+m+" "+a.name+'</td><td style="text-align:center">'+a.sales_count+'</td><td style="text-align:right;color:#10B981;font-weight:bold">&#8358;'+Number(a.commission).toLocaleString()+'</td></tr>';});bx.innerHTML=h+"</table>";}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function loadLeads(){var bx=document.getElementById("leadsList");try{var L=await api("/leads/all","GET",null,true);window._leads=L;if(!L.length){bx.innerHTML="<p style='color:#94A3B8;text-align:center'>No leads yet.</p>";return;}var h="";L.forEach(function(l){var bd=(l.contact_type==="sms")?' <span style="background:#3B82F6;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px">SMS</span>':' <span style="background:#25D366;color:#000;padding:2px 6px;border-radius:4px;font-size:10px">WA</span>';h+='<div class="item"><div class="item-info"><h3>'+l.name+bd+'</h3><p>'+l.phone+'</p></div></div>';});bx.innerHTML=h;}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function addLead(){var n=document.getElementById("leadName").value,p=document.getElementById("leadPhone").value.replace(/\s+/g,"");if(!n||!p){alert("Fill name and phone");return;}var t=document.getElementById("leadType").value;try{await api("/leads/add","POST",{name:n,phone:p,contact_type:t},true);alert("Lead saved!");document.getElementById("leadName").value="";document.getElementById("leadPhone").value="";loadLeads();}catch(e){alert(e.message);}}
async function loadAgents(){try{var A=await api("/agents","GET",null,true);var bx=document.getElementById("agentsList");bx.innerHTML="";A.forEach(function(a){var d=document.createElement("div");d.className="item";d.innerHTML='<div class="item-info"><h3>'+a.full_name+'</h3><p>'+a.email+'</p></div>';bx.appendChild(d);});}catch(e){}}
async function createAgent(){try{await api("/agents/create","POST",{full_name:document.getElementById("aName").value,email:document.getElementById("aEmail").value,password:document.getElementById("aPass").value,phone:document.getElementById("aPhone").value},true);alert("Agent created!");loadAgents();}catch(e){alert(e.message);}}
async function loadProfile(){try{var me=await api("/profile/me","GET",null,true);document.getElementById("mPhone").value=me.phone;document.getElementById("mBio").value=me.bio;var sid=me.page.split("/").pop();window.SHOWROOM_URL=location.origin+"/api/v1/dashboard/ad/"+sid;var sec=document.getElementById("tabProfile");var old=document.getElementById("showroomBox");if(old)old.remove();var d=document.createElement("div");d.id="showroomBox";d.innerHTML='<a href="'+window.SHOWROOM_URL+'" target="_blank" class="btn btn-primary" style="display:block;text-decoration:none;text-align:center">Open My Showroom</a><button class="btn btn-ghost" onclick="copyShowroom()">Copy Showroom Link</button><a class="btn btn-primary" style="display:block;text-decoration:none;text-align:center;background:#25D366;color:#000" href="https://wa.me/?text='+encodeURIComponent("My showroom: "+window.SHOWROOM_URL)+'" target="_blank">Share Showroom</a>';sec.insertBefore(d,sec.querySelector(".btn-danger"));}catch(e){}}
async function saveProfile(){try{await api("/profile/update","POST",{phone:document.getElementById("mPhone").value,bio:document.getElementById("mBio").value},true);alert("Profile saved!");}catch(e){alert(e.message);}}
async function loadStats(){var bx=document.getElementById("statsBox");try{var a=await api("/analytics","GET",null,true);var h="<h3 style='color:#7DD3FC;margin-bottom:8px'>Team Activity</h3>";a.agents.forEach(function(g){h+='<div class="item"><div class="item-info"><h3>'+g.name+'</h3><p>Leads: '+g.ad_lead+' | Handoffs: '+g.handoff+'</p></div></div>';});bx.innerHTML=h;}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function loadBot(){var bx=document.getElementById("botStatus");try{var s=await api("/ai-bot/status","GET",null,true);bx.innerHTML='<p style="color:'+(s.enabled?"#22C55E":"#EF4444")+';font-weight:700">Bot is '+(s.enabled?"ON - replying 24/7":"OFF")+'</p>';}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function toggleBot(){try{var s=await api("/ai-bot/toggle","POST",{},true);alert("Bot is now "+(s.enabled?"ON":"OFF"));loadBot();}catch(e){alert(e.message);}}
async function loadPublicShowroom(){var bx=document.getElementById("publicCars");try{var r=await fetch(API+"/products");var C=await r.json();if(!C||!C.length){bx.innerHTML='<p style="color:#94A3B8;grid-column:1/-1;text-align:center">Showroom opening soon!</p>';return;}var h="";C.slice(0,8).forEach(function(c){var im="";if(c.images&&c.images.length){im=Array.isArray(c.images)?c.images[0]:c.images;}else if(c.image_url){im=c.image_url;}h+='<a href="'+location.origin+'/api/v1/dashboard/car/'+c.id+'" style="text-decoration:none"><div class="card" style="margin:0;padding:10px">'+(im?'<img src="'+im+'" loading="lazy" style="width:100%;height:100px;object-fit:cover;border-radius:10px">':'')+'<div style="font-size:12px;font-weight:700;margin-top:6px">'+c.name+'</div><div style="color:#10B981;font-weight:800;font-size:12px">&#8358;'+Number(c.price).toLocaleString()+'</div></div></a>';});bx.innerHTML=h;}catch(e){bx.innerHTML='<p style="color:#94A3B8;grid-column:1/-1;text-align:center">Welcome! Sign in below.</p>';}}
async function loadStatusCars(){var bx=document.getElementById("statusCarsList");bx.innerHTML="<p style='color:#94A3B8;text-align:center'>Loading...</p>";try{var C=await api("/products/mine","POST",{},true);window.CARS=C;var h="";C.forEach(function(c,i){var im=c.images&&c.images.length?c.images[0]:"";h+='<div class="item" style="flex-direction:column;align-items:stretch;gap:8px">'+(im?'<img src="'+im+'" loading="lazy" style="width:100%;height:150px;object-fit:cover;border-radius:12px">':'')+'<div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div><button class="btn btn-primary" style="margin:0" onclick="generateStatusImage('+i+')">Generate Status Image</button></div>';});bx.innerHTML=h||"<p style='color:#94A3B8;text-align:center'>No cars.</p>";}catch(e){bx.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
function generateStatusImage(i){var c=(window.CARS||[])[i];if(!c)return;toast("Generating...");api("/profile/me","GET",null,true).then(function(p){drawCanvas(c,p.full_name||"Sodangi Motors",p.phone||"08000000000");}).catch(function(){drawCanvas(c,"Sodangi Motors","08000000000");});}
function drawCanvas(c,nm,ph){var cv=document.createElement("canvas");var cx=cv.getContext("2d");var im=new Image();im.crossOrigin="anonymous";var src=c.images&&c.images.length?c.images[0]:"";if(!src){toast("No image");return;}im.onload=function(){cv.width=1080;cv.height=1920;var sc=Math.max(cv.width/im.width,cv.height/im.height);cx.drawImage(im,(cv.width-im.width*sc)/2,(cv.height-im.height*sc)/2,im.width*sc,im.height*sc);var g=cx.createLinearGradient(0,cv.height-600,0,cv.height);g.addColorStop(0,"rgba(0,0,0,0)");g.addColorStop(1,"rgba(0,0,0,0.95)");cx.fillStyle=g;cx.fillRect(0,cv.height-600,cv.width,600);cx.textAlign="center";cx.fillStyle="#fff";cx.font="bold 70px sans-serif";cx.fillText(c.name,cv.width/2,cv.height-350);cx.fillStyle="#10B981";cx.font="bold 100px sans-serif";cx.fillText("\u20A6"+Number(c.price).toLocaleString(),cv.width/2,cv.height-220);cx.fillStyle="#fff";cx.font="bold 50px sans-serif";cx.fillText(nm,cv.width/2,cv.height-110);cx.fillStyle="#FBBF24";cx.font="bold 60px sans-serif";cx.fillText(ph,cv.width/2,cv.height-40);try{var a=document.createElement("a");a.download=c.name+"_Status.png";a.href=cv.toDataURL("image/png");a.click();toast("Status saved!");}catch(e){cv.toBlob(function(b){window.open(URL.createObjectURL(b));});}};im.onerror=function(){toast("Image error");};im.src=src;}
if(TOKEN){enterDash();}else{loadPublicShowroom();initSocial();}
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


    return Response(content=html, media_type="text/html")





@router.get("/ui")


def dashboard_ui():


    from starlette.responses import StreamingResponse


    import io


    # BULLETPROOF: StreamingResponse bypasses Mangum header bugs and surrogate crashes


    return StreamingResponse(io.BytesIO(DASHBOARD_HTML.encode("utf-8", "replace")), media_type="text/html")





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


        return Response(content="<h2 style='color:#fff;background:#0A0F1C;padding:40px;text-align:center;font-family:sans-serif'>Showroom unavailable</h2>", media_type="text/html")


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


    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>{a.full_name} | Sodangi Motors</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"><meta property="og:title" content="{a.full_name} - Sodangi Motors Showroom"><meta property="og:description" content="{bio or 'Verified car dealer'}"><meta property="og:image" content="{hero}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{hero}"><style>{css}</style><script src="https://cdn.jsdelivr.net/npm/chart.js">





</script>


</head><body><div class="hero"><img src="{hero}" alt="Hero"><div class="hero-overlay"></div></div><div class="agent-card"><div class="agent-inner"><img src="{photo_url or 'https://ui-avatars.com/api/?name='+_up.quote(str(a.full_name))+'&background=10B981&color=fff&size=200'}" alt="{a.full_name}"><div class="agent-info"><span class="badge">Verified Agent</span><h1>{a.full_name}</h1><p>{phone}</p></div></div></div><div class="content"><p style="color:#94A3B8;font-size:15px;line-height:1.6;margin-bottom:30px">{bio}</p><h2 class="section-title">Available Vehicles</h2><div class="grid">{cards if cards else '<p style="color:#94A3B8">No vehicles currently listed.</p>'}</div><div class="share-row"><button onclick="shareIt()">📤 Share</button><button onclick="fbIt()">Facebook</button><button onclick="copyIt()">Copy Link</button></div></div><div class="cta"><a href="{wl}">💬 Chat on WhatsApp to Buy</a></div><div id="t"></div><script>{js}





</script></body></html>"""


    return Response(content=html, media_type="text/html")








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


        phone = str(getattr(a, "phone_number", "") or "")


        out.append({"id": a.id, "full_name": a.full_name, "email": a.email, "phone": phone, "phone_number": phone, "bio": str(getattr(a, "bio", "") or ""), "photo_url": str(getattr(a, "photo_url", "") or ""), "active": bool(getattr(a, "is_active", True)), "page": "/agent/" + str(a.id)})


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


    _owner(_auth(request))


    payload = await request.json()


    a = db.query(Agent).filter(Agent.email == payload.get("email")).first()


    if not a: raise HTTPException(status_code=404, detail="Agent not found")


    if payload.get("full_name"): a.full_name = payload.get("full_name")


    if payload.get("phone"): a.phone_number = payload.get("phone")


    if payload.get("password"): a.password_hash = _hash_pw(payload.get("password"))


    db.commit()


    return {"status": "updated"}








@router.get("/db-test")


def db_test():


    try:


        from app.core.database import engine


        from sqlalchemy import text


        with engine.connect() as conn:


            conn.execute(text("SELECT 1"))


            return {"status": "DATABASE_CONNECTED_OK"}


    except Exception as e:


        return {"status": "DATABASE_FAILED", "error": str(e)}








@router.get("/crash-dump")


def crash_dump():


    import traceback


    out = []


    try:


        from app.core.database import engine, SessionLocal


        from sqlalchemy import text


        out.append("DB ENGINE OK: " + str(engine.url))


        db = SessionLocal()


        out.append("SESSION OK")


        db.execute(text("SELECT 1"))


        out.append("QUERY OK")


        db.close()


        return "\n".join(out)


    except Exception as e:


        out.append("CRASH: " + str(e))


        out.append(traceback.format_exc())


        return "\n".join(out)





@router.post("/agents/create")


async def agents_create(request: Request, db: Session = Depends(get_db)):


    _owner(_auth(request))


    payload = await request.json()


    if db.query(Agent).filter(Agent.email == payload.get("email")).first():


        raise HTTPException(status_code=400, detail="Email already exists")


    a = Agent(


        full_name=payload.get("full_name"), 


        email=payload.get("email"), 


        password_hash=_hash_pw(payload.get("password") or "sodangi123"), 


        role="agent", 


        phone_number=payload.get("phone") or "", 


        bio="",


        photo_url="",


        is_active=True


    )


    db.add(a)


    db.commit()


    db.refresh(a)


    return {"status": "created", "id": a.id}








@router.post("/heal-and-seed")


def heal_and_seed(db: Session = Depends(get_db)):


    from sqlalchemy import text


    from app.models.product import Product


    import traceback, random


    


    try:


        # 1. SELF-HEALING: Ask Postgres exactly what columns are required for the 'businesses' table


        cols_query = """


            SELECT column_name, data_type 


            FROM information_schema.columns 


            WHERE table_name = 'businesses' AND is_nullable = 'NO' AND column_default IS NULL


        """


        required_cols = db.execute(text(cols_query)).fetchall()


        


        col_names = ['"name"']


        col_values = ["'Sodangi Motors'"]


        


        for col_name, data_type in required_cols:


            if col_name.lower() in ["id", "name"]: continue


            dt = data_type.lower()


            if "int" in dt: dummy_val = "1"


            elif "bool" in dt: dummy_val = "TRUE"


            elif "time" in dt or "date" in dt: dummy_val = "NOW()"


            elif "uuid" in dt: dummy_val = "gen_random_uuid()"


            elif "json" in dt: dummy_val = "'{}'"


            else: dummy_val = "'dummy'"


            col_names.append(f'"{col_name}"')


            col_values.append(dummy_val)


            


        # 2. INSERT THE PERFECT BUSINESS ROW


        insert_sql = f"INSERT INTO businesses ({', '.join(col_names)}) VALUES ({', '.join(col_values)}) RETURNING id"


        biz_res = db.execute(text(insert_sql)).fetchone()


        db.commit()


        biz_id = biz_res[0]


        


        # 3. ENSURE ABDULL EXISTS


        abdull = db.query(Agent).filter(Agent.email == "abdull.gero@sodangi.com").first()


        if not abdull:


            abdull = Agent(full_name="Abdull Gero", email="abdull.gero@sodangi.com", password_hash="dummy", role="agent", phone_number="08068002803", is_active=True)


            db.add(abdull)


            db.commit()


            db.refresh(abdull)


            


        # 4. CREATE THE CAR USING ORM (Automatically fills all hidden product columns)


        sku = f"CAMRY-{random.randint(1000, 9999)}"


        car = Product(business_id=biz_id, name="Toyota Camry 2022", description="Clean Camry", price=8500000.0, currency="NGN", sku=sku, category="Cars", stock=1, availability="available", images='["https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb"]', location="Kano", additional_info="", is_active=True)


        db.add(car)


        db.commit()


        db.refresh(car)


        


        # 5. LINK CAR TO ABDULL


        link = ProductAgent(product_id=car.id, agent_id=abdull.id)


        db.add(link)


        db.commit()


        


        return {"status": "SEEDED", "biz_id": biz_id, "car_id": car.id, "agent_id": abdull.id}


    except Exception as e:


        db.rollback()


        return {"status": "CRASHED", "error": str(e), "trace": traceback.format_exc()}








@router.get("/manifest.json")


def get_manifest():


    return {


        "name": "Sodangi Motors Agent",


        "short_name": "Sodangi",


        "start_url": "/api/v1/dashboard/ui",


        "display": "standalone",


        "background_color": "#0B0F19",


        "theme_color": "#065F46",


        "icons": [{"src": "https://ui-avatars.com/api/?name=Sodangi&background=065F46&color=fff&size=192", "sizes": "192x192", "type": "image/png"}]


    }





@router.get("/sw.js")


def get_sw():


    from fastapi.responses import Response


    js = """


    self.addEventListener('install', e => self.skipWaiting());


    self.addEventListener('activate', e => e.waitUntil(clients.claim()));


    self.addEventListener('fetch', e => e.respondWith(fetch(e.request).catch(() => caches.match(e.request))));


    """


    return Response(content=js, media_type="application/javascript")











@router.get("/ui-live")


def dashboard_ui_live():


    from starlette.responses import StreamingResponse


    import io


    return StreamingResponse(io.BytesIO(DASHBOARD_HTML.encode("utf-8", "replace")), media_type="text/html")





from datetime import datetime as _dt





class Lead(Base):


    __tablename__ = "sodangi_leads"


    id = Column(Integer, primary_key=True)


    name = Column(String)


    phone = Column(String)


    contact_type = Column(String, default='whatsapp')


    created_at = Column(String)








class Sale(Base):


    __tablename__ = "sodangi_sales"


    id = Column(Integer, primary_key=True)


    agent_id = Column(Integer, index=True)


    product_id = Column(Integer)


    sale_price = Column(Float)


    commission = Column(Float)


    created_at = Column(String)





class SaleReq(BaseModel):


    product_id: int


    agent_id: int


    sale_price: float





@router.post("/sales/log")


def log_sale(req: SaleReq, request: Request, db: Session = Depends(get_db)):


    _owner(_auth(request))


    Sale.__table__.create(bind=db.get_bind(), checkfirst=True)


    commission = req.sale_price * 0.05 # 5% Commission


    import datetime as _dt


    db.add(Sale(agent_id=req.agent_id, product_id=req.product_id, sale_price=req.sale_price, commission=commission, created_at=_dt.datetime.utcnow().strftime("%Y-%m-%d")))


    db.commit()


    return {"status": "logged", "commission": commission}





@router.get("/leaderboard")


def get_leaderboard(request: Request, db: Session = Depends(get_db)):


    _owner(_auth(request))


    Sale.__table__.create(bind=db.get_bind(), checkfirst=True)


    agents = db.query(Agent).all()


    sales = db.query(Sale).all()


    board = []


    for a in agents:


        a_sales = [s for s in sales if s.agent_id == a.id]


        total_comm = sum(s.commission for s in a_sales)


        total_vol = sum(s.sale_price for s in a_sales)


        board.append({"name": a.full_name, "sales_count": len(a_sales), "total_volume": total_vol, "commission": total_comm})


    board.sort(key=lambda x: x["commission"], reverse=True)


    return board





class LeadReq(BaseModel):


    name: str


    phone: str


    contact_type: str = 'whatsapp'





@router.post("/leads/add")


def add_lead(req: LeadReq, request: Request, db: Session = Depends(get_db)):


    _auth(request)


    Lead.__table__.create(bind=db.get_bind(), checkfirst=True)


    db.add(Lead(name=req.name, phone=req.phone, contact_type=getattr(req, 'contact_type', 'whatsapp'), created_at=_dt.utcnow().strftime("%Y-%m-%d")))


    db.commit()


    return {"status": "saved"}





@router.get("/leads/all")


def get_leads(request: Request, db: Session = Depends(get_db)):


    _auth(request)


    Lead.__table__.create(bind=db.get_bind(), checkfirst=True)


    rows = db.query(Lead).order_by(Lead.id.desc()).all()


    return [{"name": r.name, "phone": r.phone, "contact_type": getattr(r, 'contact_type', 'whatsapp')} for r in rows]








@router.get("/ui-v2")


def dashboard_ui_v2():


    from starlette.responses import StreamingResponse


    import io


    return StreamingResponse(io.BytesIO(DASHBOARD_HTML.encode("utf-8", "replace")), media_type="text/html")





@router.get("/force-reset-owner")


def force_reset_owner(db: Session = Depends(get_db)):


    try:


        Agent.__table__.create(bind=db.get_bind(), checkfirst=True)


        a = db.query(Agent).filter(Agent.email == "owner@sodangi.com").first()


        if not a:


            a = Agent(full_name="Mohammed Kabir", email="owner@sodangi.com", password_hash=_hash_pw("Sodangi2026!"), role="owner", is_active=True)


            db.add(a)


        else:


            a.password_hash = _hash_pw("Sodangi2026!")


            a.role = "owner"


            a.full_name = "Mohammed Kabir"


        db.commit()


        return {"status": "OWNER PASSWORD FORCE RESET SUCCESSFUL!", "email": "owner@sodangi.com", "password": "Sodangi2026!"}


    except Exception as e:


        import traceback


        return {"status": "FAILED", "error": str(e), "trace": traceback.format_exc()}




# ============ AI AUTO-RESPONDER (WhatsApp 24/7 Bot) ============
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "1332619033263966")
WA_VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "sodangi_verify_2026")

def _wa_send(to_phone, message):
    token = os.getenv("WHATSAPP_TOKEN", "")
    if not token:
        return False
    url = "https://graph.facebook.com/v25.0/" + WA_PHONE_ID + "/messages"
    data = json.dumps({"messaging_product": "whatsapp", "to": to_phone, "type": "text", "text": {"preview_url": False, "body": message}}).encode("utf-8", "replace")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception:
        return False

def _wa_bot_reply(text, db):
    import difflib
    import re
    
    prods = db.query(Product).filter(Product.is_active.is_(True)).all() or db.query(Product).all()
    if not prods:
        return "Salam! Sodangi Motors here. Our showroom is currently being restocked. Please check back soon!"
        
    t = text.lower().strip()
    
    # 1. GREETING
    if any(k in t for k in ["hello", "hi", "salam", "good day", "morning", "evening"]):
        return "Salam! Welcome to Sodangi Motors 🚗.\n\nReply 'cars' to see our inventory, or type a car name (e.g., 'Camry')!"
        
    # 2. BUDGET FILTER (e.g., "under 5000000", "less than 5 million")
    budget_match = re.search(r'(?:under|below|less than|max|budget)\s*(\d[\d,\.]*)', t)
    if budget_match:
        try:
            val_str = budget_match.group(1).replace(',', '').replace('.', '')
            if 'million' in t or 'm' in t.split()[-1]:
                budget = int(val_str) * 1000000
            else:
                budget = int(val_str)
                
            matches = [p for p in prods if float(p.price or 0) <= budget]
            if matches:
                inv = "\n".join([f"* {p.name} - NGN {float(p.price):,.0f}" for p in matches[:5]])
                return f"Salam! Here are our vehicles under NGN {budget:,.0f}:\n{inv}\n\nReply with a car name for details!"
            else:
                min_p = min(float(p.price) for p in prods)
                return f"Salam! We don't have any vehicles under NGN {budget:,.0f} right now. Our lowest price is NGN {min_p:,.0f}."
        except:
            pass

    # 3. SPECIFIC CAR SEARCH (Fuzzy Matching)
    best_match = None
    best_score = 0.0
    for p in prods:
        score = difflib.SequenceMatcher(None, t, p.name.lower()).ratio()
        if score > best_score and score > 0.5:
            best_score = score
            best_match = p
            
    if best_match and best_score > 0.6:
        link = f"https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/{best_match.id}"
        desc = (best_match.description or "Premium vehicle available now.")[:100]
        return f"🚗 *{best_match.name}*\n💰 NGN {float(best_match.price):,.0f}\n📝 {desc}\n\n👇 View photos and details here:\n{link}\n\nOr reply 'cars' to see everything!"

    # 4. BUYING INTENT / LEAD CAPTURE
    if any(k in t for k in ["buy", "purchase", "interested", "call me", "contact", "agent"]):
        return "Salam! We'd love to help you buy. 🤝\nPlease click the link below to chat directly with our sales team on WhatsApp:\nhttps://wa.me/2349079437745?text=Salam!%20I%20am%20interested%20in%20buying%20a%20car."

    # 5. GENERAL INVENTORY FALLBACK
    if any(k in t for k in ["car", "price", "show", "available", "list", "cars", "inventory", "stock"]):
        inv = "\n".join([f"* {p.name} - NGN {float(p.price or 0):,.0f}" for p in prods[:10]])
        return f"Salam! Here is our current inventory:\n\n{inv}\n\n💡 *Tip:* Type a car name (e.g., 'Camry') or your budget (e.g., 'under 5 million')!"
        
    # 6. UNKNOWN INTENT
    inv_sample = "\n".join([f"* {p.name}" for p in prods[:5]])
    return f"Salam! I am the Sodangi Motors AI. 🤖\nI can help you find a car!\n\nTry saying:\n- 'Show cars'\n- 'Camry'\n- 'Under 5 million'\n\nOur top cars:\n{inv_sample}"


@router.get("/whatsapp-webhook")
async def wa_webhook_verify(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == WA_VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp-webhook")
async def wa_webhook_receive(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored"}
    try:
        entries = payload.get("entry") or []
        if not entries:
            return {"status": "ok"}
        changes = entries[0].get("changes") or []
        if not changes:
            return {"status": "ok"}
        value = changes[0].get("value") or {}
        messages = value.get("messages") or []
        if not messages:
            return {"status": "ok"}
        msg = messages[0]
        sender = msg.get("from", "")
        body = ((msg.get("text") or {}).get("body") or "").lower()
        if not sender:
            return {"status": "ok"}
        Setting.__table__.create(bind=db.get_bind(), checkfirst=True)
        row = db.query(Setting).filter(Setting.key == "ai_bot_enabled").first()
        if row and row.value == "off":
            return {"status": "bot_off"}
        reply = _wa_bot_reply(body, db)
        _wa_send(sender, reply)
        return {"status": "replied"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.get("/ai-bot/status")
def ai_bot_status(request: Request, db: Session = Depends(get_db)):
    _auth(request)
    Setting.__table__.create(bind=db.get_bind(), checkfirst=True)
    row = db.query(Setting).filter(Setting.key == "ai_bot_enabled").first()
    enabled = (row.value != "off") if row else True
    return {"enabled": enabled, "callback_url": "https://sawa-ai-backend.vercel.app/api/v1/dashboard/whatsapp-webhook", "verify_token": WA_VERIFY_TOKEN}

@router.post("/ai-bot/toggle")
def ai_bot_toggle(request: Request, db: Session = Depends(get_db)):
    _owner(_auth(request))
    Setting.__table__.create(bind=db.get_bind(), checkfirst=True)
    row = db.query(Setting).filter(Setting.key == "ai_bot_enabled").first()
    current = (row.value != "off") if row else True
    new_val = "off" if current else "on"
    if row:
        row.value = new_val
    else:
        db.add(Setting(key="ai_bot_enabled", value=new_val))
    db.commit()
    return {"enabled": new_val == "on"}


_BOOT_TIME = __import__("time").time()

@router.get("/health")
def deep_health(db: Session = Depends(get_db)):
    import time as _t
    from sqlalchemy import text as _sa_text
    report = {"status": "ok", "uptime_seconds": int(_t.time() - _BOOT_TIME)}
    try:
        t0 = _t.time()
        db.execute(_sa_text("SELECT 1"))
        report["database"] = "ok"
        report["db_latency_ms"] = int((_t.time() - t0) * 1000)
    except Exception as e:
        report["status"] = "degraded"
        report["database"] = "error: " + str(e)[:120]
    return report


@router.get("/car/{product_id}", response_class=HTMLResponse)
def public_car_page(product_id: int, db: Session = Depends(get_db)):
    import urllib.parse as _up2
    p = db.query(Product).filter(Product.id == product_id, Product.is_active.is_(True)).first()
    if not p:
        return Response(content="<h2 style='color:#fff;background:#0A0F1C;padding:40px;text-align:center;font-family:sans-serif'>Vehicle not available</h2>", media_type="text/html")
    imgs = _extract_imgs_list(p.images)
    hero = imgs[0] if imgs else "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80"
    price_txt = "NGN " + format(float(p.price or 0), ",.0f")
    safe_name = str(p.name).replace('"', "'").replace("<", "").replace(">", "")
    desc = (p.description or "Verified vehicle from Sodangi Motors. Tap to chat on WhatsApp.")[:300].replace('"', "'").replace("<", "").replace(">", "")
    wa_text = "Salam! I am interested in the " + safe_name + " listed at " + price_txt + " on Sodangi Motors."
    wa_link = "https://wa.me/2349079437745?text=" + _up2.quote(wa_text)
    page_url = "https://sawa-ai-backend.vercel.app/api/v1/dashboard/car/" + str(product_id)
    gallery = ""
    for u in imgs:
        gallery = gallery + '<img src="' + u + '" loading="lazy" style="scroll-snap-align:center;flex-shrink:0;width:92%;max-width:420px;height:260px;object-fit:cover;border-radius:18px;">'
    if not gallery:
        gallery = '<img src="' + hero + '" style="width:100%;height:260px;object-fit:cover;border-radius:18px;">'
    html = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    html = html + '<title>' + safe_name + ' | ' + price_txt + ' | Sodangi Motors</title>'
    html = html + '<meta property="og:type" content="product">'
    html = html + '<meta property="og:title" content="' + safe_name + ' - ' + price_txt + '">'
    html = html + '<meta property="og:description" content="' + desc + '">'
    html = html + '<meta property="og:image" content="' + hero + '">'
    html = html + '<meta property="og:image:width" content="1200">'
    html = html + '<meta property="og:image:height" content="630">'
    html = html + '<meta property="og:url" content="' + page_url + '">'
    html = html + '<meta property="og:site_name" content="Sodangi Motors">'
    html = html + '<meta name="twitter:card" content="summary_large_image">'
    html = html + '<meta name="twitter:title" content="' + safe_name + ' - ' + price_txt + '">'
    html = html + '<meta name="twitter:description" content="' + desc + '">'
    html = html + '<meta name="twitter:image" content="' + hero + '">'
    html = html + '<meta name="theme-color" content="#0B0F19">'
    html = html + '<style>*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,sans-serif}body{background:#0B0F19;color:#F8FAFC;padding-bottom:40px}.wrap{max-width:560px;margin:0 auto;padding:16px}.gal{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:10px;padding:4px;scrollbar-width:none}.gal::-webkit-scrollbar{display:none}.card{background:#151F38;border:1px solid #1E293B;border-radius:18px;padding:20px;margin-top:16px}.price{color:#10B981;font-size:26px;font-weight:800;margin:8px 0}.badge{display:inline-block;background:rgba(16,185,129,.15);color:#34D399;font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;text-transform:uppercase;letter-spacing:1px}.cta{display:flex;align-items:center;justify-content:center;gap:10px;background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;font-weight:800;font-size:18px;padding:18px;border-radius:16px;text-decoration:none;margin-top:18px;box-shadow:0 10px 30px rgba(37,211,102,.35)}</style>'
    html = html + '</head><body><div class="wrap">'
    html = html + '<div class="gal">' + gallery + '</div>'
    html = html + '<div class="card"><span class="badge">Verified Dealer</span><h1 style="font-size:24px;margin-top:10px">' + safe_name + '</h1>'
    html = html + '<div class="price">&#8358;' + format(float(p.price or 0), ",.0f") + '</div>'
    html = html + '<p style="color:#94A3B8;line-height:1.6">' + desc + '</p>'
    html = html + '<a class="cta" href="' + wa_link + '">Chat on WhatsApp to Buy</a>'
    html = html + '<p style="color:#64748B;font-size:12px;text-align:center;margin-top:14px">Sodangi Motors - Trusted Vehicle Marketplace</p>'
    html = html + '</div></div></body></html>'
    return Response(content=html, media_type="text/html")


@router.get("/social-config")
def social_config():
    return {"google_client_id": os.getenv("GOOGLE_CLIENT_ID", "")}

@router.post("/social-login")
def social_login(payload: dict, db: Session = Depends(get_db)):
    import urllib.request as _ur
    cid = os.getenv("GOOGLE_CLIENT_ID", "")
    cred = payload.get("credential", "")
    if not cid or not cred:
        raise HTTPException(status_code=400, detail="Google sign-in not configured yet")
    try:
        with _ur.urlopen("https://oauth2.googleapis.com/tokeninfo?id_token=" + cred, timeout=10) as resp:
            info = json.loads(resp.read().decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    if info.get("aud") != cid:
        raise HTTPException(status_code=401, detail="Google token audience mismatch")
    email = (info.get("email") or "").lower()
    gname = info.get("name") or email.split("@")[0]
    if not email:
        raise HTTPException(status_code=401, detail="No email in Google token")
    Agent.__table__.create(bind=db.get_bind(), checkfirst=True)
    a = db.query(Agent).filter(Agent.email == email).first()
    if not a:
        role = "owner" if db.query(Agent).count() == 0 else "agent"
        a = Agent(full_name=gname, email=email, password_hash=_hash_pw(os.urandom(8).hex()), role=role, is_active=True)
        db.add(a)
        db.commit()
        db.refresh(a)
    return {"status": "success", "token": _make_token(a.email, a.role), "role": a.role, "full_name": a.full_name}


@router.post("/emergency-login")
def emergency_login(payload: dict, db: Session = Depends(get_db)):
    master_pw = payload.get("master_password", "")
    if master_pw != "Sodangi2026!":
        raise HTTPException(status_code=401, detail="Wrong master password")
    owner = db.query(Agent).filter(Agent.role == "owner").first()
    if not owner:
        raise HTTPException(status_code=404, detail="No owner found in database")
    return {"status": "success", "token": _make_token(owner.email, owner.role), "role": owner.role, "full_name": owner.full_name}


@router.get("/instant-owner")
def instant_owner_dashboard():
    """Bypasses login entirely - serves dashboard with token pre-loaded"""
    token = "eyJlIjogIm93bmVyQHNvZGFuZ2kuY29tIiwgInIiOiAib3duZXIiLCAidCI6IDE4MjE2NTYwMzh9.3ad592a65e148ee1fbf0c3dc281c0c2f280ab4ab54e127d58710002ea1950f82"
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Sodangi Motors - Owner Dashboard</title></head>
<body style="margin:0;padding:0">
<script>
localStorage.setItem("sodangi_token","""" + token + """");
localStorage.setItem("sodangi_role","owner");
localStorage.setItem("sodangi_name","Mohammed Kabir");
window.location.href="/api/v1/dashboard/ui";
</script>
<div style="background:#0B0F19;color:#fff;text-align:center;padding:60px;font-family:sans-serif">
<h2>Loading your dashboard...</h2>
<p>Please wait...</p>
</div>
</body></html>"""
    return Response(content=html, media_type="text/html")


@router.get("/instant-owner-v2")
def instant_owner_dashboard_v2():
    token = "eyJlIjogIm93bmVyQHNvZGFuZ2kuY29tIiwgInIiOiAib3duZXIiLCAidCI6IDE4MjE2NTY1ODh9.ebd3ec63c8127bae6a87e20e1c96fd2274c14bc1b27e09d5f68be938b30111bd"
    html = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Redirecting...</title>
<meta http-equiv="refresh" content="2;url=/api/v1/dashboard/ui?auto=""" + token + """">
</head>
<body style="margin:0;padding:0;background:#0B0F19;color:#fff;text-align:center;padding:60px;font-family:sans-serif">
<h2>Loading your dashboard...</h2>
<p>Please wait 2 seconds...</p>
<script>
try {
  localStorage.setItem("sodangi_token","""" + token + """");
  localStorage.setItem("sodangi_role","owner");
  localStorage.setItem("sodangi_name","Mohammed Kabir");
  window.location.replace("/api/v1/dashboard/ui");
} catch(e) {
  window.location.href="/api/v1/dashboard/ui?auto=""" + token + """";
}
</script>
<p style="margin-top:40px;font-size:18px">If it does not load automatically, <br><br><a href="/api/v1/dashboard/ui?auto=""" + token + """" style="color:#22C55E;text-decoration:underline;font-weight:bold;font-size:24px">TAP HERE TO ENTER</a></p>
</body></html>"""
    return Response(content=html, media_type="text/html")

@router.get("/gate")
def manual_gate():
    """V3: A single giant button that cannot be blocked by privacy settings"""
    token = "eyJlIjogIm93bmVyQHNvZGFuZ2kuY29tIiwgInIiOiAib3duZXIiLCAidCI6IDE4MjE2NTczMjJ9.9b56c1aa618158d7d64070c4892f1d81b113d65e9558322ca0d2c6b5c18a866a"
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0B0F19;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif;text-align:center;">
  <a href="/api/v1/dashboard/ui?auto=""" + token + """" style="display:block;padding:50px 30px;background:#22C55E;color:#000;font-size:28px;font-weight:900;text-decoration:none;border-radius:20px;box-shadow:0 10px 30px rgba(34,197,94,0.5);line-height:1.4;">
    🚀 TAP HERE 🚀<br><br>TO ENTER<br>DASHBOARD
  </a>
</body></html>"""
    return Response(content=html, media_type="text/html")



@router.get("/showroom/{product_id}")
def showroom_page_elite(product_id: int, db: Session = Depends(get_db)):
    import urllib.parse as _up
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        return Response(content="<h2 style='color:#fff;text-align:center;padding:60px;font-family:sans-serif'>Vehicle not available</h2>", media_type="text/html")
    
    imgs = _extract_imgs_list(p.images)
    hero = imgs[0] if imgs else "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80"
    price_txt = format(float(p.price or 0), ",.0f")
    name = str(p.name).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "'")
    desc = (p.description or "This premium vehicle has been mechanic-inspected and comes with verified documents. Ready for immediate pickup.")
    page_url = "https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/" + str(product_id)
    
    wa_text = _up.quote(f"Salam! I am on the Sodangi Motors showroom looking at the {name} (NGN {price_txt}). I am ready to buy/verify papers. Please assist me immediately.")
    wa_link = f"https://wa.me/2349079437745?text={wa_text}"
    
    gallery = ""
    for u in imgs:
        gallery += f'<img src="{u}" loading="lazy" alt="{name}">'
    if not gallery:
        gallery = f'<img src="{hero}" loading="lazy" alt="{name}">'

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>{name} | Sodangi Motors Premium</title>
<meta property="og:title" content="{name} - NGN {price_txt} | Sodangi Motors">
<meta property="og:description" content="Verified papers, mechanic inspected. Ready for immediate pickup.">
<meta property="og:image" content="{hero}">
<meta property="og:type" content="product">
<meta name="twitter:card" content="summary_large_image">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',system-ui,sans-serif}}
body{{background:#0A0F1C;color:#F8FAFC;padding-bottom:140px;-webkit-font-smoothing:antialiased}}
.gal{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:0;scrollbar-width:none;background:#000}}
.gal::-webkit-scrollbar{{display:none}}
.gal img{{scroll-snap-align:center;flex-shrink:0;width:100%;height:320px;object-fit:cover}}
.wrap{{max-width:600px;margin:0 auto;padding:0 16px}}
.price-tag{{display:inline-block;background:linear-gradient(135deg,#10B981,#059669);color:#fff;font-size:28px;font-weight:900;padding:12px 24px;border-radius:14px;margin:16px 0;box-shadow:0 8px 24px rgba(16,185,129,0.4);letter-spacing:-0.5px}}
h1{{font-size:26px;font-weight:900;margin-bottom:8px;line-height:1.2}}
.desc{{color:#94A3B8;line-height:1.6;font-size:15px;margin-bottom:24px}}
.trust-row{{display:flex;justify-content:space-between;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:16px 10px;margin-bottom:24px;gap:8px}}
.trust-badge{{flex:1;text-align:center;font-size:11px;font-weight:700;color:#10B981;line-height:1.3}}
.trust-badge span{{display:block;font-size:20px;margin-bottom:4px}}
.dealer-card{{background:#151F38;border:1px solid #1E293B;border-radius:20px;padding:20px;display:flex;align-items:center;gap:14px;margin-bottom:24px}}
.dealer-card img{{width:50px;height:50px;border-radius:50%;border:2px solid #10B981}}
.dealer-info h3{{font-size:16px;font-weight:800;margin-bottom:2px}}
.dealer-info p{{font-size:12px;color:#94A3B8}}
.sticky-cta{{position:fixed;bottom:0;left:0;right:0;background:rgba(10,15,28,0.95);backdrop-filter:blur(12px);padding:16px;border-top:1px solid #1E293B;z-index:100}}
.cta-inner{{max-width:600px;margin:0 auto}}
.btn-main{{display:flex;align-items:center;justify-content:center;gap:10px;background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;font-size:18px;font-weight:900;padding:18px;border-radius:16px;text-decoration:none;box-shadow:0 10px 30px rgba(37,211,102,0.4);animation:pulse 2s infinite;width:100%}}
@keyframes pulse{{0%,100%{{transform:scale(1);box-shadow:0 10px 30px rgba(37,211,102,0.4)}}50%{{transform:scale(1.02);box-shadow:0 15px 40px rgba(37,211,102,0.6)}}}}
.secure-text{{text-align:center;font-size:11px;color:#10B981;font-weight:700;margin-top:10px;letter-spacing:0.5px}}
.badge-verified{{position:absolute;top:16px;left:16px;background:rgba(10,15,28,0.8);backdrop-filter:blur(8px);color:#10B981;font-size:11px;font-weight:800;padding:6px 12px;border-radius:999px;border:1px solid rgba(16,185,129,0.3);z-index:10}}
</style></head>
<body>
<div style="position:relative">
  <div class="badge-verified">✅ SODANGI VERIFIED</div>
  <div class="gal">{gallery}</div>
</div>
<div class="wrap">
  <h1>{name}</h1>
  <div class="price-tag">&#8358; {price_txt}</div>
  
  <div class="trust-row">
    <div class="trust-badge"><span>📄</span>Papers Verified</div>
    <div class="trust-badge"><span>🔧</span>Mechanic Inspected</div>
    <div class="trust-badge"><span>🔒</span>Secure Payment</div>
  </div>

  <p class="desc">{desc}</p>

  <div class="dealer-card">
    <img src="https://ui-avatars.com/api/?name=Sodangi+Motors&background=10B981&color=fff&bold=true" alt="Dealer">
    <div class="dealer-info">
      <h3>Sodangi Motors Premium</h3>
      <p>Verified Dealership • Responds in 2 mins</p>
    </div>
  </div>
</div>

<div class="sticky-cta">
  <div class="cta-inner">
    <a href="{wa_link}" target="_blank" rel="noopener" class="btn-main">💬 Verify & Buy on WhatsApp</a>
    <div class="secure-text">🔒 100% SECURE TRANSACTION GUARANTEED BY SODANGI MOTORS</div>
  </div>
</div>
</body></html>"""
    return Response(content=html, media_type="text/html")
@router.put("/products/{product_id}")
def update_product_v4(product_id: int, req: ProductReq, request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if me.get("r") != "owner":
        ag = db.query(Agent).filter(Agent.email == me["e"]).first()
        ok = False
        if ag:
            link = db.query(ProductAgent).filter(ProductAgent.product_id == product_id, ProductAgent.agent_id == ag.id).first()
            ok = link is not None
        if not ok:
            raise HTTPException(status_code=403, detail="You can only edit your own vehicles")
    p.name = req.name
    p.price = req.price
    if req.description is not None:
        p.description = req.description
    if req.image_url:
        p.images = req.image_url if req.image_url.startswith("[") else json.dumps([req.image_url])
    db.commit()
    return {"status": "updated", "id": product_id}

@router.get("/v4-dashboard")
def fresh_dashboard_v5():
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
      var r = await fetch(API + "/upload-media", {method:"POST", headers:{"Authorization":"Bearer "+TOKEN}, body:fd});
      if(!r.ok) throw new Error("Upload failed");
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
    await api("/products/upload","POST",{name:n,price:p,image_url:JSON.stringify(allMedia),description:document.getElementById("pDesc").value,stock:1});
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
    return Response(content=html, media_type="text/html")


@router.get("/bot-diagnose")
def bot_diagnose():
    import os, traceback
    out = {}
    api_key = os.getenv("OPENAI_API_KEY", "NOT SET")
    out["api_key_preview"] = api_key[:15] + "..." if len(api_key) > 15 else api_key
    
    try:
        import openai
        out["openai_installed"] = True
        try:
            out["openai_version"] = openai.__version__
        except:
            pass
    except Exception as e:
        out["openai_installed"] = False
        out["openai_error"] = str(e)
        return out

    try:
        client = openai.OpenAI(api_key=api_key)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        out["ai_test"] = "SUCCESS: " + res.choices[0].message.content
    except Exception as e:
        out["ai_test"] = "FAILED"
        out["ai_error"] = str(e)
        
    return out
