"""Pydantic models for chat request/response."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class ProductReference(BaseModel):
    sku: str
    name: str
    price: float
    category: str
    deal_type: str | None = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    products: list[ProductReference] = []
    latency_ms: float | None = None
    model: str | None = None


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    timestamp: str | None = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatHistoryItem] = []
