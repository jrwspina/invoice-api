from fastapi import FastAPI
from app.routers import users, clients

app = FastAPI()

app.include_router(users.router)
app.include_router(clients.router)
