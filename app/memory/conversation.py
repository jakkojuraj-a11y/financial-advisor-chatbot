"""
Conversation memory manager — maintains multi-turn chat history.

Features:
- Token-aware history trimming
- Turn-based limits
- Structured chat history format
- Clean interface for easy swap to Redis/DB later

Design decisions:
- We estimate tokens as (character_count / 4) — a reasonable approximation
  that avoids importing a tokenizer dependency.
- Trimming removes the OLDEST turns first (FIFO), preserving recent context.
- The memory interface is designed so swapping in-memory for Redis requires
  changing only this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("memory")


@dataclass
class ChatMessage:
    """A single message in the conversation."""

    role: str  # "user" or "model"
    content: str

    def to_dict(self) -> dict[str, str]:
        """Convert to the dict format expected by GeminiClient."""
        return {"role": self.role, "content": self.content}

    def estimated_tokens(self) -> int:
        """Rough token estimate: ~4 chars per token for English text."""
        return max(1, len(self.content) // 4)


@dataclass
class ConversationMemory:
    """
    Manages conversation history for a single session.

    Tracks messages, enforces token and turn limits, and provides
    the history in the format expected by the API client.

    Usage:
        memory = ConversationMemory()
        memory.add_user_message("What is an ETF?")
        memory.add_model_message("An ETF is...")
        history = memory.get_history()  # Returns list of dicts
    """

    messages: list[ChatMessage] = field(default_factory=list)
    _max_tokens: int = field(default=0, init=False)
    _max_turns: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        settings = get_settings()
        self._max_tokens = settings.max_history_tokens
        self._max_turns = settings.max_history_turns

    def add_user_message(self, content: str) -> None:
        """Add a user message to history."""
        self.messages.append(ChatMessage(role="user", content=content))
        self._trim_if_needed()

    def add_model_message(self, content: str) -> None:
        """Add a model response to history."""
        self.messages.append(ChatMessage(role="model", content=content))
        self._trim_if_needed()

    def get_history(self) -> list[dict[str, str]]:
        """
        Return conversation history as a list of dicts.

        Only returns the most recent turns (max_turns * 2 messages)
        to minimize token usage per API call.

        Returns:
            List of {"role": "user"|"model", "content": "..."} dicts.
        """
        # Only send recent messages to the API (saves tokens on free tier)
        max_messages = self._max_turns * 2
        recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        return [msg.to_dict() for msg in recent]

    def get_display_history(self) -> list[dict[str, str]]:
        """
        Return history formatted for Streamlit display.

        Maps 'model' role to 'assistant' for Streamlit's chat_message component.
        """
        display = []
        for msg in self.messages:
            role = "assistant" if msg.role == "model" else msg.role
            display.append({"role": role, "content": msg.content})
        return display

    @property
    def total_tokens(self) -> int:
        """Estimate total tokens across all messages."""
        return sum(msg.estimated_tokens() for msg in self.messages)

    @property
    def turn_count(self) -> int:
        """Count conversation turns (each user+model pair = 1 turn)."""
        return len(self.messages) // 2

    def _trim_if_needed(self) -> None:
        """
        Trim conversation history if it exceeds limits.

        Strategy: Remove the oldest pair of messages (user + model)
        until we're back under limits. This preserves the most recent
        context which is typically most relevant.
        """
        trimmed = False

        # Trim by turn count
        while len(self.messages) > self._max_turns * 2 and len(self.messages) >= 2:
            self.messages.pop(0)
            self.messages.pop(0)
            trimmed = True

        # Trim by token count
        while self.total_tokens > self._max_tokens and len(self.messages) >= 2:
            self.messages.pop(0)
            self.messages.pop(0)
            trimmed = True

        if trimmed:
            logger.info(
                "history_trimmed",
                remaining_messages=len(self.messages),
                remaining_tokens=self.total_tokens,
            )

    def clear(self) -> None:
        """Clear all conversation history."""
        self.messages.clear()
        logger.info("history_cleared")

    def is_empty(self) -> bool:
        """Check if there is any conversation history."""
        return len(self.messages) == 0
