"""Database models. The three inventory tables are seeded from fixtures/fleet-v1.json.

Tortoise ORM is connected in app/main.py with `generate_schemas=True`, which CREATES a table
for every model here when the app starts (and the app restarts on every save). So you can
add a model, save, and the table exists. No migration tooling.

Caveat: schema generation only creates what is missing. It does NOT alter an existing
table when you add or change a column. If you change the shape of an existing table, reset
the local database (`./scripts/reset_db.sh`, destructive) and it will be recreated + reseeded.

You may add fields to these models, add new models, or leave the database alone entirely.
"""

from tortoise import fields
from tortoise.models import Model


class Organisation(Model):
    id = fields.CharField(primary_key=True, max_length=64)
    name = fields.CharField(max_length=200)

    class Meta:
        table = "organisations"


class Department(Model):
    id = fields.CharField(primary_key=True, max_length=64)
    organisation = fields.ForeignKeyField("models.Organisation", related_name="departments")
    name = fields.CharField(max_length=200)
    timezone = fields.CharField(max_length=64)  # IANA name, e.g. "Europe/London"

    class Meta:
        table = "departments"


class Device(Model):
    """A device belongs to a department; its organisation is the department's organisation."""

    id = fields.CharField(primary_key=True, max_length=64)
    department = fields.ForeignKeyField("models.Department", related_name="devices")
    name = fields.CharField(max_length=200)

    class Meta:
        table = "devices"
