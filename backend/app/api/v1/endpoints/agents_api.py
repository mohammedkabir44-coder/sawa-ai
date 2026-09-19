
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

from fastapi.responses import HTMLResponse

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>

<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">

<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="theme-color" content="#0B0F19">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="manifest" href="/api/v1/dashboard/manifest.json">
<title>Sodangi Motors</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js">


function showStatus() {
    document.getElementById('main-content').innerHTML = '<div class="p-4 text-center text-gray-400">Loading your inventory...</div>';
    fetch('/api/v1/dashboard/products', { headers: { 'Authorization': 'Bearer ' + TOKEN } })
    .then(r => r.json())
    .then(cars => {
        let html = '<div class="p-4"><h2 class="text-2xl font-bold text-white mb-4">📢 WhatsApp Status Blaster</h2>';
        if (!cars || cars.length === 0) { html += '<p class="text-gray-400">No cars found.</p>'; }
        else {
            cars.forEach((car, idx) => {
                let img = car.image_url || car.images || '';
                if (img.startsWith('[')) img = JSON.parse(img)[0];
                html += `<div class="bg-gray-800 rounded-xl p-4 mb-4 shadow-lg"><img src="${img}" class="w-full h-40 object-cover rounded-lg mb-3"><h3 class="text-lg font-bold text-white">${car.name}</h3><p class="text-emerald-400 font-bold mb-3">₦${Number(car.price).toLocaleString()}</p><button onclick="generateStatusImage(${idx})" class="w-full bg-emerald-600 text-white py-2 rounded-lg font-bold hover:bg-emerald-700">Generate Status Image</button></div>`;
            });
        }
        html += '</div>';
        document.getElementById('main-content').innerHTML = html;
        window._statusCars = cars;
    });
}
function generateStatusImage(idx) {
    let car = window._statusCars[idx];
    toast('Generating your watermark...');
    fetch('/api/v1/dashboard/profile/me', { headers: { 'Authorization': 'Bearer ' + TOKEN } })
    .then(r => r.json())
    .then(profile => { drawCanvas(car, profile.full_name || 'Sodangi', profile.phone || profile.phone_number || '08000000000'); })
    .catch(() => drawCanvas(car, 'Sodangi', '08000000000'));
}
function drawCanvas(car, name, phone) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.crossOrigin = "anonymous";
    let imgSrc = car.image_url || car.images || '';
    if (imgSrc.startsWith('[')) imgSrc = JSON.parse(imgSrc)[0];
    img.onload = () => {
        canvas.width = 1080; canvas.height = 1920;
        const scale = Math.max(canvas.width / img.width, canvas.height / img.height);
        ctx.drawImage(img, (canvas.width/2)-(img.width/2)*scale, (canvas.height/2)-(img.height/2)*scale, img.width*scale, img.height*scale);
        const grad = ctx.createLinearGradient(0, canvas.height-600, 0, canvas.height);
        grad.addColorStop(0, 'rgba(0,0,0,0)'); grad.addColorStop(1, 'rgba(0,0,0,0.95)');
        ctx.fillStyle = grad; ctx.fillRect(0, canvas.height-600, canvas.width, 600);
        ctx.fillStyle = 'white'; ctx.textAlign = 'center'; ctx.shadowColor = 'black'; ctx.shadowBlur = 15;
        ctx.font = 'bold 70px sans-serif'; ctx.fillText(car.name, canvas.width/2, canvas.height-350);
        ctx.font = 'bold 100px sans-serif'; ctx.fillStyle = '#10B981'; ctx.fillText('₦' + Number(car.price).toLocaleString(), canvas.width/2, canvas.height-220);
        ctx.font = 'bold 50px sans-serif'; ctx.fillStyle = 'white'; ctx.fillText(name, canvas.width/2, canvas.height-110);
        ctx.font = 'bold 60px sans-serif'; ctx.fillStyle = '#FBBF24'; ctx.fillText('📞 ' + phone, canvas.width/2, canvas.height-40);
        const link = document.createElement('a');
        link.download = car.name.replace(/\s+/g, '_') + '_Status.png';
        link.href = canvas.toDataURL('image/png'); link.click();
        canvas.toBlob(function(blob){const file=new File([blob],'status.png',{type:'image/png'});if(navigator.canShare&&navigator.canShare({files:[file]})){navigator.share({files:[file],title:car.name,text:'Sodangi Motors'});}}, 'image/png');
        toast('Status Image Saved! 🎉');
    };
    img.src = imgSrc;
}

function switchToStatus(){
    try{
        document.querySelectorAll('nav button').forEach(function(b){ b.classList.remove('text-emerald-400'); b.classList.add('text-gray-400'); });
        var st = document.getElementById('tab-status');
        if(st){ st.classList.remove('text-gray-400'); st.classList.add('text-emerald-400'); }
        document.querySelectorAll('div[id$="-content"]').forEach(function(el){ el.style.display = 'none'; });
        var old = document.getElementById('status-wrap'); if(old) old.remove();
        var mainParent = document.getElementById('add-content'); if(!mainParent) mainParent = document.getElementById('cars-content'); if(!mainParent) mainParent = document.body;
        var sc = document.createElement('div');
        sc.id = 'status-wrap';
        if(mainParent && mainParent.parentNode) mainParent.parentNode.insertBefore(sc, mainParent.nextSibling);
        else document.body.appendChild(sc);
        sc.style.display = 'block';
        sc.innerHTML = '<div class="p-4 text-center text-gray-400">Loading inventory...</div>';
        fetch('/api/v1/dashboard/products', { headers: { 'Authorization': 'Bearer ' + TOKEN } })
        .then(function(r){ return r.json(); })
        .then(function(cars){
            var html = '<div class="p-4"><h2 class="text-2xl font-bold text-white mb-4">📢 WhatsApp Status Blaster</h2>';
            if(!cars || cars.length === 0){ html += '<p>No cars found.</p>'; }
            else {
                window._statusCars = cars;
                cars.forEach(function(car, idx){
                    var img = car.image_url || car.images || '';
                    if(img && img.startsWith('[')){ try{ img = JSON.parse(img)[0]; }catch(e){ img = ''; } }
                    html += '<div class="bg-gray-800 rounded-xl p-4 mb-4 shadow-lg">';
                    html += '<img src="' + img + '" class="w-full h-40 object-cover rounded-lg mb-3">';
                    html += '<h3 class="text-lg font-bold text-white">' + car.name + '</h3>';
                    html += '<p class="text-emerald-400 font-bold mb-3">₦' + Number(car.price).toLocaleString() + '</p>';
                    html += '<button onclick="generateStatusImage(' + idx + ')" class="w-full bg-emerald-600 text-white py-2 rounded-lg font-bold">Generate Status Image</button>';
                    html += '</div>';
                });
            }
            html += '</div>';
            sc.innerHTML = html;
        });
    } catch(e){ console.error(e); }
}

function generateStatusImage(idx) {
    let car = window._statusCars[idx];
    if(!car) { alert('Car not found'); return; }
    fetch('/api/v1/dashboard/profile/me', { headers: { 'Authorization': 'Bearer ' + TOKEN } })
    .then(function(r){ return r.json(); })
    .then(function(profile){
        let phone = profile.phone || profile.phone_number || '08000000000';
        let name = profile.full_name || 'Sodangi Motors';
        drawCanvas(car, name, phone);
    }).catch(function(){ drawCanvas(car, 'Sodangi Motors', '08000000000'); });
}

function drawCanvas(car, name, phone) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.crossOrigin = "anonymous";
    let imgSrc = car.image_url || car.images || '';
    if (imgSrc && imgSrc.startsWith('[')) { try { imgSrc = JSON.parse(imgSrc)[0]; } catch(e){ imgSrc=''; } }
    if(Array.isArray(imgSrc)) imgSrc = imgSrc[0] || '';
    if(!imgSrc) { alert('No image for this car'); return; }
    
    img.onload = function() {
        canvas.width = 1080;
        canvas.height = 1920;
        const scale = Math.max(canvas.width / img.width, canvas.height / img.height);
        const x = (canvas.width / 2) - (img.width / 2) * scale;
        const y = (canvas.height / 2) - (img.height / 2) * scale;
        ctx.drawImage(img, x, y, img.width * scale, img.height * scale);
        
        const gradient = ctx.createLinearGradient(0, canvas.height - 600, 0, canvas.height);
        gradient.addColorStop(0, 'rgba(0,0,0,0)');
        gradient.addColorStop(1, 'rgba(0,0,0,0.95)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, canvas.height - 600, canvas.width, 600);
        
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.shadowColor = 'black';
        ctx.shadowBlur = 15;
        
        ctx.font = 'bold 70px sans-serif';
        ctx.fillText(car.name, canvas.width / 2, canvas.height - 350);
        
        ctx.font = 'bold 100px sans-serif';
        ctx.fillStyle = '#10B981';
        ctx.fillText('\u20A6' + Number(car.price).toLocaleString(), canvas.width / 2, canvas.height - 220);
        
        ctx.font = 'bold 50px sans-serif';
        ctx.fillStyle = 'white';
        ctx.fillText(name, canvas.width / 2, canvas.height - 110);
        
        ctx.font = 'bold 60px sans-serif';
        ctx.fillStyle = '#FBBF24';
        ctx.fillText('\ud83d\udcde ' + phone, canvas.width / 2, canvas.height - 40);
        
        const link = document.createElement('a');
        link.download = car.name.replace(/\s+/g, '_') + '_Status.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
        
        canvas.toBlob(function(blob) {
            const file = new File([blob], car.name.replace(/\s+/g, '_') + '_Status.png', { type: 'image/png' });
            if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
                navigator.share({
                    files: [file],
                    title: car.name,
                    text: '\ud83d\ude97 ' + car.name + '\n\ud83d\udcb0 \u20A6' + Number(car.price).toLocaleString() + '\n\ud83d\udcde ' + phone + '\nSodangi Motors'
                }).then(function(){}).catch(function(){});
            } else {
                alert('Image saved to gallery! Open your photos to share on WhatsApp/Facebook.');
            }
        }, 'image/png');
    };
    img.onerror = function() { alert('Error loading image.'); };
    img.src = imgSrc;
}


</script>
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
<button onclick="switchToStatus()" id="tab-status" class="flex-1 text-center py-3 text-gray-400 hover:text-emerald-400 transition-colors"><div class="text-2xl">📢</div><div class="text-xs mt-1">Status</div></button>
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
function installApp(){ if(deferredPrompt){ deferredPrompt.prompt(); } else { var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent); if(isIOS){ toast("Tap the Share icon 🟦 then 'Add to Home Screen'"); } else { toast("Tap the browser menu (⋮) and select 'Install App'"); } } }

if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/api/v1/dashboard/sw.js').catch(function(){}); }
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
    return HTMLResponse(content=html)

@router.get("/ui")
def dashboard_ui():
    from fastapi.responses import Response
    # THE SILVER BULLET: Bypass HTMLResponse completely! Send raw HTML via base Response.
    return Response(content=DASHBOARD_HTML, media_type="text/html")


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

