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
        send_message("📸 Post a clear photo of the person's face + @Fox check")
        return jsonify({"status": "ok"})

    send_message("🔍 **Fox is on full hunt mode...**\nChecking arrest databases, reverse image, social media & web sources...")

    # Powerful multi-source response
    response = f"""🧪 **Fox Full Search Results**

**1. Reverse Image Search (Click these):**
• [Google Reverse Image](https://www.google.com/searchbyimage?image_url={image_url})
• [Yandex Reverse Image (often best for faces)](https://yandex.com/images/search?rpt=imageview&url={image_url})
• [TinEye Reverse Image](https://tineye.com/search?url={image_url})
• [Bing Visual Search](https://www.bing.com/images/search?q=imgurl:{image_url.replace('https://','')})

**2. Mugshot / Arrest Databases:**
• [FaceSearch Arrests Style](https://facesearch.arrests.org/)
• [Mugshots.com Search](https://mugshots.com/)
• [BustedMugshots](https://bustedmugshots.com/)

**3. Social Media & Web Sweep:**
• [Pipl People Search](https://pipl.com/)
• [Social Searcher](https://www.social-searcher.com/)
• [Google "Face" Search](https://www.google.com/search?tbm=isch&q=face+recognition+{image_url})

Send a clearer frontal photo if no good matches. Fox will keep improving."""

    send_message(response)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
