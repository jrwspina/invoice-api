from typing import Sequence
from app.schemas import PaymentCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Invoice, Payment


async def get_invoice_payments(
    invoice: Invoice,
    session: AsyncSession,
    limit: int = 10,
    offset: int = 0,
) -> Sequence[Payment]:
    stmt = (
        select(Payment)
        .where(Payment.invoice_id == invoice.id)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_payment(payment_id: int, session: AsyncSession) -> Payment | None:
    return await session.get(Payment, payment_id)


async def delete_payment(payment: Payment, session: AsyncSession):
    await session.delete(payment)


async def create_payment(
    invoice_id: int, payment: PaymentCreate, session: AsyncSession
) -> Payment:
    payment_db = Payment(**payment.model_dump())
    payment_db.invoice_id = invoice_id

    session.add(payment_db)

    return payment_db
