"""Health check endpoint."""

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter
from qdrant_client import QdrantClient

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    checks = {}

    # Check Qdrant
    try:
        client = QdrantClient(url=settings.QDRANT_URL, timeout=3)
        collections = client.get_collections()
        checks["qdrant"] = "connected"
        checks["qdrant_collections"] = len(collections.collections)
    except Exception as e:
        checks["qdrant"] = f"error: {str(e)[:100]}"

    # Check Ollama
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3.0)
            models = [m["name"] for m in resp.json().get("models", [])]
            checks["ollama"] = "connected"
            checks["ollama_models"] = len(models)
    except Exception as e:
        checks["ollama"] = f"error: {str(e)[:100]}"

    healthy = all(v == "connected" for k, v in checks.items() if not k.endswith("_collections") and not k.endswith("_models"))

    return {
        "status": "healthy" if healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": {
            "embedding": settings.EMBEDDING_PROVIDER,
            "llm": settings.LLM_PROVIDER,
        },
        "checks": checks,
    }
