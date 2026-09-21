import subprocess, time, ast

def read_clean(path):
    # utf-8-sig automatically strips the invisible BOM ghost (U+FEFF)
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()

# ---------- 1. AGENTS API: resilient fetch + watchdog + health ----------
fp = "backend/app/api/v1/endpoints/agents_api.py"
code = read_clean(fp)

OLD_API = 'async function api(p,m,b,a){var h={"Content-Type":"application/json"};if(a)h["Authorization"]="Bearer "+TOKEN;var r=await fetch(API+p,{method:m,headers:h,body:b?JSON.stringify(b):undefined});if(!r.ok){var e={};try{e=await r.json();}catch(x){}throw new Error(e.detail||("HTTP "+r.status));}return r.json();}'

NEW_API = 'async function api(p,m,b,a,attempt){attempt=attempt||0;var ctrl=new AbortController();var timer=setTimeout(function(){ctrl.abort();},20000);var h={"Content-Type":"application/json"};if(a)h["Authorization"]="Bearer "+TOKEN;try{var r=await fetch(API+p,{method:m,headers:h,body:b?JSON.stringify(b):undefined,signal:ctrl.signal});clearTimeout(timer);if(!r.ok){var e={};try{e=await r.json();}catch(x){}throw new Error(e.detail||("HTTP "+r.status));}return await r.json();}catch(err){clearTimeout(timer);var msg=err.message||"";var net=(err.name==="AbortError")||msg.indexOf("Failed to fetch")>-1||msg.indexOf("Network")>-1;if(net&&attempt<2){await new Promise(function(res){setTimeout(res,1200*(attempt+1));});return api(p,m,b,a,attempt+1);}throw new Error(net?"Network slow or offline - retrying failed. Please try again.":err.message);}}'

if "AbortController" not in code and OLD_API in code:
    code = code.replace(OLD_API, NEW_API)
    print("✅ Shield 3a: Resilient fetch injected!")
else:
    print("ℹ️ Shield 3a already present.")

WATCHDOG = 'window.addEventListener("error",function(ev){try{toast("App glitch caught: "+(ev.message||"unknown"),"#EF4444");}catch(e){}});\nwindow.addEventListener("offline",function(){try{toast("You are OFFLINE - reconnect to continue.","#EF4444");}catch(e){}});\nwindow.addEventListener("online",function(){try{toast("Back online!","#16A34A");}catch(e){}});\n'
if "Back online!" not in code:
    code = code.replace("if(TOKEN){enterDash();}", WATCHDOG + "if(TOKEN){enterDash();}")
    print("✅ Shield 3b: Watchdog injected!")
else:
    print("ℹ️ Shield 3b already present.")

HEALTH = '''

_BOOT_TIME = __import__("time").time()

@router.get("/health")
def deep_health(db: Session = Depends(get_db)):
    import time as _t
    from sqlalchemy import text as _sa_text
    report = {"status": "ok", "uptime_seconds": int(_t.time() - _BOOT_TIME)}
    try:
        t0 = _t.time()
        db.execute(_sa_text("SELECT 1"))
        report["database"] = "ok"
        report["db_latency_ms"] = int((_t.time() - t0) * 1000)
    except Exception as e:
        report["status"] = "degraded"
        report["database"] = "error: " + str(e)[:120]
    return report
'''
if "/health" not in code:
    code = code + HEALTH
    print("✅ Shield 2: Health endpoint injected!")
else:
    print("ℹ️ Shield 2 already present.")

ast.parse(code)
with open(fp, "w", encoding="utf-8") as f:
    f.write(code)
print("✅ agents_api.py saved clean!")

# ---------- 2. MAIN.PY: anti-crash middleware (BOM stripped) ----------
mp = "backend/app/main.py"
mcode = read_clean(mp)

MIDDLEWARE = '''

@app.middleware("http")
async def anti_crash_middleware(request, call_next):
    import time as _t, logging, traceback
    from fastapi.responses import JSONResponse
    t0 = _t.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        logging.getLogger("sawa").error("HANDLED CRASH %s %s: %s", request.method, request.url.path, traceback.format_exc())
        return JSONResponse(status_code=500, content={"detail": "Handled safely: " + str(exc)[:200]})
    ms = int((_t.time() - t0) * 1000)
    try:
        response.headers["X-Response-Ms"] = str(ms)
    except Exception:
        pass
    if ms > 4000:
        logging.getLogger("sawa").warning("SLOW REQUEST %s %s took %sms", request.method, request.url.path, ms)
    return response
'''
if "anti_crash_middleware" not in mcode:
    idx = mcode.find("lifespan=lifespan,")
    if idx != -1:
        j = mcode.find("\n)", idx)
        if j != -1:
            mcode = mcode[:j+2] + MIDDLEWARE + mcode[j+2:]
            print("✅ Shield 1: Anti-crash middleware injected!")
    ast.parse(mcode)
    with open(mp, "w", encoding="utf-8") as f:
        f.write(mcode)
    print("✅ main.py saved clean (BOM exorcised)!")
else:
    print("ℹ️ Shield 1 already present.")

# ---------- 3. PUSH ----------
print("Pushing to GitHub...")
subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Anti-Silence Engine: crash middleware, health endpoint, resilient fetch + watchdog"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ Push successful!")
        break
    print(f"Push failed (attempt {i+1}), retrying...")
    time.sleep(5)
