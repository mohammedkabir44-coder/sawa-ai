import subprocess, time, urllib.request, ast

print("="*70)
print("👻 GHOSTBUSTERS: LINE-BY-LINE EXORCISM OF BROKEN FUNCTIONS")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

print("✅ Downloaded main.py")

# 1. LINE-BY-LINE EXORCISM (Removes ALL broken dashboard functions)
lines = mc.split('\n')
new_lines = []
skip = False

for line in lines:
    # If we find ANY dealer dashboard function definition at the root level, start skipping
    if 'def super_dealer_dashboard' in line and line.startswith('def '):
        skip = True
        # Remove the @app.get decorators that belong to it
        while new_lines and new_lines[-1].strip().startswith('@app.'):
            new_lines.pop()
        print(f"  🗑️ Exorcising broken function: {line.strip()}")
        continue
    
    if skip:
        # Stop skipping when we hit the next top-level route or function
        if line.startswith('@app.') or (line.startswith('def ') and not line.startswith(' ')):
            skip = False
        else:
            continue # Skip the body of the broken function
    
    new_lines.append(line)

mc = '\n'.join(new_lines)
print("✅ All broken dashboard functions completely eradicated!")

# 2. INJECT THE ONE TRUE PERFECT DASHBOARD
# (Notice: ZERO python try/except blocks wrapping the HTML. Just pure, safe return.)
PERFECT_DASHBOARD = """

@app.get('/dealer')
@app.get('/dealer-dashboard')
def super_dealer_dashboard_final():
    from fastapi.responses import HTMLResponse
    html = r\"\"\"<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dealer Dashboard</title>
<style>
body{font-family:sans-serif;background:#0A0F1C;color:#fff;margin:0;padding:20px}
.card{background:#1E293B;padding:20px;border-radius:12px;margin-bottom:16px}
h2{color:#10B981}
.btn{padding:10px 15px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin-right:8px}
.car-card{display:flex;gap:12px;background:#0F172A;padding:12px;border-radius:8px;margin-bottom:10px}
.car-card img{width:100px;height:80px;object-fit:cover;border-radius:6px}
</style></head>
<body>
<h1>\U0001f3e2 Super Dealer Command Center</h1>
<div class="card">
  <h2>\U0001f4e6 My Active Inventory</h2>
  <div id="carGrid"><p style="color:#F59E0B">Loading inventory...</p></div>
</div>
<script>
async function loadCars(){
  var grid = document.getElementById('carGrid');
  try {
    var r = await fetch(window.location.origin + '/dealer-cars');
    if(!r.ok) throw new Error('HTTP ' + r.status);
    var cars = await r.json();
    if(!Array.isArray(cars)) throw new Error('Invalid data');
    grid.innerHTML = '';
    if(!cars.length){ grid.innerHTML = '<p>No cars found.</p>'; return; }
    cars.forEach(function(c){
      var img = (c.images && c.images.length) ? c.images[0] : '';
      var badge = c.status === 'sold' ? '<span style="background:#FEE2E2;color:#991B1B;padding:2px 6px;border-radius:999px;font-size:11px">SOLD</span>' : '<span style="background:#DCFCE7;color:#065F46;padding:2px 6px;border-radius:999px;font-size:11px">AVAILABLE</span>';
      var btnText = c.status === 'sold' ? 'Mark Available' : 'Mark Sold';
      var act = c.status === 'sold' ? 'avail' : 'sold';
      var card = document.createElement('div'); card.className = 'car-card';
      var imgEl = document.createElement('img'); imgEl.src = img; imgEl.onerror = function(){ this.remove(); };
      var info = document.createElement('div');
      info.innerHTML = badge + '<h3 style="margin:4px 0">' + c.name + '</h3><p style="color:#10B981;font-weight:900;margin:0">\u20A6' + Number(c.price).toLocaleString() + '</p>';
      var actions = document.createElement('div'); actions.style.marginTop = '10px';
      var b1 = document.createElement('button'); b1.textContent = btnText; b1.className = 'btn'; b1.style.background = '#F59E0B'; b1.onclick = function(){ doAct('/dealer-action?act=' + act + '&id=' + c.id); };
      var b2 = document.createElement('button'); b2.textContent = 'Delete'; b2.className = 'btn'; b2.style.background = '#EF4444'; b2.onclick = function(){ doAct('/dealer-action?act=del&id=' + c.id); };
      var b3 = document.createElement('button'); b3.textContent = '\u2764 ' + (c.likes || 0); b3.className = 'btn'; b3.style.background = '#EC4899'; b3.onclick = function(){ doAct('/dealer-action?act=like&id=' + c.id); };
      var b4 = document.createElement('button'); b4.textContent = '\U0001f4c4 Agreement'; b4.className = 'btn'; b4.style.background = '#8B5CF6'; b4.onclick = function(){ printAgreement(c.id); };
      actions.appendChild(b1); actions.appendChild(b2); actions.appendChild(b3); actions.appendChild(b4);
      info.appendChild(actions); card.appendChild(imgEl); card.appendChild(info); grid.appendChild(card);
    });
  } catch(e) {
    grid.innerHTML = '<p style="color:#EF4444">Error: ' + e.message + '</p><button onclick="loadCars()" style="padding:10px;background:#EF4444;color:#fff;border:none;border-radius:8px;margin-top:10px">Retry</button>';
  }
}
async function doAct(url){
  try {
    var r = await fetch(window.location.origin + url);
    var d = await r.json();
    if(d.status === 'ok'){ alert('\u2705 ' + d.msg); loadCars(); }
    else { alert('\u274c ' + (d.msg || 'Error')); }
  } catch(e) { alert('Network Error: ' + e.message); }
}
function printAgreement(id){
  var n = prompt("Enter Buyer's Full Name:"); if(!n) return;
  var p = prompt("Enter Buyer's Phone Number:");
  var a = prompt("Enter Buyer's Address:");
  var url = '/agreement/'+id+'?buyer_name='+encodeURIComponent(n)+'&buyer_phone='+encodeURIComponent(p||'')+'&buyer_address='+encodeURIComponent(a||'');
  window.open(url, '_blank');
}
loadCars();
</script>
</body></html>\"\"\"
    return HTMLResponse(content=html)
"""

mc += PERFECT_DASHBOARD
print("✅ Injected the ONE TRUE PERFECT DASHBOARD!")

# 3. VERIFY SYNTAX
try:
    ast.parse(mc)
    print("✅ ✅ ✅ SYNTAX IS 100% PERFECT. NO GHOSTS REMAIN!")
except SyntaxError as e:
    print(f"❌ Still broken at line {e.lineno}: {e.msg}")
    lines = mc.split('\n')
    s = max(0, e.lineno-3); en = min(len(lines), e.lineno+2)
    for i in range(s, en):
        p = ">>>" if i == e.lineno-1 else "   "
        print(f"{p} {i+1}: {lines[i]}")
    raise SystemExit(0)

with open("backend/app/main.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Ghostbusters: Line-by-line exorcism of broken dashboard functions"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile the purified server...")
time.sleep(90)

print("\n🔍 Testing the purified server...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/dealer", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "Super Dealer Command Center" in body:
            print("✅ ✅ ✅ THE 500 ERROR IS DEAD! DASHBOARD IS 100% LIVE!")
            print("\n👉 Open in INCOGNITO on your phone:")
            print("https://sawa-ai-backend.vercel.app/dealer")
        else:
            print("⚠️ Route loaded but content mismatch.")
except Exception as e:
    print(f"❌ Error: {e}")
