def test_learner_cannot_access_admin_endpoints(client, learner_headers):
    response = client.get("/admin/languages", headers=learner_headers)
    assert response.status_code == 403


def test_admin_can_manage_content_hierarchy_and_question_options(client, admin_headers):
    language = client.post(
        "/admin/languages",
        headers=admin_headers,
        json={
            "name": "Go",
            "slug": "go",
            "description": "Go backend foundations",
            "sort_order": 5,
            "is_active": True,
        },
    )
    assert language.status_code == 201
    language_id = language.json()["id"]

    track = client.post(
        "/admin/tracks",
        headers=admin_headers,
        json={
            "language_id": language_id,
            "title": "Go Backend Junior Path",
            "slug": "go-backend-junior-path",
            "description": "Go backend track",
            "target_audience": "Junior backend developer",
            "sort_order": 1,
            "is_published": True,
        },
    )
    assert track.status_code == 201
    track_id = track.json()["id"]

    level = client.post(
        "/admin/levels",
        headers=admin_headers,
        json={
            "track_id": track_id,
            "title": "Foundation",
            "slug": "foundation",
            "description": "Go basics",
            "sort_order": 1,
        },
    )
    assert level.status_code == 201
    level_id = level.json()["id"]

    module = client.post(
        "/admin/modules",
        headers=admin_headers,
        json={
            "level_id": level_id,
            "title": "Handlers",
            "slug": "handlers",
            "description": "HTTP handler basics",
            "estimated_minutes": 20,
            "sort_order": 1,
        },
    )
    assert module.status_code == 201
    module_id = module.json()["id"]

    concept = client.post(
        "/admin/concept-tags",
        headers=admin_headers,
        json={
            "name": "Handler Return",
            "slug": "handler-return",
            "description": "Returning useful handler results.",
        },
    )
    assert concept.status_code == 201
    concept_id = concept.json()["id"]

    lesson = client.post(
        "/admin/lessons",
        headers=admin_headers,
        json={
            "module_id": module_id,
            "title": "Handler output",
            "slug": "handler-output",
            "learning_goal": "Explain handler output.",
            "why_it_matters": "Handlers must communicate clear responses.",
            "estimated_minutes": 10,
            "sort_order": 1,
            "is_published": True,
        },
    )
    assert lesson.status_code == 201
    lesson_id = lesson.json()["id"]

    block = client.post(
        "/admin/lesson-blocks",
        headers=admin_headers,
        json={
            "lesson_id": lesson_id,
            "block_type": "text",
            "title": "Concept",
            "body": "Return useful data.",
            "sort_order": 1,
        },
    )
    assert block.status_code == 201
    block_id = block.json()["id"]

    question = client.post(
        "/admin/questions",
        headers=admin_headers,
        json={
            "lesson_id": lesson_id,
            "question_type": "multiple_choice",
            "prompt": "Which output is reusable?",
            "difficulty": "foundation",
            "explanation": "Reusable output can be checked by callers.",
            "concept_tag_ids": [concept_id],
            "options": [
                {
                    "label": "A",
                    "text": "Print only",
                    "is_correct": False,
                    "explanation": "Printing hides the value.",
                },
                {
                    "label": "B",
                    "text": "Return value",
                    "is_correct": True,
                    "explanation": "Returning keeps the value reusable.",
                },
            ],
        },
    )
    assert question.status_code == 201
    question_id = question.json()["id"]

    option = client.post(
        "/admin/question-options",
        headers=admin_headers,
        json={
            "question_id": question_id,
            "label": "C",
            "text": "Global variable",
            "is_correct": False,
            "explanation": "Global state is harder to test.",
        },
    )
    assert option.status_code == 201
    option_id = option.json()["id"]

    patch_option = client.patch(
        f"/admin/question-options/{option_id}",
        headers=admin_headers,
        json={"text": "Hidden global variable"},
    )
    assert patch_option.status_code == 200
    assert patch_option.json()["text"] == "Hidden global variable"

    assert client.patch(
        f"/admin/lessons/{lesson_id}",
        headers=admin_headers,
        json={"title": "Handler output updated"},
    ).status_code == 200
    assert client.delete(f"/admin/question-options/{option_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/admin/questions/{question_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/admin/lesson-blocks/{block_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/admin/lessons/{lesson_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/admin/modules/{module_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/admin/levels/{level_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/admin/tracks/{track_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/admin/concept-tags/{concept_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/admin/languages/{language_id}", headers=admin_headers).status_code == 200

