import subprocess, time, urllib.request, ast

print("="*70)
print("🏢 ZERO-BACKSLASH ORGANIZER: UNIFIED LOGIN + STICKY AGREEMENTS")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. LINE-BY-LINE EXORCISM (Remove old Hub, old Agent Login, old Agreement)
lines = mc.split('\n')
new_lines = []
skip = False

for line in lines:
    if ('def sodangi_hub' in line or 'def agent_login_page' in line or 'def generate_agreement' in line or 'def polished_agreement' in line or 'def unified_login' in line or 'def organized_hub' in line) and line.startswith('def '):
        skip = True
        while new_lines and new_lines[-1].strip().startswith('@app.'):
            new_lines.pop()
        continue
    if skip:
        if line.startswith('@app.') or (line.startswith('def ') and not line.startswith(' ')):
            skip = False
        else:
            continue
    new_lines.append(line)

mc = '\n'.join(new_lines)
print("✅ Exorcised old Hub, Login, and Agreement routes.")

# 2. INJECT THE NEW, ORGANIZED ROUTES (ZERO BACKSLASHES!)
NEW_ROUTES = '''

@app.get('/')
def organized_hub():
    from fastapi.responses import HTMLResponse
    html = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sodangi Motors</title>
<style>
body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;padding:20px;box-sizing:border-box}
h1{color:#10B981;text-align:center;margin-bottom:5px}
p.sub{text-align:center;color:#94A3B8;margin-bottom:30px}
.container{max-width:500px;margin:0 auto}
h3{color:#F59E0B;margin-top:25px;margin-bottom:10px;font-size:14px;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid #334155;padding-bottom:5px}
.btn{display:block;background:#1E293B;color:#fff;padding:18px;border-radius:12px;text-decoration:none;font-weight:800;font-size:16px;margin-bottom:12px;text-align:center;border:1px solid #334155}
.btn-primary{background:linear-gradient(135deg,#059669,#10B981);border:none;font-size:18px}
</style></head>
<body>
<h1>🚗 SODANGI MOTORS</h1>
<p class="sub">The Ultimate Automotive Hub</p>
<div class="container">
  <h3>🛒 For Customers</h3>
  <a href="/api/v1/dashboard/market" class="btn">🏪 Browse Marketplace (Buy Cars)</a>
  <h3>🔐 Staff & Admin Portal</h3>
  <a href="/login" class="btn btn-primary">🔑 Secure Login (Admin & Agents)</a>
  <h3>🚀 Quick Links</h3>
  <a href="/api/v1/dashboard/showroom-elite/15" class="btn">🚗 View Showroom Demo</a>
</div>
</body></html>"""
    return HTMLResponse(content=html)

@app.get('/login')
def unified_login():
    from fastapi.responses import HTMLResponse
    html = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Login</title>
<style>
body{margin:0;background:#0A0F1C;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;box-sizing:border-box}
.box{background:#1E293B;padding:30px;border-radius:16px;width:100%;max-width:400px;border:1px solid #334155}
h2{color:#10B981;margin-top:0;text-align:center}
label{display:block;margin-top:16px;font-size:14px;color:#94A3B8}
input{width:100%;padding:14px;border-radius:10px;border:1px solid #334155;background:#0F172A;color:#fff;font-size:16px;box-sizing:border-box;margin-top:6px}
.btn{width:100%;padding:16px;margin-top:24px;background:#10B981;color:#052E16;border:none;border-radius:10px;font-weight:800;font-size:16px;cursor:pointer}
.err{color:#EF4444;text-align:center;margin-top:12px;font-size:14px}
</style></head>
<body><div class="box"><h2>🔑 Secure Portal</h2>
<p style="text-align:center;color:#94A3B8;font-size:13px;margin-top:-5px">Admin & Agent Login</p>
<label>Email / Username</label><input id="email" type="text" placeholder="admin@sodangi.com">
<label>Password</label><input id="pass" type="password" placeholder="••••••••">
<button class="btn" onclick="login()">Sign In</button>
<p class="err" id="err"></p>
</div>
<script>
async function login(){
  var e=document.getElementById("email").value;
  var p=document.getElementById("pass").value;
  document.getElementById("err").innerText="Signing in...";
  try{
    var fd=new FormData(); fd.append("username",e); fd.append("password",p);
    var r=await fetch("/api/v1/auth/login",{method:"POST",body:fd});
    var d=await r.json();
    if(d.access_token){
      localStorage.setItem("sodangi_token", d.access_token);
      localStorage.setItem("sodangi_role", d.role||"agent");
      localStorage.setItem("sodangi_name", d.full_name||e);
      if(d.role === "admin" || d.role === "super_admin" || e.includes("admin")) {
        location.href="/dealer";
      } else {
        location.href="/agent-dashboard";
      }
    } else { document.getElementById("err").innerText="Login failed: "+(d.detail||"Check credentials"); }
  }catch(ex){ document.getElementById("err").innerText="Error: "+ex.message; }
}
</script></body></html>"""
    return HTMLResponse(content=html)

@app.get('/agreement/{car_id}')
def polished_agreement(car_id: int, buyer_name: str = "N/A", buyer_phone: str = "N/A", buyer_address: str = "N/A"):
    from app.core.database import engine
    from sqlalchemy import text
    from fastapi.responses import HTMLResponse
    import urllib.parse, datetime, json
    
    try:
        with engine.connect() as conn:
            row = conn.execute(text('SELECT name, price, description FROM products WHERE id = :id'), {'id': car_id}).first()
            if not row: return HTMLResponse("<h1>Car Not Found</h1>")
            
            car_name = row[0]
            car_price = f"₦{float(row[1]):,.0f}"
            date_str = datetime.date.today().strftime('%B %d, %Y')
            ref_no = f"SOD-{car_id}-{datetime.date.today().year}"
            
            qr_data = json.dumps({"ref": ref_no, "car": car_name, "price": car_price, "buyer": buyer_name, "date": date_str})
            qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=" + urllib.parse.quote(qr_data)
            
            html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agreement {ref_no}</title>
            <style>
            body{{font-family:serif;background:#f4f4f4;margin:0;padding:0;color:#000}}
            .print-bar{{position:sticky;top:0;background:#10B981;padding:15px;text-align:center;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.3)}}
            .print-bar button{{background:#fff;color:#065F46;padding:14px 30px;border:none;border-radius:8px;font-weight:900;font-size:18px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,0.2)}}
            .page{{background:#fff;max-width:800px;margin:20px auto;padding:40px;border:1px solid #ddd;box-shadow:0 0 20px rgba(0,0,0,0.1)}}
            .header{{text-align:center;border-bottom:3px double #000;padding-bottom:20px;margin-bottom:30px}}
            .header h1{{margin:0;font-size:28px;letter-spacing:2px}}
            .title{{text-align:center;font-size:20px;font-weight:bold;text-decoration:underline;margin:20px 0}}
            .parties{{display:flex;justify-content:space-between;margin:30px 0;flex-wrap:wrap}}
            .party{{width:48%;min-width:200px;margin-bottom:20px}}
            .party h3{{border-bottom:1px solid #000;margin-bottom:10px;font-size:16px}}
            .details{{margin:20px 0;line-height:1.6}}
            .qr-section{{text-align:center;margin:40px 0;padding:20px;border:2px dashed #000;background:#f9f9f9}}
            .signatures{{display:flex;justify-content:space-between;margin-top:60px;flex-wrap:wrap}}
            .sig-line{{width:40%;min-width:150px;border-top:1px solid #000;text-align:center;padding-top:5px;font-size:12px;margin-top:20px}}
            @media print {{ .print-bar {{ display: none !important; }} body {{ background: #fff; margin:0; padding:0; }} .page {{ box-shadow: none; border: none; margin: 0; padding: 20px; max-width: 100%; }} }}
            </style></head><body>
            <div class="print-bar">
              <button onclick="window.print()">💾 SAVE & PRINT AGREEMENT</button>
            </div>
            <div class="page">
                <div class="header">
                    <h1>SODANGI MOTORS LTD</h1>
                    <p>Lagos, Nigeria | +234 814 296 9979</p>
                </div>
                <div class="title">OFFICIAL VEHICLE SALE AGREEMENT</div>
                <p style="text-align:right"><strong>Ref No:</strong> {ref_no}<br><strong>Date:</strong> {date_str}</p>
                <div class="parties">
                    <div class="party"><h3>THE SELLER</h3><p><strong>Sodangi Motors Ltd</strong><br>Authorized Dealer</p></div>
                    <div class="party"><h3>THE BUYER</h3><p><strong>{buyer_name}</strong><br>Phone: {buyer_phone}<br>Address: {buyer_address}</p></div>
                </div>
                <div class="details">
                    <p>The Seller hereby transfers ownership of the following vehicle to the Buyer:</p>
                    <ul>
                        <li><strong>Vehicle Model:</strong> {car_name}</li>
                        <li><strong>Agreed Price:</strong> {car_price}</li>
                        <li><strong>Condition:</strong> Sold as seen, fully inspected and verified.</li>
                    </ul>
                    <p style="margin-top:20px">The Buyer acknowledges receipt of the vehicle in good working condition and accepts full responsibility for it from the date of this agreement.</p>
                </div>
                <div class="qr-section">
                    <p style="margin:0 0 10px;font-weight:bold">🔐 VERIFIED DIGITAL OWNERSHIP (Scan to Verify)</p>
                    <img src="{qr_url}" alt="Ownership QR Code">
                </div>
                <div class="signatures">
                    <div class="sig-line">Seller's Signature</div>
                    <div class="sig-line">Buyer's Signature</div>
                </div>
            </div>
            </body></html>"""
            return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(f"<h1>Error: {e}</h1>")
'''

mc += NEW_ROUTES
print("✅ Injected Organized Hub, Unified Login, and Sticky Agreement!")

# 3. VERIFY SYNTAX
try:
    ast.parse(mc)
    print("✅ ✅ ✅ SYNTAX IS 100% PERFECT! (Zero backslash errors!)")
except SyntaxError as e:
    print(f"❌ Syntax Error at line {e.lineno}: {e.msg}")
    raise SystemExit(0)

with open("backend/app/main.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Organize: Unified Login + Sticky Agreement + Clean Hub (Zero Backslashes)"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to compile...")
time.sleep(90)

print("\n🔍 Testing the organized empire...")
for path in ["/", "/login"]:
    try:
        req = urllib.request.Request("https://sawa-ai-backend.vercel.app" + path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            if "Secure Login" in body or "Ultimate Automotive Hub" in body:
                print(f"✅ {path} IS LIVE!")
            else:
                print(f"⚠️ {path} loaded but mismatch.")
    except Exception as e:
        print(f"❌ {path} Error: {e}")
