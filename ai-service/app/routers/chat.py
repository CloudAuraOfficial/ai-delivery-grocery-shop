"""Chat endpoints with full RAG pipeline."""

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse, ProductReference, ChatHistoryResponse, ChatHistoryItem
from app.rate_limit import limiter, CHAT_LIMIT
from app.security.input_guard import check as guard_check, REJECTION_MESSAGE
from app.services import retriever, generator, chat_service
from app.services.custom_responses import check_custom_scenario

logger = structlog.get_logger()

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(CHAT_LIMIT)
async def chat_message(request: Request, body: ChatRequest):
    """Send a message and get an AI response with product recommendations."""
    # Get or create session
    session_id = await chat_service.get_or_create_session(body.session_id)

    # Input guard: length cap + injection-pattern filter
    guard = guard_check(body.message)
    if not guard.ok:
        from app.routers.metrics import INPUT_GUARD_BLOCKS
        INPUT_GUARD_BLOCKS.labels(reason=guard.reason).inc()
        logger.warning("chat_input_blocked", session=session_id[:8], reason=guard.reason)
        return ChatResponse(
            message=REJECTION_MESSAGE,
            session_id=session_id,
            products=[],
            latency_ms=0,
            model="guard",
        )

    # Check custom scenarios first (order tracking, off-topic, complaints, etc.)
    custom = check_custom_scenario(body.message)
    if custom and custom["skip_rag"]:
        logger.info("chat_custom_response", session=session_id[:8], scenario="custom_skip_rag")
        await chat_service.append_message(session_id, "user", body.message)
        await chat_service.append_message(session_id, "assistant", custom["message"])
        return ChatResponse(
            message=custom["message"],
            session_id=session_id,
            products=[],
            latency_ms=0,
            model="custom",
        )

    # Get conversation history
    history = await chat_service.get_history(session_id)

    # Classify intent and retrieve context
    intent = retriever.classify_intent(body.message)
    logger.info("chat_request", intent=intent, session=session_id[:8])

    products = []
    deals = []
    stores = []

    if intent == "store_info":
        stores = await retriever.retrieve_stores(body.message, top_k=5)
        products = await retriever.retrieve_products(body.message, top_k=3)
    elif intent == "deal_inquiry":
        deals = await retriever.retrieve_deals(body.message, top_k=8)
        products = await retriever.retrieve_products(body.message, top_k=5)
    else:
        products = await retriever.retrieve_products(body.message, top_k=10)
        deals = await retriever.retrieve_deals(body.message, top_k=3)

    # If custom scenario exists but wants RAG results too (e.g., brand not carried → show alternatives)
    if custom and not custom["skip_rag"]:
        # Prepend custom message, then let RAG add product context
        context = generator.build_context(products, deals, stores)
        rag_response, latency_ms, model = await generator.generate(
            body.message, context, history
        )
        response_text = custom["message"] + "\n\n" + rag_response
    else:
        # Standard RAG flow
        context = generator.build_context(products, deals, stores)
        response_text, latency_ms, model = await generator.generate(
            body.message, context, history
        )

    # Save to session history
    await chat_service.append_message(session_id, "user", body.message)
    await chat_service.append_message(session_id, "assistant", response_text)

    # Persist to PostgreSQL (fire-and-forget)
    product_skus = [p["sku"] for p in products[:5]]
    chat_service.persist_message(session_id, "user", body.message)
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
        latency_ms=round(latency_ms, 1) if latency_ms else 0,
        model=model,
    )


@router.post("/chat/stream")
@limiter.limit(CHAT_LIMIT)
async def chat_stream(request: Request, body: ChatRequest):
    """Stream a chat response via Server-Sent Events."""
    session_id = await chat_service.get_or_create_session(body.session_id)

    guard = guard_check(body.message)
    if not guard.ok:
        logger.warning("chat_stream_input_blocked", session=session_id[:8], reason=guard.reason)
        async def rejection_stream():
            yield f"data: {REJECTION_MESSAGE}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(rejection_stream(), media_type="text/event-stream")

    history = await chat_service.get_history(session_id)

    intent = retriever.classify_intent(body.message)
    products = await retriever.retrieve_products(body.message, top_k=10)
    deals = await retriever.retrieve_deals(body.message, top_k=3)
    stores = await retriever.retrieve_stores(body.message, top_k=3) if intent == "store_info" else []

    context = generator.build_context(products, deals, stores)

    async def event_stream():
        full_response = []
        async for chunk in generator.generate_stream(body.message, context, history):
            full_response.append(chunk)
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

        # Save after streaming completes
        response_text = "".join(full_response)
        await chat_service.append_message(session_id, "user", body.message)
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
