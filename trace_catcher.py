import subprocess, time, urllib.request, re

print("="*70)
print("🕵️‍♂️ PYTHON TRACEBACK CATCHER: EXPOSING THE 500 ERROR")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# Find the dealer route and wrap it in try/except
target = "def super_dealer_dashboard_bp():"
if target in mc:
    idx = mc.find(target)
    # Find the return HTMLResponse after it
    ret_idx = mc.find("return HTMLResponse(content=html)", idx)
    
    if ret_idx != -1:
        html_start = mc.find('html = """', idx)
        if html_start != -1:
            # Inject try block before html = """
            # We indent the html assignment and return statement
            old_body = mc[html_start:ret_idx + len("return HTMLResponse(content=html)")]
            
            new_body = "    try:\n        " + old_body.replace("\n", "\n        ") + "\n    except Exception as e:\n        import traceback\n        from fastapi.responses import HTMLResponse\n        return HTMLResponse('<h1>PYTHON CRASH</h1><pre style=\"background:#111;color:#0f0;padding:20px;overflow:auto\">' + traceback.format_exc() + '</pre>')\n"
            
            mc = mc[:html_start] + new_body + mc[ret_idx + len("return HTMLResponse(content=html)"):]
            print("✅ Injected Python Traceback Catcher into /dealer route!")
        else:
            print("⚠️ Could not find html = \"\"\" start.")
    else:
        print("⚠️ Could not find return statement.")
else:
    print("⚠️ Dealer route not found.")

with open("backend/app/main.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Diag: Add traceback catcher to dealer route"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Fetching the error message...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/dealer", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "PYTHON CRASH" in body:
            print("💥 CAUGHT THE PYTHON ERROR!")
            import re
            trace = re.search(r'<pre[^>]*>(.*?)</pre>', body, re.DOTALL)
            if trace:
                print("\n" + "="*70)
                print("EXACT PYTHON ERROR (Paste this to me!):")
                print("="*70)
                print(trace.group(1)[:1500])
                print("="*70)
        elif "Super Dealer" in body:
            print("✅ Wait, the page loaded successfully! The 500 was a temporary glitch.")
        else:
            print("⚠️ Unknown response:")
            print(body[:500])
except Exception as e:
    print(f"❌ Error fetching page: {e}")
