"""Add proof evaluation audit fields.

Revision ID: 0005_evaluation_audit
Revises: 0004_proof_submissions
Create Date: 2026-06-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "0005_evaluation_audit"
down_revision: Union[str, None] = "0004_proof_submissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("user_proof_submissions")}

    additions = [
        ("heuristic_status", sa.String(length=32), None),
        ("heuristic_score_label", sa.String(length=32), None),
        ("heuristic_score_numeric", sa.Float(), None),
        ("heuristic_feedback_json", sa.JSON(), None),
        ("evaluation_confidence", sa.String(length=32), None),
        ("final_evaluation_status", sa.String(length=32), None),
        ("final_score_label", sa.String(length=32), None),
        ("final_score_numeric", sa.Float(), None),
        ("final_feedback_json", sa.JSON(), None),
        ("overridden_by_id", sa.Integer(), None),
        ("overridden_at", sa.DateTime(timezone=True), None),
        ("override_note", sa.Text(), None),
    ]
    for name, column_type, server_default in additions:
        if name not in columns:
            op.add_column(
                "user_proof_submissions",
                sa.Column(name, column_type, nullable=True, server_default=server_default),
            )

    op.execute(
        """
        UPDATE user_proof_submissions
        SET
            heuristic_status = COALESCE(heuristic_status, status),
            heuristic_score_label = COALESCE(heuristic_score_label, score_label),
            heuristic_score_numeric = COALESCE(heuristic_score_numeric, score_numeric),
            heuristic_feedback_json = COALESCE(heuristic_feedback_json, feedback_json),
            evaluation_confidence = COALESCE(evaluation_confidence, 'medium'),
            final_score_label = COALESCE(final_score_label, score_label),
            final_score_numeric = COALESCE(final_score_numeric, score_numeric),
            final_feedback_json = COALESCE(final_feedback_json, feedback_json),
            final_evaluation_status = COALESCE(
                final_evaluation_status,
                CASE
                    WHEN status IN ('passed', 'strong') THEN 'accepted'
                    WHEN score_label = 'incorrect' THEN 'rejected'
                    ELSE 'needs_review'
                END
            )
        """
    )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("user_proof_submissions")}
    for name in (
        "override_note",
        "overridden_at",
        "overridden_by_id",
        "final_feedback_json",
        "final_score_numeric",
        "final_score_label",
        "final_evaluation_status",
        "evaluation_confidence",
        "heuristic_feedback_json",
        "heuristic_score_numeric",
        "heuristic_score_label",
        "heuristic_status",
    ):
        if name in columns:
            op.drop_column("user_proof_submissions", name)
