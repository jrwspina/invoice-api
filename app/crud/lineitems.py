from typing import Sequence
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Invoice, LineItem
from app.schemas import LineItemCreate


async def get_lineitems(
    invoice: Invoice, session: AsyncSession, limit: int = 10, offset: int = 0
) -> Sequence[LineItem]:
    stmt = (
        select(LineItem)
        .where(LineItem.invoice_id == invoice.id)
        .order_by(LineItem.id)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_lineitem(lineitem_id: int, session: AsyncSession) -> LineItem | None:
    return await session.get(LineItem, lineitem_id)


async def create_lineitem(
    invoice: Invoice, lineitem: LineItemCreate, session: AsyncSession, redis: Redis
) -> LineItem:
    invoice_id = invoice.id
    db_lineitem = LineItem(**lineitem.model_dump())
    db_lineitem.invoice_id = invoice.id
    session.add(db_lineitem)
    await session.commit()
    await session.refresh(db_lineitem)
    await redis.delete(f"invoice:{invoice_id}")
    return db_lineitem


async def delete_lineitem(lineitem: LineItem, session: AsyncSession, redis: Redis):
    invoice_id = lineitem.invoice_id
    await session.delete(lineitem)
    await session.commit()
    await redis.delete(f"invoice:{invoice_id}")
