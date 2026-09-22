"""The heartbeat entry point: POST /inbound/heartbeat/  <-- START HERE.

This is the function you will change. Right now it validates the payload, logs it, and
returns 201. A 201 here means "the HTTP request was received", nothing more.

Devices send a heartbeat every few seconds while they are online. See TASK.md.
"""

import logging
import re
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter
from pydantic import AwareDatetime, BaseModel, BeforeValidator, Field

LOG = logging.getLogger("app.inbound")

router = APIRouter()

# Pydantic would otherwise also accept integers, floats and numeric strings ("0",
# "1700000000.5") as Unix timestamps. The contract wants ISO 8601 strings with a timezone.
_ISO_DATETIME_SHAPE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]")


def _require_iso_datetime_string(value: Any) -> Any:
    if isinstance(value, str) and _ISO_DATETIME_SHAPE.match(value):
        return value
    raise ValueError(
        "must be an ISO 8601 date-time string with a timezone, e.g. 2026-09-17T09:00:00Z"
    )


# Timezone-aware ISO 8601 timestamp: "Z" and numeric offsets are accepted; naive values,
# non-strings and malformed dates are rejected with a 422.
IsoAwareDatetime = Annotated[AwareDatetime, BeforeValidator(_require_iso_datetime_string)]


class Heartbeat(BaseModel):
    organisation_id: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    sent_at: IsoAwareDatetime
    # Optional: when the device last uploaded data. Both `null` and omitting it are fine.
    last_upload_at: IsoAwareDatetime | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "organisation_id": "org-northstar",
                "department_id": "dept-northstar-finance",
                "device_id": "ns-fin-01",
                "sent_at": "2026-09-17T09:00:00Z",
                "last_upload_at": "2026-09-17T08:59:55Z",
            }
        },
    }


@router.post(
    "/inbound/heartbeat/",
    status_code=201,
    tags=["Heartbeat intake (entry point)"],
    summary="Receive a device heartbeat (the ENTRY POINT)",
)
async def inbound_heartbeat(heartbeat: Heartbeat) -> dict:
    """Devices POST here every few seconds while online. Currently: log and acknowledge."""
    received_at = datetime.now(UTC)
    LOG.info(
        "Heartbeat received",
        extra={
            "organisation_id": heartbeat.organisation_id,
            "department_id": heartbeat.department_id,
            "device_id": heartbeat.device_id,
            "sent_at": heartbeat.sent_at.isoformat(),
            "last_upload_at": (
                heartbeat.last_upload_at.isoformat() if heartbeat.last_upload_at else None
            ),
            "received_at": received_at.isoformat(),
        },
    )
    return {"status": "received"}
