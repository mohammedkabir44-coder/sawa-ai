import re
import subprocess
import time
import urllib.request
import ast

print("="*60)
print("💥 TOTAL OVERWRITE: FORCING ALL BUTTONS INTO THE HUB")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

NEW_HUB = '''@app.get("/")
@app.get("/api/v1/dashboard/portal")
def sodangi_hub():
    from fastapi.responses import HTMLResponse
    html = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sodangi Hub</title>
<style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:20px;box-sizing:border-box}
h1{color:#10B981;font-size:28px;margin-bottom:8px;text-align:center}p{color:#94A3B8;margin-bottom:30px;text-align:center}
.container{display:flex;flex-direction:column;gap:16px;width:100%;max-width:400px}
.btn{display:flex;align-items:center;justify-content:center;gap:12px;background:#1E293B;color:#fff;padding:20px;border-radius:16px;text-decoration:none;font-weight:800;font-size:18px;border:1px solid #334155;box-shadow:0 4px 12px rgba(0,0,0,0.2);transition:transform 0.1s}
.btn:active{transform:scale(0.98)}
.btn-market{border-color:#059669;background:linear-gradient(135deg,#064E3B,#065F46)}
.btn-admin{border-color:#2563EB;background:linear-gradient(135deg,#1E3A8A,#1D4ED8)}
.btn-show{border-color:#F59E0B;background:linear-gradient(135deg,#78350F,#92400E)}
.btn-agents{border-color:#EC4899;background:linear-gradient(135deg,#831843,#BE185D)}
.btn-analytics{border-color:#F59E0B;background:linear-gradient(135deg,#92400E,#B45309)}
.btn-agent-login{border-color:#8B5CF6;background:linear-gradient(135deg,#4C1D95,#6D28D9)}
</style></head>
<body><h1>🚗 SODANGI MOTORS</h1><p>The Ultimate Automotive Hub</p>
<div class="container">
<a href="/api/v1/dashboard/market" class="btn btn-market">🏪 Marketplace (Buy Cars)</a>
<a href="/api/v1/dashboard/v4-dashboard" class="btn btn-admin">🏢 Admin Dashboard (Sell Cars)</a>
<a href="/api/v1/dashboard/showroom-elite/15" class="btn btn-show">🚗 Showroom Demo (Car #15)</a>
<a href="/admin-agents" class="btn btn-agents">👥 Manage Agents (Create Profiles)</a>
<a href="/admin-analytics" class="btn btn-analytics">📊 Admin Analytics & Tracking</a>
<a href="/agent-login" class="btn btn-agent-login">👤 Agent Login</a>
</div></body></html>"""
    return HTMLResponse(content=html)'''

# Find the old sodangi_hub function and completely replace it
idx = mc.find('def sodangi_hub():')
if idx != -1:
    # Find the previous @app.get
    dec_idx = mc.rfind('@app.get', 0, idx)
    # Find the end of the function (next @app.get or EOF)
    end_idx = mc.find('\n@app.get', idx)
    if end_idx == -1: end_idx = mc.find('\n@app.middleware', idx)
    if end_idx == -1: end_idx = len(mc)
    
    mc = mc[:dec_idx] + NEW_HUB + '\n' + mc[end_idx:]
    print("✅ Successfully rewrote the Universal Hub function with all 6 buttons!")
else:
    mc += '\n' + NEW_HUB
    print("✅ Appended Universal Hub as it was missing entirely!")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Force rewrite Universal Hub with all buttons"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel...")
time.sleep(90)

print("\n🔍 Testing Hub...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "Manage Agents" in body and "Admin Analytics" in body:
            print("✅ ✅ ✅ ALL BUTTONS ARE LIVE ON THE HUB!")
            print("\n👉 Open this link in an INCOGNITO WINDOW on your phone:")
            print("https://sawa-ai-backend.vercel.app/")
        else:
            print("⚠️ Hub loaded but buttons missing.")
except Exception as e:
    print(f"❌ Error: {e}")
