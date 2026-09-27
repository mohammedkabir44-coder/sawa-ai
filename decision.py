import subprocess, time, urllib.request

print("="*60)
print("🏪 INJECTING 'BUY OR CHECKOUT SHOWROOM' SECTION")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

NEW_BLOCK = """<div class="wrap" style="margin-top:20px">
  <div style="background:linear-gradient(135deg, rgba(16,185,129,0.15), rgba(5,150,105,0.05)); border:1px solid rgba(16,185,129,0.3); border-radius:20px; padding:20px; text-align:center;">
    <h2 style="color:#10B981; font-size:20px; margin-bottom:8px; letter-spacing:-0.5px;">Ready to make a move?</h2>
    <p style="color:#CBD5E1; font-size:14px; margin-bottom:16px; line-height:1.5;">Do you want to buy this car or checkout our full showroom?</p>
    <div style="display:flex; gap:12px;">
      <a href="#wa-bottom" style="flex:1; background:#1E293B; color:#fff; padding:14px; border-radius:12px; text-decoration:none; font-weight:700; font-size:14px; border:1px solid #334155; transition:transform 0.2s;">💰 Buy Now</a>
      <a href="/api/v1/dashboard/market" style="flex:1; background:#059669; color:#fff; padding:14px; border-radius:12px; text-decoration:none; font-weight:700; font-size:14px; box-shadow:0 4px 12px rgba(5,150,105,0.3); transition:transform 0.2s;">🏪 Checkout Showroom</a>
    </div>
  </div>
</div>
"""

if '<div class="cta">' in mc and 'id="wa-bottom"' not in mc:
    mc = mc.replace('<div class="cta">', NEW_BLOCK + '<div class="cta" id="wa-bottom">')
    with open("backend/app/main.py", "w", encoding="utf-8") as f:
        f.write(mc)
    print("✅ Injected 'Buy Now / Checkout Showroom' section!")
else:
    print("ℹ️ Section already exists or CTA not found.")

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "UI: Add Buy Now / Checkout Showroom buttons above WhatsApp"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel to deploy...")
time.sleep(75)

print("\n🔍 Pinging showroom 15 to verify new UI...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/15", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "Checkout Showroom" in body:
            print("✅ ✅ ✅ NEW DECISION CARD IS LIVE!")
            print("\n" + "="*60)
            print("👉 REFRESH THIS EXACT LINK ON YOUR PHONE:")
            print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/15")
            print("="*60)
        else:
            print("⚠️ Deployed, but new text not found in HTML.")
except Exception as e:
    print("❌ Error:", e)
