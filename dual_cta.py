import subprocess, time, urllib.request, re

print("="*60)
print("💎 UPGRADING SHOWROOM: DUAL CTA (WhatsApp + ₦5,000 Call)")
print("="*60)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. Upgrade the CSS for dual buttons
mc = re.sub(
    r'\.cta\{\{.*?\.btn\{\{.*?\}\}', 
    r'.cta{{position:fixed;bottom:0;left:0;right:0;padding:16px;background:#0A0F1C;border-top:1px solid #333;display:flex;flex-direction:column;gap:10px}}.btn-wa{{display:block;background:#25D366;color:#fff;padding:16px;border-radius:12px;text-decoration:none;font-weight:900;font-size:16px;box-shadow:0 10px 20px rgba(37,211,102,0.3);text-align:center}}.btn-call{{display:block;background:rgba(245,158,11,0.1);color:#F59E0B;padding:14px;border-radius:12px;text-decoration:none;font-weight:800;font-size:15px;border:1px solid #F59E0B;text-align:center}}', 
    mc, 
    flags=re.DOTALL
)
print("✅ Upgraded CSS for dual buttons!")

# 2. Upgrade the HTML to include both buttons
mc = re.sub(
    r'<div class="cta">.*?</div>', 
    r'<div class="cta"><a href="https://wa.me/2349079437745?text=Salam! I am looking at the {name}" target="_blank" class="btn-wa">💬 Verify & Buy on WhatsApp</a><a href="tel:+2349079437745" class="btn-call">📞 Call for Inspection <span style="font-size:13px;opacity:0.8">(₦5,000 Fee)</span></a></div>', 
    mc, 
    flags=re.DOTALL
)
print("✅ Injected Call for Inspection (₦5,000) button!")

with open("backend/app/main.py", "w", encoding="utf-8") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Showroom: Add Call for Inspection (₦5000) button"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 75s for Vercel...")
time.sleep(75)

print("\n🔍 Testing...")
req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15", headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "₦5,000 Fee" in body and "btn-call" in body:
            print("✅ ✅ ✅ DUAL CTA IS LIVE!")
            print("\n" + "="*60)
            print("👉 REFRESH THIS LINK ON YOUR PHONE:")
            print("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom-elite/15")
            print("="*60)
        else:
            print("⚠️ Deployed but text missing.")
except Exception as e:
    print("❌ Error:", e)
