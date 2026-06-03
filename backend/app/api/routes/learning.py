from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_optional_user
from app.db.session import get_db
from app.models import (
    ContentStatus,
    Language,
    Lesson,
    Level,
    Module,
    Question,
    Track,
    User,
    UserLessonProgress,
)
from app.schemas.learning import (
    LanguageOut,
    LessonDetailOut,
    LevelOut,
    ModuleMapOut,
    TrackDetailOut,
    TrackOut,
)
from app.services.content import lesson_to_payload, load_lesson_with_content
from app.services.learning import (
    build_track_map,
    load_track_detail,
    module_strength,
    progress_by_lesson,
    lesson_summary,
)


router = APIRouter(tags=["learning"])


@router.get("/languages", response_model=list[LanguageOut])
def list_languages(db: Session = Depends(get_db)) -> list[Language]:
    return list(
        db.scalars(select(Language).order_by(Language.sort_order.asc(), Language.name.asc()))
    )


@router.get("/tracks", response_model=list[TrackOut])
def list_tracks(db: Session = Depends(get_db)) -> list[Track]:
    return list(
        db.scalars(
            select(Track)
            .where(Track.is_published.is_(True))
            .order_by(Track.sort_order.asc(), Track.id.asc())
        )
    )


@router.get("/tracks/{track_id}", response_model=TrackDetailOut)
def get_track(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> dict:
    track = load_track_detail(db, track_id)
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")
    return build_track_map(db, track, current_user)


@router.get("/levels/{level_id}", response_model=LevelOut)
def get_level(level_id: int, db: Session = Depends(get_db)) -> Level:
    level = db.get(Level, level_id)
    if not level:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Level not found")
    return level


@router.get("/modules/{module_id}", response_model=ModuleMapOut)
def get_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> dict:
    module = db.scalar(
        select(Module)
        .where(Module.id == module_id)
        .options(selectinload(Module.lessons).selectinload(Lesson.concept_tags))
    )
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    progress_map = progress_by_lesson(db, current_user)
    lessons = [
        lesson_summary(lesson, progress_map.get(lesson.id), locked=False)
        for lesson in module.lessons
        if lesson.content_status == ContentStatus.published
    ]
    completed = sum(1 for item in lessons if item["status"].value in {"completed", "mastered"})
    progress = round(completed / len(lessons), 2) if lessons else 0.0

    return {
        "id": module.id,
        "level_id": module.level_id,
        "title": module.title,
        "slug": module.slug,
        "description": module.description,
        "estimated_minutes": module.estimated_minutes,
        "sort_order": module.sort_order,
        "progress": progress,
        "status": "completed" if progress == 1 else "in_progress" if progress > 0 else "not_started",
        "skill_strength": module_strength(module, progress_map),
        "lessons": lessons,
    }


@router.get("/lessons/{lesson_id}", response_model=LessonDetailOut)
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> dict:
    lesson = load_lesson_with_content(db, lesson_id)
    if not lesson or lesson.content_status != ContentStatus.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    progress = None
    if current_user:
        progress = db.scalar(
            select(UserLessonProgress).where(
                UserLessonProgress.user_id == current_user.id,
                UserLessonProgress.lesson_id == lesson.id,
            )
        )

    return lesson_to_payload(lesson, progress=progress, learner_view=True)
