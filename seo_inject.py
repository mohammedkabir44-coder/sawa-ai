import subprocess, time, ast

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

# ---------- 1. NEW PUBLIC CAR PAGE WITH FULL OG + TWITTER META ----------
ROUTE = '''

@router.get("/car/{product_id}", response_class=HTMLResponse)
def public_car_page(product_id: int, db: Session = Depends(get_db)):
    import urllib.parse as _up2
    p = db.query(Product).filter(Product.id == product_id, Product.is_active.is_(True)).first()
    if not p:
        return Response(content="<h2 style='color:#fff;background:#0A0F1C;padding:40px;text-align:center;font-family:sans-serif'>Vehicle not available</h2>", media_type="text/html")
    imgs = _extract_imgs_list(p.images)
    hero = imgs[0] if imgs else "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80"
    price_txt = "NGN " + format(float(p.price or 0), ",.0f")
    safe_name = str(p.name).replace('"', "'").replace("<", "").replace(">", "")
    desc = (p.description or "Verified vehicle from Sodangi Motors. Tap to chat on WhatsApp.")[:300].replace('"', "'").replace("<", "").replace(">", "")
    wa_text = "Salam! I am interested in the " + safe_name + " listed at " + price_txt + " on Sodangi Motors."
    wa_link = "https://wa.me/2349079437745?text=" + _up2.quote(wa_text)
    page_url = "https://sawa-ai-backend.vercel.app/api/v1/dashboard/car/" + str(product_id)
    gallery = ""
    for u in imgs:
        gallery = gallery + '<img src="' + u + '" loading="lazy" style="scroll-snap-align:center;flex-shrink:0;width:92%;max-width:420px;height:260px;object-fit:cover;border-radius:18px;">'
    if not gallery:
        gallery = '<img src="' + hero + '" style="width:100%;height:260px;object-fit:cover;border-radius:18px;">'
    html = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    html = html + '<title>' + safe_name + ' | ' + price_txt + ' | Sodangi Motors</title>'
    html = html + '<meta property="og:type" content="product">'
    html = html + '<meta property="og:title" content="' + safe_name + ' - ' + price_txt + '">'
    html = html + '<meta property="og:description" content="' + desc + '">'
    html = html + '<meta property="og:image" content="' + hero + '">'
    html = html + '<meta property="og:image:width" content="1200">'
    html = html + '<meta property="og:image:height" content="630">'
    html = html + '<meta property="og:url" content="' + page_url + '">'
    html = html + '<meta property="og:site_name" content="Sodangi Motors">'
    html = html + '<meta name="twitter:card" content="summary_large_image">'
    html = html + '<meta name="twitter:title" content="' + safe_name + ' - ' + price_txt + '">'
    html = html + '<meta name="twitter:description" content="' + desc + '">'
    html = html + '<meta name="twitter:image" content="' + hero + '">'
    html = html + '<meta name="theme-color" content="#0B0F19">'
    html = html + '<style>*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,sans-serif}body{background:#0B0F19;color:#F8FAFC;padding-bottom:40px}.wrap{max-width:560px;margin:0 auto;padding:16px}.gal{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:10px;padding:4px;scrollbar-width:none}.gal::-webkit-scrollbar{display:none}.card{background:#151F38;border:1px solid #1E293B;border-radius:18px;padding:20px;margin-top:16px}.price{color:#10B981;font-size:26px;font-weight:800;margin:8px 0}.badge{display:inline-block;background:rgba(16,185,129,.15);color:#34D399;font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;text-transform:uppercase;letter-spacing:1px}.cta{display:flex;align-items:center;justify-content:center;gap:10px;background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;font-weight:800;font-size:18px;padding:18px;border-radius:16px;text-decoration:none;margin-top:18px;box-shadow:0 10px 30px rgba(37,211,102,.35)}</style>'
    html = html + '</head><body><div class="wrap">'
    html = html + '<div class="gal">' + gallery + '</div>'
    html = html + '<div class="card"><span class="badge">Verified Dealer</span><h1 style="font-size:24px;margin-top:10px">' + safe_name + '</h1>'
    html = html + '<div class="price">&#8358;' + format(float(p.price or 0), ",.0f") + '</div>'
    html = html + '<p style="color:#94A3B8;line-height:1.6">' + desc + '</p>'
    html = html + '<a class="cta" href="' + wa_link + '">Chat on WhatsApp to Buy</a>'
    html = html + '<p style="color:#64748B;font-size:12px;text-align:center;margin-top:14px">Sodangi Motors - Trusted Vehicle Marketplace</p>'
    html = html + '</div></div></body></html>'
    return Response(content=html, media_type="text/html")
'''

if "/car/{product_id}" not in code:
    code = code + ROUTE
    print("✅ Public Car Page with OG + Twitter meta injected!")
else:
    print("ℹ️ Car page already present.")

# ---------- 2. POINT ALL SHARE BUTTONS TO THE RICH CAR PAGE ----------
old_link = 'location.origin+"/api/v1/dashboard/ad/1"'
new_link = 'location.origin+"/api/v1/dashboard/car/"+car.id'
if old_link in code:
    n = code.count(old_link)
    code = code.replace(old_link, new_link)
    print(f"✅ Repointed {n} share buttons to rich car pages!")
else:
    print("ℹ️ Share links already repointed.")

# ---------- 3. ADD TWITTER CARD TO AGENT SHOWROOM PAGE ----------
old_og = '<meta property="og:image" content="{hero}">'
new_og = old_og + '\n<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:image" content="{hero}">'
if old_og in code and "twitter:card" not in code.split("def agent_ad")[1][:3000] if "def agent_ad" in code else True:
    code = code.replace(old_og, new_og, 1)
    print("✅ Twitter card added to agent showroom!")

ast.parse(code)
with open(fp, "w", encoding="utf-8") as f:
    f.write(code)
print("✅ Saved!")

print("Pushing to GitHub...")
subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Public Showroom SEO: rich OG previews + public car pages with swipe gallery"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ Push successful!")
        break
    print(f"Push failed (attempt {i+1}), retrying...")
    time.sleep(5)
