"""
Structured logging configuration.

Uses structlog for JSON-formatted, context-rich logs suitable for
production log aggregation (ELK, CloudWatch, etc.).
"""

from __future__ import annotations

import logging
import sys
from functools import lru_cache

import structlog

from app.core.config import get_settings


def configure_logging() -> None:
    """
    Configure structured logging for the application.

    - Development: colored, human-readable console output
    - Production: JSON-formatted for log aggregation systems
    """
    settings = get_settings()

    # Set root logger level
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        stream=sys.stdout,
        format="%(message)s",
    )

    # Choose renderer based on environment
    if settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


@lru_cache(maxsize=1)
def get_logger(name: str = "financial_advisor") -> structlog.stdlib.BoundLogger:
    """Return a named, structured logger."""
    configure_logging()
    return structlog.get_logger(name)
