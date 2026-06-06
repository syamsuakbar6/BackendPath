from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import (
    EvaluationConfidence,
    LessonStatus,
    ProofFinalStatus,
    ProofStatus,
    ProofType,
    ScoreLabel,
    SkillStrength,
)
from app.models.user import enum_values


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)
    status: Mapped[LessonStatus] = mapped_column(
        SAEnum(LessonStatus, values_callable=enum_values, native_enum=False),
        default=LessonStatus.not_started,
        nullable=False,
    )
    reading_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quick_check_score: Mapped[float | None] = mapped_column(Float)
    explain_back_submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explain_back_score: Mapped[float | None] = mapped_column(Float)
    debug_task_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mini_task_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reflection_submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="progress")

    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),)


class UserQuestionAttempt(Base):
    __tablename__ = "user_question_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    feedback: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="question_attempts")
    question = relationship("Question", back_populates="attempts")


class UserProofSubmission(Base):
    __tablename__ = "user_proof_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)
    proof_type: Mapped[ProofType] = mapped_column(
        SAEnum(ProofType, values_callable=enum_values, native_enum=False),
        nullable=False,
    )
    question_id: Mapped[int | None] = mapped_column(ForeignKey("questions.id"))
    debug_task_id: Mapped[int | None] = mapped_column(ForeignKey("debug_tasks.id"))
    mini_task_id: Mapped[int | None] = mapped_column(ForeignKey("mini_tasks.id"))
    answer_text: Mapped[str | None] = mapped_column(Text)
    code_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProofStatus] = mapped_column(
        SAEnum(ProofStatus, values_callable=enum_values, native_enum=False),
        default=ProofStatus.submitted,
        nullable=False,
    )
    score_label: Mapped[ScoreLabel | None] = mapped_column(
        SAEnum(ScoreLabel, values_callable=enum_values, native_enum=False),
    )
    score_numeric: Mapped[float | None] = mapped_column(Float)
    feedback_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    heuristic_status: Mapped[ProofStatus | None] = mapped_column(
        SAEnum(ProofStatus, values_callable=enum_values, native_enum=False),
    )
    heuristic_score_label: Mapped[ScoreLabel | None] = mapped_column(
        SAEnum(ScoreLabel, values_callable=enum_values, native_enum=False),
    )
    heuristic_score_numeric: Mapped[float | None] = mapped_column(Float)
    heuristic_feedback_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    evaluation_confidence: Mapped[EvaluationConfidence | None] = mapped_column(
        SAEnum(EvaluationConfidence, values_callable=enum_values, native_enum=False),
    )
    final_evaluation_status: Mapped[ProofFinalStatus | None] = mapped_column(
        SAEnum(ProofFinalStatus, values_callable=enum_values, native_enum=False),
    )
    final_score_label: Mapped[ScoreLabel | None] = mapped_column(
        SAEnum(ScoreLabel, values_callable=enum_values, native_enum=False),
    )
    final_score_numeric: Mapped[float | None] = mapped_column(Float)
    final_feedback_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    overridden_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    overridden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    override_note: Mapped[str | None] = mapped_column(Text)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="proof_submissions", foreign_keys=[user_id])
    lesson = relationship("Lesson")
    question = relationship("Question")
    debug_task = relationship("DebugTask")
    mini_task = relationship("MiniTask")
    overridden_by = relationship("User", foreign_keys=[overridden_by_id])


class UserConceptMastery(Base):
    __tablename__ = "user_concept_mastery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    concept_tag_id: Mapped[int] = mapped_column(ForeignKey("concept_tags.id"), nullable=False)
    strength: Mapped[SkillStrength] = mapped_column(
        SAEnum(SkillStrength, values_callable=enum_values, native_enum=False),
        default=SkillStrength.not_started,
        nullable=False,
    )
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="concept_mastery")
    concept_tag = relationship("ConceptTag", back_populates="mastery_records")

    __table_args__ = (UniqueConstraint("user_id", "concept_tag_id", name="uq_user_concept"),)


class ReviewItem(Base):
    __tablename__ = "review_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    concept_tag_id: Mapped[int | None] = mapped_column(ForeignKey("concept_tags.id"))
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"))
    question_id: Mapped[int | None] = mapped_column(ForeignKey("questions.id"))
    debug_task_id: Mapped[int | None] = mapped_column(ForeignKey("debug_tasks.id"))
    mini_task_id: Mapped[int | None] = mapped_column(ForeignKey("mini_tasks.id"))
    proof_submission_id: Mapped[int | None] = mapped_column(ForeignKey("user_proof_submissions.id"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    due_for_review: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="review_items")
    concept_tag = relationship("ConceptTag", back_populates="review_items")
    lesson = relationship("Lesson")
    question = relationship("Question")
    debug_task = relationship("DebugTask")
    mini_task = relationship("MiniTask")
    proof_submission = relationship("UserProofSubmission")
