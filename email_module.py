import smtplib
import imaplib
import email
import mimetypes
import os
from email.header import decode_header, make_header
from email.message import EmailMessage
import config
from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER

PROJECT_DIR = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
BLOCKED_NAMES = ("config", "credentials", "token", ".env", "secret", "password")

# Optional: add ALLOWED_RECIPIENTS = ["friend@gmail.com", ...] to config.py to restrict who LEO can email
ALLOWED_RECIPIENTS = getattr(config, "ALLOWED_RECIPIENTS", None)


def _attachment_allowed(file_path):
    full = os.path.normcase(os.path.abspath(file_path))
    if full.startswith(PROJECT_DIR):
        return False
    name = os.path.basename(full)
    return not any(b in name for b in BLOCKED_NAMES)


def send_email(subject, body, file_path=None, recipient=None):
    to_address = recipient if recipient else EMAIL_RECEIVER

    if ALLOWED_RECIPIENTS and to_address != EMAIL_RECEIVER and to_address not in ALLOWED_RECIPIENTS:
        print(f"[ LEO: {to_address} is not on the allowed recipients list ]")
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_address
    msg.set_content(body)

    if file_path:
        if not os.path.exists(file_path):
            print("[ LEO: attachment file not found ]")
            return False
        if not _attachment_allowed(file_path):
            print("[ LEO: attachment blocked for security ]")
            return False
        ctype, _ = mimetypes.guess_type(file_path)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        with open(file_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype,
                               filename=os.path.basename(file_path))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"[ LEO: Email successfully sent to {to_address} ]")
        return True
    except Exception as e:
        print(f"[ LEO Email Error: {e} ]")
        return False


def _plain_text_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            disp = str(part.get("Content-Disposition"))
            if part.get_content_type() == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True) or b""
                return payload.decode(errors="ignore")
        return ""
    payload = msg.get_payload(decode=True) or b""
    return payload.decode(errors="ignore")


def check_emails(limit=3):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_SENDER, EMAIL_PASSWORD)
        mail.select("inbox", readonly=True)  # read-only: checking mail doesn't mark it as read

        status, messages = mail.search(None, "ALL")
        if status != "OK" or not messages[0]:
            mail.logout()
            return "No emails found in inbox."

        latest_ids = messages[0].split()[-limit:][::-1]

        results = []
        for e_id in latest_ids:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for part in msg_data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    subject = str(make_header(decode_header(msg.get("Subject", "No Subject"))))
                    sender = msg.get("From", "Unknown Sender")
                    body = " ".join(_plain_text_body(msg).split())[:300]
                    results.append(f"FROM: {sender}\nSUBJECT: {subject}\nBODY: {body}\n---")

        mail.logout()
        return "\n".join(results)

    except Exception as e:
        return f"Error checking emails: {e}"