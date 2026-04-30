from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_ID = "cbb5f000a40fc62c544c6767c6"

def send_message(text):
    payload = {"bot_id": BOT_ID, "text": text}
    requests.post("https://api.groupme.com/v3/bots/post", json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get('sender_type') == 'bot':
        return jsonify({"status": "ok"})

    text = data.get('text', '').strip().lower()

    if "@911" in text:
        send_message("✅ **911 Alert Bot is responding!**")

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
