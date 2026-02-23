"""
Gemini API Client — production-grade wrapper around the Google GenAI SDK.

Features:
- Automatic retry with exponential backoff (via tenacity)
- Structured response parsing
- Token usage tracking for cost monitoring
- Exception mapping to our custom hierarchy
- Configurable model parameters
"""

from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import Settings, get_settings
from app.core.exceptions import APIError
from app.core.logger import get_logger

logger = get_logger("gemini_client")


class GeminiClient:
    """
    Production wrapper around the Google GenAI SDK.

    Responsibilities:
    - Manages the GenAI client lifecycle
    - Applies retry logic for transient failures
    - Parses and validates API responses
    - Logs token usage for cost monitoring

    Usage:
        client = GeminiClient()
        response = client.generate("What is compound interest?", system_prompt="...")
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = genai.Client(api_key=self._settings.gemini_api_key)
        logger.info(
            "gemini_client_initialized",
            model=self._settings.gemini_model_name,
        )

    def _build_config(self) -> types.GenerateContentConfig:
        """Build generation config from application settings."""
        return types.GenerateContentConfig(
            temperature=self._settings.gemini_temperature,
            top_p=self._settings.gemini_top_p,
            max_output_tokens=self._settings.gemini_max_output_tokens,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def generate(
        self,
        user_message: str,
        *,
        system_prompt: str | None = None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Send a message to the Gemini API and return the response text.

        Args:
            user_message: The user's current message.
            system_prompt: System-level instructions for the model.
            chat_history: Previous conversation turns as
                          [{"role": "user"|"model", "content": "..."}]

        Returns:
            The model's response text.

        Raises:
            APIError: If the API call fails after retries.
        """
        try:
            # Build the contents list for the API call
            contents = self._build_contents(user_message, chat_history)

            # Build config with optional system instruction
            config = self._build_config()
            if system_prompt:
                config.system_instruction = system_prompt

            logger.info(
                "gemini_request",
                model=self._settings.gemini_model_name,
                history_turns=len(chat_history) if chat_history else 0,
            )

            response = self._client.models.generate_content(
                model=self._settings.gemini_model_name,
                contents=contents,
                config=config,
            )

            # Extract and validate response
            response_text = self._extract_response_text(response)

            # Log token usage for cost monitoring
            self._log_token_usage(response)

            return response_text

        except (ConnectionError, TimeoutError):
            # Let tenacity retry handle these
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error("gemini_api_error", error=error_msg, error_type=type(e).__name__)

            # Provide specific message for quota exhaustion
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                raise APIError(
                    f"Gemini API quota exhausted: {e}",
                    user_message=(
                        "⚠️ **API Quota Exhausted** — Your Google Gemini API free-tier "
                        "limit has been reached. Please wait a few minutes and try again, "
                        "or use a new API key from [Google AI Studio](https://aistudio.google.com/apikey)."
                    ),
                ) from e

            raise APIError(f"Gemini API call failed: {e}") from e

    def _build_contents(
        self,
        user_message: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> list[types.Content]:
        """
        Build the contents payload for the Gemini API.

        Converts our internal chat history format to Gemini's Content format.
        """
        contents: list[types.Content] = []

        # Add conversation history
        if chat_history:
            for turn in chat_history:
                contents.append(
                    types.Content(
                        role=turn["role"],
                        parts=[types.Part.from_text(text=turn["content"])],
                    )
                )

        # Add current user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )

        return contents

    def _extract_response_text(self, response: Any) -> str:
        """
        Extract text from the Gemini API response.

        Handles edge cases like empty responses or safety blocks.
        """
        if not response or not response.text:
            logger.warning("empty_response_from_gemini")
            return (
                "I apologize, but I wasn't able to generate a response. "
                "Could you please rephrase your question?"
            )

        return response.text.strip()

    def _log_token_usage(self, response: Any) -> None:
        """Log token usage for cost monitoring and optimization."""
        try:
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = response.usage_metadata
                logger.info(
                    "token_usage",
                    prompt_tokens=getattr(usage, "prompt_token_count", 0),
                    response_tokens=getattr(usage, "candidates_token_count", 0),
                    total_tokens=getattr(usage, "total_token_count", 0),
                )
        except Exception:
            # Never let logging break the response flow
            pass
