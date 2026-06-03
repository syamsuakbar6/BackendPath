"""Add content lifecycle status fields.

Revision ID: 0002_content_lifecycle
Revises: 0001_initial_schema
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "0002_content_lifecycle"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    for table in ("lessons", "questions", "debug_tasks", "mini_tasks"):
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "content_status" not in columns:
            op.add_column(
                table,
                sa.Column(
                    "content_status",
                    sa.String(length=32),
                    nullable=False,
                    server_default="published",
                ),
            )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    for table in ("mini_tasks", "debug_tasks", "questions", "lessons"):
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "content_status" in columns:
            op.drop_column(table, "content_status")
