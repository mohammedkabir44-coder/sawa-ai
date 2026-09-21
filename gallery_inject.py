import subprocess, time, os

file_path = "backend/app/api/v1/endpoints/agents_api.py"
print("Reading file...")
with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. INJECT SWIPEABLE GALLERY CSS
old_css = "#toast { position: fixed;"
new_css = """.gallery { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: 10px; padding: 4px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
  .gallery::-webkit-scrollbar { display: none; }
  .gallery img { scroll-snap-align: center; flex-shrink: 0; width: 90%; height: 220px; object-fit: cover; border-radius: 14px; border: 2px solid #1E293B; }
  #toast { position: fixed;"""

if old_css in code and ".gallery" not in code:
    code = code.replace(old_css, new_css, 1)
    print("✅ Injected Swipeable Gallery CSS!")
else:
    print("ℹ️ CSS already injected or anchor missing.")

# 2. INJECT SWIPEABLE GALLERY JS IN loadCars
old_js = """      var img=(c.images&&c.images.length>0)?c.images[0]:"";
      var h='<div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div>';
      if(img)h+='<img src="'+img+'" style="width:100%;height:150px;object-fit:cover;border-radius:12px;margin:8px 0">';"""

new_js = """      var imgs=(c.images&&c.images.length>0)?c.images:[];
      var h='<div class="item-info"><h3>'+c.name+'</h3><p>&#8358;'+Number(c.price).toLocaleString()+'</p></div>';
      if(imgs.length>0){h+='<div class="gallery" style="margin:10px 0">';imgs.forEach(function(url){h+='<img src="'+url+'" loading="lazy">';});h+='</div>';}"""

if old_js in code:
    code = code.replace(old_js, new_js)
    print("✅ Upgraded loadCars to Swipeable Gallery with Lazy Loading!")
else:
    print("ℹ️ loadCars already upgraded or anchor missing.")

# 3. FORCE REBUILD
with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

with open("backend/app/main.py", "a") as f:
    f.write(f"\n# GALLERY_BUILD_{int(time.time())}")

print("Pushing to GitHub...")
subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "Visual Upgrade: Swipeable Image Galleries + Lazy Loading for instant mobile speed"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ Push successful!")
        break
    print(f"Push failed (attempt {i+1}), retrying...")
    time.sleep(5)
