import subprocess, time, ast

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

SHOWROOM = '''

SHOWROOM_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__NAME__ | NGN __PRICE__ | Sodangi Motors</title>
<meta property="og:type" content="product">
<meta property="og:title" content="__NAME__ - NGN __PRICE__">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="__HERO__">
<meta property="og:url" content="__URL__">
<meta property="og:site_name" content="Sodangi Motors">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__NAME__ - NGN __PRICE__">
<meta name="twitter:image" content="__HERO__">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,sans-serif}
body{background:radial-gradient(900px 500px at 50% -120px,rgba(6,95,70,.35),transparent),#0B0F19;color:#F8FAFC;padding-bottom:110px}
.gal{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:10px;padding:10px;scrollbar-width:none}
.gal::-webkit-scrollbar{display:none}
.gal img{scroll-snap-align:center;flex-shrink:0;width:92%;max-width:480px;height:280px;object-fit:cover;border-radius:20px;border:1px solid #1E293B}
.wrap{max-width:560px;margin:0 auto;padding:6px 16px}
.badge{display:inline-block;background:rgba(16,185,129,.15);color:#34D399;font-size:11px;font-weight:800;padding:5px 12px;border-radius:999px;letter-spacing:1px;text-transform:uppercase}
h1{font-size:26px;font-weight:900;margin:10px 0 6px}
.price{display:inline-block;background:linear-gradient(135deg,#22C55E,#10B981);color:#052E16;font-size:26px;font-weight:900;padding:10px 22px;border-radius:14px;margin:8px 0 14px;box-shadow:0 8px 24px rgba(34,197,94,.35)}
.desc{color:#94A3B8;line-height:1.65;font-size:15px}
.share{margin-top:26px;background:#151F38;border:1px solid #1E293B;border-radius:18px;padding:18px}
.share h2{font-size:15px;color:#7DD3FC;margin-bottom:12px}
.sbtn{display:block;width:100%;padding:14px;margin:8px 0;border:none;border-radius:12px;font-size:15px;font-weight:800;text-decoration:none;text-align:center;color:#fff;cursor:pointer}
.wa{background:#25D366;color:#06300F}
.fb{background:#1877F2}
.tw{background:#0F1419;border:1px solid #334155}
.cp{background:#334155}
.cta{position:fixed;bottom:0;left:0;right:0;padding:14px 16px;background:rgba(11,15,25,.92);backdrop-filter:blur(8px);border-top:1px solid #1E293B}
.cta a{display:block;text-align:center;background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;font-size:18px;font-weight:900;padding:16px;border-radius:16px;text-decoration:none;box-shadow:0 10px 30px rgba(37,211,102,.45);animation:pulse 1.8s infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.02)}}
</style></head>
<body>
<div class="gal">__GAL__</div>
<div class="wrap">
<span class="badge">Verified Dealer</span>
<h1>__NAME__</h1>
<div class="price">&#8358;__PRICE__</div>
<p class="desc">__DESC__</p>
<div class="share">
<h2>Share this vehicle</h2>
<a class="sbtn wa" href="https://wa.me/?text=__SHARE__" target="_blank" rel="noopener">Share on WhatsApp</a>
<a class="sbtn fb" href="https://www.facebook.com/sharer/sharer.php?u=__URL__" target="_blank" rel="noopener">Share on Facebook</a>
<a class="sbtn tw" href="https://twitter.com/intent/tweet?text=__SHARE__" target="_blank" rel="noopener">Share on X</a>
<button class="sbtn cp" onclick="navigator.clipboard.writeText('__URL__').then(function(){alert('Link copied! Paste it anywhere.')})">Copy Link</button>
</div>
</div>
<div class="cta"><a href="https://wa.me/2349079437745?text=__WA__" target="_blank" rel="noopener">Chat on WhatsApp to Buy</a></div>
</body></html>"""

@router.get("/showroom/{product_id}")
def showroom_page_v4(product_id: int, db: Session = Depends(get_db)):
    import urllib.parse as _up
    p = db.query(Product).filter(Product.id == product_id, Product.is_active.is_(True)).first()
    if not p:
        return Response(content="<h2 style='color:#fff;text-align:center;padding:60px;font-family:sans-serif'>Vehicle not available</h2>", media_type="text/html")
    imgs = _extract_imgs_list(p.images)
    hero = imgs[0] if imgs else "https://images.unsplash.com/photo-1492144534655-ae79c464b2d7?auto=format&fit=crop&w=1200&q=80"
    price_txt = format(float(p.price or 0), ",.0f")
    name = str(p.name).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "'")
    desc = (p.description or "Verified vehicle from Sodangi Motors. Tap the green button to chat with the seller on WhatsApp.")[:400]
    desc = desc.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "'")
    page_url = "https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/" + str(product_id)
    wa_text = _up.quote("Salam! I want to buy the " + str(p.name) + " listed at NGN " + price_txt + " on Sodangi Motors.")
    share_text = _up.quote(str(p.name) + " - NGN " + price_txt + " | Sodangi Motors " + page_url)
    gal = ""
    for u in imgs:
        gal = gal + '<img src="' + u + '" loading="lazy" alt="' + name + '">'
    if not gal:
        gal = '<img src="' + hero + '" loading="lazy" alt="' + name + '">'
    html = SHOWROOM_TEMPLATE.replace("__NAME__", name).replace("__PRICE__", price_txt).replace("__DESC__", desc).replace("__HERO__", hero).replace("__GAL__", gal).replace("__URL__", page_url).replace("__WA__", wa_text).replace("__SHARE__", share_text)
    return Response(content=html, media_type="text/html")
'''

PUTROUTE = '''

@router.put("/products/{product_id}")
def update_product_v4(product_id: int, req: ProductReq, request: Request, db: Session = Depends(get_db)):
    me = _auth(request)
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if me.get("r") != "owner":
        ag = db.query(Agent).filter(Agent.email == me["e"]).first()
        ok = False
        if ag:
            link = db.query(ProductAgent).filter(ProductAgent.product_id == product_id, ProductAgent.agent_id == ag.id).first()
            ok = link is not None
        if not ok:
            raise HTTPException(status_code=403, detail="You can only edit your own vehicles")
    p.name = req.name
    p.price = req.price
    if req.description is not None:
        p.description = req.description
    if req.image_url:
        p.images = req.image_url if req.image_url.startswith("[") else json.dumps([req.image_url])
    db.commit()
    return {"status": "updated", "id": product_id}
'''

if "/showroom/{product_id}" not in code:
    code = code + SHOWROOM
    print("SHOWROOM PAGE injected by Python!")
if '@router.put("/products/{product_id}")' not in code:
    code = code + PUTROUTE
    print("EDIT (PUT) API endpoint injected by Python!")

if "editCar(" not in code:
    old_inner = """      d.innerHTML='<div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div><button class="btn btn-danger" style="width:auto;padding:8px 12px;font-size:12px;margin:0" onclick="delCar('+c.id+')">Delete</button>';"""
    new_inner = """      d.style.flexDirection="column";d.style.alignItems="stretch";d.style.gap="8px";
      d.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div><button class="btn btn-danger" style="width:auto;padding:8px 12px;font-size:12px;margin:0" onclick="delCar('+c.id+')">Delete</button></div><div style="display:flex;gap:6px;flex-wrap:wrap"><button class="btn btn-ghost" style="flex:1;min-width:80px;padding:10px;font-size:12px;margin:0" onclick="editCar('+c.id+')">Edit</button><a class="btn btn-primary" style="flex:1;min-width:80px;padding:10px;font-size:12px;margin:0;text-decoration:none;text-align:center" href="/api/v1/dashboard/showroom/'+c.id+'" target="_blank">Showroom</a><button class="btn btn-ghost" style="flex:1;min-width:80px;padding:10px;font-size:12px;margin:0;background:#25D366;color:#06300F" onclick="shareCar('+c.id+')">Share</button></div>';"""
    if old_inner in code:
        code = code.replace(old_inner, new_inner)
        print("Edit / Showroom / Share buttons added to inventory!")
    else:
        print("WARNING: inventory anchor not found")
    old_for = "    CARS.forEach(function(c){"
    if old_for in code:
        code = code.replace(old_for, "    window.V4CARS=CARS;\n    CARS.forEach(function(c){", 1)
    logout_v4 = """function logout(){
  localStorage.removeItem("sodangi_token");
  localStorage.removeItem("sodangi_role");
  localStorage.removeItem("sodangi_name");
  location.reload();
}"""
    extra_js = """function editCar(id){var c=(window.V4CARS||[]).filter(function(x){return x.id===id;})[0];if(!c)return;var n=prompt("Vehicle name:",c.name);if(n===null||n==="")return;var p=prompt("Price (Naira):",c.price);if(p===null||p==="")return;var ds=prompt("Description:",c.description||"");if(ds===null)return;api("/products/"+id,"PUT",{name:n,price:parseFloat(p),description:ds,image_url:JSON.stringify(c.images||[]),stock:c.stock||1}).then(function(){toast("Vehicle updated!");loadCars();}).catch(function(e){alert("Failed: "+e.message);});}
function shareCar(id){var c=(window.V4CARS||[]).filter(function(x){return x.id===id;})[0];if(!c)return;var url=location.origin+"/api/v1/dashboard/showroom/"+id;var txt=c.name+" - NGN "+Number(c.price).toLocaleString()+" "+url;if(navigator.share){navigator.share({title:c.name,text:txt,url:url}).catch(function(){});}else{window.open("https://wa.me/?text="+encodeURIComponent(txt));}}
"""
    if logout_v4 in code:
        code = code.replace(logout_v4, logout_v4 + "\n" + extra_js, 1)
        print("editCar + shareCar JS injected!")
    else:
        print("WARNING: logout anchor not found")

ast.parse(code)
with open(fp, "w", encoding="utf-8") as f:
    f.write(code)
print("Saved by Python!")

subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Python upgrade: showroom pages, inventory editing, social share CTAs"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("Push successful!")
        break
    print("Push retry " + str(i+1))
    time.sleep(5)
