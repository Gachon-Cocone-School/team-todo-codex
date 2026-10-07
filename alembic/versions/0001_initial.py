"""Create Todo and tag tables."""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial schema."""
    op.create_table(
        "todos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee", sa.String(length=100), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH')", name="ck_todos_priority"
        ),
        sa.CheckConstraint(
            "status IN ('TODO', 'IN_PROGRESS', 'DONE')", name="ck_todos_status"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_todos_assignee", "todos", ["assignee"])
    op.create_index("ix_todos_due_date", "todos", ["due_date"])
    op.create_index("ix_todos_priority", "todos", ["priority"])
    op.create_index("ix_todos_status_created_at", "todos", ["status", "created_at"])
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_tags_name_nocase",
        "tags",
        [sa.text("name COLLATE NOCASE")],
        unique=True,
    )
    op.create_table(
        "todo_tags",
        sa.Column("todo_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["todo_id"], ["todos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("todo_id", "tag_id"),
    )
    op.create_index("ix_todo_tags_tag_id_todo_id", "todo_tags", ["tag_id", "todo_id"])


def downgrade() -> None:
    """Drop the initial schema."""
    op.drop_index("ix_todo_tags_tag_id_todo_id", table_name="todo_tags")
    op.drop_table("todo_tags")
    op.drop_index("uq_tags_name_nocase", table_name="tags")
    op.drop_table("tags")
    op.drop_index("ix_todos_status_created_at", table_name="todos")
    op.drop_index("ix_todos_priority", table_name="todos")
    op.drop_index("ix_todos_due_date", table_name="todos")
    op.drop_index("ix_todos_assignee", table_name="todos")
    op.drop_table("todos")
