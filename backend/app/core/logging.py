"""Structured logging configuration.

Never log secrets. This module centralises logging so that sensitive
fields can be redacted consistently.
"""
import logging
import sys
from typing import Any

LOG_REDACT_KEYS = {
    "password",
    "token",
    "access_token",
    "secret",
    "api_key",
    "authorization",
    "whatsapp_access_token",
    "sms_api_key",
    "sms_api_secret",
    "gemini_api_key",
}


def _redact(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: ("[REDACTED]" if k.lower() in LOG_REDACT_KEYS else _redact(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact(i) for i in data]
    return data


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if hasattr(record, "extra"):
            record.extra = _redact(record.extra)
        return super().format(record)


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        RedactingFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, **extra: Any) -> None:
    """Log a structured event with redaction applied."""
    logger.info(event, extra={"extra": extra})