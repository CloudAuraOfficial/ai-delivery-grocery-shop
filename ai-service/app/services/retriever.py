"""Qdrant hybrid retriever with metadata filtering."""

import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import settings
from app.services.embedder import get_embedding

logger = structlog.get_logger()

_qdrant: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    global _qdrant
    if _qdrant is None:
        _qdrant = QdrantClient(url=settings.QDRANT_URL)
    return _qdrant


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


async def retrieve_products(query: str, top_k: int = 10) -> list[dict]:
    """Retrieve relevant products from Qdrant."""
    embedding = await get_embedding(query)
    qdrant = get_qdrant()

    # Build filter
    category = detect_category_filter(query)
    filters = None
    if category:
        filters = Filter(
            must=[FieldCondition(key="category", match=MatchValue(value=category))]
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
        products.append({
            "sku": payload.get("sku", ""),
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

    logger.info("product_retrieval", query=query[:50], category_filter=category, results=len(products))
    return products


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
