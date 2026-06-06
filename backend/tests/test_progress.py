from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import ReviewItem
from tests.helpers import (
    correct_option_label,
    first_lesson_id,
    first_multiple_choice_question,
)


def test_reading_completion_does_not_create_mastery(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)

    start_response = client.post(f"/lessons/{lesson_id}/start", headers=learner_headers)
    assert start_response.status_code == 200

    reading_response = client.post(
        f"/lessons/{lesson_id}/complete-reading",
        headers=learner_headers,
    )

    assert reading_response.status_code == 200
    progress = reading_response.json()["progress"]
    assert progress["reading_completed"] is True
    assert progress["mastery_score"] == 0.15
    assert progress["status"] == "in_progress"


def test_wrong_answer_returns_repair_feedback_and_schedules_review(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    question = first_multiple_choice_question(client, learner_headers, lesson_id)

    response = client.post(
        f"/questions/{question['id']}/answer",
        json={"answer": "A"},
        headers=learner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["feedback"]["is_correct"] is False
    assert body["feedback"]["what_part_is_wrong"]
    assert body["feedback"]["why_it_is_wrong"]
    assert body["feedback"]["correct_concept"]
    assert body["feedback"]["simple_example"]
    assert body["feedback"]["remedial_question"]
    assert body["feedback"]["review_scheduled"] is True
    assert body["lesson_progress"]["status"] == "needs_review"

    with SessionLocal() as db:
        reviews = db.scalars(select(ReviewItem)).all()
        assert reviews
        assert reviews[0].due_for_review.date() >= datetime.now(timezone.utc).date()


def test_correct_answer_updates_progress_without_creating_new_review(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    question = first_multiple_choice_question(client, learner_headers, lesson_id)

    response = client.post(
        f"/questions/{question['id']}/answer",
        json={"answer": correct_option_label(question)},
        headers=learner_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["feedback"]["is_correct"] is True
    assert body["feedback"]["review_scheduled"] is False
    assert body["lesson_progress"]["quick_check_score"] == 1.0
    assert body["lesson_progress"]["review_required"] is False
    assert body["lesson_progress"]["status"] == "in_progress"

    with SessionLocal() as db:
        assert db.scalars(select(ReviewItem)).all() == []


def test_mastery_requires_multiple_proof_points(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    question = first_multiple_choice_question(client, learner_headers, lesson_id)

    client.post(f"/lessons/{lesson_id}/start", headers=learner_headers)
    reading = client.post(f"/lessons/{lesson_id}/complete-reading", headers=learner_headers)
    assert reading.json()["progress"]["status"] == "in_progress"

    quick = client.post(
        f"/questions/{question['id']}/answer",
        json={"answer": correct_option_label(question)},
        headers=learner_headers,
    )
    assert quick.json()["lesson_progress"]["status"] == "in_progress"

    explain = client.post(
        f"/lessons/{lesson_id}/submit-explain-back",
        json={"answer": "A return value gives the caller something testable to use."},
        headers=learner_headers,
    )
    assert explain.json()["progress"]["status"] == "completed"

    lesson = client.get(f"/lessons/{lesson_id}", headers=learner_headers).json()
    debug = client.post(
        f"/lessons/{lesson_id}/proofs/submit",
        headers=learner_headers,
        json={
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: the function prints instead of returning. Cause: the caller gets None. Fix: return the calculated value.",
        },
    )
    assert debug.json()["progress"]["status"] == "completed"

    mini = client.post(
        f"/lessons/{lesson_id}/proofs/submit",
        headers=learner_headers,
        json={
            "proof_type": "mini_task",
            "mini_task_id": lesson["mini_tasks"][0]["id"],
            "code_text": "def build_message(name):\n    return f'Welcome, {name}'",
            "answer_text": "This uses the concept intentionally and gives a backend route a returned string it can reuse.",
        },
    )
    assert mini.json()["progress"]["status"] == "mastered"
    assert mini.json()["progress"]["mastery_score"] >= 0.95


def test_explain_back_accepts_natural_reusable_language_and_repairs_review(
    client, learner_headers
):
    lesson_id = first_lesson_id(client, learner_headers)

    weak = client.post(
        f"/lessons/{lesson_id}/submit-explain-back",
        json={"answer": "Return is useful."},
        headers=learner_headers,
    )
    assert weak.status_code == 200
    assert weak.json()["progress"]["review_required"] is True

    natural = client.post(
        f"/lessons/{lesson_id}/submit-explain-back",
        json={
            "answer": (
                "With return, the function gives back a value that can be reused "
                "multiple times when another part of the program calls it. With "
                "print, the output is only visible once in the console."
            )
        },
        headers=learner_headers,
    )

    assert natural.status_code == 200
    progress = natural.json()["progress"]
    assert progress["explain_back_score"] >= 0.7
    assert progress["review_required"] is False
