"""Command-line behavior tests using an in-memory HTTP transport."""

import json

import httpx
import pytest
from typer.testing import CliRunner

from app import cli

runner = CliRunner()
TODO = {
    "id": 1,
    "title": "Task",
    "description": None,
    "assignee": None,
    "due_date": None,
    "priority": "MEDIUM",
    "status": "TODO",
    "tags": [],
    "created_at": "2026-10-07T00:00:00Z",
    "updated_at": "2026-10-07T00:00:00Z",
}


@pytest.fixture
def requests(monkeypatch):
    captured = []
    responses = []

    def handler(request):
        captured.append(request)
        if responses:
            return responses.pop(0)
        if request.method == "DELETE":
            return httpx.Response(204)
        if request.method == "GET" and request.url.path.endswith("/todos"):
            return httpx.Response(200, json={"items": [TODO], "limit": 50, "offset": 0})
        return httpx.Response(200 if request.method != "POST" else 201, json=TODO)

    def make_client(base_url):
        return httpx.Client(base_url=base_url, transport=httpx.MockTransport(handler))

    monkeypatch.setattr(cli, "_make_client", make_client)
    return captured, responses


def test_root_and_command_help_are_plain_english():
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    for command in ("create", "list", "get", "update", "delete"):
        assert command in result.output
    assert "Manage your team's to-do list" in result.output
    for command in ("create", "list", "get", "update", "delete"):
        help_result = runner.invoke(cli.app, [command, "--help"])
        assert help_result.exit_code == 0
        assert "Example:" in help_result.output
        assert "endpoint" not in help_result.output.lower()


def test_create_maps_all_fields_and_formats_text(requests):
    captured, _ = requests
    result = runner.invoke(
        cli.app,
        [
            "create",
            "--title",
            "Task",
            "--description",
            "Info",
            "--assignee",
            "Alex",
            "--due-date",
            "2026-10-15",
            "--priority",
            "HIGH",
            "--status",
            "IN_PROGRESS",
            "--tag",
            "launch",
            "--tag",
            "review",
        ],
    )
    assert result.exit_code == 0
    assert captured[0].method == "POST"
    assert captured[0].url.path == "/api/v1/todos"
    assert json.loads(captured[0].content) == {
        "title": "Task",
        "description": "Info",
        "assignee": "Alex",
        "due_date": "2026-10-15",
        "priority": "HIGH",
        "status": "IN_PROGRESS",
        "tags": ["launch", "review"],
    }
    assert "Task" in result.output


def test_list_maps_each_filter_and_defaults(requests):
    captured, _ = requests
    result = runner.invoke(
        cli.app,
        [
            "list",
            "--status",
            "DONE",
            "--assignee",
            "Alex",
            "--priority",
            "HIGH",
            "--due-date-from",
            "2026-10-01",
            "--due-date-to",
            "2026-10-31",
            "--tag",
            "launch",
            "--limit",
            "2",
            "--offset",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert dict(captured[0].url.params) == {
        "status": "DONE",
        "assignee": "Alex",
        "priority": "HIGH",
        "due_date_from": "2026-10-01",
        "due_date_to": "2026-10-31",
        "tag": "launch",
        "limit": "2",
        "offset": "1",
    }

    runner.invoke(cli.app, ["list"])
    assert dict(captured[1].url.params) == {"limit": "50", "offset": "0"}


@pytest.mark.parametrize(
    ("option", "value", "parameter"),
    [
        ("--status", "DONE", "status"),
        ("--assignee", "Alex", "assignee"),
        ("--priority", "HIGH", "priority"),
        ("--due-date-from", "2026-10-01", "due_date_from"),
        ("--due-date-to", "2026-10-31", "due_date_to"),
        ("--tag", "launch", "tag"),
        ("--limit", "2", "limit"),
        ("--offset", "1", "offset"),
    ],
)
def test_list_filter_options_map_independently(requests, option, value, parameter):
    captured, _ = requests
    result = runner.invoke(cli.app, ["list", option, value])
    assert result.exit_code == 0
    assert dict(captured[0].url.params)[parameter] == value


@pytest.mark.parametrize(
    ("args", "method", "path", "body"),
    [
        (["get", "1"], "GET", "/api/v1/todos/1", None),
        (
            ["update", "1", "--status", "DONE"],
            "PATCH",
            "/api/v1/todos/1",
            {"status": "DONE"},
        ),
        (
            [
                "update",
                "1",
                "--clear-description",
                "--clear-assignee",
                "--clear-due-date",
                "--clear-tags",
            ],
            "PATCH",
            "/api/v1/todos/1",
            {"description": None, "assignee": None, "due_date": None, "tags": []},
        ),
        (
            ["update", "1", "--tag", "new"],
            "PATCH",
            "/api/v1/todos/1",
            {"tags": ["new"]},
        ),
        (["delete", "1"], "DELETE", "/api/v1/todos/1", None),
    ],
)
def test_resource_commands_map_requests(requests, args, method, path, body):
    captured, _ = requests
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 0
    request = captured[0]
    assert (request.method, request.url.path) == (method, path)
    if body is not None:
        assert json.loads(request.content) == body


def test_base_url_precedence_and_json_outputs(requests, monkeypatch):
    captured, _ = requests
    monkeypatch.setenv("TEAM_TODO_BASE_URL", "http://env.example/")
    result = runner.invoke(
        cli.app, ["--base-url", "http://cli.example/", "--json", "list"]
    )
    assert result.exit_code == 0
    assert captured[-1].url == httpx.URL(
        "http://cli.example/api/v1/todos?limit=50&offset=0"
    )
    assert json.loads(result.stdout)["items"] == [TODO]

    result = runner.invoke(cli.app, ["--json", "delete", "1"])
    assert result.exit_code == 0
    assert not result.stdout


@pytest.mark.parametrize(
    "args",
    [
        ["create"],
        ["update", "1"],
        ["update", "1", "--assignee", "Alex", "--clear-assignee"],
        ["update", "1", "--tag", "x", "--clear-tags"],
        ["get", "0"],
        ["list", "--priority", "URGENT"],
        ["list", "--due-date-from", "15-10-2026"],
        ["list", "--limit", "101"],
        ["list", "--offset", "-1"],
    ],
)
def test_invalid_input_fails_before_request(requests, args):
    captured, _ = requests
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 2
    assert captured == []


@pytest.mark.parametrize("status_code", [404, 409, 422, 500])
def test_api_error_uses_exit_one_and_stderr(requests, status_code):
    captured, responses = requests
    responses.append(httpx.Response(status_code, json={"detail": "Todo not found"}))
    result = runner.invoke(cli.app, ["--json", "get", "1"])
    assert result.exit_code == 1
    assert not result.stdout
    assert str(status_code) in result.stderr
    assert "Todo not found" in result.stderr
    assert captured


def test_environment_base_url_and_network_failure(requests, monkeypatch):
    captured, _ = requests
    monkeypatch.setenv("TEAM_TODO_BASE_URL", "http://env.example/")
    assert runner.invoke(cli.app, ["list"]).exit_code == 0
    assert str(captured[0].url).startswith("http://env.example/")

    def fail(request):
        message = "offline"
        raise httpx.ConnectError(message, request=request)

    monkeypatch.setattr(
        cli,
        "_make_client",
        lambda base_url: httpx.Client(
            base_url=base_url, transport=httpx.MockTransport(fail)
        ),
    )
    result = runner.invoke(cli.app, ["--base-url", "http://offline.example", "list"])
    assert result.exit_code == 1
    assert "http://offline.example" in result.stderr
    assert "Traceback" not in result.output


@pytest.mark.parametrize(
    "base_url",
    ["/relative", "ftp://todo.example", "http://todo.example/openapi.json"],
)
def test_invalid_base_url_fails_before_request(requests, base_url):
    captured, _ = requests
    result = runner.invoke(cli.app, ["--base-url", base_url, "list"])
    assert result.exit_code == 2
    assert captured == []
