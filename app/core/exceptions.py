"""
Custom exception hierarchy for the Financial Advisor Chatbot.

Centralizing exceptions allows:
- Consistent error handling across layers
- Meaningful error messages for users vs. logs
- Easy mapping to HTTP status codes if we add a REST API later
"""

from __future__ import annotations


class ChatbotError(Exception):
    """Base exception for all chatbot errors."""

    def __init__(self, message: str, *, user_message: str | None = None) -> None:
        super().__init__(message)
        # user_message is safe to display; technical 'message' goes to logs only
        self.user_message = user_message or "An unexpected error occurred. Please try again."


class APIError(ChatbotError):
    """Raised when the Gemini API call fails after retries."""

    def __init__(self, message: str, *, user_message: str | None = None) -> None:
        super().__init__(
            message,
            user_message=user_message or "I'm having trouble connecting to my knowledge base. Please try again in a moment.",
        )


class RateLimitError(ChatbotError):
    """Raised when the user exceeds the rate limit."""

    def __init__(self) -> None:
        super().__init__(
            "Rate limit exceeded",
            user_message="You're sending messages too quickly. Please wait a moment before trying again.",
        )


class PromptInjectionError(ChatbotError):
    """Raised when a prompt injection attempt is detected."""

    def __init__(self) -> None:
        super().__init__(
            "Prompt injection attempt detected",
            user_message="I can only help with financial topics. Please rephrase your question.",
        )


class ConfigurationError(ChatbotError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            user_message="The application is not configured correctly. Please contact support.",
        )


class MemoryError(ChatbotError):
    """Raised when conversation memory operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            user_message="I had trouble recalling our conversation. Could you repeat your question?",
        )
