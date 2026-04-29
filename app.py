from flask import Flask, request, jsonify
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

    fb_link = re.search(r'https?://[^\s]*facebook\.com[^\s]*', text)
    fb_link = fb_link.group(0) if fb_link else None

    image_url = None
    if attachments and attachments[0].get('type') == 'image':
        image_url = attachments[0].get('url')

    if image_url:
        send_message("🔍 **Fox analyzing photo from mugshot page...**")
        send_message(f"""🧪 **Fox Results**

**Reverse Image Search (Best for Mugshots):**
• [Yandex Reverse Image](https://yandex.com/images/search?rpt=imageview&url={image_url}) ← **Recommended first**
• [Google Reverse Image](https://www.google.com/searchbyimage?image_url={image_url})
• [TinEye](https://tineye.com/search?url={image_url})

Try these links — they work well on mugshots.""")

    elif fb_link:
        send_message(f"""🔍 **Fox detected Mugshot Facebook Page:**

{fb_link}

**Best Workflow for Mugshot Pages:**
1. Open the Facebook link
2. Find the person you want to identify
3. Take a **clear screenshot** of their face (zoom in if needed)
4. Post the screenshot here with `@Fox check`

Fox will then run strong reverse image searches on it.""")

    else:
        send_message("📸 Post a screenshot from the mugshot page + @Fox check")

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
