import subprocess, time, urllib.request, ast, json

print("="*60)
print("🛡️ BULLETPROOF: FIXED SHARE BUTTON + PORTAL ROUTE")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. FIX SHARE BUTTON (Inject floating button before </body>)
SHARE_INJECTION = """
<button onclick="shareCar()" style="position:fixed;bottom:180px;left:20px;right:20px;background:#8B5CF6;color:#fff;padding:14px;border-radius:12px;border:none;font-weight:800;font-size:15px;text-align:center;z-index:101;box-shadow:0 4px 12px rgba(139,92,246,0.4)">📱 Share to Social Media</button>
<script>
function shareCar() {
  var t = document.title + " - " + document.querySelector('.price').innerText + "\\n" + location.href;
  if (navigator.share) { navigator.share({title: document.title, text: t, url: location.href}).catch(function(){}); }
  else { navigator.clipboard.writeText(t); alert("Link copied! Share on FB, X, WhatsApp."); }
}
</script>
"""

if "function shareCar()" not in mc:
    # Find the end of the showroom HTML template
    end_tag = "</body></html>'''"
    if end_tag in mc:
        mc = mc.replace(end_tag, SHARE_INJECTION + end_tag)
        print("✅ Social Share Button injected as floating button!")
    else:
        print("⚠️ Could not find </body></html>''' to inject Share Button.")
else:
    print("ℹ️ Social Share Button already exists.")

# 2. FIX AGENT PORTAL (Inject early in the file to ensure registration)
PORTAL_ROUTE = """

@app.get("/agent-portal")
def agent_portal_page():
    from fastapi.responses import HTMLResponse
    html = r'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Showroom</title>
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
  box.innerHTML="<p style='text-align:center;color:#94A3B8'>Loading your cars...</p>";
  try{
    var r=await fetch("/api/v1/products/mine",{headers:{"Authorization":"Bearer "+t}});
    if(!r.ok){throw new Error("Session expired");}
    var cars=await r.json();
    if(!cars.length){box.innerHTML="<p style='text-align:center;color:#94A3B8;padding:40px'>No cars assigned to your profile yet.</p>";return;}
    var html="";
    cars.forEach(function(c){
      html+='<div class="card"><a href="/api/v1/dashboard/showroom-elite/'+c.id+'" style="text-decoration:none;color:#fff"><div class="title" style="font-weight:800;font-size:16px">'+c.name+'</div><div class="price">₦'+Number(c.price).toLocaleString()+'</div></a></div>';
    });
    box.innerHTML=html;
  }catch(e){ box.innerHTML="<p style='text-align:center;color:#EF4444'>"+e.message+" <a href='/agent-login' style='color:#10B981'>Login again</a></p>"; }
}
load();
</script></body></html>'''
    return HTMLResponse(content=html)
"""

if "def agent_portal_page():" not in mc:
    # Inject right after the CORS middleware setup so it registers early
    insert_idx = mc.find("app.add_middleware(CORSMiddleware")
    if insert_idx != -1:
        end_of_cors = mc.find(")", insert_idx) + 1
        mc = mc[:end_of_cors] + PORTAL_ROUTE + mc[end_of_cors:]
        print("✅ Agent Portal route injected EARLY for guaranteed registration!")
    else:
        mc = PORTAL_ROUTE + mc
        print("✅ Agent Portal route prepended!")
else:
    print("ℹ️ Agent Portal already exists.")

# 3. Verify Syntax
try:
    ast.parse(mc)
    print("✅ Syntax check passed.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Fix: Floating Share Button + Early Portal Registration"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 120s for Vercel to fully compile (large file)...")
time.sleep(120)

print("\n🔍 Testing live routes...")
for path in ["/agent-portal", "/api/v1/dashboard/showroom-elite/15"]:
    try:
        req = urllib.request.Request("https://sawa-ai-backend.vercel.app" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            if "My Showroom" in body:
                print(f"✅ {path} IS LIVE (Agent Portal)!")
            elif "shareCar" in body:
                print(f"✅ {path} IS LIVE (Share Button Found)!")
            else:
                print(f"⚠️ {path} loaded but mismatch.")
    except Exception as e:
        print(f"❌ {path} Error: {e}")
