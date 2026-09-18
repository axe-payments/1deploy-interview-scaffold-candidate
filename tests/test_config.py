"""Settings: the database URL is built safely from any local password.

These tests build Settings without env.local and without POSTGRES_* variables, so they pass
whatever the surrounding environment (host shell or the app container) contains.
"""

import pytest
from tortoise.backends.base.config_generator import expand_db_url

from app.config import Settings


@pytest.fixture
def isolated_env(monkeypatch):
    for key in (
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "DATABASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)


def build(**values) -> Settings:
    return Settings(_env_file=None, **values)


def test_database_url_percent_encodes_credentials(isolated_env):
    settings = build(
        postgres_user="interview",
        postgres_password="dev/te st#1%25",
        postgres_host="db",
        postgres_port=5433,
        postgres_db="candidate_db",
    )
    url = settings.db_url
    assert url == "postgres://interview:dev%2Fte%20st%231%2525@db:5433/candidate_db"
    credentials = expand_db_url(url)["credentials"]
    assert credentials["user"] == "interview"
    assert credentials["password"] == "dev/te st#1%25"
    assert credentials["host"] == "db" and credentials["port"] == 5433
    assert credentials["database"] == "candidate_db"


def test_database_url_override_wins(isolated_env):
    settings = build(database_url="sqlite://:memory:", postgres_password="x")
    assert settings.db_url == "sqlite://:memory:"


def test_defaults_point_at_the_compose_service(isolated_env):
    settings = build(postgres_password="pw")
    assert settings.db_url == "postgres://interview:pw@postgres:5432/interview"
