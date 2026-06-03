from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ConceptTag,
    Lesson,
    LessonStatus,
    Question,
    QuestionType,
    ReviewItem,
    SkillStrength,
    User,
    UserConceptMastery,
    UserLessonProgress,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_progress(db: Session, user_id: int, lesson_id: int) -> UserLessonProgress:
    progress = db.scalar(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id,
        )
    )
    if progress:
        return progress

    progress = UserLessonProgress(
        user_id=user_id,
        lesson_id=lesson_id,
        status=LessonStatus.in_progress,
        started_at=utc_now(),
    )
    db.add(progress)
    db.flush()
    return progress


def skill_strength_from_progress(progress: UserLessonProgress | None) -> SkillStrength:
    if not progress:
        return SkillStrength.not_started
    if progress.review_required:
        return SkillStrength.weak
    if progress.mastery_score >= 0.85:
        return SkillStrength.strong
    if progress.mastery_score >= 0.6:
        return SkillStrength.stable
    if progress.mastery_score > 0:
        return SkillStrength.learning
    return SkillStrength.not_started


def recompute_progress(progress: UserLessonProgress) -> UserLessonProgress:
    mastery = 0.0
    if progress.reading_completed:
        mastery += 0.15
    if progress.quick_check_score is not None:
        mastery += min(progress.quick_check_score, 1.0) * 0.25
    if progress.explain_back_submitted:
        mastery += (progress.explain_back_score or 0.5) * 0.2
    if progress.debug_task_completed:
        mastery += 0.2
    if progress.mini_task_completed:
        mastery += 0.2

    progress.mastery_score = round(min(mastery, 1.0), 2)

    has_multiple_proofs = (
        progress.reading_completed
        and (progress.quick_check_score or 0) >= 0.7
        and progress.explain_back_submitted
    )
    has_mastery_proofs = (
        has_multiple_proofs
        and progress.debug_task_completed
        and progress.mini_task_completed
        and (progress.explain_back_score or 0) >= 0.7
    )

    now = utc_now()
    if progress.review_required:
        progress.status = LessonStatus.needs_review
    elif has_mastery_proofs and progress.mastery_score >= 0.85:
        progress.status = LessonStatus.mastered
        progress.mastered_at = progress.mastered_at or now
        progress.completed_at = progress.completed_at or now
    elif has_multiple_proofs and progress.mastery_score >= 0.6:
        progress.status = LessonStatus.completed
        progress.completed_at = progress.completed_at or now
    elif progress.mastery_score > 0:
        progress.status = LessonStatus.in_progress
    else:
        progress.status = LessonStatus.not_started

    return progress


def start_lesson(db: Session, user: User, lesson_id: int) -> UserLessonProgress:
    db.get(Lesson, lesson_id) or _raise_missing("Lesson")
    progress = get_or_create_progress(db, user.id, lesson_id)
    if progress.status == LessonStatus.not_started:
        progress.status = LessonStatus.in_progress
    user.last_activity_at = utc_now()
    db.commit()
    db.refresh(progress)
    return progress


def complete_reading(db: Session, user: User, lesson_id: int) -> UserLessonProgress:
    db.get(Lesson, lesson_id) or _raise_missing("Lesson")
    progress = get_or_create_progress(db, user.id, lesson_id)
    progress.reading_completed = True
    recompute_progress(progress)
    user.last_activity_at = utc_now()
    db.commit()
    db.refresh(progress)
    return progress


def mark_debug_task_completed(db: Session, user: User, lesson_id: int) -> UserLessonProgress:
    progress = get_or_create_progress(db, user.id, lesson_id)
    progress.debug_task_completed = True
    recompute_progress(progress)
    db.commit()
    db.refresh(progress)
    return progress


def mark_mini_task_completed(db: Session, user: User, lesson_id: int) -> UserLessonProgress:
    progress = get_or_create_progress(db, user.id, lesson_id)
    progress.mini_task_completed = True
    recompute_progress(progress)
    db.commit()
    db.refresh(progress)
    return progress


def submit_reflection(db: Session, user: User, lesson_id: int) -> UserLessonProgress:
    progress = get_or_create_progress(db, user.id, lesson_id)
    progress.reflection_submitted = True
    recompute_progress(progress)
    db.commit()
    db.refresh(progress)
    return progress


def score_text_against_concepts(answer: str, expected_concepts: list[str] | None) -> tuple[float, list[str]]:
    if not expected_concepts:
        return (0.5 if answer.strip() else 0.0), []

    normalized = answer.lower()
    matched = [
        concept
        for concept in expected_concepts
        if concept.lower().replace("-", " ") in normalized
        or concept.lower().replace("_", " ") in normalized
    ]
    score = len(matched) / len(expected_concepts)
    return round(score, 2), matched


def submit_explain_back(
    db: Session, user: User, lesson_id: int, answer: str
) -> UserLessonProgress:
    lesson = db.get(Lesson, lesson_id) or _raise_missing("Lesson")
    question = next(
        (item for item in lesson.questions if item.question_type == QuestionType.explain_back),
        None,
    )
    score, _matched = score_text_against_concepts(
        answer, question.expected_concepts if question else None
    )

    progress = get_or_create_progress(db, user.id, lesson_id)
    progress.explain_back_submitted = True
    progress.explain_back_score = score
    if score < 0.7:
        progress.review_required = True
        for tag in lesson.concept_tags:
            update_concept_mastery(db, user, tag, is_correct=False)
            schedule_review(
                db,
                user=user,
                concept_tag=tag,
                lesson=lesson,
                question=question,
                reason="Explain-back missed expected concepts.",
                is_correct=False,
            )
    recompute_progress(progress)
    db.commit()
    db.refresh(progress)
    return progress


def update_quick_check_progress(
    db: Session, user: User, question: Question, score: float, is_correct: bool
) -> UserLessonProgress | None:
    if question.lesson_id is None or question.question_type == QuestionType.explain_back:
        return None

    progress = get_or_create_progress(db, user.id, question.lesson_id)
    previous = progress.quick_check_score or 0
    progress.quick_check_score = max(previous, score)
    if not is_correct:
        progress.review_required = True
    elif score >= 0.8:
        progress.review_required = False
    recompute_progress(progress)
    return progress


def update_concept_mastery(
    db: Session, user: User, concept_tag: ConceptTag, is_correct: bool
) -> UserConceptMastery:
    mastery = db.scalar(
        select(UserConceptMastery).where(
            UserConceptMastery.user_id == user.id,
            UserConceptMastery.concept_tag_id == concept_tag.id,
        )
    )
    if not mastery:
        mastery = UserConceptMastery(user_id=user.id, concept_tag_id=concept_tag.id)
        db.add(mastery)
        db.flush()

    if is_correct:
        mastery.correct_count += 1
    else:
        mastery.wrong_count += 1

    total = mastery.correct_count + mastery.wrong_count
    mastery.mastery_score = round(mastery.correct_count / total, 2) if total else 0
    mastery.last_practiced_at = utc_now()

    if mastery.wrong_count > mastery.correct_count:
        mastery.strength = SkillStrength.weak
    elif mastery.correct_count >= 3 and mastery.mastery_score >= 0.85:
        mastery.strength = SkillStrength.strong
    elif mastery.mastery_score >= 0.7:
        mastery.strength = SkillStrength.stable
    elif mastery.mastery_score > 0:
        mastery.strength = SkillStrength.learning
    else:
        mastery.strength = SkillStrength.not_started
    return mastery


def schedule_review(
    db: Session,
    user: User,
    concept_tag: ConceptTag | None,
    lesson: Lesson | None,
    question: Question | None,
    reason: str,
    is_correct: bool,
    create_if_missing: bool = True,
) -> ReviewItem | None:
    if not concept_tag and not lesson and not question:
        return None

    review = db.scalar(
        select(ReviewItem).where(
            ReviewItem.user_id == user.id,
            ReviewItem.concept_tag_id == (concept_tag.id if concept_tag else None),
            ReviewItem.lesson_id == (lesson.id if lesson else None),
            ReviewItem.question_id == (question.id if question else None),
            ReviewItem.is_active.is_(True),
        )
    )

    now = utc_now()
    if not review and not create_if_missing:
        return None

    if not review:
        review = ReviewItem(
            user_id=user.id,
            concept_tag_id=concept_tag.id if concept_tag else None,
            lesson_id=lesson.id if lesson else None,
            question_id=question.id if question else None,
            reason=reason,
            due_for_review=now + timedelta(days=1),
        )
        db.add(review)
        db.flush()

    review.review_count += 1
    review.last_reviewed_at = now
    review.reason = reason
    if is_correct:
        review.due_for_review = now + timedelta(days=7)
    elif review.review_count > 1:
        review.due_for_review = now + timedelta(days=3)
    else:
        review.due_for_review = now + timedelta(days=1)
    return review


def reinforce_existing_review(
    db: Session,
    user: User,
    concept_tag: ConceptTag | None,
    lesson: Lesson | None,
    question: Question | None,
    reason: str,
) -> ReviewItem | None:
    return schedule_review(
        db=db,
        user=user,
        concept_tag=concept_tag,
        lesson=lesson,
        question=question,
        reason=reason,
        is_correct=True,
        create_if_missing=False,
    )


def due_review_items(db: Session, user: User) -> list[ReviewItem]:
    return list(
        db.scalars(
            select(ReviewItem)
            .where(
                ReviewItem.user_id == user.id,
                ReviewItem.is_active.is_(True),
                ReviewItem.due_for_review <= utc_now(),
            )
            .order_by(ReviewItem.due_for_review.asc())
        )
    )


def serialize_review_item(item: ReviewItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "concept": item.concept_tag.name if item.concept_tag else None,
        "lesson_title": item.lesson.title if item.lesson else None,
        "question_prompt": item.question.prompt if item.question else None,
        "reason": item.reason,
        "due_for_review": item.due_for_review,
        "review_count": item.review_count,
    }


def _raise_missing(name: str):
    from fastapi import HTTPException, status

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} not found")
