from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ConceptTag,
    ContentStatus,
    Lesson,
    LessonStatus,
    SkillStrength,
    Track,
    User,
    UserConceptMastery,
    UserLessonProgress,
)
from app.services.learning import build_track_map, load_track_detail, lesson_summary
from app.services.progress import due_review_items, serialize_review_item


SESSION_MODES = {
    "quick": 2,
    "normal": 4,
    "project": 7,
}


def get_dashboard(db: Session, user: User) -> dict:
    track = db.scalar(
        select(Track)
        .where(Track.is_published.is_(True))
        .order_by(Track.sort_order.asc(), Track.id.asc())
    )
    track_detail = load_track_detail(db, track.id) if track else None
    track_map = build_track_map(db, track_detail, user) if track_detail else None

    continue_record = db.scalar(
        select(UserLessonProgress)
        .where(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.status.in_(
                [LessonStatus.in_progress, LessonStatus.needs_review]
            ),
        )
        .options(selectinload(UserLessonProgress.lesson))
        .order_by(UserLessonProgress.updated_at.desc())
    )
    continue_lesson = (
        lesson_summary(continue_record.lesson, continue_record)
        if continue_record and continue_record.lesson
        and continue_record.lesson.content_status == ContentStatus.published
        else None
    )

    recommended = track_map["recommended_lesson"] if track_map else None
    current_level = _find_current_level(track_map, recommended["id"] if recommended else None)

    weak_records = db.scalars(
        select(UserConceptMastery)
        .where(
            UserConceptMastery.user_id == user.id,
            UserConceptMastery.strength == SkillStrength.weak,
        )
        .options(selectinload(UserConceptMastery.concept_tag))
        .limit(5)
    ).all()

    mastery_records = db.scalars(
        select(UserConceptMastery)
        .where(UserConceptMastery.user_id == user.id)
        .options(selectinload(UserConceptMastery.concept_tag))
        .order_by(UserConceptMastery.updated_at.desc())
        .limit(8)
    ).all()

    return {
        "active_track": track.title if track else None,
        "current_level": current_level,
        "recommended_next_lesson": recommended,
        "continue_lesson": continue_lesson,
        "weak_concepts": [
            {
                "concept": record.concept_tag.name,
                "strength": record.strength,
                "mastery_score": record.mastery_score,
                "wrong_count": record.wrong_count,
                "correct_count": record.correct_count,
            }
            for record in weak_records
        ],
        "due_reviews": [serialize_review_item(item) for item in due_review_items(db, user)],
        "consistency_label": _consistency_label(user.current_streak),
        "mastery_labels": [
            f"{record.concept_tag.name}: {record.strength.value}"
            for record in mastery_records
        ],
        "session_modes": SESSION_MODES,
    }


def _find_current_level(track_map: dict | None, lesson_id: int | None) -> str | None:
    if not track_map:
        return None
    if lesson_id is None:
        first = next(iter(track_map["levels"]), None)
        return first["title"] if first else None
    for level in track_map["levels"]:
        for module in level["modules"]:
            if any(lesson["id"] == lesson_id for lesson in module["lessons"]):
                return level["title"]
    return None


def _consistency_label(streak: int) -> str:
    if streak >= 7:
        return "steady weekly rhythm"
    if streak >= 3:
        return "building consistency"
    if streak >= 1:
        return "started recently"
    return "ready for a focused first session"
