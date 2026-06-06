from tests.helpers import first_lesson_id


def _lesson(client, headers, lesson_id: int) -> dict:
    response = client.get(f"/lessons/{lesson_id}", headers=headers)
    assert response.status_code == 200
    return response.json()


def _explain_question(lesson: dict) -> dict:
    return next(item for item in lesson["questions"] if item["question_type"] == "explain_back")


def _submit(client, headers, lesson_id: int, payload: dict):
    return client.post(f"/lessons/{lesson_id}/proofs/submit", headers=headers, json=payload)


def test_keyword_only_explain_back_is_weak(client, learner_headers):
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
            "answer_text": "return caller test",
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["status"] == "needs_revision"
    assert "shallow keyword-only answer" in submission["feedback_json"]["missing_points"]
    assert submission["feedback_json"]["evaluation_source"] == "heuristic"


def test_meaningful_explain_back_passes(client, learner_headers):
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
            "answer_text": (
                "A return value gives the caller a result it can reuse in an API route, "
                "and tests can assert that returned value instead of reading console output."
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["submission"]["status"] in {"passed", "strong"}


def test_repeated_spam_answer_is_weak(client, learner_headers):
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
            "answer_text": "return caller test return caller test return caller test return caller test",
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["status"] == "needs_revision"
    assert "Repeated spam-like text detected." in submission["feedback_json"]["missing_points"]


def test_debug_answer_without_cause_is_weak(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": "Bug: it prints the result. Fix: return the value.",
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["status"] == "needs_revision"
    assert "cause explained" in submission["feedback_json"]["missing_points"]


def test_debug_answer_with_bug_cause_and_fix_passes(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "debug_task",
            "debug_task_id": lesson["debug_tasks"][0]["id"],
            "answer_text": (
                "Bug: the function prints the total. Cause: the caller receives None, "
                "so the assertion fails. Fix: return the total value instead."
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["submission"]["status"] in {"passed", "strong"}


def test_mini_task_without_code_for_code_required_task_is_weak(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "mini_task",
            "mini_task_id": lesson["mini_tasks"][0]["id"],
            "answer_text": "I would return a reusable message and explain that the API route can use it.",
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["status"] == "needs_revision"
    assert "code provided for code-required task" in submission["feedback_json"]["missing_points"]


def test_mini_task_with_code_and_explanation_passes(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    lesson = _lesson(client, learner_headers, lesson_id)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "mini_task",
            "mini_task_id": lesson["mini_tasks"][0]["id"],
            "code_text": "def discount_message(name):\n    return f'Discount ready for {name}'",
            "answer_text": (
                "This satisfies the task because the function returns a value instead of printing. "
                "A backend route can reuse the returned message and tests can assert it."
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["submission"]["status"] in {"passed", "strong"}


def test_generic_reflection_is_weak(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {"proof_type": "reflection", "answer_text": "I understand"},
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["status"] == "needs_revision"
    assert "reflection is too generic" in submission["feedback_json"]["missing_points"]


def test_specific_reflection_passes(client, learner_headers):
    lesson_id = first_lesson_id(client, learner_headers)

    response = _submit(
        client,
        learner_headers,
        lesson_id,
        {
            "proof_type": "reflection",
            "answer_text": (
                "I learned that return values let backend API routes reuse a function result "
                "instead of only printing it. It is clear because tests can assert the returned "
                "value, and I would use it in service functions."
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["submission"]["status"] in {"passed", "strong"}


def test_admin_can_list_proof_submissions(client, learner_headers, admin_headers):
    lesson_id = first_lesson_id(client, learner_headers)
    _submit(
        client,
        learner_headers,
        lesson_id,
        {"proof_type": "reflection", "answer_text": "I understand"},
    )

    response = client.get("/admin/proof-submissions", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body
    assert body[0]["user"]["email"] == "learner@example.com"
    assert body[0]["lesson"]["id"] == lesson_id
    assert body[0]["feedback_json"]["evaluation_source"] == "heuristic"


def test_learner_cannot_access_admin_proof_submissions(client, learner_headers):
    response = client.get("/admin/proof-submissions", headers=learner_headers)

    assert response.status_code == 403
