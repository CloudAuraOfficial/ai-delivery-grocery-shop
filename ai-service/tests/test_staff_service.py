"""Tests for staff service — query classification and DB query handlers."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.staff_service import classify_staff_query, execute_staff_query


# ─── Query Classification ────────────────────────────────────

class TestClassifyStaffQuery:
    """Interview topic: hybrid DB+RAG routing — structured queries skip the LLM."""

    # Count queries
    def test_count_products_general(self):
        result = classify_staff_query("How many products do we carry?")
        assert result["type"] == "db_query"
        assert result["action"] == "count_products"

    def test_count_products_by_category(self):
        result = classify_staff_query("How many baby products do we have?")
        assert result["type"] == "db_query"
        assert result["action"] == "count_products"
        assert result["params"]["category"] == "Baby"

    def test_count_organic(self):
        result = classify_staff_query("How many organic products are there?")
        assert result["type"] == "db_query"
        assert result["params"]["organic_only"] is True

    def test_count_by_brand(self):
        result = classify_staff_query("How many Pampers products do we have?")
        assert result["type"] == "db_query"
        assert result["params"]["brand"] == "pampers"

    def test_count_deals(self):
        result = classify_staff_query("How many BOGO deals are active?")
        assert result["type"] == "db_query"
        assert result["action"] == "count_deals"
        assert result["params"]["deal_type"] == "BOGO"

    def test_count_weekly_deals(self):
        result = classify_staff_query("Total weekly deals?")
        assert result["type"] == "db_query"
        assert result["action"] == "count_deals"
        assert result["params"]["deal_type"] == "WeeklyDeal"

    # Expiring deals
    def test_expiring_deals(self):
        result = classify_staff_query("What deals are expiring today?")
        assert result["type"] == "db_query"
        assert result["action"] == "expiring_deals"

    def test_ending_soon(self):
        result = classify_staff_query("Which deals are ending soon?")
        assert result["type"] == "db_query"
        assert result["action"] == "expiring_deals"

    # Category listing
    def test_list_categories(self):
        result = classify_staff_query("Show me all categories")
        assert result["type"] == "db_query"
        assert result["action"] == "list_categories"

    # Price queries
    def test_cheapest_products(self):
        result = classify_staff_query("What are the cheapest fresh products?")
        assert result["type"] == "db_query"
        assert result["action"] == "cheapest_products"
        assert result["params"]["category"] == "Fresh"

    def test_most_expensive(self):
        result = classify_staff_query("Most expensive meat products?")
        assert result["type"] == "db_query"
        assert result["action"] == "most_expensive_products"
        assert result["params"]["category"] == "Meat & Seafood"

    def test_products_under_price(self):
        result = classify_staff_query("Show products under $5 in beverages")
        assert result["type"] == "db_query"
        assert result["action"] == "products_under_price"
        assert result["params"]["max_price"] == 5.0
        assert result["params"]["category"] == "Beverages"

    # Brand queries
    def test_list_brands(self):
        result = classify_staff_query("What brands do we carry in deli?")
        assert result["type"] == "db_query"
        assert result["action"] == "list_brands"
        assert result["params"]["category"] == "Deli"

    # Store brand
    def test_store_brand(self):
        result = classify_staff_query("Show me our private label products")
        assert result["type"] == "db_query"
        assert result["action"] == "store_brand_products"

    def test_greenwise(self):
        result = classify_staff_query("List all GreenWise items in fresh")
        assert result["type"] == "db_query"
        assert result["action"] == "store_brand_products"
        assert result["params"]["category"] == "Fresh"

    # Deal summary
    def test_deal_summary(self):
        result = classify_staff_query("Give me a deal summary")
        assert result["type"] == "db_query"
        assert result["action"] == "deal_summary"

    def test_active_deals(self):
        result = classify_staff_query("How are active deals looking?")
        assert result["type"] == "db_query"
        assert result["action"] == "deal_summary"

    # Subcategories
    def test_subcategories(self):
        result = classify_staff_query("What subcategories do we have in baby?")
        assert result["type"] == "db_query"
        assert result["action"] == "list_subcategories"
        assert result["params"]["category"] == "Baby"

    # RAG fallback
    def test_natural_language_falls_to_rag(self):
        result = classify_staff_query("A customer is asking about meal planning suggestions")
        assert result["type"] == "rag"

    def test_complex_question_falls_to_rag(self):
        result = classify_staff_query("Why are we seeing low sales on organic produce this week?")
        assert result["type"] == "rag"

    def test_recommendation_falls_to_rag(self):
        result = classify_staff_query("What should I recommend to someone with a nut allergy?")
        assert result["type"] == "rag"


# ─── Query Execution ─────────────────────────────────────────

class TestExecuteStaffQuery:

    def test_handles_db_failure_gracefully(self):
        with patch("app.services.staff_service.get_connection", side_effect=Exception("DB down")):
            result = execute_staff_query("count_products", {})

        assert "Sorry" in result["answer"]
        assert result["data"] == []

    def test_count_products_returns_formatted_answer(self):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = {"cnt": 3300}

        with patch("app.services.staff_service.get_connection", return_value=mock_conn):
            result = execute_staff_query("count_products", {})

        assert "3300" in result["answer"] or "3,300" in result["answer"]
        assert result["data"] == [{"count": 3300}]

    def test_list_categories_returns_all(self):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [
            {"Name": "Baby", "Slug": "baby", "product_count": 550},
            {"Name": "Fresh", "Slug": "fresh", "product_count": 550},
        ]

        with patch("app.services.staff_service.get_connection", return_value=mock_conn):
            result = execute_staff_query("list_categories", {})

        assert "Baby" in result["answer"]
        assert "Fresh" in result["answer"]
        assert "550" in result["answer"]

    def test_deal_summary_groups_by_type(self):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [
            {"DealType": "BOGO", "cnt": 200, "avg_discount": None},
            {"DealType": "WeeklyDeal", "cnt": 150, "avg_discount": 30.5},
        ]

        with patch("app.services.staff_service.get_connection", return_value=mock_conn):
            result = execute_staff_query("deal_summary", {})

        assert "350 total" in result["answer"]
        assert "BOGO: 200" in result["answer"]
        assert "WeeklyDeal: 150" in result["answer"]
