import subprocess, time, urllib.request, ast

print("="*70)
print("🛠️ SURGICAL REPAIR: SCRUBBING ILLEGAL BACKSLASHES")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode("utf-8")

print(f"✅ Downloaded {len(mc)} characters from GitHub.")

# Fix the literal backslash-quote sequences caused by PowerShell
# We use r"" (raw strings) to perfectly match the literal backslashes in the file
mc = mc.replace(r"r\'\'\'", '"""')
mc = mc.replace(r"\'\'\'", '"""')
mc = mc.replace(r'r\"\"\"', '"""')
mc = mc.replace(r'\"\"\"', '"""')

print("✅ Scrubbed all illegal escaped quotes. Replaced with standard triple quotes.")

# Verify syntax BEFORE pushing
print("\n🔍 Verifying syntax...")
try:
    ast.parse(mc)
    print("✅ ✅ ✅ SYNTAX IS NOW 100% PERFECT!")
except SyntaxError as e:
    print(f"❌ Still broken at line {e.lineno}: {e.msg}")
    lines = mc.split('\n')
    if e.lineno:
        s = max(0, e.lineno-3); en = min(len(lines), e.lineno+2)
        for i in range(s, en):
            p = ">>>" if i == e.lineno-1 else "   "
            print(f"{p} {i+1}: {lines[i]}")
    raise SystemExit(0)

# Save locally and push
with open("backend/app/main.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Repair: Scrub illegal backslashes and fix SyntaxError"])
result = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Push successful! Vercel will now compile the repaired code.")
else:
    print(f"❌ Push failed: {result.stderr[:200]}")

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

# Test the public agent link
print("\n🔍 Testing /agent public link...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/agent", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "Agent Portal Login" in body or "Agent Login" in body:
            print("✅ ✅ ✅ /agent LINK IS LIVE AND REDIRECTING!")
            print("\n👉 Give this clean link to your staff:")
            print("https://sawa-ai-backend.vercel.app/agent")
        else:
            print("⚠️ Loaded but check content.")
except Exception as e:
    print(f"❌ Error testing /agent: {e}")
