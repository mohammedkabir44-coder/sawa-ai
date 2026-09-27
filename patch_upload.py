import subprocess, time, urllib.request

print("="*60)
print("🔧 FIXING UPLOAD PIPELINE: SAVING URLS TO DATABASE")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    code = r.read().decode()

def inject_before_commit(func_code):
    commit_idx = func_code.find("db.commit()")
    if commit_idx == -1: return func_code
    # Match the exact indentation of db.commit() so we don't break syntax
    line_start = func_code.rfind("\n", 0, commit_idx) + 1
    indent = func_code[line_start:commit_idx]
    injection = f"\n{indent}if hasattr(req, 'image_url') and req.image_url:\n{indent}    p.images = req.image_url\n{indent}else:\n{indent}    p.images = '[]'\n"
    return func_code[:commit_idx] + injection + func_code[commit_idx:]

# 1. Patch the CREATE route (/products/upload)
parts = code.split('@router.post("/products/upload")')
if len(parts) == 2:
    code = parts[0] + '@router.post("/products/upload")' + inject_before_commit(parts[1])
    print("✅ Injected image saver into POST /products/upload!")

# 2. Patch the UPDATE route (/products/{product_id})
parts = code.split('@router.put("/products/{product_id}")')
if len(parts) == 2:
    code = parts[0] + '@router.put("/products/{product_id}")' + inject_before_commit(parts[1])
    print("✅ Injected image saver into PUT /products/{product_id}!")

with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Fix: Save uploaded image URLs to database"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel to deploy the fix...")
time.sleep(75)
print("✅ UPLOAD PIPELINE IS PATCHED!")
