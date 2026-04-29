from flask import Flask, request, jsonify

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

    text = data.get('text', '').strip()
    lower = text.lower()
    attachments = data.get('attachments', [])

    if "@fox" not in lower:
        return jsonify({"status": "ok"})

    image_url = None
    if attachments and attachments[0].get('type') == 'image':
        image_url = attachments[0].get('url')

    if not image_url:
        send_message("📸 Post a clear photo of the person + @Fox check")
        return jsonify({"status": "ok"})

    send_message("🔍 **Fox is hunting this unknown person...**")

    response = f"""🧪 **Fox Results** (Unknown Person)

**Top Recommended Tools (Click these):**

• **[Yandex Reverse Image](https://yandex.com/images/search?rpt=imageview&url={image_url})** ← **Best starting point**
• **[Google Reverse Image](https://www.google.com/searchbyimage?image_url={image_url})**
• **[TinEye Reverse Image](https://tineye.com/search?url={image_url})**

**Mugshot Database:**
• [facesearch.arrests.org](https://facesearch.arrests.org/) ← Upload the photo directly here

**Quick Tip:**  
Start with **Yandex**, then try facesearch.arrests.org. These are the ones that work best for you.

Send another photo or clearer angle if needed."""

    send_message(response)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
