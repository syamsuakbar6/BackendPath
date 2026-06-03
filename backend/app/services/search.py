from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import ConceptTag, DebugTask, Lesson, MiniTask, Module, Question, Track


def search_learning(db: Session, query: str) -> dict:
    q = f"%{query.strip()}%"
    if not query.strip():
        return _empty(query)

    lessons = list(
        db.scalars(
            select(Lesson)
            .where(
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

    tag_matches = db.scalars(
        select(ConceptTag).where(
            or_(ConceptTag.name.ilike(q), ConceptTag.slug.ilike(q), ConceptTag.description.ilike(q))
        )
    ).all()
    for tag in tag_matches:
        for lesson in tag.lessons:
            if lesson not in lessons:
                lessons.append(lesson)

    questions = db.scalars(
        select(Question)
        .where(Question.prompt.ilike(q))
        .options(selectinload(Question.lesson))
        .limit(10)
    ).all()
    debug_tasks = db.scalars(
        select(DebugTask)
        .where(or_(DebugTask.title.ilike(q), DebugTask.prompt.ilike(q)))
        .options(selectinload(DebugTask.lesson))
        .limit(10)
    ).all()
    mini_tasks = db.scalars(
        select(MiniTask)
        .where(or_(MiniTask.title.ilike(q), MiniTask.prompt.ilike(q)))
        .options(selectinload(MiniTask.lesson))
        .limit(10)
    ).all()
    modules = db.scalars(
        select(Module)
        .where(or_(Module.title.ilike(q), Module.description.ilike(q)))
        .limit(10)
    ).all()
    tracks = db.scalars(
        select(Track)
        .where(or_(Track.title.ilike(q), Track.description.ilike(q), Track.target_audience.ilike(q)))
        .limit(10)
    ).all()

    return {
        "query": query,
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
        "lessons": [],
        "questions": [],
        "debug_tasks": [],
        "mini_tasks": [],
        "modules": [],
        "tracks": [],
    }
