"""Explicit Slack delivery check:  python -m app.slack_check  (or ./scripts/slack_check.sh).

Sends ONE clearly labelled test message through the same transport helper your code will
use. This is the only thing in the scaffold that sends to Slack on its own; startup, tests
and the heartbeat endpoint never do.
"""

import asyncio
import socket
import sys
from datetime import UTC, datetime

from app.config import settings
from app.log import configure_logging
from app.notifications import SlackDeliveryError, SlackNotConfigured, _send_slack_message


async def main() -> int:
    configure_logging(settings.log_level)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    message = (
        f":white_check_mark: Interview scaffold Slack check from {socket.gethostname()} at {stamp}"
    )
    try:
        await _send_slack_message(message)
    except SlackNotConfigured as exc:
        print(f"NOT CONFIGURED: {exc}", file=sys.stderr)
        return 2
    except SlackDeliveryError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    print("OK: test message delivered. Check the Slack channel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
