"""Slack transport: explicit sends work through a fake, failures are useful and redacted."""

import logging
import traceback

import httpx
import pytest

from app.config import settings
from app.log import ExtraFormatter, configure_logging
from app.notifications import (
    SlackDeliveryError,
    SlackNotConfigured,
    _send_slack_message,
    notify,
)

SENTINEL = "https://hooks.slack.com/services/SENTINEL/SECRET/VALUE"


@pytest.fixture
def real_logging(caplog):
    """Run under the app's actual logging configuration, capturing everything at DEBUG."""
    configure_logging("DEBUG")
    caplog.set_level(logging.DEBUG)
    yield caplog


@pytest.fixture
def configured():
    settings.slack_webhook_url = SENTINEL
    yield
    settings.slack_webhook_url = ""


async def test_notify_sends_placeholder_through_transport(
    slack_transport, configured, real_logging
):
    await notify("anything", ignored=True)
    assert len(slack_transport["seen"]) == 1
    request = slack_transport["seen"][0]
    assert request.method == "POST"
    assert str(request.url) == SENTINEL
    assert request.headers["content-type"].startswith("application/json")
    assert request.read() == b'{"text":"empty"}'
    assert "delivered" in _rendered(real_logging)
    assert "SENTINEL" not in _rendered(real_logging)


async def test_send_slack_message_carries_the_message(slack_transport, configured):
    await _send_slack_message("hello from a test")
    assert slack_transport["seen"][0].read() == b'{"text":"hello from a test"}'


async def test_missing_webhook_fails_only_on_explicit_use(slack_transport):
    assert settings.slack_webhook_url == ""
    with pytest.raises(SlackNotConfigured, match="SLACK_WEBHOOK_URL"):
        await _send_slack_message("x")
    assert slack_transport["seen"] == []


def _everything_about(exc: BaseException) -> str:
    return "\n".join([str(exc), repr(exc), "".join(traceback.format_exception(exc))])


def _rendered(caplog) -> str:
    """Every captured record as the app would print it, plus every attribute on it."""
    formatter = ExtraFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    return "\n".join(formatter.format(r) + " " + repr(r.__dict__) for r in caplog.records)


async def test_timeout_is_reported_by_class_without_the_url(
    slack_transport, configured, real_logging
):
    slack_transport["behaviour"]["raise"] = httpx.ReadTimeout("read timed out")
    with pytest.raises(SlackDeliveryError) as info:
        await _send_slack_message("x")
    assert "ReadTimeout" in str(info.value)
    assert info.value.__cause__ is None and info.value.__suppress_context__
    assert "SENTINEL" not in _everything_about(info.value)
    assert "SENTINEL" not in _rendered(real_logging)
    assert "request_failed" in _rendered(real_logging)


async def test_rejected_response_is_reported_by_status_without_the_url(
    slack_transport, configured, real_logging
):
    slack_transport["behaviour"]["status"] = 500
    with pytest.raises(SlackDeliveryError) as info:
        await _send_slack_message("x")
    assert "HTTP 500" in str(info.value)
    assert "SENTINEL" not in _everything_about(info.value)
    assert "SENTINEL" not in _rendered(real_logging)
    assert "rejected" in _rendered(real_logging)


async def test_connect_error_is_redacted(slack_transport, configured, real_logging):
    slack_transport["behaviour"]["raise"] = httpx.ConnectError("boom")
    with pytest.raises(SlackDeliveryError, match="ConnectError"):
        await _send_slack_message("x")
    assert "SENTINEL" not in _rendered(real_logging)


async def test_httpx_request_line_is_not_logged_at_info(slack_transport, configured, real_logging):
    """httpx logs 'HTTP Request: POST <url>' at INFO; configure_logging must silence it."""
    await _send_slack_message("x")
    assert not [r for r in real_logging.records if r.name.startswith("httpx")]
    assert "SENTINEL" not in _rendered(real_logging)
