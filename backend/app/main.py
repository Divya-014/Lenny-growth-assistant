from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown lifecycle events.
    """
    logger.info("=========================================")
    logger.info(f"Starting {settings.APP_NAME} in environment: {settings.APP_ENV}")
    logger.info(f"Port: {settings.PORT} | Host: {settings.HOST}")
    logger.info("=========================================")
    yield
    logger.info("=========================================")
    logger.info(f"Shutting down {settings.APP_NAME}")
    logger.info("=========================================")

# Initialize FastAPI App with lifespan manager
app = FastAPI(
    title=settings.APP_NAME,
    description="Asynchronous backend orchestrating RAG queries and agents for Lenny Growth Assistant.",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan
)

# CORS Policy Config (React dev server integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to exact domains in production envs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(api_router)

