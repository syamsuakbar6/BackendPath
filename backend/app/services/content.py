from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    BlockType,
    ConceptTag,
    ContentStatus,
    DebugTask,
    Lesson,
    LessonBlock,
    MiniTask,
    Module,
    Question,
    QuestionOption,
    QuestionType,
)
from app.schemas.learning import LessonImportPayload


def published_only(items):
    return [item for item in items if item.content_status == ContentStatus.published]


def load_lesson_with_content(db: Session, lesson_id: int) -> Lesson | None:
    return db.scalar(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(
            selectinload(Lesson.blocks),
            selectinload(Lesson.concept_tags),
            selectinload(Lesson.questions).selectinload(Question.options),
            selectinload(Lesson.questions).selectinload(Question.concept_tags),
            selectinload(Lesson.mini_tasks),
            selectinload(Lesson.debug_tasks),
        )
    )


def lesson_to_payload(lesson: Lesson, progress=None, learner_view: bool = False) -> dict:
    questions = lesson.questions
    debug_tasks = lesson.debug_tasks
    mini_tasks = lesson.mini_tasks
    if learner_view:
        questions = published_only(questions)
        debug_tasks = published_only(debug_tasks)
        mini_tasks = published_only(mini_tasks)

    return {
        "id": lesson.id,
        "module_id": lesson.module_id,
        "title": lesson.title,
        "slug": lesson.slug,
        "learning_goal": lesson.learning_goal,
        "why_it_matters": lesson.why_it_matters,
        "estimated_minutes": lesson.estimated_minutes,
        "sort_order": lesson.sort_order,
        "content_status": lesson.content_status,
        "concept_tags": lesson.concept_tags,
        "blocks": lesson.blocks,
        "questions": questions,
        "mini_tasks": mini_tasks,
        "debug_tasks": debug_tasks,
        "progress": progress,
    }


def validate_import_payload(payload: LessonImportPayload) -> list[str]:
    errors: list[str] = []
    known_tag_slugs = {tag.slug for tag in payload.concept_tags}
    if not payload.title.strip():
        errors.append("lesson.title is required.")
    if not payload.slug.strip():
        errors.append("lesson.slug is required.")
    if not payload.learning_goal.strip():
        errors.append("lesson.learning_goal is required.")
    if not payload.why_it_matters.strip():
        errors.append("lesson.why_it_matters is required.")

    for index, block in enumerate(payload.blocks):
        if not block.body.strip():
            errors.append(f"blocks[{index}].body is required.")

    for index, question in enumerate(payload.questions):
        if not question.prompt.strip():
            errors.append(f"questions[{index}].prompt is required.")
        if question.question_type == QuestionType.multiple_choice:
            if len(question.options) < 2:
                errors.append(f"questions[{index}] needs at least two options.")
            if not any(option.is_correct for option in question.options):
                errors.append(f"questions[{index}] needs one correct option.")
        if question.question_type == QuestionType.explain_back:
            if not question.expected_concepts:
                errors.append(f"questions[{index}].expected_concepts is required for explain-back.")
        for slug in question.concept_tag_slugs:
            if slug not in known_tag_slugs:
                errors.append(f"questions[{index}] references unknown concept tag slug '{slug}'.")

    for index, task in enumerate(payload.debug_tasks):
        if not task.broken_code.strip():
            errors.append(f"debug_tasks[{index}].broken_code is required.")
        if task.concept_tag_slug and task.concept_tag_slug not in known_tag_slugs:
            errors.append(
                f"debug_tasks[{index}] references unknown concept tag slug '{task.concept_tag_slug}'."
            )

    for index, task in enumerate(payload.mini_tasks):
        if task.concept_tag_slug and task.concept_tag_slug not in known_tag_slugs:
            errors.append(
                f"mini_tasks[{index}] references unknown concept tag slug '{task.concept_tag_slug}'."
            )

    if payload.content_status == ContentStatus.published:
        errors.extend(validate_import_publishable(payload))

    return errors


def validate_import_publishable(payload: LessonImportPayload) -> list[str]:
    errors: list[str] = []
    block_titles = [(block.title or "").lower() for block in payload.blocks]
    block_types = {block.block_type for block in payload.blocks}

    if not any("learning goal" in title or "objective" in title for title in block_titles):
        errors.append("Missing learning goal / objective block.")
    if not any("why" in title and "matter" in title for title in block_titles):
        errors.append("Missing why it matters block.")
    if not any("concept" in title for title in block_titles):
        errors.append("Missing core concept block.")
    if BlockType.example_good not in block_types:
        errors.append("Missing at least one good example block.")
    if BlockType.example_bad not in block_types and not any("mistake" in title for title in block_titles):
        errors.append("Missing at least one bad example or common mistake block.")
    if BlockType.checklist not in block_types:
        errors.append("Missing checklist block.")
    if not any(question.question_type != QuestionType.explain_back for question in payload.questions):
        errors.append("Missing at least one quick check question.")
    if not any(question.question_type == QuestionType.explain_back for question in payload.questions):
        errors.append("Missing at least one explain-back question.")
    return errors


def validate_lesson_publishable(lesson: Lesson) -> list[str]:
    errors: list[str] = []
    block_titles = [(block.title or "").lower() for block in lesson.blocks]
    blocks_by_type = {block.block_type for block in lesson.blocks}

    if not lesson.learning_goal.strip():
        errors.append("Lesson learning_goal is required.")
    if not lesson.why_it_matters.strip():
        errors.append("Lesson why_it_matters is required.")
    if not any("learning goal" in title or "objective" in title for title in block_titles):
        errors.append("Missing learning goal / objective block.")
    if not any("why" in title and "matter" in title for title in block_titles):
        errors.append("Missing why it matters block.")
    if not any("concept" in title for title in block_titles):
        errors.append("Missing core concept block.")
    if BlockType.example_good not in blocks_by_type:
        errors.append("Missing at least one good example block.")
    if BlockType.example_bad not in blocks_by_type and not any(
        "mistake" in title for title in block_titles
    ):
        errors.append("Missing at least one bad example or common mistake block.")
    if BlockType.checklist not in blocks_by_type:
        errors.append("Missing checklist block.")

    active_questions = [
        question
        for question in lesson.questions
        if question.content_status != ContentStatus.archived
    ]
    if not any(question.question_type != QuestionType.explain_back for question in active_questions):
        errors.append("Missing at least one quick check question.")
    if not any(question.question_type == QuestionType.explain_back for question in active_questions):
        errors.append("Missing at least one explain-back question.")

    return errors


def publish_lesson(db: Session, lesson: Lesson) -> Lesson:
    errors = validate_lesson_publishable(lesson)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Lesson is not publishable.", "errors": errors},
        )
    lesson.content_status = ContentStatus.published
    lesson.is_published = True
    for question in lesson.questions:
        if question.content_status == ContentStatus.draft:
            question.content_status = ContentStatus.published
    for task in lesson.debug_tasks:
        if task.content_status == ContentStatus.draft:
            task.content_status = ContentStatus.published
    for task in lesson.mini_tasks:
        if task.content_status == ContentStatus.draft:
            task.content_status = ContentStatus.published
    db.commit()
    db.refresh(lesson)
    return lesson


def archive_lesson(db: Session, lesson: Lesson) -> Lesson:
    lesson.content_status = ContentStatus.archived
    lesson.is_published = False
    db.commit()
    db.refresh(lesson)
    return lesson


def import_lesson(db: Session, payload: LessonImportPayload) -> Lesson:
    errors = validate_import_payload(payload)
    module = db.get(Module, payload.module_id)
    if not module:
        errors.append("module_id does not reference an existing module.")
    existing = db.scalar(
        select(Lesson).where(
            Lesson.module_id == payload.module_id,
            Lesson.slug == payload.slug,
        )
    )
    if existing:
        errors.append("lesson.slug already exists in this module.")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Lesson import failed validation.", "errors": errors},
        )

    tags_by_slug = _get_or_create_tags(db, payload)
    lesson = Lesson(
        module_id=payload.module_id,
        title=payload.title,
        slug=payload.slug,
        learning_goal=payload.learning_goal,
        why_it_matters=payload.why_it_matters,
        estimated_minutes=payload.estimated_minutes,
        sort_order=payload.sort_order,
        content_status=payload.content_status,
        is_published=payload.content_status == ContentStatus.published,
        concept_tags=list(tags_by_slug.values()),
    )
    lesson.blocks = [
        LessonBlock(
            block_type=block.block_type,
            title=block.title,
            body=block.body,
            code_language=block.code_language,
            block_metadata=block.block_metadata,
            sort_order=block.sort_order or index + 1,
        )
        for index, block in enumerate(payload.blocks)
    ]
    lesson.questions = [
        _build_question(question, tags_by_slug)
        for question in payload.questions
    ]
    lesson.debug_tasks = [
        DebugTask(
            title=task.title,
            prompt=task.prompt,
            broken_code=task.broken_code,
            hint=task.hint,
            expected_fix_summary=task.expected_fix_summary,
            difficulty=task.difficulty,
            content_status=task.content_status,
            concept_tag=tags_by_slug.get(task.concept_tag_slug or ""),
        )
        for task in payload.debug_tasks
    ]
    lesson.mini_tasks = [
        MiniTask(
            title=task.title,
            prompt=task.prompt,
            acceptance_criteria=task.acceptance_criteria,
            difficulty=task.difficulty,
            content_status=task.content_status,
            concept_tag=tags_by_slug.get(task.concept_tag_slug or ""),
        )
        for task in payload.mini_tasks
    ]
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return load_lesson_with_content(db, lesson.id) or lesson


def export_lesson(lesson: Lesson) -> dict:
    return {
        "module_id": lesson.module_id,
        "title": lesson.title,
        "slug": lesson.slug,
        "learning_goal": lesson.learning_goal,
        "why_it_matters": lesson.why_it_matters,
        "estimated_minutes": lesson.estimated_minutes,
        "sort_order": lesson.sort_order,
        "content_status": lesson.content_status.value,
        "concept_tags": [
            {
                "name": tag.name,
                "slug": tag.slug,
                "description": tag.description,
            }
            for tag in lesson.concept_tags
        ],
        "blocks": [
            {
                "block_type": block.block_type.value,
                "title": block.title,
                "body": block.body,
                "code_language": block.code_language,
                "block_metadata": block.block_metadata,
                "sort_order": block.sort_order,
            }
            for block in lesson.blocks
        ],
        "questions": [
            {
                "question_type": question.question_type.value,
                "prompt": question.prompt,
                "difficulty": question.difficulty,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "expected_concepts": question.expected_concepts,
                "rubric": question.rubric,
                "sample_ideal_answer": question.sample_ideal_answer,
                "misconception_notes": question.misconception_notes,
                "remedial_prompt": question.remedial_prompt,
                "sort_order": question.sort_order,
                "content_status": question.content_status.value,
                "concept_tag_slugs": [tag.slug for tag in question.concept_tags],
                "options": [
                    {
                        "label": option.label,
                        "text": option.text,
                        "is_correct": option.is_correct,
                        "explanation": option.explanation,
                    }
                    for option in question.options
                ],
            }
            for question in lesson.questions
        ],
        "debug_tasks": [
            {
                "title": task.title,
                "prompt": task.prompt,
                "broken_code": task.broken_code,
                "hint": task.hint,
                "expected_fix_summary": task.expected_fix_summary,
                "difficulty": task.difficulty,
                "content_status": task.content_status.value,
                "concept_tag_slug": task.concept_tag.slug if task.concept_tag else None,
            }
            for task in lesson.debug_tasks
        ],
        "mini_tasks": [
            {
                "title": task.title,
                "prompt": task.prompt,
                "acceptance_criteria": task.acceptance_criteria,
                "difficulty": task.difficulty,
                "content_status": task.content_status.value,
                "concept_tag_slug": task.concept_tag.slug if task.concept_tag else None,
            }
            for task in lesson.mini_tasks
        ],
    }


def _get_or_create_tags(db: Session, payload: LessonImportPayload) -> dict[str, ConceptTag]:
    tags_by_slug: dict[str, ConceptTag] = {}
    for tag_payload in payload.concept_tags:
        tag = db.scalar(select(ConceptTag).where(ConceptTag.slug == tag_payload.slug))
        if not tag:
            tag = ConceptTag(
                name=tag_payload.name,
                slug=tag_payload.slug,
                description=tag_payload.description,
            )
            db.add(tag)
            db.flush()
        tags_by_slug[tag.slug] = tag
    return tags_by_slug


def _build_question(question_payload, tags_by_slug: dict[str, ConceptTag]) -> Question:
    question = Question(
        question_type=question_payload.question_type,
        prompt=question_payload.prompt,
        difficulty=question_payload.difficulty,
        correct_answer=question_payload.correct_answer,
        explanation=question_payload.explanation,
        expected_concepts=question_payload.expected_concepts,
        rubric=question_payload.rubric,
        sample_ideal_answer=question_payload.sample_ideal_answer,
        misconception_notes=question_payload.misconception_notes,
        remedial_prompt=question_payload.remedial_prompt,
        sort_order=question_payload.sort_order,
        content_status=question_payload.content_status,
        concept_tags=[
            tags_by_slug[slug]
            for slug in question_payload.concept_tag_slugs
            if slug in tags_by_slug
        ],
    )
    question.options = [
        QuestionOption(
            label=option.label,
            text=option.text,
            is_correct=option.is_correct,
            explanation=option.explanation,
        )
        for option in question_payload.options
    ]
    return question
