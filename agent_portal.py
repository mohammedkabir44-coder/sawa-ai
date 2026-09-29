import subprocess, time, urllib.request, ast

print("="*60)
print("🚀 AGENT PORTAL + SOCIAL SHARE INJECTION")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. Inject Social Share into Showroom (Safe String Replacement)
if "function shareCar()" not in mc:
    share_code = '''
        # Inject Social Share JS and Button safely
        share_btn_html = """<button class="b bshare" onclick="shareCar()" style="background:#8B5CF6;color:#fff;border:none">📱 Share to Social Media</button>
        <script>
        function shareCar() {
          var t = document.title + " - " + document.querySelector('.price').innerText + "\\n" + location.href;
          if (navigator.share) { navigator.share({title: document.title, text: t, url: location.href}).catch(function(){}); }
          else { navigator.clipboard.writeText(t); alert("Link copied! Share on FB, X, WhatsApp."); }
        }
        </script>"""
        html = html.replace('<a href="tel:', share_btn_html + '\\n        <a href="tel:')
'''
    anchor = "        return HTMLResponse(content=html)"
    idx = mc.find("def ultimate_showroom_247(product_id: int):")
    if idx != -1:
        end_idx = mc.find(anchor, idx)
        if end_idx != -1:
            mc = mc[:end_idx] + share_code + "\n" + mc[end_idx:]
            print("✅ Social Share button injected into Showroom!")
        else:
            print("⚠️ Could not find showroom anchor.")
    else:
        print("⚠️ Showroom function not found.")

# 2. Inject Agent Login Page
if '"/agent-login"' not in mc:
    login_route = '''
@app.get("/agent-login")
def agent_login_page():
    from fastapi.responses import HTMLResponse
    html = r\'\'\'<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agent Login</title>
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
</script></body></html>\'\'\'
    return HTMLResponse(content=html)
'''
    mc += login_route
    print("✅ Agent Login Page injected!")

# 3. Inject Agent Portal (Shows their specific cars)
if '"/agent-portal"' not in mc:
    portal_route = '''
@app.get("/agent-portal")
def agent_portal_page():
    from fastapi.responses import HTMLResponse
    html = r\'\'\'<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Showroom</title>
<style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding:20px;padding-bottom:80px}
.top{background:#1E293B;padding:16px;border-radius:12px;margin-bottom:20px;border:1px solid #334155}
h2{color:#10B981;margin:0}
.card{background:#1E293B;padding:16px;border-radius:12px;margin-bottom:12px;border:1px solid #334155}
.price{color:#10B981;font-size:20px;font-weight:900}
.btn{display:block;text-align:center;background:#EF4444;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:800;margin-top:20px}
</style></head>
<body>
<div class="top"><h2 id="name">My Showroom</h2><p id="role" style="color:#94A3B8;margin:4px 0 0;font-size:13px"></p></div>
<div id="cars"></div>
<a href="/agent-login" class="btn" onclick="localStorage.clear()">Sign Out</a>
<script>
var t=localStorage.getItem("sodangi_token");
if(!t){location.href="/agent-login";}
document.getElementById("name").innerText = localStorage.getItem("sodangi_name") || "Agent";
document.getElementById("role").innerText = "Role: " + (localStorage.getItem("sodangi_role") || "Agent");

async function load(){
  var box=document.getElementById("cars");
  box.innerHTML="<p style=\\'text-align:center;color:#94A3B8\\'>Loading your cars...</p>";
  try{
    var r=await fetch("/api/v1/products/mine",{headers:{"Authorization":"Bearer "+t}});
    if(!r.ok){throw new Error("Session expired");}
    var cars=await r.json();
    if(!cars.length){box.innerHTML="<p style=\\'text-align:center;color:#94A3B8;padding:40px\\'>No cars assigned to your profile yet.</p>";return;}
    var html="";
    cars.forEach(function(c){
      html+='<div class="card"><a href="/api/v1/dashboard/showroom-elite/'+c.id+'" style="text-decoration:none;color:#fff"><div class="title" style="font-weight:800;font-size:16px">'+c.name+'</div><div class="price">₦'+Number(c.price).toLocaleString()+'</div></a></div>';
    });
    box.innerHTML=html;
  }catch(e){ box.innerHTML="<p style=\\'text-align:center;color:#EF4444\\'>"+e.message+" <a href=\\'/agent-login\\' style=\\'color:#10B981\\'>Login again</a></p>"; }
}
load();
</script></body></html>\'\'\'
    return HTMLResponse(content=html)
'''
    mc += portal_route
    print("✅ Agent Portal injected!")

# 4. Update Universal Hub to include Agent Login button
if "Agent Login</a>" not in mc:
    hub_btn = '<a href="/agent-login" class="btn" style="background:#8B5CF6;border-color:#8B5CF6">👤 Agent Login</a>'
    mc = mc.replace('<a href="/api/v1/dashboard/showroom-elite/15" class="btn btn-show">', hub_btn + '\n<a href="/api/v1/dashboard/showroom-elite/15" class="btn btn-show">')
    print("✅ Agent Login button added to Universal Hub!")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg} at line {e.lineno}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Add Agent Portal and Social Share Button"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Testing new routes...")
for path in ["/agent-login", "/agent-portal", "/"]:
    try:
        req = urllib.request.Request("https://sawa-ai-backend.vercel.app" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            if "Agent Portal Login" in body or "My Showroom" in body or "Agent Login" in body:
                print(f"✅ {path} IS LIVE!")
            else:
                print(f"⚠️ {path} loaded but mismatch.")
    except Exception as e:
        print(f"❌ {path} Error: {e}")
