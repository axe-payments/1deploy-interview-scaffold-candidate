"""docker-compose.yml wiring: the app and Postgres always see the same credentials.

Runs `docker compose config` when Docker is available; skipped otherwise.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def compose_config(env_file: Path, extra_env: dict[str, str]) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("POSTGRES_")}
    env.update(extra_env)
    result = subprocess.run(
        ["docker", "compose", "--env-file", str(env_file), "config", "--format", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    if result.returncode != 0:
        pytest.skip(f"docker compose config unavailable: {result.stderr.strip()[:200]}")
    return json.loads(result.stdout)


@pytest.fixture
def env_file(tmp_path):
    path = tmp_path / "env.test"
    path.write_text(
        "APP_PORT=8000\nPOSTGRES_DB=filedb\nPOSTGRES_USER=fileuser\n"
        "POSTGRES_PASSWORD=synthetic-file-password\nSLACK_WEBHOOK_URL=\nNGROK_AUTHTOKEN=\n"
    )
    return path


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")
@pytest.mark.parametrize(
    "shell_env",
    [
        {},
        {
            "POSTGRES_PASSWORD": "synthetic-shell-password",
            "POSTGRES_USER": "shelluser",
            "POSTGRES_DB": "shelldb",
        },
    ],
    ids=["file-only", "shell-overrides-file"],
)
def test_app_and_postgres_receive_identical_credentials(env_file, shell_env):
    config = compose_config(env_file, shell_env)
    services = config["services"]
    app_env = services["app"]["environment"]
    pg_env = services["postgres"]["environment"]
    for key in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"):
        assert app_env[key] == pg_env[key], key
    expected = shell_env or {
        "POSTGRES_PASSWORD": "synthetic-file-password",
        "POSTGRES_USER": "fileuser",
        "POSTGRES_DB": "filedb",
    }
    for key, value in expected.items():
        assert pg_env[key] == value
    assert "ports" not in services["postgres"]
    assert services["app"]["ports"][0]["host_ip"] == "127.0.0.1"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")
def test_blank_optional_settings_and_absent_profiles_still_configure(env_file):
    config = compose_config(env_file, {})
    assert set(config["services"]) == {"app", "postgres", "adminer"}  # profiles off by default
