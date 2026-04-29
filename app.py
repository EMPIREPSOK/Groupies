from flask import Flask, request, jsonify
import requests
import re

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

    # Detect Facebook link
    fb_link = None
    fb_match = re.search(r'https?://[^\s]*facebook\.com[^\s]*', text)
    if fb_match:
        fb_link = fb_match.group(0)

    image_url = None
    if attachments and attachments[0].get('type') == 'image':
        image_url = attachments[0].get('url')

    if image_url:
        send_message("🔍 **Fox analyzing uploaded photo...**")
        send_message(f"""🧪 **Fox Results**

**Reverse Image Search Links:**
• [Yandex (Best for faces)](https://yandex.com/images/search?rpt=imageview&url={image_url})
• [Google](https://www.google.com/searchbyimage?image_url={image_url})
• [TinEye](https://tineye.com/search?url={image_url})""")

    elif fb_link:
        send_message(f"""🔍 **Fox detected Mugshot Facebook Page:**

{fb_link}

**Recommended Workflow:**
1. Open the link
2. Find the person
3. Take a clear screenshot of their face
4. Post the screenshot here with `@Fox check`

Fox will run strong reverse searches on the screenshot.""")

    else:
        send_message("📸 Post a photo or Facebook mugshot link + @Fox check")

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
