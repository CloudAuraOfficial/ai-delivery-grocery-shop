"""Tests for custom response scenarios — pre-RAG routing logic."""

from app.services.custom_responses import check_custom_scenario


class TestCustomScenarios:
    """Interview topic: pre-RAG scenario routing, guardrails, off-topic handling."""

    # ─── Order tracking (skip RAG) ───────────────────────────

    def test_order_tracking_detected(self):
        result = check_custom_scenario("track my order")
        assert result is not None
        assert result["skip_rag"] is True
        assert "tracking" in result["message"].lower() or "order" in result["message"].lower()

    def test_order_status_detected(self):
        result = check_custom_scenario("What is my order status?")
        assert result is not None
        assert result["skip_rag"] is True

    # ─── Brand not carried (RAG continues for alternatives) ──

    def test_walmart_brand_detected(self):
        result = check_custom_scenario("Do you have Great Value bread?")
        assert result is not None
        assert result["skip_rag"] is False  # RAG still runs to find alternatives
        assert "alternative" in result["message"].lower()

    def test_costco_brand_detected(self):
        result = check_custom_scenario("I want Kirkland water")
        assert result is not None
        assert result["skip_rag"] is False

    def test_trader_joe_detected(self):
        result = check_custom_scenario("Do you carry Trader Joe items?")
        assert result is not None

    # ─── Delivery area (skip RAG) ────────────────────────────

    def test_delivery_area_detected(self):
        result = check_custom_scenario("Do you deliver to Tampa?")
        assert result is not None
        assert result["skip_rag"] is True
        assert "Lakeland" in result["message"]
        assert "$35" in result["message"] or "35" in result["message"]

    # ─── Payment methods (skip RAG) ──────────────────────────

    def test_payment_detected(self):
        result = check_custom_scenario("What payment methods do you accept?")
        assert result is not None
        assert result["skip_rag"] is True
        assert "demo" in result["message"].lower()

    # ─── Returns/refunds (skip RAG) ──────────────────────────

    def test_return_detected(self):
        result = check_custom_scenario("I want to return an item")
        assert result is not None
        assert result["skip_rag"] is True

    def test_refund_detected(self):
        result = check_custom_scenario("Can I get a refund?")
        assert result is not None
        assert result["skip_rag"] is True

    # ─── Coupons (RAG continues to show deals) ──────────────

    def test_coupon_detected(self):
        result = check_custom_scenario("Do you have a promo code?")
        assert result is not None
        assert result["skip_rag"] is False  # RAG shows current deals
        assert "BOGO" in result["message"]

    # ─── Dietary restrictions (RAG continues) ────────────────

    def test_vegan_detected(self):
        result = check_custom_scenario("Do you have vegan products?")
        assert result is not None
        assert result["skip_rag"] is False
        assert "vegan" in result["message"].lower()

    def test_gluten_free_detected(self):
        result = check_custom_scenario("I need gluten-free bread")
        assert result is not None
        assert "gluten-free" in result["message"].lower()

    # ─── Off-topic (skip RAG) ────────────────────────────────

    def test_weather_off_topic(self):
        result = check_custom_scenario("What's the weather like?")
        assert result is not None
        assert result["skip_rag"] is True
        assert "grocery" in result["message"].lower()

    def test_sports_off_topic(self):
        result = check_custom_scenario("Who won the sports game?")
        assert result is not None
        assert result["skip_rag"] is True

    def test_joke_off_topic(self):
        result = check_custom_scenario("Tell me a joke")
        assert result is not None
        assert result["skip_rag"] is True

    # ─── Complaints (skip RAG) ───────────────────────────────

    def test_complaint_detected(self):
        result = check_custom_scenario("I had a terrible experience")
        assert result is not None
        assert result["skip_rag"] is True
        assert "sorry" in result["message"].lower()

    # ─── Bulk/catering (RAG continues) ───────────────────────

    def test_catering_detected(self):
        result = check_custom_scenario("I need catering for a party")
        assert result is not None
        assert result["skip_rag"] is False
        assert "party" in result["message"].lower() or "platter" in result["message"].lower()

    # ─── Normal queries pass through (None) ──────────────────

    def test_product_query_returns_none(self):
        assert check_custom_scenario("What organic apples do you have?") is None

    def test_deal_query_returns_none(self):
        assert check_custom_scenario("Show me BOGO deals on meat") is None

    def test_generic_query_returns_none(self):
        assert check_custom_scenario("What's good for dinner tonight?") is None

    def test_empty_query_returns_none(self):
        assert check_custom_scenario("hello") is None
