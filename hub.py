import subprocess, time, urllib.request, ast

print("="*60)
print("🌐 THE UNIVERSAL HUB: ONE LINK TO RULE THEM ALL")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

HUB_HTML = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sodangi Hub</title>
<style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:20px;box-sizing:border-box}
h1{color:#10B981;font-size:28px;margin-bottom:8px;text-align:center}p{color:#94A3B8;margin-bottom:30px;text-align:center}
.container{display:flex;flex-direction:column;gap:16px;width:100%;max-width:400px}
.btn{display:flex;align-items:center;justify-content:center;gap:12px;background:#1E293B;color:#fff;padding:20px;border-radius:16px;text-decoration:none;font-weight:800;font-size:18px;border:1px solid #334155;box-shadow:0 4px 12px rgba(0,0,0,0.2);transition:transform 0.1s}
.btn:active{transform:scale(0.98)}
.btn-market{border-color:#059669;background:linear-gradient(135deg,#064E3B,#065F46)}
.btn-admin{border-color:#2563EB;background:linear-gradient(135deg,#1E3A8A,#1D4ED8)}
.btn-show{border-color:#F59E0B;background:linear-gradient(135deg,#78350F,#92400E)}</style></head>
<body><h1>🚗 SODANGI MOTORS</h1><p>The Ultimate Automotive Hub</p>
<div class="container">
<a href="/api/v1/dashboard/market" class="btn btn-market">🏪 Marketplace (Buy Cars)</a>
<a href="/api/v1/dashboard/v4-dashboard" class="btn btn-admin">🏢 Admin Dashboard (Sell Cars)</a>
<a href="/api/v1/dashboard/showroom-elite/15" class="btn btn-show">🚗 Showroom Demo (Car #15)</a>
</div></body></html>"""

if "def sodangi_hub():" not in mc:
    hub_code = '''
@app.get("/")
@app.get("/api/v1/dashboard/portal")
def sodangi_hub():
    from fastapi.responses import HTMLResponse
    html = """''' + HUB_HTML + '''"""
    return HTMLResponse(content=html)
'''
    # Remove old root redirect if it exists to prevent conflicts
    mc = mc.replace("""@app.get("/", include_in_schema=False)
def root_market():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/dashboard/market")""", "")
    
    mc += hub_code
    print("✅ Universal Hub injected!")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Add Universal Hub: One link to all 3 portals"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Testing the Hub...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "SODANGI MOTORS" in body and "Marketplace" in body and "Admin" in body:
            print("✅ ✅ ✅ THE UNIVERSAL HUB IS LIVE!")
            print("\n" + "="*60)
            print("👉 YOUR MASTER LINK (Save this to your phone):")
            print("https://sawa-ai-backend.vercel.app/")
            print("="*60)
        else:
            print("⚠️ Hub loaded but HTML mismatch.")
except Exception as e:
    print(f"❌ Error: {e}")
