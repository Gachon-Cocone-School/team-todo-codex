"""SQLAlchemy engine and request-scoped sessions."""

from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import TYPE_CHECKING

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import ensure_sqlite_parent, get_settings

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Generator, Iterator

settings = get_settings()
ensure_sqlite_parent(settings.database_url)
connect_args = (
    {
        "check_same_thread": False,
        "timeout": settings.sqlite_busy_timeout_ms / 1000,
    }
    if settings.database_url.startswith("sqlite")
    else {}
)
engine_options = {}
if not settings.database_url.startswith("sqlite") or settings.database_url not in {
    "sqlite://",
    "sqlite:///:memory:",
}:
    engine_options = {
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_timeout": settings.database_pool_timeout,
    }
engine = create_engine(
    settings.database_url, connect_args=connect_args, **engine_options
)

if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        connection: sqlite3.Connection, _record: object
    ) -> None:
        """Set SQLite connection safety and concurrency options."""
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute(f"PRAGMA busy_timeout={settings.sqlite_busy_timeout_ms}")
        cursor.close()

    if settings.database_url not in {"sqlite://", "sqlite:///:memory:"}:
        with engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
_sqlite_write_lock = Lock()


@contextmanager
def serialize_sqlite_write(database: Session) -> Iterator[None]:
    """Serialize write transactions for SQLite within this process."""
    if database.bind is not None and database.bind.dialect.name == "sqlite":
        with _sqlite_write_lock:
            yield
        return
    yield


def get_db() -> Generator[Session, None, None]:
    """Yield a session and always close it after the request.

    Yields:
        The request-scoped SQLAlchemy session.

    """
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
