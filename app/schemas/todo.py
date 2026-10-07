"""Request and response schemas for Todo endpoints."""

from datetime import UTC, date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.todo import Priority, Status, Todo


def normalize_tags(tags: list[str]) -> list[str]:
    """Trim tags and remove duplicates without changing first spelling/order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        cleaned = tag.strip()
        if not cleaned:
            raise ValueError("Tags must not be blank")
        if len(cleaned) > 50:
            raise ValueError("Tags must be at most 50 characters")
        key = cleaned.casefold()
        if key not in seen:
            seen.add(key)
            normalized.append(cleaned)
    return normalized


class TodoFields(BaseModel):
    """Fields accepted when creating or updating a Todo."""

    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str | None, Field(max_length=5000)] = None
    assignee: Annotated[str | None, Field(max_length=100)] = None
    due_date: date | None = None
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    tags: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        """Trim a title and reject whitespace-only input."""
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        """Normalize tag values."""
        return normalize_tags(value)


class TodoCreate(TodoFields):
    """Todo creation payload."""


class TodoUpdate(BaseModel):
    """Partial Todo update payload."""

    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    description: Annotated[str | None, Field(max_length=5000)] = None
    assignee: Annotated[str | None, Field(max_length=100)] = None
    due_date: date | None = None
    priority: Priority | None = None
    status: Status | None = None
    tags: list[str] | None = None

    @model_validator(mode="after")
    def validate_update(self) -> "TodoUpdate":
        """Reject empty patches, null non-nullable values, and blank titles."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field in ("title", "priority", "status", "tags"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        if self.title is not None:
            self.title = self.title.strip()
            if not self.title:
                raise ValueError("Title must not be blank")
        if self.tags is not None:
            self.tags = normalize_tags(self.tags)
        return self


class TodoRead(BaseModel):
    """Todo response representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    assignee: str | None
    due_date: date | None
    priority: Priority
    status: Status
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_todo(cls, todo: Todo) -> "TodoRead":
        """Build the API form, including tag names instead of ORM objects."""
        created_at = todo.created_at
        updated_at = todo.updated_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        return cls.model_validate({
            "id": todo.id,
            "title": todo.title,
            "description": todo.description,
            "assignee": todo.assignee,
            "due_date": todo.due_date,
            "priority": todo.priority,
            "status": todo.status,
            "tags": [tag.name for tag in todo.tags],
            "created_at": created_at,
            "updated_at": updated_at,
        })


class TodoPage(BaseModel):
    """A page of Todo results."""

    items: list[TodoRead]
    limit: int
    offset: int
