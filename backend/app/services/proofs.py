from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ContentStatus,
    DebugTask,
    Lesson,
    MiniTask,
    ProofStatus,
    ProofType,
    Question,
    QuestionType,
    ScoreLabel,
    User,
    UserLessonProgress,
    UserProofSubmission,
)
from app.schemas.progress import ProofSubmissionRequest
from app.services.progress import (
    get_or_create_progress,
    recompute_progress,
    reinforce_existing_review,
    schedule_review,
    score_text_against_concepts,
    update_concept_mastery,
)


PASSING_STATUSES = {ProofStatus.passed, ProofStatus.strong}
REQUIRED_PROOF_TYPES = {
    ProofType.explain_back,
    ProofType.debug_task,
    ProofType.mini_task,
}


def submit_proof_submission(
    db: Session,
    user: User,
    lesson_id: int,
    payload: ProofSubmissionRequest,
) -> tuple[UserProofSubmission, UserLessonProgress]:
    lesson = _load_published_lesson(db, lesson_id)
    question = _load_question(db, lesson, payload)
    debug_task = _load_debug_task(db, lesson, payload)
    mini_task = _load_mini_task(db, lesson, payload)

    evaluation = evaluate_proof(
        proof_type=payload.proof_type,
        lesson=lesson,
        question=question,
        debug_task=debug_task,
        mini_task=mini_task,
        answer_text=payload.answer_text,
        code_text=payload.code_text,
    )
    attempt_number = _next_attempt_number(
        db,
        user=user,
        lesson_id=lesson.id,
        proof_type=payload.proof_type,
        question_id=question.id if question else None,
        debug_task_id=debug_task.id if debug_task else None,
        mini_task_id=mini_task.id if mini_task else None,
    )
    submission = UserProofSubmission(
        user_id=user.id,
        lesson_id=lesson.id,
        proof_type=payload.proof_type,
        question_id=question.id if question else None,
        debug_task_id=debug_task.id if debug_task else None,
        mini_task_id=mini_task.id if mini_task else None,
        answer_text=payload.answer_text,
        code_text=payload.code_text,
        status=evaluation["status"],
        score_label=evaluation["score_label"],
        score_numeric=evaluation["score_numeric"],
        feedback_json=evaluation["feedback_json"],
        attempt_number=attempt_number,
        evaluated_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.flush()

    progress = _apply_proof_to_progress(
        db=db,
        user=user,
        lesson=lesson,
        submission=submission,
        question=question,
        debug_task=debug_task,
        mini_task=mini_task,
    )
    db.commit()
    db.refresh(submission)
    db.refresh(progress)
    return submission, progress


def list_proof_submissions(
    db: Session,
    user: User,
    lesson_id: int,
) -> list[UserProofSubmission]:
    _load_published_lesson(db, lesson_id)
    return list(
        db.scalars(
            select(UserProofSubmission)
            .where(
                UserProofSubmission.user_id == user.id,
                UserProofSubmission.lesson_id == lesson_id,
            )
            .order_by(UserProofSubmission.created_at.desc(), UserProofSubmission.id.desc())
        )
    )


def evaluate_proof(
    proof_type: ProofType,
    lesson: Lesson,
    question: Question | None,
    debug_task: DebugTask | None,
    mini_task: MiniTask | None,
    answer_text: str | None,
    code_text: str | None,
) -> dict[str, Any]:
    answer = (answer_text or "").strip()
    code = (code_text or "").strip()
    combined = f"{answer}\n{code}".strip()

    if not combined or len(combined) < 12:
        return _result(
            score=0.0,
            correct_points=[],
            missing_points=["Write a meaningful answer before this proof can count."],
            feedback="This proof needs more than an empty or very short response.",
            remedial_question="Can you state the idea in your own words and connect it to this lesson?",
        )

    if proof_type == ProofType.explain_back:
        return _evaluate_explain_back(question, answer)
    if proof_type == ProofType.debug_task:
        return _evaluate_debug(debug_task, answer, code)
    if proof_type == ProofType.mini_task:
        return _evaluate_mini_task(mini_task, answer, code)
    if proof_type == ProofType.reflection:
        return _evaluate_reflection(answer)
    if proof_type == ProofType.review:
        return _evaluate_review(answer, code)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported proof type")


def latest_required_proof_summary(
    db: Session,
    user: User,
    lesson_id: int,
) -> dict[ProofType, UserProofSubmission | None]:
    rows = list(
        db.scalars(
            select(UserProofSubmission)
            .where(
                UserProofSubmission.user_id == user.id,
                UserProofSubmission.lesson_id == lesson_id,
                UserProofSubmission.proof_type.in_(list(REQUIRED_PROOF_TYPES)),
            )
            .order_by(UserProofSubmission.created_at.desc(), UserProofSubmission.id.desc())
        )
    )
    latest = {proof_type: None for proof_type in REQUIRED_PROOF_TYPES}
    for row in rows:
        if latest[row.proof_type] is None:
            latest[row.proof_type] = row
    return latest


def missing_proof_requirements(
    db: Session,
    user: User,
    progress: UserLessonProgress | None,
) -> list[dict[str, str]]:
    if not progress:
        return [
            _missing("reading", "Reading", "missing", "Start the lesson and finish the reading section."),
            _missing("quick_check", "Quick check", "missing", "Answer the quick check correctly."),
            _missing("explain_back", "Explain-back", "missing", "Submit an explain-back proof."),
            _missing("debug_task", "Debug proof", "missing", "Submit a debug proof."),
            _missing("mini_task", "Mini task proof", "missing", "Submit a mini task proof."),
        ]

    latest = latest_required_proof_summary(db, user, progress.lesson_id)
    items: list[dict[str, str]] = []
    if not progress.reading_completed:
        items.append(_missing("reading", "Reading", "missing", "Finish reading the lesson."))
    if (progress.quick_check_score or 0) < 0.7:
        items.append(_missing("quick_check", "Quick check", "missing", "Pass at least one quick check."))
    for proof_type, label in (
        (ProofType.explain_back, "Explain-back"),
        (ProofType.debug_task, "Debug proof"),
        (ProofType.mini_task, "Mini task proof"),
    ):
        submission = latest.get(proof_type)
        if not submission:
            items.append(_missing(proof_type.value, label, "missing", f"Submit a {label.lower()} that passes review."))
        elif submission.status not in PASSING_STATUSES:
            items.append(
                _missing(
                    proof_type.value,
                    label,
                    "weak",
                    submission.feedback_json.get("feedback", f"Revise the {label.lower()}.")
                    if submission.feedback_json
                    else f"Revise the {label.lower()}.",
                )
            )
    if progress.review_required:
        items.append(_missing("review_required", "Review", "needs_review", "Repair weak proof or concept review items."))
    return items


def _evaluate_explain_back(question: Question | None, answer: str) -> dict[str, Any]:
    expected = question.expected_concepts if question else None
    score, matched = score_text_against_concepts(answer, expected)
    expected_set = expected or []
    missing = [concept for concept in expected_set if concept not in matched]
    correct = [f"Included concept: {concept}" for concept in matched]
    if score >= 0.7:
        feedback = "Your explanation connects the concept to enough expected ideas."
    else:
        feedback = "Your explanation needs more of the expected concepts and backend consequence."
    return _result(
        score=score,
        correct_points=correct,
        missing_points=[f"Missing concept: {concept}" for concept in missing],
        feedback=feedback,
        remedial_question=question.remedial_prompt if question and question.remedial_prompt else "What would this change in a real API route?",
    )


def _evaluate_debug(debug_task: DebugTask | None, answer: str, code: str) -> dict[str, Any]:
    combined = _normalize(f"{answer}\n{code}")
    checks = [
        ("bug identified", _has_any(combined, {"bug", "broken", "problem", "issue", "fails", "wrong", "none"})),
        ("cause explained", _has_any(combined, {"because", "cause", "caused", "why", "wrong", "returns none", "print"})),
        ("fix proposed", _has_any(combined, {"fix", "change", "replace", "return", "should", "correct"})),
    ]
    correct = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    score = len(correct) / len(checks)
    return _result(
        score=score,
        correct_points=correct,
        missing_points=missing,
        feedback="Debug proof should name the bug, explain the cause, and propose a fix.",
        remedial_question=debug_task.hint if debug_task and debug_task.hint else "What exactly breaks, why does it break, and what would you change?",
    )


def _evaluate_mini_task(mini_task: MiniTask | None, answer: str, code: str) -> dict[str, Any]:
    checks = [
        ("solution or code provided", bool(code) or len(answer) >= 20),
        ("short explanation provided", len(answer) >= 35),
    ]
    criteria = mini_task.acceptance_criteria if mini_task else None
    if criteria:
        criteria_text = _normalize(" ".join(criteria))
        user_text = _normalize(f"{answer}\n{code}")
        criteria_terms = {
            term
            for term in criteria_text.split()
            if len(term) >= 5 and term not in {"language", "concept"}
        }
        checks.append(
            (
                "acceptance criteria acknowledged",
                bool(criteria_terms and any(term in user_text for term in criteria_terms)),
            )
        )
    correct = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    score = len(correct) / len(checks)
    return _result(
        score=score,
        correct_points=correct,
        missing_points=missing,
        feedback="Mini task proof needs a solution and a short explanation of how it satisfies the task.",
        remedial_question="Can you show your solution and briefly explain why it satisfies the acceptance criteria?",
    )


def _evaluate_reflection(answer: str) -> dict[str, Any]:
    normalized = _normalize(answer)
    checks = [
        ("understanding stated", _has_any(normalized, {"understand", "learned", "paham", "mengerti", "i can"})),
        ("confusion or confidence noted", _has_any(normalized, {"confusing", "confused", "bingung", "clear", "unclear", "still"})),
        ("use case connected", _has_any(normalized, {"use", "backend", "api", "route", "test", "service", "project"})),
    ]
    correct = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    length_bonus = 0.2 if len(answer.split()) >= 18 else 0.0
    score = min(1.0, len(correct) / len(checks) + length_bonus)
    return _result(
        score=score,
        correct_points=correct,
        missing_points=missing,
        feedback="Reflection should capture what you understood, what is still unclear, and where you would use it.",
        remedial_question="What did you understand, what is still confusing, and where would this appear in backend work?",
    )


def _evaluate_review(answer: str, code: str) -> dict[str, Any]:
    score = 0.8 if len(f"{answer}\n{code}".split()) >= 12 else 0.3
    return _result(
        score=score,
        correct_points=["review response submitted"] if score >= 0.7 else [],
        missing_points=[] if score >= 0.7 else ["Add more detail to repair the weak point."],
        feedback="Review proof checks that you can revisit and repair a weak point.",
        remedial_question="Can you explain the corrected concept with one example?",
    )


def _result(
    score: float,
    correct_points: list[str],
    missing_points: list[str],
    feedback: str,
    remedial_question: str,
) -> dict[str, Any]:
    if score >= 0.85:
        proof_status = ProofStatus.strong
        score_label = ScoreLabel.strong
    elif score >= 0.7:
        proof_status = ProofStatus.passed
        score_label = ScoreLabel.stable
    elif score > 0:
        proof_status = ProofStatus.needs_revision
        score_label = ScoreLabel.weak
    else:
        proof_status = ProofStatus.needs_revision
        score_label = ScoreLabel.incorrect
    return {
        "status": proof_status,
        "score_label": score_label,
        "score_numeric": round(score, 2),
        "feedback_json": {
            "correct_points": correct_points,
            "missing_points": missing_points,
            "feedback": feedback,
            "remedial_question": remedial_question,
        },
    }


def _apply_proof_to_progress(
    db: Session,
    user: User,
    lesson: Lesson,
    submission: UserProofSubmission,
    question: Question | None,
    debug_task: DebugTask | None,
    mini_task: MiniTask | None,
) -> UserLessonProgress:
    progress = get_or_create_progress(db, user.id, lesson.id)
    passed = submission.status in PASSING_STATUSES

    if passed:
        _record_passed_proof(db, user, lesson, submission, progress, question, debug_task, mini_task)
    else:
        _record_weak_proof(db, user, lesson, submission, question, debug_task, mini_task)

    progress.review_required = _has_latest_failed_proof(db, user, lesson.id) or (
        progress.quick_check_score is not None and progress.quick_check_score < 0.8
    )
    recompute_progress(progress)
    user.last_activity_at = datetime.now(timezone.utc)
    return progress


def _record_passed_proof(
    db: Session,
    user: User,
    lesson: Lesson,
    submission: UserProofSubmission,
    progress: UserLessonProgress,
    question: Question | None,
    debug_task: DebugTask | None,
    mini_task: MiniTask | None,
) -> None:
    if submission.proof_type == ProofType.explain_back:
        progress.explain_back_submitted = True
        progress.explain_back_score = submission.score_numeric
    elif submission.proof_type == ProofType.debug_task:
        progress.debug_task_completed = True
    elif submission.proof_type == ProofType.mini_task:
        progress.mini_task_completed = True
    elif submission.proof_type == ProofType.reflection:
        progress.reflection_submitted = True

    for tag in _related_tags(lesson, question, debug_task, mini_task):
        update_concept_mastery(db, user, tag, is_correct=True)
        reinforce_existing_review(
            db,
            user=user,
            concept_tag=tag,
            lesson=lesson,
            question=question,
            reason="Proof submission repaired this weak point; schedule later reinforcement.",
            debug_task=debug_task,
            mini_task=mini_task,
            proof_submission=submission,
        )


def _record_weak_proof(
    db: Session,
    user: User,
    lesson: Lesson,
    submission: UserProofSubmission,
    question: Question | None,
    debug_task: DebugTask | None,
    mini_task: MiniTask | None,
) -> None:
    related_tags = _related_tags(lesson, question, debug_task, mini_task)
    if not related_tags:
        schedule_review(
            db,
            user=user,
            concept_tag=None,
            lesson=lesson,
            question=question,
            reason=_review_reason(submission),
            is_correct=False,
            debug_task=debug_task,
            mini_task=mini_task,
            proof_submission=submission,
        )
        return

    for tag in related_tags:
        update_concept_mastery(db, user, tag, is_correct=False)
        schedule_review(
            db,
            user=user,
            concept_tag=tag,
            lesson=lesson,
            question=question,
            reason=_review_reason(submission),
            is_correct=False,
            debug_task=debug_task,
            mini_task=mini_task,
            proof_submission=submission,
        )


def _review_reason(submission: UserProofSubmission) -> str:
    feedback = submission.feedback_json or {}
    missing = feedback.get("missing_points") or []
    summary = "; ".join(missing) if missing else "Proof needs revision."
    return f"{submission.proof_type.value} proof needs revision: {summary}"


def _has_latest_failed_proof(db: Session, user: User, lesson_id: int) -> bool:
    rows = list(
        db.scalars(
            select(UserProofSubmission)
            .where(
                UserProofSubmission.user_id == user.id,
                UserProofSubmission.lesson_id == lesson_id,
            )
            .order_by(UserProofSubmission.created_at.desc(), UserProofSubmission.id.desc())
        )
    )
    latest: dict[tuple, UserProofSubmission] = {}
    for row in rows:
        key = (row.proof_type, row.question_id, row.debug_task_id, row.mini_task_id)
        latest.setdefault(key, row)
    return any(row.status not in PASSING_STATUSES for row in latest.values())


def has_latest_failed_proof(db: Session, user: User, lesson_id: int) -> bool:
    return _has_latest_failed_proof(db, user, lesson_id)


def _related_tags(
    lesson: Lesson,
    question: Question | None,
    debug_task: DebugTask | None,
    mini_task: MiniTask | None,
):
    if question and question.concept_tags:
        return list(question.concept_tags)
    if debug_task and debug_task.concept_tag:
        return [debug_task.concept_tag]
    if mini_task and mini_task.concept_tag:
        return [mini_task.concept_tag]
    return list(lesson.concept_tags)


def _load_published_lesson(db: Session, lesson_id: int) -> Lesson:
    lesson = db.scalar(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(
            selectinload(Lesson.concept_tags),
            selectinload(Lesson.questions).selectinload(Question.concept_tags),
            selectinload(Lesson.debug_tasks).selectinload(DebugTask.concept_tag),
            selectinload(Lesson.mini_tasks).selectinload(MiniTask.concept_tag),
        )
    )
    if not lesson or lesson.content_status != ContentStatus.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


def _load_question(db: Session, lesson: Lesson, payload: ProofSubmissionRequest) -> Question | None:
    if payload.proof_type != ProofType.explain_back:
        return None
    question = None
    if payload.question_id:
        question = db.get(Question, payload.question_id)
    else:
        question = next(
            (
                item
                for item in lesson.questions
                if item.question_type == QuestionType.explain_back
                and item.content_status == ContentStatus.published
            ),
            None,
        )
    if not question or question.lesson_id != lesson.id or question.content_status != ContentStatus.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Explain-back question not found")
    return question


def _load_debug_task(db: Session, lesson: Lesson, payload: ProofSubmissionRequest) -> DebugTask | None:
    if payload.proof_type != ProofType.debug_task:
        return None
    task = db.get(DebugTask, payload.debug_task_id) if payload.debug_task_id else next(
        (item for item in lesson.debug_tasks if item.content_status == ContentStatus.published),
        None,
    )
    if not task or task.lesson_id != lesson.id or task.content_status != ContentStatus.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debug task not found")
    return task


def _load_mini_task(db: Session, lesson: Lesson, payload: ProofSubmissionRequest) -> MiniTask | None:
    if payload.proof_type != ProofType.mini_task:
        return None
    task = db.get(MiniTask, payload.mini_task_id) if payload.mini_task_id else next(
        (item for item in lesson.mini_tasks if item.content_status == ContentStatus.published),
        None,
    )
    if not task or task.lesson_id != lesson.id or task.content_status != ContentStatus.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mini task not found")
    return task


def _next_attempt_number(
    db: Session,
    user: User,
    lesson_id: int,
    proof_type: ProofType,
    question_id: int | None,
    debug_task_id: int | None,
    mini_task_id: int | None,
) -> int:
    count = db.scalar(
        select(func.count(UserProofSubmission.id)).where(
            UserProofSubmission.user_id == user.id,
            UserProofSubmission.lesson_id == lesson_id,
            UserProofSubmission.proof_type == proof_type,
            UserProofSubmission.question_id == question_id,
            UserProofSubmission.debug_task_id == debug_task_id,
            UserProofSubmission.mini_task_id == mini_task_id,
        )
    )
    return int(count or 0) + 1


def _missing(key: str, label: str, status_value: str, detail: str) -> dict[str, str]:
    return {
        "key": key,
        "label": label,
        "status": status_value,
        "detail": detail,
    }


def _normalize(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _has_any(value: str, terms: set[str]) -> bool:
    return any(term in value for term in terms)
