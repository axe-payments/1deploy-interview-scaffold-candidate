"""The heartbeat route: accepts the contract, rejects malformed input, touches nothing."""

import logging

import pytest

from app import inbound
from app.models import Department, Device, Organisation

EXAMPLE = {
    "organisation_id": "org-northstar",
    "department_id": "dept-northstar-finance",
    "device_id": "ns-fin-01",
    "sent_at": "2026-09-17T09:00:00Z",
    "last_upload_at": "2026-09-17T08:59:55Z",
}


@pytest.fixture
def orm_spy(monkeypatch):
    """Count every read/write entry point on the inventory models."""
    calls: list[str] = []
    for model in (Organisation, Department, Device):
        for name in ("get", "get_or_none", "filter", "exists", "all", "create", "bulk_create"):
            original = getattr(model, name)

            def wrapped(*args, _name=f"{model.__name__}.{name}", _orig=original, **kwargs):
                calls.append(_name)
                return _orig(*args, **kwargs)

            monkeypatch.setattr(model, name, wrapped)
    return calls


@pytest.fixture
def notify_spy(monkeypatch):
    calls: list = []

    async def record(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr("app.notifications.notify", record)
    return calls


async def test_example_payload_is_received_and_logged(client, caplog):
    caplog.set_level(logging.INFO, logger="app.inbound")
    response = await client.post("/inbound/heartbeat/", json=EXAMPLE)
    assert response.status_code == 201
    assert response.json() == {"status": "received"}
    record = next(r for r in caplog.records if r.name == "app.inbound")
    assert record.device_id == "ns-fin-01"
    assert record.department_id == "dept-northstar-finance"
    assert record.organisation_id == "org-northstar"
    assert record.sent_at == "2026-09-17T09:00:00+00:00"
    assert record.last_upload_at == "2026-09-17T08:59:55+00:00"
    assert record.received_at.endswith("+00:00")


@pytest.mark.parametrize(
    "payload",
    [
        {**EXAMPLE, "last_upload_at": None},
        {k: v for k, v in EXAMPLE.items() if k != "last_upload_at"},
        {
            **EXAMPLE,
            "sent_at": "2026-09-17T14:30:00+05:30",
            "last_upload_at": "2026-09-17T14:29:00-03:00",
        },
        {**EXAMPLE, "sent_at": "1999-01-01T00:00:00Z", "last_upload_at": "1998-12-31T23:00:00Z"},
        {**EXAMPLE, "sent_at": "2099-12-31T23:59:59Z", "last_upload_at": None},
        {**EXAMPLE, "sent_at": "2026-09-17 09:00:00+00:00"},
    ],
    ids=[
        "null-upload",
        "omitted-upload",
        "numeric-offsets",
        "far-past",
        "far-future",
        "space-separator",
    ],
)
async def test_variants_the_contract_accepts(client, payload):
    response = await client.post("/inbound/heartbeat/", json=payload)
    assert response.status_code == 201, response.text


async def test_unknown_ids_are_received_without_any_lookup(client, orm_spy, notify_spy):
    payload = {
        **EXAMPLE,
        "organisation_id": "org-unknown",
        "department_id": "dept-x",
        "device_id": "ghost",
    }
    response = await client.post("/inbound/heartbeat/", json=payload)
    assert response.status_code == 201
    assert orm_spy == [], "the initial handler must not query the inventory"
    assert notify_spy == []
    assert await Device.all().count() == 12


async def test_known_ids_write_nothing_and_notify_nobody(client, orm_spy, notify_spy, slack_spy):
    for _ in range(3):
        assert (await client.post("/inbound/heartbeat/", json=EXAMPLE)).status_code == 201
    assert orm_spy == []
    assert notify_spy == []
    assert slack_spy == []
    assert (
        await Organisation.all().count(),
        await Department.all().count(),
        await Device.all().count(),
    ) == (2, 4, 12)


@pytest.mark.parametrize(
    "payload",
    [
        {k: v for k, v in EXAMPLE.items() if k != "organisation_id"},
        {k: v for k, v in EXAMPLE.items() if k != "department_id"},
        {k: v for k, v in EXAMPLE.items() if k != "device_id"},
        {k: v for k, v in EXAMPLE.items() if k != "sent_at"},
        {**EXAMPLE, "device_id": ""},
        {**EXAMPLE, "device_id": 7},
        {**EXAMPLE, "sent_at": "2026-09-17T09:00:00"},
        {**EXAMPLE, "last_upload_at": "2026-09-17T08:59:55"},
        {**EXAMPLE, "sent_at": "not a date"},
        {**EXAMPLE, "sent_at": "2026-13-45T09:00:00Z"},
        {**EXAMPLE, "sent_at": 0},
        {**EXAMPLE, "sent_at": 1700000000.5},
        {**EXAMPLE, "sent_at": "0"},
        {**EXAMPLE, "sent_at": "1700000000.5"},
        {**EXAMPLE, "last_upload_at": 0},
        {**EXAMPLE, "last_upload_at": "1700000000"},
        {**EXAMPLE, "sent_at": None},
        {**EXAMPLE, "sent_at": {"iso": "2026-09-17T09:00:00Z"}},
    ],
    ids=[
        "missing-org", "missing-dept", "missing-device", "missing-sent_at", "empty-device",
        "int-device", "naive-sent_at", "naive-upload", "garbage-date", "impossible-date",
        "int-sent_at", "float-sent_at", "numeric-string-sent_at", "numeric-float-string-sent_at",
        "int-upload", "numeric-string-upload", "null-sent_at", "object-sent_at",
    ],
)  # fmt: skip
async def test_malformed_payloads_fail_validation(client, payload, orm_spy):
    response = await client.post("/inbound/heartbeat/", json=payload)
    assert response.status_code == 422, response.text
    assert orm_spy == []


def test_the_route_is_the_visible_handler():
    """Guard against a solved engine hiding behind a short handler."""
    route = next(r for r in inbound.router.routes if r.path == "/inbound/heartbeat/")
    assert route.endpoint is inbound.inbound_heartbeat
    assert route.status_code == 201
