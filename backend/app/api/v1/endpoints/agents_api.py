


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





DASHBOARD_HTML = """<html><body>Stripped for memory</body></html>"""








@router.get("/owner-auto", response_class=HTMLResponse)


def owner_auto_login():


    import base64, hmac, hashlib, json, time


    payload = base64.urlsafe_b64encode(json.dumps({"e": "owner@sodangi.com", "r": "owner", "t": int(time.time()) + 315360000}).encode()).decode()


    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


    token = payload + "." + sig


    force_js = """<html><body>Stripped for memory</body></html>"""


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


        cols_query = """<html><body>Stripped for memory</body></html>"""Bypasses login entirely - serves dashboard with token pre-loaded"""<html><body>Stripped for memory</body></html>"""" + token + """<html><body>Stripped for memory</body></html>""" + token + """<html><body>Stripped for memory</body></html>""" + token + """<html><body>Stripped for memory</body></html>"""
    return Response(content=html, media_type="text/html")





@router.get("/env-check")
def env_check():
    import os
    return {
        "status": "ALIVE",
        "has_whatsapp_token": bool(os.getenv("WHATSAPP_TOKEN")),
        "has_phone_id": bool(os.getenv("WHATSAPP_PHONE_ID")),
        "phone_id_value": os.getenv("WHATSAPP_PHONE_ID", "NOT SET")
    }
