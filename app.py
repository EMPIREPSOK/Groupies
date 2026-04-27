from flask import Flask, request, jsonify
import requests
import sqlite3

app = Flask(__name__)

BOT_ID = "0bd071f6a87fec9fcb76d39586"
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"

# Initialize Database
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

    if image_url or any(k in text for k in ["check", "tia", "who", "subject"]):
        reply += "📸 Image or request received.\n"
        if image_url:
            reply += f"Image URL: {image_url}\n\n"
        reply += "Send details to add:\nName | DOB | Date | Location | Outcome"

    send_message(reply)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
