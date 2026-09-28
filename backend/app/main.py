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
@app.get("/api/v1/dashboard/showroom-elite/{product_id}")
def ultimate_showroom_247(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return HTMLResponse("<html><body style='background:#0A0F1C;color:#fff;font-family:sans-serif;text-align:center;padding:50px'><h1>Vehicle Not Found</h1><a href='/api/v1/dashboard/market' style='color:#10B981'>Browse All Cars</a>
<script>
function copyCaption(n, p) {
  var text = "🚗 " + n + " - ₦" + p + "\n✅ Verified Seller | Sodangi Motors\n👉 " + location.href;
  navigator.clipboard.writeText(text).then(function() {
    alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB');
  });
}
</script>

</body></html>")
        
        imgs = []
        try:
            if isinstance(p.images, str):
                if p.images.strip().startswith('['): imgs = _json.loads(p.images)
                elif p.images.strip(): imgs = [p.images]
        except: imgs = []
            
        # FALLBACK: If DB has no photos, inject 3 beautiful fallback photos
        if not imgs:
            imgs = [
                "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1200&q=80"
            ]

        name = str(p.name or "Vehicle").replace('"',"'").replace('<', '&lt;')
        price = f"{float(p.price or 0):,.0f}"
        
        gallery = ""
        # Safely build the caption button outside the f-string to avoid crashes
        safe_name = name.replace("'", "\\'")
        caption_btn = f'<button onclick="copyCaption(\'{safe_name}\', \'{price}\')" style="background:#3B82F6;color:#fff;padding:12px;border-radius:12px;border:none;font-weight:800;width:100%;text-align:center;margin-bottom:8px">📣 Copy Ad Caption</button>'

        for u in imgs:
            if ".mp4" in str(u) or ".webm" in str(u):
                gallery += f'<video src="{u}" controls playsinline style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0;background:#000"></video>'
            else:
                gallery += f'<img src="{u}" style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0" loading="lazy">'

        html = f'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>
        <style>body{{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding-bottom:240px}}.gal{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000;scrollbar-width:none}}.gal::-webkit-scrollbar{{display:none}}.wrap{{max-width:600px;margin:0 auto;padding:20px}}.price{{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}}.badge{{background:rgba(16,185,129,0.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}}.cta{{position:fixed;bottom:0;left:0;right:0;padding:12px;background:#0A0F1C;border-top:1px solid #333;display:flex;flex-direction:column;gap:8px;z-index:100}}.btn-wa{{display:block;background:#25D366;color:#fff;padding:14px;border-radius:12px;text-decoration:none;font-weight:900;font-size:15px;text-align:center}}.btn-call{{display:block;background:rgba(245,158,11,0.1);color:#F59E0B;padding:12px;border-radius:12px;text-decoration:none;font-weight:800;font-size:14px;border:1px solid #F59E0B;text-align:center}}.btn-agent{{display:block;background:#3B82F6;color:#fff;padding:12px;border-radius:12px;text-decoration:none;font-weight:800;font-size:14px;text-align:center}}</style>
        </head><body><div class="gal">{gallery}</div><div class="wrap"><span class="badge">✅ VERIFIED SELLER</span><h1 style="margin-top:8px">{name}</h1><div class="price">₦ {price}</div></div>
        <div class="cta">
          {caption_btn}
          <a href="https://wa.me/2348142969979?text=Salam! I am looking at the {name}" target="_blank" class="btn-wa">💬 WhatsApp Seller</a>
          <button onclick="navigator.clipboard.writeText('🚗 {name} - ₦{price}\n✅ Verified Seller | Sodangi Motors\n👉 ' + location.href).then(function(){alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB')});" style="background:#3B82F6;color:#fff;padding:12px;border-radius:12px;border:none;font-weight:800;width:100%;text-align:center">📣 Copy Ad Caption</button>
        <a href="tel:+2348142969979" class="btn-call">📞 Call Inspection <span style="font-size:12px;opacity:0.8">(₦5,000 Fee)</span></a>
          <a href="/api/v1/dashboard/market" class="btn-agent">🏪 Back to Marketplace</a>
        </div>
<script>
function copyCaption(n, p) {
  var text = "🚗 " + n + " - ₦" + p + "\n✅ Verified Seller | Sodangi Motors\n👉 " + location.href;
  navigator.clipboard.writeText(text).then(function() {
    alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB');
  });
}
</script>

</body></html>'''
        
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content=f"<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Server Error: {e}</h1>", status_code=500)
    finally:
        db.close()


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
