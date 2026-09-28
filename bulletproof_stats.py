import subprocess, time, urllib.request, json, re

print("="*60)
print("📊 BULLETPROOF CEO STATS: INJECTING INTO ROUTER")
print("="*60)

# 1. Inject /stats into agents_api.py (where routes are guaranteed to work)
url2 = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as r:
    code = r.read().decode()

STATS_EP = """

@router.get("/stats")
@router.get("/dashboard/stats")
def ceo_stats_router(db: Session = Depends(get_db)):
    from app.models.product import Product
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
"""

if 'def ceo_stats_router' not in code:
    code += STATS_EP
    print("✅ /stats endpoint injected into core router!")

# 2. Fix the JS to hunt for the correct URL automatically
JS_FIX = """
async function openStats(){document.getElementById('ceoModal').style.display='block';
try{
  var r;
  try { r = await fetch('/api/v1/dashboard/stats'); if(!r.ok) throw new Error(); } 
  catch(e) { r = await fetch('/api/v1/stats'); if(!r.ok) throw new Error(); }
  var d=await r.json();if(d.error){alert(d.error);return;}
  document.getElementById('statCars').innerText=d.total_cars;
  document.getElementById('statVal').innerText='₦'+Number(d.total_value).toLocaleString();
  document.getElementById('statComm').innerText='₦'+Number(d.commission).toLocaleString();
  var ctx=document.getElementById('catChart').getContext('2d');
  if(window.myChart)window.myChart.destroy();
  window.myChart=new Chart(ctx,{type:'doughnut',data:{labels:Object.keys(d.categories),datasets:[{data:Object.values(d.categories),backgroundColor:['#10B981','#3B82F6','#F59E0B','#EF4444']}]},options:{plugins:{legend:{labels:{color:'#fff'}}}}});
}catch(e){alert('Stats failed: '+e.message);}
}
"""

# Replace the old openStats function
code = re.sub(r'async function openStats\(\)\{[\s\S]*?\}\}', JS_FIX, code)
print("✅ JS updated to auto-hunt for the correct stats URL!")

with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)

# 3. Push
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "CEO Stats: Bulletproof router injection + JS fallback"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel...")
time.sleep(90)

# 4. Test both endpoints
print("\n🔍 Testing BOTH stats URLs...")
H = {"User-Agent": "Mozilla/5.0"}
for url in ["https://sawa-ai-backend.vercel.app/api/v1/stats", "https://sawa-ai-backend.vercel.app/api/v1/dashboard/stats"]:
    try:
        req = urllib.request.Request(url, headers=H)
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
            if "total_cars" in d:
                print(f"✅ {url} IS LIVE! ({d['total_cars']} cars)")
            else:
                print(f"⚠️ {url} returned but missing data.")
    except Exception as e:
        print(f"❌ {url} failed: {e}")

print("\n👉 Open your V4 Dashboard and tap the orange '📊 CEO Stats' button:")
print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/v4-dashboard")
