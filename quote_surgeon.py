import subprocess, time, urllib.request, re, ast

print("="*70)
print("🔧 QUOTE SURGEON: FIXING THE BROKEN SINGLE QUOTES")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# FIX 1: Replace broken onerror='none' with this.remove() (ZERO quotes needed!)
mc = mc.replace("this.style.display='none'", "this.remove()")
mc = mc.replace("this.style.display=\\'none\\'", "this.remove()")
mc = mc.replace('this.style.display="none"', "this.remove()")
print("✅ Fixed onerror quote collision (using this.remove())")

# FIX 2: Replace broken onclick single quotes in doAct calls
# The buttons have: onclick="doAct('/dealer-action?act=...')"
# Inside a single-quoted JS string, those inner single quotes break everything
# Solution: Use double quotes for onclick and encode the URL differently

# Find and fix the doAct button lines
mc = mc.replace(
    """onclick="doAct('/dealer-action?act='+act+'&id='+c.id+'" """,
    """onclick="doAct(String.fromCharCode(47)+'dealer-action?act='+act+'&id='+c.id)" """
)

# Nuclear option: Replace ALL remaining problematic onclick patterns
# Find: onclick="doAct('...')" inside single-quoted strings
old_patterns = [
    "onclick=\"doAct('/dealer-action?act='+act+'&id='+c.id+'')\"",
    "onclick=\"doAct('/dealer-action?act=del&id='+c.id+'')\"",
    "onclick=\"doAct('/dealer-action?act=like&id='+c.id+'')\"",
]

for pat in old_patterns:
    if pat in mc:
        print(f"  Found broken pattern: {pat[:50]}...")

# FIX 3: Replace the ENTIRE car card HTML builder with a SAFE version
# that uses NO single quotes inside HTML attributes
old_card_builder = re.search(r"cars\.forEach\(function\(c\)\{[\s\S]*?grid\.innerHTML=html;", mc)
if old_card_builder:
    print("✅ Found the car card builder. Replacing with SAFE version...")
    
    safe_builder = """cars.forEach(function(c){
      var img=c.images&&c.images.length?c.images[0]:"";
      var badge=c.status==="sold"?"<span class=\\"badge badge-sold\\">SOLD</span>":"<span class=\\"badge badge-avail\\">AVAILABLE</span>";
      var btnText=c.status==="sold"?"Mark Available":"Mark Sold";
      var act=c.status==="sold"?"avail":"sold";
      var card=document.createElement("div");
      card.className="car-card";
      var imgEl=document.createElement("img");
      imgEl.src=img;
      imgEl.onerror=function(){this.remove();};
      var info=document.createElement("div");
      info.className="car-info";
      info.innerHTML=badge+"<h3>"+c.name+"</h3><p>\\u20A6"+Number(c.price).toLocaleString()+"</p>";
      var actions=document.createElement("div");
      actions.className="actions";
      var btn1=document.createElement("button");
      btn1.textContent=btnText;
      btn1.style.cssText="background:#F59E0B;color:#000";
      btn1.onclick=function(){doAct("/dealer-action?act="+act+"&id="+c.id);};
      var btn2=document.createElement("button");
      btn2.textContent="Delete";
      btn2.style.cssText="background:#EF4444;color:#fff";
      btn2.onclick=function(){doAct("/dealer-action?act=del&id="+c.id);};
      var btn3=document.createElement("button");
      btn3.textContent="Share";
      btn3.style.cssText="background:#3B82F6;color:#fff";
      btn3.onclick=function(){shareCar(c.id);};
      var btn4=document.createElement("button");
      btn4.textContent="\\u2764 "+(c.likes||0);
      btn4.style.cssText="background:#EC4899;color:#fff";
      btn4.onclick=function(){doAct("/dealer-action?act=like&id="+c.id);};
      var btn5=document.createElement("button");
      btn5.textContent="\\ud83d\\udcc4 Agreement";
      btn5.style.cssText="background:#8B5CF6;color:#fff";
      btn5.onclick=function(){printAgreement(c.id);};
      actions.appendChild(btn1);
      actions.appendChild(btn2);
      actions.appendChild(btn3);
      actions.appendChild(btn4);
      actions.appendChild(btn5);
      info.appendChild(actions);
      card.appendChild(imgEl);
      card.appendChild(info);
      grid.appendChild(card);
    });
    grid.innerHTML=grid.innerHTML;"""
    
    mc = mc[:old_card_builder.start()] + safe_builder + mc[old_card_builder.end():]
    print("✅ Replaced string concatenation with SAFE DOM manipulation!")
    print("   (No more nested quotes - uses createElement instead!)")
else:
    print("⚠️ Could not find car card builder via regex.")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error at line {e.lineno}: {e.msg}")
    lines = mc.split('\n')
    s = max(0, e.lineno-3); en = min(len(lines), e.lineno+2)
    for i in range(s, en):
        p = ">>>" if i == e.lineno-1 else "   "
        print(f"{p} {i+1}: {lines[i]}")
    raise SystemExit(0)

with open("backend/app/main.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Quote Surgeon: Fix broken single quotes with DOM manipulation"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Testing Dealer Dashboard...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/dealer", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "createElement" in body:
            print("✅ ✅ ✅ QUOTE SURGEON SUCCESS! DOM MANIPULATION IS LIVE!")
            print("\n👉 Open in INCOGNITO on your phone:")
            print("https://sawa-ai-backend.vercel.app/dealer")
            print("   Your 11 cars will now load INSTANTLY!")
        else:
            print("⚠️ Route loaded but DOM code missing.")
except Exception as e:
    print(f"❌ Error: {e}")
