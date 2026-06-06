from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import UserRole


def enum_values(enum_cls):
    return [item.value for item in enum_cls]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=enum_values, native_enum=False),
        default=UserRole.learner,
        nullable=False,
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lesson_progress = relationship("UserLessonProgress", back_populates="user")
    question_attempts = relationship("UserQuestionAttempt", back_populates="user")
    proof_submissions = relationship(
        "UserProofSubmission",
        back_populates="user",
        foreign_keys="UserProofSubmission.user_id",
    )
    concept_mastery = relationship("UserConceptMastery", back_populates="user")
    review_items = relationship("ReviewItem", back_populates="user")
