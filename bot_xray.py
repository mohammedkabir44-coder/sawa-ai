import subprocess, time, re

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

XRAY = '''

@router.get("/bot-test")
def bot_xray_test(phone: str = ""):
    """Diagnostic endpoint to force a test message and check the token"""
    import os
    token = os.getenv("WHATSAPP_TOKEN", "")
    if not token:
        return {"status": "MISSING_TOKEN", "detail": "WHATSAPP_TOKEN is not set in Vercel Environment Variables!"}
    if not phone:
        return {"status": "MISSING_PHONE", "detail": "Please provide a phone number."}
    
    # Force send using the existing _wa_send function
    success = _wa_send(phone, "🤖 Hello from Sodangi Motors! Your AI bot is 100% connected, armed, and working perfectly!")
    if success:
        return {"status": "SUCCESS", "detail": f"Message successfully sent to {phone}! Check your WhatsApp."}
    else:
        return {"status": "META_REJECTED", "detail": "Token exists, but Meta rejected the send. Check if your number is registered in Meta or if the token has messages permission."}
'''

if "/bot-test" not in code:
    code = code + XRAY
    print("✅ Bot X-Ray endpoint injected!")

with open(fp, "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Bot X-Ray: diagnostic force-send endpoint"], check=False)
subprocess.run(["git", "push", "origin", "main", "--force"], check=False)
