import subprocess, time, json, urllib.request, urllib.error, sys, re

print("="*60)
print("🐍 PYTHON BOT DOCTOR IS RUNNING...")
print("="*60)

# 1. INJECT THE DOCTOR ENDPOINT
fp = "backend/app/api/v1/endpoints/agents_api.py"
try:
    with open(fp, "r", encoding="utf-8") as f: code = f.read()
except Exception as e:
    print("❌ ERROR reading file:", e); sys.exit(1)

# Unique endpoint name to avoid conflicts
new_ep = """
@router.get("/bot-doctor")
def bot_doctor(phone: str = ""):
    import os, json, urllib.request, urllib.error
    tok = os.getenv("WHATSAPP_TOKEN")
    if not tok: return {"status":"MISSING_TOKEN", "fix":"Add WHATSAPP_TOKEN to Vercel Env Vars"}
    pid = os.getenv("WHATSAPP_PHONE_ID", "1332619033263966")
    if not phone: return {"status":"NO_PHONE"}
    
    url = f"https://graph.facebook.com/v18.0/{pid}/messages"
    data = json.dumps({"messaging_product":"whatsapp","to":phone,"type":"text","text":{"body":"Sodangi Bot Doctor Test V3"}}).encode()
    req = urllib.request.Request(url, data=data, headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json"}, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return {"status":"SUCCESS", "meta_response":r.read().decode()}
    except urllib.error.HTTPError as e:
        return {"status":"META_REJECTED", "error_code":e.code, "error_body":e.read().decode()[:500]}
    except Exception as e:
        return {"status":"CRASH", "error":str(e)}
"""

if "/bot-doctor" not in code:
    code += new_ep
    with open(fp, "w", encoding="utf-8") as f: f.write(code)
    print("✅ Doctor endpoint injected.")
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Bot Doctor V3"])
    subprocess.run(["git", "push", "origin", "main", "--force"])
    print("✅ Pushed to GitHub. Waiting 90s for Vercel...")
    time.sleep(90)
else:
    print("ℹ️ Doctor endpoint already exists. Skipping push.")

# 2. INTERROGATE THE SERVER WITH PYTHON (Bypasses PowerShell errors)
url = "https://sawa-ai-backend.vercel.app/api/v1/dashboard/bot-doctor?phone=2348142969979"
print(f"\n🔍 Querying Server: {url}")
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        print("\n" + "="*60)
        print("📋 SERVER RAW RESPONSE (THE TRUTH):")
        print("="*60)
        print(body)
        print("="*60)
        print("\n👉 READ THE 'status' FIELD ABOVE:")
        print("   - 'SUCCESS' = Bot sent the text! Check your phone.")
        print("   - 'MISSING_TOKEN' = You need to add WHATSAPP_TOKEN to Vercel.")
        print("   - 'META_REJECTED' = Meta blocked it (check error_body).")
        print("   - 'CRASH' = Server code error (check error).")
except urllib.error.HTTPError as e:
    print(f"\n❌ HTTP ERROR {e.code}")
    print("Server Body:", e.read().decode())
except Exception as e:
    print("\n❌ NETWORK ERROR:", e)
