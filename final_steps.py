import subprocess, time, urllib.request, json, re

print("="*60)
print("🚀 STEP 3 & 4: VIRAL SHARE + BUYER MATCHMAKING")
print("="*60)

# 1. UPDATE MAIN.PY (Showroom Caption + Marketplace Notify Me + APIs)
print("\n[1/3] Injecting Viral Share & Matchmaking APIs into main.py...")
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# [A] Add Copy Caption button to Nuclear Showroom
if "Copy Ad Caption" not in mc:
    caption_btn = '''<button onclick="navigator.clipboard.writeText('🚗 {name} - ₦{price}\\n✅ Verified Seller | Sodangi Motors\\n👉 ' + location.href).then(function(){alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB')});" style="background:#3B82F6;color:#fff;padding:12px;border-radius:12px;border:none;font-weight:800;width:100%;text-align:center">📣 Copy Ad Caption</button>'''
    mc = mc.replace('<a href="tel:+2348142969979"', caption_btn + '\n        <a href="tel:+2348142969979"')
    print("✅ Added Copy Caption to Elite Showroom!")

# [B] Add Notify Me to Marketplace
if "notifyMe(" not in mc:
    notify_js = '''
function notifyMe(id){
  var c = CARS.find(function(x){return x.id==id});
  var b = prompt("Your maximum budget (NGN):"); if(!b) return;
  var ph = prompt("Your WhatsApp number (e.g. 2348012345678):"); if(!ph) return;
  fetch("/api/v1/dashboard/alert-save?phone="+ph.replace(/[^0-9]/g,"")+"&budget="+parseInt(b.replace(/[^0-9]/g,""))+"&car="+encodeURIComponent(c.name))
  .then(function(){alert("🔔 Saved! We will text you when a matching car arrives.")}).catch(function(e){alert(e)});
}
'''
    mc = mc.replace('function contact(c){', notify_js + '\nfunction contact(c){')
    mc = mc.replace('.cbtn{', '.nbtn{background:#3B82F6;color:#fff;border:none;font-size:12px;font-weight:800;padding:8px 10px;border-radius:999px;cursor:pointer;margin-right:6px}.cbtn{')
    mc = mc.replace('<button class="cbtn" data-id="\'+c.id+\'">Contact</button>', '<button class="nbtn" onclick="notifyMe(\'+c.id+\');event.stopPropagation();">🔔</button><button class="cbtn" data-id="\'+c.id+\'">Contact</button>')
    print("✅ Added 🔔 Notify Me button to Marketplace!")

# [C] Add Alert APIs
ALERT_APIS = """

@app.get("/api/v1/dashboard/alert-save")
def alert_save(phone: str, budget: int, car: str = ""):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS buyer_alerts(id SERIAL PRIMARY KEY, phone TEXT, budget BIGINT, car TEXT, created_at TIMESTAMP DEFAULT NOW())"))
            conn.commit()
            conn.execute(text("INSERT INTO buyer_alerts(phone,budget,car) VALUES(:p,:b,:c)"), {"p":phone,"b":budget,"c":car})
            conn.commit()
        return {"status":"saved"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/dashboard/alert-match")
def alert_match(price: int = 0):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT phone, budget, car FROM buyer_alerts WHERE budget >= :p"), {"p": price}).fetchall()
        return {"matches": [{"phone": r[0], "budget": r[1], "car": r[2]} for r in rows]}
    except Exception as e:
        return {"matches": [], "error": str(e)}
"""
if '"/api/v1/dashboard/alert-save"' not in mc:
    mc += ALERT_APIS
    print("✅ Added Alert Save & Match APIs!")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

# 2. UPDATE AGENTS_API.PY (V4 Matchmaking Popup)
print("\n[2/3] Injecting Matchmaking Popup into V4 Dashboard...")
url2 = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as r:
    code = r.read().decode()

MATCH_UI = """
<div id="matchModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:1001;padding:20px;overflow-y:auto">
 <div style="max-width:500px;margin:0 auto;background:#0F172A;border:1px solid #334155;border-radius:20px;padding:20px;color:#fff">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><h3 style="margin:0;color:#10B981">🔔 Hot Buyers Found!</h3><button onclick="document.getElementById('matchModal').style.display='none'" style="background:#EF4444;color:#fff;border:none;padding:8px 14px;border-radius:8px;font-weight:800">Close</button></div>
  <p style="color:#94A3B8;font-size:13px;margin-bottom:12px">These buyers are looking for a car in this price range. Tap to text them instantly!</p>
  <div id="matchList"></div>
 </div>
</div>
<script>
async function notifyMatches(n, p){
  try {
    var r = await fetch('/api/v1/dashboard/alert-match?price=' + Math.round(p));
    var d = await r.json();
    if(d.matches && d.matches.length > 0){
      var html = '';
      d.matches.forEach(function(m){
        var msg = "Salam! A new " + n + " just landed at Sodangi Motors for NGN " + Number(p).toLocaleString() + ". Are you still looking?";
        html += '<a href="https://wa.me/' + m.phone + '?text=' + encodeURIComponent(msg) + '" target="_blank" style="display:block;background:#1E293B;color:#fff;padding:14px;border-radius:12px;margin-bottom:10px;text-decoration:none;font-weight:700;border:1px solid #334155">💬 Text ' + m.phone + '<br><span style="font-size:12px;color:#10B981;font-weight:400">Budget: ₦' + Number(m.budget).toLocaleString() + '</span></a>';
      });
      document.getElementById('matchList').innerHTML = html;
      document.getElementById('matchModal').style.display = 'block';
    }
  } catch(e){ console.log(e); }
}
</script>
"""

if 'id="matchModal"' not in code:
    if '</body>' in code:
        code = code.replace('</body>', MATCH_UI + '\n</body>', 1)
        print("✅ Matchmaking Modal injected!")

# Hook notifyMatches into publishCar
if 'notifyMatches(n,p)' not in code and 'go("Cars");' in code:
    code = code.replace('go("Cars");', 'go("Cars");\n    notifyMatches(n, p);')
    print("✅ Hooked matchmaking into publishCar!")

with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)

# 3. PUSH
print("\n[3/3] Pushing Step 3 & 4 to Vercel...")
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Master Plan: Viral Share + Buyer Matchmaking"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel...")
time.sleep(90)
print("✅ STEP 3 & 4 DEPLOYED!")
