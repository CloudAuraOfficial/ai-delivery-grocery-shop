"""FastAPI AI Service for AIDeliveryGroceryShop chatbot."""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import chat, health, embeddings, metrics, staff_chat

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

app = FastAPI(
    title="AIDeliveryGroceryShop AI Service",
    description="RAG-powered chatbot for grocery product search, deals, and recommendations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router, prefix="/api")
app.include_router(embeddings.router, prefix="/api")
app.include_router(staff_chat.router, prefix="/api")
app.include_router(metrics.router)

# OpenTelemetry (after app creation)
from app.telemetry import setup_telemetry
setup_telemetry(app)
