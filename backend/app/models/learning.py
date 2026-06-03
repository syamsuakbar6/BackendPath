from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Column,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import BlockType, QuestionType
from app.models.user import enum_values


lesson_concept_tags = Table(
    "lesson_concept_tags",
    Base.metadata,
    Column("lesson_id", ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "concept_tag_id",
        ForeignKey("concept_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

question_concept_tags = Table(
    "question_concept_tags",
    Base.metadata,
    Column("question_id", ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "concept_tag_id",
        ForeignKey("concept_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tracks = relationship("Track", back_populates="language", cascade="all, delete-orphan")


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    language = relationship("Language", back_populates="tracks")
    levels = relationship(
        "Level",
        back_populates="track",
        cascade="all, delete-orphan",
        order_by="Level.sort_order",
    )


class Level(Base):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    track = relationship("Track", back_populates="levels")
    modules = relationship(
        "Module",
        back_populates="level",
        cascade="all, delete-orphan",
        order_by="Module.sort_order",
    )

    __table_args__ = (UniqueConstraint("track_id", "slug", name="uq_level_track_slug"),)


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level_id: Mapped[int] = mapped_column(ForeignKey("levels.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    level = relationship("Level", back_populates="modules")
    lessons = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.sort_order",
    )

    __table_args__ = (UniqueConstraint("level_id", "slug", name="uq_module_level_slug"),)


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    learning_goal: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    module = relationship("Module", back_populates="lessons")
    blocks = relationship(
        "LessonBlock",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="LessonBlock.sort_order",
    )
    questions = relationship(
        "Question",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="Question.sort_order",
    )
    mini_tasks = relationship("MiniTask", back_populates="lesson", cascade="all, delete-orphan")
    debug_tasks = relationship("DebugTask", back_populates="lesson", cascade="all, delete-orphan")
    progress = relationship("UserLessonProgress", back_populates="lesson")
    concept_tags = relationship(
        "ConceptTag", secondary=lesson_concept_tags, back_populates="lessons"
    )

    __table_args__ = (UniqueConstraint("module_id", "slug", name="uq_lesson_module_slug"),)


class LessonBlock(Base):
    __tablename__ = "lesson_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)
    block_type: Mapped[BlockType] = mapped_column(
        SAEnum(BlockType, values_callable=enum_values, native_enum=False), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    code_language: Mapped[str | None] = mapped_column(String(80))
    block_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    lesson = relationship("Lesson", back_populates="blocks")


class ConceptTag(Base):
    __tablename__ = "concept_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    lessons = relationship("Lesson", secondary=lesson_concept_tags, back_populates="concept_tags")
    questions = relationship(
        "Question", secondary=question_concept_tags, back_populates="concept_tags"
    )
    mastery_records = relationship("UserConceptMastery", back_populates="concept_tag")
    review_items = relationship("ReviewItem", back_populates="concept_tag")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"))
    question_type: Mapped[QuestionType] = mapped_column(
        SAEnum(QuestionType, values_callable=enum_values, native_enum=False), nullable=False
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(80), default="foundation", nullable=False)
    correct_answer: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    expected_concepts: Mapped[list[str] | None] = mapped_column(JSON)
    rubric: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    sample_ideal_answer: Mapped[str | None] = mapped_column(Text)
    misconception_notes: Mapped[str | None] = mapped_column(Text)
    remedial_prompt: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lesson = relationship("Lesson", back_populates="questions")
    options = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.id",
    )
    concept_tags = relationship(
        "ConceptTag", secondary=question_concept_tags, back_populates="questions"
    )
    attempts = relationship("UserQuestionAttempt", back_populates="question")


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(8), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    question = relationship("Question", back_populates="options")


class MiniTask(Base):
    __tablename__ = "mini_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)
    concept_tag_id: Mapped[int | None] = mapped_column(ForeignKey("concept_tags.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    acceptance_criteria: Mapped[list[str] | None] = mapped_column(JSON)
    difficulty: Mapped[str] = mapped_column(String(80), default="foundation", nullable=False)

    lesson = relationship("Lesson", back_populates="mini_tasks")
    concept_tag = relationship("ConceptTag")


class DebugTask(Base):
    __tablename__ = "debug_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)
    concept_tag_id: Mapped[int | None] = mapped_column(ForeignKey("concept_tags.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    broken_code: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[str | None] = mapped_column(Text)
    expected_fix_summary: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(80), default="foundation", nullable=False)

    lesson = relationship("Lesson", back_populates="debug_tasks")
    concept_tag = relationship("ConceptTag")
