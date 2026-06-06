# Backend Mastery System

Backend Mastery System is a skill-based learning platform that verifies understanding, not just content completion.

The MVP is a learning engine foundation: taxonomy, auth, proof-of-understanding progress, feedback, review scheduling, search across practice surfaces, and simple admin content management.

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic, JWT auth
- Database: PostgreSQL-ready, SQLite fallback for local development
- Frontend: React, TypeScript, Vite, Tailwind CSS
- Tests: pytest

## Project Structure

```text
backend/
  alembic/
  app/
    api/routes/
    core/
    db/
    models/
    schemas/
    services/
    main.py
    seed.py
  tests/
frontend/
  src/
    api/
    components/
    features/
    pages/
    types/
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m alembic upgrade head
python -m app.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

API docs:

- http://127.0.0.1:8001/docs
- http://127.0.0.1:8001/openapi.json

The backend now uses Alembic for schema setup. `AUTO_CREATE_TABLES=false` is the default. Set it to `true` only as a temporary local fallback.

## Database

SQLite local default:

```env
DATABASE_URL=sqlite:///./backend_mastery_dev.db
```

Optional PostgreSQL with Docker:

```bash
docker compose up -d db
```

Then use:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/backend_mastery
```

Apply migrations after changing the database URL:

```bash
cd backend
python -m alembic upgrade head
python -m app.seed
```

Reset local seed data:

```bash
cd backend
python -m app.seed --reset
```

## Content System V1

Learning content now has a lifecycle:

- `draft`: visible to admins only.
- `published`: visible to learners and included in lesson/search/progress flows.
- `archived`: retained for admins, hidden from learners.

Lifecycle status is enforced for lessons, questions, debug tasks, and mini tasks. Reading a draft lesson by guessing its id should return `404` for learners.

### Import Lesson JSON

Use the admin API:

```bash
POST /admin/content/import/lesson
```

The import payload can include lesson metadata, blocks, questions, options, concept tags, debug task placeholders, and mini task placeholders.

Schema documentation:

```text
docs/content_schema.md
```

Sample import file:

```text
examples/python_function_return_lesson.json
```

Recommended local workflow:

1. Import as `draft`.
2. Preview in the admin page.
3. Publish after validation passes.

### Export Lesson JSON

Use:

```bash
GET /admin/content/export/lesson/{id}
```

This returns the lesson in the same structured JSON shape used for imports.

### Publish and Archive

Publish:

```bash
POST /admin/lessons/{id}/publish
```

Archive:

```bash
POST /admin/lessons/{id}/archive
```

A lesson cannot be published unless it has a learning goal block, why-it-matters block, core concept block, good example, bad example or common mistake, quick check question, explain-back question, and checklist block.

## Proof Submission Flow

Proof-of-understanding now uses written submissions instead of checklist-only completion for explain-back, debug tasks, mini tasks, and reflections.

Submit proof:

```bash
POST /lessons/{lesson_id}/proofs/submit
```

Payload shape:

```json
{
  "proof_type": "debug_task",
  "question_id": null,
  "debug_task_id": 1,
  "mini_task_id": null,
  "answer_text": "Bug: ... Cause: ... Fix: ...",
  "code_text": null
}
```

Supported `proof_type` values:

- `explain_back`
- `debug_task`
- `mini_task`
- `reflection`
- `review`

List lesson proof submissions for the current learner:

```bash
GET /lessons/{lesson_id}/proofs
```

Evaluation is heuristic only for now. No AI grading is used. A proof only counts toward mastery when its status is `passed` or `strong`; weak proofs create review work and keep the lesson in review until repaired.

The heuristic evaluator checks more than keyword presence:

- meaningful answer length
- expected concept coverage
- repeated spam text and repeated words
- answer specificity and backend consequence
- required structure for debug proofs: bug, cause, and fix
- acceptance criteria connection for mini tasks
- code presence when a mini task asks for code
- generic reflection answers such as `I understand`
- obvious misconception patterns such as treating `print` and `return` as interchangeable

Normalized proof feedback uses:

```json
{
  "correct_points": [],
  "missing_points": [],
  "misconceptions": [],
  "feedback": "Human-readable repair feedback.",
  "remedial_question": "Small next question.",
  "evaluation_source": "heuristic"
}
```

Mastery requires:

- reading completed
- quick check passed
- explain-back proof passed
- debug proof passed
- mini task proof passed
- no active `review_required` flag

## Review Remediation Flow

Weak proof submissions and wrong quiz answers create review items. The review page now shows the lesson, concept, original weak proof when available, missing points, remedial question, due date, and review count.

Due reviews:

```bash
GET /reviews/due
```

Submit a repair answer:

```bash
POST /reviews/{review_id}/submit
```

Payload:

```json
{
  "answer_text": "A return value gives the caller a reusable result that can be tested.",
  "code_text": null
}
```

Review evaluation is heuristic only:

- concept review: checks the missing concepts from the weak proof or related question
- debug review: expects bug, cause, and fix
- mini task review: expects a solution/code plus a short explanation

If review passes, the weak proof can be repaired, concept mastery moves forward, `review_required` can clear, and lesson mastery is recomputed. If review fails, the item stays active, `review_count` increases, and the next due date is scheduled for tomorrow.

## Admin Proof Inspection

Admins can inspect proof submissions for debugging rubric behavior and reviewing learner progress.

List submissions:

```bash
GET /admin/proof-submissions
```

Optional filters:

- `user_id`
- `lesson_id`
- `proof_type`
- `status`
- `score_label`

Detail:

```bash
GET /admin/proof-submissions/{id}
```

The admin response includes user, lesson, proof type, answer/code text, score, normalized feedback JSON, attempt number, timestamps, and whether the proof created review items. The frontend admin page includes a simple Proof Submissions panel with filters and a detail view.

## Evaluation Quality & Audit V1

Proof evaluation remains deterministic and heuristic-only. The app does not call Groq, OpenAI, Gemini, OpenRouter, or any external AI provider.

Each proof submission now stores both the original heuristic evaluation and the final evaluation used by the product:

- heuristic status, score label, score number, and feedback JSON
- evaluation confidence: `low`, `medium`, or `high`
- final evaluation status: `accepted`, `rejected`, or `needs_review`
- final score label, score number, and feedback JSON
- admin override metadata when present: admin user, timestamp, and override note

Low-confidence or borderline heuristic results are kept visible to admins. Ambiguous weak answers are marked `needs_review` as the final evaluation status, while obvious empty/incorrect submissions can be marked `rejected`.

Admin override:

```bash
PATCH /admin/proof-submissions/{id}/override
```

Payload:

```json
{
  "final_status": "accepted",
  "score_label": "stable",
  "override_note": "Manual review accepted this answer for the current rubric."
}
```

The override updates the final result and compatibility progress fields, but preserves the original heuristic snapshot for audit. If an accepted override repairs an active review item, the related review can be closed and lesson progress is recomputed.

Evaluation analytics:

```bash
GET /admin/proof-evaluation-analytics
```

The analytics endpoint returns total submissions, counts by proof type, final status, heuristic status, confidence, score label, override count/rate, top lessons with rejected or needs-review proofs, and top misconceptions found in feedback JSON.

Migration:

```bash
cd backend
python -m alembic upgrade head
```

This applies `0005_evaluation_audit.py`, which adds audit/final evaluation fields to `user_proof_submissions` and backfills existing submissions from their current heuristic result.

## Seed Accounts

- Admin: `admin@example.com` / `admin123`
- Learner: `learner@example.com` / `learner123`

## Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend dev server:

- http://localhost:5173

For the local backend on port 8001, set:

```env
VITE_API_BASE_URL=http://127.0.0.1:8001
```

## Tests and Build

Backend tests:

```bash
cd backend
python -m pytest
```

Frontend build:

```bash
cd frontend
npm run build
```

Frontend dependency audit:

```bash
cd frontend
npm audit
```

## Common Errors

- `Port 8000 already in use`: run the backend on `8001` as shown above.
- `no such table`: run `python -m alembic upgrade head`, then `python -m app.seed`.
- `401 Unauthorized`: log in again or clear the frontend token from local storage.
- `403 Forbidden` on `/admin/*`: use the seeded admin account.
- Frontend cannot reach API: check `frontend/.env` and make sure `VITE_API_BASE_URL=http://127.0.0.1:8001`.
- Duplicate seed data: use `python -m app.seed --reset` for local development reset.
