from datetime import datetime
from decimal import Decimal
from app.enums import InvoiceStatus
from pydantic import BaseModel, ConfigDict


class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class BaseUser(Base):
    firstname: str
    lastname: str
    email: str


class BaseClient(Base):
    firstname: str
    lastname: str | None = None
    email: str
    phone: str | None = None
    company: str | None = None
    billing_address: str | None = None


class UserRead(BaseUser):
    id: int


class UserReadDetail(UserRead):
    clients: list["ClientRead"]
    invoices: list["InvoiceRead"]


class UserCreate(BaseUser):
    password: str


class UserUpdate(BaseUser):
    pass


class UserPatch(Base):
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None


class ClientRead(BaseClient):
    id: int
    user_id: int


class ClientCreate(BaseClient):
    pass


class ClientReadDetail(ClientRead):
    invoices: list["InvoiceRead"]


class ClientUpdate(BaseClient):
    pass


class ClientPatch(Base):
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    billing_address: str | None = None


class BaseInvoice(Base):
    issue_date: datetime
    due_date: datetime
    notes: str | None


class InvoiceRead(BaseInvoice):
    id: int
    user_id: int
    client_id: int
    status: InvoiceStatus
    total: Decimal = Decimal(0)


class InvoiceReadDetail(InvoiceRead):
    lineitems: list["LineItemRead"]
    payments: list["PaymentRead"]


class InvoiceCreate(BaseInvoice):
    client_id: int


class InvoiceUpdate(BaseInvoice):
    status: InvoiceStatus


class InvoicePatch(Base):
    status: InvoiceStatus | None = None
    issue_date: datetime | None = None
    due_date: datetime | None = None
    notes: str | None = None


class BaseLineItem(Base):
    description: str
    quantity: Decimal
    unit_price: Decimal


class LineItemCreate(BaseLineItem):
    pass


class LineItemRead(BaseLineItem):
    id: int
    invoice_id: int


class BasePayment(Base):
    paid_at: datetime
    value: Decimal


class PaymentCreate(BasePayment):
    pass


class PaymentRead(BasePayment):
    id: int
    invoice_id: int
