"""Todo API behavior tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.todo import Tag
from app.schemas.todo import TodoCreate
from app.services.todos import create_todo, get_todo


def create(client, **values):
    """Create a Todo and return its response.

    Returns:
        The API response for the created Todo.

    """
    payload = {"title": "회의 자료 준비", **values}
    return client.post("/api/v1/todos", json=payload)


def test_create_defaults_and_read(client):
    response = create(client)
    assert response.status_code == 201
    todo = response.json()
    assert todo["title"] == "회의 자료 준비"
    assert todo["priority"] == "MEDIUM"
    assert todo["status"] == "TODO"
    assert todo["tags"] == []
    assert todo["description"] is None
    assert todo["assignee"] is None
    assert todo["due_date"] is None
    assert todo["created_at"].endswith("Z")
    assert client.get(f"/api/v1/todos/{todo['id']}").json() == todo


def test_create_fields_and_normalize_reusable_tags(client):
    response = create(
        client,
        title=" 출시 점검 ",
        description="배포 전 확인",
        assignee="민지",
        due_date="2026-10-15",
        priority="HIGH",
        status="IN_PROGRESS",
        tags=[" 출시 ", "검토", "출시"],
    )
    assert response.status_code == 201
    todo = response.json()
    assert todo["title"] == "출시 점검"
    assert todo["tags"] == ["출시", "검토"]
    second = create(client, tags=["출시"])
    assert second.status_code == 201
    assert second.json()["tags"] == ["출시"]


def test_list_filter_sort_and_pagination(client):
    first = create(
        client, status="DONE", assignee="민지", priority="HIGH", tags=["출시"]
    )
    second = create(
        client, status="TODO", assignee="민지", priority="HIGH", tags=["다른"]
    )
    third = create(client, status="DONE", assignee="준", due_date="2026-10-15")
    todos = client.get("/api/v1/todos").json()
    assert len(todos["items"]) == 3
    assert [item["id"] for item in todos["items"]] == sorted(
        [first.json()["id"], second.json()["id"], third.json()["id"]], reverse=True
    )
    assert (
        client.get("/api/v1/todos?status=DONE").json()["items"][0]["status"] == "DONE"
    )
    filtered = client.get("/api/v1/todos?assignee=%EB%AF%BC%EC%A7%80&priority=HIGH")
    assert len(filtered.json()["items"]) == 2
    assert len(client.get("/api/v1/todos?tag=%EC%B6%9C%EC%8B%9C").json()["items"]) == 1
    page = client.get("/api/v1/todos?limit=1&offset=1").json()
    assert page["limit"] == 1
    assert page["offset"] == 1
    assert len(page["items"]) == 1


def test_due_date_range_is_inclusive(client):
    create(client, due_date="2026-10-01")
    create(client, due_date="2026-10-31")
    create(client, due_date="2026-11-01")
    create(client)
    response = client.get(
        "/api/v1/todos?due_date_from=2026-10-01&due_date_to=2026-10-31"
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_patch_preserves_omitted_fields_clears_nullable_and_updates_timestamp(client):
    created = create(client, assignee="민지", tags=["기획"], description="설명").json()
    updated = client.patch(
        f"/api/v1/todos/{created['id']}",
        json={"status": "DONE", "description": None, "assignee": None, "tags": []},
    )
    assert updated.status_code == 200
    todo = updated.json()
    assert todo["status"] == "DONE"
    assert todo["title"] == created["title"]
    assert todo["tags"] == []
    assert todo["description"] is None
    assert todo["assignee"] is None
    assert datetime.fromisoformat(
        todo["updated_at"].replace("Z", "+00:00")
    ) > datetime.fromisoformat(created["updated_at"].replace("Z", "+00:00"))


def test_delete_removes_todo(client):
    todo = create(client, tags=["기획"]).json()
    response = client.delete(f"/api/v1/todos/{todo['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/v1/todos/{todo['id']}").status_code == 404


def test_invalid_inputs_return_422(client):
    assert client.post("/api/v1/todos", json={"title": "   "}).status_code == 422
    assert client.post("/api/v1/todos", json={"title": "x" * 201}).status_code == 422
    assert (
        client.post(
            "/api/v1/todos", json={"title": "x", "status": "BLOCKED"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/todos", json={"title": "x", "due_date": "15-10-2026"}
        ).status_code
        == 422
    )
    assert (
        client.post("/api/v1/todos", json={"title": "x", "tags": [" "]}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/todos", json={"title": "x", "priority": "URGENT"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/todos", json={"title": "x", "tags": ["t" * 51]}
        ).status_code
        == 422
    )
    assert client.get("/api/v1/todos?limit=101&offset=-1").status_code == 422
    assert (
        client.get(
            "/api/v1/todos?due_date_from=2026-10-31&due_date_to=2026-10-01"
        ).status_code
        == 422
    )
    assert client.post("/api/v1/todos", content='{"title":').status_code == 422


def test_empty_patch_and_missing_ids(client):
    assert client.patch("/api/v1/todos/99", json={}).status_code == 422
    assert client.get("/api/v1/todos/99").status_code == 404
    assert client.patch("/api/v1/todos/99", json={"status": "DONE"}).status_code == 404
    assert client.delete("/api/v1/todos/99").status_code == 404


def test_openapi_exposes_api_paths_and_enums(client):
    schema = client.get("/openapi.json").json()
    assert "/api/v1/todos" in schema["paths"]
    assert "/api/v1/todos/{todo_id}" in schema["paths"]
    assert "Priority" in schema["components"]["schemas"]
    assert "Status" in schema["components"]["schemas"]


@pytest.mark.parametrize(
    ("query", "expected_count"),
    [
        ("tag=launch", 1),
        ("tag=LAUNCH", 1),
        ("status=IN_PROGRESS&priority=HIGH", 1),
    ],
)
def test_list_supports_combined_and_case_insensitive_tag_filters(
    client, query, expected_count
):
    create(client, status="IN_PROGRESS", priority="HIGH", tags=["Launch"])
    create(client, status="TODO", priority="LOW", tags=["unrelated"])
    response = client.get(f"/api/v1/todos?{query}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == expected_count


def test_todo_persists_after_database_reopen(tmp_path):
    database_path = tmp_path / "persistent.db"
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    with Session(engine) as database:
        created = create_todo(database, TodoCreate(title="저장 확인", tags=["검증"]))
        todo_id = created.id
    engine.dispose()

    reopened_engine = create_engine(database_url)
    with Session(reopened_engine) as database:
        persisted = get_todo(database, todo_id)
        assert persisted is not None
        assert persisted.title == "저장 확인"
        assert [tag.name for tag in persisted.tags] == ["검증"]
    reopened_engine.dispose()


def test_concurrent_creates_reuse_same_tag(tmp_path):
    database_path = tmp_path / "concurrent.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        connection.execute("PRAGMA journal_mode=WAL")

    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def create(index):
        with session_local() as database:
            return create_todo(
                database,
                TodoCreate(title=f"동시 생성 {index}", tags=["공유 태그"]),
            ).id

    with ThreadPoolExecutor(max_workers=20) as executor:
        ids = list(executor.map(create, range(40)))

    assert len(set(ids)) == 40
    with Session(engine) as database:
        tag_count = database.query(Tag).filter(Tag.name == "공유 태그").count()
        assert tag_count == 1
    engine.dispose()
