from fastapi import APIRouter
from app.api.v1.endpoints import health, hcp, interaction, chat

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(hcp.router, prefix="/hcp", tags=["hcp"])
api_router.include_router(interaction.router, prefix="/interactions", tags=["interactions"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
