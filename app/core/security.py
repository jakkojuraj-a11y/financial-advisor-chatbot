"""
Security module — input sanitization, prompt injection defense, rate limiting.

Critical for the financial domain where:
- Prompt injection could make the bot give specific investment advice
- Unsanitized input could break prompt templates
- Uncontrolled API usage could lead to cost overruns
"""

from __future__ import annotations

import re
import time
from collections import defaultdict

from app.core.config import get_settings
from app.core.exceptions import PromptInjectionError, RateLimitError
from app.core.logger import get_logger

logger = get_logger("security")

# ── Prompt Injection Patterns ───────────────────────────────────
# These patterns detect attempts to override the system prompt
INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"pretend\s+(you('re|are)\s+)", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*:", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"override\s+(your\s+)?(rules|instructions|prompt)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|your\s+instructions)", re.IGNORECASE),
    re.compile(r"disregard\s+(all|your|the)\s+", re.IGNORECASE),
    re.compile(r"\[SYSTEM\]", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
]


def sanitize_input(user_input: str) -> str:
    """
    Sanitize user input before it enters the prompt pipeline.

    Steps:
    1. Strip leading/trailing whitespace
    2. Remove control characters
    3. Limit length to prevent token abuse
    4. Check for prompt injection patterns

    Args:
        user_input: Raw user input from the UI

    Returns:
        Sanitized input string

    Raises:
        PromptInjectionError: If injection pattern detected
    """
    if not user_input or not user_input.strip():
        return ""

    # Strip whitespace
    cleaned = user_input.strip()

    # Remove control characters (keep newlines and tabs)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

    # Limit input length (prevent token bombing)
    max_length = 2000
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
        logger.warning("input_truncated", original_length=len(user_input), max_length=max_length)

    # Check for prompt injection
    for pattern in INJECTION_PATTERNS:
        if pattern.search(cleaned):
            logger.warning(
                "prompt_injection_detected",
                pattern=pattern.pattern,
                input_preview=cleaned[:50],
            )
            raise PromptInjectionError()

    return cleaned


# ── Rate Limiter ────────────────────────────────────────────────

class RateLimiter:
    """
    Simple in-memory sliding window rate limiter.

    Tracks timestamps of requests per session and enforces the configured
    max_requests_per_minute limit.

    For production at scale, replace with Redis-based rate limiting.
    """

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._settings = get_settings()

    def check_rate_limit(self, session_id: str) -> None:
        """
        Check if the session has exceeded the rate limit.

        Args:
            session_id: Unique session identifier

        Raises:
            RateLimitError: If rate limit exceeded
        """
        now = time.time()
        window = 60.0  # 1 minute window

        # Clean old entries
        self._requests[session_id] = [
            ts for ts in self._requests[session_id]
            if now - ts < window
        ]

        if len(self._requests[session_id]) >= self._settings.max_requests_per_minute:
            logger.warning(
                "rate_limit_exceeded",
                session_id=session_id,
                count=len(self._requests[session_id]),
            )
            raise RateLimitError()

        # Record this request
        self._requests[session_id].append(now)

    def reset(self, session_id: str) -> None:
        """Clear rate limit history for a session."""
        self._requests.pop(session_id, None)


# Singleton rate limiter instance
rate_limiter = RateLimiter()
