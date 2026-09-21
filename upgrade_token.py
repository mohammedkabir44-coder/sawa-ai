import urllib.request, urllib.parse, json, subprocess, sys

APP_ID = "38061644883450174"
SHORT_TOKEN = "EAAlo8Wo4GVABScUpEvVRyBXFIC6URrzg46lywcSWa2pebjNkOoiEUIP72fXiqLzS8gy1zetnvV7HqLlnFwg8w6QDOgnMc1oRdq9zazthm7SG3zRedHJrOBJ6KtH9sYFwdwhPZBekdztqdY93sEJinDYOhiPvpByjRh34kOAAKI4uiw25EpGvtecZAkL3ZAPEOwESfPDfaPTddpUUpIA0DWPOJXNLVSrk4nkz7bfUjbBh52GhytLXfKajUPeFw4lhlghXAzdxMbNtB4ZD"

print("Reading secret.txt...")
with open("secret.txt", "r") as f:
    raw = f.read()

secret = ''.join(c for c in raw if c in '0123456789abcdefABCDEF')
print(f"Cleaned secret length: {len(secret)}")

if len(secret) != 32:
    print(f"ERROR: Secret is {len(secret)} chars. Must be exactly 32.")
    sys.exit(1)

print("Exchanging for 60-day token...")
params = urllib.parse.urlencode({"grant_type": "fb_exchange_token", "client_id": APP_ID, "client_secret": secret, "fb_exchange_token": SHORT_TOKEN})
url = f"https://graph.facebook.com/v25.0/oauth/access_token?{params}"

try:
    req = urllib.request.urlopen(url)
    res = json.loads(req.read().decode())
    long_token = res["access_token"]
    print("SUCCESS! Injecting into Vercel...")
    subprocess.run("vercel env add WHATSAPP_ACCESS_TOKEN production --force", input=long_token.encode(), shell=True, check=True)
    subprocess.run("vercel --prod --yes", shell=True, check=True)
    print("DONE!")
except Exception as e:
    print(f"Failed: {e}")
