from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import ReviewItem


def _first_lesson_id(client, headers):
    tracks = client.get("/tracks", headers=headers).json()
    track_id = tracks[0]["id"]
    track = client.get(f"/tracks/{track_id}", headers=headers).json()
    return track["recommended_lesson"]["id"]


def test_reading_completion_does_not_create_mastery(client, learner_headers):
    lesson_id = _first_lesson_id(client, learner_headers)

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
    lesson_id = _first_lesson_id(client, learner_headers)
    lesson = client.get(f"/lessons/{lesson_id}", headers=learner_headers).json()
    question = next(item for item in lesson["questions"] if item["question_type"] == "multiple_choice")

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
    assert body["feedback"]["remedial_question"]
    assert body["lesson_progress"]["status"] == "needs_review"

    with SessionLocal() as db:
        reviews = db.scalars(select(ReviewItem)).all()
        assert reviews
        assert reviews[0].due_for_review.date() >= datetime.now(timezone.utc).date()
