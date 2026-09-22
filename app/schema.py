"""Keep every table in step with its model, so a change in app/models.py just applies.

On startup, each model's definition is fingerprinted and compared with the fingerprint
recorded the last time its table was built. A table whose model changed is dropped and
recreated (its rows go; the inventory is reseeded straight afterwards). Missing tables are
created. Nothing else is touched, so a code-only save leaves your data alone.
"""

import hashlib
import json
import logging

from tortoise import Tortoise

LOG = logging.getLogger("app.schema")

FINGERPRINTS_TABLE = "_scaffold_schema"


def _fingerprint(model) -> str:
    description = Tortoise.describe_model(model, serializable=True)
    return hashlib.sha256(json.dumps(description, sort_keys=True).encode()).hexdigest()


async def sync_schema() -> list[str]:
    """Create missing tables and rebuild changed ones. Returns the rebuilt table names."""
    conn = Tortoise.get_connection("default")
    await conn.execute_script(
        f'CREATE TABLE IF NOT EXISTS "{FINGERPRINTS_TABLE}" '
        "(table_name TEXT PRIMARY KEY, fingerprint TEXT NOT NULL)"
    )
    recorded = {
        row["table_name"]: row["fingerprint"]
        for row in await conn.execute_query_dict(
            f'SELECT table_name, fingerprint FROM "{FINGERPRINTS_TABLE}"'
        )
    }
    existing = {
        row["table_name"]
        for row in await conn.execute_query_dict(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"
        )
    }

    rebuilt: list[str] = []
    current: dict[str, str] = {}
    for model in Tortoise.apps["models"].values():
        table = model._meta.db_table
        current[table] = _fingerprint(model)
        if table not in existing or table not in recorded:
            continue  # created below, or adopted as-is from a database built before this file
        if recorded[table] != current[table]:
            await conn.execute_script(f'DROP TABLE "{table}" CASCADE')
            rebuilt.append(table)

    await Tortoise.generate_schemas(safe=True)

    for table, fingerprint in current.items():
        await conn.execute_query(
            f'INSERT INTO "{FINGERPRINTS_TABLE}" (table_name, fingerprint) VALUES ($1, $2) '
            "ON CONFLICT (table_name) DO UPDATE SET fingerprint = EXCLUDED.fingerprint",
            [table, fingerprint],
        )

    for table in rebuilt:
        LOG.info(
            "Model changed: table rebuilt, its rows dropped, inventory reseeded",
            extra={"table": table},
        )
    return rebuilt
