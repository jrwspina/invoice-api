from datetime import datetime
from decimal import Decimal
from app.enums import InvoiceStatus
from pydantic import BaseModel


class BaseUser(BaseModel):
    firstname: str
    lastname: str
    email: str


class BaseClient(BaseModel):
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


class UserPatch(BaseModel):
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


class ClientPatch(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    billing_address: str | None = None


class BaseInvoice(BaseModel):
    issue_date: datetime
    due_date: datetime
    notes: str | None


class InvoiceRead(BaseInvoice):
    id: int
    user_id: int
    client_id: int
    status: InvoiceStatus


class InvoiceReadDetail(InvoiceRead):
    lineitems: list["LineItemRead"]
    payments: list["PaymentRead"]


class InvoiceCreate(BaseInvoice):
    client_id: int


class InvoiceUpdate(BaseInvoice):
    status: InvoiceStatus


class InvoicePatch(BaseModel):
    status: InvoiceStatus | None = None
    issue_date: datetime | None = None
    due_date: datetime | None = None
    notes: str | None = None


class BaseLineItem(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal


class LineItemCreate(BaseLineItem):
    pass


class LineItemRead(BaseLineItem):
    id: int
    invoice_id: int


class BasePayment(BaseModel):
    paid_at: datetime
    value: Decimal


class PaymentCreate(BasePayment):
    pass


class PaymentRead(BasePayment):
    id: int
    invoice_id: int
