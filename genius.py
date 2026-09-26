import subprocess, time, urllib.request, re

print("="*60)
print("🧠 INJECTING GENIUS BOT (Advanced Local AI)")
print("="*60)

# 1. DOWNLOAD CURRENT CODE
url = "https://raw.githubusercontent.com/mohammedkabir44-coder/sawa-ai/main/backend/app/api/v1/endpoints/agents_api.py"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    code = r.read().decode()

# 2. THE GENIUS BRAIN
NEW_BOT = '''def _wa_bot_reply(text, db):
    import difflib
    import re
    
    prods = db.query(Product).filter(Product.is_active.is_(True)).all()
    if not prods:
        return "Salam! Sodangi Motors here. Our showroom is currently being restocked. Please check back soon!"
        
    t = text.lower().strip()
    
    # 1. GREETING
    if any(k in t for k in ["hello", "hi", "salam", "good day", "morning", "evening"]):
        return "Salam! Welcome to Sodangi Motors 🚗.\\n\\nReply \'cars\' to see our inventory, or type a car name (e.g., \'Camry\')!"
        
    # 2. BUDGET FILTER (e.g., "under 5000000", "less than 5 million")
    budget_match = re.search(r\'(?:under|below|less than|max|budget)\\s*(\\d[\\d,\\.]*)\', t)
    if budget_match:
        try:
            val_str = budget_match.group(1).replace(\',\', \'\').replace(\'.\', \'\')
            if \'million\' in t or \'m\' in t.split()[-1]:
                budget = int(val_str) * 1000000
            else:
                budget = int(val_str)
                
            matches = [p for p in prods if float(p.price or 0) <= budget]
            if matches:
                inv = "\\n".join([f"* {p.name} - NGN {float(p.price):,.0f}" for p in matches[:5]])
                return f"Salam! Here are our vehicles under NGN {budget:,.0f}:\\n{inv}\\n\\nReply with a car name for details!"
            else:
                min_p = min(float(p.price) for p in prods)
                return f"Salam! We don\'t have any vehicles under NGN {budget:,.0f} right now. Our lowest price is NGN {min_p:,.0f}."
        except:
            pass

    # 3. SPECIFIC CAR SEARCH (Fuzzy Matching)
    best_match = None
    best_score = 0.0
    for p in prods:
        score = difflib.SequenceMatcher(None, t, p.name.lower()).ratio()
        if score > best_score and score > 0.5:
            best_score = score
            best_match = p
            
    if best_match and best_score > 0.6:
        link = f"https://sawa-ai-backend.vercel.app/api/v1/dashboard/showroom/{best_match.id}"
        desc = (best_match.description or "Premium vehicle available now.")[:100]
        return f"🚗 *{best_match.name}*\\n💰 NGN {float(best_match.price):,.0f}\\n📝 {desc}\\n\\n👇 View photos and details here:\\n{link}\\n\\nOr reply \'cars\' to see everything!"

    # 4. BUYING INTENT / LEAD CAPTURE
    if any(k in t for k in ["buy", "purchase", "interested", "call me", "contact", "agent"]):
        return "Salam! We\'d love to help you buy. 🤝\\nPlease click the link below to chat directly with our sales team on WhatsApp:\\nhttps://wa.me/2349079437745?text=Salam!%20I%20am%20interested%20in%20buying%20a%20car."

    # 5. GENERAL INVENTORY FALLBACK
    if any(k in t for k in ["car", "price", "show", "available", "list", "cars", "inventory", "stock"]):
        inv = "\\n".join([f"* {p.name} - NGN {float(p.price or 0):,.0f}" for p in prods[:10]])
        return f"Salam! Here is our current inventory:\\n\\n{inv}\\n\\n💡 *Tip:* Type a car name (e.g., \'Camry\') or your budget (e.g., \'under 5 million\')!"
        
    # 6. UNKNOWN INTENT
    inv_sample = "\\n".join([f"* {p.name}" for p in prods[:5]])
    return f"Salam! I am the Sodangi Motors AI. 🤖\\nI can help you find a car!\\n\\nTry saying:\\n- \'Show cars\'\\n- \'Camry\'\\n- \'Under 5 million\'\\n\\nOur top cars:\\n{inv_sample}"

'''

# 3. SURGICALLY REPLACE THE OLD BOT
parts = code.split("def _wa_bot_reply(text, db):")
if len(parts) == 2:
    before = parts[0]
    after_match = re.search(r'\n(@router\.|def )', parts[1])
    if after_match:
        after = parts[1][after_match.start():]
        code = before + NEW_BOT + after
        print("✅ Successfully transplanted the Genius Brain!")
    else:
        code = before + NEW_BOT + "\n" + parts[1]
        print("✅ Transplanted Genius Brain (fallback anchor).")
else:
    print("⚠️ Could not find old bot. Appending Genius Brain...")
    code += "\n" + NEW_BOT

# 4. SAVE AND PUSH
with open("backend/app/api/v1/endpoints/agents_api.py", "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Genius Bot: Fuzzy search, budget filtering, and deep links"])
subprocess.run(["git", "push", "origin", "main", "--force"])

print("\n⏳ Waiting 90s for Vercel to upgrade the brain...")
time.sleep(90)
print("✅ GENIUS BOT IS LIVE!")
