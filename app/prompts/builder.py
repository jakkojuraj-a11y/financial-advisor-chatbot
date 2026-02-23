"""
Dynamic prompt builder — constructs the final prompt from templates and context.

Responsibilities:
- Detect topic from user input to inject relevant templates
- Build the complete system instruction
- Handle greeting/off-topic detection
- Keep prompt construction logic separate from API and UI layers
"""

from __future__ import annotations

import re

from app.core.logger import get_logger
from app.prompts.templates import (
    GREETING_RESPONSE,
    OFF_TOPIC_RESPONSE,
    SYSTEM_PROMPT,
    TOPIC_TEMPLATES,
)

logger = get_logger("prompt_builder")

# ── Topic Detection Patterns ───────────────────────────────────
TOPIC_PATTERNS: dict[str, re.Pattern] = {
    "investment": re.compile(
        r"\b(invest|stock|bond|mutual\s+fund|etf|portfolio|dividend|"
        r"index\s+fund|equity|securities|returns|capital\s+gains)\b",
        re.IGNORECASE,
    ),
    "retirement": re.compile(
        r"\b(retire|retirement|401k|401\(k\)|ira|roth|pension|"
        r"social\s+security|annuit)\b",
        re.IGNORECASE,
    ),
    "debt": re.compile(
        r"\b(debt|loan|mortgage|credit\s+card|credit\s+score|"
        r"interest\s+rate|refinanc|payoff|owe|borrow)\b",
        re.IGNORECASE,
    ),
    "tax": re.compile(
        r"\b(tax|deduction|tax\s+bracket|capital\s+gains\s+tax|"
        r"irs|w-?2|1099|filing|taxable)\b",
        re.IGNORECASE,
    ),
    "budgeting": re.compile(
        r"\b(budget|saving|emergency\s+fund|expense|income|"
        r"spend|frugal|money\s+manage|financial\s+plan)\b",
        re.IGNORECASE,
    ),
}

# Greeting patterns
GREETING_PATTERN = re.compile(
    r"^(hi|hello|hey|good\s+(morning|afternoon|evening)|"
    r"greetings|howdy|what'?s\s+up|yo|sup)\b",
    re.IGNORECASE,
)


class PromptBuilder:
    """
    Builds dynamic prompts by combining the system prompt with
    topic-specific context based on the user's message.

    Usage:
        builder = PromptBuilder()
        result = builder.build(user_message="Tell me about index funds")
        # result.system_prompt -> enhanced system prompt
        # result.is_greeting -> False
    """

    def build(self, user_message: str) -> PromptResult:
        """
        Analyze user message and build the appropriate prompt.

        Args:
            user_message: The sanitized user input.

        Returns:
            PromptResult with system_prompt and metadata.
        """
        # Check for greeting
        if self._is_greeting(user_message):
            logger.info("greeting_detected")
            return PromptResult(
                system_prompt=SYSTEM_PROMPT,
                is_greeting=True,
                greeting_response=GREETING_RESPONSE,
                detected_topics=[],
            )

        # Detect topics
        detected_topics = self._detect_topics(user_message)

        # Build enhanced system prompt
        system_prompt = self._enhance_system_prompt(detected_topics)

        logger.info("prompt_built", topics=detected_topics)

        return PromptResult(
            system_prompt=system_prompt,
            is_greeting=False,
            greeting_response=None,
            detected_topics=detected_topics,
        )

    def _is_greeting(self, message: str) -> bool:
        """Check if the message is a simple greeting."""
        cleaned = message.strip()
        # Only treat as greeting if the message is short (< 30 chars)
        # to avoid false positives like "Hi, can you explain stocks?"
        if len(cleaned) > 30:
            return False
        return bool(GREETING_PATTERN.match(cleaned))

    def _detect_topics(self, message: str) -> list[str]:
        """Detect financial topics mentioned in the user's message."""
        topics = []
        for topic_name, pattern in TOPIC_PATTERNS.items():
            if pattern.search(message):
                topics.append(topic_name)
        return topics

    def _enhance_system_prompt(self, topics: list[str]) -> str:
        """
        Enhance the base system prompt with topic-specific instructions.

        This gives the model better context without overwhelming it
        with all topic instructions on every request.
        """
        if not topics:
            return SYSTEM_PROMPT

        topic_instructions = []
        for topic in topics:
            if topic in TOPIC_TEMPLATES:
                topic_instructions.append(TOPIC_TEMPLATES[topic])

        if not topic_instructions:
            return SYSTEM_PROMPT

        enhanced = (
            f"{SYSTEM_PROMPT}\n\n"
            f"## TOPIC-SPECIFIC GUIDANCE FOR THIS RESPONSE\n"
            f"The user is asking about: {', '.join(topics)}.\n\n"
            f"{''.join(topic_instructions)}"
        )

        return enhanced


class PromptResult:
    """Result of prompt building — carries the prompt and metadata."""

    def __init__(
        self,
        system_prompt: str,
        is_greeting: bool,
        greeting_response: str | None,
        detected_topics: list[str],
    ) -> None:
        self.system_prompt = system_prompt
        self.is_greeting = is_greeting
        self.greeting_response = greeting_response
        self.detected_topics = detected_topics
