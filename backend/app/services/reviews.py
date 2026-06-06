from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ContentStatus,
    DebugTask,
    Lesson,
    MiniTask,
    ProofStatus,
    ProofType,
    Question,
    ReviewItem,
    ScoreLabel,
    SkillStrength,
    User,
    UserConceptMastery,
    UserLessonProgress,
)
from app.schemas.progress import ReviewSubmissionRequest
from app.services.progress import (
    get_or_create_progress,
    lesson_has_due_review,
    recompute_progress,
    score_text_against_concepts,
    serialize_review_item,
    update_concept_mastery,
    utc_now,
)
from app.services.proofs import PASSING_STATUSES, evaluate_proof, has_latest_failed_proof


def submit_review_answer(
    db: Session,
    user: User,
    review_id: int,
    payload: ReviewSubmissionRequest,
) -> dict[str, Any]:
    review = _load_review(db, user, review_id)
    lesson = review.lesson
    if not lesson or lesson.content_status != ContentStatus.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    evaluation = _evaluate_review_answer(review, payload)
    passed = evaluation["status"] in PASSING_STATUSES
    progress = get_or_create_progress(db, user.id, lesson.id)
    now = utc_now()
    next_due_for_review = None

    review.last_reviewed_at = now
    review.review_count += 1

    if passed:
        _record_passed_review(db, user, review, evaluation)
        next_due_for_review = _next_due_after_pass(db, user, review, evaluation)
        if next_due_for_review is None:
            review.is_active = False
        else:
            review.is_active = True
            review.due_for_review = next_due_for_review
        review.reason = "Review answer repaired the weak point."
    else:
        review.is_active = True
        review.due_for_review = now + timedelta(days=1)
        review.reason = _failed_reason(evaluation)

    _sync_progress_after_review(db, user, progress)
    user.last_activity_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    db.refresh(progress)

    return {
        "review": serialize_review_item(review),
        "passed": passed,
        "status": evaluation["status"],
        "score_label": evaluation["score_label"],
        "score_numeric": evaluation["score_numeric"],
        "feedback_json": evaluation["feedback_json"],
        "progress": progress,
        "next_due_for_review": next_due_for_review,
        "message": "Review resolved." if passed and not review.is_active else "Review rescheduled.",
    }


def _load_review(db: Session, user: User, review_id: int) -> ReviewItem:
    review = db.scalar(
        select(ReviewItem)
        .where(ReviewItem.id == review_id, ReviewItem.user_id == user.id, ReviewItem.is_active.is_(True))
        .options(
            selectinload(ReviewItem.concept_tag),
            selectinload(ReviewItem.lesson).selectinload(Lesson.concept_tags),
            selectinload(ReviewItem.question).selectinload(Question.concept_tags),
            selectinload(ReviewItem.debug_task).selectinload(DebugTask.concept_tag),
            selectinload(ReviewItem.mini_task).selectinload(MiniTask.concept_tag),
            selectinload(ReviewItem.proof_submission),
        )
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


def _evaluate_review_answer(review: ReviewItem, payload: ReviewSubmissionRequest) -> dict[str, Any]:
    answer = (payload.answer_text or "").strip()
    code = (payload.code_text or "").strip()
    proof_type = review.proof_submission.proof_type if review.proof_submission else None

    if proof_type == ProofType.debug_task or review.debug_task_id:
        return evaluate_proof(
            proof_type=ProofType.debug_task,
            lesson=review.lesson,
            question=review.question,
            debug_task=review.debug_task,
            mini_task=review.mini_task,
            answer_text=answer,
            code_text=code,
        )
    if proof_type == ProofType.mini_task or review.mini_task_id:
        return evaluate_proof(
            proof_type=ProofType.mini_task,
            lesson=review.lesson,
            question=review.question,
            debug_task=review.debug_task,
            mini_task=review.mini_task,
            answer_text=answer,
            code_text=code,
        )
    return _evaluate_concept_review(review, answer, code)


def _evaluate_concept_review(review: ReviewItem, answer: str, code: str) -> dict[str, Any]:
    combined = f"{answer}\n{code}".strip()
    if len(combined) < 12:
        return _result(
            score=0.0,
            correct_points=[],
            missing_points=["Write a focused answer before this review can be resolved."],
            feedback="A review answer should repair the weak idea, not just acknowledge it.",
            remedial_question="Can you explain the corrected concept with one small backend example?",
        )

    expected = _expected_review_concepts(review)
    score, matched = score_text_against_concepts(combined, expected)
    missing = [concept for concept in expected if concept not in matched]
    if not expected and len(_normalize(combined).split()) >= 14:
        score = 0.75

    if score >= 0.85:
        feedback = "Your review answer repairs the weak concept and connects it back to practice."
    elif score >= 0.7:
        feedback = "Your review answer repairs the main weak concept."
    else:
        feedback = "This still misses one or more concepts from the previous feedback."

    return _result(
        score=score,
        correct_points=[f"Recovered concept: {concept}" for concept in matched],
        missing_points=[f"Still missing: {concept}" for concept in missing],
        feedback=feedback,
        remedial_question=_remedial_question(review),
    )


def _expected_review_concepts(review: ReviewItem) -> list[str]:
    concepts: list[str] = []
    feedback = review.proof_submission.feedback_json if review.proof_submission else None
    for point in (feedback or {}).get("missing_points", []):
        cleaned = re.sub(r"^(missing concept|still missing):\s*", "", str(point), flags=re.I).strip()
        if cleaned and cleaned not in concepts:
            concepts.append(cleaned)
    if review.question and review.question.expected_concepts:
        for concept in review.question.expected_concepts:
            if concept not in concepts:
                concepts.append(concept)
    if review.concept_tag and review.concept_tag.name not in concepts:
        concepts.append(review.concept_tag.name)
    return concepts


def _record_passed_review(
    db: Session,
    user: User,
    review: ReviewItem,
    evaluation: dict[str, Any],
) -> None:
    if review.concept_tag:
        update_concept_mastery(db, user, review.concept_tag, is_correct=True)

    submission = review.proof_submission
    if submission:
        submission.status = evaluation["status"]
        submission.score_label = evaluation["score_label"]
        submission.score_numeric = evaluation["score_numeric"]
        submission.feedback_json = evaluation["feedback_json"]
        submission.evaluated_at = utc_now()
        _apply_repaired_submission(review, submission)
        _resolve_sibling_reviews(db, user, review, submission.id)


def _apply_repaired_submission(review: ReviewItem, submission) -> None:
    progress = review.lesson and next(
        (item for item in review.lesson.progress if item.user_id == review.user_id),
        None,
    )
    if not progress:
        return
    if submission.proof_type == ProofType.explain_back:
        progress.explain_back_submitted = True
        progress.explain_back_score = submission.score_numeric
    elif submission.proof_type == ProofType.debug_task:
        progress.debug_task_completed = True
    elif submission.proof_type == ProofType.mini_task:
        progress.mini_task_completed = True
    elif submission.proof_type == ProofType.reflection:
        progress.reflection_submitted = True


def _resolve_sibling_reviews(
    db: Session,
    user: User,
    review: ReviewItem,
    proof_submission_id: int,
) -> None:
    siblings = db.scalars(
        select(ReviewItem).where(
            ReviewItem.user_id == user.id,
            ReviewItem.proof_submission_id == proof_submission_id,
            ReviewItem.id != review.id,
            ReviewItem.is_active.is_(True),
        )
    ).all()
    for sibling in siblings:
        sibling.is_active = False
        sibling.last_reviewed_at = utc_now()
        sibling.reason = "Review answer repaired the weak proof that created this item."


def _next_due_after_pass(
    db: Session,
    user: User,
    review: ReviewItem,
    evaluation: dict[str, Any],
) -> datetime | None:
    if evaluation["score_label"] == ScoreLabel.strong:
        return None

    if review.concept_tag_id:
        mastery = db.scalar(
            select(UserConceptMastery).where(
                UserConceptMastery.user_id == user.id,
                UserConceptMastery.concept_tag_id == review.concept_tag_id,
            )
        )
        if mastery and mastery.strength == SkillStrength.weak:
            return utc_now() + timedelta(days=3)
    return utc_now() + timedelta(days=7)


def _sync_progress_after_review(db: Session, user: User, progress: UserLessonProgress) -> None:
    progress.review_required = lesson_has_due_review(db, user, progress.lesson_id) or has_latest_failed_proof(
        db, user, progress.lesson_id
    )
    recompute_progress(progress)


def _failed_reason(evaluation: dict[str, Any]) -> str:
    missing = evaluation["feedback_json"].get("missing_points") or ["Review answer still needs revision."]
    return "Review answer needs revision: " + "; ".join(missing)


def _remedial_question(review: ReviewItem) -> str:
    feedback = review.proof_submission.feedback_json if review.proof_submission else None
    if feedback and feedback.get("remedial_question"):
        return feedback["remedial_question"]
    if review.question and review.question.remedial_prompt:
        return review.question.remedial_prompt
    if review.debug_task and review.debug_task.hint:
        return review.debug_task.hint
    return "Can you explain the corrected concept with one small backend example?"


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


def _normalize(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", normalized).strip()
