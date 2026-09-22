import subprocess, time, ast, re

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

# ---------- 1. CLEAN TABBED AUTH CARD ----------
NEW_AUTH = '''  <section id="authCard">
    <div class="card">
      <div style="text-align:center;margin-bottom:14px">
        <div style="font-size:22px;font-weight:800;letter-spacing:1px">SODANGI MOTORS</div>
        <div style="color:#94A3B8;font-size:12px;margin-top:4px">Owner & Agent Portal</div>
      </div>
      <div id="googleBtnWrap" style="display:flex;justify-content:center;margin-bottom:12px"><div id="googleBtn"></div></div>
      <div id="authDivider" style="text-align:center;color:#64748B;font-size:12px;margin-bottom:12px">or continue with email</div>
      <div style="display:flex;gap:8px;margin-bottom:14px">
        <button id="tabLoginBtn" class="btn btn-primary" style="margin:0" onclick="showAuth('login')">Sign In</button>
        <button id="tabSignupBtn" class="btn btn-ghost" style="margin:0" onclick="showAuth('signup')">Sign Up</button>
      </div>
      <div id="loginPane">
        <label>Email</label><input id="liEmail" type="email" placeholder="you@email.com">
        <label>Password</label><input id="liPass" type="password" placeholder="********">
        <button class="btn btn-primary" onclick="doLogin()">Sign In</button>
      </div>
      <div id="signupPane" class="hidden">
        <label>Full Name</label><input id="regName" placeholder="Your full name">
        <label>Email</label><input id="regEmail" type="email" placeholder="you@email.com">
        <label>Create Password</label><input id="regPass" type="password" placeholder="Min 6 characters">
        <button class="btn btn-primary" onclick="registerAgent()">Create My Account</button>
      </div>
    </div>
  </section>'''

if 'id="loginPane"' not in code:
    code = re.sub(r'<section id="authCard">[\s\S]*?</section>', NEW_AUTH, code, count=1)
    print("✅ Clean tabbed auth card installed!")

# ---------- 2. TAB SWITCHER + GOOGLE SIGN-IN JS ----------
SOCIAL_JS = '''function showAuth(mode){var lp=document.getElementById("loginPane");var sp=document.getElementById("signupPane");var lb=document.getElementById("tabLoginBtn");var sb=document.getElementById("tabSignupBtn");if(mode==="login"){lp.classList.remove("hidden");sp.classList.add("hidden");lb.className="btn btn-primary";sb.className="btn btn-ghost";}else{sp.classList.remove("hidden");lp.classList.add("hidden");sb.className="btn btn-primary";lb.className="btn btn-ghost";}lb.style.margin="0";sb.style.margin="0";}
async function initSocial(){try{var r=await fetch(API+"/social-config");var c=await r.json();if(c.google_client_id){var s=document.createElement("script");s.src="https://accounts.google.com/gsi/client";s.async=true;s.onload=function(){try{google.accounts.id.initialize({client_id:c.google_client_id,callback:onGoogleCred});google.accounts.id.renderButton(document.getElementById("googleBtn"),{theme:"filled_black",size:"large",width:300,text:"signup_with"});}catch(e){}};document.head.appendChild(s);}else{var w=document.getElementById("googleBtnWrap");if(w)w.style.display="none";var dv=document.getElementById("authDivider");if(dv)dv.style.display="none";}}catch(e){var w2=document.getElementById("googleBtnWrap");if(w2)w2.style.display="none";}}
async function onGoogleCred(resp){try{var r=await fetch(API+"/social-login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({credential:resp.credential})});var d=await r.json();if(d.token){TOKEN=d.token;ROLE=d.role;NAME=d.full_name;localStorage.setItem("sodangi_token",TOKEN);localStorage.setItem("sodangi_role",ROLE);localStorage.setItem("sodangi_name",NAME);enterDash();}else{alert("Google sign-in failed: "+(d.detail||"unknown"));}}catch(e){alert("Google sign-in error: "+e.message);}}
'''
if "showAuth" not in code:
    old_boot = "if(TOKEN){enterDash();}else{loadPublicShowroom();}"
    new_boot = SOCIAL_JS + "if(TOKEN){enterDash();}else{loadPublicShowroom();initSocial();}"
    if old_boot in code:
        code = code.replace(old_boot, new_boot)
    else:
        code = code.replace("if(TOKEN){enterDash();}", SOCIAL_JS + "if(TOKEN){enterDash();}else{loadPublicShowroom();initSocial();}")
    print("✅ Tab switcher + Google sign-in engine injected!")

# ---------- 3. BACKEND: SOCIAL CONFIG + VERIFIED GOOGLE LOGIN ----------
SOCIAL_BACKEND = '''

@router.get("/social-config")
def social_config():
    return {"google_client_id": os.getenv("GOOGLE_CLIENT_ID", "")}

@router.post("/social-login")
def social_login(payload: dict, db: Session = Depends(get_db)):
    import urllib.request as _ur
    cid = os.getenv("GOOGLE_CLIENT_ID", "")
    cred = payload.get("credential", "")
    if not cid or not cred:
        raise HTTPException(status_code=400, detail="Google sign-in not configured yet")
    try:
        with _ur.urlopen("https://oauth2.googleapis.com/tokeninfo?id_token=" + cred, timeout=10) as resp:
            info = json.loads(resp.read().decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    if info.get("aud") != cid:
        raise HTTPException(status_code=401, detail="Google token audience mismatch")
    email = (info.get("email") or "").lower()
    gname = info.get("name") or email.split("@")[0]
    if not email:
        raise HTTPException(status_code=401, detail="No email in Google token")
    Agent.__table__.create(bind=db.get_bind(), checkfirst=True)
    a = db.query(Agent).filter(Agent.email == email).first()
    if not a:
        role = "owner" if db.query(Agent).count() == 0 else "agent"
        a = Agent(full_name=gname, email=email, password_hash=_hash_pw(os.urandom(8).hex()), role=role, is_active=True)
        db.add(a)
        db.commit()
        db.refresh(a)
    return {"status": "success", "token": _make_token(a.email, a.role), "role": a.role, "full_name": a.full_name}
'''
if "/social-login" not in code:
    code = code + SOCIAL_BACKEND
    print("✅ Verified Google login backend injected!")

ast.parse(code)
with open(fp, "w", encoding="utf-8") as f:
    f.write(code)
print("✅ Saved!")

print("Pushing to GitHub...")
subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Clean Front Door: tabbed Sign In/Sign Up + verified Google social login"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ Push successful!")
        break
    print("Push failed attempt " + str(i+1) + ", retrying...")
    time.sleep(5)
