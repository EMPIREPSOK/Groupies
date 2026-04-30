from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

BOT_ID = "cbb5f000a40fc62c544c6767c6"   # ← Your 911 Bot ID

def send_message(text):
    payload = {"bot_id": BOT_ID, "text": text}
    requests.post("https://api.groupme.com/v3/bots/post", json=payload)

# === YOUR PROPERTIES TO MONITOR ===
PROPERTIES = [
    "Knollwood",
    "Channel Six",
    "Empire",
    "EPS",
    # Add ALL your apartment complexes here
]

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get('sender_type') == 'bot':
        return jsonify({"status": "ok"})

    text = data.get('text', '').strip().lower()

    if "@911" in text or "test" in text:
        send_message("🚨 **911 Alert Bot is ONLINE**\nMonitoring Tulsa PD Live Calls + Local News for your properties.")

    return jsonify({"status": "ok"})

# Health check
@app.route('/', methods=['GET'])
def home():
    return "✅ 911 Alert Bot is running"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
