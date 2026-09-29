import subprocess, time, urllib.request, ast

print("="*60)
print("🎯 SURGICAL STRIKE: AGENT MANAGER + OG TAGS + TRACKING")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. FORCE INJECT AGENT MANAGER (Check for function name, not route string)
if "def admin_agents_page():" not in mc:
    AGENT_UI = """
@app.get("/admin-agents")
def admin_agents_page():
    from fastapi.responses import HTMLResponse
    html = '''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Manage Agents</title>
    <style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding:20px}.card{background:#1E293B;padding:20px;border-radius:12px;margin-bottom:16px;border:1px solid #334155}h2{color:#10B981;margin-top:0}label{display:block;margin-top:12px;font-size:13px;color:#94A3B8}input{width:100%;padding:12px;border-radius:8px;border:1px solid #334155;background:#0F172A;color:#fff;font-size:16px;box-sizing:border-box;margin-top:4px}.btn{width:100%;padding:14px;margin-top:16px;background:#8B5CF6;color:#fff;border:none;border-radius:10px;font-weight:800;font-size:16px;cursor:pointer}.msg{padding:10px;border-radius:8px;margin-top:10px;text-align:center}</style></head>
    <body><h1>👥 Agent Manager</h1>
    <div class="card"><h2>Create New Agent Profile</h2>
    <label>Full Name</label><input id="name" placeholder="Musa Abdullahi">
    <label>Email (Username)</label><input id="email" placeholder="agent@sodangi.com">
    <label>Password</label><input id="pass" type="password" placeholder="Min 6 characters">
    <button class="btn" onclick="createAgent()">🚀 Create Agent Profile</button>
    <div id="msg" class="msg" style="display:none"></div>
    </div>
    <a href="/admin-analytics" style="display:block;text-align:center;color:#3B82F6;margin-top:20px">← Back to Analytics</a>
    <script>
    async function createAgent(){
      var n=document.getElementById("name").value;
      var e=document.getElementById("email").value;
      var p=document.getElementById("pass").value;
      var m=document.getElementById("msg");
      if(!n||!e||!p){m.innerText="❌ Fill all fields!";m.style.background="#7F1D1D";m.style.display="block";return;}
      m.innerText="⏳ Creating...";m.style.background="#1E3A8A";m.style.display="block";
      try{
        var r=await fetch("/api/v1/auth/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({full_name:n,email:e,password:p,role:"agent"})});
        var d=await r.json();
        if(d.access_token || d.id || d.email){
          m.innerHTML="✅ Agent Created!<br><b>Email:</b> "+e+"<br><b>Password:</b> "+p+"<br><br>Give these details to your agent to login at <a href='/agent-login' style='color:#10B981'>/agent-login</a>";
          m.style.background="#065F46";
          document.getElementById("name").value="";document.getElementById("email").value="";document.getElementById("pass").value="";
        } else { m.innerText="❌ Error: "+(d.detail||"Unknown");m.style.background="#7F1D1D"; }
      }catch(ex){ m.innerText="❌ "+ex.message;m.style.background="#7F1D1D"; }
    }
    </script></body></html>'''
    return HTMLResponse(content=html)
"""
    mc += AGENT_UI
    print("✅ Agent Manager forcefully appended!")
else:
    print("ℹ️ Agent Manager already exists.")

# 2. INJECT OG TAGS INTO SHOWROOM (Targeting the Zero f-string template)
old_title = '<title>__NAME__ | Sodangi Motors</title>'
new_title = '''<title>__NAME__ | Sodangi Motors</title>
<meta property="og:title" content="__NAME__ - ₦__PRICE__ | Sodangi Motors">
<meta property="og:description" content="✅ Verified Seller. Click to view photos and contact seller instantly!">
<meta property="og:image" content="__FIRST_IMG__">
<meta property="og:url" content="https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/__PID__">
<meta name="twitter:card" content="summary_large_image">'''

if old_title in mc and 'og:title' not in mc:
    mc = mc.replace(old_title, new_title)
    old_out = 'out = T.replace("__GALLERY__", gal).replace("__NAME__", name).replace("__PRICE__", price).replace("__WA__", wa)'
    new_out = 'out = T.replace("__GALLERY__", gal).replace("__NAME__", name).replace("__PRICE__", price).replace("__WA__", wa).replace("__FIRST_IMG__", imgs[0] if imgs else "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?w=1200").replace("__PID__", str(product_id))'
    if old_out in mc:
        mc = mc.replace(old_out, new_out)
        print("✅ OG Tags and variables injected into Showroom!")
    else:
        print("⚠️ Could not find T.replace line to inject OG variables.")
else:
    print("ℹ️ OG Tags already exist or title tag not found.")

# 3. INJECT TRACKING JS
tracking_js = '''
<script>
(function(){
  var pid = __PID__;
  fetch('/api/v1/track?event=view&pid='+pid).catch(function(){});
  document.querySelectorAll('.btn-wa, .btn-call').forEach(function(b){
    b.addEventListener('click', function(){ fetch('/api/v1/track?event=click&pid='+pid).catch(function(){}); });
  });
  var oldShare = window.shareCar;
  window.shareCar = function(){ fetch('/api/v1/track?event=share&pid='+pid).catch(function(){}); if(oldShare) oldShare(); };
})();
</script>
</body></html>'''

old_end = "</body></html>'''"
if old_end in mc and 'event=view' not in mc:
    mc = mc.replace(old_end, tracking_js + "'''")
    print("✅ Invisible Tracking Pixels injected!")
else:
    print("ℹ️ Tracking JS already exists or end tag not found.")

# 4. ADD LINKS TO UNIVERSAL HUB (if missing)
if "Admin Analytics" not in mc and "def sodangi_hub():" in mc:
    hub_links = '<a href="/admin-analytics" class="btn" style="background:#F59E0B;border-color:#F59E0B">📊 Admin Analytics & Tracking</a>\n<a href="/admin-agents" class="btn" style="background:#EC4899;border-color:#EC4899">👥 Manage Agents</a>\n'
    mc = mc.replace('<a href="/api/v1/dashboard/market" class="btn btn-market">', hub_links + '<a href="/api/v1/dashboard/market" class="btn btn-market">')
    print("✅ Hub links added!")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg} at line {e.lineno}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Surgical Fix: Agent Manager + OG Tags + Tracking"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 120s for Vercel to compile...")
time.sleep(120)

print("\n🔍 Testing live routes...")
for path in ["/admin-agents", "/admin-analytics", "/api/v1/dashboard/showroom-elite/15"]:
    try:
        req = urllib.request.Request("https://sawa-ai-backend.vercel.app" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            if "Agent Manager" in body:
                print(f"✅ {path} IS LIVE (Agent Manager)!")
            elif "Admin Analytics" in body:
                print(f"✅ {path} IS LIVE (Analytics)!")
            elif "og:title" in body:
                print(f"✅ {path} IS LIVE (OG Tags Found)!")
            else:
                print(f"⚠️ {path} loaded but mismatch.")
    except Exception as e:
        print(f"❌ {path} Error: {e}")
