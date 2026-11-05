from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.chat import router as chat_router
from app.api.admin import router as admin_router
from app.schemas.chat_schema import HealthResponse
from app.api.v1.routes.conversations import router as conversations_router
from app.core.logging_config import configure_logging
from app.api.v1.liquipedia import router as liquipedia_router

from app.middleware.request_logging import (
    request_logging_middleware,
)

from app.services.knowledge_refresh import (
    start_knowledge_scheduler,
    stop_knowledge_scheduler,
)

from app.api.v1.knowledge import router as knowledge_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start automatic knowledge refresh scheduler
    start_knowledge_scheduler()

    yield

    # Stop scheduler during application shutdown
    stop_knowledge_scheduler()


app = FastAPI(
    title=settings.app_name,
    description="AI assistant for Garena Free Fire esports.",
    version="1.0.0",
    lifespan=lifespan,
)
# Liquipedia API
app.include_router(
    liquipedia_router,
    prefix="/api/v1",
)
configure_logging()

app.middleware("http")(
    request_logging_middleware
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Chat API
app.include_router(
    chat_router,
    prefix=settings.api_prefix,
    tags=["Ask Sphere"],
)


# Admin API
app.include_router(
    admin_router,
    prefix=settings.api_prefix,
)


# Conversation API
app.include_router(
    conversations_router,
    prefix="/api/v1",
)


# Knowledge Base API
app.include_router(
    knowledge_router,
    prefix="/api/v1",
)


@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version="1.0.0",
    )


@app.get("/health")
async def health():
    return {"status": "healthy"}
