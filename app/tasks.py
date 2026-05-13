import asyncio

from celery.signals import worker_process_init
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.celery import app
from app.crud import (
    calculate_total as db_calculate_total,
    get_invoice as db_get_invoice,
    get_overdue_invoices as db_get_overdue_invoices,
    update_overdue_invoice as db_update_overdue_invoice,
    update_reminder_sent_invoice as db_update_reminder_sent_invoice,
)
from app.email import build_invoice_email_body, send_email, send_overdue_invoice_email
from app.settings import settings

task_session_factory = None


@worker_process_init.connect
def init_worker(**kwargs):
    global task_session_factory
    engine = create_async_engine(settings.postgres_url, poolclass=NullPool)
    task_session_factory = async_sessionmaker(engine)


async def _update_overdue_invoices(session: AsyncSession):
    invoices = await db_get_overdue_invoices(session)
    if invoices:
        for invoice in invoices:
            await db_update_overdue_invoice(invoice, session)
            if not invoice.reminder_sent_at:
                send_overdue_invoice_email(invoice)
                db_update_reminder_sent_invoice(invoice)
        await session.commit()


async def _send_invoice_email(invoice_id: int, session: AsyncSession):
    invoice = await db_get_invoice(invoice_id, session)

    if invoice:
        invoice_total = db_calculate_total(invoice)
        subject = f"Invoice #{invoice.id} from {invoice.user.firstname} {invoice.user.lastname}"

        body = build_invoice_email_body(invoice, invoice_total)

        send_email(invoice.client.email, subject, body)


@app.task()
def send_invoice_email(invoice_id: int):
    async def _run():
        async with task_session_factory() as session:
            await _send_invoice_email(invoice_id, session)

    asyncio.run(_run())


@app.task()
def check_overdue_invoices():
    async def _run():
        async with task_session_factory() as session:
            await _update_overdue_invoices(session)

    asyncio.run(_run())
