"""
Configuration module — loads and validates all settings from environment variables.

Uses pydantic-settings for type-safe configuration with validation.
All secrets come from .env (never hardcoded).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.

    Production best practices:
    - All secrets loaded from env (never hardcoded)
    - Pydantic validates types and ranges at startup (fail-fast)
    - lru_cache ensures single Settings instance (singleton pattern)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Gemini API ──────────────────────────────────────────────
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key (required)",
    )
    gemini_model_name: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model identifier",
    )

    # ── Model Parameters ────────────────────────────────────────
    gemini_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Lower = more deterministic (important for financial advice)",
    )
    gemini_top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling threshold",
    )
    gemini_max_output_tokens: int = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum tokens in response",
    )

    # ── Application ─────────────────────────────────────────────
    app_name: str = Field(default="Financial Advisor Chatbot")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
    )
    app_debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
    )

    # ── Memory ──────────────────────────────────────────────────
    max_history_tokens: int = Field(
        default=4000,
        ge=500,
        le=100000,
        description="Max tokens to keep in conversation history",
    )
    max_history_turns: int = Field(
        default=20,
        ge=2,
        le=100,
        description="Max conversation turns before trimming",
    )

    # ── Rate Limiting ───────────────────────────────────────────
    max_requests_per_minute: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Rate limit per session to control API costs",
    )

    # ── Validators ──────────────────────────────────────────────
    @field_validator("gemini_api_key")
    @classmethod
    def api_key_must_not_be_placeholder(cls, v: str) -> str:
        if v in ("your-gemini-api-key-here", "", "CHANGE_ME"):
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Copy .env.example to .env and add your real API key."
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached Settings singleton.
    Call this instead of Settings() to avoid re-reading .env on every access.
    """
    return Settings()
