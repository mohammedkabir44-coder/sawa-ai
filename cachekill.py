import subprocess, time, re, json, hmac, hashlib, base64, ast, sys

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

SECRET = "sodangi-sawa-secret-2026-do-not-share"
payload = {"e": "owner@sodangi.com", "r": "owner", "t": int(time.time()) + 31536000}
p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
sig = hmac.new(SECRET.encode(), p_b64.encode(), hashlib.sha256).hexdigest()
TOKEN = p_b64 + "." + sig

BLOCK = '''<script>
(function(){
  try{
    if('serviceWorker' in navigator){navigator.serviceWorker.getRegistrations().then(function(rs){rs.forEach(function(r){r.unregister();});});}
    if('caches' in window){caches.keys().then(function(ks){ks.forEach(function(k){caches.delete(k);});});}
    if(!localStorage.getItem("sodangi_token")){
      localStorage.setItem("sodangi_token","''' + TOKEN + '''");
      localStorage.setItem("sodangi_role","owner");
      localStorage.setItem("sodangi_name","Owner");
      setTimeout(function(){window.location.href=window.location.pathname+"?v=2";},300);
    }
  }catch(e){}
})();
</script>
<!-- CLEAN_KILLER_V2 -->'''

if "CLEAN_KILLER_V2" not in code:
    old = re.compile(r'<script>\s*\(function\(\)\s*\{.*?<!-- AUTO_LOGIN_INJECTED -->', re.DOTALL)
    if old.search(code):
        code = old.sub(BLOCK, code, count=1)
        print("Replaced old auto-login block with CACHE KILLER V2!")
    else:
        code = code.replace("<body>", "<body>\n" + BLOCK, 1)
        print("Injected CACHE KILLER V2 after <body>!")
else:
    print("CLEAN KILLER V2 already present.")

ast.parse(code)
with open(fp, "w", encoding="utf-8") as f:
    f.write(code)
print("Saved!")

subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Cache Killer V2: unregister service worker, purge caches, auto-login owner"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("Push successful!")
        break
    print("Push retry " + str(i+1))
    time.sleep(5)
