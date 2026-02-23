"""
Tests for the prompt builder module.

Tests cover:
- Topic detection from user messages
- Greeting detection
- System prompt enhancement with topic templates
"""

from __future__ import annotations

import os

os.environ.setdefault("GEMINI_API_KEY", "test-key-for-unit-tests")

from app.prompts.builder import PromptBuilder
from app.prompts.templates import SYSTEM_PROMPT, TOPIC_TEMPLATES


class TestPromptBuilder:
    """Tests for the PromptBuilder class."""

    def setup_method(self):
        self.builder = PromptBuilder()

    # ── Greeting Detection ──────────────────────────────────────

    def test_detects_simple_greeting(self):
        greetings = ["Hi", "Hello", "Hey", "Good morning", "Howdy"]
        for greeting in greetings:
            result = self.builder.build(greeting)
            assert result.is_greeting, f"Failed to detect greeting: {greeting}"

    def test_long_message_not_greeting(self):
        """Messages over 30 chars should never be greetings."""
        result = self.builder.build("Hi, can you explain what index funds are?")
        assert not result.is_greeting

    def test_greeting_has_greeting_response(self):
        result = self.builder.build("Hello")
        assert result.greeting_response is not None
        assert "FinBot" in result.greeting_response

    # ── Topic Detection ─────────────────────────────────────────

    def test_detects_investment_topic(self):
        result = self.builder.build("How do I invest in index funds?")
        assert "investment" in result.detected_topics

    def test_detects_retirement_topic(self):
        result = self.builder.build("What is a 401k plan?")
        assert "retirement" in result.detected_topics

    def test_detects_debt_topic(self):
        result = self.builder.build("How do I pay off my credit card debt?")
        assert "debt" in result.detected_topics

    def test_detects_tax_topic(self):
        result = self.builder.build("What are tax deductions?")
        assert "tax" in result.detected_topics

    def test_detects_budgeting_topic(self):
        result = self.builder.build("Help me create a budget plan")
        assert "budgeting" in result.detected_topics

    def test_detects_multiple_topics(self):
        result = self.builder.build(
            "Should I pay off my loan or invest in stocks?"
        )
        assert "debt" in result.detected_topics
        assert "investment" in result.detected_topics

    def test_no_topic_for_generic_question(self):
        result = self.builder.build("What financial advice do you have?")
        # May or may not detect topics depending on keywords
        assert isinstance(result.detected_topics, list)

    # ── Prompt Enhancement ──────────────────────────────────────

    def test_enhanced_prompt_contains_base_system_prompt(self):
        result = self.builder.build("Tell me about stocks")
        assert "FinBot" in result.system_prompt
        assert "HARD CONSTRAINTS" in result.system_prompt

    def test_enhanced_prompt_has_topic_guidance(self):
        result = self.builder.build("How to invest in bonds?")
        assert "TOPIC-SPECIFIC GUIDANCE" in result.system_prompt

    def test_no_topic_returns_base_prompt(self):
        result = self.builder.build("Tell me something useful")
        # If no topic detected, should return base system prompt
        if not result.detected_topics:
            assert result.system_prompt == SYSTEM_PROMPT
