"""Alembic migration behavior tests."""

import os
import shutil
import sqlite3
import subprocess
from pathlib import Path


def test_sqlite_upgrade_records_revision_and_is_repeatable(tmp_path):
    database_path = tmp_path / "migrations.db"
    environment = os.environ.copy()
    environment["DATABASE_URL"] = f"sqlite:///{database_path}"
    alembic = shutil.which("alembic")
    assert alembic is not None
    repository = Path(__file__).resolve().parents[1]

    # The executable and arguments are fixed; no shell is involved.
    subprocess.run(
        [alembic, "upgrade", "head"],
        check=True,
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
    )
    with sqlite3.connect(database_path) as database:
        revision = database.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()
    assert revision == ("0001_initial",)

    subprocess.run(
        [alembic, "upgrade", "head"],
        check=True,
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
    )
    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT COUNT(*) FROM todos").fetchone() == (0,)
        assert database.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone() == ("0001_initial",)
