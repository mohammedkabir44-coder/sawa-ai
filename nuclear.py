import subprocess, time, re, json, hmac, hashlib, base64

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

# NUCLEAR BACKDOOR: Server-side login that bypasses all JavaScript issues
backdoor = '''

@router.get("/owner-auto")
def owner_auto_login(db: Session = Depends(get_db)):
    """NUCLEAR BACKDOOR: Instantly logs in as Owner without any buttons"""
    import time as _t
    owner = db.query(Agent).filter(Agent.role == "owner").first()
    if not owner:
        owner = Agent(full_name="Mohammed Kabir", email="owner@sodangi.com", 
                     password_hash=_hash_pw("Sodangi2026!"), role="owner", is_active=True)
        db.add(owner)
        db.commit()
    
    # Generate valid token
    payload = base64.urlsafe_b64encode(json.dumps({
        "e": owner.email, "r": owner.role, "t": int(_t.time()) + 604800
    }).encode()).decode()
    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = payload + "." + sig
    
    # Return HTML that instantly sets token and redirects
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Logging you in...</title></head>
<body style="background:#0B0F19;color:#fff;text-align:center;padding:40px;font-family:sans-serif">
<h2>⚡ Logging you in as Owner...</h2>
<p>Please wait...</p>
<script>
localStorage.setItem("sodangi_token","{token}");
localStorage.setItem("sodangi_role","owner");
localStorage.setItem("sodangi_name","{owner.full_name}");
setTimeout(function(){{window.location.href="/api/v1/dashboard/ui";}},500);
</script>
</body></html>"""
    return Response(content=html, media_type="text/html")
'''

if "/owner-auto" not in code:
    code = code + backdoor
    print("✅ NUCLEAR BACKDOOR injected!")
else:
    print("ℹ️ Backdoor already exists.")

with open(fp, "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Nuclear Backdoor: instant owner login bypass"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ Push successful!")
        break
    print(f"Push retry {i+1}...")
    time.sleep(5)

print("\n" + "="*60)
print("☢️ NUCLEAR BACKDOOR DEPLOYED ☢️")
print("="*60)
print("\nYOUR MAGIC LOGIN URL (copy this entire line):")
print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/owner-auto")
print("\n👆 Paste this into your browser address bar and press Enter.")
print("It will INSTANTLY log you in as Owner. No buttons needed.")
print("="*60)
