from flask import Flask, request, jsonify
import requests
import sqlite3
import os
import uuid

app = Flask(__name__)

BOT_ID = "0bd071f6a87fec9fcb76d39586"
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"

def init_db():
    conn = sqlite3.connect('tia_subjects.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS subjects")
    c.execute('''CREATE TABLE subjects (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    dob TEXT,
                    descriptors TEXT,
                    history TEXT,
                    last_seen TEXT,
                    notes TEXT,
                    risk TEXT,
                    photo_url TEXT)''')
    conn.commit()
    conn.close()

init_db()

def send_message(text, image_url=None):
    payload = {"bot_id": BOT_ID, "text": text}
    if image_url:
        payload["attachments"] = [{"type": "image", "url": image_url}]
    requests.post(GROUPME_POST_URL, json=payload)

def save_subject(name, dob, descriptors, date, location, outcome, photo_url=None):
    subject_id = str(uuid.uuid4())[:8]
    history = f"{date} - {location} - {outcome}"
    conn = sqlite3.connect('tia_subjects.db')
    c = conn.cursor()
    c.execute('''INSERT INTO subjects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (subject_id, name.strip(), dob, descriptors or "", history, date, "Auto-logged by TIA", "Medium", photo_url))
    conn.commit()
    conn.close()

def find_by_location(loc):
    conn = sqlite3.connect('tia_subjects.db')
    c = conn.cursor()
    q = f"%{loc}%"
    c.execute("SELECT * FROM subjects WHERE history LIKE ?", (q,))
    rows = c.fetchall()
    conn.close()
    return rows

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get('sender_type') == 'bot':
        return jsonify({"status": "ok"})

    text = data.get('text', '').strip()
    attachments = data.get('attachments', [])
    image_url = attachments[0].get('url') if attachments else None
    lower = text.lower()

    # LOCATION SEARCH
    if any(cmd in lower for cmd in ["location", "property", "at ", "check"]):
        query = text.lower()
        for cmd in ["@tia", "location", "property", "check", "at"]:
            query = query.replace(cmd, "").strip()
        
        if query:
            subjects = find_by_location(query)
            if subjects:
                reply = f"🔴 **TIA — SUBJECTS AT {query.upper()}**\n\n"
                for s in subjects:
                    reply += f"• {s[1]} ({s[3] or 'No desc'})\n"
                send_message(reply)
            else:
                send_message(f"🔴 **TIA** — No subjects found at '**{query}**'.")
            return jsonify({"status": "ok"})

    # NAME / DESCRIPTOR CHECK
    if any(cmd in lower for cmd in ["check", "who", "lookup", "match"]):
        query = text.lower()
        for cmd in ["@tia", "check", "who", "lookup", "match"]:
            query = query.replace(cmd, "")
        query = query.strip()

        if query:
            # (reuse same find_subject logic from before)
            conn = sqlite3.connect('tia_subjects.db')
            c = conn.cursor()
            q = f"%{query}%"
            c.execute("SELECT * FROM subjects WHERE name LIKE ? OR descriptors LIKE ?", (q, q))
            subjects = c.fetchall()
            conn.close()

            if subjects:
                for s in subjects:
                    reply = f"""🔴 **TIA MATCH FOUND**

Name: {s[1]}
DOB: {s[2]}
Descriptors: {s[3] or 'None'}

History:
• {s[4]}

Last Seen: {s[5]}
Risk: {s[7]}"""
                    send_message(reply, s[8])
            else:
                send_message(f"🔴 **TIA** — No match for '**{query}**'")

    # ADD SUBJECT
    elif any(k in lower for k in ["name:", "dob:", "date:", "location:", "outcome:"]):
        name = dob = descriptors = date = location = outcome = "Unknown"
        for line in text.splitlines():
            l = line.lower()
            if "name:" in l: name = line.split(":",1)[1].strip()
            if "dob:" in l: dob = line.split(":",1)[1].strip()
            if "descriptors:" in l or "descriptor:" in l: descriptors = line.split(":",1)[1].strip()
            if "date:" in l: date = line.split(":",1)[1].strip()
            if "location:" in l: location = line.split(":",1)[1].strip()
            if "outcome:" in l: outcome = line.split(":",1)[1].strip()

        save_subject(name, dob, descriptors, date, location, outcome, image_url)
        send_message(f"✅ **NEW SUBJECT ADDED**\nName: {name}")

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
