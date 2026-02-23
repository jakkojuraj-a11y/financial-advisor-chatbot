"""
Tests for the Gemini API client module.

Uses mocking to test without real API calls.
Tests cover:
- Client initialization
- Content building
- Response extraction
- Error handling
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-key-for-unit-tests")

from app.api.gemini_client import GeminiClient
from app.core.exceptions import APIError


class TestGeminiClient:
    """Tests for the GeminiClient class."""

    @patch("app.api.gemini_client.genai.Client")
    def test_client_initializes(self, mock_client_class):
        """Test that client initializes with settings."""
        client = GeminiClient()
        mock_client_class.assert_called_once()

    @patch("app.api.gemini_client.genai.Client")
    def test_build_contents_user_only(self, mock_client_class):
        """Test content building with user message only."""
        client = GeminiClient()
        contents = client._build_contents("Hello", chat_history=None)
        assert len(contents) == 1
        assert contents[0].role == "user"

    @patch("app.api.gemini_client.genai.Client")
    def test_build_contents_with_history(self, mock_client_class):
        """Test content building with chat history."""
        client = GeminiClient()
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "model", "content": "Hello!"},
        ]
        contents = client._build_contents("Follow up", chat_history=history)
        assert len(contents) == 3  # 2 history + 1 new

    @patch("app.api.gemini_client.genai.Client")
    def test_extract_response_text(self, mock_client_class):
        """Test response text extraction."""
        client = GeminiClient()
        mock_response = MagicMock()
        mock_response.text = "  This is a response.  "
        result = client._extract_response_text(mock_response)
        assert result == "This is a response."

    @patch("app.api.gemini_client.genai.Client")
    def test_empty_response_handled(self, mock_client_class):
        """Test graceful handling of empty response."""
        client = GeminiClient()
        mock_response = MagicMock()
        mock_response.text = None
        result = client._extract_response_text(mock_response)
        assert "rephrase" in result.lower()

    @patch("app.api.gemini_client.genai.Client")
    def test_generate_success(self, mock_client_class):
        """Test successful generate call."""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance

        mock_response = MagicMock()
        mock_response.text = "Compound interest is..."
        mock_response.usage_metadata = None
        mock_instance.models.generate_content.return_value = mock_response

        client = GeminiClient()
        result = client.generate("What is compound interest?")
        assert result == "Compound interest is..."

    @patch("app.api.gemini_client.genai.Client")
    def test_generate_api_error(self, mock_client_class):
        """Test API error handling."""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.models.generate_content.side_effect = RuntimeError("API Down")

        client = GeminiClient()
        with pytest.raises(APIError):
            client.generate("Test")
