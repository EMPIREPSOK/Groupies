import os
import json
import uuid
from datetime import datetime
import resend
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_ID = "0bd071f6a87fec9fcb76d39586"
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"
DB_FILE = "tia_subjects.json"
GROUPME_TOKEN = "4e7a8ed0248a013f530b5ac23cb6c257"   # Your token

resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "TIA <security@ee15.net>")

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def send_message(text, image_url=None):
    payload = {"bot_id": BOT_ID, "text": text}
    if image_url:
        payload["attachments"] = [{"type": "image", "url": image_url}]
    requests.post(GROUPME_POST_URL, json=payload)

def send_email_backup():
    # ... (keep your existing email function)
    pass  # (add it back if needed)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get('sender_type') == 'bot':
        return jsonify({"status": "ok"})

    text = data.get('text', '').strip()
    lower = text.lower()
    attachments = data.get('attachments', [])
    image_url = attachments[0]['url'] if attachments and attachments[0].get('type') == 'image' else None

    subjects = load_db()

    # === ONE-TIME IMPORT FROM CHAT HISTORY ===
    if "import" in lower and "history" in lower:
        send_message("🔄 Starting full chat import with pictures... This may take a minute.")
        imported = import_chat_history()
        send_message(f"✅ **IMPORT COMPLETE**\nImported {imported} subjects/incidents with photos where available.")
        return jsonify({"status": "ok"})

    # === BACKUP ===
    if any(cmd in lower for cmd in ["backup", "export"]):
        # your backup code
        pass

    # === Your normal ADD, LIST, CHECK, LOOKS, 10-20, RISK commands here ===

    save_db(subjects)
    return jsonify({"status": "ok"})

def import_chat_history():
    count = 0
    subjects = load_db()
    group_id = None

    # First get all groups to find the trespass chat
    try:
        r = requests.get(f"https://api.groupme.com/v3/groups?token={GROUPME_TOKEN}")
        for g in r.json()['response']:
            if "trespass" in g['name'].lower() or "knollwood" in g['name'].lower() or len(g['messages']) > 50:  # guess the right group
                group_id = g['id']
                send_message(f"Found group: {g['name']}")
                break
    except:
        send_message("❌ Could not fetch groups")
        return 0

    if not group_id:
        send_message("❌ Could not find the trespass chat group")
        return 0

    # Pull messages (most recent first)
    try:
        r = requests.get(f"https://api.groupme.com/v3/groups/{group_id}/messages?token={GROUPME_TOKEN}&limit=100")
        messages = r.json()['response']['messages']

        for msg in messages:
            if not msg.get('text'):
                continue
            txt = msg['text']
            lower_txt = txt.lower()

            if any(k in lower_txt for k in ["name:", "dob:", "date:", "location:", "outcome:"]):
                # Parse the subject
                name = dob = descriptors = date = location = outcome = "Unknown"
                for line in txt.splitlines():
                    l = line.lower()
                    if "name:" in l: name = line.split(":",1)[1].strip()
                    if "dob:" in l: dob = line.split(":",1)[1].strip()
                    if any(d in l for d in ["descriptors:", "descriptor:"]): descriptors = line.split(":",1)[1].strip()
                    if "date:" in l: date = line.split(":",1)[1].strip()
                    if "location:" in l: location = line.split(":",1)[1].strip()
                    if "outcome:" in l: outcome = line.split(":",1)[1].strip()

                # Check if already exists
                existing = next((s for s in subjects if s.get('name','').lower() == name.lower()), None)
                photo_url = None
                if msg.get('attachments'):
                    for att in msg['attachments']:
                        if att.get('type') == 'image':
                            photo_url = att.get('url')

                if existing:
                    new_entry = f"{date} - {location} - {outcome}"
                    existing['history'] = existing.get('history', '') + f"\n• {new_entry}"
                    if photo_url:
                        existing['photo_url'] = photo_url
                else:
                    new_subject = {
                        "id": str(uuid.uuid4())[:8],
                        "name": name,
                        "dob": dob,
                        "descriptors": descriptors,
                        "history": f"{date} - {location} - {outcome}",
                        "last_seen": date,
                        "photo_url": photo_url,
                        "risk": "Medium"
                    }
                    subjects.append(new_subject)
                count += 1

        save_db(subjects)
        return count
    except Exception as e:
        send_message(f"Import error: {str(e)}")
        return 0

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
