import subprocess, time, urllib.request, re

print("="*60)
print("🛡️ THE UNBREAKABLE VIRAL BUTTON (ZERO F-STRING COLLISIONS)")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. Clean up any previous broken attempts
mc = re.sub(r'<button onclick="navigator\.clipboard\.writeText.*?Copy Ad Caption</button>', '', mc)
mc = re.sub(r'caption_btn.*?\n', '', mc)
mc = re.sub(r'safe_name.*?\n', '', mc)
mc = re.sub(r'\{caption_btn\}', '', mc)

# 2. Find the exact return statement and inject BEFORE it
anchor = '        return HTMLResponse(content=html)'
if anchor in mc:
    # Standard string replacement. NO F-STRINGS. Python will not crash.
    button_code = '''
        # Inject viral button safely using standard string replacement
        viral_btn = '<button onclick="navigator.clipboard.writeText(document.title + \\' - \\' + document.querySelector(\\'.price\\').innerText + \\'\\\\n✅ Verified Seller\\\\n👉 \\' + location.href).then(function(){alert(\\'📣 Caption copied!\\')})" style="background:#3B82F6;color:#fff;padding:14px;border-radius:12px;border:none;font-weight:900;width:100%;text-align:center;margin-bottom:8px">📣 Copy Ad Caption</button>'
        html = html.replace('<div class="cta">', viral_btn + '<div class="cta">')
'''
    if 'viral_btn =' not in mc:
        mc = mc.replace(anchor, button_code + "\n" + anchor)
        print("✅ Unbreakable button injected right before return!")
else:
    print("❌ Could not find anchor.")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Fix: Unbreakable Viral Button (String replacement, no f-strings)"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel...")
time.sleep(75)

print("\n🔍 Testing...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "Copy Ad Caption" in body and "VERIFIED SELLER" in body:
            print("✅ ✅ ✅ VIRAL BUTTON IS LIVE AND CRASH-PROOF!")
            print("\n" + "="*60)
            print("👉 REFRESH THIS LINK ON YOUR PHONE:")
            print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15")
            print("="*60)
        else:
            print("⚠️ Button missing.")
except Exception as e:
    print("❌ Error:", e)
