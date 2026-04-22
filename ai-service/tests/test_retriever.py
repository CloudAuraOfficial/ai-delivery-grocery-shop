"""Tests for retriever — intent classification, category/deal detection, Qdrant search."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.retriever import (
    classify_intent,
    detect_category_filter,
    detect_deal_filter,
    retrieve_products,
    retrieve_deals,
    retrieve_stores,
)


# ─── Intent Classification ────────────────────────────────────

class TestClassifyIntent:
    """Interview topic: keyword-based intent routing before RAG."""

    def test_deal_keywords(self):
        assert classify_intent("What's on sale today?") == "deal_inquiry"
        assert classify_intent("Show me BOGO deals") == "deal_inquiry"
        assert classify_intent("Any discounts on meat?") == "deal_inquiry"

    def test_store_keywords(self):
        assert classify_intent("Where is the nearest store?") == "store_info"
        assert classify_intent("What are your hours?") == "store_info"
        assert classify_intent("Store address in Lakeland") == "store_info"

    def test_category_keywords(self):
        assert classify_intent("I need baby diapers") == "product_search"
        assert classify_intent("Show me fresh fruit") == "product_search"
        assert classify_intent("Do you have chicken breast?") == "product_search"

    def test_general_fallback(self):
        assert classify_intent("Something for dinner") == "general"
        assert classify_intent("What do you recommend?") == "general"

    def test_case_insensitive(self):
        assert classify_intent("BOGO DEALS NOW") == "deal_inquiry"
        assert classify_intent("STORE HOURS") == "store_info"


# ─── Category Detection ──────────────────────────────────────

class TestDetectCategoryFilter:
    """Interview topic: metadata filtering before vector search."""

    def test_fresh_keywords(self):
        assert detect_category_filter("organic fruit") == "Fresh"
        assert detect_category_filter("I need vegetables") == "Fresh"

    def test_meat_keywords(self):
        assert detect_category_filter("chicken breast") == "Meat & Seafood"
        assert detect_category_filter("shrimp cocktail") == "Meat & Seafood"
        # Note: "fresh shrimp" matches "fresh" first → Fresh category
        # This is a known keyword-priority limitation of the dict iteration order

    def test_beverages_keywords(self):
        assert detect_category_filter("coffee brands") == "Beverages"
        assert detect_category_filter("bottled water") == "Beverages"

    def test_baby_keywords(self):
        assert detect_category_filter("baby formula") == "Baby"
        assert detect_category_filter("diapers size 3") == "Baby"

    def test_household_keywords(self):
        assert detect_category_filter("laundry detergent") == "Household"
        assert detect_category_filter("cleaning supplies") == "Household"

    def test_deli_keywords(self):
        assert detect_category_filter("deli cheese") == "Deli"
        assert detect_category_filter("sandwich platter") == "Deli"
        # Note: "rotisserie chicken" matches "chicken" → Meat & Seafood
        # Another keyword-priority overlap — good interview talking point

    def test_no_category_match(self):
        assert detect_category_filter("something for dinner") is None
        assert detect_category_filter("what do you recommend") is None


# ─── Deal Type Detection ─────────────────────────────────────

class TestDetectDealFilter:

    def test_bogo(self):
        assert detect_deal_filter("Show me BOGO deals") == "BOGO"
        assert detect_deal_filter("buy one get one free") == "BOGO"

    def test_weekly(self):
        assert detect_deal_filter("weekly specials") == "WeeklyDeal"

    def test_daily(self):
        assert detect_deal_filter("daily deals") == "DailyDeal"
        assert detect_deal_filter("what's on sale today") == "DailyDeal"

    def test_no_deal_match(self):
        assert detect_deal_filter("organic apples") is None


# ─── Qdrant Product Retrieval ────────────────────────────────

class TestRetrieveProducts:
    """Interview topic: vector search with metadata filtering."""

    @pytest.mark.asyncio
    async def test_retrieves_products_from_qdrant(self):
        mock_result = MagicMock()
        mock_result.payload = {
            "sku": "FRE-0042", "name": "Broccoli", "category": "Fresh",
            "subcategory": "Veg", "brand": "Cal-Organic", "price": 4.02,
            "unit": "lb", "is_organic": True, "is_store_brand": False, "tags": "veg",
        }
        mock_result.score = 0.92

        with patch("app.services.retriever.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768), \
             patch("app.services.retriever.get_qdrant") as mock_qdrant:
            mock_qdrant.return_value.search.return_value = [mock_result]

            products = await retrieve_products("organic broccoli", top_k=5)

        assert len(products) == 1
        assert products[0]["sku"] == "FRE-0042"
        assert products[0]["name"] == "Broccoli"
        assert products[0]["score"] == 0.92

    @pytest.mark.asyncio
    async def test_applies_category_filter(self):
        with patch("app.services.retriever.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768), \
             patch("app.services.retriever.get_qdrant") as mock_qdrant:
            mock_qdrant.return_value.search.return_value = []

            await retrieve_products("fresh fruit", top_k=5)

            # Verify Qdrant was called with a category filter
            call_kwargs = mock_qdrant.return_value.search.call_args
            assert call_kwargs.kwargs.get("query_filter") is not None

    @pytest.mark.asyncio
    async def test_no_filter_for_generic_query(self):
        with patch("app.services.retriever.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768), \
             patch("app.services.retriever.get_qdrant") as mock_qdrant:
            mock_qdrant.return_value.search.return_value = []

            await retrieve_products("something for dinner", top_k=5)

            call_kwargs = mock_qdrant.return_value.search.call_args
            assert call_kwargs.kwargs.get("query_filter") is None

    @pytest.mark.asyncio
    async def test_empty_qdrant_returns_empty_list(self):
        with patch("app.services.retriever.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768), \
             patch("app.services.retriever.get_qdrant") as mock_qdrant:
            mock_qdrant.return_value.search.return_value = []

            products = await retrieve_products("nonexistent xyz", top_k=5)

        assert products == []


# ─── Qdrant Deal Retrieval ───────────────────────────────────

class TestRetrieveDeals:

    @pytest.mark.asyncio
    async def test_retrieves_deals_with_type_filter(self):
        mock_result = MagicMock()
        mock_result.payload = {
            "deal_type": "BOGO", "title": "Buy One Get One",
            "product_sku": "FRE-0042", "product_name": "Broccoli",
            "category": "Fresh", "discount_percent": None,
        }
        mock_result.score = 0.90

        with patch("app.services.retriever.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768), \
             patch("app.services.retriever.get_qdrant") as mock_qdrant:
            mock_qdrant.return_value.search.return_value = [mock_result]

            deals = await retrieve_deals("BOGO deals", top_k=5)

        assert len(deals) == 1
        assert deals[0]["deal_type"] == "BOGO"

        # Verify BOGO filter was applied
        call_kwargs = mock_qdrant.return_value.search.call_args
        assert call_kwargs.kwargs.get("query_filter") is not None


# ─── Qdrant Store Retrieval ──────────────────────────────────

class TestRetrieveStores:

    @pytest.mark.asyncio
    async def test_retrieves_stores(self):
        mock_result = MagicMock()
        mock_result.payload = {
            "name": "AI Grocery - Lakeland South",
            "address": "3501 S Florida Ave", "city": "Lakeland",
            "state": "FL", "zipCode": "33803", "phone": "(863) 555-0101",
            "storeNumber": "1001",
        }
        mock_result.score = 0.95

        with patch("app.services.retriever.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 768), \
             patch("app.services.retriever.get_qdrant") as mock_qdrant:
            mock_qdrant.return_value.search.return_value = [mock_result]

            stores = await retrieve_stores("nearest store", top_k=3)

        assert len(stores) == 1
        assert stores[0]["name"] == "AI Grocery - Lakeland South"
        assert stores[0]["phone"] == "(863) 555-0101"
