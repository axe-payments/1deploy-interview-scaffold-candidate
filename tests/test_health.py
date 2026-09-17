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


async def test_tunnel_route_reports_each_provider_that_answers(client, monkeypatch):
    from app import tunnel

    async def fake_get_json(url: str):
        if "quicktunnel" in url:
            return {"hostname": "abc.trycloudflare.com"}
        return {
            "tunnels": [{"public_url": "http://x.ngrok.app"}, {"public_url": "https://x.ngrok.app"}]
        }

    monkeypatch.setattr(tunnel, "_get_json", fake_get_json)
    body = (await client.get("/tunnel/")).json()
    assert body["providers"] == {
        "cloudflared": "https://abc.trycloudflare.com",
        "ngrok": "https://x.ngrok.app",
    }
    assert body["public_base_url"] == "https://abc.trycloudflare.com"


async def test_public_base_url_override_wins(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "public_base_url", "https://fixed.example/")
    body = (await client.get("/tunnel/")).json()
    assert body["public_base_url"] == "https://fixed.example"
    assert body["override"] == "https://fixed.example/"
