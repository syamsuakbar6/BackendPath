from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_optional_user
from app.db.session import get_db
from app.models import (
    Language,
    Lesson,
    LessonBlock,
    Level,
    MiniTask,
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
    return list(db.scalars(select(Track).order_by(Track.sort_order.asc(), Track.id.asc())))


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
    lesson = db.scalar(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(
            selectinload(Lesson.blocks),
            selectinload(Lesson.concept_tags),
            selectinload(Lesson.questions).selectinload(Question.options),
            selectinload(Lesson.questions).selectinload(Question.concept_tags),
            selectinload(Lesson.mini_tasks),
            selectinload(Lesson.debug_tasks),
        )
    )
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    progress = None
    if current_user:
        progress = db.scalar(
            select(UserLessonProgress).where(
                UserLessonProgress.user_id == current_user.id,
                UserLessonProgress.lesson_id == lesson.id,
            )
        )

    return {
        "id": lesson.id,
        "module_id": lesson.module_id,
        "title": lesson.title,
        "slug": lesson.slug,
        "learning_goal": lesson.learning_goal,
        "why_it_matters": lesson.why_it_matters,
        "estimated_minutes": lesson.estimated_minutes,
        "sort_order": lesson.sort_order,
        "concept_tags": lesson.concept_tags,
        "blocks": lesson.blocks,
        "questions": lesson.questions,
        "mini_tasks": lesson.mini_tasks,
        "debug_tasks": lesson.debug_tasks,
        "progress": progress,
    }
