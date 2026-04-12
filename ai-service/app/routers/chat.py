"""Chat endpoints with full RAG pipeline."""

import structlog
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse, ProductReference, ChatHistoryResponse, ChatHistoryItem
from app.services import retriever, generator, chat_service

logger = structlog.get_logger()

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """Send a message and get an AI response with product recommendations."""
    # Get or create session
    session_id = await chat_service.get_or_create_session(request.session_id)

    # Get conversation history
    history = await chat_service.get_history(session_id)

    # Classify intent and retrieve context
    intent = retriever.classify_intent(request.message)
    logger.info("chat_request", intent=intent, session=session_id[:8])

    products = []
    deals = []
    stores = []

    if intent == "store_info":
        stores = await retriever.retrieve_stores(request.message, top_k=5)
        products = await retriever.retrieve_products(request.message, top_k=3)
    elif intent == "deal_inquiry":
        deals = await retriever.retrieve_deals(request.message, top_k=8)
        products = await retriever.retrieve_products(request.message, top_k=5)
    else:
        products = await retriever.retrieve_products(request.message, top_k=10)
        deals = await retriever.retrieve_deals(request.message, top_k=3)

    # Build context and generate response
    context = generator.build_context(products, deals, stores)
    response_text, latency_ms, model = await generator.generate(
        request.message, context, history
    )

    # Save to session history
    await chat_service.append_message(session_id, "user", request.message)
    await chat_service.append_message(session_id, "assistant", response_text)

    # Persist to PostgreSQL (fire-and-forget)
    product_skus = [p["sku"] for p in products[:5]]
    chat_service.persist_message(session_id, "user", request.message)
    chat_service.persist_message(session_id, "assistant", response_text, product_skus, latency_ms, model)

    # Build product references
    product_refs = [
        ProductReference(
            sku=p["sku"],
            name=p["name"],
            price=p["price"],
            category=p["category"],
            deal_type=next((d["deal_type"] for d in deals if d.get("product_sku") == p["sku"]), None),
        )
        for p in products[:5]
    ]

    return ChatResponse(
        message=response_text,
        session_id=session_id,
        products=product_refs,
        latency_ms=round(latency_ms, 1),
        model=model,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream a chat response via Server-Sent Events."""
    session_id = await chat_service.get_or_create_session(request.session_id)
    history = await chat_service.get_history(session_id)

    intent = retriever.classify_intent(request.message)
    products = await retriever.retrieve_products(request.message, top_k=10)
    deals = await retriever.retrieve_deals(request.message, top_k=3)
    stores = await retriever.retrieve_stores(request.message, top_k=3) if intent == "store_info" else []

    context = generator.build_context(products, deals, stores)

    async def event_stream():
        full_response = []
        async for chunk in generator.generate_stream(request.message, context, history):
            full_response.append(chunk)
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

        # Save after streaming completes
        response_text = "".join(full_response)
        await chat_service.append_message(session_id, "user", request.message)
        await chat_service.append_message(session_id, "assistant", response_text)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/chat/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_history(session_id: str):
    """Get chat history for a session."""
    messages = await chat_service.get_history(session_id)
    return ChatHistoryResponse(
        session_id=session_id,
        messages=[
            ChatHistoryItem(role=m["role"], content=m["content"], timestamp=m.get("timestamp"))
            for m in messages
        ],
    )
