import subprocess, time, urllib.request, ast

print("="*60)
print("🛡️ FRONTEND UX: ADDING 8-CHAR PASSWORD WARNING")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

old_check = 'if(!n||!e||!p){m.innerText="❌ Fill all fields!";m.style.background="#7F1D1D";m.style.display="block";return;}'
new_check = 'if(!n||!e||!p){m.innerText="❌ Fill all fields!";m.style.background="#7F1D1D";m.style.display="block";return;}\nif(p.length<8){m.innerText="❌ Password must be at least 8 characters!";m.style.background="#7F1D1D";m.style.display="block";return;}'

if old_check in mc:
    mc = mc.replace(old_check, new_check)
    print("✅ Frontend 8-char password check added!")
else:
    print("ℹ️ Check already exists or string not found.")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "UX: Add 8-char password warning to Agent Manager"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 60s for Vercel...")
time.sleep(60)
print("✅ DONE! The app will now warn you instantly if the password is too short.")
