"""Embedding service — Ollama local or Azure OpenAI production."""

import structlog
import httpx

from app.config import settings

logger = structlog.get_logger()


async def get_embedding(text: str) -> list[float]:
    """Get embedding vector for text using configured provider."""
    if settings.EMBEDDING_PROVIDER == "azure_openai":
        return await _embed_azure(text)
    return await _embed_ollama(text)


async def _embed_ollama(text: str) -> list[float]:
    """Get embedding from Ollama."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/embeddings",
            json={"model": settings.EMBED_MODEL, "prompt": text},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


async def _embed_azure(text: str) -> list[float]:
    """Get embedding from Azure OpenAI."""
    url = f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT}/embeddings?api-version=2024-02-01"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json={"input": text},
            headers={"api-key": settings.AZURE_OPENAI_API_KEY},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
