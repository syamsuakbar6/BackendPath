from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import ReviewItem, UserProofSubmission
from tests.helpers import correct_option_label, first_lesson_id, first_multiple_choice_question


def _lesson(client, headers, lesson_id: int) -> dict:
    response = client.get(f"/lessons/{lesson_id}", headers=headers)
    assert response.status_code == 200
    return response.json()


def _explain_question(lesson: dict) -> dict:
    return next(item for item in lesson["questions"] if item["question_type"] == "explain_back")


def _submit(client, headers, lesson_id: int, payload: dict):
    return client.post(f"/lessons/{lesson_id}/proofs/submit", headers=headers, json=payload)


def test_submitting_empty_proof_needs_revision(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {"proof_type": "reflection", "answer_text": ""},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["submission"]["status"] == "needs_revision"
    assert body["submission"]["score_label"] == "incorrect"
    assert body["progress"]["review_required"] is True


def test_explain_back_with_expected_concepts_passes(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)
    question = _explain_question(lesson)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "explain_back",
            "question_id": question["id"],
            "answer_text": "A return value gives the caller a result that can be tested and reused in backend code.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["submission"]["status"] in {"passed", "strong"}
    assert body["progress"]["explain_back_submitted"] is True


def test_missing_expected_concepts_returns_weak_feedback(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)
    question = _explain_question(lesson)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "explain_back",
            "question_id": question["id"],
            "answer_text": "Return is useful.",
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["status"] == "needs_revision"
    assert submission["score_label"] == "weak"
    assert submission["feedback_json"]["missing_points"]


def test_debug_proof_requires_bug_cause_and_fix(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)

    weak = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "I would return the value.",
        },
    )

    assert weak.status_code == 200
    assert weak.json()["submission"]["status"] == "needs_revision"
    assert "cause explained" in weak.json()["submission"]["feedback_json"]["missing_points"]

    passed = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: it prints. Cause: the caller receives None, so the assert fails. Fix: return the value.",
        },
    )

    assert passed.status_code == 200
    assert passed.json()["submission"]["status"] in {"passed", "strong"}


def test_mini_task_proof_requires_answer_or_code(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "mini_task",
            "mini_task_id": lesson["mini_tasks"][0]["id"],
            "answer_text": "",
            "code_text": "",
        },
    )

    assert response.status_code == 200
    assert response.json()["submission"]["status"] == "needs_revision"


def test_passed_proof_updates_lesson_progress(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: print hides the value. Cause: caller receives None. Fix: return the value.",
        },
    )

    assert response.status_code == 200
    assert response.json()["progress"]["debug_task_completed"] is True


def test_failed_proof_creates_review_item(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {"proof_type": "reflection", "answer_text": ""},
    )

    assert response.status_code == 200
    with SessionLocal() as db:
        reviews = db.scalars(select(ReviewItem)).all()
        submissions = db.scalars(select(UserProofSubmission)).all()
        assert reviews
        assert submissions
        assert reviews[0].proof_submission_id == submissions[0].id


def test_mastery_cannot_happen_without_proof_submissions(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    question = first_multiple_choice_question(client, learner_headers, lesson_id)

    client.post(f"/lessons/{lesson_id}/start", headers=learner_headers)
    client.post(f"/lessons/{lesson_id}/complete-reading", headers=learner_headers)
    quick = client.post(
        f"/questions/{question['id']}/answer",
        json={"answer": correct_option_label(question)},
        headers=learner_headers,
    )

    assert quick.status_code == 200
    progress = quick.json()["lesson_progress"]
    assert progress["status"] != "mastered"
    assert progress["debug_task_completed"] is False
    assert progress["mini_task_completed"] is False


def test_mastery_happens_when_required_proofs_pass_and_no_review_is_active(
    client, learner_headers
):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)
    question = first_multiple_choice_question(client, learner_headers, lesson_id)
    explain_question = _explain_question(lesson)

    client.post(f"/lessons/{lesson_id}/start", headers=learner_headers)
    client.post(f"/lessons/{lesson_id}/complete-reading", headers=learner_headers)
    client.post(
        f"/questions/{question['id']}/answer",
        json={"answer": correct_option_label(question)},
        headers=learner_headers,
    )
    _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "explain_back",
            "question_id": explain_question["id"],
            "answer_text": "A return value gives the caller something testable to reuse in backend code.",
        },
    )
    _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: it prints the total. Cause: caller receives None. Fix: return the total value.",
        },
    )
    final = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "mini_task",
            "mini_task_id": lesson["mini_tasks"][0]["id"],
            "code_text": "def build_message(name):\n    return f'Welcome, {name}'",
            "answer_text": "This uses the concept intentionally and gives a backend route a returned string it can reuse.",
        },
    )

    progress = final.json()["progress"]
    assert progress["status"] == "mastered"
    assert progress["review_required"] is False
