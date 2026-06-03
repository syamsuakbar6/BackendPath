def _first_module_id(client, admin_headers) -> int:
    response = client.get("/admin/modules", headers=admin_headers)
    assert response.status_code == 200
    return response.json()[0]["id"]


def _draft_lesson_payload(module_id: int, slug: str = "draft-lifecycle-lesson") -> dict:
    return {
        "module_id": module_id,
        "title": "Draft lifecycle lesson",
        "slug": slug,
        "learning_goal": "Explain the draft lifecycle.",
        "why_it_matters": "Learners should only see reviewed content.",
        "estimated_minutes": 8,
        "sort_order": 99,
        "content_status": "draft",
    }


def _complete_import_payload(module_id: int, slug: str = "content-v1-complete") -> dict:
    return {
        "module_id": module_id,
        "title": "Content V1 complete lesson",
        "slug": slug,
        "learning_goal": "Explain why return produces caller-visible backend values.",
        "why_it_matters": "API routes and tests need reusable data, not hidden console output.",
        "estimated_minutes": 12,
        "sort_order": 50,
        "content_status": "draft",
        "concept_tags": [
            {
                "name": "Return Values",
                "slug": "return-values",
                "description": "Returning data instead of only printing side effects.",
            }
        ],
        "blocks": [
            {
                "block_type": "text",
                "title": "Learning goal",
                "body": "Explain return versus print for backend logic.",
                "sort_order": 1,
            },
            {
                "block_type": "text",
                "title": "Why this matters in real backend work",
                "body": "Routes need values they can return, inspect, or test.",
                "sort_order": 2,
            },
            {
                "block_type": "text",
                "title": "Core concept",
                "body": "Return values are available to callers. Print is a side effect.",
                "sort_order": 3,
            },
            {
                "block_type": "example_good",
                "title": "Good example",
                "body": "def total(a, b):\n    return a + b",
                "code_language": "python",
                "sort_order": 4,
            },
            {
                "block_type": "example_bad",
                "title": "Bad example",
                "body": "def total(a, b):\n    print(a + b)",
                "code_language": "python",
                "sort_order": 5,
            },
            {
                "block_type": "common_mistake",
                "title": "Common beginner mistake",
                "body": "Console output is not the same as caller-visible data.",
                "sort_order": 6,
            },
            {
                "block_type": "question",
                "title": "Quick check",
                "body": "Which function result can a caller reuse?",
                "sort_order": 7,
            },
            {
                "block_type": "reflection",
                "title": "Explain-back",
                "body": "Explain return versus print in your own words.",
                "sort_order": 8,
            },
            {
                "block_type": "debug_task",
                "title": "Debug challenge",
                "body": "Explain why the caller receives None.",
                "block_metadata": {"task_slug": "debug-hidden-none"},
                "sort_order": 9,
            },
            {
                "block_type": "mini_task",
                "title": "Mini task",
                "body": "Write a small function that returns a message.",
                "block_metadata": {"task_slug": "return-message-mini-task"},
                "sort_order": 10,
            },
            {
                "block_type": "checklist",
                "title": "End checkpoint",
                "body": "Before moving on, check your understanding.",
                "block_metadata": {"items": ["Concept stated", "Bad example explained"]},
                "sort_order": 11,
            },
        ],
        "questions": [
            {
                "slug": "quick-check-return-output",
                "question_type": "multiple_choice",
                "prompt": "Which output can an API route reuse?",
                "difficulty": "foundation",
                "explanation": "Returned values are caller-visible.",
                "concept_tag_slugs": ["return-values"],
                "options": [
                    {
                        "label": "A",
                        "text": "Printed output",
                        "is_correct": False,
                        "explanation": "Printing does not return a value to the caller.",
                    },
                    {
                        "label": "B",
                        "text": "Returned output",
                        "is_correct": True,
                        "explanation": "Returning gives the caller data to use.",
                    },
                ],
            },
            {
                "slug": "explain-back-return-output",
                "question_type": "explain_back",
                "prompt": "Explain why return is better for backend logic.",
                "difficulty": "foundation",
                "expected_concepts": ["return", "caller"],
                "rubric": {
                    "strong": "Mentions return, caller, and backend reuse.",
                    "weak": "Only repeats that return is better.",
                },
                "sample_ideal_answer": "Return gives the caller data it can reuse or test.",
                "misconception_notes": "Do not confuse visible console output with reusable data.",
                "remedial_prompt": "What does the caller receive from print?",
                "concept_tag_slugs": ["return-values"],
            },
        ],
        "debug_tasks": [
            {
                "slug": "debug-hidden-none",
                "title": "Debug hidden None",
                "prompt": "Explain why total is None.",
                "broken_code": "def total(a, b):\n    print(a + b)\n\nvalue = total(1, 2)",
                "hint": "Look at what the function returns.",
                "expected_fix_summary": "Return a + b.",
                "difficulty": "foundation",
                "concept_tag_slug": "return-values",
            }
        ],
        "mini_tasks": [
            {
                "slug": "return-message-mini-task",
                "title": "Return a message",
                "prompt": "Write a function that returns a message.",
                "acceptance_criteria": ["Returns a string", "Caller stores the string"],
                "difficulty": "foundation",
                "concept_tag_slug": "return-values",
            }
        ],
    }


def _import_complete_lesson(client, admin_headers, slug: str = "content-v1-complete") -> dict:
    payload = _complete_import_payload(_first_module_id(client, admin_headers), slug=slug)
    response = client.post("/admin/content/import/lesson", headers=admin_headers, json=payload)
    assert response.status_code == 201
    return response.json()


def test_learner_cannot_see_draft_lesson_but_admin_can(client, learner_headers, admin_headers):
    module_id = _first_module_id(client, admin_headers)
    create = client.post(
        "/admin/lessons",
        headers=admin_headers,
        json=_draft_lesson_payload(module_id),
    )
    assert create.status_code == 201
    lesson_id = create.json()["id"]
    assert create.json()["content_status"] == "draft"

    learner_view = client.get(f"/lessons/{lesson_id}", headers=learner_headers)
    assert learner_view.status_code == 404

    admin_view = client.get(f"/admin/lessons/{lesson_id}", headers=admin_headers)
    assert admin_view.status_code == 200
    assert admin_view.json()["content_status"] == "draft"


def test_publish_fails_if_lesson_is_incomplete(client, admin_headers):
    module_id = _first_module_id(client, admin_headers)
    create = client.post(
        "/admin/lessons",
        headers=admin_headers,
        json=_draft_lesson_payload(module_id, slug="incomplete-publish"),
    )
    assert create.status_code == 201

    publish = client.post(f"/admin/lessons/{create.json()['id']}/publish", headers=admin_headers)
    assert publish.status_code == 422
    errors = publish.json()["detail"]["errors"]
    assert "Missing at least one good example block." in errors
    assert "Missing at least one quick check question." in errors


def test_publish_succeeds_if_lesson_has_required_blocks_and_questions(
    client, learner_headers, admin_headers
):
    lesson = _import_complete_lesson(client, admin_headers, slug="publish-ready")

    publish = client.post(f"/admin/lessons/{lesson['id']}/publish", headers=admin_headers)
    assert publish.status_code == 200
    assert publish.json()["content_status"] == "published"

    learner_view = client.get(f"/lessons/{lesson['id']}", headers=learner_headers)
    assert learner_view.status_code == 200
    assert learner_view.json()["questions"]


def test_lesson_import_creates_blocks_questions_and_tasks(client, admin_headers):
    lesson = _import_complete_lesson(client, admin_headers, slug="import-creates-content")

    assert lesson["content_status"] == "draft"
    assert len(lesson["blocks"]) >= 8
    assert len(lesson["questions"]) == 2
    assert len(lesson["debug_tasks"]) == 1
    assert len(lesson["mini_tasks"]) == 1


def test_lesson_export_returns_valid_json(client, admin_headers):
    lesson = _import_complete_lesson(client, admin_headers, slug="export-valid-json")

    export = client.get(f"/admin/content/export/lesson/{lesson['id']}", headers=admin_headers)
    assert export.status_code == 200
    body = export.json()
    assert body["slug"] == "export-valid-json"
    assert body["blocks"]
    assert body["questions"][0]["options"]
    assert body["debug_tasks"]
    assert body["mini_tasks"]


def test_archived_lesson_is_hidden_from_learner(client, learner_headers, admin_headers):
    lesson = _import_complete_lesson(client, admin_headers, slug="archive-hidden")
    assert client.post(f"/admin/lessons/{lesson['id']}/publish", headers=admin_headers).status_code == 200

    archive = client.post(f"/admin/lessons/{lesson['id']}/archive", headers=admin_headers)
    assert archive.status_code == 200
    assert archive.json()["content_status"] == "archived"

    learner_view = client.get(f"/lessons/{lesson['id']}", headers=learner_headers)
    assert learner_view.status_code == 404


def test_preview_endpoint_is_admin_only(client, learner_headers, admin_headers):
    lesson = _import_complete_lesson(client, admin_headers, slug="preview-admin-only")

    learner_preview = client.get(f"/admin/lessons/{lesson['id']}/preview", headers=learner_headers)
    assert learner_preview.status_code == 403

    admin_preview = client.get(f"/admin/lessons/{lesson['id']}/preview", headers=admin_headers)
    assert admin_preview.status_code == 200
    assert admin_preview.json()["content_status"] == "draft"


def test_draft_lesson_child_questions_do_not_appear_to_learners_or_search(
    client, learner_headers, admin_headers
):
    payload = _complete_import_payload(
        _first_module_id(client, admin_headers),
        slug="draft-child-question-hidden",
    )
    payload["questions"][0]["slug"] = "hidden-draft-child-sentinel"
    payload["questions"][0]["prompt"] = "Hidden draft child sentinel question"

    import_response = client.post(
        "/admin/content/import/lesson",
        headers=admin_headers,
        json=payload,
    )
    assert import_response.status_code == 201
    lesson = import_response.json()
    assert lesson["questions"][0]["content_status"] == "draft"

    learner_view = client.get(f"/lessons/{lesson['id']}", headers=learner_headers)
    assert learner_view.status_code == 404

    search = client.get("/search?q=hidden-draft-child-sentinel", headers=learner_headers)
    assert search.status_code == 200
    assert search.json()["questions"] == []


def test_debug_task_block_can_reference_debug_task_slug(client, admin_headers):
    lesson = _import_complete_lesson(client, admin_headers, slug="debug-block-reference")

    debug_block = next(
        block for block in lesson["blocks"] if block["block_type"] == "debug_task"
    )
    assert debug_block["block_metadata"]["task_slug"] == "debug-hidden-none"
    assert lesson["debug_tasks"][0]["slug"] == "debug-hidden-none"


def test_mini_task_block_can_reference_mini_task_slug(client, admin_headers):
    lesson = _import_complete_lesson(client, admin_headers, slug="mini-block-reference")

    mini_block = next(
        block for block in lesson["blocks"] if block["block_type"] == "mini_task"
    )
    assert mini_block["block_metadata"]["task_slug"] == "return-message-mini-task"
    assert lesson["mini_tasks"][0]["slug"] == "return-message-mini-task"


def test_common_mistake_block_passes_publish_validation(client, admin_headers):
    payload = _complete_import_payload(
        _first_module_id(client, admin_headers),
        slug="common-mistake-publishable",
    )
    payload["blocks"] = [
        block for block in payload["blocks"] if block["block_type"] != "example_bad"
    ]

    import_response = client.post(
        "/admin/content/import/lesson",
        headers=admin_headers,
        json=payload,
    )
    assert import_response.status_code == 201

    publish = client.post(
        f"/admin/lessons/{import_response.json()['id']}/publish",
        headers=admin_headers,
    )
    assert publish.status_code == 200
    assert publish.json()["content_status"] == "published"
