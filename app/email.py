from decimal import Decimal
from email.message import EmailMessage
from smtplib import SMTP

from app.models import Invoice
from app.settings import settings
from app.crud import (
    calculate_total as db_calculate_total,
    calculate_total_paid as db_calculate_total_paid,
)


def send_email(to_addr: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    with SMTP(settings.mail_server, settings.mail_port) as smtp:
        # smtp.starttls()
        if settings.email_user and settings.email_password:
            smtp.login(settings.email_user, settings.email_password)
        smtp.send_message(msg)


def build_invoice_email_body(
    invoice: Invoice,
    invoice_total: Decimal = Decimal(0),
) -> str:
    invoice_info = f"""
    Invoice #{invoice.id}
    Total: {invoice_total}
    Items:
    """
    items = []
    for li in invoice.lineitems:
        item = f"- {li.description} | Quantity: {li.quantity} | Unit Price: {li.unit_price} | Relative Total: {li.unit_price*li.quantity}"
        items.append(item)

    body = invoice_info
    for item in items:
        body += f"\n{item}"

    return body


def send_overdue_invoice_email(invoice: Invoice):
    invoice_total = db_calculate_total(invoice)
    invoice_total_paid = db_calculate_total_paid(invoice)

    subject = f"OVERDUE: Invoice #{invoice.id} from {invoice.user.firstname} {invoice.user.lastname}."

    body = f"Invoice #{invoice.id} has overdue payments (${invoice_total - invoice_total_paid} left to be paid.)"
    body += f"\n {build_invoice_email_body(invoice, invoice_total)}"

    send_email(invoice.client.email, subject, body)
