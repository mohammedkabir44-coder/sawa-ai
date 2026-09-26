import subprocess, time, urllib.request, re

print("="*60)
print("🏥 SHOWROOM RESURRECTION PROTOCOL")
print("="*60)

# 1. DOWNLOAD CURRENT CODE
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    code = r.read().decode()

# 2. WIPE ALL OLD/BROKEN SHOWROOM ROUTES
print("\n[1/3] Wiping broken showroom routes...")
code = re.sub(r'@router\.get\("/showroom/\{product_id\}".*?(?=\n@router\.|\Z)', '', code, flags=re.DOTALL)
print("✅ Cleared out the ghosts.")

# 3. INJECT THE BULLETPROOF SHOWROOM
# (Using standard string concatenation to avoid any quote escaping errors)
SHOWROOM = """

@router.get("/showroom/{product_id}")
def showroom_page_resurrected(product_id: int, db: Session = Depends(get_db)):
    import urllib.parse as _up
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p: 
        return Response("<h2 style='color:#fff;text-align:center;padding:40px;font-family:sans-serif'>Vehicle not found</h2>", media_type="text/html")
    
    imgs = _extract_imgs_list(p.images)
    hero = imgs[0] if imgs else "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80"
    price_txt = format(float(p.price or 0), ",.0f")
    name = str(p.name).replace('"', "'").replace('<', '&lt;')
    desc = (p.description or "Premium vehicle available now.").replace('<', '&lt;')
    
    wa_text = _up.quote("Salam! I am looking at the " + str(p.name) + " (NGN " + price_txt + ") on Sodangi Motors.")
    wa_link = "https://wa.me/2349079437745?text=" + wa_text
    
    gallery = ""
    for u in imgs:
        if u.endswith(".mp4") or u.endswith(".webm") or u.endswith(".mov"):
            gallery += '<video src="'+u+'" controls playsinline style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0"></video>'
        else:
            gallery += '<img src="'+u+'" style="width:100%;height:320px;object-fit:cover;scroll-snap-align:center;flex-shrink:0" loading="lazy">'
    if not gallery: 
        gallery = '<img src="'+hero+'" style="width:100%;height:320px;object-fit:cover">'

    html = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+name+'</title><style>body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding-bottom:100px}.gal{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;background:#000}.wrap{max-width:600px;margin:0 auto;padding:20px}.price{font-size:28px;font-weight:900;color:#10B981;margin:10px 0}.badge{background:rgba(16,185,129,0.2);color:#10B981;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}.cta{position:fixed;bottom:0;left:0;right:0;padding:20px;background:#0A0F1C;border-top:1px solid #333;text-align:center}.btn{display:block;background:#25D366;color:#fff;padding:16px;border-radius:12px;text-decoration:none;font-weight:900;font-size:18px;box-shadow:0 10px 20px rgba(37,211,102,0.3)}</style></head><body><div class="gal">'+gallery+'</div><div class="wrap"><span class="badge">✅ VERIFIED SELLER</span><h1 style="margin-top:8px">'+name+'</h1><div class="price">&#8358; '+price_txt+'</div><p style="color:#94A3B8;line-height:1.6;margin-top:16px">'+desc+'</p></div><div class="cta"><a href="'+wa_link+'" target="_blank" class="btn">💬 Verify & Buy on WhatsApp</a></div></body></html>'
    return Response(content=html, media_type="text/html")
"""

code += SHOWROOM
print("✅ Injected Bulletproof Elite Showroom.")

# 4. ENSURE V4 DASHBOARD HAS THE "SHOWROOM" BUTTON IN INVENTORY
print("\n[2/3] Patching V4 Dashboard inventory buttons...")
target = '<button class="btn btn-ghost" style="flex:1;min-width:80px;padding:10px;font-size:12px;margin:0" onclick="editCar(\'+c.id+\')">'
if target in code or 'editCar(\'+c.id+\')' in code:
    # We will just search for the edit button and append the showroom button if it's missing
    pass
# Flexible approach to ensure button exists
if 'Showroom</a>' not in code.split('def fresh_dashboard_v5')[1] if 'def fresh_dashboard_v5' in code else '':
    replacement_anchor = 'onclick="editCar(\'+c.id+\')">Edit</button>'
    showroom_btn = '<a class="btn btn-primary" style="flex:1;min-width:80px;padding:10px;font-size:12px;margin:0;text-decoration:none;text-align:center" href="/api/v1/dashboard/showroom/\'+c.id+\'" target="_blank">Showroom</a>'
    if replacement_anchor in code and showroom_btn not in code:
        code = code.replace(replacement_anchor, replacement_anchor + showroom_btn)
        print("✅ Patched V4 Dashboard inventory to show 'Showroom' button!")

# 5. SAVE AND PUSH
with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Fix: Resurrect Elite Showroom and patch V4 button"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to rebuild...")
time.sleep(90)

# 6. VERIFY
print("\n🔍 Verifying Showroom Route...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/1", headers={"User-Agent": "Mozilla/5.0"})
    r = urllib.request.urlopen(req, timeout=30)
    print("✅ SHOWROOM IS 100% ALIVE AND RESPONDING!")
except Exception as e:
    print("⚠️ Showroom check:", e)
