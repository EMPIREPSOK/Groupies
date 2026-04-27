import os
import json
import uuid
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_ID = "0bd071f6a87fec9fcb76d39586"
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"
DB_FILE = "tia_subjects.json"
LAST_BACKUP_FILE = "last_backup.txt"

# Email settings from Railway Variables
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
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

def send_email_backup():
    subjects = load_db()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_data = {
        "backup_date": datetime.now().isoformat(),
        "total_subjects": len(subjects),
        "subjects": subjects
    }
    backup_json = json.dumps(backup_data, indent=2)

    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        return "❌ Email not configured in Railway Variables"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = EMAIL_RECIPIENT
    msg['Subject'] = f"TIA Auto Backup - {timestamp}"

    body = f"TIA Full Database Backup\nAuto-generated: {timestamp}\nTotal Subjects: {len(subjects)}\n\nAttached is the complete JSON backup."
    msg.attach(MIMEText(body, 'plain'))

    attachment = MIMEText(backup_json, 'plain')
    attachment.add_header('Content-Disposition', 'attachment', filename=f"tia_backup_{timestamp}.json")
    msg.attach(attachment)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(EMAIL_HOST_USER, EMAIL_RECIPIENT.split(','), msg.as_string())
        server.quit()
        save_last_backup_time()
        return f"✅ Auto backup emailed ({len(subjects)} subjects)"
    except Exception as e:
        return f"❌ Auto email failed: {str(e)}"

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

    # === AUTO BACKUP EVERY 3 DAYS ===
    last_backup = get_last_backup_time()
    if datetime.now() - last_backup > timedelta(days=3):
        auto_status = send_email_backup()
        send_message(f"🛡️ **TIA AUTO BACKUP**\n{auto_status}")

    # === MANUAL EMAIL BACKUP ===
    if "backup" in lower and "email" in lower:
        manual_status = send_email_backup()
        send_message(f"✅ **TIA MANUAL EMAIL BACKUP**\n{manual_status}")
        return jsonify({"status": "ok"})

    # === REGULAR JSON BACKUP ===
    if any(cmd in lower for cmd in ["backup", "export"]) and "email" not in lower:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_data = {"backup_date": datetime.now().isoformat(), "total_subjects": len(subjects), "subjects": subjects}
        backup_json = json.dumps(backup_data, indent=2)
        send_message(f"✅ **TIA BACKUP v2.3**\nGenerated: {timestamp}\nTotal Subjects: {len(subjects)}\n\n```json\n{backup_json}\n```")
        return jsonify({"status": "ok"})

    # ====================== CORE TIA COMMANDS ======================
    # ADD NEW SUBJECT / INCIDENT
    if any(k in lower for k in ["name:", "dob:", "date:", "location:", "outcome:"]):
        name = dob = descriptors = date = location = outcome = "Unknown"
        for line in text.splitlines():
            l = line.lower()
            if "name:" in l: name = line.split(":", 1)[1].strip()
            if "dob:" in l: dob = line.split(":", 1)[1].strip()
            if "descriptors:" in l or "descriptor:" in l: descriptors = line.split(":", 1)[1].strip()
            if "date:" in l: date = line.split(":", 1)[1].strip()
            if "location:" in l: location = line.split(":", 1)[1].strip()
            if "outcome:" in l: outcome = line.split(":", 1)[1].strip()

        existing = next((s for s in subjects if s.get('name', '').lower() == name.lower()), None)
        if existing:
            new_entry = f"{date} - {location} - {outcome}"
            if existing.get('history'):
                existing['history'] += f"\n• {new_entry}"
            else:
                existing['history'] = new_entry
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

    # LIST
    if "list" in lower:
        if not subjects:
            send_message("📋 **TIA Database**:\nEmpty")
        else:
            msg = "📋 **TIA Database**:\n"
            for s in subjects:
                msg += f"• {s['name']} | Risk: {s.get('risk','Medium')}\n"
            send_message(msg)
        return jsonify({"status": "ok"})

    # CHECK / LOOKS / NAME SEARCH
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
        for cmd in ["@tia", "10-20", "1020", "location", "property", "20"]:
            query = query.replace(cmd, "").strip()
        matches = [s for s in subjects if query in s.get('history','').lower()]
        if matches:
            reply = f"🔴 **SUBJECTS AT {query.upper()}** ({len(matches)} found)\n\n"
            for s in matches:
                reply += f"• {s['name']} | {s.get('descriptors','No desc')}\n"
            send_message(reply)
        else:
            send_message(f"🔴 No subjects at '{query}'")
        return jsonify({"status": "ok"})

    # RISK UPDATE
    if "risk" in lower:
        parts = text.split()
        try:
            name = parts[1]
            level = parts[2].capitalize()
            for s in subjects:
                if s['name'].lower() == name.lower():
                    s['risk'] = level
                    send_message(f"✅ Risk updated for {name} → {level}")
                    save_db(subjects)
                    return jsonify({"status": "ok"})
        except:
            pass
        send_message("❌ Risk command: @TIA risk [Name] [High/Medium/Low]")

    save_db(subjects)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
