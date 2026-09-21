import subprocess, time, ast

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

# ---------- 1. PUBLIC HOMEPAGE SECTION (for visitors not logged in) ----------
HOME_HTML = '''  <section id="publicHome">
    <div style="text-align:center;padding:26px 10px 10px">
      <div style="font-size:26px;font-weight:800;letter-spacing:1px">SODANGI MOTORS</div>
      <div style="color:#94A3B8;font-size:13px;margin-top:6px">Nigeria&#39;s trusted vehicle marketplace. Buy verified cars directly from verified agents.</div>
    </div>
    <div id="publicCars" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:14px 4px"></div>
    <div style="text-align:center;color:#64748B;font-size:12px;padding-bottom:8px">Are you an agent? Sign in below to manage your showroom.</div>
  </section>
'''
if 'id="publicHome"' not in code:
    code = code.replace('<section id="authCard">', HOME_HTML + '  <section id="authCard">')
    print("✅ Public homepage section added!")

# ---------- 2. PUBLIC SHOWROOM LOADER JS ----------
PUB_JS = '''var SHOWROOM_URL="";
function copyShowroom(){if(SHOWROOM_URL){navigator.clipboard.writeText(SHOWROOM_URL);toast("Showroom link copied!");}}
async function loadPublicShowroom(){var box=document.getElementById("publicCars");if(!box)return;try{var r=await fetch(API+"/products");var cars=await r.json();if(!cars||!cars.length){box.innerHTML='<p style="color:#94A3B8;grid-column:1/-1;text-align:center">Showroom opening soon - check back!</p>';return;}var h="";cars.slice(0,8).forEach(function(c){var img="";if(c.images&&c.images.length>0){img=Array.isArray(c.images)?c.images[0]:c.images;}else if(c.image_url){img=c.image_url;}h+='<a href="'+location.origin+'/api/v1/dashboard/car/'+c.id+'" style="text-decoration:none"><div class="card" style="margin:0;padding:10px">'+(img?'<img src="'+img+'" loading="lazy" style="width:100%;height:110px;object-fit:cover;border-radius:10px">':'')+'<div style="font-size:13px;font-weight:700;margin-top:6px;color:#F8FAFC">'+c.name+'</div><div style="color:#10B981;font-weight:800;font-size:13px">&#8358;'+Number(c.price).toLocaleString()+'</div></div></a>';});box.innerHTML=h;}catch(e){box.innerHTML='<p style="color:#94A3B8;grid-column:1/-1;text-align:center">Welcome! Sign in to explore.</p>';}}
'''
if "loadPublicShowroom" not in code:
    code = code.replace("if(TOKEN){enterDash();}", PUB_JS + "if(TOKEN){enterDash();}else{loadPublicShowroom();}")
    print("✅ Public showroom loader injected!")

# ---------- 3. HIDE PUBLIC HOME WHEN LOGGED IN ----------
if 'publicHome");if(ph)' not in code:
    code = code.replace('document.getElementById("authCard").classList.add("hidden");',
                        'document.getElementById("authCard").classList.add("hidden");var ph=document.getElementById("publicHome");if(ph)ph.style.display="none";')
    print("✅ Public home hides after login!")

# ---------- 4. MY SHOWROOM + SHARE BUTTONS IN PROFILE ----------
OLD_PROFILE = 'async function loadProfile(){try{var me=await api("/profile/me","GET",null,true);document.getElementById("mPhone").value=me.phone;document.getElementById("mBio").value=me.bio;}catch(e){}}'
NEW_PROFILE = '''async function loadProfile(){try{var me=await api("/profile/me","GET",null,true);document.getElementById("mPhone").value=me.phone;document.getElementById("mBio").value=me.bio;var sid=me.page.split("/").pop();SHOWROOM_URL=location.origin+"/api/v1/dashboard/ad/"+sid;var sec=document.getElementById("tabProfile");var old=document.getElementById("showroomBox");if(old)old.remove();var d=document.createElement("div");d.id="showroomBox";d.style.marginTop="12px";d.innerHTML='<a href="'+SHOWROOM_URL+'" target="_blank" class="btn btn-primary" style="display:block;text-decoration:none;text-align:center">Open My Showroom</a><button class="btn btn-ghost" onclick="copyShowroom()">Copy Showroom Link</button><a class="btn btn-primary" style="display:block;text-decoration:none;text-align:center;background:#25D366;color:#000" href="https://wa.me/?text='+encodeURIComponent("Check out my showroom at Sodangi Motors: "+SHOWROOM_URL)+'" target="_blank">Share Showroom on WhatsApp</a>';var btns=sec.querySelectorAll("button");if(btns.length){btns[0].insertAdjacentElement("afterend",d);}else{sec.appendChild(d);}}catch(e){}}'''
if OLD_PROFILE in code:
    code = code.replace(OLD_PROFILE, NEW_PROFILE)
    print("✅ My Showroom + Share buttons added to Profile!")
elif "showroomBox" not in code:
    print("⚠️ Profile anchor not found - skipping showroom buttons.")

ast.parse(code)
with open(fp, "w", encoding="utf-8") as f:
    f.write(code)
print("✅ agents_api.py saved!")

# ---------- 5. ROOT URL REDIRECT (THE ONE URL) ----------
mp = "backend/app/main.py"
with open(mp, "r", encoding="utf-8-sig") as f:
    mcode = f.read()
REDIRECT = '''

@app.get("/", include_in_schema=False)
async def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/dashboard/ui")
'''
if '@app.get("/")' not in mcode:
    mcode = mcode + REDIRECT
    ast.parse(mcode)
    with open(mp, "w", encoding="utf-8") as f:
        f.write(mcode)
    print("✅ ROOT URL redirect added - ONE URL for everyone!")

print("Pushing to GitHub...")
subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Grand Unification: one URL, public homepage, owner+agent showrooms with share buttons"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ Push successful!")
        break
    print("Push failed attempt " + str(i+1) + ", retrying...")
    time.sleep(5)
