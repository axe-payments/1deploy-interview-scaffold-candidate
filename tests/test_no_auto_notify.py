"""Nothing in the scaffold sends to Slack on its own: not startup, seeding, health, heartbeats."""

from app.notifications import _send_slack_message


async def test_startup_and_traffic_never_touch_slack(slack_spy, client):
    assert (await client.get("/health")).status_code == 200
    payload = {
        "organisation_id": "org-harbour",
        "department_id": "dept-harbour-finance",
        "device_id": "hb-fin-02",
        "sent_at": "2026-09-17T09:00:00Z",
    }
    for _ in range(5):
        assert (await client.post("/inbound/heartbeat/", json=payload)).status_code == 201
    assert slack_spy == []


def test_notify_is_the_only_caller_of_the_transport_in_app_code():
    """A grep-level guard: only app/notifications.py and app/slack_check.py may call it."""
    from pathlib import Path

    offenders = []
    for path in Path("app").glob("*.py"):
        if path.name in {"notifications.py", "slack_check.py"}:
            continue
        if _send_slack_message.__name__ in path.read_text(encoding="utf-8"):
            offenders.append(path.name)
    assert offenders == []
