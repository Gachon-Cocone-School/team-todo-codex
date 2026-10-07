"""Todo REST endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db, serialize_sqlite_write
from app.models.todo import Priority, Status, Todo
from app.schemas.todo import TodoCreate, TodoPage, TodoRead, TodoUpdate
from app.services import todos

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])


def _todo_or_404(database: Session, todo_id: int) -> Todo:
    todo = todos.get_todo(database, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.post("", status_code=status.HTTP_201_CREATED)
def create_todo(
    payload: TodoCreate, database: Annotated[Session, Depends(get_db)]
) -> TodoRead:
    """Create a Todo."""
    with serialize_sqlite_write(database):
        try:
            return TodoRead.from_todo(todos.create_todo(database, payload))
        except IntegrityError as error:
            database.rollback()
            raise HTTPException(
                status_code=409, detail="Todo conflicts with stored data"
            ) from error


@router.get("")
def read_todos(
    database: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[Status | None, Query(alias="status")] = None,
    assignee: str | None = None,
    priority: Priority | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    tag: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TodoPage:
    """List Todos with optional filters and pagination."""
    if (
        due_date_from is not None
        and due_date_to is not None
        and due_date_from > due_date_to
    ):
        raise HTTPException(
            status_code=422, detail="due_date_from must not exceed due_date_to"
        )
    items = todos.list_todos(
        database,
        status=status_filter,
        assignee=assignee,
        priority=priority,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        tag=tag,
        limit=limit,
        offset=offset,
    )
    return TodoPage(
        items=[TodoRead.from_todo(todo) for todo in items], limit=limit, offset=offset
    )


@router.get("/{todo_id}")
def read_todo(todo_id: int, database: Annotated[Session, Depends(get_db)]) -> TodoRead:
    """Read one Todo."""
    return TodoRead.from_todo(_todo_or_404(database, todo_id))


@router.patch("/{todo_id}")
def patch_todo(
    todo_id: int,
    payload: TodoUpdate,
    database: Annotated[Session, Depends(get_db)],
) -> TodoRead:
    """Update supplied Todo fields."""
    with serialize_sqlite_write(database):
        todo = _todo_or_404(database, todo_id)
        try:
            return TodoRead.from_todo(todos.update_todo(database, todo, payload))
        except IntegrityError as error:
            database.rollback()
            raise HTTPException(
                status_code=409, detail="Todo conflicts with stored data"
            ) from error


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_todo(
    todo_id: int, database: Annotated[Session, Depends(get_db)]
) -> Response:
    """Permanently delete a Todo."""
    with serialize_sqlite_write(database):
        todos.delete_todo(database, _todo_or_404(database, todo_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
