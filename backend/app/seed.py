from __future__ import annotations

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import Base, SessionLocal, engine
from app.models import (
    BlockType,
    ConceptTag,
    DebugTask,
    Language,
    Lesson,
    LessonBlock,
    Level,
    MiniTask,
    Module,
    Question,
    QuestionOption,
    QuestionType,
    Track,
    User,
    UserRole,
)


def seed_database(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if db.scalar(select(Language).where(Language.slug == "python")):
            print("Seed data already exists.")
            return

        admin = User(
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.admin,
        )
        learner = User(
            email="learner@example.com",
            full_name="Learner User",
            hashed_password=get_password_hash("learner123"),
            role=UserRole.learner,
        )
        db.add_all([admin, learner])

        tag_specs = [
            ("Function Design", "function-design", "Designing functions with reusable outputs."),
            ("Return Values", "return-values", "Returning data instead of only printing side effects."),
            ("Backend Logic", "backend-logic", "Logic that can be tested and reused by API routes."),
            ("Authentication", "authentication", "Verifying who a user is."),
            ("Authorization", "authorization", "Checking what a verified user may access."),
            ("HTTP Status Codes", "http-status-codes", "Choosing status codes that communicate API behavior."),
            ("Error Handling", "error-handling", "Handling invalid or failed backend states clearly."),
        ]
        tags = {
            slug: ConceptTag(name=name, slug=slug, description=description)
            for name, slug, description in tag_specs
        }
        db.add_all(tags.values())

        python = Language(
            name="Python",
            slug="python",
            description="Python backend engineering foundations.",
            sort_order=1,
        )
        track = Track(
            language=python,
            title="Python Backend Junior Path",
            slug="python-backend-junior-path",
            description="A proof-based path for beginner to junior backend developers.",
            target_audience="Beginner to junior backend developer",
            sort_order=1,
        )
        foundation = Level(
            track=track,
            title="Programming Foundation",
            slug="programming-foundation",
            description="Core programming habits that make backend code testable.",
            sort_order=1,
        )
        backend_foundation = Level(
            track=track,
            title="Backend Foundation",
            slug="backend-foundation",
            description="Backend concepts used in real HTTP APIs.",
            sort_order=2,
        )

        function_design = Module(
            level=foundation,
            title="Function Design",
            slug="function-design",
            description="Write functions that return useful values and are easy to test.",
            estimated_minutes=35,
            sort_order=1,
        )
        error_handling = Module(
            level=foundation,
            title="Error Handling",
            slug="error-handling",
            description="Understand how backend systems communicate invalid or failed states.",
            estimated_minutes=30,
            sort_order=2,
        )
        http_basics = Module(
            level=backend_foundation,
            title="HTTP Basics",
            slug="http-basics",
            description="Reason about requests, responses, identity, and access in APIs.",
            estimated_minutes=45,
            sort_order=1,
        )
        db.add_all([python, track, foundation, backend_foundation, function_design, error_handling, http_basics])
        db.flush()

        _add_lesson(
            module=function_design,
            title="Why return is better than print for backend logic",
            slug="return-better-than-print",
            goal="Explain why backend logic should return values callers can use.",
            why="Routes, tests, services, and background jobs need values they can inspect. Printing hides the result from the caller.",
            tag_objects=[tags["function-design"], tags["return-values"], tags["backend-logic"]],
            good_code=(
                "def build_user_message(name: str) -> str:\n"
                "    return f\"Welcome, {name}\"\n\n"
                "message = build_user_message(\"Ayu\")"
            ),
            bad_code=(
                "def build_user_message(name: str) -> None:\n"
                "    print(f\"Welcome, {name}\")\n\n"
                "message = build_user_message(\"Ayu\")  # message is None"
            ),
            quick_prompt="Which function design is easier for an API route to test and reuse?",
            options=[
                ("A", "A function that prints the result immediately.", False, "Printing is a side effect; the caller cannot reuse the printed value."),
                ("B", "A function that returns the result to the caller.", True, "Returning keeps the value available for routes, tests, and other services."),
                ("C", "A function that does both print and return every time.", False, "Mixing both often adds noise and makes behavior harder to reason about."),
            ],
            correct_explanation="Returning values makes backend logic composable and testable.",
            expected_concepts=["return", "caller", "test"],
            remedial="What can an API route do with a returned value that it cannot do with printed output?",
            debug_code=(
                "def calculate_total(price, tax):\n"
                "    print(price + tax)\n\n"
                "total = calculate_total(10, 2)\n"
                "assert total == 12"
            ),
            mini_prompt="Rewrite a function that prints a discount message so it returns the message instead.",
            sort_order=1,
        )

        _add_lesson(
            module=http_basics,
            title="Authentication vs Authorization",
            slug="authentication-vs-authorization",
            goal="Distinguish identity checks from permission checks in backend APIs.",
            why="Secure backend routes need to know who the user is before deciding what that user is allowed to do.",
            tag_objects=[tags["authentication"], tags["authorization"], tags["backend-logic"]],
            good_code=(
                "def can_view_invoice(user, invoice):\n"
                "    if not user.is_authenticated:\n"
                "        return False\n"
                "    return invoice.owner_id == user.id or user.role == \"admin\""
            ),
            bad_code=(
                "def can_view_invoice(user, invoice):\n"
                "    return user is not None  # identity exists, but permission was not checked"
            ),
            quick_prompt="Authentication answers which question?",
            options=[
                ("A", "Who is this user?", True, "Authentication verifies identity."),
                ("B", "What can this user access?", False, "That is authorization."),
                ("C", "Which database table should be queried?", False, "That can support auth, but it is not the concept itself."),
            ],
            correct_explanation="Authentication verifies identity; authorization checks permissions.",
            expected_concepts=["identity", "permission", "authorization"],
            remedial="After login succeeds, what separate question should the backend still ask?",
            debug_code=(
                "def delete_project(user, project):\n"
                "    if user.is_authenticated:\n"
                "        return \"deleted\"\n"
                "    return \"login required\""
            ),
            mini_prompt="Write two plain-English checks for an endpoint that updates a team billing plan.",
            sort_order=1,
        )

        _add_lesson(
            module=http_basics,
            title="401 vs 403",
            slug="401-vs-403",
            goal="Choose between 401 and 403 by reasoning about identity and permission.",
            why="Clear status codes help frontend clients, logs, and API consumers understand what failed.",
            tag_objects=[tags["http-status-codes"], tags["authentication"], tags["authorization"], tags["error-handling"]],
            good_code=(
                "if not user:\n"
                "    return {\"status\": 401, \"detail\": \"Login required\"}\n"
                "if not user.can_access(resource):\n"
                "    return {\"status\": 403, \"detail\": \"Forbidden\"}"
            ),
            bad_code=(
                "if not user or not user.can_access(resource):\n"
                "    return {\"status\": 403, \"detail\": \"Forbidden\"}"
            ),
            quick_prompt="A request has no valid token. Which status best fits?",
            options=[
                ("A", "401 Unauthorized", True, "401 means the request is not authenticated."),
                ("B", "403 Forbidden", False, "403 fits when identity is known but access is denied."),
                ("C", "200 OK with an error message", False, "The status code should communicate the failure clearly."),
            ],
            correct_explanation="Use 401 for missing or invalid identity, and 403 for known identity without permission.",
            expected_concepts=["401", "403", "permission"],
            remedial="When would a logged-in user receive 403 instead of 401?",
            debug_code=(
                "def get_admin_report(user):\n"
                "    if not user:\n"
                "        return 403\n"
                "    if user.role != \"admin\":\n"
                "        return 401\n"
                "    return 200"
            ),
            mini_prompt="Create a tiny decision table for unauthenticated user, normal user, and admin user.",
            sort_order=2,
        )

        db.commit()
        print("Seed data created.")


def _add_lesson(
    module: Module,
    title: str,
    slug: str,
    goal: str,
    why: str,
    tag_objects: list[ConceptTag],
    good_code: str,
    bad_code: str,
    quick_prompt: str,
    options: list[tuple[str, str, bool, str]],
    correct_explanation: str,
    expected_concepts: list[str],
    remedial: str,
    debug_code: str,
    mini_prompt: str,
    sort_order: int,
) -> Lesson:
    lesson = Lesson(
        title=title,
        slug=slug,
        learning_goal=goal,
        why_it_matters=why,
        estimated_minutes=15,
        sort_order=sort_order,
        concept_tags=tag_objects,
    )
    module.lessons.append(lesson)
    lesson.blocks = [
        LessonBlock(
            block_type=BlockType.text,
            title="Concept",
            body=goal,
            sort_order=1,
        ),
        LessonBlock(
            block_type=BlockType.text,
            title="Why this matters in real backend work",
            body=why,
            sort_order=2,
        ),
        LessonBlock(
            block_type=BlockType.example_good,
            title="Good example",
            body=good_code,
            code_language="python",
            sort_order=3,
        ),
        LessonBlock(
            block_type=BlockType.example_bad,
            title="Bad example",
            body=bad_code,
            code_language="python",
            sort_order=4,
        ),
        LessonBlock(
            block_type=BlockType.warning,
            title="Common beginner mistake",
            body="Treating visible output as proof that the backend logic is reusable or secure.",
            sort_order=5,
        ),
        LessonBlock(
            block_type=BlockType.question,
            title="Quick check",
            body=quick_prompt,
            sort_order=6,
        ),
        LessonBlock(
            block_type=BlockType.reflection,
            title="Explain-back",
            body="Explain the idea as if you were reviewing a junior developer's pull request.",
            sort_order=7,
        ),
        LessonBlock(
            block_type=BlockType.debug_task,
            title="Debug challenge",
            body="Find the broken reasoning in the placeholder task and describe the fix.",
            sort_order=8,
        ),
        LessonBlock(
            block_type=BlockType.mini_task,
            title="Mini task",
            body=mini_prompt,
            sort_order=9,
        ),
        LessonBlock(
            block_type=BlockType.checklist,
            title="End checkpoint",
            body="I can state the concept, spot the bad example, answer a quick check, explain it back, and connect it to backend work.",
            block_metadata={"items": ["Concept stated", "Bad example explained", "Practice attempted", "Reflection submitted"]},
            sort_order=10,
        ),
    ]

    quick_question = Question(
        lesson=lesson,
        question_type=QuestionType.multiple_choice,
        prompt=quick_prompt,
        difficulty="foundation",
        explanation=correct_explanation,
        sample_ideal_answer=correct_explanation,
        remedial_prompt=remedial,
        sort_order=1,
        concept_tags=tag_objects,
        options=[
            QuestionOption(label=label, text=text, is_correct=is_correct, explanation=explanation)
            for label, text, is_correct, explanation in options
        ],
    )
    explain_question = Question(
        lesson=lesson,
        question_type=QuestionType.explain_back,
        prompt="Explain this concept back in your own words.",
        difficulty="foundation",
        expected_concepts=expected_concepts,
        rubric={
            "strong": "Mentions all expected concepts and connects them to backend behavior.",
            "stable": "Mentions most concepts with a usable example.",
            "weak": "Mentions terms but misses the practical consequence.",
        },
        sample_ideal_answer=correct_explanation,
        misconception_notes="Watch for answers that repeat vocabulary without explaining the backend consequence.",
        remedial_prompt=remedial,
        sort_order=2,
        concept_tags=tag_objects,
    )
    lesson.questions = [quick_question, explain_question]
    lesson.debug_tasks = [
        DebugTask(
            title="Debug the reasoning",
            prompt="Explain what is broken and what the corrected version should do.",
            broken_code=debug_code,
            hint="Look for the place where the code hides or reverses the important backend signal.",
            expected_fix_summary="Preserve the concept boundary and make the caller-visible result clear.",
            concept_tag=tag_objects[0],
        )
    ]
    lesson.mini_tasks = [
        MiniTask(
            title="Apply the concept",
            prompt=mini_prompt,
            acceptance_criteria=[
                "Uses the concept intentionally",
                "Names one realistic backend use case",
                "Can be explained in plain language",
            ],
            concept_tag=tag_objects[0],
        )
    ]
    return lesson


if __name__ == "__main__":
    seed_database()
