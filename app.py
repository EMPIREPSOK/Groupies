import os
import json
import uuid
from datetime import datetime
import resend
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_ID = "0bd071f6a87fec9fcb76d39586"
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"
DB_FILE = "tia_subjects.json"

resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "TIA <onboarding@resend.dev>")

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
    subjects = load_db()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_data = {
        "backup_date": datetime.now().isoformat(),
        "total_subjects": len(subjects),
        "subjects": subjects
    }
    backup_json = json.dumps(backup_data, indent=2)

    try:
        r = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": "empirepsok@gmail.com",
            "subject": f"TIA Backup - {timestamp}",
            "html": f"<h2>TIA Full Database Backup</h2><p>Generated: {timestamp}</p><p>Total Subjects: {len(subjects)}</p>",
            "attachments": [{
                "filename": f"tia_backup_{timestamp}.json",
                "content": backup_json
            }]
        })
        return f"✅ Backup emailed successfully"
    except Exception as e:
        return f"❌ Email failed: {str(e)}"

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

    # === BACKUP COMMAND ===
    if any(cmd in lower for cmd in ["backup", "export"]):
        status = send_email_backup()
        send_message(f"✅ **TIA BACKUP v2.6**\n{status}\nTotal Subjects: {len(subjects)}")
        return jsonify({"status": "ok"})

    # === ADD / INCIDENT ===
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

    # LIST, CHECK, LOOKS, 10-20, RISK (same as before)
    if "list" in lower:
        msg = "📋 **TIA Database**:\n" + ("\n".join(f"• {s['name']} | Risk: {s.get('risk','Medium')}" for s in subjects) or "Empty")
        send_message(msg)
        return jsonify({"status": "ok"})

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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
