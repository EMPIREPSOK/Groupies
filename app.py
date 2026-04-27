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

def send_message(text, image_url=None):
    payload = {"bot_id": BOT_ID, "text": text}
    if image_url:
        payload["attachments"] = [{"type": "image", "url": image_url}]
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

    # === LOOKUP ===
    if any(word in lower_text for word in ["check", "who", "lookup", "match"]):
        search_name = text.replace("check", "").replace("who", "").replace("lookup", "").replace("match", "").strip()
        subject = find_subject(search_name)
        if subject and subject[7]:  # photo_url exists
            reply = f"""🔴 **TIA MATCH FOUND**

Name: {subject[1]}
DOB: {subject[2]}

History:
• {subject[3]}

Last Seen: {subject[4]}
Notes: {subject[5]}
Risk Level: {subject[6]}"""
            send_message(reply, subject[7])  # Send original photo
            return jsonify({"status": "ok"})
        elif subject:
            send_message(f"""🔴 **TIA MATCH FOUND**

Name: {subject[1]}
DOB: {subject[2]}

History:
• {subject[3]}

Last Seen: {subject[4]}
Notes: {subject[5]}
Risk Level: {subject[6]}""")
        else:
            send_message("🔴 **TIA** — No match found.\nUpload new subject details to add.")

    # === ADD NEW SUBJECT ===
    elif any(word in lower_text for word in ["name:", "dob:", "date:"]) or image_url:
        name = dob = date = location = outcome = "Unknown"
        for line in text.splitlines():
            l = line.lower()
            if "name:" in l: name = line.split(":",1)[1].strip()
            if "dob:" in l: dob = line.split(":",1)[1].strip()
            if "date:" in l: date = line.split(":",1)[1].strip()
            if "location:" in l: location = line.split(":",1)[1].strip()
            if "outcome:" in l: outcome = line.split(":",1)[1].strip()

        save_subject(name, dob, date, location, outcome, image_url)
        
        reply = f"""✅ **NEW SUBJECT ADDED**

🔴 **TIA RECORD**
Name: {name}
DOB: {dob}
Date: {date}
Location: {location}
Outcome: {outcome}

📸 Original photo saved.
TIA will now show this photo on future lookups."""

        send_message(reply)
    
    else:
        send_message("🔴 **TIA ACTIVE** ✅\n\nPost photo + details or type `@TIA check [Name]`")

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
