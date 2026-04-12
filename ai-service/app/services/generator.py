"""LLM generation service — Ollama local or Azure OpenAI production."""

import json
import time
from typing import AsyncGenerator

import structlog
import httpx

from app.config import settings

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are a helpful AI shopping assistant for AI Delivery Grocery Shop, a grocery delivery service with 9 store locations in the Lakeland, Florida area.

Your capabilities:
- Search and recommend products from our catalog of 3,000+ items across 6 categories
- Inform customers about current deals (BOGO, Weekly Deals, Daily Deals)
- Provide store locations, hours, and contact information
- Help build shopping lists and suggest meal ideas
- Answer questions about product availability and pricing

Rules:
1. Only recommend products that appear in the provided context.
2. Always mention current deals when they apply to recommended products.
3. Include prices in your recommendations.
4. If asked about something outside grocery shopping, politely redirect.
5. Format product recommendations clearly with name, price, and any active deals.
6. If you don't have information about a specific product, say so honestly.
7. Be friendly, concise, and helpful — like a knowledgeable grocery store associate.
8. When listing multiple products, use a numbered list for clarity."""


def build_context(products: list[dict], deals: list[dict], stores: list[dict]) -> str:
    """Build context string from retrieved results."""
    parts = []

    if products:
        parts.append("=== Available Products ===")
        for p in products[:8]:
            line = f"- {p['name']} | ${p['price']:.2f}/{p['unit']} | {p['category']}"
            if p.get("is_organic"):
                line += " | Organic"
            if p.get("brand"):
                line += f" | {p['brand']}"
            parts.append(line)

    if deals:
        parts.append("\n=== Current Deals ===")
        for d in deals[:5]:
            line = f"- {d['title']}: {d['product_name']} ({d['deal_type']})"
            if d.get("discount_percent"):
                line += f" — {d['discount_percent']}% off"
            parts.append(line)

    if stores:
        parts.append("\n=== Store Locations ===")
        for s in stores[:3]:
            parts.append(f"- {s['name']}: {s['address']}, {s['city']}, {s['state']} {s['zipCode']} | Phone: {s['phone']}")

    return "\n".join(parts) if parts else "No relevant products found in our catalog."


def build_messages(
    user_message: str,
    context: str,
    history: list[dict] | None = None,
) -> list[dict]:
    """Build the message array for LLM completion."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history (last 5 exchanges)
    if history:
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Add context + user message
    augmented = f"Based on the following product information:\n\n{context}\n\nCustomer question: {user_message}"
    messages.append({"role": "user", "content": augmented})

    return messages


async def generate(
    user_message: str,
    context: str,
    history: list[dict] | None = None,
) -> tuple[str, float, str]:
    """Generate a response. Returns (response_text, latency_ms, model_name)."""
    messages = build_messages(user_message, context, history)
    start = time.time()

    if settings.LLM_PROVIDER == "azure_openai":
        response, model = await _generate_azure(messages)
    else:
        response, model = await _generate_ollama(messages)

    latency = (time.time() - start) * 1000
    logger.info("llm_generation", model=model, latency_ms=round(latency, 1), input_tokens=len(str(messages)))

    return response, latency, model


async def generate_stream(
    user_message: str,
    context: str,
    history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream a response token by token."""
    messages = build_messages(user_message, context, history)

    if settings.LLM_PROVIDER == "azure_openai":
        async for chunk in _stream_azure(messages):
            yield chunk
    else:
        async for chunk in _stream_ollama(messages):
            yield chunk


async def _generate_ollama(messages: list[dict]) -> tuple[str, str]:
    """Generate via Ollama."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={"model": settings.LLM_MODEL, "messages": messages, "stream": False},
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"], settings.LLM_MODEL


async def _stream_ollama(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Stream via Ollama."""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={"model": settings.LLM_MODEL, "messages": messages, "stream": True},
            timeout=120.0,
        ) as resp:
            async for line in resp.aiter_lines():
                if line:
                    data = json.loads(line)
                    if content := data.get("message", {}).get("content", ""):
                        yield content


async def _generate_azure(messages: list[dict]) -> tuple[str, str]:
    """Generate via Azure OpenAI."""
    url = f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_CHAT_DEPLOYMENT}/chat/completions?api-version=2024-02-01"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json={"messages": messages, "max_tokens": 1000, "temperature": 0.7},
            headers={"api-key": settings.AZURE_OPENAI_API_KEY},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"], settings.AZURE_OPENAI_CHAT_DEPLOYMENT


async def _stream_azure(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Stream via Azure OpenAI."""
    url = f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_CHAT_DEPLOYMENT}/chat/completions?api-version=2024-02-01"
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            url,
            json={"messages": messages, "max_tokens": 1000, "temperature": 0.7, "stream": True},
            headers={"api-key": settings.AZURE_OPENAI_API_KEY},
            timeout=60.0,
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    data = json.loads(line[6:])
                    if choices := data.get("choices", []):
                        if content := choices[0].get("delta", {}).get("content", ""):
                            yield content
