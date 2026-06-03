# Backend Mastery System

Backend Mastery System is a skill-based learning platform that verifies understanding, not just content completion.

This base MVP includes:

- FastAPI backend with JWT auth, roles, SQLAlchemy models, seed data, OpenAPI docs, and pytest tests.
- PostgreSQL-ready schema with a SQLite fallback for quick local development.
- React + TypeScript + Vite frontend with Tailwind CSS.
- Dashboard, skill map, module detail, lesson flow, question feedback, review queue, search, and simple admin content base.

## Project Structure

```text
backend/
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
python -m app.seed
uvicorn app.main:app --reload
```

API docs will be available at:

- http://localhost:8000/docs
- http://localhost:8000/openapi.json

Sample seeded accounts:

- Admin: `admin@example.com` / `admin123`
- Learner: `learner@example.com` / `learner123`

The backend defaults to SQLite for a no-friction local run. To use PostgreSQL, set `DATABASE_URL` in `backend/.env`, for example:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/backend_mastery
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server:

- http://localhost:5173

If your API runs somewhere else, set:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Optional PostgreSQL With Docker

```bash
docker compose up -d db
```

Then set the backend `DATABASE_URL` to the PostgreSQL URL shown above and run:

```bash
cd backend
python -m app.seed
uvicorn app.main:app --reload
```

## Tests

```bash
cd backend
pytest
```

The tests cover auth, reading-only progress behavior, wrong-answer feedback, and review scheduling.
