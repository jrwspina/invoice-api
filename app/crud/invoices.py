from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence
from redis.asyncio import Redis
from sqlalchemy import or_, select
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


def update_reminder_sent_invoice(invoice: Invoice):
    invoice.reminder_sent_at = datetime.now(timezone.utc)


async def get_overdue_invoices(session: AsyncSession) -> Sequence[Invoice]:
    c1 = or_(
        Invoice.status == InvoiceStatus.PARTIALLY_PAID,
        Invoice.status == InvoiceStatus.SENT,
    )
    c2 = Invoice.due_date < datetime.now(timezone.utc)

    stmt = (
        select(Invoice)
        .options(
            selectinload(Invoice.lineitems),
            selectinload(Invoice.payments),
            selectinload(Invoice.client),
            selectinload(Invoice.user),
        )
        .where(c1, c2)
    )

    result = await session.execute(stmt)

    return result.scalars().all()


async def update_overdue_invoice(invoice: Invoice, session: AsyncSession):
    invoice.status = InvoiceStatus.OVERDUE


async def send_drafted_invoice(
    invoice: Invoice, session: AsyncSession, redis: Redis
) -> bool:
    invoice_id = invoice.id
    if invoice.status != InvoiceStatus.DRAFT:
        return False

    invoice.status = InvoiceStatus.SENT
    await session.commit()
    await redis.delete(f"invoice:{invoice_id}")
    return True


async def update_invoice_status(invoice_id: int, session: AsyncSession, redis: Redis):
    invoice = await get_invoice_nocache(invoice_id, session)
    assert invoice is not None

    total = calculate_total(invoice)

    stmt = select(Payment).where(Payment.invoice_id == invoice.id)
    payments = (await session.execute(stmt)).scalars().all()
    total_paid = sum(p.value for p in payments)

    await redis.delete(f"invoice:{invoice_id}")

    if total_paid == 0:
        if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID]:
            invoice.status = InvoiceStatus.SENT
        else:
            return
    elif total_paid < total:
        invoice.status = InvoiceStatus.PARTIALLY_PAID

    elif total_paid >= total:
        invoice.status = InvoiceStatus.PAID


async def get_invoices(
    user_id: int, session: AsyncSession, limit: int = 10, offset: int = 0
) -> Sequence[Invoice]:

    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.lineitems), selectinload(Invoice.payments))
        .where(Invoice.user_id == user_id)
        .order_by(Invoice.id)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_invoice(
    invoice_id: int, session: AsyncSession, redis: Redis
) -> InvoiceRead | None:
    cached = await redis.get(f"invoice:{invoice_id}")
    if cached:
        return InvoiceRead.model_validate_json(cached)
    stmt = (
        select(Invoice)
        .options(
            selectinload(Invoice.lineitems),
            selectinload(Invoice.payments),
            selectinload(Invoice.client),
            selectinload(Invoice.user),
        )
        .where(Invoice.id == invoice_id)
    )
    invoice = (await session.execute(stmt)).scalar_one_or_none()
    if invoice:
        invoice = to_invoice_read(invoice)
        await redis.set(
            f"invoice:{invoice_id}",
            invoice.model_dump_json(),
            ex=300,
        )
        return invoice
    return None


async def get_invoice_nocache(invoice_id: int, session: AsyncSession) -> Invoice | None:
    stmt = (
        select(Invoice)
        .options(
            selectinload(Invoice.lineitems),
            selectinload(Invoice.payments),
            selectinload(Invoice.client),
            selectinload(Invoice.user),
        )
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

    result = await get_invoice_nocache(db_invoice.id, session)
    assert result is not None
    return result


async def update_invoice(
    invoice: Invoice, new_data: InvoiceUpdate, session: AsyncSession, redis: Redis
) -> Invoice:
    invoice.issue_date = new_data.issue_date
    invoice.due_date = new_data.due_date
    invoice.notes = new_data.notes
    invoice.status = new_data.status
    invoice_id = invoice.id

    await session.commit()
    await session.refresh(invoice)
    await redis.delete(f"invoice:{invoice_id}")

    result = await get_invoice_nocache(invoice.id, session)
    assert result is not None
    return result


async def patch_invoice(
    invoice: Invoice, data: InvoicePatch, session: AsyncSession, redis: Redis
) -> Invoice:
    new_data = data.model_dump(exclude_unset=True)
    invoice_id = invoice.id

    for key, value in new_data.items():
        setattr(invoice, key, value)

    await session.commit()
    await session.refresh(invoice)
    await redis.delete(f"invoice:{invoice_id}")

    result = await get_invoice_nocache(invoice.id, session)
    assert result is not None
    return result


async def delete_invoice(invoice: Invoice, session: AsyncSession, redis: Redis):
    invoice_id = invoice.id
    await session.delete(invoice)
    await session.commit()
    await redis.delete(f"invoice:{invoice_id}")
