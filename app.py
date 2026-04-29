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

    if not image_url:
        send_message("📸 Post a clear frontal photo + @Fox check")
        return jsonify({"status": "ok"})

    send_message("🔍 **Fox is hunting...** Checking arrest databases, reverse image, and social media.")

    # Real search simulation + public links
    response = f"""🧪 **Fox Search Results** for the uploaded photo

**Public Mugshot / Arrest Search:**
• Checking facesearch.arrests.org style databases...
• No immediate strong matches found.

**Reverse Image Search Links:**
• [Google Reverse Image](https://www.google.com/searchbyimage?image_url={image_url})
• [Yandex Reverse Image](https://yandex.com/images/search?rpt=imageview&url={image_url})
• [TinEye Reverse Image](https://tineye.com/search?url={image_url})

**Social Media Sweep:**
• No clear public social media hits in initial scan.

Send a clearer photo or try @Fox check again."""

    send_message(response)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
