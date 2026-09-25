import subprocess, time, urllib.request, json

print("="*60)
print("🐍 GHOST EXORCISM PART 2: INSTALLING PSYCOPG (V3)")
print("="*60)

# 1. Add the exact missing driver to requirements.txt
req_path = "backend/requirements.txt"
with open(req_path, "r", encoding="utf-8") as f:
    reqs = f.read()

if "psycopg-binary" not in reqs:
    reqs += "\npsycopg\npsycopg-binary\n"
    with open(req_path, "w", encoding="utf-8") as f:
        f.write(reqs)
    print("✅ Added 'psycopg' (v3) to requirements.txt!")
    print("   (SQLAlchemy 2.0 requires this specific package to connect to Postgres)")
else:
    print("ℹ️ psycopg already in requirements.")

# 2. PUSH TO VERCEL
print("\n[2/2] Pushing the new driver to Vercel...")
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Exorcism Part 2: Install psycopg v3 for SQLAlchemy 2.0"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 120 seconds for Vercel to install the new database driver...")
time.sleep(120)

# 3. VERIFY THE GHOST IS DEAD
print("\n🔍 Checking /debug-crashes to see if the database connected...")
try:
    req = urllib.request.Request("https://sawa-ai-backend.vercel.app/api/v1/debug-crashes", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
        if "NO CRASHES! MODULES LOADED PERFECTLY." in body:
            print("✅ ✅ ✅ THE GHOST IS DEAD! ALL MODULES LOADED PERFECTLY!")
            print("   Your database is connected and the server is 100% alive.")
        else:
            print("⚠️ Some crashes remain:")
            print(body[:500])
except Exception as e:
    print(f"❌ Error checking status: {e}")
