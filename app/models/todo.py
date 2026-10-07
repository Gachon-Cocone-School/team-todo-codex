"""Todo and reusable tag database models."""

from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Priority(StrEnum):
    """Supported Todo priorities."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Status(StrEnum):
    """Supported Todo states."""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


todo_tags = Table(
    "todo_tags",
    Base.metadata,
    Column("todo_id", ForeignKey("todos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_todo_tags_tag_id_todo_id", "tag_id", "todo_id"),
)


class Todo(Base):
    """A task tracked by the team."""

    __tablename__ = "todos"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH')", name="ck_todos_priority"
        ),
        CheckConstraint(
            "status IN ('TODO', 'IN_PROGRESS', 'DONE')", name="ck_todos_status"
        ),
        Index("ix_todos_status_created_at", "status", "created_at"),
        Index("ix_todos_assignee", "assignee"),
        Index("ix_todos_priority", "priority"),
        Index("ix_todos_due_date", "due_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    assignee: Mapped[str | None] = mapped_column(String(100))
    due_date: Mapped[date | None] = mapped_column(Date)
    priority: Mapped[Priority] = mapped_column(
        String(10), nullable=False, default=Priority.MEDIUM
    )
    status: Mapped[Status] = mapped_column(
        String(20), nullable=False, default=Status.TODO
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=todo_tags, back_populates="todos", lazy="selectin"
    )


class Tag(Base):
    """A reusable tag whose first stored spelling is preserved."""

    __tablename__ = "tags"
    __table_args__ = (
        Index("uq_tags_name_nocase", text("name COLLATE NOCASE"), unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    todos: Mapped[list[Todo]] = relationship(secondary=todo_tags, back_populates="tags")
