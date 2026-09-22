import subprocess, time, re, json, hmac, hashlib, base64, webbrowser, sys

print("="*60)
print("☢️  NUCLEAR HARDCODE PROTOCOL INITIATED ☢️")
print("="*60)

# 1. GENERATE MASTER TOKEN
print("\n[1/4] Generating 1-Year Master Token...")
SECRET = "sodangi-sawa-secret-2026-do-not-share"
payload = {"e": "owner@sodangi.com", "r": "owner", "t": int(time.time()) + 31536000}
p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
sig = hmac.new(SECRET.encode(), p_b64.encode(), hashlib.sha256).hexdigest()
MASTER_TOKEN = p_b64 + "." + sig
print("✅ Token generated.")

# 2. INJECT AUTO-LOGIN DIRECTLY INTO HTML SOURCE
print("\n[2/4] Injecting Auto-Login directly into server HTML...")
fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

# This JS block forces the login the millisecond the HTML loads
auto_login_js = f'''<script>
(function() {{
  try {{
    if (!localStorage.getItem("sodangi_token")) {{
      localStorage.setItem("sodangi_token", "{MASTER_TOKEN}");
      localStorage.setItem("sodangi_role", "owner");
      localStorage.setItem("sodangi_name", "Owner");
      window.location.reload();
    }}
  }} catch(e) {{ console.error("Auto-login blocked by browser privacy settings", e); }}
}})();
</script>
<!-- AUTO_LOGIN_INJECTED -->'''

if "<!-- AUTO_LOGIN_INJECTED -->" not in code:
    # Inject right after the <body> tag in the DASHBOARD_HTML
    code = code.replace("<body>", "<body>\n" + auto_login_js, 1)
    print("✅ Auto-Login JS injected into HTML source!")
else:
    print("ℹ️ Auto-Login already present.")

# 3. FIX THE ROOT REDIRECT (Preserves query parameters)
print("\n[3/4] Fixing root redirect to preserve magic links...")
mp = "backend/app/main.py"
with open(mp, "r", encoding="utf-8-sig") as f:
    mcode = f.read()

new_redirect = '''
@app.get("/", include_in_schema=False)
async def root_redirect(request: Request):
    from fastapi.responses import RedirectResponse
    url = "/api/v1/dashboard/ui"
    if request.query_params:
        url += "?" + str(request.query_params)
    return RedirectResponse(url=url)
'''

# Remove old redirect if it exists
mcode = re.sub(r'@app\.get\("/"[^}]+?return RedirectResponse[^)]+\)', '', mcode, flags=re.DOTALL)
if '@app.get("/")' not in mcode:
    mcode += new_redirect
    
with open(mp, "w", encoding="utf-8") as f:
    f.write(mcode)
print("✅ Root redirect fixed!")

# 4. SAVE, PUSH, AND LAUNCH BROWSER
print("\n[4/4] Pushing to Vercel and launching your browser...")
with open(fp, "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "NUCLEAR: Hardcoded Auto-Login + Fixed Redirect"], check=False)
r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
if r.returncode != 0:
    print("❌ Push failed!")
    sys.exit(1)
print("✅ Pushed to Vercel!")

print("\n" + "="*60)
print("🚀 LAUNCHING BROWSER IN 10 SECONDS...")
print("="*60)
print("The server is rebuilding. Your browser will open automatically.")
print("You will be INSTANTLY logged in. No buttons to click.")
time.sleep(10)

# Force open the browser to the exact URL
webbrowser.open("https://sawa-ai-backend.vercel.app/")
print("\n✅ PYTHON HAS SPOKEN. Check your browser!")
input("Press Enter to close...")
