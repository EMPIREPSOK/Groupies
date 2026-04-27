from flask import Flask, request, jsonify
import requests
import sqlite3
import os

app = Flask(__name__)

BOT_ID = "0bd071f6a87fec9fcb76d39586"
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"

def init_db():
    conn = sqlite3.connect('tia_subjects.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subjects (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    dob TEXT,
                    history TEXT,
                    last_seen TEXT,
                    notes TEXT,
                    risk TEXT,
                    photo_url TEXT)''')
    conn.commit()
    conn.close()

init_db()

def send_message(text):
    payload = {"bot_id": BOT_ID, "text": text}
    requests.post(GROUPME_POST_URL, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get('sender_type') == 'bot':
        return jsonify({"status": "ok"})

    text = data.get('text', '').lower()
    attachments = data.get('attachments', [])
    image_url = attachments[0].get('url') if attachments else None

    reply = "🔴 **TIA ACTIVE** ✅\n\n"

    if image_url or any(word in text for word in ["tia", "test", "check", "who", "subject", "photo"]):
        reply += "✅ Message & image received!\n"
        if image_url:
            reply += f"📸 Image URL: {image_url}\n\n"
        reply += "Ready to log new subject.\n"
        reply += "Send details like:\n"
        reply += "Name: Charles Jones\nDOB: 4-18-1991\nDate: Apr 26 2026\nLocation: Knollwood\nOutcome: Formal Trespass"

    send_message(reply)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
