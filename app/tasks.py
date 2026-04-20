import asyncio
from app.crud.invoices import calculate_total, get_invoice

from app.celery import app
from app.database import async_session
from app.email import send_email


async def fetch_invoice_data(invoice_id: int):
    async with async_session() as session:
        return await get_invoice(invoice_id, session)


@app.task()
def send_invoice_email(invoice_id: int):

    invoice = asyncio.run(fetch_invoice_data(invoice_id))

    if invoice:
        invoice_total = calculate_total(invoice)
        subject = f"Invoice #{invoice.id} from {invoice.user.firstname} {invoice.user.lastname}"

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

        send_email(invoice.client.email, subject, body)
