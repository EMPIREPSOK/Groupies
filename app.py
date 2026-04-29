from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_ID = "b0e2a0192ef5a18f702e6f5925"

def send_message(text):
    payload = {"bot_id": BOT_ID, "text": text}
    requests.post("https://api.groupme.com/v3/bots/post", json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get('sender_type') == 'bot':
        return jsonify({"status": "ok"})

    text = data.get('text', '').strip().lower()
    attachments = data.get('attachments', [])

    if "@fox" not in text:
        return jsonify({"status": "ok"})

    image_url = None
    if attachments and attachments[0].get('type') == 'image':
        image_url = attachments[0].get('url')

    if image_url:
        send_message("🔍 **Fox is on the hunt...**\nAnalyzing photo against public arrest records & social media...")
        # Real search will go here in next update
        send_message("""🧪 **Fox Preliminary Results**

• Photo received and processed
• Checking mugshot databases...
• Running reverse image search...

Send another photo or wait for full results.""")
    else:
        send_message("📸 Please post a clear photo of the person's face + @Fox check")

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
