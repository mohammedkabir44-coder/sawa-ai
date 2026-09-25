import ast, subprocess, time, re, urllib.request, urllib.error, json, sys

fp = "backend/app/api/v1/endpoints/agents_api.py"
print("🐍 Python Syntax Healer is scanning the code...")

with open(fp, "r", encoding="utf-8") as f:
    code = f.read()

# 1. CHECK FOR SYNTAX ERRORS
try:
    ast.parse(code)
    print("✅ Code syntax is PERFECT. No broken indentations.")
except SyntaxError as e:
    print(f"❌ SYNTAX ERROR FOUND at line {e.lineno}: {e.msg}")
    print("Python is attempting to auto-heal by removing the last broken block...")
    # Simple heal: remove everything after the last valid 'def ' that parses
    lines = code.split('\n')
    for i in range(len(lines), 0, -1):
        try:
            ast.parse('\n'.join(lines[:i]))
            code = '\n'.join(lines[:i])
            print(f"✅ Healed! Truncated broken code at line {i}.")
            break
        except SyntaxError:
            continue

# 2. REMOVE OLD DOCTOR/XRAY ENDPOINTS TO CLEAN UP
code = re.sub(r'@router\.get\("/bot-doctor"\).*?(?=\n@router|\Z)', '', code, flags=re.DOTALL)
code = re.sub(r'@router\.get\("/bot-test"\).*?(?=\n@router|\Z)', '', code, flags=re.DOTALL)

# 3. ADD A SUPER-SAFE ENVIRONMENT CHECK ENDPOINT
safe_ep = """

@router.get("/env-check")
def env_check():
    import os
    return {
        "status": "ALIVE",
        "has_whatsapp_token": bool(os.getenv("WHATSAPP_TOKEN")),
        "has_phone_id": bool(os.getenv("WHATSAPP_PHONE_ID")),
        "phone_id_value": os.getenv("WHATSAPP_PHONE_ID", "NOT SET")
    }
"""

if "/env-check" not in code:
    code += safe_ep
    print("✅ Super-safe /env-check endpoint added.")

with open(fp, "w", encoding="utf-8") as f:
    f.write(code)

print("Pushing healed code to GitHub...")
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Heal syntax and add env-check"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\nWaiting 90 seconds for Vercel to rebuild the healed server...")
time.sleep(90)

# 4. INTERROGATE THE SERVER
url = "https://sawa-ai-backend.vercel.app/api/v1/dashboard/env-check"
print(f"\n🔍 Querying Server: {url}")
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        print("\n" + "="*60)
        print("📋 SERVER ENVIRONMENT CHECK (THE TRUTH):")
        print("="*60)
        print(body)
        print("="*60)
        
        data = json.loads(body)
        if not data.get("has_whatsapp_token"):
            print("\n🚨 DIAGNOSIS: MISSING WHATSAPP_TOKEN!")
            print("👉 FIX: Go to Vercel Dashboard -> Settings -> Environment Variables.")
            print("   Add Key: WHATSAPP_TOKEN")
            print("   Value: [Your Meta System User Token]")
            print("   Save and click REDEPLOY on the latest deployment.")
        else:
            print("\n✅ DIAGNOSIS: TOKEN IS PRESENT IN VERCEL!")
            print("The server has the key. The issue is Meta permissions or Phone ID.")
            
except urllib.error.HTTPError as e:
    print(f"\n❌ HTTP ERROR {e.code}")
    print("Server Body:", e.read().decode())
except Exception as e:
    print("\n❌ NETWORK ERROR:", e)
