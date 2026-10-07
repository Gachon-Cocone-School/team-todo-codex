"""Environment-backed application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///./data/team_todo.db")
    database_pool_size: int = Field(default=10, ge=1)
    database_max_overflow: int = Field(default=20, ge=0)
    database_pool_timeout: float = Field(default=30, gt=0)
    sqlite_busy_timeout_ms: int = Field(default=30_000, ge=0)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings.

    Returns:
        The cached environment-backed settings.

    """
    return Settings()


def ensure_sqlite_parent(database_url: str) -> None:
    """Create the parent directory for a file-backed SQLite database."""
    prefix = "sqlite:///"
    if database_url.startswith(prefix) and database_url != "sqlite:///:memory:":
        database_path = Path(database_url.removeprefix(prefix))
        if not database_path.is_absolute():
            database_path = Path.cwd() / database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
