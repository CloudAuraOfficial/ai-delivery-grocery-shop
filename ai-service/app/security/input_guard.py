"""Input validation and prompt-injection defense for the chat endpoint."""

import re

MAX_INPUT_CHARS = 1000

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)", re.I),
    re.compile(r"forget\s+(everything|all|your\s+(instructions|prompt|rules))", re.I),
    re.compile(r"(reveal|show|print|output|repeat|tell\s+me)\s+(your\s+)?(system\s+(prompt|instructions?|message)|initial\s+prompt|hidden\s+instructions?)", re.I),
    re.compile(r"you\s+are\s+(now|going\s+to\s+be)\s+(a|an|in)\s+", re.I),
    re.compile(r"act\s+(as|like)\s+(a|an)\s+(?!shopping|grocery|customer)", re.I),
    re.compile(r"developer\s+mode|jailbreak|DAN\s+mode|do\s+anything\s+now", re.I),
    re.compile(r"<\|(im_start|im_end|system|endoftext)\|>", re.I),
]

REJECTION_MESSAGE = (
    "I'm a grocery shopping assistant. I can help you find products, current deals, "
    "and store information. What would you like to shop for today?"
)


class InputGuardResult:
    __slots__ = ("ok", "reason", "cleaned")

    def __init__(self, ok: bool, reason: str = "", cleaned: str = ""):
        self.ok = ok
        self.reason = reason
        self.cleaned = cleaned


def check(message: str) -> InputGuardResult:
    """Validate a user message. Returns ok=False with a reason if blocked."""
    if not isinstance(message, str):
        return InputGuardResult(False, "non_string")

    stripped = message.strip()
    if not stripped:
        return InputGuardResult(False, "empty")

    if len(stripped) > MAX_INPUT_CHARS:
        return InputGuardResult(False, "too_long")

    for pat in INJECTION_PATTERNS:
        if pat.search(stripped):
            return InputGuardResult(False, "injection_pattern")

    return InputGuardResult(True, "", stripped)
