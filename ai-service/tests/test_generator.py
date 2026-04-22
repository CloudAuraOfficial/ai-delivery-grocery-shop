"""Tests for generator — context building, message construction, LLM generation."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.generator import build_context, build_messages, generate, SYSTEM_PROMPT


# ─── Context Building ────────────────────────────────────────

class TestBuildContext:
    """Interview topic: RAG context assembly from retrieval results."""

    def test_products_only(self, sample_products):
        context = build_context(sample_products, [], [])

        assert "=== Available Products ===" in context
        assert "Cal-Organic Broccoli" in context
        assert "$4.02/lb" in context
        assert "Organic" in context  # is_organic flag
        assert "Cal-Organic" in context  # brand

    def test_deals_included(self, sample_products, sample_deals):
        context = build_context(sample_products, sample_deals, [])

        assert "=== Current Deals ===" in context
        assert "30% Off Cal-Organic Broccoli" in context
        assert "WeeklyDeal" in context
        assert "30% off" in context

    def test_stores_included(self, sample_products, sample_stores):
        context = build_context(sample_products, [], sample_stores)

        assert "=== Store Locations ===" in context
        assert "Lakeland South" in context
        assert "(863) 555-0101" in context

    def test_full_context(self, sample_products, sample_deals, sample_stores):
        context = build_context(sample_products, sample_deals, sample_stores)

        assert "=== Available Products ===" in context
        assert "=== Current Deals ===" in context
        assert "=== Store Locations ===" in context

    def test_empty_retrieval_returns_fallback(self):
        context = build_context([], [], [])

        assert context == "No relevant products found in our catalog."

    def test_limits_products_to_8(self):
        products = [
            {"name": f"Product {i}", "price": 1.0, "unit": "each",
             "category": "Fresh", "is_organic": False, "brand": None}
            for i in range(15)
        ]
        context = build_context(products, [], [])

        # Should have exactly 8 product lines (limited by [:8])
        product_lines = [l for l in context.split("\n") if l.startswith("- Product")]
        assert len(product_lines) == 8

    def test_limits_deals_to_5(self):
        deals = [
            {"title": f"Deal {i}", "product_name": f"P{i}",
             "deal_type": "WeeklyDeal", "discount_percent": 20}
            for i in range(10)
        ]
        context = build_context([], deals, [])

        deal_lines = [l for l in context.split("\n") if l.startswith("- Deal")]
        assert len(deal_lines) == 5


# ─── Message Construction ────────────────────────────────────

class TestBuildMessages:
    """Interview topic: LLM prompt engineering, system prompts, context injection."""

    def test_basic_message_structure(self):
        messages = build_messages("What fruit do you have?", "Some context")

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT
        assert messages[1]["role"] == "user"
        assert "What fruit do you have?" in messages[1]["content"]
        assert "Some context" in messages[1]["content"]

    def test_context_injected_before_question(self):
        messages = build_messages("my question", "product info here")

        user_msg = messages[1]["content"]
        # Context should come before the question
        ctx_pos = user_msg.index("product info here")
        q_pos = user_msg.index("my question")
        assert ctx_pos < q_pos

    def test_history_included(self, sample_history):
        messages = build_messages("follow up question", "context", sample_history)

        # system + 2 history msgs + 1 user = 4
        assert len(messages) == 4
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "What fruit do you have?"
        assert messages[2]["role"] == "assistant"

    def test_history_limited_to_last_10(self):
        long_history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
            for i in range(20)
        ]
        messages = build_messages("new question", "ctx", long_history)

        # system + 10 history + 1 user = 12
        assert len(messages) == 12

    def test_no_history(self):
        messages = build_messages("first message", "context", None)

        assert len(messages) == 2  # system + user only

    def test_system_prompt_contains_key_rules(self):
        assert "3,000+" in SYSTEM_PROMPT
        assert "Only recommend products that appear in the provided context" in SYSTEM_PROMPT
        assert "Lakeland, Florida" in SYSTEM_PROMPT


# ─── LLM Generation ──────────────────────────────────────────

class TestGenerate:
    """Interview topic: provider abstraction, latency tracking."""

    @pytest.mark.asyncio
    async def test_ollama_generation(self):
        mock_response = {
            "message": {"content": "Here are some great organic options!"},
        }

        with patch("app.services.generator.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "ollama"
            mock_settings.LLM_MODEL = "llama3.1:8b"
            mock_settings.OLLAMA_BASE_URL = "http://ollama:11434"

            with patch("app.services.generator._generate_ollama", new_callable=AsyncMock,
                       return_value=("Here are some great organic options!", "llama3.1:8b")):
                response, latency, model = await generate("organic fruit", "context")

        assert response == "Here are some great organic options!"
        assert model == "llama3.1:8b"
        assert latency >= 0  # latency is always non-negative

    @pytest.mark.asyncio
    async def test_azure_generation(self):
        with patch("app.services.generator.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "azure_openai"
            mock_settings.AZURE_OPENAI_CHAT_DEPLOYMENT = "gpt-4o"

            with patch("app.services.generator._generate_azure", new_callable=AsyncMock,
                       return_value=("Azure response here", "gpt-4o")):
                response, latency, model = await generate("query", "context")

        assert response == "Azure response here"
        assert model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_latency_is_tracked(self):
        with patch("app.services.generator.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "ollama"
            mock_settings.LLM_MODEL = "llama3.1:8b"

            with patch("app.services.generator._generate_ollama", new_callable=AsyncMock,
                       return_value=("response", "llama3.1:8b")):
                _, latency, _ = await generate("query", "context")

        assert isinstance(latency, float)
        assert latency >= 0
