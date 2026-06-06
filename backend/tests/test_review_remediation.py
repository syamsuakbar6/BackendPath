from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import ReviewItem, UserConceptMastery, UserLessonProgress
from tests.helpers import correct_option_label, first_lesson_id, first_multiple_choice_question


def _lesson(client, headers, lesson_id: int) -> dict:
    response = client.get(f"/lessons/{lesson_id}", headers=headers)
    assert response.status_code == 200
    return response.json()


def _explain_question(lesson: dict) -> dict:
    return next(item for item in lesson["questions"] if item["question_type"] == "explain_back")


def _submit_proof(client, headers, lesson_id: int, payload: dict):
    return client.post(f"/lessons/{lesson_id}/proofs/submit", headers=headers, json=payload)


def _create_weak_explain_review(client, headers) -> tuple[int, int]:
    lesson_id = first_lesson_id(client, headers)
    lesson = _lesson(client, headers, lesson_id)
    response = _submit_proof(
        client,
        headers,
        lesson_id,
        {
            "proof_type": "explain_back",
            "question_id": _explain_question(lesson)["id"],
            "answer_text": "Return is useful.",
        },
    )
    assert response.status_code == 200
    assert response.json()["progress"]["review_required"] is True
    with SessionLocal() as db:
        review = db.scalars(select(ReviewItem).order_by(ReviewItem.id.asc())).first()
        assert review
        return lesson_id, review.id


def _make_due(review_id: int) -> None:
    with SessionLocal() as db:
        review = db.get(ReviewItem, review_id)
        assert review
        review.due_for_review = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()


def _good_concept_review_answer() -> str:
    return (
        "A return value gives the caller a result it can reuse, test, and pass into an API route. "
        "Printing only shows output in the console, so backend logic cannot compose the value."
    )


def test_weak_proof_creates_review_item(client, learner_headers):
    _lesson_id, review_id = _create_weak_explain_review(client, learner_headers)

    with SessionLocal() as db:
        review = db.get(ReviewItem, review_id)
        assert review
        assert review.is_active is True
        assert review.proof_submission_id is not None


def test_due_review_appears_with_details(client, learner_headers):
    _lesson_id, review_id = _create_weak_explain_review(client, learner_headers)
    _make_due(review_id)

    response = client.get("/reviews/due", headers=learner_headers)

    assert response.status_code == 200
    body = response.json()
    assert body
    item = body[0]
    assert item["lesson_title"]
    assert item["concept"]
    assert item["reason"]
    assert item["original_answer_text"] == "Return is useful."
    assert item["missing_points"]
    assert item["remedial_question"]
    assert item["review_count"] >= 1


def test_review_submit_with_weak_answer_keeps_review_active(client, learner_headers):
    _lesson_id, review_id = _create_weak_explain_review(client, learner_headers)

    response = client.post(
        f"/reviews/{review_id}/submit",
        headers=learner_headers,
        json={"answer_text": "It is useful."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False
    assert body["status"] == "needs_revision"
    assert body["review"]["is_active"] is True
    assert body["review"]["missing_points"]


def test_review_submit_with_good_answer_resolves_review(client, learner_headers):
    _lesson_id, review_id = _create_weak_explain_review(client, learner_headers)

    response = client.post(
        f"/reviews/{review_id}/submit",
        headers=learner_headers,
        json={"answer_text": _good_concept_review_answer()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["status"] in {"passed", "strong"}
    assert body["review"]["is_active"] is False


def test_resolved_review_can_clear_lesson_review_required(client, learner_headers):
    lesson_id, review_id = _create_weak_explain_review(client, learner_headers)

    response = client.post(
        f"/reviews/{review_id}/submit",
        headers=learner_headers,
        json={"answer_text": _good_concept_review_answer()},
    )

    assert response.status_code == 200
    assert response.json()["progress"]["review_required"] is False
    with SessionLocal() as db:
        progress = db.scalar(select(UserLessonProgress).where(UserLessonProgress.lesson_id == lesson_id))
        assert progress
        assert progress.review_required is False


def test_failed_review_reschedules_due_date(client, learner_headers):
    _lesson_id, review_id = _create_weak_explain_review(client, learner_headers)
    before = datetime.now()

    response = client.post(
        f"/reviews/{review_id}/submit",
        headers=learner_headers,
        json={"answer_text": "Not sure."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False
    assert datetime.fromisoformat(body["review"]["due_for_review"]) > before
    assert body["review"]["review_count"] >= 2


def test_passed_review_updates_concept_mastery(client, learner_headers):
    _lesson_id, review_id = _create_weak_explain_review(client, learner_headers)

    response = client.post(
        f"/reviews/{review_id}/submit",
        headers=learner_headers,
        json={"answer_text": _good_concept_review_answer()},
    )

    assert response.status_code == 200
    with SessionLocal() as db:
        review = db.get(ReviewItem, review_id)
        assert review
        mastery = db.scalar(
            select(UserConceptMastery).where(
                UserConceptMastery.concept_tag_id == review.concept_tag_id
            )
        )
        assert mastery
        assert mastery.correct_count >= 1
        assert mastery.mastery_score > 0


def test_lesson_mastery_can_happen_after_review_is_resolved_and_all_proofs_pass(
    client, learner_headers
):
    lesson_id, review_id = _create_weak_explain_review(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)
    quick_question = first_multiple_choice_question(client, learner_headers, lesson_id)

    client.post(f"/lessons/{lesson_id}/start", headers=learner_headers)
    client.post(f"/lessons/{lesson_id}/complete-reading", headers=learner_headers)
    client.post(
        f"/questions/{quick_question['id']}/answer",
        json={"answer": correct_option_label(quick_question)},
        headers=learner_headers,
    )
    review = client.post(
        f"/reviews/{review_id}/submit",
        headers=learner_headers,
        json={"answer_text": _good_concept_review_answer()},
    )
    assert review.status_code == 200
    assert review.json()["progress"]["review_required"] is False

    _submit_proof(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: it prints the value. Cause: the caller gets None. Fix: return the value.",
        },
    )
    final = _submit_proof(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "mini_task",
            "mini_task_id": lesson["mini_tasks"][0]["id"],
            "code_text": "def build_message(name):\n    return f'Welcome, {name}'",
            "answer_text": (
                "This uses the return concept intentionally and gives a backend route a returned string it can reuse. "
                "It satisfies the acceptance criteria because the function returns a value, avoids print, and is easy to test."
            ),
        },
    )

    assert final.status_code == 200
    assert final.json()["progress"]["status"] == "mastered"
