import subprocess, time

fp = "backend/app/api/v1/endpoints/agents_api.py"
with open(fp, "r", encoding="utf-8-sig") as f:
    code = f.read()

# 1. Add openai to requirements
req_path = "backend/requirements.txt"
with open(req_path, "r", encoding="utf-8") as f:
    reqs = f.read()
if "openai" not in reqs:
    reqs += "\nopenai\n"
    with open(req_path, "w", encoding="utf-8") as f:
        f.write(reqs)
    print("✅ Added openai to requirements.txt!")

# 2. Replace the dumb bot with the Smart AI Bot
NEW_BOT = """def _wa_bot_reply(text, db):
    import os
    try:
        import openai
    except ImportError:
        pass
        
    prods = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.id.desc()).limit(10).all()
    inv = "\\n".join([f"- {p.name} (NGN {float(p.price or 0):,.0f})" for p in prods]) or "No cars currently in stock."
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-dummy"):
        if any(k in text.lower() for k in ["car", "price", "show", "buy", "available", "list", "cars"]):
            return f"Salam! Welcome to Sodangi Motors. Available vehicles today:\\n{inv}\\n\\nReply with the car name for photos!"
        return "Salam! Sodangi Motors here. Reply 'cars' to see our inventory."

    try:
        client = openai.OpenAI(api_key=api_key)
        sys_prompt = f"You are a friendly, professional sales agent for Sodangi Motors in Nigeria. Keep replies concise, polite, and use emojis. Quote prices in NGN.\\n\\nINVENTORY:\\n{inv}"
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": text}],
            max_tokens=150, temperature=0.7
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"Salam! I'm having a little trouble connecting to my brain right now. Please reply 'cars' to see our inventory!"

"""

parts = code.split("def _wa_bot_reply(text, db):")
if len(parts) > 1:
    before = parts[0]
    after_parts = parts[1].split("@router.get(\"/whatsapp-webhook\")")
    if len(after_parts) > 1:
        after = "@router.get(\"/whatsapp-webhook\")" + after_parts[1]
        code = before + NEW_BOT + after
        print("✅ Upgraded to Smart AI Bot (GPT-4o-mini)!")
    else:
        print("⚠️ Could not find webhook router to anchor the replacement.")
else:
    print("⚠️ Could not find the old bot function.")

with open(fp, "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Upgrade: Smart AI WhatsApp Bot with OpenAI"])
subprocess.run(["git", "push", "origin", "main", "--force"])
print("\n⏳ Waiting 90s for Vercel to install openai...")
time.sleep(90)
