from typing import Any, Type

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import (
    ConceptTag,
    ContentStatus,
    DebugTask,
    Language,
    Lesson,
    LessonBlock,
    Level,
    MiniTask,
    Module,
    Question,
    QuestionOption,
    Track,
    User,
)
from app.schemas.learning import (
    ConceptTagCreate,
    ConceptTagOut,
    LanguageCreate,
    LanguageOut,
    LessonBlockCreate,
    LessonBlockOut,
    LessonCreate,
    LessonDetailOut,
    LessonImportPayload,
    LessonValidationResponse,
    LevelCreate,
    LevelOut,
    MiniTaskCreate,
    MiniTaskOut,
    ModuleCreate,
    ModuleOut,
    QuestionCreate,
    QuestionOptionAdminCreate,
    QuestionOptionCreate,
    QuestionOptionOut,
    QuestionOut,
    TrackCreate,
    TrackOut,
    DebugTaskCreate,
    DebugTaskOut,
)
from app.services.content import (
    archive_lesson,
    export_lesson,
    import_lesson,
    lesson_to_payload,
    load_lesson_with_content,
    publish_lesson,
    validate_lesson_publishable,
)


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/languages", response_model=list[LanguageOut])
def admin_languages(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[Language]:
    return list(db.scalars(select(Language).order_by(Language.sort_order.asc())))


@router.post("/languages", response_model=LanguageOut, status_code=status.HTTP_201_CREATED)
def create_language(
    payload: LanguageCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Language:
    item = Language(**payload.model_dump())
    return _create(db, item)


@router.get("/languages/{item_id}", response_model=LanguageOut)
def get_language(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Language:
    return _get_or_404(db, Language, item_id)


@router.patch("/languages/{item_id}", response_model=LanguageOut)
def update_language(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Language:
    return _update(db, _get_or_404(db, Language, item_id), payload)


@router.delete("/languages/{item_id}")
def delete_language(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, Language, item_id))


@router.get("/tracks", response_model=list[TrackOut])
def admin_tracks(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[Track]:
    return list(db.scalars(select(Track).order_by(Track.sort_order.asc())))


@router.post("/tracks", response_model=TrackOut, status_code=status.HTTP_201_CREATED)
def create_track(
    payload: TrackCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Track:
    item = Track(**payload.model_dump())
    return _create(db, item)


@router.get("/tracks/{item_id}", response_model=TrackOut)
def get_track_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Track:
    return _get_or_404(db, Track, item_id)


@router.patch("/tracks/{item_id}", response_model=TrackOut)
def update_track(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Track:
    return _update(db, _get_or_404(db, Track, item_id), payload)


@router.delete("/tracks/{item_id}")
def delete_track(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, Track, item_id))


@router.get("/levels", response_model=list[LevelOut])
def admin_levels(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[Level]:
    return list(db.scalars(select(Level).order_by(Level.sort_order.asc())))


@router.post("/levels", response_model=LevelOut, status_code=status.HTTP_201_CREATED)
def create_level(
    payload: LevelCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Level:
    return _create(db, Level(**payload.model_dump()))


@router.get("/levels/{item_id}", response_model=LevelOut)
def get_level_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Level:
    return _get_or_404(db, Level, item_id)


@router.patch("/levels/{item_id}", response_model=LevelOut)
def update_level(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Level:
    return _update(db, _get_or_404(db, Level, item_id), payload)


@router.delete("/levels/{item_id}")
def delete_level(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, Level, item_id))


@router.get("/modules", response_model=list[ModuleOut])
def admin_modules(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[Module]:
    return list(db.scalars(select(Module).order_by(Module.sort_order.asc())))


@router.post("/modules", response_model=ModuleOut, status_code=status.HTTP_201_CREATED)
def create_module(
    payload: ModuleCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Module:
    return _create(db, Module(**payload.model_dump()))


@router.get("/modules/{item_id}", response_model=ModuleOut)
def get_module_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Module:
    return _get_or_404(db, Module, item_id)


@router.patch("/modules/{item_id}", response_model=ModuleOut)
def update_module(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Module:
    return _update(db, _get_or_404(db, Module, item_id), payload)


@router.delete("/modules/{item_id}")
def delete_module(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, Module, item_id))


@router.get("/lessons", response_model=list[LessonDetailOut])
def admin_lessons(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[dict]:
    lessons = list(
        db.scalars(
            select(Lesson).options(
                selectinload(Lesson.blocks),
                selectinload(Lesson.questions).selectinload(Question.options),
                selectinload(Lesson.questions).selectinload(Question.concept_tags),
                selectinload(Lesson.concept_tags),
                selectinload(Lesson.mini_tasks),
                selectinload(Lesson.debug_tasks),
            )
        )
    )
    return [lesson_to_payload(lesson) for lesson in lessons]


@router.post("/lessons", response_model=LessonDetailOut, status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    data = payload.model_dump()
    requested_status = data["content_status"]
    if requested_status == ContentStatus.published:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Create lessons as draft, then publish after blocks and questions are valid."
            },
        )
    data["is_published"] = requested_status == ContentStatus.published
    return lesson_to_payload(_create(db, Lesson(**data)))


@router.get("/lessons/{item_id}", response_model=LessonDetailOut)
def get_lesson_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    lesson = load_lesson_with_content(db, item_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson_to_payload(lesson)


@router.patch("/lessons/{item_id}", response_model=LessonDetailOut)
def update_lesson(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    target_status = payload.pop("content_status", None)
    lesson = _get_or_404(db, Lesson, item_id)
    if payload:
        lesson = _update(db, lesson, payload)
    lesson = load_lesson_with_content(db, item_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    if target_status == ContentStatus.published or target_status == ContentStatus.published.value:
        return lesson_to_payload(publish_lesson(db, lesson))
    if target_status == ContentStatus.archived or target_status == ContentStatus.archived.value:
        return lesson_to_payload(archive_lesson(db, lesson))
    if target_status == ContentStatus.draft or target_status == ContentStatus.draft.value:
        lesson.content_status = ContentStatus.draft
        lesson.is_published = False
        db.commit()
        db.refresh(lesson)

    return lesson_to_payload(load_lesson_with_content(db, item_id) or lesson)


@router.delete("/lessons/{item_id}")
def delete_lesson(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, Lesson, item_id))


@router.get("/lessons/{item_id}/preview", response_model=LessonDetailOut)
def preview_lesson_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    lesson = load_lesson_with_content(db, item_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson_to_payload(lesson, progress=None, learner_view=False)


@router.get("/lessons/{item_id}/validate", response_model=LessonValidationResponse)
def validate_lesson_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    lesson = load_lesson_with_content(db, item_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    errors = validate_lesson_publishable(lesson)
    return {"lesson_id": lesson.id, "valid": not errors, "errors": errors}


@router.post("/lessons/{item_id}/publish", response_model=LessonDetailOut)
def publish_lesson_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    lesson = load_lesson_with_content(db, item_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson_to_payload(publish_lesson(db, lesson))


@router.post("/lessons/{item_id}/archive", response_model=LessonDetailOut)
def archive_lesson_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    lesson = load_lesson_with_content(db, item_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson_to_payload(archive_lesson(db, lesson))


@router.post("/content/import/lesson", response_model=LessonDetailOut, status_code=status.HTTP_201_CREATED)
def import_lesson_admin(
    payload: LessonImportPayload,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    lesson = import_lesson(db, payload)
    return lesson_to_payload(lesson)


@router.get("/content/export/lesson/{item_id}")
def export_lesson_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    lesson = load_lesson_with_content(db, item_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return export_lesson(lesson)


@router.get("/lesson-blocks", response_model=list[LessonBlockOut])
def admin_lesson_blocks(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[LessonBlock]:
    return list(db.scalars(select(LessonBlock).order_by(LessonBlock.sort_order.asc())))


@router.post("/lesson-blocks", response_model=LessonBlockOut, status_code=status.HTTP_201_CREATED)
def create_lesson_block(
    payload: LessonBlockCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> LessonBlock:
    return _create(db, LessonBlock(**payload.model_dump()))


@router.patch("/lesson-blocks/{item_id}", response_model=LessonBlockOut)
def update_lesson_block(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> LessonBlock:
    return _update(db, _get_or_404(db, LessonBlock, item_id), payload)


@router.delete("/lesson-blocks/{item_id}")
def delete_lesson_block(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, LessonBlock, item_id))


@router.get("/debug-tasks", response_model=list[DebugTaskOut])
def admin_debug_tasks(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[DebugTask]:
    return list(db.scalars(select(DebugTask).order_by(DebugTask.id.asc())))


@router.post("/debug-tasks", response_model=DebugTaskOut, status_code=status.HTTP_201_CREATED)
def create_debug_task(
    payload: DebugTaskCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> DebugTask:
    return _create(db, DebugTask(**payload.model_dump()))


@router.patch("/debug-tasks/{item_id}", response_model=DebugTaskOut)
def update_debug_task(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> DebugTask:
    return _update(db, _get_or_404(db, DebugTask, item_id), payload)


@router.delete("/debug-tasks/{item_id}")
def delete_debug_task(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, DebugTask, item_id))


@router.get("/mini-tasks", response_model=list[MiniTaskOut])
def admin_mini_tasks(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[MiniTask]:
    return list(db.scalars(select(MiniTask).order_by(MiniTask.id.asc())))


@router.post("/mini-tasks", response_model=MiniTaskOut, status_code=status.HTTP_201_CREATED)
def create_mini_task(
    payload: MiniTaskCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> MiniTask:
    return _create(db, MiniTask(**payload.model_dump()))


@router.patch("/mini-tasks/{item_id}", response_model=MiniTaskOut)
def update_mini_task(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> MiniTask:
    return _update(db, _get_or_404(db, MiniTask, item_id), payload)


@router.delete("/mini-tasks/{item_id}")
def delete_mini_task(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, MiniTask, item_id))


@router.get("/concept-tags", response_model=list[ConceptTagOut])
def admin_concept_tags(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[ConceptTag]:
    return list(db.scalars(select(ConceptTag).order_by(ConceptTag.name.asc())))


@router.post("/concept-tags", response_model=ConceptTagOut, status_code=status.HTTP_201_CREATED)
def create_concept_tag(
    payload: ConceptTagCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> ConceptTag:
    return _create(db, ConceptTag(**payload.model_dump()))


@router.patch("/concept-tags/{item_id}", response_model=ConceptTagOut)
def update_concept_tag(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> ConceptTag:
    return _update(db, _get_or_404(db, ConceptTag, item_id), payload)


@router.delete("/concept-tags/{item_id}")
def delete_concept_tag(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, ConceptTag, item_id))


@router.get("/questions", response_model=list[QuestionOut])
def admin_questions(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[Question]:
    return list(
        db.scalars(
            select(Question).options(
                selectinload(Question.options), selectinload(Question.concept_tags)
            )
        )
    )


@router.post("/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Question:
    data = payload.model_dump(exclude={"options", "concept_tag_ids"})
    question = Question(**data)
    if payload.concept_tag_ids:
        question.concept_tags = list(
            db.scalars(
                select(ConceptTag).where(ConceptTag.id.in_(payload.concept_tag_ids))
            )
        )
    question.options = [QuestionOption(**item.model_dump()) for item in payload.options]
    return _create(db, question)


@router.get("/questions/{item_id}", response_model=QuestionOut)
def get_question_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Question:
    return _get_or_404(db, Question, item_id)


@router.patch("/questions/{item_id}", response_model=QuestionOut)
def update_question(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Question:
    question = _get_or_404(db, Question, item_id)
    concept_tag_ids = payload.pop("concept_tag_ids", None)
    if concept_tag_ids is not None:
        question.concept_tags = list(
            db.scalars(select(ConceptTag).where(ConceptTag.id.in_(concept_tag_ids)))
        )
    return _update(db, question, payload)


@router.delete("/questions/{item_id}")
def delete_question(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, Question, item_id))


@router.get("/question-options", response_model=list[QuestionOptionOut])
def admin_question_options(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[QuestionOption]:
    return list(db.scalars(select(QuestionOption).order_by(QuestionOption.id.asc())))


@router.post(
    "/question-options",
    response_model=QuestionOptionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_question_option(
    payload: QuestionOptionAdminCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> QuestionOption:
    _get_or_404(db, Question, payload.question_id)
    data = payload.model_dump()
    question_id = data.pop("question_id")
    return _create(db, QuestionOption(question_id=question_id, **data))


@router.get("/question-options/{item_id}", response_model=QuestionOptionOut)
def get_question_option_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> QuestionOption:
    return _get_or_404(db, QuestionOption, item_id)


@router.patch("/question-options/{item_id}", response_model=QuestionOptionOut)
def update_question_option(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> QuestionOption:
    return _update(db, _get_or_404(db, QuestionOption, item_id), payload)


@router.delete("/question-options/{item_id}")
def delete_question_option(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, QuestionOption, item_id))


def _create(db: Session, item):
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _get_or_404(db: Session, model: Type, item_id: int):
    item = db.get(model, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} not found",
        )
    return item


def _update(db: Session, item, payload: dict[str, Any]):
    for key, value in payload.items():
        if hasattr(item, key):
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def _delete(db: Session, item) -> dict[str, str]:
    db.delete(item)
    db.commit()
    return {"status": "deleted"}
