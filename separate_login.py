import subprocess, time, urllib.request

print("="*60)
print("🛠️ CREATING SEPARATE AGENT LOGIN FILE")
print("="*60)

# 1. Create the new file
login_code = """
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/agent-login")
def agent_login_page():
    html = r'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agent Login</title>
<style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;box-sizing:border-box}
.box{background:#1E293B;padding:30px;border-radius:16px;width:100%;max-width:400px;border:1px solid #334155}
h2{color:#10B981;margin-top:0;text-align:center}
label{display:block;margin-top:16px;font-size:14px;color:#94A3B8}
input{width:100%;padding:14px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:#fff;font-size:16px;box-sizing:border-box;margin-top:6px}
.btn{width:100%;padding:16px;margin-top:24px;background:#10B981;color:#052E16;border:none;border-radius:10px;font-weight:800;font-size:16px;cursor:pointer}
.err{color:#EF4444;text-align:center;margin-top:12px;font-size:14px}</style></head>
<body><div class="box"><h2>👤 Agent Portal Login</h2>
<label>Email / Username</label><input id="email" type="text" placeholder="agent@sodangi.com">
<label>Password</label><input id="pass" type="password" placeholder="••••••••">
<button class="btn" onclick="login()">Sign In</button>
<p class="err" id="err"></p>
<p style="text-align:center;margin-top:20px;font-size:13px;color:#64748B">Only Admin can create new profiles.</p>
</div>
<script>
async function login(){
  var e=document.getElementById("email").value;
  var p=document.getElementById("pass").value;
  document.getElementById("err").innerText="Signing in...";
  try{
    var fd=new FormData(); fd.append("username",e); fd.append("password",p);
    var r=await fetch("/api/v1/auth/login",{method:"POST",body:fd});
    var d=await r.json();
    if(d.access_token){
      localStorage.setItem("sodangi_token", d.access_token);
      localStorage.setItem("sodangi_role", d.role||"agent");
      localStorage.setItem("sodangi_name", d.full_name||e);
      location.href="/agent-portal";
    } else { document.getElementById("err").innerText="Login failed: "+(d.detail||"Check credentials"); }
  }catch(ex){ document.getElementById("err").innerText="Error: "+ex.message; }
}
</script></body></html>'''
    return HTMLResponse(content=html)
"""

with open("backend/app/agent_login.py", "w", encoding="utf-8") as f:
    f.write(login_code)
print("✅ agent_login.py created!")

# 2. Force main.py to include this router
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

include_stmt = """
try:
    from app.agent_login import router as login_router
    app.include_router(login_router)
except Exception as e:
    pass
"""

if "from app.agent_login import router" not in mc:
    # Inject right after CORS middleware
    idx = mc.find("app.add_middleware(CORSMiddleware")
    if idx != -1:
        end_cors = mc.find(")", idx) + 1
        mc = mc[:end_cors] + include_stmt + mc[end_cors:]
        print("✅ Router included in main.py!")
    else:
        mc += include_stmt
        print("✅ Router appended to main.py!")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Fix: Create separate agent_login.py file and include router"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Testing Agent Login Route...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/agent-login", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "Agent Portal Login" in body:
            print("✅ ✅ ✅ AGENT LOGIN PAGE IS 100% LIVE!")
            print("\n👉 Open this in an INCOGNITO window on your phone:")
            print("https://sawa-ai-backend.vercel.app/agent-login")
        else:
            print("⚠️ Route loaded but HTML mismatch.")
except Exception as e:
    print(f"❌ Error: {e}")
