import subprocess, time, urllib.request

print("="*60)
print("🛡️ SAFE VIRAL BUTTON INJECTION (CRASH-PROOF)")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. Inject the JS function safely before </body>
JS_FUNC = """
<script>
function copyCaption(n, p) {
  var text = "🚗 " + n + " - ₦" + p + "\\n✅ Verified Seller | Sodangi Motors\\n👉 " + location.href;
  navigator.clipboard.writeText(text).then(function() {
    alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB');
  });
}
</script>
"""
if "function copyCaption(" not in mc:
    mc = mc.replace("</body>", JS_FUNC + "\n</body>")
    print("✅ Safe JS function injected!")

# 2. Build the button OUTSIDE the f-string to avoid brace collisions
old_gallery = 'gallery = ""'
new_gallery = '''gallery = ""
        # Safely build the caption button outside the f-string to avoid crashes
        safe_name = name.replace("'", "\\\\'")
        caption_btn = f'<button onclick="copyCaption(\\'{safe_name}\\', \\'{price}\\')" style="background:#3B82F6;color:#fff;padding:12px;border-radius:12px;border:none;font-weight:800;width:100%;text-align:center;margin-bottom:8px">📣 Copy Ad Caption</button>'
'''

if 'safe_name = name.replace' not in mc:
    mc = mc.replace('gallery = ""', new_gallery, 1)
    print("✅ Button variable created safely!")

# 3. Drop the variable into the HTML right before the WhatsApp button
if '{caption_btn}' not in mc:
    mc = mc.replace('<a href="https://wa.me/2348142969979?text=Salam! I am looking at the {name}"', '{caption_btn}\n          <a href="https://wa.me/2348142969979?text=Salam! I am looking at the {name}"')
    print("✅ Button injected into HTML!")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Safe Viral Button: Crash-proof injection"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel...")
time.sleep(75)

print("\n🔍 Testing...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "Copy Ad Caption" in body and "VERIFIED SELLER" in body:
            print("✅ ✅ ✅ SAFE VIRAL BUTTON IS LIVE!")
            print("\n" + "="*60)
            print("👉 REFRESH THIS LINK ON YOUR PHONE:")
            print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15")
            print("="*60)
        else:
            print("⚠️ Button missing.")
except Exception as e:
    print("❌ Error:", e)
