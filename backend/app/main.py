import os
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# CATCHES ALL 500 ERRORS AND PRINTS THE TRACEBACK
@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc), "trace": traceback.format_exc()})

@app.get("/", include_in_schema=False)
def root_market():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/dashboard/market")

try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    trace = traceback.format_exc()
    @app.get("/api/v1/dashboard/health")
    @app.get("/api/v1/dashboard/ping")
    def router_crash():
        return {"status": "ROUTER_IMPORT_CRASH", "error": str(e), "trace": trace}


@app.get("/api/v1/dashboard/debug-first-car")
def debug_first_car_direct():
    from app.core.database import SessionLocal
    from app.models.product import Product
    db = SessionLocal()
    try:
        p = db.query(Product).order_by(Product.id.desc()).first()
        if p:
            return {"id": p.id, "name": p.name, "url": "/api/v1/dashboard/showroom/" + str(p.id)}
        return {"error": "No cars in database!"}
    except Exception as e:
        return {"error": "DB Query failed: " + str(e)}
    finally:
        db.close()



@app.get("/api/v1/dashboard/debug-car-15")
def debug_car_15():
    from app.core.database import SessionLocal
    from app.models.product import Product
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == 15).first()
        if not p: return {"error": "Car 15 not found"}
        return {
            "id": p.id,
            "name": p.name,
            "images_raw": p.images,
            "images_type": str(type(p.images)),
            "is_json_string": isinstance(p.images, str) and p.images.startswith('[')
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@app.post("/api/v1/dashboard/force-image-15")
def force_image_15():
    from app.core.database import SessionLocal
    from app.models.product import Product
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == 15).first()
        if not p: return {"error": "Car 15 not found"}
        
        # 3 High quality car photos
        photos = [
            "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1494905998402-395d579af36f?auto=format&fit=crop&w=1000&q=80"
        ]
        p.images = _json.dumps(photos)
        db.commit()
        return {"status": "INJECTED", "count": len(photos)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()




@app.get("/api/v1/dashboard/showroom/{product_id}")

@app.get("/api/v1/dashboard/stats")
def ceo_stats_endpoint():
    from app.core.database import SessionLocal
    from app.models.product import Product
    db = SessionLocal()
    try:
        prods = db.query(Product).all()
        total = sum(float(p.price or 0) for p in prods)
        cats = {"Luxury":0, "SUVs":0, "Sedans":0, "Trucks":0}
        for p in prods:
            n = str(p.name).lower()
            if any(x in n for x in ["lexus","benz","bmw","porsche","range","gtr"]): cats["Luxury"]+=1
            elif any(x in n for x in ["suv","highlander","rx3","ml3","pajero","escalade","venza"]): cats["SUVs"]+=1
            elif any(x in n for x in ["truck","bus","van","sienna","trailer"]): cats["Trucks"]+=1
            else: cats["Sedans"]+=1
        return {"total_value": total, "total_cars": len(prods), "categories": cats, "commission": total*0.05}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@app.get("/api/v1/dashboard/alert-save")
def alert_save(phone: str, budget: int, car: str = ""):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS buyer_alerts(id SERIAL PRIMARY KEY, phone TEXT, budget BIGINT, car TEXT, created_at TIMESTAMP DEFAULT NOW())"))
            conn.commit()
            conn.execute(text("INSERT INTO buyer_alerts(phone,budget,car) VALUES(:p,:b,:c)"), {"p":phone,"b":budget,"c":car})
            conn.commit()
        return {"status":"saved"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/dashboard/alert-match")
def alert_match(price: int = 0):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT phone, budget, car FROM buyer_alerts WHERE budget >= :p"), {"p": price}).fetchall()
        return {"matches": [{"phone": r[0], "budget": r[1], "car": r[2]} for r in rows]}
    except Exception as e:
        return {"matches": [], "error": str(e)}


@app.get("/api/v1/dashboard/showroom/{product_id}")
@app.get("/api/v1/dashboard/showroom-elite/{product_id}")
def ultimate_showroom_247(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    from urllib.parse import quote as _q
    import json as _json
    T = r'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__NAME__ | Sodangi Motors</title>
<style>
body{margin:0;background:#0A0F1C;color:#fff;font-family:system-ui,sans-serif;padding-bottom:250px}
.gal{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000;scrollbar-width:none}
.gal::-webkit-scrollbar{display:none}
.gal img,.gal video{width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0}
.wrap{max-width:600px;margin:0 auto;padding:20px}
.badge{background:rgba(16,185,129,.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}
.price{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}
.cta{position:fixed;bottom:0;left:0;right:0;padding:12px;background:#0A0F1C;border-top:1px solid #333;display:flex;flex-direction:column;gap:8px;z-index:100}
.b{display:block;padding:14px;border-radius:12px;text-decoration:none;font-weight:900;font-size:15px;text-align:center;border:none;width:100%;cursor:pointer}
.bcap{background:#3B82F6;color:#fff}
.bwa{background:#25D366;color:#fff}
.bcall{background:rgba(245,158,11,.1);color:#F59E0B;border:1px solid #F59E0B}
.bmkt{background:#1E293B;color:#93C5FD;border:1px solid #334155}
</style></head><body>
<div class="gal">__GALLERY__</div>
<div class="wrap">
<span class="badge">✅ VERIFIED SELLER</span>
<h1 style="margin-top:8px">__NAME__</h1>
<div class="price">₦ __PRICE__</div>
</div>
<div class="cta">
<button class="b bcap" onclick="copyCap()">📣 Copy Ad Caption</button>
<a class="b bwa" href="__WA__" target="_blank" rel="noopener">💬 WhatsApp Seller</a>
<a class="b bcall" href="tel:+2348142969979">📞 Call Inspection (₦5,000 Fee)</a>
<a class="b bmkt" href="/api/v1/dashboard/market">🏪 Checkout Full Showroom</a>
</div>
<script>
function copyCap(){
  var lines=[document.title, document.querySelector(".price").innerText, "✅ Verified Seller | Sodangi Motors", "👉 " + location.href];
  var t=lines.join(String.fromCharCode(10));
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(t).then(function(){alert("📣 Caption copied! Paste on WhatsApp Status / IG / FB");},function(){prompt("Copy this caption:",t);});
  }else{prompt("Copy this caption:",t);}
}
</script>
</body></html>'''
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return HTMLResponse("<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Car " + str(product_id) + " not found. <a style='color:#10B981' href='/api/v1/dashboard/market'>Browse all cars</a></h1>", status_code=404)
        imgs = []
        try:
            if isinstance(p.images, str):
                s = p.images.strip()
                if s.startswith("["):
                    parsed = _json.loads(s)
                    imgs = parsed if isinstance(parsed, list) else []
                elif s:
                    imgs = [s]
        except Exception:
            imgs = []
        if not imgs:
            imgs = ["https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80",
                    "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
                    "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1200&q=80"]
        name = str(p.name or "Vehicle").replace("&", "&amp;").replace("<", "&lt;").replace('"', "'")
        price = format(float(p.price or 0), ",.0f")
        gal = ""
        for u in imgs:
            su = str(u)
            if su.endswith(".mp4") or su.endswith(".webm") or su.endswith(".mov"):
                gal += '<video src="' + su + '" controls playsinline></video>'
            else:
                gal += '<img src="' + su + '" loading="lazy" alt="">'
        wa = "https://wa.me/2348142969979?text=" + _q("Salam! I am looking at the " + name + " (NGN " + price + ") on Sodangi Motors")
        out = T.replace("__GALLERY__", gal).replace("__NAME__", name).replace("__PRICE__", price).replace("__WA__", wa)
        return HTMLResponse(content=out)
    except Exception as e:
        return HTMLResponse(content="<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Server Error: " + str(e) + "</h1>", status_code=500)
    finally:
        db.close()

# FORCE DEPLOY 1790639648.4990754
