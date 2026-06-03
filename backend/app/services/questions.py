from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Question, QuestionType, User, UserQuestionAttempt
from app.services.progress import (
    reinforce_existing_review,
    schedule_review,
    score_text_against_concepts,
    update_concept_mastery,
    update_quick_check_progress,
)


def answer_question(db: Session, user: User, question_id: int, answer: Any) -> dict[str, Any]:
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    evaluation = evaluate_question(question, answer)
    review_scheduled = False

    for tag in question.concept_tags:
        update_concept_mastery(db, user, tag, evaluation["is_correct"])
        if evaluation["is_correct"]:
            review = reinforce_existing_review(
                db,
                user=user,
                concept_tag=tag,
                lesson=question.lesson,
                question=question,
                reason="Correct after review; schedule a later reinforcement.",
            )
        else:
            review = schedule_review(
                db,
                user=user,
                concept_tag=tag,
                lesson=question.lesson,
                question=question,
                reason="Incorrect answer created a weak concept review.",
                is_correct=False,
            )
        review_scheduled = review_scheduled or review is not None

    evaluation["feedback"]["review_scheduled"] = review_scheduled

    progress = update_quick_check_progress(
        db, user=user, question=question, score=evaluation["score"], is_correct=evaluation["is_correct"]
    )
    attempt = UserQuestionAttempt(
        user_id=user.id,
        question_id=question.id,
        answer={"value": answer},
        is_correct=evaluation["is_correct"],
        score=evaluation["score"],
        feedback=evaluation["feedback"],
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    if progress:
        db.refresh(progress)
    return {"attempt": attempt, "feedback": evaluation["feedback"], "progress": progress}


def evaluate_question(question: Question, answer: Any) -> dict[str, Any]:
    if question.question_type == QuestionType.multiple_choice:
        return _evaluate_multiple_choice(question, answer)
    if question.question_type == QuestionType.true_false:
        return _evaluate_true_false(question, answer)
    return _evaluate_textual(question, str(answer or ""))


def _evaluate_multiple_choice(question: Question, answer: Any) -> dict[str, Any]:
    normalized = str(answer).strip().lower()
    correct_option = next((option for option in question.options if option.is_correct), None)
    selected_option = next(
        (
            option
            for option in question.options
            if str(option.id) == normalized or option.label.lower() == normalized
        ),
        None,
    )
    is_correct = bool(correct_option and selected_option and selected_option.id == correct_option.id)
    explanation = (
        selected_option.explanation
        if selected_option
        else "That option was not available in this question."
    )
    return _build_result(
        question=question,
        is_correct=is_correct,
        score=1.0 if is_correct else 0.0,
        selected=str(answer),
        explanation=question.explanation if is_correct else explanation,
    )


def _evaluate_true_false(question: Question, answer: Any) -> dict[str, Any]:
    expected = str(question.correct_answer).strip().lower()
    normalized = str(answer).strip().lower()
    if normalized in {"true", "1", "yes"}:
        normalized = "true"
    if normalized in {"false", "0", "no"}:
        normalized = "false"
    is_correct = normalized == expected
    return _build_result(
        question=question,
        is_correct=is_correct,
        score=1.0 if is_correct else 0.0,
        selected=str(answer),
        explanation=question.explanation,
    )


def _evaluate_textual(question: Question, answer: str) -> dict[str, Any]:
    score, matched = score_text_against_concepts(answer, question.expected_concepts)
    is_correct = score >= 0.7
    missing = [
        concept
        for concept in (question.expected_concepts or [])
        if concept not in matched
    ]
    explanation = question.explanation
    if missing and not is_correct:
        explanation = f"Missing concepts: {', '.join(missing)}."
    return _build_result(
        question=question,
        is_correct=is_correct,
        score=score,
        selected=answer,
        explanation=explanation,
    )


def _build_result(
    question: Question,
    is_correct: bool,
    score: float,
    selected: str,
    explanation: str | None,
) -> dict[str, Any]:
    concept = ", ".join(tag.name for tag in question.concept_tags) or "the core concept"
    if is_correct:
        feedback = {
            "is_correct": True,
            "score": score,
            "what_part_is_wrong": None,
            "why_it_is_wrong": None,
            "correct_concept": concept,
            "simple_example": question.sample_ideal_answer
            or "You chose the option that matches the backend reasoning pattern.",
            "remedial_question": question.remedial_prompt
            or "Can you explain where this would appear in a real backend endpoint?",
            "explanation": explanation,
            "review_scheduled": False,
        }
    else:
        feedback = {
            "is_correct": False,
            "score": score,
            "what_part_is_wrong": f"Your answer focused on `{selected}`.",
            "why_it_is_wrong": explanation
            or "It does not match the behavior this backend concept is meant to protect.",
            "correct_concept": concept,
            "simple_example": question.sample_ideal_answer
            or "Prefer returning values from backend logic so routes, tests, and callers can use the result.",
            "remedial_question": question.remedial_prompt
            or "What would break if another function needed to reuse this result?",
            "explanation": question.explanation,
            "review_scheduled": False,
        }
    return {"is_correct": is_correct, "score": score, "feedback": feedback}
