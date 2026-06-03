"""Add optional slugs for lesson child content.

Revision ID: 0003_child_content_slugs
Revises: 0002_content_lifecycle
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "0003_child_content_slugs"
down_revision: Union[str, None] = "0002_content_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    for table in ("questions", "debug_tasks", "mini_tasks"):
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "slug" not in columns:
            op.add_column(table, sa.Column("slug", sa.String(length=255), nullable=True))


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    for table in ("mini_tasks", "debug_tasks", "questions"):
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "slug" in columns:
            op.drop_column(table, "slug")
