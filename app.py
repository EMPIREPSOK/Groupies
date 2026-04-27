from flask import Flask, request, jsonify
import requests
import json
import os
import uuid

app = Flask(__name__)

BOT_ID = "0bd071f6a87fec9fcb76d39586"
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"
DB_FILE = "tia_subjects.json"

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
    attachments = data.get('attachments', [])
    image_url = attachments[0].get('url') if attachments else None
    lower = text.lower()

    subjects = load_db()

    # === ADD SUBJECT / NEW INCIDENT ===
    if any(k in lower for k in ["name:", "dob:", "date:", "location:", "outcome:"]):
        name = dob = descriptors = date = location = outcome = "Unknown"
        for line in text.splitlines():
            l = line.lower()
            if "name:" in l: name = line.split(":",1)[1].strip()
            if "dob:" in l: dob = line.split(":",1)[1].strip()
            if "descriptors:" in l or "descriptor:" in l: descriptors = line.split(":",1)[1].strip()
            if "date:" in l: date = line.split(":",1)[1].strip()
            if "location:" in l: location = line.split(":",1)[1].strip()
            if "outcome:" in l: outcome = line.split(":",1)[1].strip()

        existing = next((s for s in subjects if s['name'].lower() == name.lower()), None)
        if existing:
            new_entry = f"{date} - {location} - {outcome}"
            existing['history'] = f"{existing.get('history','')}\n• {new_entry}" if existing.get('history') else new_entry
            existing['last_seen'] = date
            if image_url:
                existing['photo_url'] = image_url
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

    # === LIST ===
    if any(w in lower for w in ["list", "all", "show", "database"]):
        if subjects:
            msg = f"📋 **TIA Database** ({len(subjects)} total):\n"
            for s in subjects:
                msg += f"• {s['name']} | Risk: {s.get('risk','Medium')}\n"
        else:
            msg = "Database empty."
        send_message(msg)
        return jsonify({"status": "ok"})

    # === LOCATION / 10-20 SEARCH ===
    if any(cmd in lower for cmd in ["10-20", "1020", "location", "property"]) or ("20" in lower and len(text.split()) <= 6):
        query = text.lower()
        for cmd in ["@tia", "10-20", "1020", "location", "property", " at ", "check"]:
            query = query.replace(cmd, "").strip()
        if query:
            matches = [s for s in subjects if query in s.get('history','').lower()]
            if matches:
                reply = f"🔴 **SUBJECTS AT {query.upper()}** ({len(matches)} found)\n\n
