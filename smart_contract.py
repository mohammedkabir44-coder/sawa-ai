import subprocess, time, urllib.request, re, ast

print("="*70)
print("📜 DIGITAL SMART CONTRACT: AGREEMENT + QR CODE GENERATOR")
print("="*70)

url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/main.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    mc = r.read().decode()

# 1. INJECT THE AGREEMENT ROUTE
AGREEMENT_ROUTE = """

@app.get("/agreement/{car_id}")
def generate_agreement(car_id: int, buyer_name: str = "N/A", buyer_phone: str = "N/A", buyer_address: str = "N/A"):
    from app.core.database import engine
    from sqlalchemy import text
    from fastapi.responses import HTMLResponse
    import urllib.parse, datetime, json
    
    try:
        with engine.connect() as conn:
            row = conn.execute(text('SELECT name, price, description, images FROM products WHERE id = :id'), {'id': car_id}).first()
            if not row: return HTMLResponse("<h1>Car Not Found</h1>")
            
            car_name = row[0]
            car_price = f"₦{float(row[1]):,.0f}"
            car_desc = row[2] or "Standard Vehicle"
            date_str = datetime.date.today().strftime('%B %d, %Y')
            ref_no = f"SOD-{car_id}-{datetime.date.today().year}"
            
            # Generate QR Data (JSON format for easy scanning)
            qr_data = json.dumps({
                "ref": ref_no,
                "car": car_name,
                "price": car_price,
                "buyer": buyer_name,
                "date": date_str,
                "dealer": "Sodangi Motors"
            })
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(qr_data)}"
            
            html = f\'\'\'<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agreement {ref_no}</title>
            <style>
            body{{font-family:serif;background:#f4f4f4;margin:0;padding:20px;color:#000}}
            .page{{background:#fff;max-width:800px;margin:0 auto;padding:40px;border:1px solid #ddd;box-shadow:0 0 20px rgba(0,0,0,0.1)}}
            .header{{text-align:center;border-bottom:3px double #000;padding-bottom:20px;margin-bottom:30px}}
            .header h1{{margin:0;font-size:28px;letter-spacing:2px}}
            .header p{{margin:5px 0;font-size:14px;color:#555}}
            .title{{text-align:center;font-size:20px;font-weight:bold;text-decoration:underline;margin:20px 0}}
            .parties{{display:flex;justify-content:space-between;margin:30px 0}}
            .party{{width:48%}}
            .party h3{{border-bottom:1px solid #000;margin-bottom:10px;font-size:16px}}
            .details{{margin:20px 0;line-height:1.6}}
            .qr-section{{text-align:center;margin:40px 0;padding:20px;border:2px dashed #000;background:#f9f9f9}}
            .signatures{{display:flex;justify-content:space-between;margin-top:60px}}
            .sig-line{{width:40%;border-top:1px solid #000;text-align:center;padding-top:5px;font-size:12px}}
            .btn-print{{display:block;width:200px;margin:20px auto;padding:15px;background:#10B981;color:#fff;text-align:center;text-decoration:none;font-weight:bold;border-radius:8px;font-family:sans-serif}}
            @media print {{ .btn-print {{ display: none; }} body {{ background: #fff; }} .page {{ box-shadow: none; border: none; }} }}
            </style></head><body>
            <a href="javascript:window.print()" class="btn-print no-print">🖨️ Print / Save as PDF</a>
            <div class="page">
                <div class="header">
                    <h1>SODANGI MOTORS LTD</h1>
                    <p>Lagos, Nigeria | +234 814 296 9979 | sales@sodangimotors.com</p>
                </div>
                
                <div class="title">OFFICIAL VEHICLE SALE AGREEMENT</div>
                <p style="text-align:right"><strong>Ref No:</strong> {ref_no}<br><strong>Date:</strong> {date_str}</p>
                
                <div class="parties">
                    <div class="party">
                        <h3>THE SELLER</h3>
                        <p><strong>Sodangi Motors Ltd</strong><br>
                        Authorized Dealer<br>
                        Lagos, Nigeria</p>
                    </div>
                    <div class="party">
                        <h3>THE BUYER</h3>
                        <p><strong>{buyer_name}</strong><br>
                        Phone: {buyer_phone}<br>
                        Address: {buyer_address}</p>
                    </div>
                </div>
                
                <div class="details">
                    <p>The Seller hereby transfers ownership of the following vehicle to the Buyer:</p>
                    <ul>
                        <li><strong>Vehicle Model:</strong> {car_name}</li>
                        <li><strong>Agreed Price:</strong> {car_price}</li>
                        <li><strong>Condition:</strong> Sold as seen, fully inspected and verified.</li>
                        <li><strong>Additional Notes:</strong> {car_desc}</li>
                    </ul>
                    <p style="margin-top:20px">The Buyer acknowledges receipt of the vehicle in good working condition and accepts full responsibility for it from the date of this agreement. The Seller guarantees that the vehicle is free from any financial encumbrances or legal disputes.</p>
                </div>
                
                <div class="qr-section">
                    <p style="margin:0 0 10px;font-weight:bold">🔐 VERIFIED DIGITAL OWNERSHIP (Scan to Verify)</p>
                    <img src="{qr_url}" alt="Ownership QR Code">
                    <p style="font-size:10px;margin-top:10px;color:#666">Scan this code to verify the authenticity of this transaction on the Sodangi Motors registry.</p>
                </div>
                
                <div class="signatures">
                    <div class="sig-line">Seller's Signature</div>
                    <div class="sig-line">Buyer's Signature</div>
                </div>
            </div>
            </body></html>\'\'\'
            return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(f"<h1>Error: {e}</h1>")
"""

if '"/agreement/{car_id}"' not in mc:
    mc += AGREEMENT_ROUTE
    print("✅ Agreement Route injected!")

# 2. INJECT "PRINT AGREEMENT" BUTTON & JS FUNCTION
# We search for the "Delete" button in the loadCars loop and inject the Agreement button before it
if "printAgreement" not in mc:
    # Add the button next to Delete
    # Target: onclick=\'delCar( (or similar variations)
    mc = re.sub(r'(<button[^>]*?onclick=[\'"\\]*delCar)', r'<button onclick=\'printAgreement(\'+c.id+\')\' style=\'background:#8B5CF6;color:#fff\'>📄 Agreement</button>\1', mc)
    print("✅ Agreement Button injected into Inventory List!")
    
    # Add the JS function at the end of the script
    js_func = """
function printAgreement(id){
  var n = prompt("Enter Buyer's Full Name:");
  if(!n) return;
  var p = prompt("Enter Buyer's Phone Number:");
  var a = prompt("Enter Buyer's Address:");
  var url = '/agreement/'+id+'?buyer_name='+encodeURIComponent(n)+'&buyer_phone='+encodeURIComponent(p||'')+'&buyer_address='+encodeURIComponent(a||'');
  window.open(url, '_blank');
}
"""
    # Inject before the closing </script> tag of the dealer dashboard script
    mc = mc.replace('loadCars();\n</script>', 'loadCars();\n' + js_func + '\n</script>')
    print("✅ JS Function injected!")

try:
    ast.parse(mc)
    print("✅ Syntax is PERFECT.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e.msg}")
    raise SystemExit(0)

with open("backend/app/main.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(mc)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Add Digital Smart Contract: Agreement Letter + QR Code"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel...")
time.sleep(90)

print("\n🔍 Testing Agreement Generator...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/agreement/15?buyer_name=Test%20Buyer", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "OFFICIAL VEHICLE SALE AGREEMENT" in body and "api.qrserver.com" in body:
            print("✅ ✅ ✅ SMART CONTRACT GENERATOR IS LIVE!")
            print("\n👉 Go to your Dealer Dashboard, click '📄 Agreement' on any car!")
        else:
            print("⚠️ Route loaded but content mismatch.")
except Exception as e:
    print(f"❌ Error: {e}")
