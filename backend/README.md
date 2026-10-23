# Expense Tracker — Backend

FastAPI (Python 3.12) + Supabase. All routes are under `/api`.

## Structure

```
app/
  main.py                      app factory, /api prefix, health check
  core/config.py               env settings (SUPABASE_URL, SUPABASE_KEY, APP_TIMEZONE)
  core/errors.py               every error -> {"error": "message"}; validation -> 400
  core/clock.py                "today" in the configured timezone
  schemas/expense.py           request validation + response models
  repositories/expense_repo.py Supabase queries (behind a Protocol, faked in tests)
  services/expense_service.py  pagination, totals, monthly summary
  api/routes/expenses.py       HTTP layer
sql/001_create_expenses.sql    table, indexes, RLS, aggregate functions
tests/                         unit tests (fake repo) + tests/integration (live Supabase, opt-in)
scripts/package.sh             builds the Beanstalk zip
scripts/check.sh               lint + format + tests with coverage
```

## Setup

1. In Supabase → SQL editor, run `sql/001_create_expenses.sql`.
2. Fill in `backend/.env` (copy of `.env.example`) with the project URL and **secret** key.
3. Install and run:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/api/docs

## Tests and checks

```bash
./scripts/check.sh                                 # ruff lint + format check + unit tests (coverage >= 90%)
.venv/bin/pytest                                   # unit tests only (in-memory fake repo, no network)
RUN_INTEGRATION=1 .venv/bin/pytest tests/integration   # live tests against Supabase from .env
```

- `tests/test_*.py` cover every validation rule, filters, ordering, pagination, totals across pages,
  404s, monthly summary, the `{"error"}` shape, and the Supabase query building (with a fake client).
- `tests/integration/` hits the real database through the real app. Each run writes into a random empty
  month between 1900 and 1989 and deletes what it created, so it never touches real data.
- CI (`.github/workflows/backend.yml`) runs the checks on every PR touching `backend/`, runs the live
  suite when `SUPABASE_URL`/`SUPABASE_KEY` repo secrets exist, and uploads the Beanstalk zip as an artifact.

## API

| Method | Path | Notes |
|---|---|---|
| POST | `/api/expenses` | `{title, amount, category, date?}` → 201 |
| GET | `/api/expenses` | `?category=&from=&to=&page=&limit=` (limit default 10, max 100) → `{items, total_count, total_amount}` |
| DELETE | `/api/expenses/{id}` | 204, 404 if missing |
| GET | `/api/expenses/summary?month=YYYY-MM` | `{month, totals: {food, travel, bills, other}, total}` |
| GET | `/api/health` | Beanstalk health check |

`total_amount` is computed in Postgres over **all** matching rows, not the current page.

## Deploy (Elastic Beanstalk, Python 3.12 platform)

```bash
./scripts/package.sh   # -> dist/backend-<timestamp>.zip
```

Upload the zip in the Beanstalk console (Upload and deploy). Set environment properties
`SUPABASE_URL`, `SUPABASE_KEY` (and optionally `APP_TIMEZONE`) under Configuration → Updates, monitoring
and logging → Environment properties. The `Procfile` runs gunicorn with uvicorn workers on port 8000
(the platform's nginx proxies to it), and `.ebextensions` sets the health check to `/api/health`.
