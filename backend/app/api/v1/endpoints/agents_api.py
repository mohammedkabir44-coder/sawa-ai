
import json, hmac, hashlib, base64, time, os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Text
from app.core.database import get_db, Base
from app.models.product import Product

router = APIRouter(prefix="/dashboard", tags=["Sodangi Agents"])
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
