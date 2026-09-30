import subprocess, time, urllib.request, re, ast

print("="*70)
print("💥 NUCLEAR JS PATCH: FORCING INVENTORY TO LOAD")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. REPLACE THE OLD loadCars() FUNCTION WITH THE NUCLEAR VERSION
old_loadcars = """function loadCars(){
  var grid=document.getElementById('carGrid');
  fetch('/dealer-cars').then(function(r){return r.json()}).then(function(cars){"""

new_loadcars = """function loadCars(){
  var grid=document.getElementById('carGrid');
  grid.innerHTML = '<p style="color:#F59E0B;text-align:center">Fetching cars from server...</p>';
  var url = window.location.origin + '/dealer-cars';
  fetch(url).then(function(r){
    if(!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }).then(function(cars){
    if(!Array.isArray(cars)) throw new Error('Invalid data format');"""

if old_loadcars in mc:
    mc = mc.replace(old_loadcars, new_loadcars)
    print("✅ Nuclear fetch injected (replaced old fetch)!")
else:
    print("⚠️ Could not find exact old fetch. Trying regex fallback...")
    mc = re.sub(r"function loadCars\(\)\{[\s\S]*?fetch\('/dealer-cars'\)\.then", 
                "function loadCars(){\n  var grid=document.getElementById('carGrid');\n  grid.innerHTML = '<p style=\"color:#F59E0B;text-align:center\">Fetching cars from server...</p>';\n  var url = window.location.origin + '/dealer-cars';\n  fetch(url).then", mc)
    print("✅ Regex fallback applied!")

# 2. REPLACE THE CATCH BLOCK TO SHOW VISIBLE ERRORS
old_catch = """.catch(function(e){grid.innerHTML='<p style="color:#EF4444">'+e+'</p>'});"""
new_catch = """.catch(function(e){
      grid.innerHTML='<div style="text-align:center;padding:20px"><p style="color:#EF4444;font-weight:bold">Failed to load inventory: ' + e.message + '</p><button onclick="loadCars()" style="margin-top:15px;padding:12px 24px;background:#EF4444;color:#fff;border:none;border-radius:8px;font-weight:bold">🔄 Retry Loading</button></div>';
    });"""

if old_catch in mc:
    mc = mc.replace(old_catch, new_catch)
    print("✅ Visible error screen with Retry button injected!")
else:
    print("⚠️ Could not find exact catch block.")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")
    raise SystemExit(0)

with open("backend/app/main.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Nuclear Fix: Absolute URLs and visible error screen for inventory"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Testing Dealer Dashboard...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/dealer", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "window.location.origin + '/dealer-cars'" in body:
            print("✅ ✅ ✅ NUCLEAR PATCH IS LIVE!")
            print("\n👉 Open on your phone IN AN INCOGNITO WINDOW:")
            print("https://sawa-ai-backend.vercel.app/dealer")
            print("   (If it still fails, it will show a RED ERROR and a RETRY button. Screenshot it!)")
        else:
            print("⚠️ Route loaded but nuclear JS missing.")
except Exception as e:
    print(f"❌ Error: {e}")
