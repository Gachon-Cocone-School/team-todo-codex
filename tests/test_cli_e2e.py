"""End-to-end CLI tests against a local API and an isolated SQLite database."""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
UV = shutil.which("uv")


def _free_port() -> int:
    """Return a currently unused local TCP port.

    Returns:
        An unused local TCP port number.

    """
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@pytest.fixture
def api_server(tmp_path: Path) -> Iterator[str]:
    """Start a migrated API server backed by a temporary SQLite file.

    Yields:
        The base URL of the ready API server.

    """
    if UV is None:
        pytest.skip("uv is required to run the CLI package entry point")

    database_url = f"sqlite:///{(tmp_path / 'cli-e2e.db').as_posix()}"
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    migration = subprocess.run(
        [UV, "run", "--locked", "alembic", "upgrade", "head"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )
    assert migration.returncode == 0, migration.stderr

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "error",
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if server.poll() is not None:
                pytest.fail("API server exited before becoming ready")
            try:
                response = httpx.get(f"{base_url}/api/v1/todos", timeout=1)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        else:
            pytest.fail("API server did not become ready within 15 seconds")
        yield base_url
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


def _run_cli(*args: str, base_url: str) -> subprocess.CompletedProcess[str]:
    """Run the installed project command through uv.

    Returns:
        The completed CLI process, including captured output and exit code.

    """
    assert UV is not None
    return subprocess.run(
        [UV, "run", "--locked", "ttodo", "--base-url", base_url, *args],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )


def test_cli_crud_filters_json_and_api_errors(api_server: str) -> None:
    """Exercise CRUD, filters, output modes, and API errors through the CLI."""
    created = _run_cli(
        "create",
        "--title",
        "Release check",
        "--description",
        "Before shipping",
        "--assignee",
        "Mina",
        "--due-date",
        "2026-10-15",
        "--priority",
        "HIGH",
        "--tag",
        "release",
        "--tag",
        "review",
        base_url=api_server,
    )
    assert created.returncode == 0, created.stderr
    assert "Release check" in created.stdout
    assert "Traceback" not in created.stderr

    listed = _run_cli(
        "--json",
        "list",
        "--status",
        "TODO",
        "--assignee",
        "Mina",
        "--priority",
        "HIGH",
        "--due-date-from",
        "2026-10-01",
        "--due-date-to",
        "2026-10-31",
        "--tag",
        "release",
        "--limit",
        "2",
        "--offset",
        "0",
        base_url=api_server,
    )
    assert listed.returncode == 0, listed.stderr
    page = json.loads(listed.stdout)
    assert page["limit"] == 2
    assert page["offset"] == 0
    assert len(page["items"]) == 1
    todo_id = page["items"][0]["id"]

    fetched = _run_cli("--json", "get", str(todo_id), base_url=api_server)
    assert fetched.returncode == 0, fetched.stderr
    todo = json.loads(fetched.stdout)
    assert todo["title"] == "Release check"
    assert todo["tags"] == ["release", "review"]

    updated = _run_cli(
        "--json",
        "update",
        str(todo_id),
        "--status",
        "DONE",
        "--clear-assignee",
        "--tag",
        "complete",
        base_url=api_server,
    )
    assert updated.returncode == 0, updated.stderr
    updated_todo = json.loads(updated.stdout)
    assert updated_todo["status"] == "DONE"
    assert updated_todo["assignee"] is None
    assert updated_todo["tags"] == ["complete"]
    assert updated_todo["title"] == "Release check"

    removed = _run_cli("--json", "delete", str(todo_id), base_url=api_server)
    assert removed.returncode == 0, removed.stderr
    assert not removed.stdout

    missing = _run_cli("get", "999999", base_url=api_server)
    assert missing.returncode == 1
    assert "404" in missing.stderr
    assert "Traceback" not in missing.stderr


def test_cli_input_and_connection_errors(api_server: str) -> None:
    """Keep invalid input local and report connection failures without traces."""
    invalid = _run_cli(
        "create", "--title", "Invalid", "--due-date", "15-10-2026", base_url=api_server
    )
    assert invalid.returncode == 2
    assert "Traceback" not in invalid.stderr

    unavailable = _run_cli("list", base_url="http://127.0.0.1:9")
    assert unavailable.returncode == 1
    assert "Could not reach http://127.0.0.1:9" in unavailable.stderr
    assert "Traceback" not in unavailable.stderr
