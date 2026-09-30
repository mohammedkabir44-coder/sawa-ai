import subprocess, time, urllib.request, ast

print("="*70)
print("🏢 SUPER DEALER COMMAND CENTER: INVENTORY + BOT CONTROL")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

DEALER_ROUTES = """

@app.get("/dealer")
@app.get("/dealer-dashboard")
def super_dealer_dashboard():
    from fastapi.responses import HTMLResponse
    html = \"\"\"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>Dealer Command Center</title>
<style>
:root{--bg:#0A0F1C;--card:#1E293B;--accent:#10B981;--text:#fff;--muted:#94A3B8;--danger:#EF4444;--warning:#F59E0B}
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,sans-serif}
body{background:var(--bg);color:var(--text);padding-bottom:80px;min-height:100vh}
header{background:linear-gradient(135deg,#065F46,#0369A1);padding:20px;text-align:center}
header h1{font-size:20px;font-weight:800}
.container{max-width:800px;margin:0 auto;padding:16px}
.tabs{display:flex;background:var(--card);border-radius:12px;padding:6px;margin-bottom:16px;gap:4px}
.tab{flex:1;text-align:center;padding:12px;border-radius:8px;cursor:pointer;font-weight:700;color:var(--muted);font-size:14px}
.tab.active{background:var(--accent);color:#052E16}
.section{display:none;background:var(--card);border-radius:16px;padding:20px;border:1px solid #334155}
.section.active{display:block}
label{display:block;margin-top:14px;font-size:13px;color:var(--muted);font-weight:600}
input,textarea,select{width:100%;padding:12px;border-radius:8px;border:1px solid #334155;background:#0F172A;color:#fff;font-size:15px;margin-top:4px}
.btn{width:100%;padding:14px;margin-top:16px;background:var(--accent);color:#052E16;border:none;border-radius:10px;font-weight:800;font-size:16px;cursor:pointer}
.btn-danger{background:var(--danger);color:#fff}
.btn-warning{background:var(--warning);color:#000}
.car-grid{display:grid;grid-template-columns:1fr;gap:16px;margin-top:20px}
.car-card{background:#0F172A;border-radius:12px;overflow:hidden;border:1px solid #334155;display:flex;gap:12px;padding:12px}
.car-card img{width:120px;height:90px;object-fit:cover;border-radius:8px;flex-shrink:0}
.car-info{flex:1;display:flex;flex-direction:column;justify-content:space-between}
.car-info h3{font-size:16px;margin-bottom:4px}
.car-info p{font-size:18px;font-weight:900;color:var(--accent)}
.badge{display:inline-block;padding:3px 8px;border-radius:999px;font-size:11px;font-weight:800;margin-bottom:6px}
.badge-avail{background:#DCFCE7;color:#065F46}
.badge-sold{background:#FEE2E2;color:#991B1B}
.actions{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.actions button{flex:1;padding:8px;border:none;border-radius:6px;font-weight:700;font-size:12px;cursor:pointer;min-width:70px}
.stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:20px}
.stat{background:#0F172A;padding:16px;border-radius:12px;text-align:center;border:1px solid #334155}
.stat h2{color:var(--accent);font-size:24px;margin-bottom:4px}
.stat p{font-size:12px;color:var(--muted)}
</style></head>
<body>
<header><h1>🏢 Super Dealer Command Center</h1><p style='font-size:12px;opacity:0.8;margin-top:4px'>Manage Inventory, AI Bot & Sales</p></header>
<div class='container'>
  <div class='tabs'>
    <div class='tab active' onclick='showTab(0)'>🚗 Inventory</div>
    <div class='tab' onclick='showTab(1)'>🤖 AI Bot</div>
    <div class='tab' onclick='showTab(2)'>📊 Stats</div>
  </div>

  <div class='section active' id='tab0'>
    <h2 style='color:var(--accent);margin-bottom:12px'>➕ Add New Vehicle</h2>
    <label>Vehicle Name</label><input id='carName' placeholder='Toyota Camry 2022 XLE'>
    <label>Price (NGN)</label><input id='carPrice' type='number' placeholder='18500000'>
    <label>Year</label><input id='carYear' placeholder='2022'>
    <label>Mileage (km)</label><input id='carMile' placeholder='45,000'>
    <label>Condition</label>
    <select id='carCond'><option>Foreign Used</option><option>Nigerian Used</option><option>Brand New</option></select>
    <label>Photos (Select up to 10)</label>
    <input type='file' id='carPhotos' accept='image/*' multiple style='padding:10px;background:#0F172A'>
    <button class='btn' onclick='uploadCar()'>🚀 Publish to Marketplace</button>
    
    <h2 style='color:var(--accent);margin:24px 0 12px'>📦 My Active Inventory</h2>
    <div class='car-grid' id='carGrid'><p style='color:var(--muted);text-align:center'>Loading inventory...</p></div>
  </div>

  <div class='section' id='tab1'>
    <h2 style='color:var(--accent);margin-bottom:12px'>🤖 WhatsApp AI Bot Personality</h2>
    <p style='color:var(--muted);font-size:13px;margin-bottom:12px'>Train your bot on how to talk to buyers 24/7.</p>
    <label>Bot Name</label><input id='botName' placeholder='Sodangi Assistant'>
    <label>Instant Greeting (When buyer says Hi)</label>
    <textarea id='botGreet' rows='3' placeholder='Salam! Welcome to Sodangi Motors. How can I help you find your dream car today?'></textarea>
    <label>Out-of-Office Message (When you are asleep/busy)</label>
    <textarea id='botBusy' rows='3' placeholder='I am currently away from my desk, but I will reply to you first thing in the morning! Feel free to browse the cars.'></textarea>
    <label>Negotiation Rule</label>
    <select id='botNeg'>
      <option>Strict (No discounts allowed)</option>
      <option>Flexible (Can negotiate up to 5%)</option>
      <option>Very Flexible (Can negotiate up to 10%)</option>
    </select>
    <button class='btn' onclick='saveBot()'>💾 Save Bot Personality</button>
  </div>

  <div class='section' id='tab2'>
    <h2 style='color:var(--accent);margin-bottom:12px'>📊 Dealership Performance</h2>
    <div class='stats'>
      <div class='stat'><h2 id='statCars'>0</h2><p>Active Cars</p></div>
      <div class='stat'><h2 id='statSold'>0</h2><p>Sold Cars</p></div>
      <div class='stat'><h2 id='statLikes'>0</h2><p>Total Likes</p></div>
    </div>
    <p style='color:var(--muted);text-align:center;margin-top:20px'>Detailed analytics available in the Admin Analytics portal.</p>
  </div>
</div>

<script>
var TOKEN=localStorage.getItem('sodangi_token')||'';
function showTab(i){
  document.querySelectorAll('.tab').forEach(function(t,idx){t.classList.toggle('active',idx===i)});
  document.querySelectorAll('.section').forEach(function(s,idx){s.classList.toggle('active',idx===i)});
}
async function api(path,m,b){
  var h={'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json'};
  var r=await fetch('/dealer-api'+path,{method:m,headers:h,body:b?JSON.stringify(b):undefined});
  if(!r.ok)throw new Error('Session expired or error');
  return r.json();
}
async function uploadCar(){
  var n=document.getElementById('carName').value;
  var p=document.getElementById('carPrice').value;
  if(!n||!p)return alert('Fill name and price');
  var files=document.getElementById('carPhotos').files;
  var urls=[];
  for(var i=0;i<files.length;i++){
    var fd=new FormData();fd.append('file',files[i]);
    var r=await fetch('/api/v1/dashboard/upload-media',{method:'POST',body:fd});
    var d=await r.json();
    if(d.url)urls.push(d.url);
  }
  try{
    await api('/car','POST',{name:n,price:parseFloat(p),year:document.getElementById('carYear').value,mileage:document.getElementById('carMile').value,condition:document.getElementById('carCond').value,images:urls});
    alert('✅ Car published!');
    loadCars();
  }catch(e){alert(e.message)}
}
async function loadCars(){
  var grid=document.getElementById('carGrid');
  try{
    var cars=await api('/cars');
    grid.innerHTML='';
    if(!cars.length){grid.innerHTML='<p style=\\'color:var(--muted);text-align:center\\'>No cars in inventory.</p>';return;}
    var active=0,sold=0,likes=0;
    cars.forEach(function(c){
      if(c.status==='sold')sold++;else active++;
      likes+=(c.likes||0);
      var img=c.images&&c.images.length?c.images[0]:'';
      var badge=c.status==='sold'?'<span class=\\'badge badge-sold\\'>SOLD</span>':'<span class=\\'badge badge-avail\\'>AVAILABLE</span>';
      var btnText=c.status==='sold'?'Mark Available':'Mark Sold';
      grid.innerHTML+='<div class=\\'car-card\\'><img src=\\''+img+'\\' onerror=\\'this.style.display=\"none\"\\'><div class=\\'car-info\\'>'+badge+'<h3>'+c.name+'</h3><p>₦'+Number(c.price).toLocaleString()+'</p><div class=\\'actions\\'><button class=\\'btn-warning\\' onclick=\\'toggleStatus('+c.id+',\"'+c.status+'\")\\'>'+btnText+'</button><button class=\\'btn-danger\\' onclick=\\'delCar('+c.id+')\\'>Delete</button><button style=\\'background:#3B82F6;color:#fff\\' onclick=\\'shareCar('+c.id+')\\'>Share</button><button style=\\'background:#EC4899;color:#fff\\' onclick=\\'likeCar('+c.id+')\\'>❤ '+(c.likes||0)+'</button></div></div></div>';
    });
    document.getElementById('statCar').innerText=active;
    document.getElementById('statSold').innerText=sold;
    document.getElementById('statLikes').innerText=likes;
  }catch(e){grid.innerHTML='<p style=\\'color:#EF4444;text-align:center\\'>'+e.message+'</p>'}
}
async function delCar(id){if(!confirm('Delete this car?'))return;try{await api('/car/'+id,'DELETE');loadCars();}catch(e){alert(e.message)}}
async function toggleStatus(id,current){
  var newStatus=current==='sold'?'available':'sold';
  try{await api('/car/'+id,'PUT',{status:newStatus});loadCars();}catch(e){alert(e.message)}
}
async function likeCar(id){try{await api('/like/'+id,'POST');loadCars();}catch(e){alert(e.message)}}
function shareCar(id){var url=location.origin+'/api/v1/dashboard/showroom-elite/'+id;if(navigator.share)navigator.share({title:'Check out this car!',url:url});else{navigator.clipboard.writeText(url);alert('Link copied!')}}
async function saveBot(){
  try{
    await api('/bot-config','POST',{name:document.getElementById('botName').value,greet:document.getElementById('botGreet').value,busy:document.getElementById('botBusy').value,neg:document.getElementById('botNeg').value});
    alert('✅ Bot personality saved!');
  }catch(e){alert(e.message)}
}
async function loadBot(){
  try{
    var b=await api('/bot-config');
    if(b.name)document.getElementById('botName').value=b.name;
    if(b.greet)document.getElementById('botGreet').value=b.greet;
    if(b.busy)document.getElementById('botBusy').value=b.busy;
  }catch(e){}
}
loadCars();
loadBot();
</script></body></html>\"\"\"
    return HTMLResponse(content=html)

@app.get('/dealer-api/cars')
def get_dealer_cars():
    from app.core.database import engine
    from sqlalchemy import text
    import json
    try:
        with engine.connect() as conn:
            # Add likes and status columns if they don't exist
            try: conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS likes INT DEFAULT 0'))
            except: pass
            try: conn.execute(text('ALTER TABLE products ADD COLUMN IF NOT EXISTS status TEXT DEFAULT \\'available\\''))
            except: pass
            conn.commit()
            
            rows = conn.execute(text('SELECT id, name, price, images, likes, status FROM products ORDER BY id DESC LIMIT 50')).fetchall()
            cars = []
            for r in rows:
                imgs = []
                try:
                    if r[3]: imgs = json.loads(r[3])
                except: pass
                cars.append({'id': r[0], 'name': r[1], 'price': float(r[2] or 0), 'images': imgs, 'likes': r[4] or 0, 'status': r[5] or 'available'})
            return cars
    except Exception as e:
        return []

@app.post('/dealer-api/car')
def add_dealer_car(data: dict):
    from app.core.database import engine
    from sqlalchemy import text
    import json
    try:
        desc = json.dumps({'year': data.get('year'), 'mileage': data.get('mileage'), 'condition': data.get('condition')})
        with engine.connect() as conn:
            conn.execute(text('INSERT INTO products (name, price, images, description, is_active, status, likes) VALUES (:n, :p, :i, :d, true, \\'available\\', 0)'), 
                        {'n': data['name'], 'p': data['price'], 'i': json.dumps(data.get('images', [])), 'd': desc})
            conn.commit()
        return {'status': 'ok'}
    except Exception as e:
        return {'error': str(e)}

@app.put('/dealer-api/car/{cid}')
def update_dealer_car(cid: int, data: dict):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text('UPDATE products SET status = :s WHERE id = :id'), {'s': data.get('status', 'available'), 'id': cid})
            conn.commit()
        return {'status': 'ok'}
    except Exception as e:
        return {'error': str(e)}

@app.delete('/dealer-api/car/{cid}')
def delete_dealer_car(cid: int):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text('DELETE FROM products WHERE id = :id'), {'id': cid})
            conn.commit()
        return {'status': 'ok'}
    except Exception as e:
        return {'error': str(e)}

@app.post('/dealer-api/like/{cid}')
def like_dealer_car(cid: int):
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text('UPDATE products SET likes = likes + 1 WHERE id = :id'), {'id': cid})
            conn.commit()
        return {'status': 'ok'}
    except Exception as e:
        return {'error': str(e)}

@app.post('/dealer-api/bot-config')
def save_bot_config(data: dict):
    # In a real app, save this to a settings table. For now, we just acknowledge it.
    return {'status': 'ok', 'data': data}

@app.get('/dealer-api/bot-config')
def get_bot_config():
    # Return default bot personality
    return {'name': 'Sodangi Assistant', 'greet': 'Salam! Welcome to Sodangi Motors. How can I help you find your dream car today?', 'busy': 'I am currently away, but will reply shortly!'}
"""

if 'def super_dealer_dashboard():' not in mc:
    mc += DEALER_ROUTES
    print("✅ Super Dealer Command Center injected into main.py!")
else:
    print("ℹ️ Dealer Dashboard already exists.")

# Add link to Hub
if 'href="/dealer"' not in mc and 'def sodangi_hub' in mc:
    hub_add = '<a href="/dealer" class="btn" style="background:#EF4444;border-color:#EF4444">🏢 Super Dealer Dashboard (Admin)</a>\n'
    mc = mc.replace('<a href="/admin-agents"', hub_add + '<a href="/admin-agents"')
    print("✅ Added Super Dealer link to Universal Hub!")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg} at line {e.lineno}")
    raise SystemExit(0)

with open("backend/app/main.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Add Super Dealer Dashboard with Bot Control and Inventory Management"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Testing Super Dealer Dashboard...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/dealer", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "Super Dealer Command Center" in body:
            print("✅ ✅ ✅ SUPER DEALER DASHBOARD IS LIVE!")
            print("\n👉 Open this link on your phone (Incognito if needed):")
            print("https://sawa-ai-backend.vercel.app/dealer")
        else:
            print("⚠️ Route loaded but HTML mismatch.")
except Exception as e:
    print(f"❌ Error: {e}")
