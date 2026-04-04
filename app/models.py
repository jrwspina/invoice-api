from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from app.enums import InvoiceStatus


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)

    firstname: Mapped[str]
    lastname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)

    password_hash: Mapped[str]

    clients: Mapped[list["Client"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Client(Base):
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(primary_key=True)

    firstname: Mapped[str]
    lastname: Mapped[Optional[str]]

    email: Mapped[str]
    phone: Mapped[Optional[str]]
    company: Mapped[Optional[str]]
    billing_address: Mapped[Optional[str]]

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="clients")

    invoices: Mapped[list["Invoice"]] = relationship(back_populates="client")


class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[int] = mapped_column(primary_key=True)

    status: Mapped[InvoiceStatus] = mapped_column(default=InvoiceStatus.DRAFT)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]]

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="invoices")

    client_id: Mapped[int] = mapped_column(ForeignKey("client.id"))
    client: Mapped["Client"] = relationship(back_populates="invoices")

    lineitems: Mapped[list["LineItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )


class LineItem(Base):
    __tablename__ = "invoice_line_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoice.id"))
    invoice: Mapped["Invoice"] = relationship(back_populates="lineitems")

    description: Mapped[str]
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2))


class Payment(Base):
    __tablename__ = "invoice_payment"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoice.id"))
    invoice: Mapped["Invoice"] = relationship(back_populates="payments")

    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2))
