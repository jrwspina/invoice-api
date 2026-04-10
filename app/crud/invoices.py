from decimal import Decimal
from typing import Sequence
from app.crud import payments
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import InvoiceStatus
from app.models import Invoice, Payment
from app.schemas import InvoiceCreate, InvoicePatch, InvoiceRead, InvoiceUpdate


def calculate_total(invoice: Invoice) -> Decimal:
    return sum(
        item.unit_price * item.quantity for item in invoice.lineitems
    ) or Decimal(0)


def calculate_total_paid(invoice: Invoice) -> Decimal:
    return sum(payment.value for payment in invoice.payments) or Decimal(0)


def to_invoice_read(invoice: Invoice) -> InvoiceRead:
    return InvoiceRead.model_validate(invoice).model_copy(
        update={
            "total": calculate_total(invoice),
            "total_paid": calculate_total_paid(invoice),
        }
    )


async def send_drafted_invoice(invoice: Invoice, session: AsyncSession) -> bool:
    if invoice.status != InvoiceStatus.DRAFT:
        return False

    invoice.status = InvoiceStatus.SENT
    await session.commit()
    return True


async def update_invoice_status(invoice_id: int, session: AsyncSession):
    invoice = await get_invoice(invoice_id, session)
    assert invoice is not None

    total = calculate_total(invoice)

    stmt = select(Payment).where(Payment.invoice_id == invoice.id)
    payments = (await session.execute(stmt)).scalars().all()
    total_paid = sum(p.value for p in payments)

    if total_paid == 0:
        if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID]:
            invoice.status = InvoiceStatus.SENT
        else:
            return
    elif total_paid < total:
        invoice.status = InvoiceStatus.PARTIALLY_PAID

    elif total_paid >= total:
        invoice.status = InvoiceStatus.PAID


async def get_invoices(user_id: int, session: AsyncSession) -> Sequence[Invoice]:

    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.lineitems), selectinload(Invoice.payments))
        .where(Invoice.user_id == user_id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_invoice(invoice_id: int, session: AsyncSession) -> Invoice | None:
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.lineitems), selectinload(Invoice.payments))
        .where(Invoice.id == invoice_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_invoice(
    invoice: InvoiceCreate, user_id: int, session: AsyncSession
) -> Invoice:
    db_invoice = Invoice(**invoice.model_dump())
    db_invoice.user_id = user_id

    session.add(db_invoice)
    await session.commit()
    await session.refresh(db_invoice)

    result = await get_invoice(db_invoice.id, session)
    assert result is not None
    return result


async def update_invoice(
    invoice: Invoice, new_data: InvoiceUpdate, session: AsyncSession
) -> Invoice:
    invoice.issue_date = new_data.issue_date
    invoice.due_date = new_data.due_date
    invoice.notes = new_data.notes
    invoice.status = new_data.status

    await session.commit()
    await session.refresh(invoice)

    result = await get_invoice(invoice.id, session)
    assert result is not None
    return result


async def patch_invoice(
    invoice: Invoice, data: InvoicePatch, session: AsyncSession
) -> Invoice:
    new_data = data.model_dump(exclude_unset=True)

    for key, value in new_data.items():
        setattr(invoice, key, value)

    await session.commit()
    await session.refresh(invoice)

    result = await get_invoice(invoice.id, session)
    assert result is not None
    return result


async def delete_invoice(invoice: Invoice, session: AsyncSession):
    await session.delete(invoice)
    await session.commit()
