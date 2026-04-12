"""Chat session management with Redis (active) + PostgreSQL (persistence)."""

import json
import uuid
from datetime import datetime, timezone

import structlog
import redis.asyncio as aioredis
import psycopg2

from app.config import settings

logger = structlog.get_logger()

SESSION_TTL = 7200  # 2 hours

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
        )
    return _redis


def get_pg_connection():
    return psycopg2.connect(settings.postgres_dsn)


async def get_or_create_session(session_id: str | None) -> str:
    """Get existing session or create a new one."""
    r = await get_redis()

    if session_id:
        exists = await r.exists(f"chat:{session_id}")
        if exists:
            return session_id

    # Create new session
    new_id = str(uuid.uuid4())
    session_data = json.dumps({"messages": [], "created_at": datetime.now(timezone.utc).isoformat()})
    await r.setex(f"chat:{new_id}", SESSION_TTL, session_data)
    return new_id


async def get_history(session_id: str) -> list[dict]:
    """Get conversation history from Redis."""
    r = await get_redis()
    data = await r.get(f"chat:{session_id}")
    if not data:
        return []
    session = json.loads(data)
    return session.get("messages", [])


async def append_message(session_id: str, role: str, content: str):
    """Append a message to the session history in Redis."""
    r = await get_redis()
    data = await r.get(f"chat:{session_id}")

    if data:
        session = json.loads(data)
    else:
        session = {"messages": [], "created_at": datetime.now(timezone.utc).isoformat()}

    session["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Keep last 20 messages in Redis
    session["messages"] = session["messages"][-20:]
    await r.setex(f"chat:{session_id}", SESSION_TTL, json.dumps(session))


def persist_message(
    session_id: str,
    role: str,
    content: str,
    retrieved_product_ids: list[str] | None = None,
    latency_ms: float | None = None,
    model: str | None = None,
):
    """Persist a chat message to PostgreSQL for analytics."""
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # Ensure session exists in DB
        cur.execute(
            'INSERT INTO "ChatSessions" ("Id", "SessionToken", "CreatedAt", "LastMessageAt") '
            'VALUES (%s, %s, %s, %s) '
            'ON CONFLICT ("SessionToken") DO UPDATE SET "LastMessageAt" = %s',
            (str(uuid.uuid4()), session_id, datetime.now(timezone.utc), datetime.now(timezone.utc), datetime.now(timezone.utc))
        )

        # Get session DB id
        cur.execute('SELECT "Id" FROM "ChatSessions" WHERE "SessionToken" = %s', (session_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return
        db_session_id = row[0]

        # Insert message
        cur.execute(
            'INSERT INTO "ChatMessages" ("Id", "SessionId", "Role", "Content", "RetrievedProductIds", "LatencyMs", "Model", "CreatedAt") '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
            (
                str(uuid.uuid4()), str(db_session_id), role, content,
                json.dumps(retrieved_product_ids) if retrieved_product_ids else None,
                latency_ms, model, datetime.now(timezone.utc)
            )
        )

        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("persist_message_failed", error=str(e))
