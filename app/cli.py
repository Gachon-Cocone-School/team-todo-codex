"""Command-line interface for the Team Todo API."""

import json
from datetime import date
from enum import StrEnum
from typing import Annotated, Any

import httpx
import typer

API_PATH = "/api/v1/todos"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"


class Priority(StrEnum):
    """Supported task importance values."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Status(StrEnum):
    """Supported task states."""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


app = typer.Typer(
    name="ttodo",
    help="Manage your team's to-do list from the command line.",
    no_args_is_help=True,
    epilog=(
        "Examples:\n"
        '  ttodo create --title "Prepare meeting notes"\n'
        "  ttodo list\n"
        "  ttodo get 1\n"
        "  ttodo update 1 --status DONE\n"
        "  ttodo delete 1"
    ),
)


def _make_client(base_url: str) -> httpx.Client:
    """Create an HTTP client for the selected API server.

    Returns:
        A configured HTTP client.

    """
    return httpx.Client(base_url=base_url.rstrip("/"), timeout=10.0)


def _base_url(value: str | None) -> str:
    """Choose and normalize the API server address.

    Returns:
        The API server address without a trailing slash.

    """
    address = (value or DEFAULT_BASE_URL).rstrip("/")
    try:
        parsed = httpx.URL(address)
    except httpx.InvalidURL as error:
        message = "Use a server address with a host and optional port."
        raise typer.BadParameter(message) from error
    invalid_address = any((
        parsed.scheme not in {"http", "https"},
        not parsed.host,
        parsed.path not in {"", "/"},
        bool(parsed.query),
        bool(parsed.fragment),
        bool(parsed.username),
        bool(parsed.password),
    ))
    if invalid_address:
        message = "Use a server address with a host and optional port."
        raise typer.BadParameter(message)
    return str(parsed).rstrip("/")


def _parse_date(value: str) -> str:
    """Validate and normalize a YYYY-MM-DD value.

    Returns:
        The date in ISO format.

    """
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        message = "Use a day written as YYYY-MM-DD."
        raise typer.BadParameter(message) from error


def _request(
    ctx: typer.Context,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> httpx.Response | None:
    """Send one request and turn expected failures into short CLI errors.

    Returns:
        The response, or None when the server confirms deletion.

    """
    settings = ctx.obj
    base_url = settings["base_url"]
    try:
        with _make_client(base_url) as client:
            response = client.request(method, path, params=params, json=body)
    except httpx.RequestError as error:
        typer.echo(
            f"Could not reach {base_url}. Check the server address and "
            "make sure the server is running.",
            err=True,
        )
        raise typer.Exit(1) from error

    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except (ValueError, AttributeError):
            detail = response.text or response.reason_phrase
        typer.echo(f"Server returned {response.status_code}: {detail}", err=True)
        raise typer.Exit(1)
    return None if response.status_code == httpx.codes.NO_CONTENT else response


def _show(ctx: typer.Context, response: httpx.Response | None) -> None:
    """Print a response as JSON or readable text."""
    if response is None:
        if not ctx.obj["json"]:
            typer.echo("Task deleted.")
        return
    data = response.json()
    if ctx.obj["json"]:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    elif isinstance(data, dict) and "items" in data:
        if not data["items"]:
            typer.echo("No tasks found.")
            return
        typer.echo("ID  TITLE  STATUS  PRIORITY  ASSIGNEE  DUE DATE")
        for item in data["items"]:
            typer.echo(
                f"{item['id']}  {item['title']}  {item['status']}  "
                f"{item['priority']}  {item['assignee'] or '-'}  "
                f"{item['due_date'] or '-'}"
            )
    else:
        for key, value in data.items():
            label = key.replace("_", " ").capitalize()
            shown_value = value
            if isinstance(shown_value, list):
                shown_value = ", ".join(str(item) for item in shown_value) or "-"
            typer.echo(f"{label}: {shown_value if shown_value is not None else '-'}")


@app.callback()
def main(
    ctx: typer.Context,
    base_url: Annotated[
        str | None,
        typer.Option(
            "--base-url",
            envvar="TEAM_TODO_BASE_URL",
            help=f"Use a different Todo server. Default: {DEFAULT_BASE_URL}.",
        ),
    ] = None,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json", help="Print the result as JSON for use with other tools."
        ),
    ] = False,
) -> None:
    """Set options shared by all commands."""
    ctx.ensure_object(dict)
    ctx.obj.update(base_url=_base_url(base_url), json=as_json)


@app.command(
    help=(
        "Create a task to remember. Example: "
        'ttodo create --title "Prepare meeting notes"'
    )
)
def create(
    ctx: typer.Context,
    title: Annotated[
        str,
        typer.Option(
            ..., help="A short name for the task (required when creating a task)."
        ),
    ],
    description: Annotated[
        str | None, typer.Option(help="More information about the task.")
    ] = None,
    assignee: Annotated[
        str | None,
        typer.Option(help="The name of the person responsible for this task."),
    ] = None,
    due_date: Annotated[
        str | None, typer.Option(help="The day the task is due, written as YYYY-MM-DD.")
    ] = None,
    priority: Annotated[
        Priority,
        typer.Option(
            help=(
                "How important the task is: LOW, MEDIUM, or HIGH. New tasks use MEDIUM."
            )
        ),
    ] = Priority.MEDIUM,
    status: Annotated[
        Status,
        typer.Option(
            help=(
                "Where the task stands: TODO, IN_PROGRESS, or DONE. New tasks use TODO."
            )
        ),
    ] = Status.TODO,
    tag: Annotated[
        list[str] | None,
        typer.Option(
            help=(
                "A label for grouping tasks. Add this option again to use "
                "more than one label."
            )
        ),
    ] = None,
) -> None:
    """Create a task with a required title and optional details."""
    body: dict[str, Any] = {"title": title}
    body.update({
        key: value
        for key, value in (
            ("description", description),
            ("assignee", assignee),
            ("due_date", _parse_date(due_date) if due_date else None),
            ("priority", priority),
            ("status", status),
            ("tags", tag or []),
        )
        if value is not None
    })
    _show(ctx, _request(ctx, "POST", API_PATH, body=body))


@app.command(
    name="list",
    help=(
        "Show tasks. You can narrow the list by status, person, priority, due "
        "date, or tag. Example: ttodo list --status TODO"
    ),
)
def list_todos(
    ctx: typer.Context,
    status: Annotated[
        Status | None,
        typer.Option(help="Where the task stands: TODO, IN_PROGRESS, or DONE."),
    ] = None,
    assignee: Annotated[
        str | None, typer.Option(help="Show tasks assigned to this person.")
    ] = None,
    priority: Annotated[
        Priority | None,
        typer.Option(help="How important the task is: LOW, MEDIUM, or HIGH."),
    ] = None,
    due_date_from: Annotated[
        str | None,
        typer.Option(
            "--due-date-from", help="Show tasks due on or after this day (YYYY-MM-DD)."
        ),
    ] = None,
    due_date_to: Annotated[
        str | None,
        typer.Option(
            "--due-date-to", help="Show tasks due on or before this day (YYYY-MM-DD)."
        ),
    ] = None,
    tag: Annotated[str | None, typer.Option(help="Show tasks with this label.")] = None,
    limit: Annotated[
        int,
        typer.Option(
            min=1,
            max=100,
            help="The most tasks to show at once (1-100; default: 50).",
        ),
    ] = 50,
    offset: Annotated[
        int,
        typer.Option(
            min=0, help="How many tasks to skip before showing results (default: 0)."
        ),
    ] = 0,
) -> None:
    """Show tasks with optional filters and page controls."""
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    params.update({
        key: value
        for key, value in (
            ("status", status),
            ("assignee", assignee),
            ("priority", priority),
            ("due_date_from", _parse_date(due_date_from) if due_date_from else None),
            ("due_date_to", _parse_date(due_date_to) if due_date_to else None),
            ("tag", tag),
        )
        if value is not None
    })
    if (
        due_date_from
        and due_date_to
        and _parse_date(due_date_from) > _parse_date(due_date_to)
    ):
        typer.echo("The start day must be on or before the end day.", err=True)
        raise typer.Exit(2)
    _show(ctx, _request(ctx, "GET", API_PATH, params=params))


def _positive_id(value: int) -> int:
    if value < 1:
        raise typer.BadParameter("Task ID must be a positive number.")
    return value


@app.command(help="Show all details for one task. Example: ttodo get 1")
def get(
    ctx: typer.Context,
    todo_id: Annotated[
        int,
        typer.Argument(help="The number of the task to show.", callback=_positive_id),
    ],
) -> None:
    """Show one task."""
    _show(ctx, _request(ctx, "GET", f"{API_PATH}/{todo_id}"))


@app.command(
    help=(
        "Change only the details you provide. Leave out anything you want to "
        "keep as it is. Example: ttodo update 1 --status DONE"
    )
)
def update(
    ctx: typer.Context,
    todo_id: Annotated[
        int,
        typer.Argument(help="The number of the task to change.", callback=_positive_id),
    ],
    title: Annotated[
        str | None, typer.Option(help="A short name for the task.")
    ] = None,
    description: Annotated[
        str | None, typer.Option(help="More information about the task.")
    ] = None,
    assignee: Annotated[
        str | None,
        typer.Option(help="The name of the person responsible for this task."),
    ] = None,
    due_date: Annotated[
        str | None, typer.Option(help="The day the task is due, written as YYYY-MM-DD.")
    ] = None,
    priority: Annotated[
        Priority | None,
        typer.Option(help="How important the task is: LOW, MEDIUM, or HIGH."),
    ] = None,
    status: Annotated[
        Status | None,
        typer.Option(help="Where the task stands: TODO, IN_PROGRESS, or DONE."),
    ] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option(
            help="Replace all labels. Add this option again to use more than one."
        ),
    ] = None,
    clear_description: Annotated[
        bool, typer.Option(help="Remove the task description.")
    ] = False,
    clear_assignee: Annotated[
        bool, typer.Option(help="Remove the assigned person's name.")
    ] = False,
    clear_due_date: Annotated[bool, typer.Option(help="Remove the due date.")] = False,
    clear_tags: Annotated[
        bool, typer.Option(help="Remove all labels from the task.")
    ] = False,
) -> None:
    """Change only the task details you name."""
    if clear_description and description is not None:
        raise typer.BadParameter("Use --description or --clear-description, not both.")
    if clear_assignee and assignee is not None:
        raise typer.BadParameter("Use --assignee or --clear-assignee, not both.")
    if clear_due_date and due_date is not None:
        raise typer.BadParameter("Use --due-date or --clear-due-date, not both.")
    if clear_tags and tag:
        raise typer.BadParameter("Use --tag or --clear-tags, not both.")

    body: dict[str, Any] = {}
    fields = (
        ("title", title),
        ("description", None if clear_description else description),
        ("assignee", None if clear_assignee else assignee),
        (
            "due_date",
            None if clear_due_date else _parse_date(due_date) if due_date else None,
        ),
        ("priority", priority),
        ("status", status),
    )
    clear_fields = {
        "description": clear_description,
        "assignee": clear_assignee,
        "due_date": clear_due_date,
    }
    body.update({
        key: value
        for key, value in fields
        if value is not None or clear_fields.get(key)
    })
    if tag is not None:
        body["tags"] = tag
    elif clear_tags:
        body["tags"] = []
    if not body:
        typer.echo("Choose at least one task detail to change.", err=True)
        raise typer.Exit(2)
    _show(ctx, _request(ctx, "PATCH", f"{API_PATH}/{todo_id}", body=body))


@app.command(
    help="Delete a task permanently. This cannot be undone. Example: ttodo delete 1"
)
def delete(
    ctx: typer.Context,
    todo_id: Annotated[
        int,
        typer.Argument(help="The number of the task to delete.", callback=_positive_id),
    ],
) -> None:
    """Permanently delete one task without asking for confirmation."""
    _show(ctx, _request(ctx, "DELETE", f"{API_PATH}/{todo_id}"))


if __name__ == "__main__":
    app()
