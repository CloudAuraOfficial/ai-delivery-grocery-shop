"""Prometheus metrics endpoint."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

# Existing
CHAT_REQUESTS = Counter("grocery_chat_requests_total", "Total chat requests", ["intent"])
CHAT_LATENCY = Histogram("grocery_chat_latency_seconds", "Chat response latency", buckets=[0.5, 1, 2, 3, 5, 10, 30])
RETRIEVAL_RESULTS = Histogram("grocery_retrieval_results", "Number of retrieved documents", buckets=[0, 1, 3, 5, 10, 20])
EMBEDDING_REQUESTS = Counter("grocery_embedding_requests_total", "Total embedding requests", ["status"])

# LLM-specific cost + performance telemetry
LLM_TOKENS = Counter(
    "grocery_llm_tokens_total",
    "Tokens consumed by the LLM",
    ["model", "kind"],  # kind = prompt | completion | total
)
LLM_LATENCY = Histogram(
    "grocery_llm_latency_seconds",
    "LLM generation latency (excludes retrieval)",
    ["model", "outcome"],  # outcome = ok | fallback
    buckets=[0.25, 0.5, 1, 2, 4, 8, 16],
)
RAG_RETRIEVAL_LATENCY = Histogram(
    "grocery_rag_retrieval_latency_seconds",
    "Retrieval latency split by lane",
    ["lane"],  # lane = vector | keyword | fused
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2],
)
SESSION_CACHE = Counter(
    "grocery_session_cache_total",
    "Redis chat-session cache outcome",
    ["outcome"],  # hit | miss
)
INPUT_GUARD_BLOCKS = Counter(
    "grocery_input_guard_blocks_total",
    "Chat inputs blocked by the prompt-injection guard",
    ["reason"],
)


@router.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
