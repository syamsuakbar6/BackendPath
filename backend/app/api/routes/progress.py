from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.progress import (
    DashboardOut,
    ExplainBackRequest,
    LessonActionResponse,
    ProofSubmissionOut,
    ProofSubmissionRequest,
    ProofSubmissionResponse,
    QuestionAnswerRequest,
    QuestionAnswerResponse,
    ReviewItemOut,
)
from app.services.dashboard import get_dashboard
from app.services.progress import (
    complete_reading,
    due_review_items,
    serialize_review_item,
    start_lesson,
)
from app.services.proofs import list_proof_submissions, submit_proof_submission
from app.services.questions import answer_question
from app.models import ProofType


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
    _submission, progress = submit_proof_submission(
        db,
        current_user,
        lesson_id,
        ProofSubmissionRequest(
            proof_type=ProofType.explain_back,
            answer_text=payload.answer,
        ),
    )
    return {"progress": progress, "message": "Explain-back submitted for rubric matching."}


@router.post("/lessons/{lesson_id}/proofs/submit", response_model=ProofSubmissionResponse)
def submit_lesson_proof(
    lesson_id: int,
    payload: ProofSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    submission, progress = submit_proof_submission(db, current_user, lesson_id, payload)
    return {
        "submission": submission,
        "progress": progress,
        "message": "Proof submitted and evaluated.",
    }


@router.get("/lessons/{lesson_id}/proofs", response_model=list[ProofSubmissionOut])
def list_lesson_proofs(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return list_proof_submissions(db, current_user, lesson_id)


@router.post("/lessons/{lesson_id}/complete-debug-task", response_model=LessonActionResponse)
def complete_debug_task(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Submit debug proof through /lessons/{lesson_id}/proofs/submit.",
    )


@router.post("/lessons/{lesson_id}/complete-mini-task", response_model=LessonActionResponse)
def complete_mini_task(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Submit mini task proof through /lessons/{lesson_id}/proofs/submit.",
    )


@router.post("/lessons/{lesson_id}/submit-reflection", response_model=LessonActionResponse)
def reflection(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Submit reflection proof through /lessons/{lesson_id}/proofs/submit.",
    )


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
