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
