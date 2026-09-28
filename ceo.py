import subprocess, time, urllib.request, json, re

print("="*60)
print("📊 DEPLOYING CEO FINANCIAL DASHBOARD (Step 2)")
print("="*60)

# 1. INJECT /stats API ENDPOINT INTO main.py
print("\n[1/3] Injecting CEO Stats API into main.py...")
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

STATS_EP = """

@app.get("/api/v1/dashboard/stats")
def ceo_stats_endpoint():
    from app.core.database import SessionLocal
    from app.models.product import Product
    db = SessionLocal()
    try:
        prods = db.query(Product).all()
        total = sum(float(p.price or 0) for p in prods)
        cats = {"Luxury":0, "SUVs":0, "Sedans":0, "Trucks":0}
        for p in prods:
            n = str(p.name).lower()
            if any(x in n for x in ["lexus","benz","bmw","porsche","range","gtr"]): cats["Luxury"]+=1
            elif any(x in n for x in ["suv","highlander","rx3","ml3","pajero","escalade","venza"]): cats["SUVs"]+=1
            elif any(x in n for x in ["truck","bus","van","sienna","trailer"]): cats["Trucks"]+=1
            else: cats["Sedans"]+=1
        return {"total_value": total, "total_cars": len(prods), "categories": cats, "commission": total*0.05}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
"""

if '"/api/v1/dashboard/stats"' not in mc:
    # Inject before the final 'if __name__' or at the very end
    if 'if __name__' in mc:
        mc = mc.replace('if __name__', STATS_EP + '\nif __name__')
    else:
        mc += STATS_EP
    print("✅ /stats API endpoint added!")
else:
    print("ℹ️ /stats API already exists.")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

# 2. INJECT CEO DASHBOARD UI INTO V4 DASHBOARD (agents_api.py)
print("\n[2/3] Injecting CEO Dashboard UI into V4 Dashboard...")
url2 = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as r:
    code = r.read().decode()

STATS_UI = """
<a href="#" onclick="openStats();return false;" style="position:fixed;bottom:90px;right:16px;background:linear-gradient(135deg,#F59E0B,#D97706);color:#fff;padding:12px 18px;border-radius:50px;font-weight:900;box-shadow:0 8px 18px rgba(245,158,11,.4);z-index:999;text-decoration:none">📊 CEO Stats</a>
<div id="ceoModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:1000;padding:20px;overflow-y:auto">
 <div style="max-width:600px;margin:0 auto;background:#0F172A;border:1px solid #334155;border-radius:20px;padding:20px;color:#fff">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><h2 style="margin:0;color:#F59E0B">📊 CEO Dashboard</h2><button onclick="document.getElementById('ceoModal').style.display='none'" style="background:#EF4444;color:#fff;border:none;padding:8px 14px;border-radius:8px;font-weight:800">Close</button></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
   <div style="background:#1E293B;padding:14px;border-radius:12px;text-align:center"><p style="margin:0;font-size:12px;color:#94A3B8">Cars in Stock</p><h3 id="statCars" style="margin:6px 0 0;color:#10B981">0</h3></div>
   <div style="background:#1E293B;padding:14px;border-radius:12px;text-align:center"><p style="margin:0;font-size:12px;color:#94A3B8">Inventory Value</p><h3 id="statVal" style="margin:6px 0 0;color:#10B981">₦0</h3></div>
   <div style="background:#1E293B;padding:14px;border-radius:12px;text-align:center;grid-column:span 2"><p style="margin:0;font-size:12px;color:#94A3B8">Potential 5% Commission</p><h3 id="statComm" style="margin:6px 0 0;color:#F59E0B">₦0</h3></div>
  </div>
  <canvas id="catChart" style="background:#1E293B;border-radius:12px;padding:10px;max-height:260px"></canvas>
 </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
async function openStats(){document.getElementById('ceoModal').style.display='block';try{var r=await fetch('/api/v1/dashboard/stats');var d=await r.json();if(d.error){alert(d.error);return;}document.getElementById('statCars').innerText=d.total_cars;document.getElementById('statVal').innerText='₦'+Number(d.total_value).toLocaleString();document.getElementById('statComm').innerText='₦'+Number(d.commission).toLocaleString();var ctx=document.getElementById('catChart').getContext('2d');if(window.myChart)window.myChart.destroy();window.myChart=new Chart(ctx,{type:'doughnut',data:{labels:Object.keys(d.categories),datasets:[{data:Object.values(d.categories),backgroundColor:['#10B981','#3B82F6','#F59E0B','#EF4444']}]},options:{plugins:{legend:{labels:{color:'#fff'}}}}});}catch(e){alert('Stats failed: '+e.message);}}
</script>
"""

if 'id="ceoModal"' not in code:
    # Inject before the first </body> tag in the V4 HTML template
    if '</body>' in code:
        code = code.replace('</body>', STATS_UI + '\n</body>', 1)
        print("✅ CEO Dashboard UI injected into V4 Dashboard!")
    else:
        code += STATS_UI
        print("✅ CEO Dashboard UI appended!")
else:
    print("ℹ️ CEO Dashboard UI already exists.")

with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)

# 3. PUSH TO VERCEL
print("\n[3/3] Pushing CEO Dashboard to Vercel...")
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "CEO Dashboard: Financial Stats + Chart.js"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to deploy...")
time.sleep(90)

print("\n🔍 Verifying CEO Stats API...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/stats", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
        if "total_cars" in data:
            print("✅ ✅ ✅ CEO STATS API IS LIVE!")
            print(f"   📊 {data['total_cars']} cars | ₦{data['total_value']:,.0f} value | ₦{data['commission']:,.0f} commission")
            print("\n👉 Open your V4 Dashboard and tap the orange '📊 CEO Stats' button:")
            print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/v4-dashboard")
        else:
            print("⚠️ API responded but data missing:", data)
except Exception as e:
    print("❌ Error checking stats:", e)
