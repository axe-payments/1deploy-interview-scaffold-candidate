"""Startup seeding creates the inventory once and never clobbers local changes."""

from asgi_lifespan import LifespanManager

from app.main import app
from app.models import Department, Device, Organisation


async def counts() -> tuple[int, int, int]:
    return (
        await Organisation.all().count(),
        await Department.all().count(),
        await Device.all().count(),
    )


async def test_fresh_startup_seeds_inventory(booted):
    assert await counts() == (2, 4, 12)
    device = await Device.get(id="hb-sup-03").prefetch_related("department__organisation")
    assert device.department.id == "dept-harbour-support"
    assert device.department.organisation.id == "org-harbour"
    assert device.department.timezone == "America/New_York"


async def test_second_startup_adds_no_duplicates(fresh_db):
    async with LifespanManager(app):
        assert await counts() == (2, 4, 12)
    async with LifespanManager(app):
        assert await counts() == (2, 4, 12)


async def test_local_edits_survive_restart(fresh_db):
    async with LifespanManager(app):
        device = await Device.get(id="ns-fin-01")
        device.name = "Renamed by candidate"
        await device.save()
        await Device.create(id="extra-01", department_id="dept-northstar-finance", name="EXTRA")
        org = await Organisation.get(id="org-harbour")
        org.name = "Harbour Renamed"
        await org.save()
    async with LifespanManager(app):
        assert (await Device.get(id="ns-fin-01")).name == "Renamed by candidate"
        assert await Device.exists(id="extra-01")
        assert (await Organisation.get(id="org-harbour")).name == "Harbour Renamed"
        assert await counts() == (2, 4, 13)
