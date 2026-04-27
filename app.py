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

    # === ADD NEW INCIDENT (supports multiple history) ===
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

        # Find existing subject or create new
        existing = next((s for s in subjects if s['name'].lower() == name.lower()), None)
        if existing:
            new_entry = f"{date} - {location} - {outcome}"
            existing['history'] = f"{existing.get('history','')}\n• {new_entry}" if existing.get('history') else new_entry
            existing['last_seen'] = date
            if image_url:
                existing['photo_url'] = image_url
            send_message(f"✅ **NEW INCIDENT ADDED** for {name}\nLocation: {location}")
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
            send_message(f"✅ **NEW SUBJECT ADDED**\nName: {name}\nLocation: {location}")

        save_db(subjects)
        return jsonify({"status": "ok"})

    # === LIST ===
    if any(w in lower for w in ["list", "all", "show", "database"]):
        if subjects:
            msg = f"📋 **TIA Database** ({len(subjects)} total):\n\n"
            for s in subjects:
                msg += f"• {s['name']} | Risk: {s.get('risk','Medium')}\n"
        else:
            msg = "Database empty."
        send_message(msg)
        return jsonify({"status": "ok"})

    # === RISK LEVEL ===
    if "risk " in lower:
        parts = text.split()
        if len(parts) >= 3:
            risk_level = parts[-1].capitalize()
            name_query = " ".join(parts[2:-1]).lower()
            for s in subjects:
                if name_query in s['name'].lower():
                    s['risk'] = risk_level
                    save_db(subjects)
                    send_message(f"✅ Risk for **{s['name']}** updated to **{risk_level}**")
                    return jsonify({"status": "ok"})
            send_message("🔴 Subject not found.")
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
Risk: {s.get('risk','Medium')}

History:
{s.get('history','No history')}
"""
                    send_message(reply, s.get('photo_url'))
            else:
                send_message(f"🔴 **TIA** — No match for '**{query}**'")
        return jsonify({"status": "ok"})

    # === LOCATION SEARCH ===
    if any(cmd in lower for cmd in ["10-20", "1020", "location", "property"]) or ("20" in lower and len(text.split()) <= 6):
        query = text.lower()
        for cmd in ["@tia", "10-20", "1020", "location", "property", " at ", "check"]:
            query = query.replace(cmd, "").strip()
        if query:
            matches = [s for s in subjects if query in s.get('history','').lower()]
            if matches:
                reply = f"🔴 **SUBJECTS AT {query.upper()}** ({len(matches
