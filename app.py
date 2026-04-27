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
    c.execute('''INSERT INTO subjects 
                 (id, name, dob, descriptors, history, last_seen, notes, risk, photo_url)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (subject_id, name, dob, descriptors, history, date, "Auto-logged by TIA", "Medium", photo_url))
    conn.commit()
    conn.close()

def find_subject(query):
    conn = sqlite3.connect('tia_subjects.db')
    c = conn.cursor()
    # Search name + descriptors
    c.execute("""SELECT * FROM subjects 
                 WHERE name LIKE ? OR descriptors LIKE ?""", 
              (f"%{query}%", f"%{query}%"))
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

    # === LOOKUP COMMAND ===
    if any(cmd in lower for cmd in ["check", "who", "lookup", "match"]):
        query = text.replace("check", "").replace("who", "").replace("lookup", "").replace("match", "").strip()
        if not query:
            send_message("🔴 **TIA** — What name or descriptor do you want to check?")
            return jsonify({"status": "ok"})

        subjects = find_subject(query)
        if subjects:
            for subject in subjects:
                reply = f"""🔴 **TIA MATCH FOUND**

Name: {subject[1]}
DOB: {subject[2]}
Descriptors: {subject[3] or 'None'}

History:
• {subject[4]}

Last Seen: {subject[5]}
Notes: {subject[6]}
Risk Level: {subject[7]}"""
                send_message(reply, subject[8])  # Send photo
        else:
            send_message("🔴 **TIA** — No match found for that name or descriptor.")

    # === ADD NEW SUBJECT ===
    elif any(k in lower for k in ["name:", "dob:", "date:", "location:", "outcome:"]) or ("add" in lower and image_url):
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
        
        send_message(f"""✅ **NEW SUBJECT ADDED TO TIA DATABASE**

Name: {name}
DOB: {dob}
Descriptors: {descriptors or 'None'}
Date: {date}
Location: {location}
Outcome: {outcome}

📸 Photo saved. TIA will now recognize this subject + descriptors.""")

    # Silent mode - no reply for random messages
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
