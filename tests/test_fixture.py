"""The shared inventory fixture is exactly the agreed contract."""

import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.seed import FixtureError, validate_fixture

FIXTURE = Path("fixtures/fleet-v1.json")


def load() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_version_and_counts():
    data = load()
    assert data["fixture_version"] == 1
    assert len(data["organisations"]) == 2
    assert len(data["departments"]) == 4
    assert len(data["devices"]) == 12


def test_fixture_exact_ids():
    data = load()
    assert [o["id"] for o in data["organisations"]] == ["org-northstar", "org-harbour"]
    assert [d["id"] for d in data["departments"]] == [
        "dept-northstar-finance",
        "dept-northstar-support",
        "dept-harbour-finance",
        "dept-harbour-support",
    ]
    assert [d["id"] for d in data["devices"]] == [
        "ns-fin-01", "ns-fin-02", "ns-fin-03",
        "ns-sup-01", "ns-sup-02", "ns-sup-03",
        "hb-fin-01", "hb-fin-02", "hb-fin-03",
        "hb-sup-01", "hb-sup-02", "hb-sup-03",
    ]  # fmt: skip


def test_fixture_relationships_and_zones():
    data = load()
    validate_fixture(data)  # raises FixtureError on any inconsistency
    org_ids = {o["id"] for o in data["organisations"]}
    dept_ids = {d["id"] for d in data["departments"]}
    assert all(d["organisation_id"] in org_ids for d in data["departments"])
    assert all(d["department_id"] in dept_ids for d in data["devices"])
    for dept in data["departments"]:
        ZoneInfo(dept["timezone"])  # valid IANA name
    # Both organisations have a Finance and a Support department: names are not unique.
    assert sorted(d["name"] for d in data["departments"]) == [
        "Finance",
        "Finance",
        "Support",
        "Support",
    ]


def test_fixture_formatting_is_canonical():
    raw = FIXTURE.read_bytes()
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert b"\t" not in raw
    canonical = json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n"
    assert raw.decode("utf-8") == canonical


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d.update(fixture_version=2), "unsupported fixture_version"),
        (lambda d: d["devices"].append(dict(d["devices"][0])), "duplicate ids"),
        (lambda d: d["devices"][0].update(department_id="nope"), "unknown department"),
        (lambda d: d["departments"][0].update(organisation_id="nope"), "unknown organisation"),
        (lambda d: d["departments"][0].update(timezone="Mars/Olympus"), "invalid timezone"),
    ],
)
def test_validate_fixture_rejects_inconsistencies(mutate, message):
    data = load()
    mutate(data)
    with pytest.raises(FixtureError, match=message):
        validate_fixture(data)
