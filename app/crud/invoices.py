from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Invoice
from app.schemas import InvoiceCreate, InvoicePatch, InvoiceUpdate


async def get_invoices(session: AsyncSession) -> Sequence[Invoice]:
    result = await session.execute(select(Invoice))
    return result.scalars().all()


async def get_invoice(invoice_id: int, session: AsyncSession) -> Invoice | None:
    return await session.get(Invoice, invoice_id)


async def create_invoice(invoice: InvoiceCreate, session: AsyncSession) -> Invoice:
    db_invoice = Invoice(**invoice.model_dump())

    session.add(db_invoice)
    await session.commit()
    await session.refresh(db_invoice)
    return db_invoice


async def update_invoice(
    invoice: Invoice, new_data: InvoiceUpdate, session: AsyncSession
) -> Invoice:
    invoice.issue_date = new_data.issue_date
    invoice.due_date = new_data.due_date
    invoice.notes = new_data.notes
    invoice.status = new_data.status

    await session.commit()
    await session.refresh(invoice)
    return invoice


async def patch_invoice(
    invoice: Invoice, data: InvoicePatch, session: AsyncSession
) -> Invoice:
    new_data = data.model_dump(exclude_unset=True)

    for key, value in new_data.items():
        setattr(invoice, key, value)

    await session.commit()
    await session.refresh(invoice)
    return invoice


async def delete_invoice(invoice: Invoice, session: AsyncSession):
    await session.delete(invoice)
    await session.commit()
