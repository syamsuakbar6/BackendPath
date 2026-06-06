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
    EvaluationConfidence,
    Lesson,
    MiniTask,
    ProofFinalStatus,
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

BACKEND_CONTEXT_TERMS = {
    "api",
    "route",
    "backend",
    "caller",
    "function",
    "service",
    "test",
    "assert",
    "reuse",
    "reusable",
    "permission",
    "identity",
    "request",
    "response",
}
EXPLANATION_TERMS = {
    "because",
    "why",
    "so",
    "therefore",
    "means",
    "allows",
    "causes",
    "happens",
    "breaks",
    "fix",
    "prevents",
}
GENERIC_REFLECTIONS = {
    "i understand",
    "i know now",
    "nothing confusing",
    "all clear",
    "i get it",
    "understand now",
}
COMMON_MISCONCEPTIONS = [
    (
        "Treats print and return as interchangeable.",
        {"print and return are same", "print and return are the same", "print is same as return", "same as return"},
    ),
    (
        "Treats visible output as reusable backend data.",
        {"print is enough", "printed value can be reused", "console output can be reused", "print returns"},
    ),
    (
        "Confuses identity with permission.",
        {"authentication gives permission", "login means allowed", "authenticated means authorized"},
    ),
    (
        "Reverses 401 and 403.",
        {"401 means forbidden", "403 means not logged in", "403 means unauthenticated"},
    ),
]


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
        heuristic_status=evaluation["status"],
        heuristic_score_label=evaluation["score_label"],
        heuristic_score_numeric=evaluation["score_numeric"],
        heuristic_feedback_json=evaluation["feedback_json"],
        evaluation_confidence=evaluation["confidence"],
        final_evaluation_status=final_status_from_evaluation(evaluation),
        final_score_label=evaluation["score_label"],
        final_score_numeric=evaluation["score_numeric"],
        final_feedback_json=evaluation["feedback_json"],
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
        return _evaluate_reflection(lesson, answer)
    if proof_type == ProofType.review:
        return _evaluate_review(answer, code)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported proof type")


def final_status_from_evaluation(evaluation: dict[str, Any]) -> ProofFinalStatus:
    if evaluation["status"] in PASSING_STATUSES:
        return ProofFinalStatus.accepted
    if evaluation["score_label"] == ScoreLabel.incorrect and evaluation["confidence"] == EvaluationConfidence.high:
        return ProofFinalStatus.rejected
    return ProofFinalStatus.needs_review


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
            feedback = (
                submission.feedback_json.get("feedback", f"Revise the {label.lower()}.")
                if submission.feedback_json
                else f"Revise the {label.lower()}."
            )
            items.append(
                _missing(
                    proof_type.value,
                    label,
                    "weak",
                    f"{label} is weak: {feedback}",
                )
            )
    if progress.review_required:
        items.append(_missing("review_required", "Review", "needs_review", "Review still active: repair weak proof or concept review items."))
    return items


def _evaluate_explain_back(question: Question | None, answer: str) -> dict[str, Any]:
    return evaluate_conceptual_answer(
        answer=answer,
        expected_concepts=question.expected_concepts if question else None,
        remedial_question=question.remedial_prompt if question and question.remedial_prompt else "What would this change in a real API route?",
        misconception_notes=question.misconception_notes if question else None,
        passing_feedback="Your explanation connects the concept to enough expected ideas and backend consequence.",
        weak_feedback="Your explanation needs more expected concepts, specificity, and backend consequence.",
    )


def _evaluate_debug(debug_task: DebugTask | None, answer: str, code: str) -> dict[str, Any]:
    combined = _normalize(f"{answer}\n{code}")
    answer_normalized = _normalize(answer)
    quality = _quality_issues(answer, code, min_words=8)
    misconceptions = _detect_misconceptions(f"{answer}\n{code}")
    explanation_present = _word_count(answer) >= 8 or _has_any(
        answer_normalized,
        {"bug", "cause", "because", "why", "fix", "happens", "wrong"},
    )
    code_clearly_fixes = bool(code.strip()) and _has_any(
        _normalize(code),
        {"return", "raise", "401", "403", "false", "true"},
    )
    checks = [
        (
            "bug identified",
            _has_any(combined, {"bug", "broken", "problem", "issue", "fails", "wrong", "none", "reversed"})
            or _has_any(combined, {"prints instead", "returns none", "permission missing"}),
        ),
        (
            "cause explained",
            _has_any(combined, {"because", "cause", "caused", "why", "happens", "caller", "assert", "permission", "identity"})
            and _has_any(combined, {"none", "print", "fails", "hidden", "wrong", "reversed", "denied", "unauthenticated"}),
        ),
        (
            "fix proposed",
            _has_any(combined, {"fix", "change", "replace", "return", "should", "correct", "swap", "check"})
            or code_clearly_fixes,
        ),
        ("explanation provided", explanation_present),
    ]
    correct = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    score = len(correct) / len(checks)
    core_missing = any(label in missing for label in {"bug identified", "cause explained", "fix proposed"})
    if core_missing:
        score = min(score, 0.65)
    if code and not explanation_present:
        score = min(score, 0.55)
        missing.append("explanation must accompany code")
    if quality:
        score = min(score, 0.35)
        missing.extend(quality)
    if misconceptions:
        score = min(score, 0.4)
    return _result(
        score=score,
        correct_points=correct,
        missing_points=missing,
        misconceptions=misconceptions,
        feedback="Debug proof should name the bug, explain the cause, and propose a fix.",
        remedial_question=debug_task.hint if debug_task and debug_task.hint else "What exactly breaks, why does it break, and what would you change?",
    )


def _evaluate_mini_task(mini_task: MiniTask | None, answer: str, code: str) -> dict[str, Any]:
    quality = _quality_issues(answer, code, min_words=8)
    misconceptions = _detect_misconceptions(f"{answer}\n{code}")
    criteria = mini_task.acceptance_criteria if mini_task else None
    criteria_match = _criteria_match(criteria, f"{answer}\n{code}")
    code_required = _mini_task_requires_code(mini_task)
    explanation_present = _word_count(answer) >= 12 and _has_any(
        _normalize(answer),
        EXPLANATION_TERMS | {"works", "satisfies", "meets", "allows", "use", "backend"},
    )
    checks = [
        ("solution or code provided", bool(code) or len(answer) >= 20),
        ("short explanation provided", explanation_present),
        ("acceptance criteria connected", criteria_match if criteria else True),
    ]
    if code_required:
        checks.append(("code provided for code-required task", bool(code.strip())))
    correct = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    score = len(correct) / len(checks)
    if code_required and not code.strip():
        score = min(score, 0.65)
    if quality:
        score = min(score, 0.35)
        missing.extend(quality)
    if misconceptions:
        score = min(score, 0.4)
    return _result(
        score=score,
        correct_points=correct,
        missing_points=missing,
        misconceptions=misconceptions,
        feedback="Mini task proof needs a solution and a short explanation of how it satisfies the task.",
        remedial_question="Can you show your solution and briefly explain why it satisfies the acceptance criteria?",
    )


def _evaluate_reflection(lesson: Lesson, answer: str) -> dict[str, Any]:
    normalized = _normalize(answer)
    quality = _quality_issues(answer, None, min_words=8)
    concept_terms = _lesson_concept_terms(lesson)
    generic = any(phrase == normalized or phrase in normalized for phrase in GENERIC_REFLECTIONS)
    checks = [
        (
            "specific concept learned",
            _has_any(normalized, {"learned", "understand", "paham", "mengerti", "i can"})
            and _has_any(normalized, concept_terms),
        ),
        ("confusion or confidence noted", _has_any(normalized, {"confusing", "confused", "bingung", "clear", "unclear", "still", "not confusing", "nothing confusing"})),
        ("use case connected", _has_any(normalized, {"use", "backend", "api", "route", "test", "service", "project"})),
    ]
    correct = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    length_bonus = 0.15 if len(answer.split()) >= 18 else 0.0
    score = min(1.0, len(correct) / len(checks) + length_bonus)
    misconceptions = _detect_misconceptions(answer)
    if generic:
        score = min(score, 0.35)
        missing.append("reflection is too generic")
    if quality:
        score = min(score, 0.35)
        missing.extend(quality)
    if misconceptions:
        score = min(score, 0.4)
    return _result(
        score=score,
        correct_points=correct,
        missing_points=missing,
        misconceptions=misconceptions,
        feedback="Reflection should capture what you understood, what is still unclear, and where you would use it.",
        remedial_question="What did you understand, what is still confusing, and where would this appear in backend work?",
    )


def _evaluate_review(answer: str, code: str) -> dict[str, Any]:
    quality = _quality_issues(answer, code, min_words=10)
    misconceptions = _detect_misconceptions(f"{answer}\n{code}")
    normalized = _normalize(f"{answer}\n{code}")
    has_repair_signal = _has_any(normalized, {"because", "fix", "correct", "return", "caller", "permission", "401", "403", "test"})
    score = 0.8 if len(f"{answer}\n{code}".split()) >= 12 and has_repair_signal else 0.35
    if quality:
        score = min(score, 0.35)
    if misconceptions:
        score = min(score, 0.4)
    return _result(
        score=score,
        correct_points=["review response submitted"] if score >= 0.7 else [],
        missing_points=[] if score >= 0.7 else ["Add more detail to repair the weak point.", *quality],
        misconceptions=misconceptions,
        feedback="Review proof checks that you can revisit and repair a weak point.",
        remedial_question="Can you explain the corrected concept with one example?",
    )


def evaluate_conceptual_answer(
    answer: str,
    expected_concepts: list[str] | None,
    remedial_question: str,
    misconception_notes: str | None = None,
    passing_feedback: str = "Your answer repairs the weak concept.",
    weak_feedback: str = "Your answer still misses one or more expected concepts.",
) -> dict[str, Any]:
    expected = expected_concepts or []
    required = _required_concept_count(len(expected))
    score, matched = score_text_against_concepts(answer, expected)
    missing_concepts = [concept for concept in expected if concept not in matched]
    normalized = _normalize(answer)
    quality = _quality_issues(answer, None, min_words=10)
    keyword_only = _looks_keyword_only(answer, expected)
    misconceptions = _detect_misconceptions(answer, misconception_notes)
    has_specificity = _has_any(normalized, BACKEND_CONTEXT_TERMS) and _has_any(
        normalized, EXPLANATION_TERMS | {"reusable", "reuse", "value", "permission", "identity"}
    )

    if expected:
        coverage_score = len(matched) / len(expected)
        score = min(1.0, coverage_score * 0.75 + (0.2 if has_specificity else 0.0) + (0.05 if _word_count(answer) >= 16 else 0.0))
    elif has_specificity and _word_count(answer) >= 12:
        score = max(score, 0.75)

    if len(matched) < required:
        score = min(score, 0.65)
    if not has_specificity:
        score = min(score, 0.62)
    if keyword_only:
        score = min(score, 0.45)
        quality.append("shallow keyword-only answer")
    if quality:
        score = min(score, 0.35 if _has_spam_signal(answer) else 0.55)
    if misconceptions:
        score = min(score, 0.4)
    if expected and len(matched) == len(expected) and has_specificity and not quality and not misconceptions:
        score = 1.0

    correct = [f"Included concept: {concept}" for concept in matched]
    missing_points = [f"Missing concept: {concept}" for concept in missing_concepts]
    missing_points.extend(quality)
    if len(matched) < required and expected:
        missing_points.append(f"Needs at least {required} expected concepts explained together.")

    return _result(
        score=score,
        correct_points=correct,
        missing_points=_dedupe(missing_points),
        misconceptions=misconceptions,
        feedback=passing_feedback if score >= 0.7 else weak_feedback,
        remedial_question=remedial_question,
    )


def _result(
    score: float,
    correct_points: list[str],
    missing_points: list[str],
    feedback: str,
    remedial_question: str,
    misconceptions: list[str] | None = None,
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
        "confidence": _confidence_for_result(score, missing_points, misconceptions or []),
        "feedback_json": {
            "correct_points": correct_points,
            "missing_points": _dedupe(missing_points),
            "misconceptions": _dedupe(misconceptions or []),
            "feedback": feedback,
            "remedial_question": remedial_question,
            "evaluation_source": "heuristic",
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


def _word_count(value: str | None) -> int:
    return len(_words(value or ""))


def _confidence_for_result(
    score: float,
    missing_points: list[str],
    misconceptions: list[str],
) -> EvaluationConfidence:
    if 0.55 <= score < 0.75:
        return EvaluationConfidence.low
    if misconceptions and score >= 0.35:
        return EvaluationConfidence.low
    if any("acceptance criteria" in point or "cause explained" in point for point in missing_points) and score >= 0.5:
        return EvaluationConfidence.low
    if score >= 0.85 and not missing_points and not misconceptions:
        return EvaluationConfidence.high
    if score <= 0.25 and (
        not missing_points
        or any("empty" in point.lower() or "meaningful answer" in point.lower() for point in missing_points)
    ):
        return EvaluationConfidence.high
    return EvaluationConfidence.medium


def _words(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())


def _quality_issues(answer: str | None, code: str | None, min_words: int) -> list[str]:
    text = (answer or "").strip()
    combined = f"{answer or ''}\n{code or ''}".strip()
    issues: list[str] = []
    if _word_count(text) < min_words and _word_count(combined) < min_words:
        issues.append(f"Needs at least {min_words} meaningful words.")
    if _has_spam_signal(combined):
        issues.append("Repeated spam-like text detected.")
    if _too_many_repeated_words(combined):
        issues.append("Too many repeated words.")
    return _dedupe(issues)


def _has_spam_signal(value: str) -> bool:
    words = _words(value)
    if len(words) < 8:
        return False
    if len(set(words)) / len(words) < 0.35:
        return True
    shingles: dict[tuple[str, ...], int] = {}
    for index in range(max(0, len(words) - 2)):
        key = tuple(words[index:index + 3])
        shingles[key] = shingles.get(key, 0) + 1
    return any(count >= 3 for count in shingles.values())


def _too_many_repeated_words(value: str) -> bool:
    words = [word for word in _words(value) if len(word) >= 4]
    if len(words) < 10:
        return False
    counts: dict[str, int] = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return max(counts.values(), default=0) / len(words) > 0.35


def _looks_keyword_only(answer: str, expected_concepts: list[str] | None) -> bool:
    words = _words(answer)
    if not words:
        return True
    if len(words) > 12:
        return False
    normalized = _normalize(answer)
    has_explanation = _has_any(normalized, EXPLANATION_TERMS | BACKEND_CONTEXT_TERMS)
    if has_explanation and len(words) >= 8:
        return False
    expected_words = {
        word
        for concept in (expected_concepts or [])
        for word in _words(concept)
    }
    if expected_words and set(words).issubset(expected_words | {"and", "or", "is", "are", "the", "for"}):
        return True
    return not has_explanation


def _required_concept_count(total: int) -> int:
    if total <= 0:
        return 0
    if total <= 2:
        return total
    if total == 3:
        return 2
    return min(3, total)


def _detect_misconceptions(answer: str, misconception_notes: str | None = None) -> list[str]:
    normalized = _normalize(answer)
    misconceptions: list[str] = []
    for label, patterns in COMMON_MISCONCEPTIONS:
        if _has_any(normalized, patterns):
            misconceptions.append(label)
    notes = _normalize(misconception_notes or "")
    if "repeat vocabulary" in notes and _looks_keyword_only(answer, None):
        misconceptions.append("Repeats vocabulary without explaining the backend consequence.")
    return _dedupe(misconceptions)


def _criteria_match(criteria: list[str] | None, value: str) -> bool:
    if not criteria:
        return True
    user_text = _normalize(value)
    matched = 0
    for criterion in criteria:
        terms = {
            term
            for term in _words(criterion)
            if len(term) >= 5 and term not in {"language", "concept", "plain"}
        }
        if terms and any(term in user_text for term in terms):
            matched += 1
    required = 1 if len(criteria) <= 2 else 2
    return matched >= required


def _mini_task_requires_code(mini_task: MiniTask | None) -> bool:
    if not mini_task:
        return False
    text = _normalize(
        " ".join(
            [
                mini_task.prompt or "",
                " ".join(mini_task.acceptance_criteria or []),
            ]
        )
    )
    return _has_any(text, {"function", "code", "python", "def", "implement", "rewrite", "return the", "returns the"})


def _lesson_concept_terms(lesson: Lesson) -> set[str]:
    terms = set(BACKEND_CONTEXT_TERMS)
    for tag in lesson.concept_tags:
        terms.update(_words(tag.name))
        terms.update(_words(tag.slug))
    terms.update(_words(lesson.title))
    terms.update(_words(lesson.learning_goal))
    return {term for term in terms if len(term) >= 3}


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    output = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            output.append(item)
    return output
