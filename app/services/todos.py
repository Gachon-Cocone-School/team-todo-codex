"""Todo persistence and filtering rules."""

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.todo import Priority, Status, Tag, Todo
from app.schemas.todo import TodoCreate, TodoUpdate


def _tags_for_names(database: Session, names: list[str]) -> list[Tag]:
    """Find reusable tags case-insensitively or create missing ones."""
    tags: list[Tag] = []
    for name in names:
        tag = database.scalar(select(Tag).where(Tag.name.collate("NOCASE") == name))
        if tag is not None:
            tags.append(tag)
            continue
        if database.bind is not None and database.bind.dialect.name == "sqlite":
            database.execute(
                sqlite_insert(Tag).values(name=name).on_conflict_do_nothing()
            )
        tag = database.scalar(select(Tag).where(Tag.name.collate("NOCASE") == name))
        if tag is None:
            tag = Tag(name=name)
            database.add(tag)
            database.flush()
        tags.append(tag)
    return tags


def create_todo(database: Session, values: TodoCreate) -> Todo:
    """Create a Todo and its tag links in one transaction."""
    data = values.model_dump(exclude={"tags"})
    todo = Todo(**data, tags=_tags_for_names(database, values.tags))
    database.add(todo)
    database.commit()
    database.refresh(todo)
    return todo


def get_todo(database: Session, todo_id: int) -> Todo | None:
    """Return a Todo by ID."""
    return database.get(Todo, todo_id)


def update_todo(database: Session, todo: Todo, values: TodoUpdate) -> Todo:
    """Apply only supplied fields and commit the update atomically."""
    data = values.model_dump(exclude_unset=True)
    tags = data.pop("tags", None)
    for field, value in data.items():
        setattr(todo, field, value)
    if tags is not None:
        todo.tags = _tags_for_names(database, tags)
    todo.updated_at = datetime.now(UTC)
    database.commit()
    database.refresh(todo)
    return todo


def delete_todo(database: Session, todo: Todo) -> None:
    """Permanently delete a Todo and its association rows."""
    database.delete(todo)
    database.commit()


def list_todos(
    database: Session,
    *,
    status: Status | None,
    assignee: str | None,
    priority: Priority | None,
    due_date_from: date | None,
    due_date_to: date | None,
    tag: str | None,
    limit: int,
    offset: int,
) -> list[Todo]:
    """Select filtered Todos in stable default order."""
    query = select(Todo).distinct()
    if status is not None:
        query = query.where(Todo.status == status)
    if assignee is not None:
        query = query.where(Todo.assignee == assignee)
    if priority is not None:
        query = query.where(Todo.priority == priority)
    if due_date_from is not None:
        query = query.where(Todo.due_date >= due_date_from)
    if due_date_to is not None:
        query = query.where(Todo.due_date <= due_date_to)
    if tag is not None:
        query = query.join(Todo.tags).where(Tag.name.collate("NOCASE") == tag)
    query = query.order_by(Todo.created_at.desc(), Todo.id.desc())
    return list(database.scalars(query.limit(limit).offset(offset)).unique())
