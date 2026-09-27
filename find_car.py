import subprocess, time, urllib.request, json

print("="*60)
print("🔍 FINDING YOUR EXACT LIVE CAR ID")
print("="*60)

# 1. Inject diagnostic endpoint
fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

DIAG = """

@router.get("/debug-first-car")
def debug_first_car(db: Session = Depends(get_db)):
    p = db.query(Product).order_by(Product.id.desc()).first()
    if p:
        return {"id": p.id, "name": p.name, "url": "/api/v1/dashboard/showroom/" + str(p.id)}
    return {"error": "No cars in database!"}
"""

if "/debug-first-car" not in code:
    code += DIAG
    with open(fp, "w", encoding="utf-8") as f:
        f.write(code)
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Add debug-first-car"])
    subprocess.run(["git", "push", "origin", "main", "--force"])
    print("⏳ Waiting 60s for Vercel...")
    time.sleep(60)
else:
    print("ℹ️ Diagnostic endpoint already exists.")

# 2. Fetch the ID
print("\nFetching actual car ID from your live database...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/dashboard/debug-first-car", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
        print("\n" + "="*60)
        if "id" in data:
            print("✅ FOUND A LIVE CAR IN YOUR DATABASE!")
            print(f"Car Name: {data['name']}")
            print(f"Car ID:   {data['id']}")
            url = "https://sawa-ai-backend.vercel.app" + data['url']
            print("\n👉 COPY AND PASTE THIS EXACT URL INTO YOUR BROWSER:")
            print(url)
            print("="*60)
        else:
            print("❌ DATABASE IS EMPTY! You need to add a car via the V4 dashboard first.")
            print("="*60)
except Exception as e:
    print("❌ Error:", e)
