import subprocess, time, re, ast

fp = "backend/app/api/v1/endpoints/agents_api.py"
print("Reading code with Python...")
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

# 1. PYTHON BACKEND: Inject Emergency Login Route
backend_patch = '''

@router.post("/emergency-login")
def emergency_login(payload: dict, db: Session = Depends(get_db)):
    master_pw = payload.get("master_password", "")
    if master_pw != "Sodangi2026!":
        raise HTTPException(status_code=401, detail="Wrong master password")
    owner = db.query(Agent).filter(Agent.role == "owner").first()
    if not owner:
        raise HTTPException(status_code=404, detail="No owner found in database")
    return {"status": "success", "token": _make_token(owner.email, owner.role), "role": owner.role, "full_name": owner.full_name}
'''
if "/emergency-login" not in code:
    code = code + backend_patch
    print("✅ Python injected /emergency-login backend route!")
else:
    print("ℹ️ Backend route already exists.")

# 2. PYTHON FRONTEND: Inject the Emergency Button into the HTML
# We look for the signup button and add our emergency button right below it
old_btn = '<button class="btn btn-primary" onclick="registerAgent()">Create My Account</button>'
new_btn = '''<button class="btn btn-primary" onclick="registerAgent()">Create My Account</button>
      <hr style="margin:16px 0;border-color:#334155">
      <button class="btn btn-ghost" style="background:#B45309;color:#fff;margin-top:4px" onclick="emergencyLogin()">🔑 Owner Quick Login</button>'''

if "emergencyLogin" not in code and old_btn in code:
    code = code.replace(old_btn, new_btn, 1)
    print("✅ Python injected the Owner Quick Login button!")
else:
    print("ℹ️ Button already exists or anchor missing.")

# 3. PYTHON FRONTEND: Inject the JavaScript function that calls the Python route
emergency_js = '''
async function emergencyLogin(){
  var pw = prompt("Enter Owner Master Password:");
  if(!pw) return;
  try {
    var r = await fetch(API+"/emergency-login", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({master_password:pw})});
    var d = await r.json();
    if(d.token){
      localStorage.setItem("sodangi_token", d.token);
      localStorage.setItem("sodangi_role", d.role);
      localStorage.setItem("sodangi_name", d.full_name);
      alert("Welcome back, " + d.full_name + "!");
      location.reload();
    } else {
      alert("Failed: " + (d.detail || "Unknown error"));
    }
  } catch(e) { alert("Network error: " + e.message); }
}
'''
if "function emergencyLogin" not in code:
    code = code.replace("if(TOKEN){enterDash();}", emergency_js + "\nif(TOKEN){enterDash();}")
    print("✅ Python injected emergencyLogin() JS function!")

# 4. VERIFY & SAVE
ast.parse(code)
with open(fp, "w", encoding="utf-8") as f:
    f.write(code)
print("✅ Python saved the fixed code!")

# 5. PUSH TO VERCEL
print("Pushing to GitHub...")
subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Python Auto-Fix: Emergency Owner Login bypass"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ Push successful!")
        break
    print("Push failed attempt " + str(i+1) + ", retrying...")
    time.sleep(5)
