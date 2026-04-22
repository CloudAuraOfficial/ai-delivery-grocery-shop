"""Tests for chat service — Redis session management, PostgreSQL persistence."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.chat_service import (
    get_or_create_session,
    get_history,
    append_message,
    persist_message,
)


# ─── Session Management ──────────────────────────────────────

class TestGetOrCreateSession:
    """Interview topic: Redis session design, TTL, idempotency."""

    @pytest.mark.asyncio
    async def test_creates_new_session_when_none_provided(self):
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            session_id = await get_or_create_session(None)

        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_existing_session_if_valid(self):
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=True)

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            session_id = await get_or_create_session("existing-uuid-1234")

        assert session_id == "existing-uuid-1234"
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_new_session_if_expired(self):
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=False)  # session expired
        mock_redis.setex = AsyncMock()

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            session_id = await get_or_create_session("expired-uuid")

        # Should create a new session, not return the expired one
        assert session_id != "expired-uuid"
        mock_redis.setex.assert_called_once()


# ─── History Retrieval ────────────────────────────────────────

class TestGetHistory:

    @pytest.mark.asyncio
    async def test_returns_messages_from_redis(self):
        session_data = json.dumps({
            "messages": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        })
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=session_data)

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            history = await get_history("session-123")

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["content"] == "Hi there!"

    @pytest.mark.asyncio
    async def test_returns_empty_for_missing_session(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            history = await get_history("nonexistent")

        assert history == []


# ─── Message Appending ───────────────────────────────────────

class TestAppendMessage:
    """Interview topic: Redis session state, message cap, TTL refresh."""

    @pytest.mark.asyncio
    async def test_appends_to_existing_session(self):
        existing = json.dumps({"messages": [{"role": "user", "content": "hi"}]})
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=existing)
        mock_redis.setex = AsyncMock()

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            await append_message("session-1", "assistant", "Hello!")

        # Verify setex was called with updated session
        call_args = mock_redis.setex.call_args
        saved_data = json.loads(call_args[0][2])
        assert len(saved_data["messages"]) == 2
        assert saved_data["messages"][1]["role"] == "assistant"
        assert saved_data["messages"][1]["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_creates_session_if_not_exists(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            await append_message("new-session", "user", "first message")

        call_args = mock_redis.setex.call_args
        saved_data = json.loads(call_args[0][2])
        assert len(saved_data["messages"]) == 1

    @pytest.mark.asyncio
    async def test_caps_at_20_messages(self):
        existing_msgs = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        existing = json.dumps({"messages": existing_msgs})
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=existing)
        mock_redis.setex = AsyncMock()

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            await append_message("session-1", "user", "message 21")

        call_args = mock_redis.setex.call_args
        saved_data = json.loads(call_args[0][2])
        # Should still be 20 (capped), with oldest dropped
        assert len(saved_data["messages"]) == 20
        assert saved_data["messages"][-1]["content"] == "message 21"
        assert saved_data["messages"][0]["content"] == "msg 1"  # msg 0 was dropped

    @pytest.mark.asyncio
    async def test_ttl_refreshed_on_append(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({"messages": []}))
        mock_redis.setex = AsyncMock()

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            await append_message("session-1", "user", "hello")

        # Verify TTL = 7200 seconds (2 hours)
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 7200

    @pytest.mark.asyncio
    async def test_timestamp_added_to_message(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({"messages": []}))
        mock_redis.setex = AsyncMock()

        with patch("app.services.chat_service.get_redis", return_value=mock_redis):
            await append_message("session-1", "user", "hello")

        call_args = mock_redis.setex.call_args
        saved_data = json.loads(call_args[0][2])
        assert "timestamp" in saved_data["messages"][0]


# ─── PostgreSQL Persistence ──────────────────────────────────

class TestPersistMessage:
    """Interview topic: dual-write (Redis hot + Postgres cold), fire-and-forget,
    the 3 observability columns (LatencyMs, Model, RetrievedProductIds)."""

    def test_persists_with_observability_columns(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("db-session-uuid",)

        with patch("app.services.chat_service.get_pg_connection", return_value=mock_conn):
            persist_message(
                session_id="session-1",
                role="assistant",
                content="Here are your options...",
                retrieved_product_ids=["FRE-0042", "FRE-0105"],
                latency_ms=1340.5,
                model="llama3.1:8b",
            )

        # Verify two INSERTs: session upsert + message insert
        assert mock_cursor.execute.call_count == 3  # session upsert, session select, message insert
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        # Verify the message INSERT contains the observability columns
        message_insert_call = mock_cursor.execute.call_args_list[2]
        sql = message_insert_call[0][0]
        params = message_insert_call[0][1]
        assert '"LatencyMs"' in sql
        assert '"Model"' in sql
        assert '"RetrievedProductIds"' in sql
        assert 1340.5 in params
        assert "llama3.1:8b" in params

    def test_persists_user_message_without_observability(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("db-session-uuid",)

        with patch("app.services.chat_service.get_pg_connection", return_value=mock_conn):
            persist_message(
                session_id="session-1",
                role="user",
                content="What organic fruit is on sale?",
            )

        mock_conn.commit.assert_called_once()

    def test_handles_db_failure_gracefully(self):
        """Fire-and-forget: DB failure should not crash the chat endpoint."""
        with patch("app.services.chat_service.get_pg_connection", side_effect=Exception("DB down")):
            # Should NOT raise — logs warning and continues
            persist_message("session-1", "user", "hello")

    def test_session_upsert_on_conflict(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("existing-session-uuid",)

        with patch("app.services.chat_service.get_pg_connection", return_value=mock_conn):
            persist_message("session-1", "user", "hello")

        # First execute should be the ON CONFLICT upsert
        first_sql = mock_cursor.execute.call_args_list[0][0][0]
        assert "ON CONFLICT" in first_sql
        assert '"SessionToken"' in first_sql
