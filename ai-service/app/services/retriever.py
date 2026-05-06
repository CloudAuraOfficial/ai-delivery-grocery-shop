"""Hybrid retriever: Qdrant dense vectors + Postgres FTS/trigram, fused via RRF."""

import asyncio

import psycopg2
import psycopg2.extras
import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import settings
from app.services.embedder import get_embedding

logger = structlog.get_logger()

_qdrant: QdrantClient | None = None

RRF_K = 60  # standard RRF constant; higher = flatter weighting


def get_qdrant() -> QdrantClient:
    global _qdrant
    if _qdrant is None:
        _qdrant = QdrantClient(url=settings.QDRANT_URL)
    return _qdrant


def _pg_conn():
    return psycopg2.connect(settings.postgres_dsn)


def _keyword_search_products(query: str, top_k: int, category: str | None) -> list[dict]:
    """BM25-equivalent retrieval via Postgres FTS + trigram similarity on Name."""
    sql = """
        SELECT p."Sku", p."Name", p."Brand", p."Price", p."Unit",
               p."IsOrganic", p."IsStoreBrand", p."Tags",
               c."Name" AS category, c."Slug" AS category_slug,
               (
                 0.7 * COALESCE(ts_rank(
                   to_tsvector('english', p."Name" || ' ' || COALESCE(p."Description",'') || ' ' || COALESCE(p."Tags",'')),
                   plainto_tsquery('english', %(q)s)
                 ), 0)
                 +
                 0.3 * similarity(p."Name", %(q)s)
               ) AS score
        FROM "Products" p
        JOIN "Categories" c ON c."Id" = p."CategoryId"
        WHERE p."IsAvailable" = TRUE
          AND (
            to_tsvector('english', p."Name" || ' ' || COALESCE(p."Description",'') || ' ' || COALESCE(p."Tags",''))
              @@ plainto_tsquery('english', %(q)s)
            OR similarity(p."Name", %(q)s) > 0.15
          )
          AND (%(cat)s IS NULL OR c."Name" = %(cat)s)
        ORDER BY score DESC
        LIMIT %(k)s
    """
    try:
        with _pg_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, {"q": query, "cat": category, "k": top_k})
            rows = cur.fetchall()
    except Exception as exc:
        logger.warning("keyword_search_failed", error=str(exc))
        return []

    return [
        {
            "sku": r["Sku"],
            "name": r["Name"],
            "brand": r["Brand"] or "",
            "price": float(r["Price"]),
            "unit": r["Unit"],
            "is_organic": r.get("IsOrganic", False),
            "is_store_brand": r.get("IsStoreBrand", False),
            "tags": r["Tags"] or "",
            "category": r["category"],
            "subcategory": "",
            "score": float(r["score"]),
        }
        for r in rows
    ]


def _rrf_fuse(rankings: list[list[dict]], top_k: int) -> list[dict]:
    """Reciprocal Rank Fusion across ordered ranking lists, keyed by sku."""
    scores: dict[str, float] = {}
    seen: dict[str, dict] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking):
            sku = item.get("sku")
            if not sku:
                continue
            scores[sku] = scores.get(sku, 0.0) + 1.0 / (RRF_K + rank + 1)
            if sku not in seen:
                seen[sku] = item
    fused = sorted(
        ({**seen[sku], "rrf_score": s} for sku, s in scores.items()),
        key=lambda x: x["rrf_score"],
        reverse=True,
    )
    return fused[:top_k]


def classify_intent(query: str) -> str:
    """Simple keyword-based intent classification."""
    q = query.lower()

    deal_keywords = ["deal", "bogo", "sale", "discount", "off", "save", "coupon", "weekly", "daily", "free"]
    store_keywords = ["store", "location", "near", "address", "hours", "open", "close", "phone", "where"]
    category_keywords = ["baby", "beverage", "drink", "household", "cleaning", "fresh", "fruit", "vegetable",
                         "meat", "seafood", "chicken", "beef", "deli", "cheese"]

    if any(k in q for k in store_keywords):
        return "store_info"
    if any(k in q for k in deal_keywords):
        return "deal_inquiry"
    if any(k in q for k in category_keywords):
        return "product_search"

    return "general"


def detect_category_filter(query: str) -> str | None:
    """Detect if the query targets a specific category."""
    q = query.lower()
    category_map = {
        "baby": "Baby", "diaper": "Baby", "formula": "Baby", "wipes": "Baby",
        "beverage": "Beverages", "drink": "Beverages", "water": "Beverages", "soda": "Beverages",
        "coffee": "Beverages", "juice": "Beverages", "tea": "Beverages",
        "household": "Household", "cleaning": "Household", "paper towel": "Household", "laundry": "Household",
        "fresh": "Fresh", "fruit": "Fresh", "vegetable": "Fresh", "organic": "Fresh",
        "meat": "Meat & Seafood", "seafood": "Meat & Seafood", "chicken": "Meat & Seafood",
        "beef": "Meat & Seafood", "fish": "Meat & Seafood", "pork": "Meat & Seafood",
        "shrimp": "Meat & Seafood",
        "deli": "Deli", "cheese": "Deli", "sandwich": "Deli", "rotisserie": "Deli",
    }

    for keyword, category in category_map.items():
        if keyword in q:
            return category
    return None


def detect_deal_filter(query: str) -> str | None:
    """Detect if the query targets a specific deal type."""
    q = query.lower()
    if "bogo" in q or "buy one" in q:
        return "BOGO"
    if "weekly" in q:
        return "WeeklyDeal"
    if "daily" in q or "today" in q:
        return "DailyDeal"
    return None


async def _vector_search_products(query: str, top_k: int, category: str | None) -> list[dict]:
    embedding = await get_embedding(query)
    qdrant = get_qdrant()
    filters = (
        Filter(must=[FieldCondition(key="category", match=MatchValue(value=category))])
        if category else None
    )
    results = qdrant.search(
        collection_name="grocery_products",
        query_vector=embedding,
        limit=top_k,
        query_filter=filters,
    )
    products = []
    for r in results:
        payload = r.payload or {}
        sku = payload.get("sku") or f"qid-{r.id}"
        products.append({
            "sku": sku,
            "name": payload.get("name", ""),
            "category": payload.get("category", ""),
            "subcategory": payload.get("subcategory", ""),
            "brand": payload.get("brand", ""),
            "price": payload.get("price", 0),
            "unit": payload.get("unit", "each"),
            "is_organic": payload.get("is_organic", False),
            "is_store_brand": payload.get("is_store_brand", False),
            "tags": payload.get("tags", ""),
            "score": r.score,
        })
    return products


async def retrieve_products(query: str, top_k: int = 10) -> list[dict]:
    """Hybrid retrieval: vector + keyword, fused via RRF."""
    import time
    from app.routers.metrics import RAG_RETRIEVAL_LATENCY

    category = detect_category_filter(query)
    pool_k = max(top_k * 3, 20)  # over-fetch from each lane to give RRF room

    fused_start = time.time()

    async def timed_vector():
        s = time.time()
        out = await _vector_search_products(query, pool_k, category)
        RAG_RETRIEVAL_LATENCY.labels(lane="vector").observe(time.time() - s)
        return out

    async def timed_keyword():
        s = time.time()
        out = await asyncio.to_thread(_keyword_search_products, query, pool_k, category)
        RAG_RETRIEVAL_LATENCY.labels(lane="keyword").observe(time.time() - s)
        return out

    vector_results, keyword_results = await asyncio.gather(timed_vector(), timed_keyword())
    fused = _rrf_fuse([vector_results, keyword_results], top_k)
    RAG_RETRIEVAL_LATENCY.labels(lane="fused").observe(time.time() - fused_start)

    logger.info(
        "product_retrieval",
        query=query[:50],
        category_filter=category,
        vector=len(vector_results),
        keyword=len(keyword_results),
        fused=len(fused),
    )
    return fused


async def retrieve_deals(query: str, top_k: int = 10) -> list[dict]:
    """Retrieve relevant deals from Qdrant."""
    embedding = await get_embedding(query)
    qdrant = get_qdrant()

    deal_type = detect_deal_filter(query)
    filters = None
    if deal_type:
        filters = Filter(
            must=[FieldCondition(key="deal_type", match=MatchValue(value=deal_type))]
        )

    results = qdrant.search(
        collection_name="grocery_deals",
        query_vector=embedding,
        limit=top_k,
        query_filter=filters,
    )

    deals = []
    for r in results:
        payload = r.payload or {}
        deals.append({
            "deal_type": payload.get("deal_type", ""),
            "title": payload.get("title", ""),
            "product_sku": payload.get("product_sku", ""),
            "product_name": payload.get("product_name", ""),
            "category": payload.get("category", ""),
            "discount_percent": payload.get("discount_percent"),
            "score": r.score,
        })

    logger.info("deal_retrieval", query=query[:50], deal_filter=deal_type, results=len(deals))
    return deals


async def retrieve_stores(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve relevant stores from Qdrant."""
    embedding = await get_embedding(query)
    qdrant = get_qdrant()

    results = qdrant.search(
        collection_name="grocery_stores",
        query_vector=embedding,
        limit=top_k,
    )

    stores = []
    for r in results:
        payload = r.payload or {}
        stores.append({
            "name": payload.get("name", ""),
            "address": payload.get("address", ""),
            "city": payload.get("city", ""),
            "state": payload.get("state", ""),
            "zipCode": payload.get("zipCode", ""),
            "phone": payload.get("phone", ""),
            "storeNumber": payload.get("storeNumber", ""),
            "score": r.score,
        })

    return stores
