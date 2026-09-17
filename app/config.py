"""Application settings, read from the environment and from `env.local`.

Precedence: real environment variables first, then `env.local` (copied from `env.example`).
Nothing here is hard-coded for an integration: the Slack webhook, the tunnel token and the
public URL are all optional and blank by default. The database password is the only value
you must set locally (Compose refuses to start Postgres without it).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="env.local", env_file_encoding="utf-8", extra="ignore"
    )

    app_port: int = 8000
    log_level: str = "INFO"

    # --- Database (Postgres in Docker; the host name is the Compose service name) ---
    postgres_db: str = "interview"
    postgres_user: str = "interview"
    postgres_password: str = ""
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    # Full connection URL override. Blank normally; the test-suite points it at SQLite.
    database_url: str = ""

    # --- Optional integrations ---
    slack_webhook_url: str = ""
    ngrok_authtoken: str = ""
    public_base_url: str = ""

    # Local discovery endpoints of the optional tunnel containers (see docker-compose.yml).
    cloudflared_api_url: str = "http://cloudflared:2000/quicktunnel"
    ngrok_api_url: str = "http://ngrok:4040/api/tunnels"

    # Shared inventory fixture, seeded into the database on startup.
    fixture_path: str = "fixtures/fleet-v1.json"

    @property
    def db_url(self) -> str:
        """Tortoise ORM connection URL: `DATABASE_URL` if set, else built from POSTGRES_*."""
        if self.database_url:
            return self.database_url
        return (
            f"postgres://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
