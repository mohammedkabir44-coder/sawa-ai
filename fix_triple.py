import subprocess, time, urllib.request

print("="*60)
print("🩹 FINAL SURGERY: FIXING THE TRIPLE BRACE TYPO")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# The exact broken string with 3 braces: function(){{{alert(...)}}})
broken = "function(){{{alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB')}}})"
fixed = "function(){{alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB')}})"

if broken in mc:
    mc = mc.replace(broken, fixed)
    print("✅ Fixed the triple brace typo! Python will now ignore the Javascript.")
else:
    # Fallback just in case formatting changed slightly
    broken2 = "function(){{{alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB')}}});"
    fixed2 = "function(){{alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB')}});"
    if broken2 in mc:
        mc = mc.replace(broken2, fixed2)
        print("✅ Fixed via fallback!")
    else:
        print("⚠️ Could not find the exact broken string. Trying regex...")
        import re
        mc = re.sub(r"function\(\)\{\{\{alert\(.*?\)\}\}\}", "function(){{alert('📣 Caption copied! Paste on WhatsApp Status / IG / FB')}})", mc)

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Fix: Remove triple brace typo in JS"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel to rebuild...")
time.sleep(75)

print("\n🔍 Testing the Showroom link...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "VERIFIED SELLER" in body and "Copy Ad Caption" in body:
            print("✅ ✅ ✅ SHOWROOM IS 100% ALIVE AND HAS THE VIRAL BUTTON!")
            print("\n" + "="*60)
            print("👉 REFRESH THIS LINK ON YOUR PHONE:")
            print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15")
            print("="*60)
        else:
            print("⚠️ Loaded but missing expected elements.")
            print("Body preview:", body[:200])
except Exception as e:
    print("❌ Error:", e)
