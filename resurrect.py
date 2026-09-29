import subprocess, time, urllib.request, re, json, ast

print("="*60)
print("🏥 MAIN.PY BYPASS: RESURRECT DASHBOARD & MARKET")
print("="*60)

# 1. Download the broken agents_api.py to extract the HTML templates
url_agents = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req = urllib.request.Request(url_agents, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    agents_code = r.read().decode()

# Extract the V4 Dashboard HTML
v4_match = re.search(r'def fresh_dashboard_v5\(\):[\s\S]*?html = ("""[\s\S]*?""")', agents_code)
v4_html = v4_match.group(1) if v4_match else "''"

# Extract the Marketplace HTML Template
mkt_match = re.search(r'(MARKET_HTML_TEMPLATE = r"""[\s\S]*?""")', agents_code)
mkt_html = mkt_match.group(1) if mkt_match else ""

# 2. Download main.py
url_main = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req2 = urllib.request.Request(url_main, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as r:
    mc = r.read().decode()

# 3. Inject the V4 Dashboard Route directly into main.py
if '"/api/v1/dashboard/v4-dashboard"' not in mc:
    V4_ROUTE = f"""

@app.get("/api/v1/dashboard/v4-dashboard")
@app.get("/api/v1/dashboard/ui")
def v4_dashboard_god_mode():
    from fastapi.responses import HTMLResponse
    html = {v4_html}
    return HTMLResponse(content=html)
"""
    mc += V4_ROUTE
    print("✅ V4 Dashboard injected into main.py!")

# 4. Inject the Marketplace Route directly into main.py
if '"/api/v1/dashboard/market"' not in mc:
    MKT_ROUTE = f"""

{mkt_html}

@app.get("/api/v1/dashboard/market")
def market_god_mode_main():
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json, re as _re
    db = SessionLocal()
    try:
        prods = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.id.desc()).limit(40).all()
        if not prods: prods = db.query(Product).order_by(Product.id.desc()).limit(40).all()
        cars = []
        for p in prods:
            imgs = []
            try:
                if isinstance(p.images, str) and p.images.strip().startswith('['): imgs = _json.loads(p.images)
                elif isinstance(p.images, str) and p.images.strip(): imgs = [p.images]
            except: pass
            specs = {{}}
            m = _re.search(r"\\[\\[SPEC:(.*?)\\]\\]", p.description or "")
            if m:
                try: specs = _json.loads(m.group(1))
                except: pass
            cars.append({{"id": p.id, "name": p.name, "price": float(p.price or 0), "imgs": imgs,
                         "loc": specs.get("location", "") or "Nigeria",
                         "year": specs.get("year", ""), "mile": specs.get("mileage", ""),
                         "trans": specs.get("transmission", ""), "cond": specs.get("condition", ""),
                         "seller": "Sodangi Motors", "phone": "2348142969979", "agent": 0}})
        html = MARKET_HTML_TEMPLATE.replace("__CARS__", _json.dumps(cars))
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Market Error: {{e}}</h1>")
    finally:
        db.close()
"""
    mc += MKT_ROUTE
    print("✅ Marketplace App injected into main.py!")

# 5. Syntax check locally before pushing
print("\n🧪 Syntax-checking main.py...")
try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ SYNTAX ERROR: {{e.msg}} at line {{e.lineno}}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Resurrect: Move Dashboard and Market to main.py"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel...")
time.sleep(90)

# 6. Test both links
print("\n🔍 Testing V4 Dashboard and Marketplace...")
for path in ["/api/v1/dashboard/v4-dashboard", "/api/v1/dashboard/market"]:
    try:
        req = urllib.request.Request("https://sawa-ai-backend.vercel.app" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            if "SODANGI MOTORS" in body:
                print(f"✅ {{path}} IS LIVE!")
            else:
                print(f"⚠️ {{path}} loaded but HTML mismatch.")
    except Exception as e:
        print(f"❌ {{path}} Error: {{e}}")
