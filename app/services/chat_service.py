"""
Chat service — the orchestrator that ties all layers together.

This is the ONLY module the UI layer talks to. It coordinates:
1. Input sanitization (security)
2. Rate limiting (security)
3. Prompt building (prompts)
4. Memory retrieval (memory)
5. API call (api)
6. Memory update (memory)

The UI never directly calls the API client or memory manager.
This ensures clean separation of concerns and testability.
"""

from __future__ import annotations

from app.api.gemini_client import GeminiClient
from app.core.exceptions import ChatbotError
from app.core.logger import get_logger
from app.core.security import rate_limiter, sanitize_input
from app.memory.conversation import ConversationMemory
from app.prompts.builder import PromptBuilder

logger = get_logger("chat_service")


class ChatService:
    """
    Orchestrates the complete chat flow.

    Usage:
        service = ChatService(
            memory=ConversationMemory(),
            session_id="unique-session-id",
        )
        response = service.process_message("What is an ETF?")
    """

    def __init__(
        self,
        memory: ConversationMemory,
        session_id: str,
        gemini_client: GeminiClient | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.memory = memory
        self.session_id = session_id
        self._client = gemini_client or GeminiClient()
        self._prompt_builder = prompt_builder or PromptBuilder()

    def process_message(self, user_input: str) -> str:
        """
        Process a user message through the complete pipeline.

        Flow:
        1. Sanitize input → 2. Rate limit check → 3. Build prompt
        → 4. Call Gemini API → 5. Update memory → 6. Return response

        Args:
            user_input: Raw user input from the UI.

        Returns:
            The chatbot's response string.

        Raises:
            ChatbotError: Any error in the pipeline (with user_message).
        """
        try:
            # Step 1: Sanitize input
            sanitized = sanitize_input(user_input)
            if not sanitized:
                return "Please enter a message so I can help you with your financial questions."

            logger.info("processing_message", session_id=self.session_id)

            # Step 2: Rate limit check
            rate_limiter.check_rate_limit(self.session_id)

            # Step 3: Build prompt
            prompt_result = self._prompt_builder.build(sanitized)

            # Handle greeting without API call
            if prompt_result.is_greeting and self.memory.is_empty():
                return prompt_result.greeting_response

            # Step 4: Get conversation history for context
            history = self.memory.get_history()

            # Step 5: Call Gemini API
            response = self._client.generate(
                user_message=sanitized,
                system_prompt=prompt_result.system_prompt,
                chat_history=history if history else None,
            )

            # Step 6: Update memory
            self.memory.add_user_message(sanitized)
            self.memory.add_model_message(response)

            logger.info(
                "message_processed",
                session_id=self.session_id,
                topics=prompt_result.detected_topics,
                history_turns=self.memory.turn_count,
            )

            return response

        except ChatbotError:
            # Re-raise our custom exceptions — they have user_message set
            raise
        except Exception as e:
            logger.error(
                "unexpected_error",
                session_id=self.session_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return (
                "I apologize, but I encountered an unexpected issue. "
                "Please try again, and if the problem persists, "
                "try starting a new conversation."
            )

    def clear_conversation(self) -> None:
        """Clear conversation history and rate limit state."""
        self.memory.clear()
        rate_limiter.reset(self.session_id)
        logger.info("conversation_cleared", session_id=self.session_id)
