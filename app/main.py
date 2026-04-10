from fastapi import FastAPI
from app.routers import auth, users, clients, invoices, lineitems, payments

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(invoices.router)
app.include_router(lineitems.router)
app.include_router(payments.router)
