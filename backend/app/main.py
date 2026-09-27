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


@app.get("/api/v1/dashboard/showroom/{product_id}")
def showroom_direct_hardcoded(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return HTMLResponse(content="<h2 style='color:#fff;text-align:center;padding:40px;font-family:sans-serif'>Vehicle ID " + str(product_id) + " not found in database.</h2>", status_code=404)
        
        imgs = []
        if p.images:
            try:
                parsed = _json.loads(p.images) if isinstance(p.images, str) else p.images
                if isinstance(parsed, list): imgs = parsed
            except: imgs = [p.images]
        
        hero = imgs[0] if imgs else "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80"
        price_txt = f"{float(p.price or 0):,.0f}"
        name = str(p.name or "Unknown Car").replace('"', "'").replace('<', '&lt;')
        desc = str(p.description or "Premium vehicle available now.").replace('<', '&lt;')
        
        gallery = ""
        for u in imgs:
            if str(u).endswith((".mp4", ".webm", ".mov")):
                gallery += f'<video src="{u}" controls playsinline style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0"></video>'
            else:
                gallery += f'<img src="{u}" style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0" loading="lazy">'
        if not gallery: 
            gallery = f'<img src="{hero}" style="width:100%;height:320px;object-fit:cover">'

        html = f'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>
        <style>body{{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding-bottom:100px}}.gal{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000}}.wrap{{max-width:600px;margin:0 auto;padding:20px}}.price{{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}}.badge{{background:rgba(16,185,129,0.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}}.cta{{position:fixed;bottom:0;left:0;right:0;padding:20px;background:#0A0F1C;border-top:1px solid #333;text-align:center}}.btn{{display:block;background:#25D366;color:#fff;padding:16px;border-radius:12px;text-decoration:none;font-weight:900;font-size:18px;box-shadow:0 10px 20px rgba(37,211,102,0.3)}}</style>
        </head><body><div class="gal">{gallery}</div><div class="wrap"><span class="badge">✅ VERIFIED SELLER</span><h1 style="margin-top:8px">{name}</h1><div class="price">&#8358; {price_txt}</div><p style="color:#94A3B8;line-height:1.6;margin-top:16px">{desc}</p></div>
        <div class="cta"><a href="https://wa.me/2349079437745?text=Salam! I am looking at the {name} (NGN {price_txt})" target="_blank" class="btn">💬 Verify & Buy on WhatsApp</a></div></body></html>'''
        
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content="<h2 style='color:#fff;text-align:center;padding:40px;font-family:sans-serif'>Server Error: " + str(e) + "</h2>", status_code=500)
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
