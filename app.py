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

    # === ADD SUBJECT ===
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

        new_subject = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "dob": dob,
            "descriptors": descriptors,
            "history": f"{date} - {location} - {outcome}",
            "last_seen": date,
            "photo_url": image_url
        }
        subjects.append(new_subject)
        save_db(subjects)

        send_message(f"✅ **SUBJECT SAVED**\nName: {name}\nLocation: {location}\nTotal in DB: {len(subjects)}")
        return jsonify({"status": "ok"})

    # === LIST ALL ===
    if any(w in lower for w in ["list", "all", "show", "database"]):
        if subjects:
            msg = f"📋 **TIA Database** ({len(subjects)} subjects):\n"
            for s in subjects:
                msg += f"• {s['name']} | {s.get('descriptors','None')}\n"
        else:
            msg = "Database empty."
        send_message(msg)
        return jsonify({"status": "ok"})

    # === LOCATION / 10-20 SEARCH ===
    if any(cmd in lower for cmd in ["10-20", "1020", "location", "property", " at "]) or ("20" in lower and len(text.split()) <= 6):
        query = text.lower()
        for cmd in ["@tia", "10-20", "1020", "location", "property", " at ", "check"]:
            query = query.replace(cmd, "").strip()
        if query:
            matches = [s for s in subjects if query in s.get('history','').lower() or query in s.get('last_seen','').lower()]
            if matches:
                reply = f"🔴 **SUBJECTS AT {query.upper()}** ({len(matches)} found)\n\n"
                for s in matches:
                    reply += f"• {s['name']} | {s.get('descriptors','No desc')}\n"
                send_message(reply)
            else:
                send_message(f"🔴 **TIA** — No subjects at '**{query}**'.")
            return jsonify({"status": "ok"})

    # === NAME / LOOKS CHECK ===
    if any(cmd in lower for cmd in ["check ", "looks ", "who ", "match "]):
        query = text.lower()
        for cmd in ["@tia", "check", "looks", "who", "match"]:
            query = query.replace(cmd, "").strip()
        if query:
            matches = [s for s in subjects if query in s['name'].lower() or query in s.get('descriptors','').lower()]
            if matches:
                for s in matches:
                    reply = f"""🔴 **TIA MATCH FOUND**

Name: {s['name']}
DOB: {s.get('dob','Unknown')}
Descriptors: {s.get('descriptors','None')}

History:
• {s.get('history','')}

Last Seen: {s.get('last_seen','')}
Risk: Medium"""
                    send_message(reply, s.get('photo_url'))
            else:
                send_message(f"🔴 **TIA** — No match for '**{query}**'")
        return jsonify({"status": "ok"})

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
