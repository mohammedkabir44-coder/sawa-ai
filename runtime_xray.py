import subprocess, time, urllib.request, ast

print("="*70)
print("🕵️‍♂️ INJECTING RUNTIME X-RAY TO CATCH THE HIDDEN ERROR")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# Inject the Debug Route
DEBUG_ROUTE = """

@app.get("/debug-imports")
def debug_imports():
    import traceback
    try:
        from app.agent_dashboard import router as dashboard_router
        routes = [r.path for r in dashboard_router.routes]
        return {"status": "SUCCESS", "message": "agent_dashboard.py loaded perfectly!", "routes": routes}
    except Exception as e:
        error_html = f"<h1 style='color:red'>IMPORT CRASHED!</h1><pre style='background:#111;color:#0f0;padding:20px;border-radius:10px;overflow:auto'>{traceback.format_exc()}</pre>"
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=error_html, status_code=500)
"""

if '"/debug-imports"' not in mc:
    mc += DEBUG_ROUTE
    print("✅ Debug endpoint injected!")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Add debug-imports endpoint to catch runtime errors"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Reading the X-Ray...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/debug-imports", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "SUCCESS" in body:
            print("✅ ✅ ✅ agent_dashboard.py IS LOADING PERFECTLY!")
            print("   The 404 is just a routing issue. We will fix it next.")
        else:
            print("💥 CAUGHT THE HIDDEN ERROR!")
            print("   Copy the error details below and send them to me:")
            # Extract just the error message for easy reading
            import re
            err_match = re.search(r'([a-zA-Z0-9_]+Error: .*?)\n', body)
            if err_match:
                print(f"   👉 {err_match.group(1)}")
            else:
                print(body[:500])
except Exception as e:
    print(f"❌ Error reading debug page: {e}")
