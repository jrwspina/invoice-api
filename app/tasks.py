import asyncio
from decimal import Decimal
from app.models import Invoice
from celery.signals import worker_process_init
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.celery import app
from app.crud.invoices import (
    calculate_total as db_calculate_total,
    get_invoice as db_get_invoice,
    get_overdue_invoices as db_get_overdue_invoices,
    update_overdue_invoice as db_update_overdue_invoice,
)
from app.email import send_email
from app.settings import settings

task_session_factory = None


@worker_process_init.connect
def init_worker(**kwargs):
    global task_session_factory
    engine = create_async_engine(settings.postgres_url, poolclass=NullPool)
    task_session_factory = async_sessionmaker(engine)


async def get_invoice_data(invoice_id: int):
    async with task_session_factory() as session:
        return await db_get_invoice(invoice_id, session)


async def update_overdue_invoices():
    async with task_session_factory() as session:

        invoices = await db_get_overdue_invoices(session)
        if invoices:
            for invoice in invoices:
                await db_update_overdue_invoice(invoice, session)

            await session.commit()


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


@app.task()
def send_invoice_email(invoice_id: int):

    invoice = asyncio.run(get_invoice_data(invoice_id))

    if invoice:
        invoice_total = db_calculate_total(invoice)
        subject = f"Invoice #{invoice.id} from {invoice.user.firstname} {invoice.user.lastname}"

        body = build_invoice_email_body(invoice, invoice_total)

        send_email(invoice.client.email, subject, body)


@app.task()
def check_overdue_invoices():
    asyncio.run(update_overdue_invoices())
