# Content Schema V1

This schema describes the lesson JSON accepted by:

- `POST /admin/content/import/lesson`
- `GET /admin/content/export/lesson/{id}`

Lessons are imported as structured learning units, not static articles. A publishable lesson needs reading, examples, recall, explain-back, practice placeholders, and an end checklist.

## Lesson Object

```json
{
  "module_id": 1,
  "title": "Why return is better than print for backend logic",
  "slug": "return-better-than-print-import-v1",
  "learning_goal": "Explain why backend functions should return values callers can use.",
  "why_it_matters": "API routes, services, tests, and jobs need reusable values.",
  "estimated_minutes": 12,
  "sort_order": 10,
  "content_status": "draft",
  "concept_tags": [],
  "blocks": [],
  "questions": [],
  "debug_tasks": [],
  "mini_tasks": []
}
```

Required lesson fields:

- `module_id`: existing module id.
- `title`: learner-facing lesson title.
- `slug`: unique inside the module.
- `learning_goal`: the target outcome.
- `why_it_matters`: practical backend relevance.
- `content_status`: `draft`, `published`, or `archived`.

`draft` is the safest import status. Use the publish endpoint after preview and validation.

Imported child content inherits the lesson status when its own `content_status` is omitted. For example, importing a `draft` lesson with questions that omit `content_status` creates draft questions. Publishing the lesson later promotes draft child questions, debug tasks, and mini tasks to `published`.

## Block Types

Supported `block_type` values:

- `text`
- `code`
- `warning`
- `example_good`
- `example_bad`
- `common_mistake`
- `question`
- `reflection`
- `mini_task`
- `debug_task`
- `checklist`

Each block accepts:

- `block_type`
- `title`
- `body`
- `code_language`
- `block_metadata`
- `sort_order`

Checklist blocks can store items in `block_metadata.items`.

Debug and mini task blocks can reference task content by slug:

```json
{
  "block_type": "debug_task",
  "title": "Debug challenge",
  "body": "Find the broken reasoning.",
  "block_metadata": {
    "task_slug": "debug-hidden-none"
  }
}
```

For `debug_task` blocks, `block_metadata.task_slug` must match a slug in `debug_tasks` when provided. For `mini_task` blocks, it must match a slug in `mini_tasks`.

## Question Types

Supported `question_type` values:

- `multiple_choice`
- `true_false`
- `short_answer`
- `explain_back`
- `scenario_question`

Multiple-choice questions should include at least two options and one correct option:

```json
{
  "slug": "quick-check-return-vs-print",
  "question_type": "multiple_choice",
  "prompt": "Which output is reusable by an API route?",
  "difficulty": "foundation",
  "explanation": "Returned values remain available to callers.",
  "concept_tag_slugs": ["return-values"],
  "options": [
    {
      "label": "A",
      "text": "Printing inside the function",
      "is_correct": false,
      "explanation": "Printing hides the value from the caller."
    },
    {
      "label": "B",
      "text": "Returning from the function",
      "is_correct": true,
      "explanation": "Returning keeps the value reusable."
    }
  ]
}
```

Question fields:

- `slug`: optional authoring identifier unique within the imported lesson payload.
- `content_status`: optional. Inherits lesson status when omitted.
- `concept_tag_slugs`: optional list of concept tag slugs from `concept_tags`.

Explain-back questions should include:

- `prompt`
- `expected_concepts`
- `rubric`
- `sample_ideal_answer`
- `misconception_notes`
- `remedial_prompt`

Debug task fields:

- `slug`: optional authoring identifier. Used by `debug_task` blocks through `block_metadata.task_slug`.
- `title`
- `prompt`
- `broken_code`
- `hint`
- `expected_fix_summary`
- `difficulty`
- `content_status`: optional. Inherits lesson status when omitted.
- `concept_tag_slug`: optional concept tag slug.

Mini task fields:

- `slug`: optional authoring identifier. Used by `mini_task` blocks through `block_metadata.task_slug`.
- `title`
- `prompt`
- `acceptance_criteria`
- `difficulty`
- `content_status`: optional. Inherits lesson status when omitted.
- `concept_tag_slug`: optional concept tag slug.

## Publish Validation

A lesson cannot be published unless it has:

- Learning goal or objective block.
- Why it matters block.
- Core concept block.
- At least one `example_good` block.
- At least one `example_bad` block, `common_mistake` block, or title-based common mistake block.
- At least one quick check question.
- At least one explain-back question.
- At least one `checklist` block.

If validation fails, the API returns `422` with clear missing items.

## Import Validation

Import fails when:

- The target `module_id` does not exist.
- The slug already exists in that module.
- Required strings are empty.
- Multiple-choice questions do not have enough options or a correct option.
- Explain-back questions omit `expected_concepts`.
- Questions or tasks reference unknown `concept_tag_slugs`.
- Duplicate question, debug task, or mini task slugs are provided.
- A `debug_task` or `mini_task` block references an unknown `block_metadata.task_slug`.

Concept tags in `concept_tags` are created if their slug does not already exist.

## Example File

See:

```text
examples/python_function_return_lesson.json
```
