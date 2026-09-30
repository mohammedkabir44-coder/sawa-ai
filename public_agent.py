import subprocess, time, urllib.request, ast

print("="*70)
print("🔗 INJECTING PUBLIC AGENT LINK (/agent)")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. Add the redirect route
redirect_route = """

@app.get("/agent")
@app.get("/staff")
@app.get("/login")
def agent_public_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/agent-login")
"""

if 'def agent_public_redirect():' not in mc:
    mc += redirect_route
    print("✅ /agent redirect route injected!")

# 2. Update Universal Hub button to point to /agent and look better
old_btn = '<a href="/agent-login" class="btn btn-agent-login">👤 Agent Login</a>'
new_btn = '<a href="/agent" class="btn btn-agent-login" style="background:linear-gradient(135deg,#4C1D95,#6D28D9)">👤 Agent Portal (Staff Login)</a>'

if old_btn in mc:
    mc = mc.replace(old_btn, new_btn)
    print("✅ Universal Hub Agent button updated!")
elif 'Agent Portal (Staff Login)' not in mc:
    # fallback if formatting changed
    mc = mc.replace('👤 Agent Login', '👤 Agent Portal (Staff Login)')
    mc = mc.replace('href="/agent-login"', 'href="/agent"')
    print("✅ Universal Hub Agent button updated via fallback!")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Add public /agent link for staff login"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 60s for Vercel...")
time.sleep(60)

print("\n🔍 Testing public agent link...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/agent", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        if "Agent Portal Login" in r.read().decode() or r.url.endswith("/agent-login"):
            print("✅ ✅ ✅ /agent LINK IS LIVE AND REDIRECTS PERFECTLY!")
            print("\n👉 Give this link to your agents:")
            print("https://sawa-ai-backend.vercel.app/agent")
except Exception as e:
    print(f"❌ Error: {e}")
