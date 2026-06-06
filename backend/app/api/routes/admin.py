from datetime import datetime, timezone
from typing import Any, Type

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import (
    ConceptTag,
    ContentStatus,
    DebugTask,
    EvaluationConfidence,
    Language,
    Lesson,
    LessonBlock,
    Level,
    MiniTask,
    Module,
    ProofFinalStatus,
    ProofStatus,
    ProofType,
    Question,
    QuestionOption,
    ReviewItem,
    ScoreLabel,
    Track,
    User,
    UserProofSubmission,
)
from app.schemas.progress import (
    AdminProofOverrideRequest,
    AdminProofSubmissionOut,
    ProofEvaluationAnalyticsOut,
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
from app.services.progress import get_or_create_progress, recompute_progress
from app.services.proofs import PASSING_STATUSES, has_latest_failed_proof


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/proof-submissions", response_model=list[AdminProofSubmissionOut])
def admin_proof_submissions(
    user_id: int | None = Query(default=None),
    lesson_id: int | None = Query(default=None),
    proof_type: ProofType | None = Query(default=None),
    status_filter: ProofStatus | None = Query(default=None, alias="status"),
    score_label: ScoreLabel | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[dict]:
    stmt = (
        select(UserProofSubmission)
        .options(
            selectinload(UserProofSubmission.user),
            selectinload(UserProofSubmission.lesson),
            selectinload(UserProofSubmission.overridden_by),
        )
        .order_by(UserProofSubmission.created_at.desc(), UserProofSubmission.id.desc())
    )
    if user_id is not None:
        stmt = stmt.where(UserProofSubmission.user_id == user_id)
    if lesson_id is not None:
        stmt = stmt.where(UserProofSubmission.lesson_id == lesson_id)
    if proof_type is not None:
        stmt = stmt.where(UserProofSubmission.proof_type == proof_type)
    if status_filter is not None:
        stmt = stmt.where(UserProofSubmission.status == status_filter)
    if score_label is not None:
        stmt = stmt.where(UserProofSubmission.final_score_label == score_label)

    submissions = list(db.scalars(stmt))
    review_ids = _review_ids_by_proof_submission(db, [item.id for item in submissions])
    return [_serialize_admin_proof_submission(item, review_ids.get(item.id, [])) for item in submissions]


@router.get("/proof-evaluation-analytics", response_model=ProofEvaluationAnalyticsOut)
def admin_proof_evaluation_analytics(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    submissions = list(
        db.scalars(
            select(UserProofSubmission).options(selectinload(UserProofSubmission.lesson))
        )
    )
    return _build_proof_evaluation_analytics(submissions)


@router.get("/proof-submissions/{item_id}", response_model=AdminProofSubmissionOut)
def admin_proof_submission_detail(
    item_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    submission = db.scalar(
        select(UserProofSubmission)
        .where(UserProofSubmission.id == item_id)
        .options(
            selectinload(UserProofSubmission.user),
            selectinload(UserProofSubmission.lesson),
            selectinload(UserProofSubmission.overridden_by),
        )
    )
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proof submission not found")
    review_ids = _review_ids_by_proof_submission(db, [submission.id])
    return _serialize_admin_proof_submission(submission, review_ids.get(submission.id, []))


@router.patch("/proof-submissions/{item_id}/override", response_model=AdminProofSubmissionOut)
def admin_override_proof_submission(
    item_id: int,
    payload: AdminProofOverrideRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    submission = db.scalar(
        select(UserProofSubmission)
        .where(UserProofSubmission.id == item_id)
        .options(
            selectinload(UserProofSubmission.user),
            selectinload(UserProofSubmission.lesson),
            selectinload(UserProofSubmission.overridden_by),
        )
    )
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proof submission not found")
    _apply_admin_override(db, submission, payload, admin)
    db.commit()
    db.refresh(submission)
    review_ids = _review_ids_by_proof_submission(db, [submission.id])
    return _serialize_admin_proof_submission(submission, review_ids.get(submission.id, []))


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


def _review_ids_by_proof_submission(db: Session, proof_submission_ids: list[int]) -> dict[int, list[int]]:
    if not proof_submission_ids:
        return {}
    rows = db.scalars(
        select(ReviewItem).where(ReviewItem.proof_submission_id.in_(proof_submission_ids))
    ).all()
    output: dict[int, list[int]] = {}
    for row in rows:
        if row.proof_submission_id is not None:
            output.setdefault(row.proof_submission_id, []).append(row.id)
    return output


def _serialize_admin_proof_submission(
    submission: UserProofSubmission,
    review_item_ids: list[int],
) -> dict[str, Any]:
    return {
        "id": submission.id,
        "user": {
            "id": submission.user.id,
            "email": submission.user.email,
            "full_name": submission.user.full_name,
            "role": submission.user.role.value,
        },
        "lesson": {
            "id": submission.lesson.id,
            "title": submission.lesson.title,
            "slug": submission.lesson.slug,
        },
        "proof_type": submission.proof_type,
        "question_id": submission.question_id,
        "debug_task_id": submission.debug_task_id,
        "mini_task_id": submission.mini_task_id,
        "answer_text": submission.answer_text,
        "code_text": submission.code_text,
        "status": submission.status,
        "score_label": submission.score_label,
        "score_numeric": submission.score_numeric,
        "feedback_json": submission.feedback_json,
        "heuristic_status": submission.heuristic_status or submission.status,
        "heuristic_score_label": submission.heuristic_score_label or submission.score_label,
        "heuristic_score_numeric": submission.heuristic_score_numeric if submission.heuristic_score_numeric is not None else submission.score_numeric,
        "heuristic_feedback_json": submission.heuristic_feedback_json or submission.feedback_json,
        "evaluation_confidence": submission.evaluation_confidence or EvaluationConfidence.medium,
        "final_evaluation_status": submission.final_evaluation_status or _final_status_from_current_submission(submission),
        "final_score_label": submission.final_score_label or submission.score_label,
        "final_score_numeric": submission.final_score_numeric if submission.final_score_numeric is not None else submission.score_numeric,
        "final_feedback_json": submission.final_feedback_json or submission.feedback_json,
        "overridden_by_id": submission.overridden_by_id,
        "overridden_by_email": submission.overridden_by.email if submission.overridden_by else None,
        "overridden_at": submission.overridden_at,
        "override_note": submission.override_note,
        "attempt_number": submission.attempt_number,
        "created_at": submission.created_at,
        "evaluated_at": submission.evaluated_at,
        "created_review_item": bool(review_item_ids),
        "review_item_ids": review_item_ids,
    }


def _apply_admin_override(
    db: Session,
    submission: UserProofSubmission,
    payload: AdminProofOverrideRequest,
    admin: User,
) -> None:
    final_score_label = payload.score_label or _default_score_label_for_final_status(payload.final_status)
    final_score_numeric = _score_numeric_for_override(payload.final_status, final_score_label, submission)
    final_feedback = _feedback_with_admin_override(submission, payload.final_status, payload.override_note)

    submission.final_evaluation_status = payload.final_status
    submission.final_score_label = final_score_label
    submission.final_score_numeric = final_score_numeric
    submission.final_feedback_json = final_feedback
    submission.overridden_by_id = admin.id
    submission.overridden_at = datetime.now(timezone.utc)
    submission.override_note = payload.override_note

    submission.status = _proof_status_for_final_status(payload.final_status, final_score_label)
    submission.score_label = final_score_label
    submission.score_numeric = final_score_numeric
    submission.feedback_json = final_feedback
    submission.evaluated_at = submission.overridden_at

    if payload.final_status == ProofFinalStatus.accepted:
        _close_reviews_for_submission(db, submission.id)
    _sync_progress_for_overridden_submission(db, submission)


def _proof_status_for_final_status(
    final_status: ProofFinalStatus,
    score_label: ScoreLabel,
) -> ProofStatus:
    if final_status == ProofFinalStatus.accepted:
        return ProofStatus.strong if score_label == ScoreLabel.strong else ProofStatus.passed
    return ProofStatus.needs_revision


def _default_score_label_for_final_status(final_status: ProofFinalStatus) -> ScoreLabel:
    if final_status == ProofFinalStatus.accepted:
        return ScoreLabel.stable
    if final_status == ProofFinalStatus.rejected:
        return ScoreLabel.incorrect
    return ScoreLabel.weak


def _score_numeric_for_override(
    final_status: ProofFinalStatus,
    score_label: ScoreLabel,
    submission: UserProofSubmission,
) -> float:
    if final_status == ProofFinalStatus.accepted:
        baseline = 0.9 if score_label == ScoreLabel.strong else 0.75
        return max(submission.score_numeric or 0, baseline)
    if final_status == ProofFinalStatus.rejected:
        return min(submission.score_numeric or 0.0, 0.2)
    return min(submission.score_numeric or 0.6, 0.6)


def _feedback_with_admin_override(
    submission: UserProofSubmission,
    final_status: ProofFinalStatus,
    override_note: str,
) -> dict[str, Any]:
    original = submission.final_feedback_json or submission.feedback_json or {}
    return {
        "correct_points": original.get("correct_points", []),
        "missing_points": original.get("missing_points", []),
        "misconceptions": original.get("misconceptions", []),
        "feedback": f"Admin override set final status to {final_status.value}.",
        "remedial_question": original.get("remedial_question", "Review the admin note and revise the proof if needed."),
        "evaluation_source": "admin_override",
        "override_note": override_note,
    }


def _close_reviews_for_submission(db: Session, proof_submission_id: int) -> None:
    reviews = db.scalars(
        select(ReviewItem).where(
            ReviewItem.proof_submission_id == proof_submission_id,
            ReviewItem.is_active.is_(True),
        )
    ).all()
    for review in reviews:
        review.is_active = False
        review.last_reviewed_at = datetime.now(timezone.utc)
        review.reason = "Admin override accepted the proof submission."


def _sync_progress_for_overridden_submission(db: Session, submission: UserProofSubmission) -> None:
    progress = get_or_create_progress(db, submission.user_id, submission.lesson_id)
    latest = _latest_required_submissions_for_progress(db, submission.user_id, submission.lesson_id)
    explain = latest.get(ProofType.explain_back)
    debug = latest.get(ProofType.debug_task)
    mini = latest.get(ProofType.mini_task)

    progress.explain_back_submitted = bool(explain and explain.status in PASSING_STATUSES)
    progress.explain_back_score = explain.score_numeric if explain and explain.status in PASSING_STATUSES else None
    progress.debug_task_completed = bool(debug and debug.status in PASSING_STATUSES)
    progress.mini_task_completed = bool(mini and mini.status in PASSING_STATUSES)
    progress.review_required = has_latest_failed_proof(db, submission.user, submission.lesson_id) or (
        progress.quick_check_score is not None and progress.quick_check_score < 0.8
    )
    recompute_progress(progress)


def _latest_required_submissions_for_progress(
    db: Session,
    user_id: int,
    lesson_id: int,
) -> dict[ProofType, UserProofSubmission | None]:
    rows = list(
        db.scalars(
            select(UserProofSubmission)
            .where(
                UserProofSubmission.user_id == user_id,
                UserProofSubmission.lesson_id == lesson_id,
                UserProofSubmission.proof_type.in_(
                    [ProofType.explain_back, ProofType.debug_task, ProofType.mini_task]
                ),
            )
            .order_by(UserProofSubmission.created_at.desc(), UserProofSubmission.id.desc())
        )
    )
    latest: dict[ProofType, UserProofSubmission | None] = {
        ProofType.explain_back: None,
        ProofType.debug_task: None,
        ProofType.mini_task: None,
    }
    for row in rows:
        if latest[row.proof_type] is None:
            latest[row.proof_type] = row
    return latest


def _final_status_from_current_submission(submission: UserProofSubmission) -> ProofFinalStatus:
    if submission.status in PASSING_STATUSES:
        return ProofFinalStatus.accepted
    if submission.score_label == ScoreLabel.incorrect:
        return ProofFinalStatus.rejected
    return ProofFinalStatus.needs_review


def _build_proof_evaluation_analytics(submissions: list[UserProofSubmission]) -> dict[str, Any]:
    total = len(submissions)
    count_by_proof_type = _count_values([item.proof_type.value for item in submissions])
    count_by_final_status = _count_values([
        (item.final_evaluation_status or _final_status_from_current_submission(item)).value
        for item in submissions
    ])
    count_by_heuristic_status = _count_values([
        (item.heuristic_status or item.status).value
        for item in submissions
    ])
    count_by_confidence = _count_values([
        (item.evaluation_confidence or EvaluationConfidence.medium).value
        for item in submissions
    ])
    count_by_score_label = _count_values([
        (item.final_score_label or item.score_label).value
        for item in submissions
        if item.final_score_label or item.score_label
    ])
    override_count = sum(1 for item in submissions if item.overridden_by_id is not None)

    lesson_counts: dict[int, dict[str, int | str]] = {}
    for item in submissions:
        final_status = item.final_evaluation_status or _final_status_from_current_submission(item)
        if final_status not in {ProofFinalStatus.rejected, ProofFinalStatus.needs_review}:
            continue
        lesson_counts.setdefault(
            item.lesson_id,
            {
                "lesson_id": item.lesson_id,
                "lesson_title": item.lesson.title if item.lesson else "Unknown lesson",
                "count": 0,
            },
        )
        lesson_counts[item.lesson_id]["count"] = int(lesson_counts[item.lesson_id]["count"]) + 1

    misconception_counts: dict[str, int] = {}
    for item in submissions:
        feedback = item.heuristic_feedback_json or item.feedback_json or {}
        for misconception in feedback.get("misconceptions", []) or []:
            misconception_counts[str(misconception)] = misconception_counts.get(str(misconception), 0) + 1

    return {
        "total_submissions": total,
        "count_by_proof_type": count_by_proof_type,
        "count_by_final_status": count_by_final_status,
        "count_by_heuristic_status": count_by_heuristic_status,
        "count_by_confidence": count_by_confidence,
        "count_by_score_label": count_by_score_label,
        "override_count": override_count,
        "override_rate": round(override_count / total, 2) if total else 0.0,
        "top_lessons_with_rejected_or_needs_review": sorted(
            lesson_counts.values(),
            key=lambda item: int(item["count"]),
            reverse=True,
        )[:5],
        "top_misconceptions": [
            {"misconception": key, "count": value}
            for key, value in sorted(misconception_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        ],
    }


def _count_values(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts
