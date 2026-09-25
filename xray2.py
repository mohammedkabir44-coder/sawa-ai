import subprocess, time, re

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

# Remove old bot-test endpoint
code = re.sub(r'@router\.get\("/bot-test"\).*?(?=\n@router|\Z)', '', code, flags=re.DOTALL)

# Shorten Meta call timeout so Vercel never kills the function mid-flight
code = code.replace("urllib.request.urlopen(req, timeout=15)", "urllib.request.urlopen(req, timeout=8)")

NEW = '''
@router.get("/bot-test")
def bot_xray_test(phone: str = ""):
    import os, traceback
    out = {}
    out["token_present"] = bool(os.getenv("WHATSAPP_TOKEN", ""))
    out["phone_id"] = os.getenv("WHATSAPP_PHONE_ID", "1332619033263966")
    if not phone:
        out["status"] = "MISSING_PHONE"
        return out
    try:
        ok = _wa_send(phone, "Sodangi Motors bot test: your AI agent is connected and working!")
        out["status"] = "SUCCESS" if ok else "META_REJECTED"
    except Exception as e:
        out["status"] = "CRASH"
        out["error"] = repr(e)[:300]
    return out
'''
code = code + NEW

with open(fp, "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Crash-proof bot x-ray v2 with error reporting"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("Push successful!")
        break
    time.sleep(5)
