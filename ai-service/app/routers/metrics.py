"""Prometheus metrics endpoint."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

# Custom metrics
CHAT_REQUESTS = Counter("grocery_chat_requests_total", "Total chat requests", ["intent"])
CHAT_LATENCY = Histogram("grocery_chat_latency_seconds", "Chat response latency", buckets=[0.5, 1, 2, 3, 5, 10, 30])
RETRIEVAL_RESULTS = Histogram("grocery_retrieval_results", "Number of retrieved documents", buckets=[0, 1, 3, 5, 10, 20])
EMBEDDING_REQUESTS = Counter("grocery_embedding_requests_total", "Total embedding requests", ["status"])


@router.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
