"""Find the app's public URL when an optional tunnel container is running.

The staff simulator needs to reach this app from outside your machine, so docker-compose
offers two tunnel services (see the `tunnel` and `ngrok` profiles). Each exposes a small
local API from which the random public hostname can be read:

- cloudflared: GET http://cloudflared:2000/quicktunnel  -> {"hostname": "....trycloudflare.com"}
- ngrok:       GET http://ngrok:4040/api/tunnels        -> {"tunnels": [{"public_url": ...}]}

Set PUBLIC_BASE_URL in env.local to skip discovery entirely. GET /tunnel/ shows the result.
From the host, ./scripts/tunnel_url.sh reads the same endpoints on localhost.
"""

import logging

import httpx

from app.config import settings

LOG = logging.getLogger("app.tunnel")


async def _get_json(url: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else None
    except (httpx.HTTPError, ValueError):
        return None


async def discover_tunnels() -> dict[str, str | None]:
    """Query each tunnel provider's local API. Missing providers simply report None."""
    found: dict[str, str | None] = {"cloudflared": None, "ngrok": None}

    data = await _get_json(settings.cloudflared_api_url)
    hostname = (data or {}).get("hostname") or ""
    if hostname:
        found["cloudflared"] = f"https://{hostname}"

    data = await _get_json(settings.ngrok_api_url)
    for tunnel in (data or {}).get("tunnels", []):
        url = tunnel.get("public_url", "") if isinstance(tunnel, dict) else ""
        if url.startswith("https://"):
            found["ngrok"] = url.rstrip("/")
            break

    return found


async def public_base_url() -> str | None:
    """PUBLIC_BASE_URL if set, else the first tunnel that answers (cloudflared, then ngrok)."""
    if settings.public_base_url:
        return settings.public_base_url.rstrip("/")
    found = await discover_tunnels()
    return found["cloudflared"] or found["ngrok"]
