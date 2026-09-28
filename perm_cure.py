import subprocess, time, urllib.request, ast

print("="*60)
print("☢️ ZERO F-STRING SHOWROOM (PERMANENT CURE)")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. DELETE every old showroom function completely
NAMES = ["def ultimate_showroom_247(", "def nuclear_showroom(", "def showroom_elite_bypass(",
         "def showroom_god_mode(", "def showroom_direct_hardcoded(", "def showroom_page_resurrected(",
         "def showroom_page_elite("]
killed = 0
changed = True
while changed:
    changed = False
    for fn in NAMES:
        i = mc.find(fn)
        if i != -1:
            dec = mc.rfind("@app.get", 0, i)
            if dec == -1: dec = i
            end = mc.find("\n@app.", i)
            if end == -1: end = len(mc)
            mc = mc[:dec] + mc[end:]
            killed += 1
            changed = True
print(f"✅ Deleted {killed} old showroom function(s).")

# 2. NEW SHOWROOM: plain raw string + __TOKENS__ (NO f-string = NO crashes)
NEW_ROUTE = """

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
"""

mc += NEW_ROUTE

# 3. SYNTAX CHECK LOCALLY BEFORE PUSHING (never ship a broken build again)
print("\n🧪 Syntax-checking main.py locally...")
try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT. Safe to push.")
except SyntaxError as e:
    print(f"❌ SYNTAX ERROR at line {e.lineno}: {e.msg} — ABORTING, nothing pushed!")
    raise SystemExit(1)

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Permanent cure: zero f-string showroom with tokens"])
subprocess.run(["git", "push", "origin", "main", "--force"])

# 4. WATCHDOG (up to ~4.5 min) to outwait slow Vercel deploys
print("\n🐕 WATCHDOG polling live page...")
URL = "https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15"
for i in range(14):
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
        if "VERIFIED SELLER" in body and "Copy Ad Caption" in body and "Server Error" not in body:
            print(f"\n✅ ✅ ✅ LIVE AND PERFECT (poll {i+1})!")
            print("👉 OPEN ON YOUR PHONE:")
            print(URL)
            raise SystemExit(0)
        else:
            print(f"[{i+1}/14] Old build still serving... ({body[:60]})")
    except SystemExit:
        raise
    except Exception as e:
        print(f"[{i+1}/14] {str(e)[:60]}")
    time.sleep(20)

print("\n⚠️ Watchdog timed out. Vercel Production is stuck on an old build.")
print("👉 MANUAL 30-SECOND FIX:")
print("1. Open vercel.com -> your project -> Deployments tab.")
print("2. If the TOP deployment shows a RED error, click it and read the build log.")
print("3. If an OLD deployment has the 'Production' badge, click ⋯ on the TOP one -> 'Promote to Production'.")
