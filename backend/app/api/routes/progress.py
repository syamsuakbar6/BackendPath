from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.progress import (
    DashboardOut,
    ExplainBackRequest,
    LessonActionResponse,
    QuestionAnswerRequest,
    QuestionAnswerResponse,
    ReviewItemOut,
)
from app.services.dashboard import get_dashboard
from app.services.progress import (
    complete_reading,
    due_review_items,
    mark_debug_task_completed,
    mark_mini_task_completed,
    serialize_review_item,
    start_lesson,
    submit_explain_back,
    submit_reflection,
)
from app.services.questions import answer_question


router = APIRouter(tags=["progress"])


@router.post("/lessons/{lesson_id}/start", response_model=LessonActionResponse)
def start(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    progress = start_lesson(db, current_user, lesson_id)
    return {"progress": progress, "message": "Lesson started. Keep the session focused."}


@router.post("/lessons/{lesson_id}/complete-reading", response_model=LessonActionResponse)
def complete_lesson_reading(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    progress = complete_reading(db, current_user, lesson_id)
    return {
        "progress": progress,
        "message": "Reading recorded. Mastery still needs proof points.",
    }


@router.post("/lessons/{lesson_id}/submit-explain-back", response_model=LessonActionResponse)
def explain_back(
    lesson_id: int,
    payload: ExplainBackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    progress = submit_explain_back(db, current_user, lesson_id, payload.answer)
    return {"progress": progress, "message": "Explain-back submitted for rubric matching."}


@router.post("/lessons/{lesson_id}/complete-debug-task", response_model=LessonActionResponse)
def complete_debug_task(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    progress = mark_debug_task_completed(db, current_user, lesson_id)
    return {"progress": progress, "message": "Debug proof point recorded."}


@router.post("/lessons/{lesson_id}/complete-mini-task", response_model=LessonActionResponse)
def complete_mini_task(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    progress = mark_mini_task_completed(db, current_user, lesson_id)
    return {"progress": progress, "message": "Mini task proof point recorded."}


@router.post("/lessons/{lesson_id}/submit-reflection", response_model=LessonActionResponse)
def reflection(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    progress = submit_reflection(db, current_user, lesson_id)
    return {"progress": progress, "message": "Reflection checkpoint recorded."}


@router.post("/questions/{question_id}/answer", response_model=QuestionAnswerResponse)
def answer(
    question_id: int,
    payload: QuestionAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = answer_question(db, current_user, question_id, payload.answer)
    return {
        "attempt_id": result["attempt"].id,
        "feedback": result["feedback"],
        "lesson_progress": result["progress"],
    }


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return get_dashboard(db, current_user)


@router.get("/reviews/due", response_model=list[ReviewItemOut])
def reviews_due(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    return [serialize_review_item(item) for item in due_review_items(db, current_user)]
