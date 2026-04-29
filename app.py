import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_ID = "b0e2a0192ef5a18f702e6f5925"   # ← Fox Bot ID
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"

def send_message(text):
    payload = {"bot_id": BOT_ID, "text": text}
    requests.post(GROUPME_POST_URL, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get('sender_type') == 'bot':
        return jsonify({"status": "ok"})

    text = data.get('text', '').strip()
    lower = text.lower()
    attachments = data.get('attachments', [])

    # Only respond when mentioned
    if "@fox" not in lower:
        return jsonify({"status": "ok"})

    image_url = None
    if attachments and attachments[0].get('type') == 'image':
        image_url = attachments[0].get('url')

    if not image_url:
        send_message("📸 Post a clear photo of the person + @Fox check")
        return jsonify({"status": "ok"})

    send_message("🔍 **Fox is searching** public sources and arrest databases for this person...\nThis may take 10-20 seconds.")

    # Basic placeholder response (we'll expand with real search next)
    send_message("""🧪 **Fox Search Results**

No strong public matches found in initial scan.

• Reverse image search running...
• Arrest database check running...
• Social media & web search running...

Send another photo or type @Fox help for commands.""")
    
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
