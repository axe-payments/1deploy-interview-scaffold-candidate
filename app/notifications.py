"""Outbound notifications: `notify()` is yours to shape; `_send_slack_message()` is the transport.

`_send_slack_message(message)` posts `message` to the Slack channel configured by
SLACK_WEBHOOK_URL in env.local (the webhook fixes the channel; there is nothing else to set
up). Prove it works with `./scripts/slack_check.sh` before relying on it.

`notify(...)` is a placeholder wrapper. Decide its signature, what it says, and who calls it.
Nothing in the scaffold calls it for you.
"""

import logging
from typing import Any

import httpx

from app.config import settings

LOG = logging.getLogger("app.notifications")

SLACK_TIMEOUT_SECONDS = 10.0


class SlackNotConfigured(RuntimeError):
    """SLACK_WEBHOOK_URL is blank. Startup and tests never hit this; only explicit sends do."""


class SlackDeliveryError(RuntimeError):
    """The webhook request failed or Slack rejected it. Carries a class name or status only."""


def _build_client() -> httpx.AsyncClient:
    # Separate function so tests can swap in a fake transport without touching the send path.
    return httpx.AsyncClient(timeout=SLACK_TIMEOUT_SECONDS)


async def _send_slack_message(message: str) -> None:
    """Post one message to the configured Slack webhook. Raises on any failure.

    Errors never include the webhook URL: httpx exception strings and request objects
    contain it, so only the exception class name or the HTTP status is reported.
    """
    url = settings.slack_webhook_url.strip()
    if not url:
        raise SlackNotConfigured(
            "SLACK_WEBHOOK_URL is not set. Add it to env.local (see env.example) and restart."
        )
    try:
        async with _build_client() as client:
            response = await client.post(url, json={"text": message})
    except httpx.HTTPError as exc:
        error_class = type(exc).__name__
        LOG.error(
            "Slack delivery failed", extra={"outcome": "request_failed", "error": error_class}
        )
        raise SlackDeliveryError(f"Slack request failed ({error_class})") from None

    if not 200 <= response.status_code < 300:
        # httpx does not follow redirects, so a 3xx is not a delivery either.
        LOG.error(
            "Slack rejected the message",
            extra={"outcome": "rejected", "status": response.status_code},
        )
        raise SlackDeliveryError(
            f"Slack rejected the message (HTTP {response.status_code})"
        ) from None

    LOG.info(
        "Slack message delivered", extra={"outcome": "delivered", "status": response.status_code}
    )


async def notify(*args: Any, **kwargs: Any) -> None:
    """Placeholder notification wrapper. Change the signature, the message, and the callers."""
    await _send_slack_message(message="empty")
