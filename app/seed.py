"""Seed the inventory tables from fixtures/fleet-v1.json on startup, idempotently.

Rules (deliberate, so your own data survives restarts):
- Rows are inserted parent-first only when their id is missing.
- Existing rows are never updated or deleted, even if they differ from the fixture.
- Extra rows and extra tables you add are left alone.
- Nothing is truncated or dropped here. Rows go only when a model changes (its table is
  rebuilt, see app/schema.py) or with ./scripts/reset_db.sh.
"""

import json
import logging
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import settings
from app.models import Department, Device, Organisation

LOG = logging.getLogger("app.seed")

SUPPORTED_FIXTURE_VERSION = 1


class FixtureError(ValueError):
    """The fixture file is malformed or internally inconsistent."""


def load_fixture(path: str | Path | None = None) -> dict:
    fixture_path = Path(path or settings.fixture_path)
    with fixture_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    validate_fixture(data)
    return data


def validate_fixture(data: dict) -> None:
    if data.get("fixture_version") != SUPPORTED_FIXTURE_VERSION:
        raise FixtureError(
            f"unsupported fixture_version {data.get('fixture_version')!r}; "
            f"expected {SUPPORTED_FIXTURE_VERSION}"
        )
    orgs = data.get("organisations", [])
    depts = data.get("departments", [])
    devices = data.get("devices", [])
    for label, rows in (("organisations", orgs), ("departments", depts), ("devices", devices)):
        ids = [row.get("id") for row in rows]
        if any(not isinstance(i, str) or not i for i in ids):
            raise FixtureError(f"every {label} row needs a non-empty string id")
        if len(set(ids)) != len(ids):
            raise FixtureError(f"duplicate ids in {label}")
    org_ids = {row["id"] for row in orgs}
    dept_ids = {row["id"] for row in depts}
    for dept in depts:
        if dept.get("organisation_id") not in org_ids:
            raise FixtureError(f"department {dept['id']} references unknown organisation")
        try:
            ZoneInfo(dept.get("timezone", ""))
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            raise FixtureError(f"department {dept['id']} has invalid timezone") from None
    for device in devices:
        if device.get("department_id") not in dept_ids:
            raise FixtureError(f"device {device['id']} references unknown department")


async def seed_inventory(path: str | Path | None = None) -> dict[str, dict[str, int]]:
    """Insert any missing fixture rows. Returns per-table created/existing counts."""
    data = load_fixture(path)
    summary: dict[str, dict[str, int]] = {}

    async def insert_missing(model, label: str, rows: list[dict], build: callable) -> None:
        created = existing = 0
        for row in rows:
            if await model.exists(id=row["id"]):
                existing += 1
            else:
                await model.create(**build(row))
                created += 1
        summary[label] = {"created": created, "existing": existing}

    await insert_missing(
        Organisation,
        "organisations",
        data["organisations"],
        lambda r: {"id": r["id"], "name": r["name"]},
    )
    await insert_missing(
        Department,
        "departments",
        data["departments"],
        lambda r: {
            "id": r["id"],
            "organisation_id": r["organisation_id"],
            "name": r["name"],
            "timezone": r["timezone"],
        },
    )
    await insert_missing(
        Device,
        "devices",
        data["devices"],
        lambda r: {"id": r["id"], "department_id": r["department_id"], "name": r["name"]},
    )

    LOG.info(
        "Inventory seed complete",
        extra={f"{table}_{k}": v for table, counts in summary.items() for k, v in counts.items()},
    )
    return summary
