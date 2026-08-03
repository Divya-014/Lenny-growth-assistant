from fastapi import APIRouter
from app.api.endpoints import health, chat, sessions

api_router = APIRouter()

# Include health, chat, and sessions routers under root prefix
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(sessions.router)
