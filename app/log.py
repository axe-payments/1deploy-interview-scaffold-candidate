"""Logging setup: plain lines plus every `extra={...}` field as key=value.

Stdlib logging silently drops `extra` fields unless the format string names them, so a
formatter that appends them is what makes structured receipt logs visible in
`docker compose logs`.
"""

import logging

# Attributes every LogRecord has out of the box; anything else came from `extra={...}`.
_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class ExtraFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = {k: v for k, v in record.__dict__.items() if k not in _RESERVED}
        if extras:
            base += " " + " ".join(f"{k}={v!r}" for k, v in extras.items())
        return base


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(ExtraFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # httpx logs every request line at INFO *including the full URL*. For a Slack call that
    # URL is the secret webhook, so these two loggers stay at WARNING regardless of LOG_LEVEL.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
