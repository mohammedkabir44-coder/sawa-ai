import subprocess, time, urllib.request, json

print("="*60)
print("🧠 AI BOT DIAGNOSTIC X-RAY")
print("="*60)

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

DIAG = """

@router.get("/bot-diagnose")
def bot_diagnose():
    import os, traceback
    out = {}
    api_key = os.getenv("OPENAI_API_KEY", "NOT SET")
    out["api_key_preview"] = api_key[:15] + "..." if len(api_key) > 15 else api_key
    
    try:
        import openai
        out["openai_installed"] = True
        try:
            out["openai_version"] = openai.__version__
        except:
            pass
    except Exception as e:
        out["openai_installed"] = False
        out["openai_error"] = str(e)
        return out

    try:
        client = openai.OpenAI(api_key=api_key)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        out["ai_test"] = "SUCCESS: " + res.choices[0].message.content
    except Exception as e:
        out["ai_test"] = "FAILED"
        out["ai_error"] = str(e)
        
    return out
"""

if "/bot-diagnose" not in code:
    code += DIAG
    with open(fp, "w", encoding="utf-8") as f:
        f.write(code)
    print("✅ Diagnostic endpoint injected.")
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Add bot-diagnose endpoint"])
    subprocess.run(["git", "push", "origin", "main", "--force"])
    print("⏳ Waiting 60s for Vercel...")
    time.sleep(60)
else:
    print("ℹ️ Diagnostic endpoint already exists.")

print("\n🔍 Running AI Diagnostic...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/bot-diagnose", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        print("\n" + "="*60)
        print("📋 AI BRAIN DIAGNOSIS:")
        print("="*60)
        print(body)
        print("="*60)
except Exception as e:
    print("❌ Failed to reach diagnostic endpoint:", e)
