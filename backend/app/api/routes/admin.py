from typing import Any, Type

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import (
    ConceptTag,
    Language,
    Lesson,
    LessonBlock,
    Level,
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
    LevelCreate,
    LevelOut,
    ModuleCreate,
    ModuleOut,
    QuestionCreate,
    QuestionOptionAdminCreate,
    QuestionOptionCreate,
    QuestionOptionOut,
    QuestionOut,
    TrackCreate,
    TrackOut,
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
    return [_lesson_payload(lesson) for lesson in lessons]


@router.post("/lessons", response_model=LessonDetailOut, status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    return _lesson_payload(_create(db, Lesson(**payload.model_dump())))


@router.get("/lessons/{item_id}", response_model=LessonDetailOut)
def get_lesson_admin(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    return _lesson_payload(_get_or_404(db, Lesson, item_id))


@router.patch("/lessons/{item_id}", response_model=LessonDetailOut)
def update_lesson(
    item_id: int,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    return _lesson_payload(_update(db, _get_or_404(db, Lesson, item_id), payload))


@router.delete("/lessons/{item_id}")
def delete_lesson(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, str]:
    return _delete(db, _get_or_404(db, Lesson, item_id))


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


def _lesson_payload(lesson: Lesson) -> dict:
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
        "progress": None,
    }
