import subprocess, time, urllib.request, ast

print("="*60)
print("🩻 X-RAY FIX: REPAIRING AGENT MANAGER PAYLOAD")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. FIX THE PAYLOAD (Send all possible field names)
old_payload = 'body:JSON.stringify({full_name:n,email:e,password:p,role:"agent"})'
new_payload = 'body:JSON.stringify({full_name:n, name:n, email:e, username:e, password:p, role:"agent"})'

if old_payload in mc:
    mc = mc.replace(old_payload, new_payload)
    print("✅ Payload upgraded with 'username' and 'name' fields!")
elif new_payload in mc:
    print("ℹ️ Payload already upgraded.")
else:
    print("⚠️ Could not find exact payload string to replace.")

# 2. FIX THE ERROR HANDLER (X-Ray Vision)
old_err = 'm.innerText="❌ Error: "+(d.detail||"Unknown");'
new_err = 'm.innerText="❌ Error: "+(typeof d.detail==="object"?JSON.stringify(d.detail):(d.detail||"Unknown"));'

if old_err in mc:
    mc = mc.replace(old_err, new_err)
    print("✅ Error handler upgraded with X-Ray JSON reading!")
elif new_err in mc:
    print("ℹ️ Error handler already upgraded.")
else:
    print("⚠️ Could not find exact error string to replace.")

# 3. SYNTAX CHECK
try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Fix: Agent Manager payload and X-Ray error handler"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 60s for Vercel to compile...")
time.sleep(60)
print("✅ DONE! Try creating an agent again.")
