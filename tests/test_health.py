"""Server liveness and API docs, with optional integrations left blank."""

from app.config import settings


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_optional_integrations_are_blank_and_startup_still_works(client):
    assert settings.slack_webhook_url == ""
    assert settings.ngrok_authtoken == ""
    assert settings.public_base_url == ""
    assert (await client.get("/health")).status_code == 200


async def test_docs_and_openapi_describe_the_heartbeat_route(client):
    assert (await client.get("/docs")).status_code == 200
    assert (await client.get("/redoc")).status_code == 200
    spec = (await client.get("/openapi.json")).json()
    assert "/inbound/heartbeat/" in spec["paths"]
    post = spec["paths"]["/inbound/heartbeat/"]["post"]
    assert "201" in post["responses"]
    example = spec["components"]["schemas"]["Heartbeat"]["example"]
    assert example["device_id"] == "ns-fin-01"
    assert example["department_id"] == "dept-northstar-finance"
    assert example["organisation_id"] == "org-northstar"


async def test_tunnel_route_without_a_tunnel(client):
    response = await client.get("/tunnel/")
    assert response.status_code == 200
    body = response.json()
    assert body["public_base_url"] is None
    assert body["providers"] == {"cloudflared": None, "ngrok": None}
