"""Shared fixtures for AI service tests."""

import pytest


@pytest.fixture
def sample_products():
    """Realistic product results from Qdrant retrieval."""
    return [
        {
            "sku": "FRE-0042",
            "name": "Cal-Organic Broccoli",
            "category": "Fresh",
            "subcategory": "Vegetables",
            "brand": "Cal-Organic",
            "price": 4.02,
            "unit": "lb",
            "is_organic": True,
            "is_store_brand": False,
            "tags": "vegetable,organic,broccoli",
            "score": 0.92,
        },
        {
            "sku": "FRE-0105",
            "name": "GreenWise Organic Spinach",
            "category": "Fresh",
            "subcategory": "Leafy Greens",
            "brand": "GreenWise",
            "price": 3.49,
            "unit": "each",
            "is_organic": True,
            "is_store_brand": True,
            "tags": "vegetable,organic,spinach",
            "score": 0.88,
        },
        {
            "sku": "BEV-0201",
            "name": "Crystal Clear Spring Water 24-Pack",
            "category": "Beverages",
            "subcategory": "Water",
            "brand": "Crystal Clear",
            "price": 4.99,
            "unit": "pack",
            "is_organic": False,
            "is_store_brand": False,
            "tags": "water,hydration",
            "score": 0.45,
        },
    ]


@pytest.fixture
def sample_deals():
    """Realistic deal results from Qdrant retrieval."""
    return [
        {
            "deal_type": "WeeklyDeal",
            "title": "30% Off Cal-Organic Broccoli",
            "product_sku": "FRE-0042",
            "product_name": "Cal-Organic Broccoli",
            "category": "Fresh",
            "discount_percent": 30,
            "score": 0.91,
        },
        {
            "deal_type": "BOGO",
            "title": "Buy One Get One Free",
            "product_sku": "FRE-0105",
            "product_name": "GreenWise Organic Spinach",
            "category": "Fresh",
            "discount_percent": None,
            "score": 0.85,
        },
    ]


@pytest.fixture
def sample_stores():
    """Realistic store results from Qdrant retrieval."""
    return [
        {
            "name": "AI Grocery - Lakeland South",
            "address": "3501 S Florida Ave",
            "city": "Lakeland",
            "state": "FL",
            "zipCode": "33803",
            "phone": "(863) 555-0101",
            "storeNumber": "1001",
            "score": 0.95,
        },
    ]


@pytest.fixture
def sample_history():
    """Conversation history from Redis."""
    return [
        {"role": "user", "content": "What fruit do you have?"},
        {"role": "assistant", "content": "We have a great selection of fresh fruits!"},
    ]
