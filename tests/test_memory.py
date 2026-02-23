"""
Tests for the conversation memory module.

Tests cover:
- Adding messages
- History retrieval
- Token-based trimming
- Turn-based trimming
- Display history formatting
"""

from __future__ import annotations

import os

os.environ.setdefault("GEMINI_API_KEY", "test-key-for-unit-tests")

from app.memory.conversation import ChatMessage, ConversationMemory


class TestChatMessage:
    """Tests for the ChatMessage dataclass."""

    def test_to_dict(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.to_dict() == {"role": "user", "content": "Hello"}

    def test_estimated_tokens(self):
        # ~4 chars per token
        msg = ChatMessage(role="user", content="a" * 100)
        assert msg.estimated_tokens() == 25

    def test_minimum_one_token(self):
        msg = ChatMessage(role="user", content="Hi")
        assert msg.estimated_tokens() >= 1


class TestConversationMemory:
    """Tests for the ConversationMemory class."""

    def test_add_messages(self):
        memory = ConversationMemory()
        memory.add_user_message("Hello")
        memory.add_model_message("Hi there!")
        assert len(memory.messages) == 2

    def test_get_history_format(self):
        memory = ConversationMemory()
        memory.add_user_message("What is an ETF?")
        memory.add_model_message("An ETF is...")

        history = memory.get_history()
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "What is an ETF?"}
        assert history[1] == {"role": "model", "content": "An ETF is..."}

    def test_display_history_remaps_model_to_assistant(self):
        memory = ConversationMemory()
        memory.add_user_message("Question")
        memory.add_model_message("Answer")

        display = memory.get_display_history()
        assert display[0]["role"] == "user"
        assert display[1]["role"] == "assistant"

    def test_turn_count(self):
        memory = ConversationMemory()
        memory.add_user_message("Q1")
        memory.add_model_message("A1")
        memory.add_user_message("Q2")
        memory.add_model_message("A2")
        assert memory.turn_count == 2

    def test_trimming_by_turns(self):
        memory = ConversationMemory()
        memory._max_turns = 2  # Allow only 2 turns (4 messages)

        # Add 3 turns
        for i in range(3):
            memory.add_user_message(f"Question {i}")
            memory.add_model_message(f"Answer {i}")

        # Should have trimmed to 2 turns (4 messages)
        assert len(memory.messages) <= 4
        # Most recent messages should be preserved
        assert memory.messages[-1].content == "Answer 2"

    def test_trimming_by_tokens(self):
        memory = ConversationMemory()
        memory._max_tokens = 50  # Very low token limit

        # Add messages that exceed token limit
        memory.add_user_message("a" * 100)  # 25 tokens
        memory.add_model_message("b" * 100)  # 25 tokens
        memory.add_user_message("c" * 100)  # 25 tokens => total exceeds 50
        memory.add_model_message("d" * 100)

        # Should have trimmed oldest messages
        assert memory.total_tokens <= 50 or len(memory.messages) <= 2

    def test_clear(self):
        memory = ConversationMemory()
        memory.add_user_message("Hello")
        memory.add_model_message("Hi")
        memory.clear()
        assert memory.is_empty()

    def test_is_empty(self):
        memory = ConversationMemory()
        assert memory.is_empty()
        memory.add_user_message("Hello")
        assert not memory.is_empty()

    def test_total_tokens(self):
        memory = ConversationMemory()
        memory.add_user_message("a" * 40)  # ~10 tokens
        memory.add_model_message("b" * 40)  # ~10 tokens
        assert memory.total_tokens == 20
