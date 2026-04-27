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

# Email settings (Railway Variables)
EMAIL_HOST_USER = os.getenv("empirepsreport@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("xkex dgbn xseq pvui")
EMAIL_RECIPIENT = os.getenv("empirepsok@gmail.com")
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
    return datetime.now() - timedelta(days=10)  # Force first backup

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
        return "❌ Email not configured"

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

    # === REGULAR BACKUP (JSON in chat) ===
    if any(cmd in lower for cmd in ["backup", "export"]) and "email" not in lower:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_data = {"backup_date": datetime.now().isoformat(), "total_subjects": len(subjects), "subjects": subjects}
        backup_json = json.dumps(backup_data, indent=2)
        send_message(f"✅ **TIA BACKUP v2.3**\nGenerated: {timestamp}\nTotal Subjects: {len(subjects)}\n\n```json\n{backup_json}\n```")
        return jsonify({"status": "ok"})

    # === PASTE ALL YOUR PREVIOUS COMMANDS HERE (add, list, check, looks, 10-20, risk) ===

    save_db(subjects)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
