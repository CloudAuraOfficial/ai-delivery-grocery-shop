"""Per-IP rate limiter for cost-bound LLM endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])

CHAT_LIMIT = "30/minute"
