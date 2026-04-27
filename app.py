import os
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_ID = "0bd071f6a87fec9fcb76d39586"
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"
DB_FILE = "tia_subjects.json"
LAST_BACKUP_FILE = "last_backup.txt"

# Email temporarily disabled due to Railway SMTP block
# EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
# etc.

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

def get_last_backup_time():
    if os.path.exists(LAST_BACKUP_FILE):
        try:
            with open(LAST_BACKUP_FILE, 'r') as f:
                return datetime.fromisoformat(f.read().strip())
        except:
            pass
    return datetime.now() - timedelta(days=10)

def save_last_backup_time():
    with open(LAST_BACKUP_FILE, 'w') as f:
        f.write(datetime.now().isoformat())

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

    # === MANUAL JSON BACKUP (always works) ===
    if any(cmd in lower for cmd in ["backup", "export"]):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_data = {
            "backup_date": datetime.now().isoformat(),
            "total_subjects": len(subjects),
            "subjects": subjects
        }
        backup_json = json.dumps(backup_data, indent=2)
        send_message(f"✅ **TIA BACKUP v2.4**\nGenerated: {timestamp}\nTotal Subjects: {len(subjects)}\n\n```json\n{backup_json}\n```")
        save_last_backup_time()
        return jsonify({"status": "ok"})

    # ====================== CORE TIA COMMANDS ======================
    # ADD / NEW INCIDENT
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

    # LOCATION / 10-20
    if any(cmd in lower for cmd in ["10-20", "1020", "location", "property", "20"]):
        query = text.lower()
        for cmd in ["@tia", "10-20", "1020", "location", "property", "20", "at"]:
            query = query.replace(cmd, "").strip()
        matches = [s for s in subjects if query in s.get('history','').lower()]
        if matches:
            reply = f"🔴 **SUBJECTS AT {query.upper()}** ({len(matches)} found)\n\n" + "\n".join(f"• {s['name']} | {s.get('descriptors','No desc')}" for s in matches)
            send_message(reply)
        else:
            send_message(f"🔴 No subjects at '{query}'")
        return jsonify({"status": "ok"})

    # RISK
    if lower.startswith("@tia risk"):
        try:
            parts = text.split(maxsplit=3)
            name = parts[2]
            level = parts[3].capitalize()
            for s in subjects:
                if s['name'].lower() == name.lower():
                    s['risk'] = level
                    send_message(f"✅ Risk for {name} updated to {level}")
                    save_db(subjects)
                    return jsonify({"status": "ok"})
        except:
            send_message("Usage: @TIA risk [Name] [High/Medium/Low]")

    save_db(subjects)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
