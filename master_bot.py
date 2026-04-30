import os
import time
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ══════════════════════════════════════════════════════════════════
#  FIREBASE CONFIG (Royal Darbar)
# ══════════════════════════════════════════════════════════════════
FIREBASE_PROJECT = "royal-darbar-1"
FIREBASE_API_KEY = "AIzaSyAyr0rhJLng0d2FWxSBYBw7a2R4YadqkaE"

def get_bot_config():
    try:
        url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT}/databases/(default)/documents/config/bot?key={FIREBASE_API_KEY}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            fields = r.json().get("fields", {})
            cfg = {}
            for k, v in fields.items():
                if "booleanValue" in v:
                    cfg[k] = v["booleanValue"]
                elif "stringValue" in v:
                    cfg[k] = v["stringValue"]
                elif "integerValue" in v:
                    cfg[k] = int(v["integerValue"])
            return cfg
    except Exception as e:
        print(f"[FIREBASE] Config fetch error: {e}")
    return {}

# ══════════════════════════════════════════════════════════════════
#  CLIENT REGISTRY
# ══════════════════════════════════════════════════════════════════
CLIENTS = {
    "medisoft": {
        "name":         "MediSoft Pharmacy",
        "fonnte_token": os.environ.get("MEDISOFT_FONNTE", "W4ZDb6dcnTGCAacJwRjp"),
        "admin_phone":  os.environ.get("MEDISOFT_PHONE", "918407853708"),
        "website":      "https://medisoft.netlify.app",
        "address":      "Patna, Bihar",
        "timing":       "08:00 AM - 10:00 PM",
        "emoji":        "💊",
        "use_firebase": False,
        "structured":   False,
    },
    "royaldarbar": {
        "name":         "Royal Darbar Restaurant & Resort",
        "fonnte_token": os.environ.get("ROYAL_FONNTE", "bixhuKjh9aJb87X2DCKT"),
        "admin_phone":  os.environ.get("ROYAL_PHONE", "918434928777"),
        "website":      "https://royal-darbar1.netlify.app",
        "address":      "Matiara Tok, Sarai, Bihar",
        "timing":       "10:00 AM - 11:00 PM",
        "emoji":        "🍽️",
        "use_firebase": True,
        "structured":   True,
    },
}

# ══════════════════════════════════════════════════════════════════
#  USER SESSION (in-memory)
# ══════════════════════════════════════════════════════════════════
user_sessions = {}

def get_session(phone):
    if phone not in user_sessions:
        user_sessions[phone] = {"step": "menu", "last_seen": time.time()}
    user_sessions[phone]["last_seen"] = time.time()
    return user_sessions[phone]

def clean_sessions():
    while True:
        time.sleep(3600)
        cutoff = time.time() - 7200  # 2 hours
        for p in list(user_sessions.keys()):
            if user_sessions[p]["last_seen"] < cutoff:
                del user_sessions[p]

threading.Thread(target=clean_sessions, daemon=True).start()

# ══════════════════════════════════════════════════════════════════
#  SELF PING
# ══════════════════════════════════════════════════════════════════
def self_ping():
    time.sleep(10)
    while True:
        try:
            url = os.environ.get("SELF_URL", "https://royal-darbar1.onrender.com")
            r = requests.get(f"{url}/health", timeout=10)
            print(f"[PING] ok → {r.status_code}")
        except Exception as e:
            print(f"[PING ERROR] {e}")
        time.sleep(300)

threading.Thread(target=self_ping, daemon=True).start()

# ══════════════════════════════════════════════════════════════════
#  MESSAGING
# ══════════════════════════════════════════════════════════════════
def send_msg(client, phone, text):
    try:
        phone = str(phone).replace("+", "").replace(" ", "").replace("-", "")
        payload = {"target": phone, "message": text, "countryCode": "91"}
        headers = {"Authorization": client["fonnte_token"]}
        r = requests.post("https://api.fonnte.com/send", data=payload, headers=headers, timeout=10)
        print(f"[FONNTE] {phone} → {r.status_code} | {r.text[:100]}")
    except Exception as e:
        print(f"[SEND ERROR] {e}")

# ══════════════════════════════════════════════════════════════════
#  STRUCTURED BOT — Royal Darbar
# ══════════════════════════════════════════════════════════════════
MENU_MSG = """🍽️ *Royal Darbar Restaurant & Resort*
_Aapka swagat hai!_ 🙏

Aap kya jaanna chahte hain?

1️⃣ Menu & Prices
2️⃣ Table Booking
3️⃣ Timing & Location
4️⃣ Website
5️⃣ Contact

👉 *Sirf number bhejein* (1-5)"""

def structured_reply(client, sender, message):
    session = get_session(sender)
    msg = message.strip().lower()

    # Reset keywords
    if any(w in msg for w in ["hi", "hello", "hii", "hey", "menu", "start", "help", "namaste", "namaskar"]):
        session["step"] = "menu"
        return MENU_MSG

    step = session.get("step", "menu")

    if step == "menu":
        if msg in ["1", "menu", "price"]:
            session["step"] = "menu"
            return (
                f"🍽️ *Royal Darbar Menu*\n\n"
                f"Hamare complete menu ke liye website visit karein:\n"
                f"🌐 {client['website']}\n\n"
                f"Kuch aur jaanna hai?\n"
                f"0️⃣ *Main Menu pe wapas jayen*"
            )
        elif msg in ["2", "booking", "book", "table"]:
            session["step"] = "menu"
            return (
                f"📅 *Table Booking*\n\n"
                f"Booking ke liye:\n"
                f"📞 Call karein: +{client['admin_phone']}\n"
                f"🌐 Website: {client['website']}\n\n"
                f"Ya directly aayein:\n"
                f"📍 {client['address']}\n\n"
                f"0️⃣ *Main Menu pe wapas jayen*"
            )
        elif msg in ["3", "timing", "location", "address", "time"]:
            session["step"] = "menu"
            return (
                f"⏰ *Timing & Location*\n\n"
                f"🕙 *Khulne ka samay:* {client['timing']}\n"
                f"📍 *Address:* {client['address']}\n\n"
                f"🗺️ Google Maps pe dhundhen:\n"
                f"_Royal Darbar Restaurant Sarai Bihar_\n\n"
                f"0️⃣ *Main Menu pe wapas jayen*"
            )
        elif msg in ["4", "website", "site", "web"]:
            session["step"] = "menu"
            return (
                f"🌐 *Hamari Website*\n\n"
                f"{client['website']}\n\n"
                f"Website pe aap dekh sakte hain:\n"
                f"✅ Poora menu\n"
                f"✅ Online order\n"
                f"✅ Table booking\n\n"
                f"0️⃣ *Main Menu pe wapas jayen*"
            )
        elif msg in ["5", "contact", "phone", "number", "call"]:
            session["step"] = "menu"
            return (
                f"📞 *Contact Us*\n\n"
                f"📱 WhatsApp / Call:\n+{client['admin_phone']}\n\n"
                f"📍 *Address:* {client['address']}\n"
                f"⏰ *Timing:* {client['timing']}\n\n"
                f"0️⃣ *Main Menu pe wapas jayen*"
            )
        elif msg in ["0", "back", "wapas", "main"]:
            session["step"] = "menu"
            return MENU_MSG
        else:
            return (
                f"🙏 Kripya *1 se 5* ke beech koi number bhejein.\n\n"
                + MENU_MSG
            )
    return MENU_MSG

# ══════════════════════════════════════════════════════════════════
#  SIMPLE REPLY — MediSoft
# ══════════════════════════════════════════════════════════════════
def simple_reply(client):
    return (
        f"{client['emoji']} *{client['name']}*\n\n"
        f"🌐 *Website:*\n{client['website']}\n\n"
        f"📍 *Address:*\n{client['address']}\n\n"
        f"⏰ *Timing:* {client['timing']}\n\n"
        f"📞 *Contact:*\n+{client['admin_phone']}"
    )

# ══════════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ══════════════════════════════════════════════════════════════════
@app.route("/webhook/<client_id>", methods=["GET", "POST"])
def webhook(client_id):
    if client_id not in CLIENTS:
        return jsonify({"status": "unknown client"}), 404

    if request.method == "GET":
        return jsonify({"status": "ok"}), 200

    try:
        if request.content_type and "application/json" in request.content_type:
            data = request.json or {}
        else:
            data = request.form.to_dict() or request.json or {}

        print(f"[WEBHOOK/{client_id}] Raw: {data}")

        sender  = (data.get("sender") or data.get("from") or "").strip()
        message = (data.get("message") or data.get("text") or "").strip()

        if not sender or not message:
            return jsonify({"status": "ignored"}), 200

        client       = CLIENTS[client_id]
        admin_clean  = client["admin_phone"].replace("+", "").replace(" ", "")
        sender_clean = sender.replace("+", "").replace(" ", "")

        if sender_clean == admin_clean:
            return jsonify({"status": "self"}), 200

        print(f"[WEBHOOK/{client_id}] From: {sender} | Msg: {message}")

        # Firebase bot config check (Royal Darbar only)
        if client.get("use_firebase"):
            cfg = get_bot_config()
            if not cfg.get("is_active", True):
                offline = cfg.get("offline_message", "")
                if offline:
                    time.sleep(0.5)
                    send_msg(client, sender, offline)
                return jsonify({"status": "ok"}), 200

            if cfg.get("hours_only", True):
                start = cfg.get("working_hours_start", "10:00")
                end   = cfg.get("working_hours_end", "22:00")
                now   = time.strftime("%H:%M")
                if not (start <= now <= end):
                    offline = cfg.get("offline_message", f"Abhi hum band hain. Kal {start} baje se phir milenge. 🙏")
                    time.sleep(0.5)
                    send_msg(client, sender, offline)
                    return jsonify({"status": "ok"}), 200

        # Get reply
        if client.get("structured"):
            reply = structured_reply(client, sender_clean, message)
        else:
            reply = simple_reply(client)

        time.sleep(0.5)
        send_msg(client, sender, reply)
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"[ERROR webhook/{client_id}] {e}")
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    clients_info = "".join(
        f"<li><b>{cid}</b> ({c['name']}) — /webhook/{cid}</li>"
        for cid, c in CLIENTS.items()
    )
    return f"<h2>🤖 Next Gen Web — Master Bot (2 Clients)</h2><ul>{clients_info}</ul><p>✅ Running</p>"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running", "clients": list(CLIENTS.keys())})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
