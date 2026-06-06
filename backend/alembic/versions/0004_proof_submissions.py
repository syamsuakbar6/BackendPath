"""Add user proof submissions.

Revision ID: 0004_proof_submissions
Revises: 0003_child_content_slugs
Create Date: 2026-06-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "0004_proof_submissions"
down_revision: Union[str, None] = "0003_child_content_slugs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "user_proof_submissions" not in tables:
        op.create_table(
            "user_proof_submissions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("lesson_id", sa.Integer(), nullable=False),
            sa.Column("proof_type", sa.String(length=32), nullable=False),
            sa.Column("question_id", sa.Integer(), nullable=True),
            sa.Column("debug_task_id", sa.Integer(), nullable=True),
            sa.Column("mini_task_id", sa.Integer(), nullable=True),
            sa.Column("answer_text", sa.Text(), nullable=True),
            sa.Column("code_text", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("score_label", sa.String(length=32), nullable=True),
            sa.Column("score_numeric", sa.Float(), nullable=True),
            sa.Column("feedback_json", sa.JSON(), nullable=True),
            sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["debug_task_id"], ["debug_tasks.id"]),
            sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
            sa.ForeignKeyConstraint(["mini_task_id"], ["mini_tasks.id"]),
            sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    review_columns = {
        column["name"] for column in inspector.get_columns("review_items")
    }
    for column_name in ("debug_task_id", "mini_task_id", "proof_submission_id"):
        if column_name not in review_columns:
            op.add_column("review_items", sa.Column(column_name, sa.Integer(), nullable=True))


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    review_columns = {
        column["name"] for column in inspector.get_columns("review_items")
    }
    for column_name in ("proof_submission_id", "mini_task_id", "debug_task_id"):
        if column_name in review_columns:
            op.drop_column("review_items", column_name)

    if "user_proof_submissions" in set(inspector.get_table_names()):
        op.drop_table("user_proof_submissions")
