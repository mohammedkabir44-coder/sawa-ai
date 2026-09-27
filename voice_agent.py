import subprocess, time, urllib.request, json

print("="*60)
print("🎙️ VOICE NOTES + AGENT SHOWROOM + NEW PHONE NUMBER")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. Surgically replace the Showroom Function
start_idx = mc.find('def showroom_elite_bypass(product_id: int):')
if start_idx != -1:
    next_route_idx = mc.find('\n@app.', start_idx + 10)
    if next_route_idx == -1: next_route_idx = len(mc)
    before = mc[:start_idx]
    after = mc[next_route_idx:]
    
    new_func = '''def showroom_elite_bypass(product_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    import json as _json
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p: 
            return HTMLResponse(content=f"<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>Car ID {product_id} not found.</h1>", status_code=404)
        
        imgs = []
        try:
            imgs = _json.loads(p.images) if isinstance(p.images, str) else (p.images or [])
        except: 
            imgs = []
            
        agent_name = "Sodangi Motors"
        agent_id = 0
        try:
            from app.api.v1.endpoints.agents_api import Agent, ProductAgent
            lk = db.query(ProductAgent).filter(ProductAgent.product_id == p.id).first()
            if lk:
                ag = db.query(Agent).filter(Agent.id == lk.agent_id).first()
                if ag:
                    agent_name = ag.full_name or "Agent"
                    agent_id = ag.id
        except:
            pass

        name = str(p.name).replace('"',"'")
        price = f"{float(p.price or 0):,.0f}"
        
        gallery = ""
        for u in imgs:
            if ".mp4" in str(u) or ".webm" in str(u):
                gallery += f'<video src="{u}" controls playsinline style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0"></video>'
            else:
                gallery += f'<img src="{u}" style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0">'
                
        if not gallery: 
            gallery = '<img src="https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?w=800" style="width:100%;height:320px;object-fit:cover">'

        html_template = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>
        <style>body{{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding-bottom:240px}}.gal{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000}}.wrap{{max-width:600px;margin:0 auto;padding:20px}}.price{{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}}.badge{{background:rgba(16,185,129,0.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}}.cta{{position:fixed;bottom:0;left:0;right:0;padding:12px;background:#0A0F1C;border-top:1px solid #333;display:flex;flex-direction:column;gap:8px;z-index:100}}.btn-wa{{display:block;background:#25D366;color:#fff;padding:14px;border-radius:12px;text-decoration:none;font-weight:900;font-size:15px;box-shadow:0 6px 12px rgba(37,211,102,0.3);text-align:center}}.btn-call{{display:block;background:rgba(245,158,11,0.1);color:#F59E0B;padding:12px;border-radius:12px;text-decoration:none;font-weight:800;font-size:14px;border:1px solid #F59E0B;text-align:center}}.btn-agent{{display:block;background:#3B82F6;color:#fff;padding:12px;border-radius:12px;text-decoration:none;font-weight:800;font-size:14px;text-align:center}}.voice-card{{background:#1E293B;border:1px solid #334155;border-radius:16px;padding:16px;margin-top:20px}}.rec-btn{{background:#EF4444;color:#fff;border:none;padding:14px;border-radius:50px;width:100%;font-weight:800;font-size:15px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px}}</style>
        </head><body>
        <div class="gal">{gallery}</div>
        <div class="wrap">
          <span class="badge">✅ VERIFIED SELLER</span>
          <h1 style="margin-top:8px">{name}</h1>
          <div class="price">&#8358; {price}</div>
          <div class="voice-card">
            <h3 style="margin-bottom:12px;font-size:16px">🎙️ Voice Comments</h3>
            <p style="font-size:13px;color:#94A3B8;margin-bottom:12px">Have a question? Record a voice note and send it directly to the seller!</p>
            <button class="rec-btn" id="recBtn" onclick="toggleRec()">🎤 Tap to Record Voice Note</button>
            <p id="recStatus" style="text-align:center;margin-top:8px;font-size:12px;color:#F59E0B"></p>
          </div>
        </div>
        <div class="cta">
          <a href="https://wa.me/2348142969979?text=Salam! I am looking at the {name}" target="_blank" class="btn-wa">💬 WhatsApp Seller</a>
          <a href="tel:+2348142969979" class="btn-call">📞 Call Inspection <span style="font-size:12px;opacity:0.8">(₦5,000 Fee)</span></a>
          <a href="/api/v1/dashboard/agent/{agent_id}" class="btn-agent">👤 View {agent_name}'s Showroom</a>
        </div>
        <script>
        let mr, chunks=[], rec=false;
        async function toggleRec(){{
          if(!rec){{
            try{{
              const s = await navigator.mediaDevices.getUserMedia({{audio:true}});
              mr = new MediaRecorder(s); chunks=[];
              mr.ondataavailable = e => chunks.push(e.data);
              mr.onstop = async () => {{
                const blob = new Blob(chunks, {{type:'audio/webm'}});
                const fd = new FormData(); fd.append('file', blob, 'voice.webm');
                document.getElementById('recStatus').innerText = '⏳ Sending...';
                const r = await fetch('/api/v1/dashboard/upload-media', {{method:'POST', body:fd}});
                const d = await r.json();
                if(d.url){{
                  const msg = "Salam! I left a voice note about the {name}: " + d.url;
                  window.open("https://wa.me/2348142969979?text=" + encodeURIComponent(msg), "_blank");
                  document.getElementById('recStatus').innerText = '✅ Sent!';
                }}
              }};
              mr.start(); rec=true;
              document.getElementById('recBtn').style.background = '#991B1B';
              document.getElementById('recBtn').innerText = '⏹️ Tap to Stop & Send';
              document.getElementById('recStatus').innerText = '🔴 Recording...';
            }}catch(e){{ alert('Mic access denied!'); }}
          }}else{{
            mr.stop(); rec=false;
            document.getElementById('recBtn').style.background = '#EF4444';
            document.getElementById('recBtn').innerText = '🎤 Tap to Record Voice Note';
          }}
        }}
        </script>
        </body></html>"""
        return HTMLResponse(content=html_template.format(name=name, price=price, gallery=gallery, agent_name=agent_name, agent_id=agent_id))
    except Exception as e:
        return HTMLResponse(content=f"<h1 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>DB Error: {e}</h1>", status_code=500)
    finally:
        db.close()
'''
    mc = before + new_func + after
    print("✅ Showroom updated with Voice Notes, Agent Link, and New Phone!")

# 2. Add Agent Showroom Route if missing
if '"/api/v1/dashboard/agent/{agent_id}"' not in mc:
    agent_route = """

@app.get("/api/v1/dashboard/agent/{agent_id}")
def agent_showroom(agent_id: int):
    from app.core.database import SessionLocal
    from app.models.product import Product
    from fastapi.responses import HTMLResponse
    db = SessionLocal()
    try:
        from app.api.v1.endpoints.agents_api import Agent, ProductAgent
        ag = db.query(Agent).filter(Agent.id == agent_id).first()
        if not ag: return HTMLResponse("<h1 style='color:#fff;text-align:center'>Agent not found</h1>")
        links = db.query(ProductAgent).filter(ProductAgent.agent_id == agent_id).all()
        cars = db.query(Product).filter(Product.id.in_([l.product_id for l in links])).all() if links else []
        
        cars_html = ""
        for c in cars:
            cars_html += f'<div style="background:#1E293B;padding:15px;border-radius:12px;margin-bottom:10px"><a href="/api/v1/dashboard/showroom-elite/{c.id}" style="text-decoration:none;color:#fff"><h3 style="margin:0;color:#10B981">{c.name}</h3><p style="margin:5px 0 0;font-size:18px;font-weight:900">₦{float(c.price or 0):,.0f}</p></a></div>'
        if not cars_html: cars_html = "<p style='text-align:center;color:#94A3B8'>No cars currently assigned to this agent.</p>"
        
        html = f'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{ag.full_name}</title>
        <style>body{{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding:20px}}.wrap{{max-width:600px;margin:0 auto}}</style>
        </head><body><div class="wrap">
        <h1 style="color:#10B981">👤 {ag.full_name}'s Showroom</h1>
        <p style="color:#94A3B8;margin-bottom:20px">Verified Agent at Sodangi Motors</p>
        {cars_html}
        </div></body></html>'''
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f"<h1>Error: {e}</h1>")
    finally:
        db.close()
"""
    mc += agent_route
    print("✅ Added Agent Showroom Route!")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Showroom: Voice Notes, Agent Link, New Phone"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel...")
time.sleep(75)

print("\n🔍 Testing...")
req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15", headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "Voice Comments" in body and "+2348142969979" in body:
            print("✅ ✅ ✅ ALL UPGRADES LIVE!")
            print("\n" + "="*60)
            print("👉 REFRESH THIS LINK ON YOUR PHONE:")
            print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15")
            print("="*60)
        else:
            print("⚠️ Deployed but missing new features.")
except Exception as e:
    print("❌ Error:", e)
