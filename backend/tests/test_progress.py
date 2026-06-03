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

    debug = client.post(f"/lessons/{lesson_id}/complete-debug-task", headers=learner_headers)
    assert debug.json()["progress"]["status"] == "completed"

    mini = client.post(f"/lessons/{lesson_id}/complete-mini-task", headers=learner_headers)
    assert mini.json()["progress"]["status"] == "mastered"
    assert mini.json()["progress"]["mastery_score"] >= 0.95
