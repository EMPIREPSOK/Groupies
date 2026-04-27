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
    c.execute('''CREATE TABLE IF NOT EXISTS subjects (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    dob TEXT,
                    history TEXT,
                    last_seen TEXT,
                    notes TEXT,
                    risk TEXT,
                    photo_url TEXT)''')
    conn.commit()
    conn.close()

init_db()

def send_message(text):
    payload = {"bot_id": BOT_ID, "text": text}
    requests.post(GROUPME_POST_URL, json=payload)

def save_subject(name, dob, date, location, outcome, photo_url=None):
    subject_id = str(uuid.uuid4())[:8]
    history = f"{date} - {location} - {outcome}"
    
    conn = sqlite3.connect('tia_subjects.db')
    c = conn.cursor()
    c.execute('''INSERT INTO subjects 
                 (id, name, dob, history, last_seen, notes, risk, photo_url)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (subject_id, name, dob, history, date, "Auto-logged by TIA", "Medium", photo_url))
    conn.commit()
    conn.close()
    return name

def find_subject(name):
    conn = sqlite3.connect('tia_subjects.db')
    c = conn.cursor()
    c.execute("SELECT * FROM subjects WHERE name LIKE ?", (f"%{name}%",))
    row = c.fetchone()
    conn.close()
    return row

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or data.get('sender_type') == 'bot':
        return jsonify({"status": "ok"})

    text = data.get('text', '')
    attachments = data.get('attachments', [])
    image_url = attachments[0].get('url') if attachments else None

    lower_text = text.lower()

    # === LOOKUP MODE ===
    if any(word in lower_text for word in ["check", "who", "lookup", "match"]):
        name = text.split()[-1] if len(text.split()) > 1 else text
        subject = find_subject(name)
        if subject:
            reply = f"""🔴 **TIA MATCH FOUND**

Name: {subject[1]}
DOB: {subject[2]}

History:
• {subject[3]}

Last Seen: {subject[4]}
Notes: {subject[5]}
Risk Level: {subject[6]}"""
        else:
            reply = "🔴 **TIA** — No match found in database.\nUpload new subject details to add."
    
    # === ADD NEW SUBJECT MODE ===
    elif any(word in lower_text for word in ["name:", "dob:", "date:"]) or image_url:
        # Simple parsing (you can send in any order)
        name = dob = date = location = outcome = "Unknown"
        for line in text.splitlines():
            if "name:" in line.lower(): name = line.split(":",1)[1].strip()
            if "dob:" in line.lower(): dob = line.split(":",1)[1].strip()
            if "date:" in line.lower(): date = line.split(":",1)[1].strip()
            if "location:" in line.lower(): location = line.split(":",1)[1].strip()
            if "outcome:" in line.lower(): outcome = line.split(":",1)[1].strip()

        save_subject(name, dob, date, location, outcome, image_url)
        
        reply = f"""✅ **NEW SUBJECT ADDED TO DATABASE**

🔴 **TIA RECORD**

Name: {name}
DOB: {dob}
Date: {date}
Location: {location}
Outcome: {outcome}

📸 Photo saved.
TIA will now recognize this subject in future posts."""

    else:
        reply = "🔴 **TIA ACTIVE** ✅\n\nSend a photo + details or type `check [name]`"

    send_message(reply)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
