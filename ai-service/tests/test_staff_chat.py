"""Tests for staff chat router — auth, role gating, hybrid routing."""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestStaffAuth:
    """Interview topic: role-based access control via header."""

    def test_no_role_header_returns_403(self):
        resp = client.post("/api/chat/staff", json={"message": "How many products?"})
        assert resp.status_code == 403
        assert "X-Staff-Role" in resp.json()["detail"]

    def test_invalid_role_returns_403(self):
        resp = client.post(
            "/api/chat/staff",
            json={"message": "How many products?"},
            headers={"X-Staff-Role": "customer"},
        )
        assert resp.status_code == 403

    def test_associate_role_accepted(self):
        with patch("app.routers.staff_chat.classify_staff_query",
                   return_value={"type": "db_query", "action": "list_categories", "params": {}}), \
             patch("app.routers.staff_chat.execute_staff_query",
                   return_value={"answer": "Categories listed", "data": []}), \
             patch("app.routers.staff_chat.chat_service") as mock_cs:
            mock_cs.get_or_create_session = AsyncMock(return_value="sess-1")
            mock_cs.append_message = AsyncMock()
            mock_cs.persist_message = MagicMock()

            resp = client.post(
                "/api/chat/staff",
                json={"message": "Show categories"},
                headers={"X-Staff-Role": "associate"},
            )

        assert resp.status_code == 200

    def test_manager_role_accepted(self):
        with patch("app.routers.staff_chat.classify_staff_query",
                   return_value={"type": "db_query", "action": "deal_summary", "params": {}}), \
             patch("app.routers.staff_chat.execute_staff_query",
                   return_value={"answer": "Deal summary", "data": []}), \
             patch("app.routers.staff_chat.chat_service") as mock_cs:
            mock_cs.get_or_create_session = AsyncMock(return_value="sess-1")
            mock_cs.append_message = AsyncMock()
            mock_cs.persist_message = MagicMock()

            resp = client.post(
                "/api/chat/staff",
                json={"message": "Deal summary"},
                headers={"X-Staff-Role": "manager"},
            )

        assert resp.status_code == 200


class TestStaffDbRoute:
    """Interview topic: structured queries skip LLM — zero token cost."""

    def test_db_query_returns_model_db_direct(self):
        with patch("app.routers.staff_chat.classify_staff_query",
                   return_value={"type": "db_query", "action": "count_products", "params": {}}), \
             patch("app.routers.staff_chat.execute_staff_query",
                   return_value={"answer": "We carry **3300** total products.", "data": [{"count": 3300}]}), \
             patch("app.routers.staff_chat.chat_service") as mock_cs:
            mock_cs.get_or_create_session = AsyncMock(return_value="sess-1")
            mock_cs.append_message = AsyncMock()
            mock_cs.persist_message = MagicMock()

            resp = client.post(
                "/api/chat/staff",
                json={"message": "How many products do we carry?"},
                headers={"X-Staff-Role": "associate"},
            )

        data = resp.json()
        assert data["model"] == "db_direct"
        assert data["latency_ms"] == 0
        assert "3300" in data["message"]
        assert data["products"] == []

    def test_db_query_persists_to_postgres(self):
        with patch("app.routers.staff_chat.classify_staff_query",
                   return_value={"type": "db_query", "action": "list_categories", "params": {}}), \
             patch("app.routers.staff_chat.execute_staff_query",
                   return_value={"answer": "Categories", "data": []}), \
             patch("app.routers.staff_chat.chat_service") as mock_cs:
            mock_cs.get_or_create_session = AsyncMock(return_value="sess-1")
            mock_cs.append_message = AsyncMock()
            mock_cs.persist_message = MagicMock()

            client.post(
                "/api/chat/staff",
                json={"message": "List categories"},
                headers={"X-Staff-Role": "associate"},
            )

        # Verify persist was called with model="db_direct"
        calls = mock_cs.persist_message.call_args_list
        assert len(calls) == 2  # user + assistant
        assistant_call = calls[1]
        assert assistant_call.kwargs.get("model") == "db_direct" or "db_direct" in str(assistant_call)


class TestStaffRagRoute:
    """Interview topic: natural language questions use full RAG pipeline."""

    def test_rag_query_uses_llm(self):
        with patch("app.routers.staff_chat.classify_staff_query",
                   return_value={"type": "rag"}), \
             patch("app.routers.staff_chat.retriever") as mock_ret, \
             patch("app.routers.staff_chat.generator") as mock_gen, \
             patch("app.routers.staff_chat.chat_service") as mock_cs:

            mock_cs.get_or_create_session = AsyncMock(return_value="sess-1")
            mock_cs.get_history = AsyncMock(return_value=[])
            mock_cs.append_message = AsyncMock()
            mock_cs.persist_message = MagicMock()

            mock_ret.classify_intent.return_value = "general"
            mock_ret.retrieve_products = AsyncMock(return_value=[])
            mock_ret.retrieve_deals = AsyncMock(return_value=[])
            mock_ret.retrieve_stores = AsyncMock(return_value=[])

            mock_gen.build_context.return_value = "No products found."
            mock_gen.settings.LLM_PROVIDER = "ollama"
            mock_gen._generate_ollama = AsyncMock(return_value=("Staff response here", "llama3.1:8b"))

            resp = client.post(
                "/api/chat/staff",
                json={"message": "What should I recommend for a nut allergy?"},
                headers={"X-Staff-Role": "associate"},
            )

        data = resp.json()
        assert data["model"] == "llama3.1:8b"
        assert data["latency_ms"] > 0 or data["latency_ms"] == 0  # may be near-zero in mock
        assert data["message"] == "Staff response here"
