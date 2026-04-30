from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

BOT_ID = "YOUR_EPS_ALERT_BOT_ID_HERE"   # ← Paste the new Bot ID here

def send_message(text):
    payload = {"bot_id": BOT_ID, "text": text}
    requests.post("https://api.groupme.com/v3/bots/post", json=payload)

# Your properties to monitor
PROPERTIES = [
    "Knollwood", "Channel Six", "Empire", "EPS",
    # Add all your apartment names here, one per line
]

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get('sender_type') == 'bot':
        return jsonify({"status": "ok"})

    text = data.get('text', '').strip().lower()

    if "@alert" in text or "test" in text:
        send_message("✅ **EPS Alert Bot is online**\nMonitoring Tulsa PD Live Calls + Local News for your properties.")

    return jsonify({"status": "ok"})

# Simple status check
@app.route('/', methods=['GET'])
def home():
    return "EPS Alert Bot is running"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
