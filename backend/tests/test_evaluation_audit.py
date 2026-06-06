from tests.helpers import first_lesson_id


def _lesson(client, headers, lesson_id: int) -> dict:
    response = client.get(f"/lessons/{lesson_id}", headers=headers)
    assert response.status_code == 200
    return response.json()


def _explain_question(lesson: dict) -> dict:
    return next(item for item in lesson["questions"] if item["question_type"] == "explain_back")


def _submit(client, headers, lesson_id: int, payload: dict):
    response = client.post(f"/lessons/{lesson_id}/proofs/submit", headers=headers, json=payload)
    assert response.status_code == 200
    return response.json()["submission"]


def test_evaluator_confidence_for_strong_explain_back(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)
    question = _explain_question(lesson)

    submission = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "explain_back",
            "question_id": question["id"],
            "answer_text": (
                "A return value gives the caller a reusable result, so an API route can pass it "
                "into another function and tests can assert the returned value instead of reading "
                "printed console output."
            ),
        },
    )

    assert submission["status"] in {"passed", "strong"}
    assert submission["evaluation_confidence"] == "high"
    assert submission["final_evaluation_status"] == "accepted"
    assert submission["heuristic_status"] == submission["status"]
    assert submission["heuristic_feedback_json"]["evaluation_source"] == "heuristic"


def test_borderline_debug_case_is_low_confidence_and_needs_review(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)

    submission = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: it prints the result. Fix: return the value.",
        },
    )

    assert submission["status"] == "needs_revision"
    assert submission["evaluation_confidence"] == "low"
    assert submission["final_evaluation_status"] == "needs_review"
    assert "cause explained" in submission["feedback_json"]["missing_points"]


def test_admin_override_endpoint_updates_final_evaluation(client, learner_headers, admin_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)
    weak_submission = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: it prints the result. Fix: return the value.",
        },
    )

    response = client.patch(
        f"/admin/proof-submissions/{weak_submission['id']}/override",
        headers=admin_headers,
        json={
            "final_status": "accepted",
            "score_label": "stable",
            "override_note": "Manual review accepted the explanation for this MVP sample.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "passed"
    assert body["final_evaluation_status"] == "accepted"
    assert body["final_score_label"] == "stable"
    assert body["override_note"] == "Manual review accepted the explanation for this MVP sample."
    assert body["overridden_by_email"] == "admin@example.com"
    assert body["final_feedback_json"]["evaluation_source"] == "admin_override"


def test_admin_override_preserves_original_heuristic_result(client, learner_headers, admin_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)
    weak_submission = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: it prints the result. Fix: return the value.",
        },
    )

    response = client.patch(
        f"/admin/proof-submissions/{weak_submission['id']}/override",
        headers=admin_headers,
        json={
            "final_status": "accepted",
            "score_label": "strong",
            "override_note": "Accepted after inspecting the learner's intent.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["heuristic_status"] == "needs_revision"
    assert body["heuristic_score_label"] == "weak"
    assert "cause explained" in body["heuristic_feedback_json"]["missing_points"]
    assert body["final_evaluation_status"] == "accepted"
    assert body["final_score_label"] == "strong"
    assert body["final_feedback_json"]["evaluation_source"] == "admin_override"


def test_admin_proof_evaluation_analytics(client, learner_headers, admin_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)
    question = _explain_question(lesson)

    strong_submission = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "explain_back",
            "question_id": question["id"],
            "answer_text": (
                "Return gives the caller a reusable value, lets an API route compose that value, "
                "and allows tests to assert the returned result instead of reading print output."
            ),
        },
    )
    _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: it prints the result. Fix: return the value.",
        },
    )
    _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "explain_back",
            "question_id": question["id"],
            "answer_text": (
                "Print and return are the same because print returns values to the API caller "
                "and makes the value reusable."
            ),
        },
    )
    override = client.patch(
        f"/admin/proof-submissions/{strong_submission['id']}/override",
        headers=admin_headers,
        json={
            "final_status": "accepted",
            "override_note": "Admin confirms this strong proof.",
        },
    )
    assert override.status_code == 200

    response = client.get("/admin/proof-evaluation-analytics", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_submissions"] == 3
    assert body["count_by_proof_type"]["explain_back"] == 2
    assert body["count_by_proof_type"]["debug_task"] == 1
    assert body["count_by_final_status"]["accepted"] >= 1
    assert body["count_by_final_status"]["needs_review"] >= 1
    assert body["count_by_confidence"]["low"] >= 1
    assert body["count_by_confidence"]["high"] >= 1
    assert body["override_count"] == 1
    assert body["override_rate"] > 0
    assert body["top_lessons_with_rejected_or_needs_review"]
    assert body["top_misconceptions"]
