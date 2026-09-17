"""Settings: the database URL is built safely from any local password."""

from tortoise.backends.base.config_generator import expand_db_url

from app.config import Settings


def test_database_url_percent_encodes_credentials():
    settings = Settings(
        database_url="",
        postgres_user="interview",
        postgres_password="dev/te st#1%25",
        postgres_host="db",
        postgres_port=5433,
    )
    url = settings.db_url
    assert url == "postgres://interview:dev%2Fte%20st%231%2525@db:5433/interview"
    credentials = expand_db_url(url)["credentials"]
    assert credentials["user"] == "interview"
    assert credentials["password"] == "dev/te st#1%25"
    assert credentials["host"] == "db" and credentials["port"] == 5433
    assert credentials["database"] == "interview"


def test_database_url_override_wins():
    settings = Settings(database_url="sqlite://:memory:", postgres_password="x")
    assert settings.db_url == "sqlite://:memory:"


def test_defaults_point_at_the_compose_service():
    settings = Settings(database_url="", postgres_password="pw")
    assert settings.db_url == "postgres://interview:pw@postgres:5432/interview"
