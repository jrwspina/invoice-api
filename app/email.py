from email.message import EmailMessage
from smtplib import SMTP

from app.settings import settings


def send_email(to_addr: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    with SMTP(settings.mail_server, settings.mail_port) as smtp:
        smtp.starttls()
        if settings.email_user and settings.email_password:
            smtp.login(settings.email_user, settings.email_password)
        smtp.send_message(msg)
