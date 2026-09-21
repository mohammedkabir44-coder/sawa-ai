import subprocess, time, ast

file_path = "backend/app/api/v1/endpoints/agents_api.py"
print("Reading file...")
with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# ============ 1. BACKEND: WEBHOOK + AI BRAIN (append to end of file) ============
BACKEND = '''

# ============ AI AUTO-RESPONDER (WhatsApp 24/7 Bot) ============
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "1332619033263966")
WA_VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "sodangi_verify_2026")

def _wa_send(to_phone, message):
    token = os.getenv("WHATSAPP_TOKEN", "")
    if not token:
        return False
    url = "https://graph.facebook.com/v25.0/" + WA_PHONE_ID + "/messages"
    data = json.dumps({"messaging_product": "whatsapp", "to": to_phone, "type": "text", "text": {"preview_url": False, "body": message}}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception:
        return False

def _wa_bot_reply(text, db):
    prods = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.id.desc()).limit(6).all()
    car_words = ["car", "price", "show", "buy", "available", "list", "suv", "camry", "lexus", "toyota", "benz"]
    if any(k in text for k in car_words):
        if not prods:
            return "Salam! Sodangi Motors here. No cars in stock right now, please check back soon!"
        lines = ["Salam! Welcome to Sodangi Motors.", "Available vehicles today:", ""]
        for p in prods:
            lines.append("* " + str(p.name) + " - NGN " + format(float(p.price or 0), ",.0f"))
        lines.append("")
        lines.append("Reply with the car name for photos, or WhatsApp us to book a test drive!")
        return "\\n".join(lines)
    if any(k in text for k in ["hello", "hi", "salam", "good day"]):
        return "Salam! Welcome to Sodangi Motors. Reply 'cars' to see today's available vehicles with prices."
    return "Salam! Sodangi Motors here. Reply 'cars' to see available vehicles with prices, or tell us what you need (e.g. 'SUV under 5 million')."

@router.get("/whatsapp-webhook")
async def wa_webhook_verify(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == WA_VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp-webhook")
async def wa_webhook_receive(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored"}
    try:
        entries = payload.get("entry") or []
        if not entries:
            return {"status": "ok"}
        changes = entries[0].get("changes") or []
        if not changes:
            return {"status": "ok"}
        value = changes[0].get("value") or {}
        messages = value.get("messages") or []
        if not messages:
            return {"status": "ok"}
        msg = messages[0]
        sender = msg.get("from", "")
        body = ((msg.get("text") or {}).get("body") or "").lower()
        if not sender:
            return {"status": "ok"}
        Setting.__table__.create(bind=db.get_bind(), checkfirst=True)
        row = db.query(Setting).filter(Setting.key == "ai_bot_enabled").first()
        if row and row.value == "off":
            return {"status": "bot_off"}
        reply = _wa_bot_reply(body, db)
        _wa_send(sender, reply)
        return {"status": "replied"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.get("/ai-bot/status")
def ai_bot_status(request: Request, db: Session = Depends(get_db)):
    _auth(request)
    Setting.__table__.create(bind=db.get_bind(), checkfirst=True)
    row = db.query(Setting).filter(Setting.key == "ai_bot_enabled").first()
    enabled = (row.value != "off") if row else True
    return {"enabled": enabled, "callback_url": "https://sawa-ai-backend.vercel.app/api/v1/dashboard/whatsapp-webhook", "verify_token": WA_VERIFY_TOKEN}

@router.post("/ai-bot/toggle")
def ai_bot_toggle(request: Request, db: Session = Depends(get_db)):
    _owner(_auth(request))
    Setting.__table__.create(bind=db.get_bind(), checkfirst=True)
    row = db.query(Setting).filter(Setting.key == "ai_bot_enabled").first()
    current = (row.value != "off") if row else True
    new_val = "off" if current else "on"
    if row:
        row.value = new_val
    else:
        db.add(Setting(key="ai_bot_enabled", value=new_val))
    db.commit()
    return {"enabled": new_val == "on"}
'''

if "/whatsapp-webhook" not in code:
    code = code + BACKEND
    print("✅ Injected WhatsApp Webhook + AI Brain!")
else:
    print("ℹ️ Webhook already present.")

# ============ 2. FRONTEND: Add Bot tab ============
if '"Bot"' not in code:
    code = code.replace('["Upload","Cars","Agents","Stats","Profile","Leads","Leaderboard","SMS"].forEach', '["Upload","Cars","Agents","Stats","Profile","Leads","Leaderboard","SMS","Bot"].forEach')
    code = code.replace('if(tab==="Leaderboard")loadLeaderboard();', 'if(tab==="Leaderboard")loadLeaderboard();if(tab==="Bot")loadBot();')
    code = code.replace('<button id="navProfile"', '<button id="navBot" onclick="go(\'Bot\')"><span>&#129302;</span>Bot</button>\n  <button id="navProfile"')
    bot_section = '''  <section id="tabBot" class="card hidden">
    <h2>&#129302; AI Auto-Responder</h2>
    <p style="color:#94A3B8;font-size:13px;margin-bottom:12px">24/7 WhatsApp bot that replies to buyers with your live inventory.</p>
    <div id="botStatus" style="margin-bottom:12px"></div>
    <button class="btn btn-primary" onclick="toggleBot()">Toggle Bot On/Off</button>
    <hr style="margin:16px 0;border-color:#334155">
    <label>Meta Callback URL (copy into Meta dashboard):</label>
    <input readonly value="https://sawa-ai-backend.vercel.app/api/v1/dashboard/whatsapp-webhook" onclick="this.select()">
    <label>Verify Token:</label>
    <input readonly value="sodangi_verify_2026" onclick="this.select()">
  </section>
'''
    code = code.replace('<nav class="nav hidden" id="bottomNav">', bot_section + '<nav class="nav hidden" id="bottomNav">')
    bot_js = '''async function loadBot(){var box=document.getElementById("botStatus");try{var s=await api("/ai-bot/status","GET",null,true);box.innerHTML='<p style="color:'+(s.enabled?"#22C55E":"#EF4444")+';font-weight:700">Bot is '+(s.enabled?"ON - replying to buyers 24/7":"OFF")+'</p>';}catch(e){box.innerHTML='<p style="color:#EF4444">'+e.message+'</p>';}}
async function toggleBot(){try{var s=await api("/ai-bot/toggle","POST",{},true);alert("Bot is now "+(s.enabled?"ON":"OFF"));loadBot();}catch(e){alert(e.message);}}
'''
    code = code.replace('if(TOKEN){enterDash();}', bot_js + 'if(TOKEN){enterDash();}')
    print("✅ Added Bot control tab to dashboard!")

# ============ 3. VERIFY + SAVE + PUSH ============
try:
    ast.parse(code)
    print("✅ Python syntax valid!")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    raise SystemExit(1)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)
with open("backend/app/main.py", "a") as f:
    f.write(f"\n# BOT_BUILD_{int(time.time())}")

print("Pushing to GitHub...")
subprocess.run(["git", "add", "."], check=False)
subprocess.run(["git", "commit", "-m", "AI Auto-Responder: WhatsApp 24/7 bot with live inventory replies"], check=False)
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ Push successful!")
        break
    print(f"Push failed (attempt {i+1}), retrying...")
    time.sleep(5)
