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

    # Handle Facebook / external links
    link = None
    if "facebook.com" in text or "fb.com" in text:
        for word in text.split():
            if "facebook.com" in word or "fb.com" in word:
                link = word
                break

    if image_url:
        send_message("🔍 **Fox hunting...** Analyzing uploaded photo + any links.")
        response = f"""🧪 **Fox Results**

**Uploaded Photo:**
• Reverse searches ready:
• [Google](https://www.google.com/searchbyimage?image_url={image_url})
• [Yandex (Best for faces)](https://yandex.com/images/search?rpt=imageview&url={image_url})

**Facebook Link Detected:**
• {link if link else 'None'}
• Opening in browser recommended for manual check."""

    elif link:
        send_message(f"🔍 **Fox checking Facebook link:**\n{link}\n\nFox can't access private FB posts directly. Open the link and post a screenshot/photo for full analysis.")
    else:
        send_message("📸 Post a photo or Facebook link + @Fox check")

    send_message(response if 'response' in locals() else "Fox is ready.")
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
