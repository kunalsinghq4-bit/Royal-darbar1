import os
import time
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ══════════════════════════════════════════════════════════════════
#  CLIENT REGISTRY — 2 Clients
# ══════════════════════════════════════════════════════════════════
CLIENTS = {

    "medisoft": {
        "name":          "MediSoft Pharmacy",
        "fonnte_token":  os.environ.get("MEDISOFT_FONNTE", "W4ZDb6dcnTGCAacJwRjp"),
        "admin_phone":   os.environ.get("MEDISOFT_PHONE",  "918407853708"),
        "website":       "https://medisoft.netlify.app",
        "address":       "Patna, Bihar",
        "timing":        "08:00 AM - 10:00 PM",
        "emoji":         "💊",
    },

    "royaldarbar": {
        "name":          "Royal Darbar Restaurant & Resort",
        "fonnte_token":  os.environ.get("ROYAL_FONNTE", "bixhuKjh9aJb87X2DCKT"),
        "admin_phone":   os.environ.get("ROYAL_PHONE",  "918434928777"),
        "website":       os.environ.get("ROYAL_WEBSITE", "https://royal-darbar.netlify.app"),
        "address":       "Matiara Tok, Sarai, Bihar",
        "timing":        "10:00 AM - 11:00 PM",
        "emoji":         "🍽️",
    },

}

# ══════════════════════════════════════════════════════════════════
#  SELF PING
# ══════════════════════════════════════════════════════════════════
def self_ping():
    time.sleep(10)
    while True:
        try:
            url = os.environ.get("SELF_URL", "https://master-bot.onrender.com")
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
        payload = {
            "target":      phone,
            "message":     text,
            "countryCode": "91"
        }
        headers = {"Authorization": client["fonnte_token"]}
        r = requests.post("https://api.fonnte.com/send", data=payload, headers=headers, timeout=10)
        print(f"[FONNTE] {phone} → {r.status_code} | {r.text[:100]}")
    except Exception as e:
        print(f"[SEND ERROR] {e}")

# ══════════════════════════════════════════════════════════════════
#  AUTO REPLY — Kuch bhi aaye, yahi reply
# ══════════════════════════════════════════════════════════════════
def auto_reply(client):
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
@app.route("/webhook/<client_id>", methods=["POST"])
def webhook(client_id):
    if client_id not in CLIENTS:
        return jsonify({"status": "unknown client"}), 404
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

        # Admin ka message ignore karo
        if sender_clean == admin_clean:
            return jsonify({"status": "self"}), 200

        print(f"[WEBHOOK/{client_id}] From: {sender} | Msg: {message}")

        # Kuch bhi aaye — auto reply bhejo
        time.sleep(0.5)
        send_msg(client, sender, auto_reply(client))

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
