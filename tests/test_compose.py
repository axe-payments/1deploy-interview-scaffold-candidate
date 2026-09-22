"""docker-compose.yml and the helper scripts agree with Compose about effective settings.

The Compose checks run `docker compose config` in an isolated temporary project (a copy of
docker-compose.yml plus a synthetic env.local), so they need neither this checkout's
env.local nor a running stack. They are skipped only when Docker Compose is not installed;
any configuration error is a failure.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FILE_ENV = (
    "APP_PORT=8000\nPOSTGRES_DB=filedb\nPOSTGRES_USER=fileuser\n"
    "POSTGRES_PASSWORD=synthetic-file-password\nSLACK_WEBHOOK_URL=\nNGROK_AUTHTOKEN=\n"
)
SHELL_ENV = {
    "POSTGRES_PASSWORD": "synthetic-shell-password",
    "POSTGRES_USER": "shelluser",
    "POSTGRES_DB": "shelldb",
    "APP_PORT": "8123",
}


def compose_available() -> bool:
    if shutil.which("docker") is None:
        return False
    probe = subprocess.run(
        ["docker", "compose", "version"], capture_output=True, text=True, timeout=60
    )
    return probe.returncode == 0


needs_compose = pytest.mark.skipif(not compose_available(), reason="docker compose not installed")


def clean_env(extra: dict[str, str]) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("POSTGRES_", "APP_PORT"))}
    env.update(extra)
    return env


@pytest.fixture
def project(tmp_path) -> Path:
    """An isolated copy of the Compose file with its own synthetic env.local."""
    shutil.copy(ROOT / "docker-compose.yml", tmp_path / "docker-compose.yml")
    (tmp_path / "env.local").write_text(FILE_ENV)
    (tmp_path / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "_compose.sh", tmp_path / "scripts" / "_compose.sh")
    return tmp_path


def compose_config(project: Path, shell_env: dict[str, str]) -> dict:
    result = subprocess.run(
        ["docker", "compose", "--env-file", "env.local", "config", "--format", "json"],
        cwd=project,
        capture_output=True,
        text=True,
        env=clean_env(shell_env),
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@needs_compose
@pytest.mark.parametrize("shell_env", [{}, SHELL_ENV], ids=["file-only", "shell-overrides-file"])
def test_app_adminer_and_postgres_receive_identical_credentials(project, shell_env):
    services = compose_config(project, shell_env)["services"]
    pg_env = services["postgres"]["environment"]
    for service in ("app", "adminer"):
        for key in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"):
            assert services[service]["environment"][key] == pg_env[key], (service, key)
    expected = shell_env or {
        "POSTGRES_PASSWORD": "synthetic-file-password",
        "POSTGRES_USER": "fileuser",
        "POSTGRES_DB": "filedb",
    }
    for key in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"):
        assert pg_env[key] == expected[key]
    assert "ports" not in services["postgres"]
    app_port = services["app"]["ports"][0]
    assert app_port["host_ip"] == "127.0.0.1"
    assert str(app_port["published"]) == shell_env.get("APP_PORT", "8000")


@needs_compose
def test_adminer_mounts_the_autologin_plugin(project):
    """Without the plugin in plugins-enabled/, localhost:8080 falls back to a login form."""
    adminer = compose_config(project, {})["services"]["adminer"]
    mounts = [
        m for m in adminer["volumes"] if m["target"].startswith("/var/www/html/plugins-enabled/")
    ]
    assert len(mounts) == 1
    assert mounts[0]["read_only"] is True
    source = Path(mounts[0]["source"]).resolve().relative_to(project.resolve())
    assert (ROOT / source).is_file()
    assert adminer["ports"][0]["host_ip"] == "127.0.0.1"


@needs_compose
def test_blank_optional_settings_configure_and_profiles_stay_off(project):
    assert set(compose_config(project, {})["services"]) == {
        "app",
        "postgres",
        "adminer",
        "cloudflared",
        "tunnel-url",
    }


@needs_compose
def test_missing_password_is_a_clear_configuration_error(project):
    (project / "env.local").write_text(
        FILE_ENV.replace("POSTGRES_PASSWORD=synthetic-file-password", "POSTGRES_PASSWORD=")
    )
    result = subprocess.run(
        ["docker", "compose", "--env-file", "env.local", "config"],
        cwd=project,
        capture_output=True,
        text=True,
        env=clean_env({}),
        timeout=120,
    )
    assert result.returncode != 0
    assert "Set POSTGRES_PASSWORD in env.local" in result.stderr


@pytest.mark.parametrize(
    "shell_env",
    [{}, SHELL_ENV, {"APP_PORT": "", "POSTGRES_DB": ""}],
    ids=["file-only", "shell-overrides-file", "exported-but-empty-counts-as-set"],
)
def test_helper_scripts_resolve_settings_like_compose(project, shell_env):
    """scripts/_compose.sh env_value: a variable set in the shell wins even when empty."""
    script = (
        "source scripts/_compose.sh; for k in APP_PORT POSTGRES_DB POSTGRES_USER; "
        "do printf '%s=%s\\n' $k \"$(env_value $k)\"; done"
    )
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=project,
        capture_output=True,
        text=True,
        env=clean_env(shell_env),
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    got = dict(line.split("=", 1) for line in result.stdout.strip().splitlines())
    expected = {"APP_PORT": "8000", "POSTGRES_DB": "filedb", "POSTGRES_USER": "fileuser"}
    expected.update({k: v for k, v in shell_env.items() if k in expected})
    assert got == expected


@needs_compose
def test_empty_shell_override_publishes_the_compose_default_port(project):
    (project / "env.local").write_text(FILE_ENV.replace("APP_PORT=8000", "APP_PORT=8123"))
    services = compose_config(project, {"APP_PORT": ""})["services"]
    assert str(services["app"]["ports"][0]["published"]) == "8000"
    services = compose_config(project, {})["services"]
    assert str(services["app"]["ports"][0]["published"]) == "8123"
