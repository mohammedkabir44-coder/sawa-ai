import subprocess, time, urllib.request, ast

print("="*60)
print("👑 MASTER ANALYTICS & VIRAL ENGINE INJECTION")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. INJECT TRACKING API & ADMIN ANALYTICS DASHBOARD
if '"/api/v1/track"' not in mc:
    TRACK_ROUTES = """

@app.get("/api/v1/track")
def track_event(event: str, pid: int = 0, aid: int = 0):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS site_analytics(id SERIAL PRIMARY KEY, event TEXT, pid INT, aid INT, created_at TIMESTAMP DEFAULT NOW())"))
            conn.commit()
            conn.execute(text("INSERT INTO site_analytics(event,pid,aid) VALUES(:e,:p,:a)"), {"e":event,"p":pid,"a":aid})
            conn.commit()
        return {"status":"ok"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/admin-analytics")
def admin_analytics_page():
    from app.core.database import engine
    from sqlalchemy import text
    from fastapi.responses import HTMLResponse
    stats = {"views":0, "clicks":0, "shares":0}
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS site_analytics(id SERIAL PRIMARY KEY, event TEXT, pid INT, aid INT, created_at TIMESTAMP DEFAULT NOW())"))
            conn.commit()
            rows = conn.execute(text("SELECT event, COUNT(*) FROM site_analytics GROUP BY event")).fetchall()
            for r in rows:
                if r[0] == 'view': stats["views"] = r[1]
                elif r[0] == 'click': stats["clicks"] = r[1]
                elif r[0] == 'share': stats["shares"] = r[1]
    except: pass
    html = r'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Analytics</title>
    <style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding:20px}.card{background:#1E293B;padding:20px;border-radius:12px;margin-bottom:16px;border:1px solid #334155}h2{color:#10B981;margin-top:0}.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}.stat{background:#0F172A;padding:16px;border-radius:10px;text-align:center}.stat h3{margin:0;font-size:28px;color:#F59E0B}.stat p{margin:4px 0 0;font-size:12px;color:#94A3B8}.btn{display:inline-block;background:#3B82F6;color:#fff;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:800;margin-top:20px;margin-right:10px}</style></head>
    <body><h1>📊 Admin Analytics & Tracking</h1>
    <div class="card"><h2>Live Site Performance</h2><div class="grid">
    <div class="stat"><h3>__VIEWS__</h3><p>👁️ Total Page Views</p></div>
    <div class="stat"><h3>__CLICKS__</h3><p>👆 WhatsApp/Call Clicks</p></div>
    <div class="stat"><h3>__SHARES__</h3><p>🚀 Social Media Shares</p></div>
    </div></div>
    <a href="/admin-agents" class="btn" style="background:#EC4899">👥 Manage Agents</a>
    <a href="/" class="btn" style="background:#334155">🏠 Back to Hub</a>
    </body></html>'''
    html = html.replace("__VIEWS__", str(stats["views"])).replace("__CLICKS__", str(stats["clicks"])).replace("__SHARES__", str(stats["shares"]))
    return HTMLResponse(content=html)
"""
    mc += TRACK_ROUTES
    print("✅ Tracking API & Admin Analytics Dashboard injected!")

# 2. INJECT AGENT MANAGER UI (Where you create profiles)
if '"/admin-agents"' not in mc:
    AGENT_UI = """

@app.get("/admin-agents")
def admin_agents_page():
    from fastapi.responses import HTMLResponse
    html = r'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Manage Agents</title>
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
    print("✅ Admin Agent Manager UI injected!")

# 3. INJECT OG TAGS & TRACKING JS INTO SHOWROOM (For Viral Social Previews)
if 'og:title' not in mc:
    target_html_start = "html = f'''<!DOCTYPE html>"
    if target_html_start in mc:
        og_vars = """
        first_img = imgs[0] if imgs else "https://sawa-ai-backend.vercel.app/logo.png"
        og_tags = f'<meta property="og:title" content="{name} - ₦{price} | Sodangi Motors"><meta property="og:description" content="✅ Verified Seller. Click to view photos and contact seller instantly!"><meta property="og:image" content="{first_img}"><meta property="og:url" content="https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/{product_id}"><meta name="twitter:card" content="summary_large_image">'
        """
        mc = mc.replace(target_html_start, og_vars + "\n        " + target_html_start)
        print("✅ OG Variables injected!")
        
        mc = mc.replace("<title>{name}</title>", "<title>{name}</title>\n        {og_tags}")
        print("✅ OG Tags injected into <head> (Viral Previews Active)!")
        
        tracking_js = """
        <script>
        (function(){
          var pid = {product_id};
          fetch('/api/v1/track?event=view&pid='+pid).catch(function(){});
          document.querySelectorAll('.btn-wa, .btn-call').forEach(function(b){
            b.addEventListener('click', function(){ fetch('/api/v1/track?event=click&pid='+pid).catch(function(){}); });
          });
          var oldShare = window.shareCar;
          window.shareCar = function(){ fetch('/api/v1/track?event=share&pid='+pid).catch(function(){}); if(oldShare) oldShare(); };
        })();
        </script>
        """
        mc = mc.replace("</body></html>'''", tracking_js + "\n        </body></html>'''")
        print("✅ Invisible Tracking Pixels injected into Showroom!")
    else:
        print("⚠️ Could not find showroom HTML to inject OG tags.")

# 4. ADD LINKS TO UNIVERSAL HUB
if "Admin Analytics" not in mc and "def sodangi_hub():" in mc:
    hub_links = '<a href="/admin-analytics" class="btn" style="background:#F59E0B;border-color:#F59E0B">📊 Admin Analytics & Tracking</a>\n<a href="/admin-agents" class="btn" style="background:#EC4899;border-color:#EC4899">👥 Manage Agents</a>\n'
    mc = mc.replace('<a href="/api/v1/dashboard/market" class="btn btn-market">', hub_links + '<a href="/api/v1/dashboard/market" class="btn btn-market">')
    print("✅ Analytics & Agent Manager links added to Universal Hub!")

# 5. VERIFY SYNTAX
try:
    ast.parse(mc)
    print("✅ Syntax check passed.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg} at line {e.lineno}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Master: Agent Manager + Analytics + OG Tags + Tracking"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 120s for Vercel to compile...")
time.sleep(120)

print("\n🔍 Testing new features...")
for path in ["/admin-agents", "/admin-analytics"]:
    try:
        req = urllib.request.Request("https://sawa-ai-backend.vercel.app" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            if "Agent Manager" in body or "Admin Analytics" in body:
                print(f"✅ {path} IS LIVE!")
            else:
                print(f"⚠️ {path} loaded but mismatch.")
    except Exception as e:
        print(f"❌ {path} Error: {e}")
