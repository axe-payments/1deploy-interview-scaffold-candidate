"""FastAPI application: wires routes, the database, seeding and logging together.

You should not need to change this file, but you can.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

from app.config import settings
from app.inbound import router as inbound_router
from app.log import configure_logging
from app.schema import sync_schema
from app.seed import seed_inventory
from app.tunnel import discover_tunnels, public_base_url

LOG = logging.getLogger("app.main")

DESCRIPTION = (
    "Starter application for the fleet heartbeat exercise. See **TASK.md**.\n\n"
    "`/health` reports that this server is up. It says nothing about the health of any "
    "device, and a `201` from the heartbeat endpoint only means the request was received."
)

OPENAPI_TAGS = [
    {
        "name": "Heartbeat intake (entry point)",
        "description": "Where device heartbeats arrive. Currently logs and acknowledges only.",
    },
    {"name": "Health", "description": "Liveness of this server (not fleet health)."},
    {"name": "Tunnel", "description": "Public URL discovery when a tunnel container is running."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    # sync_schema creates a table for every model in app/models.py and rebuilds any whose
    # model changed since its table was built (see app/schema.py).
    async with RegisterTortoise(
        app,
        db_url=settings.db_url,
        modules={"models": ["app.models"]},
    ):
        await sync_schema()
        summary = await seed_inventory()
        LOG.info(
            "Startup complete",
            extra={
                "organisations": sum(summary["organisations"].values()),
                "departments": sum(summary["departments"].values()),
                "devices": sum(summary["devices"].values()),
                "slack_configured": bool(settings.slack_webhook_url),
            },
        )
        url = await public_base_url()
        if url:
            LOG.info("Public URL", extra={"public_base_url": url})
        else:
            LOG.info("No public URL yet (no tunnel running, or it is still starting)")
        yield


app = FastAPI(
    title="Fleet heartbeat interview scaffold",
    version="1.0.0",
    description=DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

app.include_router(inbound_router)


@app.get("/health", tags=["Health"], summary="Liveness check for this server")
async def health() -> dict:
    """Returns ok when the HTTP server is up. Not a statement about any device."""
    return {"status": "ok"}


@app.get("/tunnel/", tags=["Tunnel"], summary="Public URL of this app, if a tunnel is running")
async def tunnel() -> dict:
    """Effective public base URL plus every tunnel provider that answered."""
    return {
        "public_base_url": await public_base_url(),
        "override": settings.public_base_url or None,
        "providers": await discover_tunnels(),
    }
