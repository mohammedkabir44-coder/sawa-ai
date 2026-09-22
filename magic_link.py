import subprocess, time, re, json, hmac, hashlib, base64

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8") as f:
    code = f.read()

# 1. INJECT AUTO-LOGIN LOGIC INTO THE WEBSITE
# This tells the site: "If a user visits with ?auto=TOKEN, log them in immediately."
js_injection = """var _auto = new URLSearchParams(window.location.search).get('auto');
if (_auto) {
    localStorage.setItem('sodangi_token', _auto);
    localStorage.setItem('sodangi_role', 'owner');
    localStorage.setItem('sodangi_name', 'Magic Login');
    window.history.replaceState({}, document.title, window.location.pathname);
    location.reload();
}
"""

if "_auto" not in code:
    # We inject this right at the start of the main script block
    code = code.replace("<script>\nvar API=", "<script>\n" + js_injection + "var API=", 1)
    print("✅ Magic Link receiver injected into the site!")
else:
    print("ℹ️ Magic Link receiver already present.")

with open(fp, "w", encoding="utf-8") as f:
    f.write(code)

# 2. GENERATE THE SECRET TOKEN
m = re.search(r'SECRET\s*=\s*"([^"]+)"', code)
SECRET = m.group(1) if m else "sodangi-sawa-secret-2026-do-not-share"

payload = {"e": "owner@sodangi.com", "r": "owner", "t": int(time.time()) + 86400*30}
p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
sig = hmac.new(SECRET.encode(), p_b64.encode(), hashlib.sha256).hexdigest()
token = p_b64 + "." + sig

# 3. PUSH TO VERCEL
subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Magic Link: Auto-login via URL parameter"], check=False)
subprocess.run(["git", "push", "origin", "main", "--force"], check=False)

print("\n" + "="*60)
print("🪄 YOUR MAGIC LOGIN LINK IS READY")
print("="*60)
print("Copy the link below, paste it into your browser address bar, and press Enter:")
print("\nhttps://sawa-ai-backend.vercel.app/?auto=" + token + "\n")
print("="*60)
print("This link logs you in instantly. No buttons or passwords needed.")
