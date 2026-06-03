from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ConceptTag,
    ContentStatus,
    DebugTask,
    Lesson,
    MiniTask,
    Module,
    Question,
    Track,
)


def search_learning(db: Session, query: str) -> dict:
    q = f"%{query.strip()}%"
    if not query.strip():
        return _empty(query)

    lessons = list(
        db.scalars(
            select(Lesson)
            .where(
                Lesson.content_status == ContentStatus.published,
                or_(
                    Lesson.title.ilike(q),
                    Lesson.learning_goal.ilike(q),
                    Lesson.why_it_matters.ilike(q),
                )
            )
            .options(selectinload(Lesson.module), selectinload(Lesson.concept_tags))
            .limit(10)
        )
    )

    tag_matches = list(
        db.scalars(
            select(ConceptTag).where(
                or_(
                    ConceptTag.name.ilike(q),
                    ConceptTag.slug.ilike(q),
                    ConceptTag.description.ilike(q),
                )
            )
        )
    )
    for tag in tag_matches:
        for lesson in tag.lessons:
            if lesson.content_status == ContentStatus.published:
                lessons = _append_unique(lessons, lesson)

    questions = list(
        db.scalars(
            select(Question)
            .where(or_(Question.prompt.ilike(q), Question.slug.ilike(q)))
            .where(Question.content_status == ContentStatus.published)
            .options(selectinload(Question.lesson), selectinload(Question.concept_tags))
            .limit(10)
        )
    )
    questions = [
        question
        for question in questions
        if question.lesson and question.lesson.content_status == ContentStatus.published
    ]
    debug_tasks = list(
        db.scalars(
            select(DebugTask)
            .where(
                or_(
                    DebugTask.title.ilike(q),
                    DebugTask.prompt.ilike(q),
                    DebugTask.slug.ilike(q),
                )
            )
            .where(DebugTask.content_status == ContentStatus.published)
            .options(selectinload(DebugTask.lesson))
            .limit(10)
        )
    )
    mini_tasks = list(
        db.scalars(
            select(MiniTask)
            .where(
                or_(
                    MiniTask.title.ilike(q),
                    MiniTask.prompt.ilike(q),
                    MiniTask.slug.ilike(q),
                )
            )
            .where(MiniTask.content_status == ContentStatus.published)
            .options(selectinload(MiniTask.lesson))
            .limit(10)
        )
    )

    for tag in tag_matches:
        for question in tag.questions:
            if (
                question.content_status == ContentStatus.published
                and question.lesson
                and question.lesson.content_status == ContentStatus.published
            ):
                questions = _append_unique(questions, question)
        debug_tasks.extend(
            item
            for item in db.scalars(
                select(DebugTask)
                .where(DebugTask.concept_tag_id == tag.id)
                .where(DebugTask.content_status == ContentStatus.published)
                .options(selectinload(DebugTask.lesson))
            )
            if item.id not in {task.id for task in debug_tasks}
            and item.lesson
            and item.lesson.content_status == ContentStatus.published
        )
        mini_tasks.extend(
            item
            for item in db.scalars(
                select(MiniTask)
                .where(MiniTask.concept_tag_id == tag.id)
                .where(MiniTask.content_status == ContentStatus.published)
                .options(selectinload(MiniTask.lesson))
            )
            if item.id not in {task.id for task in mini_tasks}
            and item.lesson
            and item.lesson.content_status == ContentStatus.published
        )

    for lesson in lessons:
        for question in lesson.questions:
            if question.content_status == ContentStatus.published:
                questions = _append_unique(questions, question)
        for task in lesson.debug_tasks:
            if task.content_status == ContentStatus.published:
                debug_tasks = _append_unique(debug_tasks, task)
        for task in lesson.mini_tasks:
            if task.content_status == ContentStatus.published:
                mini_tasks = _append_unique(mini_tasks, task)

    modules = db.scalars(
        select(Module)
        .where(or_(Module.title.ilike(q), Module.description.ilike(q)))
        .limit(10)
    ).all()
    tracks = db.scalars(
        select(Track)
        .where(Track.is_published.is_(True))
        .where(or_(Track.title.ilike(q), Track.description.ilike(q), Track.target_audience.ilike(q)))
        .limit(10)
    ).all()

    return {
        "query": query,
        "concept_tags": [
            {
                "type": "concept_tag",
                "id": tag.id,
                "title": tag.name,
                "description": tag.description,
                "parent": None,
            }
            for tag in tag_matches[:10]
        ],
        "lessons": [
            {
                "type": "lesson",
                "id": lesson.id,
                "title": lesson.title,
                "description": lesson.learning_goal,
                "parent": lesson.module.title if lesson.module else None,
            }
            for lesson in lessons[:10]
        ],
        "questions": [
            {
                "type": "question",
                "id": question.id,
                "title": question.prompt,
                "description": question.question_type.value,
                "parent": question.lesson.title if question.lesson else None,
            }
            for question in questions
        ],
        "debug_tasks": [
            {
                "type": "debug_task",
                "id": task.id,
                "title": task.title,
                "description": task.prompt,
                "parent": task.lesson.title if task.lesson else None,
            }
            for task in debug_tasks
        ],
        "mini_tasks": [
            {
                "type": "mini_task",
                "id": task.id,
                "title": task.title,
                "description": task.prompt,
                "parent": task.lesson.title if task.lesson else None,
            }
            for task in mini_tasks
        ],
        "modules": [
            {
                "type": "module",
                "id": module.id,
                "title": module.title,
                "description": module.description,
                "parent": None,
            }
            for module in modules
        ],
        "tracks": [
            {
                "type": "track",
                "id": track.id,
                "title": track.title,
                "description": track.description,
                "parent": None,
            }
            for track in tracks
        ],
    }


def _empty(query: str) -> dict:
    return {
        "query": query,
        "concept_tags": [],
        "lessons": [],
        "questions": [],
        "debug_tasks": [],
        "mini_tasks": [],
        "modules": [],
        "tracks": [],
    }


def _append_unique(items: list, item):
    if item.id not in {existing.id for existing in items}:
        items.append(item)
    return items
