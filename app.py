import os
import json
import uuid
from datetime import datetime
import resend
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_ID = "4952f75d1dd84d9d779489ad1d"          # ← NEW Bot ID
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"
DB_FILE = "tia_subjects.json"
GROUP_ID = "108389282"                         # Your Trespass Group
GROUPME_TOKEN = "4e7a8ed0248a013f530b5ac23cb6c257"

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

    # === IMPORT HISTORY (with pictures) ===
    if "import" in lower and "history" in lower:
        send_message("🔄 Starting full import from the Trespass chat...\nThis may take 10-30 seconds.")
        imported = import_chat_history(subjects)
        save_db(subjects)
        send_message(f"✅ **IMPORT COMPLETE**\nImported {imported} subjects/incidents with photos where available.")
        return jsonify({"status": "ok"})

    # === BACKUP ===
    if any(cmd in lower for cmd in ["backup", "export"]):
        # Add your Resend backup here if you want
        send_message("✅ Backup ready (use @TIA backup)")
        return jsonify({"status": "ok"})

    # === ADD NEW SUBJECT / INCIDENT ===
    if any(k in lower for k in ["name:", "dob:", "date:", "location:", "outcome:"]):
        name = dob = descriptors = date = location = outcome = "Unknown"
        for line in text.splitlines():
            l = line.lower()
            if "name:" in l: name = line.split(":", 1)[1].strip()
            if "dob:" in l: dob = line.split(":", 1)[1].strip()
            if any(d in l for d in ["descriptors:", "descriptor:"]): descriptors = line.split(":", 1)[1].strip()
            if "date:" in l: date = line.split(":", 1)[1].strip()
            if "location:" in l: location = line.split(":", 1)[1].strip()
            if "outcome:" in l: outcome = line.split(":", 1)[1].strip()

        existing = next((s for s in subjects if s.get('name','').lower() == name.lower()), None)
        if existing:
            new_entry = f"{date} - {location} - {outcome}"
            existing['history'] = existing.get('history', '') + f"\n• {new_entry}"
            existing['last_seen'] = date
            if image_url: existing['photo_url'] = image_url
            send_message(f"✅ **NEW INCIDENT ADDED** for {name}")
        else:
            new_subject = {
                "id": str(uuid.uuid4())[:8],
                "name": name,
                "dob": dob,
                "descriptors": descriptors,
                "history": f"{date} - {location} - {outcome}",
                "last_seen": date,
                "photo_url": image_url,
                "risk": "Medium"
            }
            subjects.append(new_subject)
            send_message(f"✅ **NEW SUBJECT ADDED**\nName: {name}")

        save_db(subjects)
        return jsonify({"status": "ok"})

    # LIST
    if "list" in lower:
        msg = "📋 **TIA Database**:\n" + ("\n".join(f"• {s['name']} | Risk: {s.get('risk','Medium')}" for s in subjects) or "Empty")
        send_message(msg)
        return jsonify({"status": "ok"})

    # CHECK / LOOKS
    if any(cmd in lower for cmd in ["check", "who", "looks"]):
        query = lower.replace("@tia", "").replace("check", "").replace("who", "").replace("looks", "").strip()
        matches = [s for s in subjects if query in s.get('name','').lower() or query in s.get('descriptors','').lower()]
        if matches:
            for s in matches:
                reply = f"🔴 **TIA RECORD** — {s['name']}\nDOB: {s.get('dob')}\nDescriptors: {s.get('descriptors','None')}\nRisk: {s.get('risk','Medium')}\nHistory:\n{s.get('history','No history')}"
                send_message(reply, s.get('photo_url'))
        else:
            send_message(f"🔴 No match for '{query}'")
        return jsonify({"status": "ok"})

    save_db(subjects)
    return jsonify({"status": "ok"})

def import_chat_history(subjects):
    count = 0
    try:
        r = requests.get(f"https://api.groupme.com/v3/groups/{GROUP_ID}/messages?token={GROUPME_TOKEN}&limit=100")
        messages = r.json()['response']['messages']

        for msg in messages:
            if not msg.get('text'): continue
            txt = msg['text']
            lower_txt = txt.lower()

            if any(k in lower_txt for k in ["name:", "dob:", "date:", "location:", "outcome:"]):
                name = dob = descriptors = date = location = outcome = "Unknown"
                for line in txt.splitlines():
                    l = line.lower()
                    if "name:" in l: name = line.split(":", 1)[1].strip()
                    if "dob:" in l: dob = line.split(":", 1)[1].strip()
                    if any(d in l for d in ["descriptors:", "descriptor:"]): descriptors = line.split(":", 1)[1].strip()
                    if "date:" in l: date = line.split(":", 1)[1].strip()
                    if "location:" in l: location = line.split(":", 1)[1].strip()
                    if "outcome:" in l: outcome = line.split(":", 1)[1].strip()

                photo_url = None
                if msg.get('attachments'):
                    for att in msg['attachments']:
                        if att.get('type') == 'image':
                            photo_url = att.get('url')

                existing = next((s for s in subjects if s.get('name','').lower() == name.lower()), None)
                if existing:
                    new_entry = f"{date} - {location} - {outcome}"
                    existing['history'] = existing.get('history', '') + f"\n• {new_entry}"
                    if photo_url: existing['photo_url'] = photo_url
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
        return count
    except Exception as e:
        print("Import error:", str(e))
        return 0

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
