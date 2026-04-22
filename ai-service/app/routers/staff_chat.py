"""Staff chat endpoint — hybrid DB + RAG for store associates."""

import structlog
from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, ProductReference
from app.services import retriever, generator, chat_service
from app.services.staff_service import classify_staff_query, execute_staff_query

logger = structlog.get_logger()

router = APIRouter(tags=["staff-chat"])

VALID_ROLES = {"associate", "manager"}

STAFF_SYSTEM_PROMPT = """You are an internal AI assistant for AI Delivery Grocery Shop store associates and managers.
You help staff with:
- Product lookups (stock, pricing, SKUs, brands)
- Deal status and performance
- Category and subcategory information
- Customer question preparation (helping staff answer customer questions)

Rules:
1. Be concise and data-driven. Staff want facts, not marketing copy.
2. Always include SKUs and exact prices when referencing products.
3. When showing deals, include the deal type, discount, and expiry date.
4. If you don't have data, say so — don't guess inventory or pricing.
5. For managers: include aggregate data (counts, averages) when relevant.
6. Format responses for quick scanning — use bullet points and bold for key numbers."""


@router.post("/chat/staff", response_model=ChatResponse)
async def staff_chat(
    request: ChatRequest,
    x_staff_role: str = Header(default=None, alias="X-Staff-Role"),
):
    """Staff chat endpoint with role-based access."""
    # Auth: require valid staff role
    if not x_staff_role or x_staff_role.lower() not in VALID_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Provide X-Staff-Role header with one of: {', '.join(VALID_ROLES)}",
        )

    role = x_staff_role.lower()
    session_id = await chat_service.get_or_create_session(request.session_id)

    # Classify: can we answer from DB directly?
    classification = classify_staff_query(request.message)
    logger.info("staff_query", type=classification["type"], role=role, session=session_id[:8])

    if classification["type"] == "db_query":
        # Direct DB path — zero LLM cost
        result = execute_staff_query(classification["action"], classification["params"])

        # Save to session
        await chat_service.append_message(session_id, "user", request.message)
        await chat_service.append_message(session_id, "assistant", result["answer"])

        # Persist to PostgreSQL
        chat_service.persist_message(session_id, "user", request.message)
        chat_service.persist_message(
            session_id, "assistant", result["answer"],
            latency_ms=0, model="db_direct",
        )

        return ChatResponse(
            message=result["answer"],
            session_id=session_id,
            products=[],
            latency_ms=0,
            model="db_direct",
        )

    # RAG path — for natural language questions
    history = await chat_service.get_history(session_id)

    intent = retriever.classify_intent(request.message)
    products = await retriever.retrieve_products(request.message, top_k=10)
    deals = await retriever.retrieve_deals(request.message, top_k=5)
    stores = await retriever.retrieve_stores(request.message, top_k=3) if intent == "store_info" else []

    context = generator.build_context(products, deals, stores)

    # Use staff system prompt instead of customer prompt
    messages = [{"role": "system", "content": STAFF_SYSTEM_PROMPT}]
    if history:
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    role_context = " You are speaking to a store manager." if role == "manager" else ""
    augmented = f"Based on the following product data:\n\n{context}\n\nStaff question ({role}): {request.message}{role_context}"
    messages.append({"role": "user", "content": augmented})

    # Generate via LLM
    import time
    start = time.time()
    if generator.settings.LLM_PROVIDER == "azure_openai":
        response_text, model = await generator._generate_azure(messages)
    else:
        response_text, model = await generator._generate_ollama(messages)
    latency = (time.time() - start) * 1000

    # Save to session + persist
    await chat_service.append_message(session_id, "user", request.message)
    await chat_service.append_message(session_id, "assistant", response_text)

    product_skus = [p["sku"] for p in products[:5]]
    chat_service.persist_message(session_id, "user", request.message)
    chat_service.persist_message(
        session_id, "assistant", response_text,
        product_skus, latency, model,
    )

    product_refs = [
        ProductReference(
            sku=p["sku"], name=p["name"], price=p["price"],
            category=p["category"],
            deal_type=next((d["deal_type"] for d in deals if d.get("product_sku") == p["sku"]), None),
        )
        for p in products[:5]
    ]

    return ChatResponse(
        message=response_text,
        session_id=session_id,
        products=product_refs,
        latency_ms=round(latency, 1),
        model=model,
    )
