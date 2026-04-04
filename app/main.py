from fastapi import FastAPI
from app.routers import users, clients, invoices, lineitems

app = FastAPI()

app.include_router(users.router)
app.include_router(clients.router)
app.include_router(invoices.router)
app.include_router(lineitems.router)
