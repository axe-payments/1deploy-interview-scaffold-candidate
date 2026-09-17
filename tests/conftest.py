"""Test wiring.

The real app (lifespan, schema generation, seeding, routes) is booted for each test that
asks for `client`, against a fresh SQLite file. Optional integrations are forced blank in
the process environment BEFORE the app is imported, so a filled-in env.local on disk can
never leak into a test run (process environment beats the env file in pydantic-settings).
No test ever sends to Slack: the HTTP transport is replaced with a fake.
"""

import os
import tempfile
from pathlib import Path

# Must happen before `app.config` is imported anywhere.
_SCRATCH = Path(tempfile.mkdtemp(prefix="scaffold-tests-"))
os.environ["DATABASE_URL"] = f"sqlite://{_SCRATCH / 'bootstrap.db'}"
os.environ["SLACK_WEBHOOK_URL"] = ""
os.environ["NGROK_AUTHTOKEN"] = ""
os.environ["PUBLIC_BASE_URL"] = ""

import httpx  # noqa: E402
import pytest  # noqa: E402
from asgi_lifespan import LifespanManager  # noqa: E402

from app import notifications  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def fresh_db(tmp_path):
    """Point the app at a brand-new SQLite database for this test."""
    settings.database_url = f"sqlite://{tmp_path / 'test.db'}"
    yield settings.database_url


@pytest.fixture
async def booted(fresh_db):
    """The real app through its lifespan (schema + seed). Yields the app."""
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(booted):
    transport = httpx.ASGITransport(app=booted)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def slack_transport(monkeypatch):
    """Route `_send_slack_message` through a fake transport; records requests it saw."""
    seen: list[httpx.Request] = []
    behaviour: dict = {"status": 200, "raise": None}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if behaviour["raise"] is not None:
            raise behaviour["raise"]
        return httpx.Response(behaviour["status"], text="ok")

    def fake_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(notifications, "_build_client", fake_client)
    return {"seen": seen, "behaviour": behaviour}


@pytest.fixture
def slack_spy(monkeypatch):
    """Replace the transport helper with a recorder, to prove nothing calls it implicitly."""
    calls: list[str] = []

    async def record(message: str) -> None:
        calls.append(message)

    monkeypatch.setattr(notifications, "_send_slack_message", record)
    return calls
