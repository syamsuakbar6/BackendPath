from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Lesson,
    LessonStatus,
    ContentStatus,
    Level,
    Module,
    SkillStrength,
    Track,
    User,
    UserLessonProgress,
)
from app.services.progress import skill_strength_from_progress


def load_track_detail(db: Session, track_id: int) -> Track | None:
    return db.scalar(
        select(Track)
        .where(Track.id == track_id)
        .options(
            selectinload(Track.language),
            selectinload(Track.levels)
            .selectinload(Level.modules)
            .selectinload(Module.lessons)
            .selectinload(Lesson.concept_tags),
        )
    )


def progress_by_lesson(db: Session, user: User | None) -> dict[int, UserLessonProgress]:
    if not user:
        return {}
    records = db.scalars(
        select(UserLessonProgress).where(UserLessonProgress.user_id == user.id)
    ).all()
    return {item.lesson_id: item for item in records}


def lesson_summary(lesson: Lesson, progress: UserLessonProgress | None, locked: bool = False) -> dict:
    return {
        "id": lesson.id,
        "module_id": lesson.module_id,
        "title": lesson.title,
        "slug": lesson.slug,
        "learning_goal": lesson.learning_goal,
        "estimated_minutes": lesson.estimated_minutes,
        "sort_order": lesson.sort_order,
        "status": progress.status if progress else LessonStatus.not_started,
        "skill_strength": skill_strength_from_progress(progress),
        "mastery_score": progress.mastery_score if progress else 0.0,
        "locked": locked,
        "content_status": lesson.content_status,
    }


def module_strength(module: Module, progress_map: dict[int, UserLessonProgress]) -> SkillStrength:
    lessons = [
        lesson
        for lesson in module.lessons
        if lesson.content_status == ContentStatus.published
    ]
    if not lessons:
        return SkillStrength.not_started
    strengths = [
        skill_strength_from_progress(progress_map.get(lesson.id)) for lesson in lessons
    ]
    if SkillStrength.weak in strengths:
        return SkillStrength.weak
    if all(item == SkillStrength.strong for item in strengths):
        return SkillStrength.strong
    if any(item == SkillStrength.stable for item in strengths):
        return SkillStrength.stable
    if any(item == SkillStrength.learning for item in strengths):
        return SkillStrength.learning
    return SkillStrength.not_started


def build_track_map(db: Session, track: Track, user: User | None) -> dict:
    progress_map = progress_by_lesson(db, user)
    recommended = None
    previous_complete = True
    levels = []

    for level in track.levels:
        modules = []
        for module in level.modules:
            lesson_items = []
            completed_count = 0
            published_lessons = [
                lesson
                for lesson in module.lessons
                if lesson.content_status == ContentStatus.published
            ]
            for lesson in published_lessons:
                progress = progress_map.get(lesson.id)
                locked = not previous_complete
                if progress and progress.status in {LessonStatus.completed, LessonStatus.mastered}:
                    completed_count += 1
                if recommended is None and not locked and (
                    progress is None
                    or progress.status
                    not in {LessonStatus.completed, LessonStatus.mastered}
                ):
                    recommended = lesson_summary(lesson, progress, locked=False)

                lesson_items.append(lesson_summary(lesson, progress, locked=locked))
                previous_complete = bool(
                    progress and progress.status in {LessonStatus.completed, LessonStatus.mastered}
                )

            progress_percent = (
                round(completed_count / len(published_lessons), 2) if published_lessons else 0.0
            )
            modules.append(
                {
                    "id": module.id,
                    "level_id": module.level_id,
                    "title": module.title,
                    "slug": module.slug,
                    "description": module.description,
                    "estimated_minutes": module.estimated_minutes,
                    "sort_order": module.sort_order,
                    "progress": progress_percent,
                    "status": LessonStatus.completed
                    if progress_percent == 1
                    else LessonStatus.in_progress
                    if progress_percent > 0
                    else LessonStatus.not_started,
                    "skill_strength": module_strength(module, progress_map),
                    "lessons": lesson_items,
                }
            )

        levels.append(
            {
                "id": level.id,
                "track_id": level.track_id,
                "title": level.title,
                "slug": level.slug,
                "description": level.description,
                "sort_order": level.sort_order,
                "modules": modules,
            }
        )

    return {
        "id": track.id,
        "language_id": track.language_id,
        "title": track.title,
        "slug": track.slug,
        "description": track.description,
        "target_audience": track.target_audience,
        "sort_order": track.sort_order,
        "is_published": track.is_published,
        "language": track.language,
        "levels": levels,
        "recommended_lesson": recommended,
    }
