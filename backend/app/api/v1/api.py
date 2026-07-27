from fastapi import APIRouter
from app.api.v1.endpoints import health, customer, complaint, chat, upload

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(customer.router, prefix="/customer", tags=["customer"])
api_router.include_router(complaint.router, prefix="/complaints", tags=["complaints"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
